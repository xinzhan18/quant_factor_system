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

from research.compute.cache import FactorValueCache
from research.compute.preprocess import PreprocessConfig
from research.phases.phase2_execute import CandidateInputs, Phase2Inputs, run_phase2
from research.storage.paths import StoragePaths
from research.storage.yaml_io import load_yaml

# Full cache window. Library/candidate DSL signals are materialized once
# across this entire window and sliced on read, so different batch time
# ranges all share one cached expression → key-stable.
CACHE_FULL_START = "2015-01-01"
CACHE_FULL_END = "2025-12-31"

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
    """Convert Qlib's (instrument, datetime) MultiIndex to (datetime, instrument).

    Qlib D.features() returns MultiIndex with level 0 = instrument (str),
    level 1 = datetime. Phase 2 expects (datetime, instrument) with datetime time.
    """
    if not isinstance(df.index, pd.MultiIndex):
        return df
    # Qlib order: (instrument, datetime) → swap to (datetime, instrument)
    df = df.swaplevel()
    df.index.names = ["datetime", "instrument"]
    df = df.sort_index()
    # Ensure datetime level is datetime
    dt_level = df.index.get_level_values("datetime")
    if not pd.api.types.is_datetime64_any_dtype(dt_level):
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


DEFAULT_DECAY_HORIZONS: list[int] = [1, 3, 5, 10, 20]


def _returns_col(h: int) -> str:
    """Column name for h-day forward returns."""
    return f"returns_{h}d"


