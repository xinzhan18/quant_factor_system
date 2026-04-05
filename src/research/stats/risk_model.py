"""Risk model views: raw / neutral / barra IC and alpha survival ratio.

Pure vectorized functions. No I/O, no Qlib.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

from core.factor_stats import daily_cross_sectional_ic


def _neutralize_cross_section(
    factor_wide: pd.DataFrame,
    market_cap_wide: pd.DataFrame,
    industry_wide: Optional[pd.DataFrame],
) -> pd.DataFrame:
    """Cross-sectionally neutralize factor values w.r.t. log-cap and industry.

    For each date:
      1. Regress factor on [log(market_cap), industry_dummies].
      2. Return residuals.

    Fully vectorized per-date using numpy lstsq.
    """
    result = factor_wide.copy()
    result[:] = np.nan

    for date in factor_wide.index:
        y = factor_wide.loc[date].values.astype(float)
        cap = market_cap_wide.loc[date].values.astype(float) if date in market_cap_wide.index else None

        if cap is None:
            continue

        valid = np.isfinite(y) & np.isfinite(cap) & (cap > 0)
        if valid.sum() < 30:
            continue

        log_cap = np.log(cap[valid])
        y_v = y[valid]

        # Build regressor matrix: intercept + log_cap [+ industry dummies]
        regressors = [np.ones(valid.sum()), log_cap]

        if industry_wide is not None and date in industry_wide.index:
            ind = industry_wide.loc[date].values[valid]
            # Dummies for all but the most common code
            unique_codes = np.unique(ind[np.isfinite(ind)])
            if len(unique_codes) > 1:
                for code in unique_codes[1:]:
                    regressors.append((ind == code).astype(float))

        X = np.column_stack(regressors)
        try:
            beta, _, _, _ = np.linalg.lstsq(X, y_v, rcond=None)
            resid = y_v - X @ beta
        except np.linalg.LinAlgError:
            continue

        full_resid = np.full(len(y), np.nan)
        full_resid[valid] = resid
        result.loc[date] = full_resid

    return result


def compute_risk_views(
    factor_values: pd.DataFrame,
    forward_returns: pd.DataFrame,
    market_cap: pd.DataFrame,
    industry: Optional[pd.DataFrame] = None,
    min_obs: int = 30,
) -> Dict[str, Any]:
    """Compute raw, cap-industry-neutral, and residual IC views.

    All inputs are flat DataFrames with columns [time, symbol, value].

    Args:
        factor_values: Factor values.
        forward_returns: Forward returns.
        market_cap: Market capitalisation values.
        industry: Optional industry codes (numeric).
        min_obs: Minimum observations per day.

    Returns:
        Dict with raw_ic, neutral_ic, alpha_survival_ratio.
    """
    # Raw IC
    raw_ic_series = daily_cross_sectional_ic(
        factor_values, forward_returns, min_obs=min_obs
    )
    raw_ic = float(raw_ic_series.mean()) if not raw_ic_series.empty else np.nan

    # Pivot factor values for neutralization
    merged = factor_values.merge(
        market_cap.rename(columns={"value": "cap"}), on=["time", "symbol"], how="inner"
    )
    if industry is not None:
        merged = merged.merge(
            industry.rename(columns={"value": "ind"}), on=["time", "symbol"], how="left"
        )

    if merged.empty:
        return {
            "raw_ic": round(raw_ic, 6) if np.isfinite(raw_ic) else np.nan,
            "neutral_ic": np.nan,
            "alpha_survival_ratio": np.nan,
        }

    fv_wide = merged.pivot(index="time", columns="symbol", values="value")
    cap_wide = merged.pivot(index="time", columns="symbol", values="cap")
    ind_wide = (
        merged.pivot(index="time", columns="symbol", values="ind")
        if industry is not None and "ind" in merged.columns
        else None
    )

    neutral_wide = _neutralize_cross_section(fv_wide, cap_wide, ind_wide)

    # Convert neutral back to flat for IC computation
    neutral_flat = neutral_wide.stack().reset_index()
    neutral_flat.columns = ["time", "symbol", "value"]
    neutral_flat = neutral_flat.dropna(subset=["value"])

    neutral_ic_series = daily_cross_sectional_ic(
        neutral_flat, forward_returns, min_obs=min_obs
    )
    neutral_ic = float(neutral_ic_series.mean()) if not neutral_ic_series.empty else np.nan

    # Alpha survival ratio: |neutral_ic| / |raw_ic|
    if np.isfinite(raw_ic) and abs(raw_ic) > 1e-8 and np.isfinite(neutral_ic):
        alpha_survival = abs(neutral_ic) / abs(raw_ic)
    else:
        alpha_survival = np.nan

    return {
        "raw_ic": round(raw_ic, 6) if np.isfinite(raw_ic) else np.nan,
        "neutral_ic": round(neutral_ic, 6) if np.isfinite(neutral_ic) else np.nan,
        "alpha_survival_ratio": (
            round(alpha_survival, 4) if np.isfinite(alpha_survival) else np.nan
        ),
    }
