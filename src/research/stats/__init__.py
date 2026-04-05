"""Statistical computation functions for the research evidence engine.

Pure vectorized functions on DataFrames. No I/O, no Qlib.
"""

from research.stats.effect_strength import compute_effect_strength
from research.stats.stability import (
    compute_split_stability,
    compute_regime_stability,
    compute_sign_consistency,
    compute_train_validation_decay,
)
from research.stats.reliability import (
    compute_expanding_window_ic,
    compute_bootstrap_stability,
    compute_purged_walk_forward,
)
from research.stats.multiple_testing import (
    compute_multiple_testing_risk,
    compute_search_adjusted_strength,
)
from research.stats.risk_model import compute_risk_views
from research.stats.support_windows import check_support_windows
from research.stats.probe import run_probe

__all__ = [
    "compute_effect_strength",
    "compute_split_stability",
    "compute_regime_stability",
    "compute_sign_consistency",
    "compute_train_validation_decay",
    "compute_expanding_window_ic",
    "compute_bootstrap_stability",
    "compute_purged_walk_forward",
    "compute_multiple_testing_risk",
    "compute_search_adjusted_strength",
    "compute_risk_views",
    "check_support_windows",
    "run_probe",
]
