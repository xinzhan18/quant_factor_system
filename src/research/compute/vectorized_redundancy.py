"""Vectorized pairwise redundancy — CP05 inputs.

Thin re-implementation of the legacy ``research.redundancy.pairwise``:

* cross-sectional Spearman rank correlation per date, averaged
* candidate-vs-library pairwise with a ``nearest_factor_id`` summary
* batch-level dedup to flag near-duplicate candidates within one batch

The old pairwise module already uses the right per-date structure
(``groupby(level=0).apply(_corr)``). The speedup on large panels comes
not from within a single pair but from avoiding N² pair overhead. We
keep the same math so the golden fixture matches bit-for-bit.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def _as_series(signal: pd.DataFrame | pd.Series) -> pd.Series:
    """Extract a single-column DataFrame as a Series, or pass through."""
    if hasattr(signal, "ndim") and signal.ndim == 2:
        return signal.iloc[:, 0]
    return signal  # type: ignore[return-value]


def _rank_corr_per_date(
    candidate: pd.Series,
    library_factor: pd.Series,
) -> pd.Series:
    """Cross-sectional Spearman rank correlation for each date.

    Both inputs must share a (datetime, instrument) MultiIndex.
    Returns a Series indexed by date with one correlation per row.
    """
    merged = pd.concat(
        [candidate.rename("cand"), library_factor.rename("lib")],
        axis=1,
    ).dropna()

    if merged.empty:
        return pd.Series(dtype=float)

    def _corr(group: pd.DataFrame) -> float:
        if len(group) < 5:
            return float("nan")
        return group["cand"].rank().corr(group["lib"].rank())

    return merged.groupby(level=0).apply(_corr).dropna()


def compute_pairwise_redundancy(
    candidate_signal: pd.DataFrame | pd.Series,
    library_signals: dict[str, pd.DataFrame | pd.Series],
    threshold: float = 0.7,
) -> dict[str, Any]:
    """Candidate-vs-library cross-sectional rank correlation summary.

    Parameters
    ----------
    candidate_signal
        MultiIndex (datetime, instrument), single value column (or Series).
    library_signals
        ``{factor_id: DataFrame}`` for all admitted factors.
    threshold
        Absolute correlation cutoff for the ``exceeds_threshold`` flag
        (typically ``config.thresholds.max_lib_corr_high == 0.70``).

    Returns
    -------
    dict with keys ``max_lib_corr, nearest_factor_id, is_near_duplicate,
    exceeds_threshold, all_correlations``. ``is_near_duplicate`` is
    hardcoded at ``|corr| > 0.9`` (a stricter gate than
    ``exceeds_threshold``).
    """
    cand = _as_series(candidate_signal)

    all_corrs: dict[str, float] = {}
    for fid, lib_df in library_signals.items():
        lib_series = _as_series(lib_df)
        daily_corrs = _rank_corr_per_date(cand, lib_series)
        if daily_corrs.empty:
            all_corrs[fid] = float("nan")
        else:
            all_corrs[fid] = float(daily_corrs.mean())

    if not all_corrs:
        return {
            "max_lib_corr": 0.0,
            "nearest_factor_id": None,
            "is_near_duplicate": False,
            "exceeds_threshold": False,
            "all_correlations": {},
        }

    abs_corrs = {
        fid: abs(c) for fid, c in all_corrs.items() if not np.isnan(c)
    }
    if not abs_corrs:
        return {
            "max_lib_corr": 0.0,
            "nearest_factor_id": None,
            "is_near_duplicate": False,
            "exceeds_threshold": False,
            "all_correlations": all_corrs,
        }

    nearest_id = max(abs_corrs, key=lambda k: abs_corrs[k])
    max_corr = abs_corrs[nearest_id]

    return {
        "max_lib_corr": round(max_corr, 4),
        "nearest_factor_id": nearest_id,
        "is_near_duplicate": max_corr > 0.9,
        "exceeds_threshold": max_corr > threshold,
        "all_correlations": all_corrs,
    }


def batch_dedup(
    candidate_signals: dict[str, pd.DataFrame | pd.Series],
    threshold: float = 0.9,
) -> list[tuple[str, str, float]]:
    """Identify near-duplicate pairs within a batch of candidates.

    Returns a list of ``(id_a, id_b, abs_corr)`` tuples where the
    absolute mean cross-sectional rank correlation exceeds *threshold*.
    """
    ids = list(candidate_signals.keys())
    pairs: list[tuple[str, str, float]] = []

    for i in range(len(ids)):
        s_i = _as_series(candidate_signals[ids[i]])
        for j in range(i + 1, len(ids)):
            s_j = _as_series(candidate_signals[ids[j]])
            daily_corrs = _rank_corr_per_date(s_i, s_j)
            if daily_corrs.empty:
                continue
            abs_corr = abs(float(daily_corrs.mean()))
            if abs_corr > threshold:
                pairs.append((ids[i], ids[j], round(abs_corr, 4)))

    return pairs
