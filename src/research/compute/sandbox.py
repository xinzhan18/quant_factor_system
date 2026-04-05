"""Sandbox -- isolated execution of LLM-generated Python factor code.

Rewrite of ``mining.sandbox`` for the research pipeline.  Provides
``run_factor_in_sandbox`` which:

1. Statically checks the code with ``ast`` for forbidden imports.
2. Wraps the code in a function definition.
3. Executes the wrapped function inside a ``multiprocessing.Process`` so
   any crash, infinite loop, or malicious side-effect cannot affect the
   parent process.
4. Communicates the result (or error) back through a ``multiprocessing.Pipe``.
5. Enforces a wall-clock timeout by killing the child process.

The child receives a lightweight ``_OpsAdapter`` instance so factor code
can call ``ops.std(...)``, ``ops.cs_rank(...)``, etc.
"""

from __future__ import annotations

import ast
import multiprocessing
import pickle
import textwrap
from typing import Any, Dict

import pandas as pd

# -----------------------------------------------------------------------
# Forbidden modules
# -----------------------------------------------------------------------

_FORBIDDEN_IMPORTS = frozenset(
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

# -----------------------------------------------------------------------
# Public exception
# -----------------------------------------------------------------------


class SandboxError(Exception):
    """Raised for any sandbox failure: static check, timeout, or runtime error."""


# -----------------------------------------------------------------------
# Static analysis
# -----------------------------------------------------------------------


def _check_forbidden_imports(code: str) -> None:
    """Parse *code* with ast and raise SandboxError for any forbidden import."""
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        raise SandboxError(f"SyntaxError: {exc}") from exc

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
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


# -----------------------------------------------------------------------
# Lightweight OpsAdapter (embedded in sandbox, no external imports)
# -----------------------------------------------------------------------


class _OpsAdapter:
    """Pandas-based operator wrappers for panel DataFrames.

    All methods accept pd.Series with (datetime, instrument) MultiIndex.
    Embedded directly in the sandbox module to avoid importing from
    ``mining`` package.
    """

    @staticmethod
    def _ts_apply(series, func):
        return series.groupby(level="instrument", group_keys=False).apply(func)

    def std(self, series, window):
        return self._ts_apply(
            series, lambda s: s.rolling(window, min_periods=window).std()
        )

    def mean(self, series, window):
        return self._ts_apply(
            series, lambda s: s.rolling(window, min_periods=window).mean()
        )

    def cs_rank(self, series):
        def _rank01(s):
            import pandas as _pd

            n = len(s)
            if n <= 1:
                return _pd.Series(0.0, index=s.index)
            r = s.rank(method="average")
            return (r - 1) / (n - 1)

        return series.groupby(level="datetime", group_keys=False).apply(_rank01)

    def cs_zscore(self, series):
        def _zscore(s):
            mu = s.mean()
            sigma = s.std()
            if sigma == 0:
                return s * 0.0
            return (s - mu) / sigma

        return series.groupby(level="datetime", group_keys=False).apply(_zscore)

    def delta(self, series, period):
        return self._ts_apply(series, lambda s: s.diff(period))

    def signed_power(self, series, exp):
        import numpy as _np

        return _np.sign(series) * _np.abs(series) ** exp

    def tanh(self, series):
        import numpy as _np

        return _np.tanh(series)

    def safe_div(self, x, y):
        import numpy as _np

        result = x / y
        result = result.replace([_np.inf, -_np.inf], 0.0)
        result = result.where(~(y == 0), other=0.0)
        return result

    def log1p_abs(self, series):
        import numpy as _np

        return _np.sign(series) * _np.log1p(_np.abs(series))


# -----------------------------------------------------------------------
# Subprocess target
# -----------------------------------------------------------------------


def _subprocess_target(conn, wrapped_code: str, df_bytes: bytes, params: dict) -> None:
    """Execute factor code inside the child process."""
    try:
        df = pickle.loads(df_bytes)
        ops = _OpsAdapter()

        import numpy as np

        namespace: Dict[str, Any] = {
            "__builtins__": {
                "abs": abs,
                "round": round,
                "min": min,
                "max": max,
                "len": len,
                "range": range,
                "enumerate": enumerate,
                "zip": zip,
                "map": map,
                "filter": filter,
                "list": list,
                "tuple": tuple,
                "dict": dict,
                "set": set,
                "int": int,
                "float": float,
                "str": str,
                "bool": bool,
                "isinstance": isinstance,
                "issubclass": issubclass,
                "hasattr": hasattr,
                "getattr": getattr,
                "print": print,
                "__import__": (
                    __builtins__["__import__"]
                    if isinstance(__builtins__, dict)
                    else __import__
                ),
            },
            "pd": pd,
            "np": np,
        }

        exec(compile(wrapped_code, "<factor>", "exec"), namespace)  # noqa: S102

        fn = namespace["_factor_fn"]
        result = fn(df, params, ops)

        if not isinstance(result, pd.Series):
            conn.send(
                (
                    "error",
                    f"SandboxError: factor must return pd.Series, got {type(result).__name__}",
                )
            )
            return

        conn.send(("ok", pickle.dumps(result)))
    except Exception as exc:  # noqa: BLE001
        conn.send(("error", f"{type(exc).__name__}: {exc}"))
    finally:
        conn.close()


# -----------------------------------------------------------------------
# Public API
# -----------------------------------------------------------------------


def run_factor_in_sandbox(
    code: str,
    df: pd.DataFrame,
    params: dict,
    timeout: int = 60,
) -> pd.Series:
    """Execute *code* in an isolated subprocess and return the resulting Series.

    Args:
        code:    Python snippet ending with a ``return`` statement.
                 Receives ``df`` (DataFrame), ``params`` (dict), ``ops`` (_OpsAdapter).
        df:      Panel DataFrame with (datetime, instrument) MultiIndex.
        params:  Hyper-parameters dict passed into the factor code.
        timeout: Wall-clock seconds before the subprocess is killed.

    Returns:
        pd.Series produced by the factor code.

    Raises:
        SandboxError: on syntax error, forbidden import, timeout, runtime
                      error, or non-Series return value.
    """
    _check_forbidden_imports(code)

    indented = textwrap.indent(code, "    ")
    wrapped_code = f"def _factor_fn(df, params, ops):\n{indented}\n"

    df_bytes = pickle.dumps(df)

    parent_conn, child_conn = multiprocessing.Pipe(duplex=False)

    proc = multiprocessing.Process(
        target=_subprocess_target,
        args=(child_conn, wrapped_code, df_bytes, params),
        daemon=True,
    )
    proc.start()
    child_conn.close()

    finished = parent_conn.poll(timeout)
    if not finished:
        proc.kill()
        proc.join()
        parent_conn.close()
        raise SandboxError(f"Sandbox timeout: factor execution exceeded {timeout}s")

    try:
        status, payload = parent_conn.recv()
    except EOFError as exc:
        proc.join()
        parent_conn.close()
        raise SandboxError(
            "Sandbox subprocess terminated without sending a result"
        ) from exc
    finally:
        proc.join()
        parent_conn.close()

    if status == "ok":
        return pickle.loads(payload)

    msg = payload
    if "SandboxError: factor must return pd.Series" in msg:
        raise SandboxError(msg)
    raise SandboxError(msg)