def load_market_data(
    start: str = "2015-01-01",
    end: str = "2023-12-31",
    cache_path: Path | None = None,
    decay_horizons: list[int] | None = None,
) -> pd.DataFrame:
    """Load market data fields needed by Phase 2.

    Returns DataFrame with MultiIndex (time, symbol) and columns:
    ``returns_1d``, ``returns_3d``, ..., ``$amount``, ``$market_cap``.

    If *cache_path* provided, reads from / writes to parquet.  When the
    cache exists but is missing required horizon columns it is rebuilt
    automatically.
    """
    if decay_horizons is None:
        decay_horizons = list(DEFAULT_DECAY_HORIZONS)

    required_cols = (
        {_returns_col(h) for h in decay_horizons}
        | {"$amount", "$market_cap", "$close", "$volume"}
    )

    if cache_path and cache_path.exists():
        logger.info("Loading cached market_daily from %s", cache_path)
        df = pd.read_parquet(cache_path)
        if isinstance(df.index, pd.MultiIndex):
            time_level = df.index.get_level_values(0)
            if not pd.api.types.is_datetime64_any_dtype(time_level):
                df.index = df.index.set_levels(pd.to_datetime(df.index.levels[0]), level=0)
        # If cache is missing required columns, rebuild
        if required_cols.issubset(set(df.columns)):
            return df
        logger.info("Cache missing columns %s — rebuilding",
                     required_cols - set(df.columns))

    logger.info("Loading market data from Qlib (%s to %s, horizons=%s)",
                start, end, decay_horizons)
    from qlib.data import D

    inst_dict = D.instruments("all")
    # One D.features call for all horizons + amount + market_cap + raw close/volume
    fields = (
        [f"Ref($close, -{h}) / $close - 1" for h in decay_horizons]
        + ["$amount", "$market_cap", "$close", "$volume"]
    )
    df = D.features(inst_dict, fields=fields, start_time=start, end_time=end)
    df = _qlib_to_time_symbol(df)
    df.columns = (
        [_returns_col(h) for h in decay_horizons]
        + ["$amount", "$market_cap", "$close", "$volume"]
    )

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
    market_df: pd.DataFrame | None = None,
) -> dict[str, pd.DataFrame]:
    """Load all admitted factors' signals for redundancy check.

    Two source types contribute:

    * **DSL factors** — ``vault/factors/F*.yaml`` with ``source_type=dsl``.
      Computed via :func:`eval_dsl_batch` and cached per ``sha256(expr)``
      key in ``FactorValueCache``.
    * **Python factors** (R8 escape hatch) — ``source_type=python``, whose
      ``python_path`` points to a validated Python factor module. Executed
      via :mod:`research.compute.python_runner` against ``market_df``.
      Cached per ``sha256(module source)`` key.

    Both kinds land in the same ``{factor_id: MultiIndex DataFrame}`` dict
    so downstream pairwise-redundancy treats them uniformly. Without this,
    a Python candidate that replicates an already-admitted Python factor
    sails past the ``near_duplicate`` hard gate (see F004/F005 incident:
    library only held DSL factors, so the Python replica's max_lib_corr
    was ~0.15 against DSL neighbours instead of ~1.0 against its twin).

    Parameters
    ----------
    market_df
        Time-symbol MultiIndex market data needed to execute Python
        factors. Required iff any admitted factor has ``source_type=python``.
    """
    factor_files = sorted(paths.factors_dir.glob("F*.yaml"))
    if not factor_files:
        return {}

    dsl_expr_by_fid: dict[str, str] = {}
    py_path_by_fid: dict[str, Path] = {}
    for f in factor_files:
        meta = load_yaml(f) or {}
        fid = meta.get("factor_id", f.stem)
        source = meta.get("source_type", "dsl")
        if source == "dsl":
            expr = meta.get("expression")
            if expr:
                dsl_expr_by_fid[fid] = expr
        elif source == "python":
            py_ref = meta.get("python_path")
            if py_ref:
                py_path_by_fid[fid] = Path(py_ref)

    if not dsl_expr_by_fid and not py_path_by_fid:
        return {}

    cache = FactorValueCache(paths.factor_values_cache_dir)
    result: dict[str, pd.DataFrame] = {}

    # --- DSL factors (cached per expression hash) ---
    misses: dict[str, str] = {}
    for fid, expr in dsl_expr_by_fid.items():
        key = cache.make_key(expr)
        hit = cache.get_slice(key, start=start, end=end)
        if hit is not None:
            result[fid] = hit
        else:
            misses[fid] = expr

    if misses:
        logger.info(
            "library DSL cache: %d/%d hit, %d miss — computing",
            len(result), len(dsl_expr_by_fid), len(misses),
        )
        full_series = eval_dsl_batch(
            misses, start=CACHE_FULL_START, end=CACHE_FULL_END,
        )
        for fid, series in full_series.items():
            full_df = series.to_frame(name="value")
            full_df.index.names = ["datetime", "instrument"]
            cache.put(cache.make_key(misses[fid]), full_df)
            level0 = full_df.index.get_level_values(0)
            mask = (level0 >= pd.Timestamp(start)) & (level0 <= pd.Timestamp(end))
            result[fid] = full_df.loc[mask]
    elif dsl_expr_by_fid:
        logger.info(
            "library DSL cache: %d/%d hit (full cache)",
            len(result), len(dsl_expr_by_fid),
        )

    # --- Python factors (cached per module-source hash) ---
    if py_path_by_fid:
        if market_df is None:
            raise ValueError(
                "load_library_signals: market_df is required when the "
                f"library contains Python factors ({sorted(py_path_by_fid)})"
            )
        from research.compute.python_runner import (
            load_python_candidate, run_python_factor,
        )

        py_hit = 0
        for fid, py_path in py_path_by_fid.items():
            if not py_path.exists():
                logger.warning(
                    "library Python factor %s source missing: %s — skipped",
                    fid, py_path,
                )
                continue
            source_text = py_path.read_text(encoding="utf-8")
            key = cache.make_key(source_text)
            hit = cache.get_slice(key, start=start, end=end)
            if hit is not None:
                result[fid] = hit
                py_hit += 1
                continue
            loaded = load_python_candidate(py_path)
            series = run_python_factor(loaded, market_df)
            full_df = series.to_frame(name="value")
            full_df.index.names = ["datetime", "instrument"]
            cache.put(key, full_df)
            level0 = full_df.index.get_level_values(0)
            mask = (level0 >= pd.Timestamp(start)) & (level0 <= pd.Timestamp(end))
            result[fid] = full_df.loc[mask]
        logger.info(
            "library Python: %d/%d cache hit",
            py_hit, len(py_path_by_fid),
        )

    return result


# ---------------------------------------------------------------------------
# Candidate signal evaluation
# ---------------------------------------------------------------------------


