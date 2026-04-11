"""Vectorized stability diagnostics — CP06 Validation Stability inputs.

Three families of tests on the validation IC series:

* **split stability** — partition validation into ``n_splits`` equal chunks
  and check per-chunk IC sign consistency + dispersion (drives
  ``split_stability_bucket`` in ``result.yaml``).
* **expanding-window IC** — expand a window from ``start`` outward and check
  whether the cumulative IC mean stays same-sign as the final window
  (drives ``expanding_window_pass``).
* **simple 2-series helpers** — ``sign_consistency`` and
  ``train_validation_decay`` which are tiny utilities consumed by the
  Phase 2 orchestrator.

All functions are pure (no I/O, no Qlib). They are extracted from the
legacy ``research.stats.{stability,reliability}`` modules with
behaviour-preserving edits:

* type-annotated for Python 3.10+
* removed unused "bucket" strings that depended on deprecated thresholds
* unified return dicts to what ``result.yaml`` actually consumes

The computations were already vectorized in the legacy code — no
performance-relevant changes. Golden tests verify numerical equivalence.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from core.factor_stats import daily_cross_sectional_ic


# ---------------------------------------------------------------------------
# Split stability
# ---------------------------------------------------------------------------


def compute_split_stability(
    ic_series: pd.Series,
    n_splits: int = 4,
    min_days: int = 60,
) -> dict[str, Any]:
    """Split the IC series into equal periods and assess stability.

    Parameters
    ----------
    ic_series
        Daily IC values with DatetimeIndex (possibly sparse — missing days
        are dropped).
    n_splits
        Target number of equal-length splits. Falls back to ``n_splits - 1``
        if 4 splits don't each meet ``min_days``.
    min_days
        Minimum trading days per split.

    Returns
    -------
    dict with keys: ``split_ic_means, sign_consistency, dispersion,
    bucket, n_splits``. ``bucket`` is one of ``"high"``, ``"medium"``,
    ``"low"``, ``"insufficient_splits"``.
    """
    ic = ic_series.dropna().sort_index()
    if ic.empty:
        return _insufficient_splits()

    # Try n_splits first, fall back to n_splits - 1.
    for n in (n_splits, n_splits - 1):
        if n < 3:
            return _insufficient_splits()
        chunks = np.array_split(ic.values, n)
        if all(len(c) >= min_days for c in chunks):
            break
    else:
        return _insufficient_splits()

    split_means = [float(np.mean(c)) for c in chunks]
    overall_mean = float(np.mean(ic.values))

    # Sign consistency: fraction of splits sharing sign with the overall mean
    if abs(overall_mean) < 1e-10:
        sign_consistency = 0.0
    else:
        target_sign = np.sign(overall_mean)
        sign_consistency = sum(
            1 for m in split_means if np.sign(m) == target_sign
        ) / len(split_means)

    # Dispersion: std of split means normalized by |mean of split means|
    dispersion = float(
        np.std(split_means, ddof=0) / (abs(np.mean(split_means)) + 1e-6)
    )

    if sign_consistency >= 0.75 and dispersion <= 0.75:
        bucket = "high"
    elif sign_consistency >= 0.50 and dispersion <= 1.25:
        bucket = "medium"
    else:
        bucket = "low"

    return {
        "split_ic_means": split_means,
        "sign_consistency": round(sign_consistency, 4),
        "dispersion": round(dispersion, 4),
        "bucket": bucket,
        "n_splits": len(chunks),
    }


def _insufficient_splits() -> dict[str, Any]:
    return {
        "split_ic_means": [],
        "sign_consistency": None,
        "dispersion": None,
        "bucket": "insufficient_splits",
        "n_splits": 0,
    }


# ---------------------------------------------------------------------------
# Train ↔ validation consistency
# ---------------------------------------------------------------------------


def compute_sign_consistency(
    ic_train: pd.Series, ic_validation: pd.Series
) -> bool:
    """Whether train and validation IC means share the same sign.

    Returns ``False`` if either series is empty or has near-zero mean.
    """
    t_mean = ic_train.dropna().mean() if not ic_train.empty else 0.0
    v_mean = (
        ic_validation.dropna().mean() if not ic_validation.empty else 0.0
    )
    if abs(t_mean) < 1e-10 or abs(v_mean) < 1e-10:
        return False
    return bool(np.sign(t_mean) == np.sign(v_mean))


def compute_train_validation_decay(
    ic_train_mean: float, ic_val_mean: float
) -> float:
    """``|val| / |train|`` — values < 1 indicate decay, NaN if train ≈ 0."""
    if abs(ic_train_mean) < 1e-10:
        return float("nan")
    return abs(ic_val_mean) / abs(ic_train_mean)


# ---------------------------------------------------------------------------
# Expanding-window IC stability
# ---------------------------------------------------------------------------


def compute_expanding_window_ic(
    factor_flat: pd.DataFrame,
    returns_flat: pd.DataFrame,
    start: str,
    step_months: int = 6,
    min_obs: int = 30,
) -> dict[str, Any]:
    """Expand training window from *start* in steps, compute cumulative IC.

    At each step the window grows by ``step_months`` months and we compute
    IC over the entire window up to that point. Returns the full path plus
    a ``pass`` flag used by CP06.
    """
    start_ts = pd.Timestamp(start)
    fv = factor_flat.loc[factor_flat["time"] >= start_ts]
    fr = returns_flat.loc[returns_flat["time"] >= start_ts]

    if fv.empty or fr.empty:
        return _empty_expanding()

    max_date = fv["time"].max()
    path: list[dict[str, Any]] = []

    end = start_ts + pd.DateOffset(months=step_months)
    while end <= max_date:
        fv_win = fv.loc[fv["time"] <= end]
        fr_win = fr.loc[fr["time"] <= end]
        ic_series = daily_cross_sectional_ic(fv_win, fr_win, min_obs=min_obs)
        if not ic_series.empty:
            path.append(
                {
                    "end_date": str(end.date()),
                    "ic_mean": float(ic_series.mean()),
                }
            )
        end += pd.DateOffset(months=step_months)

    if len(path) < 2:
        return _empty_expanding(path=path)

    ic_means = np.array([p["ic_mean"] for p in path])

    final_sign = np.sign(ic_means[-1])
    if final_sign == 0:
        sign_consistency = 0.0
    else:
        sign_consistency = float(np.mean(np.sign(ic_means) == final_sign))

    std = float(np.std(ic_means, ddof=1)) if len(ic_means) > 1 else 0.0
    mean_abs = abs(float(np.mean(ic_means)))
    cv = std / (mean_abs + 1e-8)
    stability = float(np.clip(1.0 - cv, 0.0, 1.0))

    if abs(ic_means[0]) < 1e-10:
        decay_ratio: float | None = None
    else:
        decay_ratio = float(abs(ic_means[-1]) / abs(ic_means[0]))

    passed = bool(sign_consistency >= 0.6 and stability >= 0.3)

    return {
        "path": path,
        "stability": round(stability, 4),
        "sign_consistency": round(sign_consistency, 4),
        "decay_ratio": round(decay_ratio, 4) if decay_ratio is not None else None,
        "pass": passed,
    }


def _empty_expanding(path: list | None = None) -> dict[str, Any]:
    return {
        "path": path or [],
        "stability": None,
        "sign_consistency": None,
        "decay_ratio": None,
        "pass": False,
    }
