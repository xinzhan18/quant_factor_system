"""Research configuration loader.

Single source of truth: ``storage/governance/research_config.yaml``.

All skills, CLI commands, and pipeline code should call
``load_research_config()`` to get the full config, then extract
the section they need (evaluation_profile, sample_policy, etc.).

``load_evaluation_profile()`` and ``load_sample_policy()`` are
convenience wrappers that extract their respective sections.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Type alias
# ---------------------------------------------------------------------------
EvaluationProfile = Dict[str, Any]

# ---------------------------------------------------------------------------
# Canonical config path
# ---------------------------------------------------------------------------
RESEARCH_CONFIG_PATH = Path("storage/governance/research_config.yaml")

# ---------------------------------------------------------------------------
# Hardcoded fallbacks — used ONLY when the YAML file is missing (tests, CI)
# ---------------------------------------------------------------------------
_FALLBACK_CONFIG: Dict[str, Any] = {
    "universe": "csi1000",
    "qlib_data_dir": "~/.qlib/qlib_data/cn_data_1d",
    "evaluation_profile": {
        "profile_id": "research_eval_v1",
        "delay": 1,
        "holding_horizon": 5,
    },
    "sample_policy": {
        "data_start": "2015-01-01",
        "active_train_range": ["2015-01-01", "2021-12-31"],
        "active_validation_range": ["2022-01-01", "2023-12-31"],
        "support_validation_windows": [
            {"window_id": "val_2020_2021", "range": ["2020-01-01", "2021-12-31"]},
            {"window_id": "val_2021_2022", "range": ["2021-01-01", "2022-12-31"]},
            {"window_id": "val_2022_2023", "range": ["2022-01-01", "2023-12-31"]},
        ],
        "holdout_pool_range": ["2024-01-01", "2025-12-31"],
        "holdout_used": True,
        "validation_policy_version": "research_sample_v3",
    },
    "thresholds": {
        "ic_threshold": 0.01,
        "correlation_threshold": 0.7,
    },
    "probe": {
        "start": "2019-01-01",
        "end": "2023-12-31",
    },
}

# Module-level cache so the file is read at most once per process
_cached_config: Optional[Dict[str, Any]] = None


def load_research_config(
    path: Optional[str | Path] = None,
) -> Dict[str, Any]:
    """Load the unified research config from YAML.

    Parameters
    ----------
    path : str | Path, optional
        Explicit path.  When *None*, uses ``RESEARCH_CONFIG_PATH``.

    Returns
    -------
    dict — full research config with all sections.
    """
    global _cached_config
    if _cached_config is not None and path is None:
        return _cached_config

    filepath = Path(path) if path else RESEARCH_CONFIG_PATH
    if filepath.exists():
        with open(filepath, "r") as fh:
            raw = yaml.safe_load(fh) or {}
        # Merge with fallbacks so missing keys are filled
        config = _deep_merge(_FALLBACK_CONFIG, raw)
        logger.info("Loaded research config from %s", filepath)
    else:
        logger.warning("Research config not found at %s; using fallbacks", filepath)
        config = dict(_FALLBACK_CONFIG)

    if path is None:
        _cached_config = config
    return config


# ---------------------------------------------------------------------------
# Convenience accessors (used by existing code)
# ---------------------------------------------------------------------------

def load_evaluation_profile(
    path: Optional[str | Path] = None,
) -> EvaluationProfile:
    """Load the evaluation profile section from research config.

    If *path* points to a standalone profile YAML, load that instead.
    """
    config = load_research_config()
    profile = dict(config.get("evaluation_profile", {}))
    # Inject top-level universe into profile for backward compat
    profile.setdefault("universe", config.get("universe", "csi1000"))

    # If an explicit path is given, overlay its contents
    if path is not None:
        filepath = Path(path)
        if filepath.exists():
            with open(filepath, "r") as fh:
                raw = yaml.safe_load(fh) or {}
            overlay = raw.get("evaluation_profile", raw)
            profile.update(overlay)

    return profile


def load_sample_policy(
    path: Optional[str | Path] = None,
) -> Dict[str, Any]:
    """Load the sample policy section from research config."""
    config = load_research_config()
    policy = dict(config.get("sample_policy", {}))

    if path is not None:
        filepath = Path(path)
        if filepath.exists():
            with open(filepath, "r") as fh:
                raw = yaml.safe_load(fh) or {}
            overlay = raw.get("sample_policy", raw)
            policy.update(overlay)

    return policy


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _deep_merge(base: Dict, overlay: Dict) -> Dict:
    """Recursively merge overlay into base (overlay wins on conflict)."""
    result = dict(base)
    for k, v in overlay.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result
