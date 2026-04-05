"""RiskReview schema — the single evidence object for risk analysis."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import math


@dataclass(frozen=True)
class RiskReview:
    """Immutable risk review result produced by RiskEngine."""

    raw_view_ic: Optional[float] = None
    cap_industry_neutral_ic: Optional[float] = None  # cap-only degradation; name kept for doc alignment
    barra_residual_ic: Optional[float] = None
    barra_residual_icir: Optional[float] = None
    alpha_survival_ratio: Optional[float] = None
    dominant_style_exposure: Optional[str] = None
    style_crowding_risk: str = "low"
    style_r_squared: Optional[float] = None
    style_exposures: Dict[str, float] = field(default_factory=dict)
    risk_model_review_bucket: str = "acceptable"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "raw_view_ic": self.raw_view_ic,
            "cap_industry_neutral_ic": self.cap_industry_neutral_ic,
            "barra_residual_ic": self.barra_residual_ic,
            "barra_residual_icir": self.barra_residual_icir,
            "alpha_survival_ratio": self.alpha_survival_ratio,
            "dominant_style_exposure": self.dominant_style_exposure,
            "style_crowding_risk": self.style_crowding_risk,
            "style_r_squared": self.style_r_squared,
            "style_exposures": dict(self.style_exposures),
            "risk_model_review_bucket": self.risk_model_review_bucket,
        }

    @classmethod
    def stub(cls) -> RiskReview:
        """Return a valid stub with NaN values and acceptable bucket."""
        return cls(
            raw_view_ic=None,
            cap_industry_neutral_ic=None,
            barra_residual_ic=None,
            barra_residual_icir=None,
            alpha_survival_ratio=None,
            dominant_style_exposure=None,
            style_crowding_risk="low",
            style_r_squared=None,
            style_exposures={},
            risk_model_review_bucket="acceptable",
        )


def compute_risk_bucket(
    alpha_survival: Optional[float],
    crowding: str,
) -> str:
    """Classify risk review into acceptable / borderline / poor.

    Bucket is computed inside the risk subsystem — downstream consumers
    (judge packet, candidate judge) read it directly.
    """
    survival_bad = (
        alpha_survival is not None
        and not math.isnan(alpha_survival)
        and alpha_survival < 0.3
    )
    survival_borderline = (
        alpha_survival is not None
        and not math.isnan(alpha_survival)
        and alpha_survival < 0.6
    )

    if survival_bad or crowding == "high":
        return "poor"
    if survival_borderline or crowding == "medium":
        return "borderline"
    return "acceptable"
