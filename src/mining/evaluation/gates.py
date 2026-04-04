"""Hard-gate filter applied after Stage 3 report-card computation.

These gates are non-negotiable — they cannot be overridden by LLM judge
or any manual flag.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Tuple

from ..config import MiningConfig

logger = logging.getLogger(__name__)


def apply_hard_gates(
    screened: List[Dict[str, Any]], config: MiningConfig
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Post-Stage3 hard gates. Returns (passed, gated)."""
    passed, gated = [], []
    for c in screened:
        rc = c.get("report_card", {})
        reasons: List[Dict[str, Any]] = []

        if rc.get("ic_sign_consistent") is False:
            reasons.append({"code": "ic_sign_flip", "value": None})

        decay = rc.get("oos_decay_ratio")
        if decay is not None and decay < config.hard_gate_oos_decay_min:
            reasons.append({"code": "oos_decay_too_low",
                            "value": round(decay, 3),
                            "threshold": config.hard_gate_oos_decay_min})

        cov = rc.get("coverage")
        if cov is not None and cov < config.hard_gate_coverage_min:
            reasons.append({"code": "coverage_too_low",
                            "value": round(cov, 3),
                            "threshold": config.hard_gate_coverage_min})

        mono_is = rc.get("monotonicity_is")
        mono_oos = rc.get("monotonicity_oos")
        if (mono_is is not None and mono_oos is not None
                and mono_is != 0 and mono_oos != 0
                and (mono_is * mono_oos < 0)):
            reasons.append({"code": "mono_sign_flip",
                            "value": {"is": round(mono_is, 2),
                                      "oos": round(mono_oos, 2)}})

        ic_oos_val = rc.get("ic_mean_oos")
        if ic_oos_val is not None and abs(ic_oos_val) < config.hard_gate_ic_oos_min:
            reasons.append({"code": "ic_oos_too_low",
                            "value": round(abs(ic_oos_val), 4),
                            "threshold": config.hard_gate_ic_oos_min})

        if reasons:
            c["hard_gate_reject"] = reasons
            gated.append(c)
            logger.info("Hard gate reject %s: %s",
                        c["name"], [r["code"] for r in reasons])
        else:
            passed.append(c)
    return passed, gated
