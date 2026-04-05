"""Evaluation profile loader for research execute pipeline.

Reads ``research_eval_v1.yaml`` (or similar) from the evaluation_profiles
directory and returns a typed ``EvaluationProfile`` dict that the pipeline
uses for universe, preprocessing, neutralization, and sample policy settings.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Type alias -- keeps downstream code readable without adding a runtime dep
# ---------------------------------------------------------------------------
EvaluationProfile = Dict[str, Any]

# ---------------------------------------------------------------------------
# Defaults -- used when no YAML file is available (tests, bootstrap)
# ---------------------------------------------------------------------------
DEFAULT_PROFILE: EvaluationProfile = {
    "profile_id": "research_eval_v1",
    "universe_profile": "cn_all_tradable_v1",
    "tradability_profile": "cn_t1_limit_v1",
    "preprocess_profile": "default_rank_v1",
    "neutralization_profile": "cap_industry_barra_v1",
    "delay": 1,
    "holding_horizon": 5,
    "primary_pipeline": [
        "universe_mask",
        "tradability_mask",
        "winsorize",
        "zscore_or_rank",
        "neutralization",
    ],
    "auxiliary_views": [
        "raw_view",
        "cap_industry_neutral_view",
        "barra_residual_view",
    ],
}

DEFAULT_SAMPLE_POLICY: Dict[str, Any] = {
    "data_start": "2015-01-01",
    "active_train_range": ["2015-01-01", "2021-12-31"],
    "active_validation_range": ["2022-01-01", "2023-12-31"],
    "support_validation_windows": [
        {"window_id": "val_2020_2021", "range": ["2020-01-01", "2021-12-31"]},
        {"window_id": "val_2021_2022", "range": ["2021-01-01", "2022-12-31"]},
        {"window_id": "val_2022_2023", "range": ["2022-01-01", "2023-12-31"]},
    ],
    "holdout_pool_range": ["2024-01-01", "2025-12-31"],
    "holdout_used": False,
    "validation_policy_version": "research_sample_v3",
    "validation_window_id": "val_2022_2023",
}


def load_evaluation_profile(
    path: Optional[str | Path] = None,
) -> EvaluationProfile:
    """Load an evaluation profile from a YAML file.

    Parameters
    ----------
    path:
        Path to the YAML file.  When *None* the built-in default profile
        is returned (useful for tests and bootstrap).

    Returns
    -------
    EvaluationProfile
        A dictionary matching the schema described in
        ``docs/refacor_logic/research_execute.md`` section 4.1.
    """
    if path is None:
        logger.debug("No evaluation profile path given; returning default profile")
        return dict(DEFAULT_PROFILE)

    filepath = Path(path)
    if not filepath.exists():
        logger.warning(
            "Evaluation profile not found at %s; using defaults", filepath
        )
        return dict(DEFAULT_PROFILE)

    with open(filepath, "r") as fh:
        raw = yaml.safe_load(fh) or {}

    # The file may nest the profile under a top-level key
    profile = raw.get("evaluation_profile", raw)

    # Merge with defaults so optional keys always exist
    merged: EvaluationProfile = {**DEFAULT_PROFILE, **profile}
    logger.info("Loaded evaluation profile '%s' from %s", merged.get("profile_id"), filepath)
    return merged


def load_sample_policy(
    path: Optional[str | Path] = None,
) -> Dict[str, Any]:
    """Load sample policy from YAML, falling back to built-in defaults."""
    if path is None:
        return dict(DEFAULT_SAMPLE_POLICY)

    filepath = Path(path)
    if not filepath.exists():
        logger.warning("Sample policy not found at %s; using defaults", filepath)
        return dict(DEFAULT_SAMPLE_POLICY)

    with open(filepath, "r") as fh:
        raw = yaml.safe_load(fh) or {}

    policy = raw.get("sample_policy", raw)
    merged = {**DEFAULT_SAMPLE_POLICY, **policy}
    return merged
