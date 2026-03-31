"""Sandbox — isolated execution of LLM-generated Python factor code.

Provides ``run_factor_in_sandbox`` which:
1. Statically checks the code with ``ast`` for forbidden imports.
2. Wraps the code in a function definition.
3. Executes the wrapped function inside a ``multiprocessing.Process`` so
   any crash, infinite loop, or malicious side-effect cannot affect the
   parent process.
4. Communicates the result (or error) back through a ``multiprocessing.Pipe``.
5. Enforces a wall-clock timeout by killing the child process if it exceeds
   the limit.

The child receives an ``OpsAdapter`` instance so factor code can call
``ops.std(...)``, ``ops.cs_rank(...)``, etc.
"""

from __future__ import annotations

import ast
import multiprocessing
import pickle
import textwrap
from typing import Any

import pandas as pd

from mining.ops_adapter import OpsAdapter

# ---------------------------------------------------------------------------
# Forbidden top-level module names
# ---------------------------------------------------------------------------

_FORBIDDEN_IMPORTS: frozenset[str] = frozenset(
    [
        "os",
        "sys",
        "subprocess",
        "shutil",
        "socket",
        "http",
        "urllib",
        "requests",
        "pathlib",
        "importlib",
        "ctypes",
        "signal",
    ]
)


# ---------------------------------------------------------------------------
# Public exception
# ---------------------------------------------------------------------------


class SandboxError(Exception):
    """Raised for any sandbox failure: static check, timeout, or runtime error."""


# ---------------------------------------------------------------------------
# Static analysis helper
# ---------------------------------------------------------------------------


def _check_forbidden_imports(code: str) -> None:
    """Parse *code* with ast and raise SandboxError for any forbidden import.

    Checks both ``import X`` and ``from X import ...`` statements.
    Raises:
        SandboxError: if a forbidden import is detected.
        SandboxError: if the code contains a SyntaxError.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        raise SandboxError(f"SyntaxError: {exc}") from exc

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                # Take only the top-level package name (e.g. "os.path" → "os")
                top = alias.name.split(".")[0]
                if top in _FORBIDDEN_IMPORTS:
                    raise SandboxError(
                        f"Forbidden import detected: '{alias.name}' is not allowed"
                    )
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            top = module.split(".")[0]
            if top in _FORBIDDEN_IMPORTS:
                raise SandboxError(
                    f"Forbidden import detected: '{module}' is not allowed"
                )


# ---------------------------------------------------------------------------
# Subprocess target
# ---------------------------------------------------------------------------


def _subprocess_target(conn, wrapped_code: str, df_bytes: bytes, params: dict) -> None:
    """Target function executed inside the child process.

    Deserialises *df*, executes *wrapped_code*, then pickles the result (or
    an error description) back through *conn*.

    Protocol over *conn*:
        On success: send  ("ok",   pickled_series_bytes)
        On failure: send  ("error", error_message_string)
    """
    try:
        df = pickle.loads(df_bytes)
        ops = OpsAdapter()

        # Build a namespace with safe builtins plus the modules factor code typically needs
        import numpy as np

        namespace: dict[str, Any] = {
            "__builtins__": {
                # math
                "abs": abs, "round": round, "min": min, "max": max,
                "len": len, "range": range, "enumerate": enumerate,
                "zip": zip, "map": map, "filter": filter,
                "list": list, "tuple": tuple, "dict": dict, "set": set,
                "int": int, "float": float, "str": str, "bool": bool,
                "isinstance": isinstance, "issubclass": issubclass,
                "hasattr": hasattr, "getattr": getattr,
                "print": print,
                # allow importing safe numeric libraries inside factor code
                "__import__": __builtins__["__import__"] if isinstance(__builtins__, dict) else __import__,
            },
            "pd": pd,
            "np": np,
        }

        exec(compile(wrapped_code, "<factor>", "exec"), namespace)  # noqa: S102

        fn = namespace["_factor_fn"]
        result = fn(df, params, ops)

        if not isinstance(result, pd.Series):
            conn.send(("error", f"SandboxError: factor must return pd.Series, got {type(result).__name__}"))
            return

        conn.send(("ok", pickle.dumps(result)))
    except Exception as exc:  # noqa: BLE001
        conn.send(("error", f"{type(exc).__name__}: {exc}"))
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run_factor_in_sandbox(
    code: str,
    df: pd.DataFrame,
    params: dict,
    timeout: int = 60,
) -> pd.Series:
    """Execute *code* in an isolated subprocess and return the resulting Series.

    Args:
        code:    Python snippet that ends with a ``return`` statement.
                 It receives ``df`` (pd.DataFrame), ``params`` (dict), and
                 ``ops`` (OpsAdapter) as arguments.
        df:      Panel DataFrame with (datetime, instrument) MultiIndex.
        params:  Hyper-parameters passed as the ``params`` dict inside the
                 factor code.
        timeout: Wall-clock seconds before the subprocess is killed.

    Returns:
        pd.Series produced by the factor code.

    Raises:
        SandboxError: on syntax error, forbidden import, timeout, runtime
                      error, or non-Series return value.
    """
    # 1. Static checks (before spawning any process)
    _check_forbidden_imports(code)

    # 2. Wrap code in a function so ``return`` statements are legal
    indented = textwrap.indent(code, "    ")
    wrapped_code = f"def _factor_fn(df, params, ops):\n{indented}\n"

    # 3. Serialise the DataFrame once in the parent to avoid fork-copy overhead
    df_bytes = pickle.dumps(df)

    # 4. Set up inter-process communication
    parent_conn, child_conn = multiprocessing.Pipe(duplex=False)

    # 5. Spawn child process
    proc = multiprocessing.Process(
        target=_subprocess_target,
        args=(child_conn, wrapped_code, df_bytes, params),
        daemon=True,
    )
    proc.start()
    child_conn.close()  # parent does not write to the pipe

    # 6. Wait for result with timeout
    finished = parent_conn.poll(timeout)
    if not finished:
        proc.kill()
        proc.join()
        parent_conn.close()
        raise SandboxError(f"Sandbox timeout: factor execution exceeded {timeout}s")

    # 7. Read result
    try:
        status, payload = parent_conn.recv()
    except EOFError as exc:
        proc.join()
        parent_conn.close()
        raise SandboxError("Sandbox subprocess terminated without sending a result") from exc
    finally:
        proc.join()
        parent_conn.close()

    # 8. Interpret result
    if status == "ok":
        return pickle.loads(payload)

    # status == "error"
    msg = payload  # already a descriptive string
    if "SandboxError: factor must return pd.Series" in msg:
        raise SandboxError(msg)
    raise SandboxError(msg)
