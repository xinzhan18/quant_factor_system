"""Composite 7-dim scorer — pure function over result.yaml scalars.

Outputs 7 sub-scores [0..100] + overall score + letter grade.
No plotting, no IO — called by the renderer and by the radar chart.
"""
from __future__ import annotations


def _scale(x: float | None, lo: float, hi: float) -> float:
    """Linearly map abs(x) in [lo, hi] to [0, 100], clipped."""
    if x is None:
        return 0.0
    try:
        v = (abs(x) - lo) / (hi - lo)
    except ZeroDivisionError:
        return 0.0
    return max(0.0, min(100.0, v * 100.0))


def compute_composite(candidate: dict) -> dict:
    ic = (candidate.get("ic") or {}).get("validation") or {}
    icir = ic.get("ic_ir") or 0.0

    q_val = (candidate.get("quintile") or {}).get("validation") or {}
    mono = q_val.get("monotonicity") or 0.0
    ls_val = ((candidate.get("quintile") or {}).get("ls_stats") or {}).get("validation") or {}
    sharpe = ls_val.get("sharpe") or 0.0

    stab = ((candidate.get("stability") or {}).get("split_stability") or {})
    sign_consist = stab.get("sign_consistency") or 0.0

    uniq = candidate.get("uniqueness") or {}
    max_corr = uniq.get("max_lib_corr") or 0.0
    is_dup = uniq.get("is_near_duplicate", False)

    tv_decay = (candidate.get("ic") or {}).get("train_validation_decay") or 0.0

    by_h = (candidate.get("ic") or {}).get("by_horizon") or {}
    ic_1d = ((by_h.get(1) or by_h.get("1") or {}).get("validation") or {}).get("ic_mean") or 0.0
    ic_longest = 0.0
    for blk in by_h.values():
        val = ((blk or {}).get("validation") or {}).get("ic_mean")
        if val is not None and abs(val) > abs(ic_longest):
            ic_longest = val
    if abs(ic_1d) < 1e-9:
        decay_resist = 100.0 if abs(ic_longest) > 0 else 0.0
    else:
        decay_resist = _scale(abs(ic_longest) / max(abs(ic_1d), 1e-9), 1.0, 2.5)

    sub = {
        "predictive_power": _scale(abs(icir), 0.15, 0.55),
        "signal_stability": 100.0 * float(sign_consist),
        "profitability": _scale(abs(sharpe), 1.0, 4.0),
        "monotonicity": _scale(abs(mono), 0.5, 1.0),
        "oos_robustness": _scale(abs(tv_decay), 0.5, 1.2),
        "uniqueness": 0.0 if is_dup else _scale(1.0 - abs(max_corr), 0.1, 0.9),
        "decay_resistance": decay_resist,
    }
    score = sum(sub.values()) / 7.0
    grade = "A" if score >= 75 else "B" if score >= 60 else "C" if score >= 45 else "D"
    return {**sub, "score": round(score, 1), "grade": grade}
