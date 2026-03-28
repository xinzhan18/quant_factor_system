"""6-dimension factor evaluation metrics.

Computes a comprehensive FactorReportCard from raw factor/return data.
All functions are stateless — they take data and return metrics.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from core.metrics import ic_summary_from_series, max_drawdown as compute_max_drawdown

logger = logging.getLogger(__name__)

NaN = float("nan")


# ──────────────────── FactorReportCard ────────────────────


@dataclass
class FactorReportCard:
    """6-dimension factor evaluation report card."""

    # --- Dimension 1: Predictive Power ---
    ic_mean: float = NaN
    ic_std: float = NaN
    ic_ir: float = NaN
    ic_win_rate: float = NaN
    ic_by_year: Dict[int, float] = field(default_factory=dict)
    ic_by_month: Dict[int, float] = field(default_factory=dict)

    # --- Dimension 2: Robustness ---
    ic_mean_oos: float = NaN
    ic_ir_oos: float = NaN
    oos_decay_ratio: float = NaN
    ic_autocorr: float = NaN
    ic_max_drawdown: float = NaN
    worst_quarter_ic: float = NaN
    best_quarter_ic: float = NaN

    # --- Dimension 3: Economic Coherence ---
    quantile_returns_is: Dict[str, float] = field(default_factory=dict)
    quantile_returns_oos: Dict[str, float] = field(default_factory=dict)
    monotonicity_is: float = NaN
    monotonicity_oos: float = NaN
    ls_return: float = NaN
    ls_tstat: float = NaN
    ic_sign_consistent: bool = True

    # --- Dimension 4: Decay & Turnover ---
    ic_decay: Dict[int, float] = field(default_factory=dict)
    half_life_days: float = NaN
    factor_turnover: float = NaN
    factor_autocorr: float = NaN

    # --- Dimension 5: Coverage & Distribution ---
    coverage: float = NaN
    zero_ratio: float = NaN
    factor_skew: float = NaN
    factor_kurt: float = NaN
    extreme_ratio: float = NaN

    # --- Dimension 6: Uniqueness ---
    max_lib_corr: float = 0.0
    max_corr_factor_id: str = ""
    lib_corr_profile: Dict[str, float] = field(default_factory=dict)
    incremental_ic: float = NaN
    expression_depth: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Serializable dict for YAML/JSON. NaN -> None."""
        return _sanitize(asdict(self))


