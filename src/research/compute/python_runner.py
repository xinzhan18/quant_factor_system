"""Python factor runner — R8 escape hatch.

DSL is the default path for Phase 2 factor evaluation. A Python factor is
the escape hatch when a hypothesis cannot be expressed in the Qlib DSL.
Each admitted Python factor lives at
``storage/python_factors/F{id}_{name}.py`` and each in-flight candidate
lives at ``storage/batches/batch_{id}/python_candidates/C{id}.py``.

Module contract (enforced by :func:`load_python_candidate`):

* ``REQUIRED_FIELDS: list[str]`` — list of ``$``-prefixed market fields
  the factor needs (``$close``, ``$volume``, ``$turnover_rate``, …)
* ``VECTORIZED: bool`` — must be ``True`` (R5 — no row-wise loops allowed)
* ``def compute(df: pd.DataFrame) -> pd.Series`` — the actual logic,
  taking a MultiIndex(time, symbol) frame with the requested columns and
  returning a MultiIndex(time, symbol) Series of factor values

Violations raise :class:`PythonFactorContractError` before any code from
the candidate module executes — the runner uses :mod:`ast` static analysis
for the import whitelist / forbidden-call check instead of trusting the
module at import time.

Security: Python candidates are written by the LLM and then run in-process.
The AST whitelist is a defense-in-depth check, not a sandbox. Phase 1
DESIGN should also enforce these rules at freeze time (checklist P3).
"""

from __future__ import annotations

import ast
import importlib.util
import inspect
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


# Module-level imports we allow Python candidates to use
_ALLOWED_IMPORTS: frozenset[str] = frozenset(
    {
        "numpy",
        "pandas",
        "scipy",
        # Standard library utilities that are safe
        "math",
        "typing",
        "dataclasses",
        "functools",
        "itertools",
        "__future__",
    }
)

# Top-level built-in calls we never want to see in a candidate
_FORBIDDEN_CALLS: frozenset[str] = frozenset(
    {
        "eval",
        "exec",
        "compile",
        "__import__",
        "open",
        "input",
        "breakpoint",
    }
)


class PythonFactorContractError(ValueError):
    """Raised when a Python factor module violates the R8 contract."""


@dataclass
class LoadedPythonFactor:
    """A validated + imported Python factor module ready to run."""

    path: Path
    module: Any
    required_fields: list[str]
    vectorized: bool

    def compute(self, df: pd.DataFrame) -> pd.Series:
        return self.module.compute(df)


# ---------------------------------------------------------------------------
# AST-level static validation (runs before the module is imported)
# ---------------------------------------------------------------------------


def _validate_ast(source: str, path: Path) -> None:
    """Reject imports, calls, and names that violate the contract.

    Checks:

    * all ``import X`` / ``from X import ...`` must target a name in
      ``_ALLOWED_IMPORTS``
    * no top-level or nested calls to names in ``_FORBIDDEN_CALLS``
    * no ``getattr`` / ``setattr`` / ``delattr`` (prevents attribute-based
      sandbox escapes)
    """
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        raise PythonFactorContractError(
            f"{path.name}: syntax error: {exc}"
        ) from exc

    for node in ast.walk(tree):
        # Imports
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".")[0]
                if top not in _ALLOWED_IMPORTS:
                    raise PythonFactorContractError(
                        f"{path.name}: forbidden import '{alias.name}' "
                        f"(allowed top-levels: {sorted(_ALLOWED_IMPORTS)})"
                    )
        elif isinstance(node, ast.ImportFrom):
            if node.module is None:
                continue
            top = node.module.split(".")[0]
            if top not in _ALLOWED_IMPORTS:
                raise PythonFactorContractError(
                    f"{path.name}: forbidden import 'from {node.module}' "
                    f"(allowed top-levels: {sorted(_ALLOWED_IMPORTS)})"
                )
        # Forbidden function calls
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id in _FORBIDDEN_CALLS:
                raise PythonFactorContractError(
                    f"{path.name}: forbidden call '{func.id}()'"
                )
            if (
                isinstance(func, ast.Name)
                and func.id in ("getattr", "setattr", "delattr")
            ):
                raise PythonFactorContractError(
                    f"{path.name}: attribute manipulation via '{func.id}()' "
                    "is not allowed in Python factors"
                )


# ---------------------------------------------------------------------------
# Module contract validation (runs after the module is imported)
# ---------------------------------------------------------------------------


