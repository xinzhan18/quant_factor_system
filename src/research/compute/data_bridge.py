"""Data bridge: DB / Qlib → Phase2Inputs.

Assembles the 6 DataFrames + candidate signals that Phase 2 needs.
This is the glue between the data layer (``data/``) and the compute
layer (``research/compute/`` + ``research/phases/phase2_execute.py``).

Responsibilities:
1. **Qlib init** — one-time ``qlib.init`` + custom operator registration
2. **DSL evaluation** — ``D.features()`` for each DSL candidate
3. **Python factor evaluation** — ``python_runner.run_python_factor()``
4. **Barra style matrix** — build the 7-column style matrix from Qlib fields
5. **Library signals** — load admitted factors for redundancy check
6. **Cache** — build/load ``market_daily.parquet`` and ``barra_factors.parquet``
7. **Assembly** — ``build_phase2_inputs()`` returns a ready ``Phase2Inputs``

Usage from mine.py::

    from research.compute.data_bridge import make_phase2_executor
    inputs.phase2_executor = make_phase2_executor(config)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from research.compute.preprocess import PreprocessConfig
from research.phases.phase2_execute import CandidateInputs, Phase2Inputs, run_phase2
from research.storage.paths import StoragePaths
from research.storage.yaml_io import load_yaml

logger = logging.getLogger(__name__)

# Barra style factor expressions (Qlib DSL).
# Must produce the 7 columns in the same order as vectorized_barra.STYLE_NAMES.
BARRA_STYLE_EXPRS: dict[str, str] = {
    "log_circ_cap": "Log($circ_market_cap)",
    "book_to_price": "Div(1, $pb_ratio)",
    "mom_12_1": "Div($close, Ref($close, 240)) - Div($close, Ref($close, 20))",
    "str_1m": "Div($close, Ref($close, 20)) - 1",
    "vol_20d": "Std(Div($close, Ref($close, 1)) - 1, 20)",
    "turnover_20d": "Mean($turnover_rate, 20)",
    "ep_ratio": "Div(1, $pe_ratio)",
}

# ---------------------------------------------------------------------------
# Qlib initialization
# ---------------------------------------------------------------------------

_QLIB_INITIALIZED = False


def init_qlib(qlib_data_dir: str = "~/.qlib/qlib_data/cn_data_1d") -> None:
    """Initialize Qlib + register custom operators. Idempotent."""
    global _QLIB_INITIALIZED
    if _QLIB_INITIALIZED:
        return

    import qlib
    from qlib.config import C

    qlib.init(provider_uri=str(Path(qlib_data_dir).expanduser()))
    C.kernels = 1  # workers don't inherit custom _ops

    from research.compute.operators import register_custom_operators
    register_custom_operators()

    _QLIB_INITIALIZED = True
    logger.info("Qlib initialized: %s", qlib_data_dir)


# ---------------------------------------------------------------------------
# DSL expression evaluation
# ---------------------------------------------------------------------------


def _qlib_to_time_symbol(df: pd.DataFrame) -> pd.DataFrame:
    """Convert Qlib's (instrument, datetime) MultiIndex to (time, symbol).

    Qlib D.features() returns MultiIndex with level 0 = instrument (str),
    level 1 = datetime. Phase 2 expects (time, symbol) with datetime time.
    """
    if not isinstance(df.index, pd.MultiIndex):
        return df
    # Qlib order: (instrument, datetime) → swap to (datetime, instrument)
    df = df.swaplevel()
    df.index.names = ["time", "symbol"]
    df = df.sort_index()
    # Ensure time level is datetime
    time_level = df.index.get_level_values("time")
    if not pd.api.types.is_datetime64_any_dtype(time_level):
        df.index = df.index.set_levels(
            pd.to_datetime(df.index.levels[0]), level=0
        )
    return df


def eval_dsl_expression(
    expression: str,
    start: str = "2015-01-01",
    end: str = "2023-12-31",
) -> pd.Series:
    """Evaluate a Qlib DSL expression and return MultiIndex(time, symbol) Series."""
    from qlib.data import D

    inst_dict = D.instruments("all")
    df = D.features(inst_dict, fields=[expression], start_time=start, end_time=end)
    df = _qlib_to_time_symbol(df)
    return df.iloc[:, 0]


def eval_dsl_batch(
    expressions: dict[str, str],
    start: str = "2015-01-01",
    end: str = "2023-12-31",
) -> dict[str, pd.Series]:
    """Evaluate multiple DSL expressions in one D.features() call."""
    from qlib.data import D

    if not expressions:
        return {}

    inst_dict = D.instruments("all")
    fields = list(expressions.values())
    df = D.features(inst_dict, fields=fields, start_time=start, end_time=end)
    df = _qlib_to_time_symbol(df)

    result = {}
    for name, expr in expressions.items():
        idx = fields.index(expr)
        result[name] = df.iloc[:, idx]
    return result


# ---------------------------------------------------------------------------
# Barra style matrix
# ---------------------------------------------------------------------------


def build_barra_style_matrix(
    start: str = "2015-01-01",
    end: str = "2023-12-31",
    cache_path: Path | None = None,
) -> pd.DataFrame:
    """Build the 7-column Barra style matrix.

    Returns DataFrame with MultiIndex (datetime, instrument) and columns
    matching ``vectorized_barra.STYLE_NAMES``.

    If *cache_path* is provided, reads from / writes to parquet.
    """
    if cache_path and cache_path.exists():
        logger.info("Loading cached barra_factors from %s", cache_path)
        return pd.read_parquet(cache_path)

    logger.info("Building Barra style matrix from Qlib (%s to %s)", start, end)
    series_dict = eval_dsl_batch(BARRA_STYLE_EXPRS, start=start, end=end)

    df = pd.DataFrame(series_dict)
    # Phase 2's vectorized_barra expects (datetime, instrument)
    df.index.names = ["datetime", "instrument"]

    if cache_path:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(cache_path)
        logger.info("Cached barra_factors to %s (%.1f MB)",
                     cache_path, cache_path.stat().st_size / 1024 / 1024)

    return df


# ---------------------------------------------------------------------------
# Market data (forward returns, amount, market_cap)
# ---------------------------------------------------------------------------


def load_market_data(
    start: str = "2015-01-01",
    end: str = "2023-12-31",
    cache_path: Path | None = None,
) -> pd.DataFrame:
    """Load market data fields needed by Phase 2.

    Returns DataFrame with MultiIndex (time, symbol) and columns:
    ``returns_1d``, ``$amount``, ``$market_cap``.

    If *cache_path* provided, reads from / writes to parquet.
    """
    if cache_path and cache_path.exists():
        logger.info("Loading cached market_daily from %s", cache_path)
        df = pd.read_parquet(cache_path)
        # Ensure datetime index
        if isinstance(df.index, pd.MultiIndex):
            time_level = df.index.get_level_values(0)
            if not pd.api.types.is_datetime64_any_dtype(time_level):
                df.index = df.index.set_levels(pd.to_datetime(df.index.levels[0]), level=0)
        return df

    logger.info("Loading market data from Qlib (%s to %s)", start, end)
    from qlib.data import D

    inst_dict = D.instruments("all")
    fields = [
        "Ref($close, -1) / $close - 1",  # forward returns (t+1)
        "$amount",
        "$market_cap",
    ]
    df = D.features(inst_dict, fields=fields, start_time=start, end_time=end)
    df = _qlib_to_time_symbol(df)
    df.columns = ["returns_1d", "$amount", "$market_cap"]

    if cache_path:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(cache_path)
        logger.info("Cached market_daily to %s (%.1f MB)",
                     cache_path, cache_path.stat().st_size / 1024 / 1024)

    return df


# ---------------------------------------------------------------------------
# Library signals (for redundancy check)
# ---------------------------------------------------------------------------


def load_library_signals(
    paths: StoragePaths,
    start: str = "2015-01-01",
    end: str = "2023-12-31",
) -> dict[str, pd.DataFrame]:
    """Load all admitted factors' signals for redundancy check.

    Reads ``vault/factors/F*.yaml`` to get expressions, evaluates DSL
    factors via Qlib, and returns ``{factor_id: MultiIndex DataFrame}``.
    """
    factor_files = sorted(paths.factors_dir.glob("F*.yaml"))
    if not factor_files:
        return {}

    exprs: dict[str, str] = {}
    for f in factor_files:
        meta = load_yaml(f) or {}
        fid = meta.get("factor_id", f.stem)
        expr = meta.get("expression")
        source = meta.get("source_type", "dsl")
        if source == "dsl" and expr:
            exprs[fid] = expr

    if not exprs:
        return {}

    logger.info("Loading %d library signals for redundancy", len(exprs))
    series_dict = eval_dsl_batch(exprs, start=start, end=end)

    result = {}
    for fid, series in series_dict.items():
        df = series.to_frame(name="value")
        df.index.names = ["datetime", "instrument"]
        result[fid] = df

    return result


# ---------------------------------------------------------------------------
# Candidate signal evaluation
# ---------------------------------------------------------------------------


def evaluate_candidates(
    manifest: dict[str, Any],
    market_df: pd.DataFrame | None = None,
    start: str = "2015-01-01",
    end: str = "2023-12-31",
) -> list[CandidateInputs]:
    """Evaluate each candidate in the manifest and return CandidateInputs list.

    DSL candidates are evaluated via Qlib D.features().
    Python candidates are loaded and executed via python_runner.
    """
    from research.compute.python_runner import load_python_candidate, run_python_factor

    candidates = manifest.get("candidates", [])
    results: list[CandidateInputs] = []

    for cand in candidates:
        cid = cand["candidate_id"]
        source_type = cand.get("source_type", "dsl")
        expression = cand.get("expression", "")

        try:
            if source_type == "dsl":
                series = eval_dsl_expression(expression, start=start, end=end)
            else:
                py_ref = cand.get("python_ref", cand.get("path", ""))
                loaded = load_python_candidate(py_ref)
                if market_df is None:
                    raise ValueError("market_df required for Python candidates")
                series = run_python_factor(loaded, market_df)

            # Tradable mask: True where factor is not NaN
            tradable_mask = ~series.isna()

            results.append(CandidateInputs(
                candidate_id=cid,
                expression=expression or py_ref,
                source_type=source_type,
                factor_series=series,
                tradable_mask=tradable_mask,
            ))
        except Exception as exc:
            logger.error("Failed to evaluate %s: %s", cid, exc)
            # Create a dummy candidate with NaN series so Phase 2 records the error
            dummy = pd.Series(dtype=float, name=cid)
            dummy.index = pd.MultiIndex.from_tuples([], names=["time", "symbol"])
            results.append(CandidateInputs(
                candidate_id=cid,
                expression=expression,
                source_type=source_type,
                factor_series=dummy,
                tradable_mask=pd.Series(dtype=bool),
            ))

    return results


# ---------------------------------------------------------------------------
# Assembly: build_phase2_inputs
# ---------------------------------------------------------------------------


def build_phase2_inputs(
    batch_id: str,
    manifest: dict[str, Any],
    paths: StoragePaths,
    config: dict[str, Any],
) -> Phase2Inputs:
    """Assemble all data into a Phase2Inputs ready for run_phase2().

    This is the main entry point called by the mine loop's phase2_executor.
    """
    qlib_dir = config.get("qlib_data_dir", "~/.qlib/qlib_data/cn_data_1d")
    init_qlib(qlib_dir)

    sample = config.get("sample_policy", {})
    train_start, train_end = sample.get("train_range", ["2015-01-01", "2021-12-31"])
    val_start, val_end = sample.get("validation_range", ["2022-01-01", "2023-12-31"])
    full_start = train_start
    full_end = val_end

    # 1. Market data (returns, amount, market_cap)
    market = load_market_data(
        start=full_start, end=full_end,
        cache_path=paths.market_daily_cache,
    )

    # 2. Barra style matrix
    style_matrix = build_barra_style_matrix(
        start=full_start, end=full_end,
        cache_path=paths.barra_factors_cache,
    )

    # 3. Library signals
    library_signals = load_library_signals(paths, start=full_start, end=full_end)

    # 4. Candidate signals
    candidates = evaluate_candidates(
        manifest, start=full_start, end=full_end,
    )

    # 5. Extract single columns
    forward_returns_flat = market[["returns_1d"]].reset_index()
    forward_returns_flat.columns = ["time", "symbol", "value"]
    forward_returns_flat["time"] = pd.to_datetime(forward_returns_flat["time"])

    amount_data = market[["$amount"]].copy()
    amount_data.columns = ["$amount"]
    amount_data.index.names = ["datetime", "instrument"]

    market_cap_data = market[["$market_cap"]].copy()
    market_cap_data.columns = ["$market_cap"]
    market_cap_data.index.names = ["datetime", "instrument"]

    # 6. Preprocess config
    pp_cfg = config.get("preprocess", {})
    preprocess_config = PreprocessConfig(
        winsorize_mad_k=pp_cfg.get("winsorize_mad_k", 5),
        winsorize_mad_scale=pp_cfg.get("winsorize_mad_scale", 1.4826),
        zscore=pp_cfg.get("zscore", True),
    )

    return Phase2Inputs(
        batch_id=batch_id,
        candidates=candidates,
        forward_returns_flat=forward_returns_flat,
        style_matrix=style_matrix,
        library_signals=library_signals,
        amount_data=amount_data,
        market_cap=market_cap_data,
        train_range=(train_start, train_end),
        validation_range=(val_start, val_end),
        sample_policy_version=sample.get("sample_policy_version", "v3"),
        preprocess_config=preprocess_config,
    )


# ---------------------------------------------------------------------------
# phase2_executor callback for mine.py
# ---------------------------------------------------------------------------


def make_phase2_executor(config: dict[str, Any]):
    """Return a Phase2ExecutorCallback for use in mine.py's MineInputs.

    Usage::

        inputs = MineInputs(
            ...,
            phase2_executor=make_phase2_executor(config),
        )
    """

    def _executor(batch_id: str, paths: StoragePaths) -> None:
        manifest = load_yaml(paths.batch_manifest_file(batch_id))
        if not manifest:
            raise FileNotFoundError(f"manifest.yaml missing for {batch_id}")

        phase2_inputs = build_phase2_inputs(batch_id, manifest, paths, config)
        result_path = paths.batch_result_file(batch_id)
        run_phase2(phase2_inputs, result_path)
        logger.info("Phase 2 complete: %s", result_path)

    return _executor
