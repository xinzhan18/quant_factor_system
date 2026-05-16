"""Report-time holdout quintile compute.

Phase 2/3 never see the holdout period — that is the discipline of the
4-fold split (``train ≤ 2021``, ``validation 2022–2023``, ``holdout 2024``).
The report layer is the *only* place where holdout data is allowed to
enter the picture, by design.

This module re-evaluates a factor's DSL expression on the holdout window,
applies the same preprocess + tradable-mask + quintile pipeline as Phase 2,
and returns a ``q1..q5`` daily-return DataFrame matching the schema of
``quantile_daily_train.parquet`` / ``quantile_daily_validation.parquet`` —
so chart code can splice the three regions as truly homogeneous data.

Python-source factors return ``None`` (their compute path goes through
``python_runner`` which is heavier; wire that in only when needed).

A factor-local parquet cache at
``vault/factors/F{id}/holdout_quintile_daily.parquet`` makes re-renders
free after the first run.
"""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

# Calendar-day buffer prepended to the eval window so rolling operators
# (Mean/Std/Cov/Corr/TsRank etc.) have full lookback at holdout_start.
# 250 calendar days ≈ 170 trading days — covers the longest current
# window (Cov(..., 120) in F075).
_DEFAULT_LOOKBACK_DAYS = 250


def compute_holdout_quintile_returns(
    expression: str,
    source_type: str,
    holdout_start: str,
    holdout_end: str,
    *,
    factor_dir: Path | None = None,
    lookback_days: int = _DEFAULT_LOOKBACK_DAYS,
    use_cache: bool = True,
) -> pd.DataFrame | None:
    """Compute raw quintile daily returns on the holdout window.

    Parameters
    ----------
    expression
        DSL string (Qlib-evaluable). Source-of-truth in ``F{id}.yaml.expression``.
    source_type
        ``"dsl"`` or ``"python"``. Python factors are not yet supported here.
    holdout_start, holdout_end
        ISO date strings (``YYYY-MM-DD``).
    factor_dir
        If given, cache the result at ``factor_dir / "holdout_quintile_daily.parquet"``.
    lookback_days, use_cache
        See module docstring.

    Returns
    -------
    DataFrame
        Indexed by datetime, columns ``q1..q5``, values = daily return of
        the equal-weight stock basket in that quintile. ``None`` when the
        factor is not DSL-evaluable.
    """
    if source_type != "dsl":
        logger.info(
            "holdout quintile compute skipped: source_type=%s not supported",
            source_type,
        )
        return None

    cache_path = (
        factor_dir / "holdout_quintile_daily.parquet"
        if factor_dir is not None
        else None
    )
    if use_cache and cache_path is not None and cache_path.exists():
        return pd.read_parquet(cache_path)

    from research.compute.data_bridge import (
        init_qlib, eval_dsl_expression, load_market_data,
    )
    from research.compute.masks import build_tradable_mask
    from research.compute.preprocess import PreprocessConfig, preprocess_factor
    from research.compute.vectorized_quintile import compute_quintile_returns

    init_qlib()

    lookback_start = (
        pd.Timestamp(holdout_start) - pd.Timedelta(days=lookback_days)
    ).strftime("%Y-%m-%d")

    logger.info(
        "Holdout compute: evaluating %r over [%s, %s] (lookback %dd)",
        expression, lookback_start, holdout_end, lookback_days,
    )
    factor_series = eval_dsl_expression(
        expression, start=lookback_start, end=holdout_end,
    )

    market_df = load_market_data(
        start=lookback_start, end=holdout_end, decay_horizons=[1],
        cache_path=None,  # Holdout slice is small; in-memory load is fine
    )
    tradable_mask = build_tradable_mask(market_df)

    clean = preprocess_factor(
        factor_series, PreprocessConfig(), tradable_mask=tradable_mask,
    )

    h0, h1 = pd.Timestamp(holdout_start), pd.Timestamp(holdout_end)
    factor_flat = clean.dropna().reset_index()
    factor_flat.columns = ["time", "symbol", "value"]
    factor_flat = factor_flat[(factor_flat["time"] >= h0) & (factor_flat["time"] <= h1)]

    returns_flat = market_df["returns_1d"].reset_index()
    returns_flat.columns = ["time", "symbol", "value"]
    returns_flat = returns_flat[
        (returns_flat["time"] >= h0) & (returns_flat["time"] <= h1)
    ]

    qret = compute_quintile_returns(factor_flat, returns_flat)
    per_q = qret["per_quintile_daily"]

    if cache_path is not None:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        per_q.to_parquet(cache_path)
        logger.info("Cached holdout quintile to %s", cache_path)

    return per_q
