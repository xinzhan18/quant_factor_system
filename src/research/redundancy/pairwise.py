"""Layer 1: Pairwise duplication detection.

Computes cross-sectional rank correlations between a candidate signal and each
library factor, averaged across dates.  Pure functions, no I/O.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def _as_series(signal) -> pd.Series:
    """Extract a single-column DataFrame as a Series, or pass through."""
    if hasattr(signal, "ndim") and signal.ndim == 2:
        return signal.iloc[:, 0]
    return signal


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
            return np.nan
        return group["cand"].rank().corr(group["lib"].rank())

    return merged.groupby(level=0).apply(_corr).dropna()


def compute_pairwise_redundancy(
    candidate_signal: pd.DataFrame,
    library_signals: dict[str, pd.DataFrame],
    threshold: float = 0.7,
) -> dict:
    """Compute cross-sectional rank correlation between candidate and each
    library factor.

    Parameters
    ----------
    candidate_signal : DataFrame
        MultiIndex (datetime, instrument) with a single value column.
    library_signals : dict[str, DataFrame]
        ``{factor_id: DataFrame}`` for all admitted factors, same index shape.
    threshold : float
        Correlation threshold for ``is_near_duplicate`` flag (default 0.9 is
        only used by callers; the *threshold* parameter here controls the
        ``exceeds_threshold`` flag, while near-duplicate uses a hard 0.9).

    Returns
    -------
    dict with keys:
        max_lib_corr, nearest_factor_id, is_near_duplicate,
        exceeds_threshold, all_correlations
    """
    cand = _as_series(candidate_signal)

    all_corrs: dict[str, float] = {}
    for fid, lib_df in library_signals.items():
        lib_series = _as_series(lib_df)
        daily_corrs = _rank_corr_per_date(cand, lib_series)
        if daily_corrs.empty:
            all_corrs[fid] = np.nan
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

    # Use absolute correlation for finding the most similar factor.
    abs_corrs = {fid: abs(c) for fid, c in all_corrs.items() if not np.isnan(c)}
    if not abs_corrs:
        return {
            "max_lib_corr": 0.0,
            "nearest_factor_id": None,
            "is_near_duplicate": False,
            "exceeds_threshold": False,
            "all_correlations": all_corrs,
        }

    nearest_id = max(abs_corrs, key=abs_corrs.get)  # type: ignore[arg-type]
    max_corr = abs_corrs[nearest_id]

    return {
        "max_lib_corr": round(max_corr, 4),
        "nearest_factor_id": nearest_id,
        "is_near_duplicate": max_corr > 0.9,
        "exceeds_threshold": max_corr > threshold,
        "all_correlations": all_corrs,
    }


def batch_dedup(
    candidate_signals: dict[str, pd.DataFrame],
    threshold: float = 0.9,
) -> list[tuple]:
    """Identify near-duplicate pairs within a batch of candidates.

    Returns a list of ``(id_a, id_b, abs_corr)`` tuples where the
    absolute mean cross-sectional rank correlation exceeds *threshold*.
    """
    ids = list(candidate_signals.keys())
    pairs: list[tuple] = []

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
