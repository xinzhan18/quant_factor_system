"""Vectorized stability diagnostics — CP06 Validation Stability inputs.

Two families of tests on the IC series:

* **split stability** — partition validation into ``n_splits`` equal chunks
  and emit raw per-chunk IC means, sign-consistency ratio, and dispersion
  (CV). The judge LLM interprets these raw numbers; Python no longer
  classifies them into high/medium/low buckets.
* **simple 2-series helpers** — ``sign_consistency`` and
  ``train_validation_decay`` which are tiny utilities consumed by the
  Phase 2 orchestrator.

All functions are pure (no I/O, no Qlib).
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


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
    n_splits``. ``n_splits == 0`` signals that the validation window was
    too short to split — callers should treat missing sign_consistency /
    dispersion as "unknown", not "bad".
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

    return {
        "split_ic_means": split_means,
        "sign_consistency": round(sign_consistency, 4),
        "dispersion": round(dispersion, 4),
        "n_splits": len(chunks),
    }


def _insufficient_splits() -> dict[str, Any]:
    return {
        "split_ic_means": [],
        "sign_consistency": None,
        "dispersion": None,
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
    """Signed decay ratio ``val / train`` — values < 1 indicate decay.

    Returns NaN if ``train ≈ 0``. Sign is preserved so sign flips are
    visible as negative decay (e.g. ``train=0.05, val=-0.02 → -0.4``).
    """
    if abs(ic_train_mean) < 1e-10:
        return float("nan")
    return ic_val_mean / ic_train_mean