def _validate_module(module: Any, path: Path) -> tuple[list[str], bool]:
    """Check ``REQUIRED_FIELDS``, ``VECTORIZED``, and ``compute`` signature."""
    if not hasattr(module, "REQUIRED_FIELDS"):
        raise PythonFactorContractError(
            f"{path.name}: missing REQUIRED_FIELDS module-level attribute"
        )
    required = module.REQUIRED_FIELDS
    if not isinstance(required, list) or not all(
        isinstance(f, str) and f.startswith("$") for f in required
    ):
        raise PythonFactorContractError(
            f"{path.name}: REQUIRED_FIELDS must be a list of '$'-prefixed "
            f"strings, got {type(required).__name__}"
        )

    if not hasattr(module, "VECTORIZED"):
        raise PythonFactorContractError(
            f"{path.name}: missing VECTORIZED module-level attribute"
        )
    if module.VECTORIZED is not True:
        raise PythonFactorContractError(
            f"{path.name}: VECTORIZED must be True (R5 — no row loops)"
        )

    if not hasattr(module, "compute"):
        raise PythonFactorContractError(
            f"{path.name}: missing compute(df) function"
        )
    if not callable(module.compute):
        raise PythonFactorContractError(
            f"{path.name}: compute is not callable"
        )

    # Signature: def compute(df: pd.DataFrame) -> pd.Series
    sig = inspect.signature(module.compute)
    params = list(sig.parameters.values())
    if len(params) != 1:
        raise PythonFactorContractError(
            f"{path.name}: compute() must take exactly one argument, "
            f"got {len(params)}"
        )

    return list(required), bool(module.VECTORIZED)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def load_python_candidate(path: str | Path) -> LoadedPythonFactor:
    """Load + validate a Python factor candidate.

    Raises
    ------
    PythonFactorContractError
        If the AST check fails, the module lacks required attributes,
        VECTORIZED is not True, or ``compute`` has the wrong signature.
    """
    p = Path(path)
    if not p.exists():
        raise PythonFactorContractError(f"python factor not found: {p}")

    source = p.read_text(encoding="utf-8")
    _validate_ast(source, p)

    spec = importlib.util.spec_from_file_location(p.stem, p)
    if spec is None or spec.loader is None:
        raise PythonFactorContractError(
            f"{p.name}: could not construct import spec"
        )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    required, vectorized = _validate_module(module, p)

    return LoadedPythonFactor(
        path=p,
        module=module,
        required_fields=required,
        vectorized=vectorized,
    )


def run_python_factor(
    loaded: LoadedPythonFactor,
    market_df: pd.DataFrame,
    timing_warn_threshold_s: float = 5.0,
) -> pd.Series:
    """Execute a loaded Python factor against ``market_df`` and return values.

    Parameters
    ----------
    loaded
        The ``LoadedPythonFactor`` from :func:`load_python_candidate`.
    market_df
        MultiIndex (time, symbol) DataFrame with at least all columns in
        ``loaded.required_fields``.
    timing_warn_threshold_s
        If ``compute()`` takes longer than this, emit a warning — catches
        silent regressions into Python-level loops.

    Returns
    -------
    pd.Series
        MultiIndex (time, symbol) factor values.

    Raises
    ------
    PythonFactorContractError
        If ``market_df`` is missing a required column, or if ``compute()``
        returns the wrong type.
    """
    missing = [
        f for f in loaded.required_fields if f not in market_df.columns
    ]
    if missing:
        raise PythonFactorContractError(
            f"{loaded.path.name}: market_df missing columns {missing}"
        )

    t0 = time.perf_counter()
    out = loaded.compute(market_df)
    elapsed = time.perf_counter() - t0

    if not isinstance(out, pd.Series):
        raise PythonFactorContractError(
            f"{loaded.path.name}: compute() must return pd.Series, "
            f"got {type(out).__name__}"
        )
    if not isinstance(out.index, pd.MultiIndex):
        raise PythonFactorContractError(
            f"{loaded.path.name}: compute() return must have MultiIndex, "
            f"got {type(out.index).__name__}"
        )
    if out.index.duplicated().any():
        raise PythonFactorContractError(
            f"{loaded.path.name}: compute() returned duplicated index entries"
        )

    if elapsed > timing_warn_threshold_s:
        # Surface via logging rather than print so Phase 2 can route it
        import logging

        logging.getLogger(__name__).warning(
            "python factor %s compute() took %.2fs (> %.1fs threshold) — "
            "likely non-vectorized",
            loaded.path.name,
            elapsed,
            timing_warn_threshold_s,
        )

    return out
