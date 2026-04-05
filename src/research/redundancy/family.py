"""Layer 2: Family-level redundancy detection.

Computes family_overlap_score from three components:
  - same_family_corr_p90
  - structure_overlap_score
  - residual_survival_ratio

Pure functions, no I/O.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from research.redundancy.pairwise import _as_series, _rank_corr_per_date


def _bucket(score: float) -> str:
    """Map family_overlap_score to a bucket label."""
    if score < 0.45:
        return "low"
    elif score <= 0.70:
        return "medium"
    else:
        return "high"


def _compute_member_abs_corrs(
    candidate_signal: pd.DataFrame,
    family_members: dict[str, pd.DataFrame],
) -> list[float]:
    """Compute |mean_daily_rank_corr| between candidate and each family member.

    Returns a list of absolute mean correlations (one per member).
    """
    cand = _as_series(candidate_signal)
    abs_mean_corrs: list[float] = []
    for _fid, member_df in family_members.items():
        member = _as_series(member_df)
        daily_corrs = _rank_corr_per_date(cand, member)
        if not daily_corrs.empty:
            abs_mean_corrs.append(abs(float(daily_corrs.mean())))
    return abs_mean_corrs


def _compute_structure_overlap(
    candidate_structure: dict,
    family_registry_entry: dict,
) -> float:
    """Overlap of structure_template, conditioning_type, horizon_bucket.

    Returns (number_of_matches) / 3, in [0, 1].
    """
    keys = ["structure_template", "conditioning_type", "horizon_bucket"]
    matches = 0
    for key in keys:
        cand_val = candidate_structure.get(key)
        reg_val = family_registry_entry.get(key)
        if cand_val is not None and reg_val is not None and cand_val == reg_val:
            matches += 1
    return matches / 3.0


def compute_family_overlap(
    candidate_signal: pd.DataFrame,
    family_members: dict[str, pd.DataFrame],
    candidate_structure: dict,
    family_registry_entry: dict,
) -> dict:
    """Compute family-level redundancy score.

    Parameters
    ----------
    candidate_signal : DataFrame
        MultiIndex (datetime, instrument), single value column.
    family_members : dict[str, DataFrame]
        ``{factor_id: DataFrame}`` for same-family admitted factors.
    candidate_structure : dict
        Must contain keys: structure_template, conditioning_type, horizon_bucket.
    family_registry_entry : dict
        Family registry row with the same three keys.

    Returns
    -------
    dict with keys:
        family_overlap_score, family_overlap_bucket,
        same_family_corr_p90, structure_overlap_score,
        residual_survival_ratio, family_size,
        family_history_status
    """
    family_size = len(family_members)

    if family_size == 0:
        return {
            "family_overlap_score": 0.0,
            "family_overlap_bucket": "low",
            "same_family_corr_p90": 0.0,
            "structure_overlap_score": 0.0,
            "residual_survival_ratio": 1.0,
            "family_size": 0,
            "family_history_status": "insufficient",
        }

    # Compute member correlations once, reuse for both p90 and residual ratio.
    abs_corrs = _compute_member_abs_corrs(candidate_signal, family_members)

    corr_p90 = float(np.percentile(abs_corrs, 90)) if abs_corrs else 0.0
    residual_ratio = float(1.0 - max(abs_corrs)) if abs_corrs else 1.0

    struct_overlap = _compute_structure_overlap(candidate_structure, family_registry_entry)

    # 0.50 * same_family_corr_p90
    # + 0.30 * structure_overlap_score
    # + 0.20 * (1 - clip(residual_survival_ratio, 0, 1))
    clipped_residual = float(np.clip(residual_ratio, 0.0, 1.0))
    score = (
        0.50 * corr_p90
        + 0.30 * struct_overlap
        + 0.20 * (1.0 - clipped_residual)
    )

    history_status = "sufficient" if family_size >= 2 else "insufficient"

    return {
        "family_overlap_score": round(score, 4),
        "family_overlap_bucket": _bucket(score),
        "same_family_corr_p90": round(corr_p90, 4),
        "structure_overlap_score": round(struct_overlap, 4),
        "residual_survival_ratio": round(residual_ratio, 4),
        "family_size": family_size,
        "family_history_status": history_status,
    }
