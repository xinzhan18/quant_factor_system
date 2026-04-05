"""RiskEngine — the single entry point for risk review.

Orchestrates data fetching, caching, style factor computation,
exposure regression, cap neutralization, and bucket classification.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

from core.factor_stats import daily_cross_sectional_ic, ic_summary, multiindex_to_flat
from research.compute.data_provider import DataProvider

from .cache import RiskCache
from .constants import LOOKBACK_CALENDAR_DAYS, REQUIRED_FIELDS, SURVIVAL_RAW_IC_MIN
from .exposures import compute_barra_exposures
from .factors import compute_style_factor_matrix
from .neutralization import neutralize_cap
from .schema import RiskReview, compute_risk_bucket

logger = logging.getLogger(__name__)


class RiskEngine:
    """Self-contained risk review subsystem.

    Owns data fetching (via DataProvider), caching, and all computation.
    External consumers only see compute_risk_review() → RiskReview.
    """

    def __init__(
        self,
        data_provider: DataProvider,
        cache: Optional[RiskCache] = None,
    ) -> None:
        self.provider = data_provider
        self.cache = cache or RiskCache()

    def compute_risk_review(
        self,
        evaluation_ready_signal: pd.DataFrame,
        sample_policy: Dict[str, Any],
        profile: Dict[str, Any],
    ) -> RiskReview:
        """Compute full risk review for a candidate alpha factor.

        Parameters
        ----------
        evaluation_ready_signal : MultiIndex (datetime, instrument) DataFrame.
            The preprocessed alpha signal. Already winsorized + z-scored.
        sample_policy : dict with ``active_validation_range`` (date windows only).
        profile : dict with ``holding_horizon`` (computation config only).

        Returns
        -------
        RiskReview frozen dataclass with all fields populated (NaN where
        data is insufficient).
        """
        # Extract parameters
        val_range = sample_policy.get("active_validation_range", [])
        val_start = val_range[0] if len(val_range) > 0 else "2022-01-01"
        val_end = val_range[1] if len(val_range) > 1 else "2023-12-31"
        horizon = profile.get("holding_horizon", 5)

        # Convert signal to flat format
        factor_flat = multiindex_to_flat(evaluation_ready_signal)
        if factor_flat.empty:
            return RiskReview.stub()

        # Trim factor to validation window
        factor_flat = _trim_to_range(factor_flat, val_start, val_end)
        if factor_flat.empty:
            return RiskReview.stub()

        # Self-fetch forward returns (trimmed to validation)
        try:
            returns_mi = self.provider.get_returns(val_start, val_end, horizon=horizon)
            returns_flat = multiindex_to_flat(returns_mi)
        except Exception:
            logger.warning("Failed to fetch forward returns for risk review")
            returns_flat = pd.DataFrame(columns=["time", "symbol", "value"])

        if returns_flat.empty:
            return RiskReview.stub()

        # Raw IC
        raw_ic_series = daily_cross_sectional_ic(factor_flat, returns_flat)
        raw_ic_stats = ic_summary(raw_ic_series) if not raw_ic_series.empty else {}
        raw_view_ic = raw_ic_stats.get("ic_mean", np.nan)

        # Cap-neutral IC
        cap_neutral_ic = self._compute_cap_neutral_ic(
            factor_flat, returns_flat, val_start, val_end
        )

        # Style matrix (cached)
        style_matrix = self._get_style_matrix(val_start, val_end)
        if style_matrix is None or style_matrix.empty:
            # No style analysis possible — return partial result
            bucket = compute_risk_bucket(None, "low")
            return RiskReview(
                raw_view_ic=_safe(raw_view_ic),
                cap_industry_neutral_ic=_safe(cap_neutral_ic),
                risk_model_review_bucket=bucket,
            )

        # Barra exposure analysis
        barra = compute_barra_exposures(
            factor_flat=factor_flat,
            style_matrix=style_matrix,
            forward_returns_flat=returns_flat,
            raw_view_ic=raw_view_ic if np.isfinite(raw_view_ic) else 0.0,
        )

        # Compute bucket
        bucket = compute_risk_bucket(
            barra.get("alpha_survival_ratio"),
            barra.get("style_crowding_risk", "low"),
        )

        return RiskReview(
            raw_view_ic=_safe(raw_view_ic),
            cap_industry_neutral_ic=_safe(cap_neutral_ic),
            barra_residual_ic=barra.get("barra_residual_ic"),
            barra_residual_icir=barra.get("barra_residual_icir"),
            alpha_survival_ratio=barra.get("alpha_survival_ratio"),
            dominant_style_exposure=barra.get("dominant_style_exposure"),
            style_crowding_risk=barra.get("style_crowding_risk", "low"),
            style_r_squared=barra.get("style_r_squared"),
            style_exposures=barra.get("style_exposures", {}),
            risk_model_review_bucket=bucket,
        )

    # ------------------------------------------------------------------
    # Internal methods
    # ------------------------------------------------------------------

    def _get_style_matrix(self, val_start: str, val_end: str) -> Optional[pd.DataFrame]:
        """Get or compute cached style factor matrix."""
        universe_name = self.provider.universe.name

        cached = self.cache.get_style_matrix(universe_name, val_start, val_end)
        if cached is not None:
            return cached

        # Extend start for lookback (momentum needs 252 trading days)
        extended_start = _extend_start(val_start, LOOKBACK_CALENDAR_DAYS)

        try:
            market = self.provider.get_market_data(
                REQUIRED_FIELDS, extended_start, val_end
            )
        except Exception:
            logger.warning("Failed to fetch market data for style factors")
            return None

        if market.empty:
            return None

        matrix = compute_style_factor_matrix(
            close=market["$close"],
            circ_market_cap=market["$circ_market_cap"],
            pb_ratio=market["$pb_ratio"],
            pe_ratio=market["$pe_ratio"],
            turnover_rate=market["$turnover_rate"],
        )

        # Trim to validation range (remove lookback prefix)
        matrix = matrix.loc[val_start:]

        self.cache.put_style_matrix(universe_name, val_start, val_end, matrix)
        return matrix

    def _compute_cap_neutral_ic(
        self,
        factor_flat: pd.DataFrame,
        returns_flat: pd.DataFrame,
        val_start: str,
        val_end: str,
    ) -> float:
        """Compute cap-neutral IC. Cap-only; no industry provider yet."""
        try:
            cap_mi = self.provider.get_market_data(
                ["$circ_market_cap"], val_start, val_end
            )
        except Exception:
            return np.nan

        if cap_mi.empty:
            return np.nan

        # Pivot to wide
        fv_wide = factor_flat.pivot(index="time", columns="symbol", values="value")
        cap_wide = cap_mi.reset_index()
        if "instrument" in cap_wide.columns:
            cap_wide = cap_wide.rename(columns={"instrument": "symbol"})
        if "datetime" in cap_wide.columns:
            cap_wide = cap_wide.rename(columns={"datetime": "time"})

        # Handle MultiIndex cap_mi
        cap_flat = multiindex_to_flat(cap_mi)
        cap_pivot = cap_flat.pivot(index="time", columns="symbol", values="value")

        neutral_wide = neutralize_cap(fv_wide, cap_pivot)

        # Convert back to flat
        neutral_flat = neutral_wide.stack().reset_index()
        neutral_flat.columns = ["time", "symbol", "value"]
        neutral_flat = neutral_flat.dropna(subset=["value"])

        ic_series = daily_cross_sectional_ic(neutral_flat, returns_flat)
        if ic_series.empty:
            return np.nan
        return float(ic_series.mean())

    @classmethod
    def stub(cls) -> _StubRiskEngine:
        """Return a stub engine that produces RiskReview.stub() without data."""
        return _StubRiskEngine()


class _StubRiskEngine:
    """Stub that returns RiskReview.stub() for every call."""

    def compute_risk_review(self, *args, **kwargs) -> RiskReview:
        return RiskReview.stub()


def _extend_start(start: str, calendar_days: int) -> str:
    dt = datetime.strptime(start, "%Y-%m-%d") - timedelta(days=calendar_days)
    return dt.strftime("%Y-%m-%d")


def _trim_to_range(df: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    mask = (df["time"] >= pd.Timestamp(start)) & (df["time"] <= pd.Timestamp(end))
    return df.loc[mask].copy()


def _safe(v: float) -> Optional[float]:
    if v is None or not np.isfinite(v):
        return None
    return round(float(v), 6)
