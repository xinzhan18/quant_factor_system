"""Multiple testing risk and search-adjusted strength.

Pure functions. No I/O, no Qlib.
"""
from __future__ import annotations

from typing import Any, Dict

import numpy as np


def compute_multiple_testing_risk(
    family_attempts: int,
    logic_attempts: int,
    val_exposure: int,
) -> Dict[str, Any]:
    """Compute multiple-testing risk score and bucket.

    Formula:
        score = 0.50 * clip(log1p(family_attempts) / log(25), 0, 1)
              + 0.30 * clip(log1p(logic_attempts) / log(60), 0, 1)
              + 0.20 * clip(val_exposure / 12, 0, 1)

    Args:
        family_attempts: Cumulative family-level attempt count.
        logic_attempts: Cumulative logic-level attempt count.
        val_exposure: Number of times the validation window has been exposed.

    Returns:
        Dict with score and bucket (low / medium / high).
    """
    term_family = np.clip(np.log1p(family_attempts) / np.log(25), 0, 1)
    term_logic = np.clip(np.log1p(logic_attempts) / np.log(60), 0, 1)
    term_val = np.clip(val_exposure / 12, 0, 1)

    score = float(0.50 * term_family + 0.30 * term_logic + 0.20 * term_val)

    if score < 0.40:
        bucket = "low"
    elif score <= 0.70:
        bucket = "medium"
    else:
        bucket = "high"

    return {"score": round(score, 4), "bucket": bucket}


def compute_search_adjusted_strength(
    ic_mean: float,
    ic_ir: float,
    mono: float,
    expanding_pass: bool,
    mt_score: float,
) -> Dict[str, Any]:
    """Compute search-adjusted validation strength.

    raw = 0.40 * clip(|ic_mean| / 0.02, 0, 1)
        + 0.30 * clip(|ic_ir| / 0.20, 0, 1)
        + 0.20 * clip(|mono| / 0.40, 0, 1)
        + 0.10 * int(expanding_pass)

    adjusted = raw * (1 - 0.50 * mt_score)

    Args:
        ic_mean: Validation IC mean.
        ic_ir: Validation IC information ratio.
        mono: Validation monotonicity (Spearman corr of quintile returns).
        expanding_pass: Whether expanding-window IC passed.
        mt_score: Multiple-testing risk score (0-1).

    Returns:
        Dict with raw, adjusted, bucket (high / medium / low).
    """
    # Handle NaN inputs gracefully
    _ic = 0.0 if np.isnan(ic_mean) else ic_mean
    _ir = 0.0 if np.isnan(ic_ir) else ic_ir
    _mono = 0.0 if np.isnan(mono) else mono

    raw = (
        0.40 * np.clip(abs(_ic) / 0.02, 0, 1)
        + 0.30 * np.clip(abs(_ir) / 0.20, 0, 1)
        + 0.20 * np.clip(abs(_mono) / 0.40, 0, 1)
        + 0.10 * int(expanding_pass)
    )
    adjusted = float(raw * (1 - 0.50 * mt_score))

    if adjusted >= 0.70:
        bucket = "high"
    elif adjusted >= 0.40:
        bucket = "medium"
    else:
        bucket = "low"

    return {
        "raw": round(float(raw), 4),
        "adjusted": round(adjusted, 4),
        "bucket": bucket,
    }
