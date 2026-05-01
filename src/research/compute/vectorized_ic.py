"""Vectorized IC computation — Phase 2 interface over ``core.factor_stats``.

``core.factor_stats.daily_cross_sectional_ic`` is the fully vectorized
reference implementation (pivot → rank → matrix Pearson, no per-date
Python loop). This module orchestrates IC at three scopes:

1. **Single-slice IC** — ``compute_ic_series`` + ``compute_ic_stats`` for
   one flat ``[time, symbol, value]`` panel.
2. **Train / validation effect strength** — ``compute_effect_strength``
   runs IC on both splits and returns the dict consumed by
   ``result.yaml.candidates[].ic.{train,validation}``.
3. **Multi-horizon + analytics** — ``compute_multi_horizon_ic`` runs IC
   for every forward-return horizon on both train and validation;
   ``compute_ic_analytics`` derives by-year / autocorr / cum-IC drawdown
   / best-worst quarter from an IC series;
   ``compute_ic_half_life`` maps the per-horizon train IC means into a
   half-life estimate via ``core.factor_stats.estimate_half_life``.

All functions are pure and stateless. Every metric is produced exactly
once — upstream callers must not re-run ``compute_ic_series`` on the
same slice.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from core.factor_stats import (
    daily_cross_sectional_ic,
    daily_cross_sectional_ic_from_wides,
    estimate_half_life,
    ic_by_year,
    ic_summary,
)
from core.metrics import max_drawdown


def _filter_range(df: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    """Inclusive date-range filter on a flat ``[time, symbol, value]`` frame."""
    mask = (df["time"] >= pd.Timestamp(start)) & (df["time"] <= pd.Timestamp(end))
    return df.loc[mask]


def compute_ic_series(
    factor_flat: pd.DataFrame,
    returns_flat: pd.DataFrame,
    min_obs: int = 30,
    method: str = "spearman",
) -> pd.Series:
    """Daily cross-sectional IC as a ``DatetimeIndex`` Series."""
    return daily_cross_sectional_ic(
        factor_flat, returns_flat, method=method, min_obs=min_obs
    )


def compute_ic_stats(ic_series: pd.Series) -> dict[str, float]:
    """``ic_mean / ic_std / ic_ir / ic_win_rate / n_days`` for one IC series."""
    stats = ic_summary(ic_series)
    return {
        "ic_mean": stats["ic_mean"],
        "ic_std": stats["ic_std"],
        "ic_ir": stats["ic_ir"],
        "ic_win_rate": stats["ic_win_rate"],
        "n_days": int(len(ic_series)),
    }


def compute_effect_strength(
    factor_flat: pd.DataFrame,
    returns_flat: pd.DataFrame,
    train_range: tuple[str, str],
    validation_range: tuple[str, str],
    min_obs: int = 30,
) -> dict[str, Any]:
    """Train / validation IC stats + raw IC series for downstream stability.

    Returns
    -------
    dict
        ``{"train": stats, "validation": stats, "ic_series_train": Series,
        "ic_series_validation": Series}``
    """
    fv_train = _filter_range(factor_flat, *train_range)
    fr_train = _filter_range(returns_flat, *train_range)
    fv_val = _filter_range(factor_flat, *validation_range)
    fr_val = _filter_range(returns_flat, *validation_range)

    ic_train = compute_ic_series(fv_train, fr_train, min_obs=min_obs)
    ic_val = compute_ic_series(fv_val, fr_val, min_obs=min_obs)

    return {
        "train": compute_ic_stats(ic_train),
        "validation": compute_ic_stats(ic_val),
        "ic_series_train": ic_train,
        "ic_series_validation": ic_val,
    }


def compute_multi_horizon_ic(
    factor_flat: pd.DataFrame,
    returns_by_horizon: dict[int, pd.DataFrame],
    train_range: tuple[str, str],
    validation_range: tuple[str, str],
    min_obs: int = 30,
    *,
    returns_wides_by_horizon: dict[int, pd.DataFrame] | None = None,
) -> dict[int, dict[str, Any]]:
    """Multi-horizon IC on train + validation.

    Pivots the candidate's factor exactly once into wide format, then
    reuses it across every (horizon × split) IC call. When
    ``returns_wides_by_horizon`` is provided, the per-horizon returns
    pivot is also skipped — Phase 2 caches both once per batch.

    Returns
    -------
    dict[int, dict]
        ``{h: {"train": stats, "validation": stats, "ic_series_train":
        Series, "ic_series_validation": Series}}``
    """
    factor_wide = (
        factor_flat
        .set_index(["time", "symbol"])["value"]
        .unstack(level=-1)
    )
    factor_wide.index = pd.DatetimeIndex(factor_wide.index)
    train_start, train_end = (pd.Timestamp(train_range[0]), pd.Timestamp(train_range[1]))
    val_start, val_end = (pd.Timestamp(validation_range[0]), pd.Timestamp(validation_range[1]))
    fv_train_wide = factor_wide.loc[train_start:train_end]
    fv_val_wide = factor_wide.loc[val_start:val_end]

    out: dict[int, dict[str, Any]] = {}
    for h, ret_flat in returns_by_horizon.items():
        if returns_wides_by_horizon is not None and int(h) in returns_wides_by_horizon:
            ret_wide = returns_wides_by_horizon[int(h)]
        else:
            ret_wide = (
                ret_flat.set_index(["time", "symbol"])["value"].unstack(level=-1)
            )
            ret_wide.index = pd.DatetimeIndex(ret_wide.index)
        fr_train_wide = ret_wide.loc[train_start:train_end]
        fr_val_wide = ret_wide.loc[val_start:val_end]

        ic_train = daily_cross_sectional_ic_from_wides(
            fv_train_wide, fr_train_wide, min_obs=min_obs,
        )
        ic_val = daily_cross_sectional_ic_from_wides(
            fv_val_wide, fr_val_wide, min_obs=min_obs,
        )

        out[int(h)] = {
            "train": compute_ic_stats(ic_train),
            "validation": compute_ic_stats(ic_val),
            "ic_series_train": ic_train,
            "ic_series_validation": ic_val,
        }
    return out


def compute_ic_analytics(ic_series: pd.Series) -> dict[str, Any]:
    """Derive by-year, autocorr, cumulative-IC MDD, best/worst quarter.

    Input is a ``DatetimeIndex`` series (train + validation concatenated
    is conventional for by_year, but any IC series works).

    Returns
    -------
    dict
        ``{"by_year": dict, "autocorr_lag1": float|None,
        "cum_ic_max_drawdown": float|None,
        "best_quarter": float|None, "worst_quarter": float|None}``
    """
    if ic_series is None or ic_series.empty:
        return {
            "by_year": {},
            "autocorr_lag1": None,
            "cum_ic_max_drawdown": None,
            "best_quarter": None,
            "worst_quarter": None,
        }

    by_year = ic_by_year(ic_series)

    arr = ic_series.dropna().values.astype(float)
    autocorr_lag1: float | None
    if len(arr) > 2:
        c = np.corrcoef(arr[:-1], arr[1:])[0, 1]
        autocorr_lag1 = float(c) if np.isfinite(c) else None
    else:
        autocorr_lag1 = None

    cum_ic_mdd = float(max_drawdown(ic_series.cumsum()))
    if not np.isfinite(cum_ic_mdd):
        cum_ic_mdd_out: float | None = None
    else:
        cum_ic_mdd_out = round(cum_ic_mdd, 6)

    quarterly = ic_series.groupby(
        [ic_series.index.year, ic_series.index.quarter]
    ).mean()
    if len(quarterly) == 0:
        best_q: float | None = None
        worst_q: float | None = None
    else:
        best_q = float(quarterly.max())
        worst_q = float(quarterly.min())

    return {
        "by_year": by_year,
        "autocorr_lag1": round(autocorr_lag1, 6) if autocorr_lag1 is not None else None,
        "cum_ic_max_drawdown": cum_ic_mdd_out,
        "best_quarter": round(best_q, 6) if best_q is not None else None,
        "worst_quarter": round(worst_q, 6) if worst_q is not None else None,
    }


def compute_ic_half_life(ic_means_by_horizon: dict[int, float]) -> float | None:
    """IC-decay half-life from a per-horizon mean IC dict.

    Thin wrapper over ``core.factor_stats.estimate_half_life`` that
    filters non-finite entries and returns ``None`` instead of NaN.
    """
    clean = {
        int(h): float(v)
        for h, v in ic_means_by_horizon.items()
        if v is not None and np.isfinite(v)
    }
    if len(clean) < 2:
        return None
    hl = estimate_half_life(clean)
    if hl is None or not np.isfinite(hl):
        return None
    return round(float(hl), 4)
