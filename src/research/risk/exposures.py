"""Barra exposure regression, residual IC, crowding detection.

Pure functions. No I/O, no Qlib.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

from core.factor_stats import daily_cross_sectional_ic, ic_summary, multiindex_to_flat
from .constants import (
    CROWDING_EXPOSURE_HIGH,
    CROWDING_EXPOSURE_MEDIUM,
    CROWDING_R2_HIGH,
    CROWDING_R2_MEDIUM,
    STYLE_NAMES,
    SURVIVAL_RAW_IC_MIN,
)


def compute_barra_exposures(
    factor_flat: pd.DataFrame,
    style_matrix: pd.DataFrame,
    forward_returns_flat: pd.DataFrame,
    raw_view_ic: float,
    min_obs: int = 50,
) -> Dict[str, Any]:
    """Full Barra exposure analysis.

    Parameters
    ----------
    factor_flat : [time, symbol, value] — evaluation_ready_signal converted to flat.
    style_matrix : (datetime, instrument) x N style columns, already normalized.
    forward_returns_flat : [time, symbol, value].
    raw_view_ic : pre-computed raw IC for survival ratio.
    min_obs : minimum stocks per date for OLS.

    Returns dict with style_exposures, style_r_squared, barra_residual_ic,
    barra_residual_icir, alpha_survival_ratio, dominant_style_exposure,
    style_crowding_risk.
    """
    if factor_flat.empty or style_matrix.empty:
        return _empty_result()

    style_cols = [c for c in style_matrix.columns if c in STYLE_NAMES]
    if not style_cols:
        return _empty_result()

    # Pivot factor to wide: (date x symbol)
    fv_wide = factor_flat.pivot(index="time", columns="symbol", values="value")

    # Align dates
    common_dates = fv_wide.index.intersection(style_matrix.index.get_level_values(0).unique())
    if len(common_dates) == 0:
        return _empty_result()

    # Pre-allocate residual wide DataFrame
    residual_wide = pd.DataFrame(np.nan, index=fv_wide.index, columns=fv_wide.columns)
    betas_per_date = []
    r2_per_date = []

    for date in common_dates:
        y = fv_wide.loc[date]
        if date not in style_matrix.index.get_level_values(0):
            continue

        style_day = style_matrix.loc[date]
        if isinstance(style_day, pd.Series):
            continue  # single row edge case

        # Align symbols
        common_syms = y.dropna().index.intersection(style_day.dropna(how="any").index)
        if len(common_syms) < min_obs:
            continue

        y_v = y.loc[common_syms].values.astype(float)
        X_styles = style_day.loc[common_syms][style_cols].values.astype(float)

        # Check for NaN in X
        valid_mask = np.isfinite(y_v) & np.all(np.isfinite(X_styles), axis=1)
        if valid_mask.sum() < min_obs:
            continue

        y_v = y_v[valid_mask]
        X_styles = X_styles[valid_mask]
        syms = common_syms[valid_mask]

        # OLS: y = intercept + X @ beta + residual
        X = np.column_stack([np.ones(len(y_v)), X_styles])
        try:
            beta, _, _, _ = np.linalg.lstsq(X, y_v, rcond=None)
            resid = y_v - X @ beta
            if not np.all(np.isfinite(resid)):
                continue
        except (np.linalg.LinAlgError, FloatingPointError):
            continue

        # R²
        ss_tot = np.var(y_v) * len(y_v)
        ss_res = np.var(resid) * len(resid)
        r2 = max(0.0, min(1.0, 1.0 - ss_res / max(ss_tot, 1e-12)))

        betas_per_date.append(beta[1:])  # exclude intercept
        r2_per_date.append(r2)

        # Direct assignment — no dict creation
        residual_wide.loc[date, syms] = resid

    if not betas_per_date:
        return _empty_result()

    # Aggregate exposures: mean(|beta|) per style
    beta_arr = np.array(betas_per_date)  # (n_dates, n_styles)
    style_exposures = {}
    for i, name in enumerate(style_cols):
        style_exposures[name] = float(np.mean(np.abs(beta_arr[:, i])))

    style_r_squared = float(np.median(r2_per_date))

    # Dominant style
    dominant_idx = int(np.argmax([style_exposures[n] for n in style_cols]))
    dominant_style = style_cols[dominant_idx]

    # Crowding
    style_crowding_risk = _classify_crowding(style_r_squared, style_exposures)

    # Convert residual wide to flat for IC computation
    residual_flat = residual_wide.stack().reset_index()
    residual_flat.columns = ["time", "symbol", "value"]
    residual_flat = residual_flat.dropna(subset=["value"])
    if residual_flat.empty:
        return _empty_result()

    residual_ic_series = daily_cross_sectional_ic(residual_flat, forward_returns_flat)
    if residual_ic_series.empty:
        barra_residual_ic = np.nan
        barra_residual_icir = np.nan
    else:
        ic_stats = ic_summary(residual_ic_series)
        barra_residual_ic = ic_stats.get("ic_mean", np.nan)
        barra_residual_icir = ic_stats.get("ic_ir", np.nan)

    # Survival ratio
    if (
        raw_view_ic is None
        or not np.isfinite(raw_view_ic)
        or abs(raw_view_ic) < SURVIVAL_RAW_IC_MIN
    ):
        alpha_survival = np.nan
    elif np.isfinite(barra_residual_ic):
        alpha_survival = abs(barra_residual_ic) / abs(raw_view_ic)
    else:
        alpha_survival = np.nan

    return {
        "style_exposures": style_exposures,
        "style_r_squared": style_r_squared,
        "barra_residual_ic": _safe_round(barra_residual_ic),
        "barra_residual_icir": _safe_round(barra_residual_icir),
        "alpha_survival_ratio": _safe_round(alpha_survival, 4),
        "dominant_style_exposure": dominant_style,
        "style_crowding_risk": style_crowding_risk,
    }


def _classify_crowding(r2: float, exposures: Dict[str, float]) -> str:
    max_exp = max(exposures.values()) if exposures else 0.0
    any_above_medium = any(v > CROWDING_EXPOSURE_MEDIUM for v in exposures.values())

    if r2 > CROWDING_R2_HIGH and max_exp > CROWDING_EXPOSURE_HIGH:
        return "high"
    if r2 > CROWDING_R2_MEDIUM or any_above_medium:
        return "medium"
    return "low"


def _safe_round(v: float, decimals: int = 6) -> Optional[float]:
    if v is None or not np.isfinite(v):
        return None
    return round(float(v), decimals)


def _empty_result() -> Dict[str, Any]:
    return {
        "style_exposures": {},
        "style_r_squared": None,
        "barra_residual_ic": None,
        "barra_residual_icir": None,
        "alpha_survival_ratio": None,
        "dominant_style_exposure": None,
        "style_crowding_risk": "low",
    }