def _sanitize(obj):
    """Recursively convert numpy types and NaN to JSON-safe Python types."""
    if isinstance(obj, dict):
        return {_sanitize(k): _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(v) for v in obj]
    if isinstance(obj, (np.floating, float)):
        return None if np.isnan(obj) else float(obj)
    if isinstance(obj, (np.integer, int)):
        return int(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    return obj


# ──────────────────── Dimension 1: Predictive Power ────────────────────


def dim1_predictive_power(daily_ics: pd.Series) -> Dict[str, Any]:
    """Compute predictive power metrics from datetime-indexed IC series."""
    if daily_ics.empty:
        return {"ic_mean": NaN, "ic_std": NaN, "ic_ir": NaN, "ic_win_rate": NaN,
                "ic_by_year": {}, "ic_by_month": {}}

    summary = ic_summary_from_series(daily_ics)

    ic_by_year = {int(y): float(g.mean()) for y, g in daily_ics.groupby(daily_ics.index.year)}
    ic_by_month = {int(m): float(g.mean()) for m, g in daily_ics.groupby(daily_ics.index.month)}

    return {**summary, "ic_by_year": ic_by_year, "ic_by_month": ic_by_month}


# ──────────────────── Dimension 2: Robustness ────────────────────


def dim2_robustness(daily_ics_is: pd.Series, daily_ics_oos: pd.Series) -> Dict[str, Any]:
    """Compute robustness metrics from IS and OOS daily IC series."""
    ic_mean_is = float(daily_ics_is.mean()) if not daily_ics_is.empty else NaN

    # OOS summary
    ic_mean_oos = NaN
    ic_ir_oos = NaN
    if not daily_ics_oos.empty:
        arr_oos = daily_ics_oos.values.astype(float)
        ic_mean_oos = float(np.nanmean(arr_oos))
        ic_std_oos = float(np.nanstd(arr_oos)) if len(arr_oos) > 1 else NaN
        if ic_std_oos and ic_std_oos > 0:
            ic_ir_oos = float(ic_mean_oos / ic_std_oos)

    # OOS decay ratio
    oos_decay_ratio = NaN
    if not np.isnan(ic_mean_is) and abs(ic_mean_is) > 1e-8:
        oos_decay_ratio = float(ic_mean_oos / ic_mean_is)

    # IC autocorrelation (lag-1)
    ic_autocorr = NaN
    if len(daily_ics_is) > 2:
        arr = daily_ics_is.dropna().values.astype(float)
        if len(arr) > 2:
            ic_autocorr = float(np.corrcoef(arr[:-1], arr[1:])[0, 1])

    # IC max drawdown (cumulative IC)
    ic_max_drawdown = NaN
    if not daily_ics_is.empty:
        ic_max_drawdown = compute_max_drawdown(daily_ics_is.cumsum())

    # Best / worst quarter
    worst_quarter_ic = NaN
    best_quarter_ic = NaN
    if not daily_ics_is.empty:
        quarterly = daily_ics_is.groupby(
            [daily_ics_is.index.year, daily_ics_is.index.quarter],
        ).mean()
        if len(quarterly) > 0:
            worst_quarter_ic = float(quarterly.min())
            best_quarter_ic = float(quarterly.max())

    return {
        "ic_mean_oos": ic_mean_oos, "ic_ir_oos": ic_ir_oos,
        "oos_decay_ratio": oos_decay_ratio, "ic_autocorr": ic_autocorr,
        "ic_max_drawdown": ic_max_drawdown,
        "worst_quarter_ic": worst_quarter_ic, "best_quarter_ic": best_quarter_ic,
    }


# ──────────────────── Dimension 3: Economic Coherence ────────────────────


def _quantile_returns(
    factor_values: pd.DataFrame, returns: pd.DataFrame, n_quantiles: int = 5,
) -> Tuple[Dict[str, float], List[float]]:
    """Compute quintile returns and daily long-short returns."""
    factor_col = factor_values.columns[0]
    returns_col = returns.columns[0]
    merged = factor_values.join(returns, how="inner").dropna()
    if merged.empty:
        return {f"q{i + 1}": NaN for i in range(n_quantiles)}, []

    daily_qs: Dict[str, List[float]] = {}
    daily_ls: List[float] = []

    for _, group in merged.groupby(level="datetime"):
        if len(group) < n_quantiles:
            continue
        g = group.copy()
        g["quantile"] = pd.qcut(g[factor_col], n_quantiles, labels=False, duplicates="drop")
        for q in range(n_quantiles):
            q_ret = g.loc[g["quantile"] == q, returns_col].mean()
            daily_qs.setdefault(f"q{q + 1}", []).append(q_ret)
        q_top = g.loc[g["quantile"] == n_quantiles - 1, returns_col].mean()
        q_bot = g.loc[g["quantile"] == 0, returns_col].mean()
        if not np.isnan(q_top) and not np.isnan(q_bot):
            daily_ls.append(q_top - q_bot)

    avg_qs = {k: float(np.nanmean(v)) if v else NaN for k, v in daily_qs.items()}
    return avg_qs, daily_ls


def _monotonicity(quantile_returns: Dict[str, float]) -> float:
    q_keys = sorted(quantile_returns.keys())
    q_vals = [quantile_returns[k] for k in q_keys
              if not np.isnan(quantile_returns.get(k, NaN))]
    if len(q_vals) < 3:
        return NaN
    rho, _ = spearmanr(range(len(q_vals)), q_vals)
    return float(rho) if not np.isnan(rho) else NaN


def dim3_economic_coherence(
    factor_vals_is: pd.DataFrame, returns_is: pd.DataFrame,
    factor_vals_oos: pd.DataFrame, returns_oos: pd.DataFrame,
    ic_mean_is: float, ic_mean_oos: float,
) -> Dict[str, Any]:
    """Compute economic coherence metrics."""
    q_is, daily_ls_is = _quantile_returns(factor_vals_is, returns_is)
    q_oos, _ = _quantile_returns(factor_vals_oos, returns_oos)

    mono_is = _monotonicity(q_is)
    mono_oos = _monotonicity(q_oos)

    ls_return = NaN
    ls_tstat = NaN
    if daily_ls_is:
        ls_arr = np.array(daily_ls_is)
        ls_return = float(np.nanmean(ls_arr))
        ls_std = float(np.nanstd(ls_arr))
        n = int(np.sum(~np.isnan(ls_arr)))
        if ls_std > 0 and n > 1:
            ls_tstat = float(ls_return / (ls_std / np.sqrt(n)))

    ic_sign_consistent = True
    if not np.isnan(ic_mean_is) and not np.isnan(ic_mean_oos):
        ic_sign_consistent = (ic_mean_is >= 0) == (ic_mean_oos >= 0)

    return {
        "quantile_returns_is": q_is, "quantile_returns_oos": q_oos,
        "monotonicity_is": mono_is, "monotonicity_oos": mono_oos,
        "ls_return": ls_return, "ls_tstat": ls_tstat,
        "ic_sign_consistent": ic_sign_consistent,
    }


# ──────────────────── Dimension 4: Decay & Turnover ────────────────────


def _estimate_half_life(ic_decay: Dict[int, float]) -> float:
    sorted_h = sorted(ic_decay.keys())
    if len(sorted_h) < 2:
        return NaN
    ic_1d = ic_decay.get(sorted_h[0], NaN)
    if np.isnan(ic_1d) or abs(ic_1d) < 1e-8:
        return NaN
    target = abs(ic_1d) / 2.0
    for i in range(1, len(sorted_h)):
        h = sorted_h[i]
        ic_h = abs(ic_decay.get(h, NaN))
        if np.isnan(ic_h):
            continue
        if ic_h <= target:
            h_prev = sorted_h[i - 1]
            ic_prev = abs(ic_decay[h_prev])
            denom = ic_prev - ic_h
            if abs(denom) < 1e-10:
                return float(h)
            frac = (ic_prev - target) / denom
            return float(h_prev + frac * (h - h_prev))
    return NaN


def dim4_decay_turnover(
    daily_ics_by_horizon: Dict[int, pd.Series],
    factor_vals: pd.DataFrame,
) -> Dict[str, Any]:
    """Compute decay and turnover metrics."""
    ic_decay = {}
    for h, ics in daily_ics_by_horizon.items():
        ic_decay[h] = float(ics.mean()) if not ics.empty else NaN
    half_life = _estimate_half_life(ic_decay)

    # Factor turnover / autocorrelation
    factor_turnover = NaN
    factor_autocorr = NaN
    if not factor_vals.empty:
        factor_col = factor_vals.columns[0]
        dates = factor_vals.index.get_level_values("datetime").unique().sort_values()
        rank_corrs = []
        for i in range(1, len(dates)):
            try:
                prev = factor_vals.loc[dates[i - 1]]
                curr = factor_vals.loc[dates[i]]
            except KeyError:
                continue
            common = prev.index.intersection(curr.index)
            if len(common) < 5:
                continue
            rho, _ = spearmanr(
                prev.loc[common, factor_col], curr.loc[common, factor_col],
            )
            if not np.isnan(rho):
                rank_corrs.append(rho)
        if rank_corrs:
            factor_autocorr = float(np.mean(rank_corrs))
            factor_turnover = 1.0 - factor_autocorr

    return {"ic_decay": ic_decay, "half_life_days": half_life,
            "factor_turnover": factor_turnover, "factor_autocorr": factor_autocorr}


# ──────────────────── Dimension 5: Coverage & Distribution ────────────────────


def dim5_distribution(factor_vals: pd.DataFrame) -> Dict[str, Any]:
    """Compute coverage and distribution metrics from raw factor values."""
    factor_col = factor_vals.columns[0]
    vals = factor_vals[factor_col]
    total = len(vals)
    if total == 0:
        return {"coverage": NaN, "zero_ratio": NaN, "factor_skew": NaN,
                "factor_kurt": NaN, "extreme_ratio": NaN}

    coverage = float(1 - vals.isna().sum() / total)
    zero_ratio = float((vals == 0).sum() / total)

    # Cross-sectional skew / kurt (averaged across days)
    skews, kurts = [], []
    for _, group in factor_vals.groupby(level="datetime"):
        g = group[factor_col].dropna()
        if len(g) < 5:
            continue
        skews.append(float(g.skew()))
        kurts.append(float(g.kurt()))
    factor_skew = float(np.nanmean(skews)) if skews else NaN
    factor_kurt = float(np.nanmean(kurts)) if kurts else NaN

    # Extreme ratio (|z| > 3)
    extreme_ratio = NaN
    non_nan = vals.dropna()
    if len(non_nan) > 10:
        std = non_nan.std()
        if std > 0:
            z = ((non_nan - non_nan.mean()) / std).abs()
            extreme_ratio = float((z > 3).sum() / len(z))
        else:
            extreme_ratio = 0.0

    return {"coverage": coverage, "zero_ratio": zero_ratio,
            "factor_skew": factor_skew, "factor_kurt": factor_kurt,
            "extreme_ratio": extreme_ratio}


# ──────────────────── Dimension 6: Uniqueness ────────────────────


def _compute_incremental_ic(
    factor_vals: pd.DataFrame, returns: pd.DataFrame,
    lib_values: Dict[str, pd.DataFrame],
) -> float:
    """IC of factor residuals after regressing out library factors."""
    if not lib_values:
        return NaN

    factor_col = factor_vals.columns[0]
    returns_col = returns.columns[0]

    merged = factor_vals.copy()
    lib_cols = []
    for lid, lvals in lib_values.items():
        col = f"lib_{lid}"
        lib_cols.append(col)
        merged = merged.join(
            lvals.rename(columns={lvals.columns[0]: col}), how="inner",
        )
    merged = merged.join(returns, how="inner")

    daily_ics = []
    min_obs = max(10, len(lib_cols) + 2)
    for _, group in merged.groupby(level="datetime"):
        g = group.dropna()
        if len(g) < min_obs:
            continue
        y = g[factor_col].values
        X = np.column_stack([np.ones(len(y)), g[lib_cols].values])
        try:
            beta, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
            resid = y - X @ beta
        except np.linalg.LinAlgError:
            continue
        if np.std(resid) < 1e-10 or np.std(g[returns_col].values) < 1e-10:
            continue
        ic, _ = spearmanr(resid, g[returns_col].values)
        if not np.isnan(ic):
            daily_ics.append(ic)

    return float(np.mean(daily_ics)) if daily_ics else NaN


def dim6_uniqueness(
    factor_vals: pd.DataFrame, returns: pd.DataFrame,
    lib_values: Dict[str, pd.DataFrame],
    lib_corr_profile: Dict[str, float],
    stage2_info: Dict[str, Any],
    expression_depth: int,
) -> Dict[str, Any]:
    """Compute uniqueness metrics."""
    incr_ic = _compute_incremental_ic(factor_vals, returns, lib_values)
    return {
        "max_lib_corr": stage2_info.get("max_corr", 0.0),
        "max_corr_factor_id": stage2_info.get("max_corr_factor", "") or "",
        "lib_corr_profile": lib_corr_profile,
        "incremental_ic": incr_ic,
        "expression_depth": expression_depth,
    }


# ──────────────────── Top-Level Builder ────────────────────


def compute_report_card(
    daily_ics_is: pd.Series,
    daily_ics_oos: pd.Series,
    factor_vals_is: pd.DataFrame,
    factor_vals_oos: pd.DataFrame,
    returns_is: pd.DataFrame,
    returns_oos: pd.DataFrame,
    daily_ics_by_horizon: Dict[int, pd.Series],
    lib_values: Dict[str, pd.DataFrame],
    lib_corr_profile: Dict[str, float],
    stage2_info: Dict[str, Any],
    expression_depth: int,
) -> FactorReportCard:
    """Build a complete 6-dimension FactorReportCard."""
    d1 = dim1_predictive_power(daily_ics_is)
    d2 = dim2_robustness(daily_ics_is, daily_ics_oos)
    d3 = dim3_economic_coherence(
        factor_vals_is, returns_is, factor_vals_oos, returns_oos,
        d1["ic_mean"], d2["ic_mean_oos"],
    )
    d4 = dim4_decay_turnover(daily_ics_by_horizon, factor_vals_is)
    d5 = dim5_distribution(factor_vals_is)
    d6 = dim6_uniqueness(
        factor_vals_is, returns_is, lib_values,
        lib_corr_profile, stage2_info, expression_depth,
    )

    return FactorReportCard(
        # D1
        ic_mean=d1["ic_mean"], ic_std=d1["ic_std"], ic_ir=d1["ic_ir"],
        ic_win_rate=d1["ic_win_rate"],
        ic_by_year=d1["ic_by_year"], ic_by_month=d1["ic_by_month"],
        # D2
        ic_mean_oos=d2["ic_mean_oos"], ic_ir_oos=d2["ic_ir_oos"],
        oos_decay_ratio=d2["oos_decay_ratio"], ic_autocorr=d2["ic_autocorr"],
        ic_max_drawdown=d2["ic_max_drawdown"],
        worst_quarter_ic=d2["worst_quarter_ic"], best_quarter_ic=d2["best_quarter_ic"],
        # D3
        quantile_returns_is=d3["quantile_returns_is"],
        quantile_returns_oos=d3["quantile_returns_oos"],
        monotonicity_is=d3["monotonicity_is"], monotonicity_oos=d3["monotonicity_oos"],
        ls_return=d3["ls_return"], ls_tstat=d3["ls_tstat"],
        ic_sign_consistent=d3["ic_sign_consistent"],
        # D4
        ic_decay=d4["ic_decay"], half_life_days=d4["half_life_days"],
        factor_turnover=d4["factor_turnover"], factor_autocorr=d4["factor_autocorr"],
        # D5
        coverage=d5["coverage"], zero_ratio=d5["zero_ratio"],
        factor_skew=d5["factor_skew"], factor_kurt=d5["factor_kurt"],
        extreme_ratio=d5["extreme_ratio"],
        # D6
        max_lib_corr=d6["max_lib_corr"], max_corr_factor_id=d6["max_corr_factor_id"],
        lib_corr_profile=d6["lib_corr_profile"], incremental_ic=d6["incremental_ic"],
        expression_depth=d6["expression_depth"],
    )