def evaluate_candidates(
    manifest: dict[str, Any],
    paths: StoragePaths | None = None,
    market_df: pd.DataFrame | None = None,
    start: str = "2015-01-01",
    end: str = "2023-12-31",
) -> list[CandidateInputs]:
    """Evaluate each candidate in the manifest and return CandidateInputs list.

    DSL candidates hit the full-window ``FactorValueCache`` keyed on
    ``sha256(expression)``; misses are computed over
    ``[CACHE_FULL_START, CACHE_FULL_END]`` and persisted, then sliced
    to ``[start, end]``. Python candidates are loaded and executed via
    python_runner without caching (closures are not key-stable).
    """
    from research.compute.python_runner import load_python_candidate, run_python_factor

    candidates = manifest.get("candidates", [])
    results: list[CandidateInputs] = []

    cache = (
        FactorValueCache(paths.factor_values_cache_dir) if paths is not None else None
    )

    # First pass: collect DSL expressions that miss the cache so we can
    # batch-evaluate them in one Qlib call.
    dsl_misses: dict[str, str] = {}  # candidate_id → expr
    dsl_hits: dict[str, pd.Series] = {}  # candidate_id → sliced series
    for cand in candidates:
        if cand.get("source_type", "dsl") != "dsl":
            continue
        expr = cand.get("expression", "")
        if not expr or cache is None:
            continue
        key = cache.make_key(expr)
        hit = cache.get_slice(key, start=start, end=end)
        if hit is not None and not hit.empty:
            dsl_hits[cand["candidate_id"]] = hit.iloc[:, 0]
        else:
            dsl_misses[cand["candidate_id"]] = expr

    # Compute misses over the full window in one Qlib call
    dsl_full_series: dict[str, pd.Series] = {}
    if dsl_misses:
        dsl_full_series = eval_dsl_batch(
            dsl_misses, start=CACHE_FULL_START, end=CACHE_FULL_END,
        )
        if cache is not None:
            for cid, full_series in dsl_full_series.items():
                full_df = full_series.to_frame(name="value")
                full_df.index.names = ["datetime", "instrument"]
                cache.put(cache.make_key(dsl_misses[cid]), full_df)

    for cand in candidates:
        cid = cand["candidate_id"]
        source_type = cand.get("source_type", "dsl")
        expression = cand.get("expression", "")
        py_ref = ""

        try:
            if source_type == "dsl":
                if cid in dsl_hits:
                    series = dsl_hits[cid]
                elif cid in dsl_full_series:
                    full = dsl_full_series[cid]
                    level0 = full.index.get_level_values(0)
                    mask = (
                        (level0 >= pd.Timestamp(start))
                        & (level0 <= pd.Timestamp(end))
                    )
                    series = full.loc[mask]
                else:
                    # Fallback path (no cache / no expr): direct eval
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

    eval_cfg = config.get("evaluation", {})
    decay_horizons = eval_cfg.get("decay_horizons", DEFAULT_DECAY_HORIZONS)
    primary_horizon = eval_cfg.get("primary_horizon", 5)

    # 1. Market data (multi-horizon returns + amount + market_cap)
    market = load_market_data(
        start=full_start, end=full_end,
        cache_path=paths.market_daily_cache,
        decay_horizons=decay_horizons,
    )

    # 2. Barra style matrix
    style_matrix = build_barra_style_matrix(
        start=full_start, end=full_end,
        cache_path=paths.barra_factors_cache,
    )

    # 3. Library signals (DSL + Python — both contribute to redundancy)
    library_signals = load_library_signals(
        paths, start=full_start, end=full_end, market_df=market,
    )

    # 4. Candidate signals
    candidates = evaluate_candidates(
        manifest, paths=paths, market_df=market, start=full_start, end=full_end,
    )

    # 5. Extract per-horizon forward returns as flat DataFrames
    def _extract_returns(col: str) -> pd.DataFrame:
        df = market[[col]].reset_index()
        df.columns = ["time", "symbol", "value"]
        df["time"] = pd.to_datetime(df["time"])
        return df

    # Resolve primary horizon: must exist in decay_horizons
    if primary_horizon not in decay_horizons:
        primary_horizon = decay_horizons[0]

    forward_returns_by_horizon = {
        h: _extract_returns(_returns_col(h)) for h in decay_horizons
    }

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

    universe = config.get("universe") or config.get("universes", {}).get("primary", "csi1000")

    return Phase2Inputs(
        batch_id=batch_id,
        candidates=candidates,
        forward_returns_by_horizon=forward_returns_by_horizon,
        primary_horizon=int(primary_horizon),
        style_matrix=style_matrix,
        library_signals=library_signals,
        amount_data=amount_data,
        market_cap=market_cap_data,
        train_range=(train_start, train_end),
        validation_range=(val_start, val_end),
        preprocess_config=preprocess_config,
        universe=universe,
        paths=paths,
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
