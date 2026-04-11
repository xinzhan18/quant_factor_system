"""Vectorized IC computation — Phase 2 interface over ``core.factor_stats``.

``core.factor_stats.daily_cross_sectional_ic`` is already the fully
vectorized reference implementation (pivot → rank → matrix Pearson, no
per-date Python loop). This module is a thin orchestration wrapper that:

1. runs IC on train and validation slices,
2. returns a structured dict ready to be merged into ``result.yaml``,
3. optionally runs support-window flip checks.

The "核心数学" lives in ``core/``, which is not deprecated — importing it
from new P1 code is explicitly allowed (only ``research.{logic,governance,
feasibility,redundancy,risk,stats}`` are forbidden by R9).
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from core.factor_stats import daily_cross_sectional_ic, ic_summary


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
    """``ic_mean / ic_std / ic_ir / ic_win_rate`` for one IC series."""
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
    """Train / validation IC metrics in one structured dict.

    Returns a shape identical to what ``result.yaml`` will hold for the
    "effect_strength" block, plus the raw IC series (not persisted into
    YAML but passed to downstream stability / reliability modules).
    """
    fv_train = _filter_range(factor_flat, *train_range)
    fr_train = _filter_range(returns_flat, *train_range)
    fv_val = _filter_range(factor_flat, *validation_range)
    fr_val = _filter_range(returns_flat, *validation_range)

    ic_train = compute_ic_series(fv_train, fr_train, min_obs=min_obs)
    ic_val = compute_ic_series(fv_val, fr_val, min_obs=min_obs)

    train_stats = compute_ic_stats(ic_train)
    val_stats = compute_ic_stats(ic_val)

    return {
        "train": train_stats,
        "validation": val_stats,
        # Raw series carried forward for stability / support_windows
        "ic_series_train": ic_train,
        "ic_series_validation": ic_val,
    }


def compute_support_windows(
    factor_flat: pd.DataFrame,
    returns_flat: pd.DataFrame,
    primary_sign: float,
    windows: list[dict[str, Any]],
    min_obs: int = 30,
) -> dict[str, Any]:
    """Run IC checks on support validation windows and detect sign flips.

    Replaces the old ``research.stats.support_windows.check_support_windows``.

    Parameters
    ----------
    factor_flat, returns_flat
        Flat ``[time, symbol, value]`` frames.
    primary_sign
        +1 or -1 — the sign of the IC mean from the primary validation
        window. Used as reference for flip detection.
    windows
        List of ``{"window_id": str, "range": [start, end]}`` dicts.
    min_obs
        Minimum cross-sectional observations per day.

    Returns
    -------
    dict
        ``{"checks": [per-window dicts], "warning": "none"|"single_flip"|
        "repeated_flip"}``
    """
    checks: list[dict[str, Any]] = []
    n_flips = 0

    for win in windows:
        wid = win["window_id"]
        start, end = win["range"][0], win["range"][1]

        fv = _filter_range(factor_flat, start, end)
        fr = _filter_range(returns_flat, start, end)

        ic_series = compute_ic_series(fv, fr, min_obs=min_obs)
        if ic_series.empty:
            checks.append(
                {
                    "window_id": wid,
                    "ic_mean_support": None,
                    "sign_consistent": False,
                }
            )
            continue

        ic_mean = float(ic_series.mean())
        sign_ok = (
            bool(np.sign(ic_mean) == np.sign(primary_sign))
            if abs(ic_mean) > 1e-10
            else False
        )
        if not sign_ok:
            n_flips += 1

        checks.append(
            {
                "window_id": wid,
                "ic_mean_support": round(ic_mean, 6),
                "sign_consistent": sign_ok,
            }
        )

    if n_flips == 0:
        warning = "none"
    elif n_flips == 1:
        warning = "single_flip"
    else:
        warning = "repeated_flip"

    return {"checks": checks, "warning": warning}
