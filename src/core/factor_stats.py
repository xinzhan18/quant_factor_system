"""Shared factor statistical computations.

Pure functions operating on flat DataFrames with columns [time, symbol, value].
Dependencies: numpy, pandas, scipy only. No Plotly/Qlib/DB imports.

Used by both mining/ and report/analytics/ pipelines.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.stats import spearmanr, skew, kurtosis


# ──────────────────── Helpers ────────────────────


def multiindex_to_flat(df: pd.DataFrame) -> pd.DataFrame:
    """Convert a Qlib-style MultiIndex (datetime, instrument) DataFrame to flat format.

    Input:  MultiIndex (datetime, instrument), single value column.
    Output: Columns [time, symbol, value].
    """
    if df.empty:
        return pd.DataFrame(columns=["time", "symbol", "value"])
    result = df.reset_index()
    col_map = {}
    for c in result.columns:
        cl = c.lower()
        if cl in ("datetime", "date"):
            col_map[c] = "time"
        elif cl in ("instrument", "stock", "ticker"):
            col_map[c] = "symbol"
    result = result.rename(columns=col_map)
    # Rename the value column (the one that's not time/symbol)
    non_key = [c for c in result.columns if c not in ("time", "symbol")]
    if len(non_key) == 1:
        result = result.rename(columns={non_key[0]: "value"})
    elif len(non_key) > 1:
        # Take the first non-key column as value
        result = result.rename(columns={non_key[0]: "value"})
        result = result[["time", "symbol", "value"]]
    return result[["time", "symbol", "value"]]


# ──────────────────── IC Computation ────────────────────


def daily_cross_sectional_ic(
    factor_df: pd.DataFrame,
    returns_df: pd.DataFrame,
    method: str = "spearman",
    min_obs: int = 30,
) -> pd.Series:
    """Compute daily cross-sectional IC between factor values and returns.

    Args:
        factor_df: Flat DataFrame [time, symbol, value].
        returns_df: Flat DataFrame [time, symbol, value] (forward returns).
        method: "spearman" or "pearson".
        min_obs: Minimum observations per day to compute IC.

    Returns:
        pd.Series with DatetimeIndex and IC values.
    """
    merged = factor_df.merge(
        returns_df, on=["time", "symbol"], suffixes=("_factor", "_return"),
    )
    merged = merged.dropna(subset=["value_factor", "value_return"])

    if merged.empty:
        return pd.Series(dtype=float)

    corr_func = spearmanr if method == "spearman" else _pearsonr_safe

    records = []
    for dt, group in merged.groupby("time"):
        if len(group) < min_obs:
            continue
        if group["value_factor"].nunique() < 2 or group["value_return"].nunique() < 2:
            continue
        corr, _ = corr_func(group["value_factor"], group["value_return"])
        if np.isfinite(corr):
            records.append((dt, float(corr)))

    if not records:
        return pd.Series(dtype=float)
    dates, ics = zip(*records)
    return pd.Series(ics, index=pd.DatetimeIndex(dates), dtype=float)


def _pearsonr_safe(a, b):
    """Pearson correlation with safe fallback."""
    from scipy.stats import pearsonr
    try:
        return pearsonr(a, b)
    except Exception:
        return np.nan, np.nan


# ──────────────────── IC Summary ────────────────────


def ic_summary(daily_ics: pd.Series) -> dict:
    """Compute summary statistics from a daily IC series.

    Returns:
        dict with ic_mean, ic_std, ic_ir, ic_win_rate.
    """
    if daily_ics.empty:
        return {"ic_mean": np.nan, "ic_std": np.nan, "ic_ir": np.nan,
                "ic_win_rate": np.nan}
    arr = daily_ics.dropna().values.astype(float)
    if len(arr) == 0:
        return {"ic_mean": np.nan, "ic_std": np.nan, "ic_ir": np.nan,
                "ic_win_rate": np.nan}
    ic_mean = float(np.mean(arr))
    ic_std = float(np.std(arr, ddof=1)) if len(arr) > 1 else np.nan
    ic_ir = float(ic_mean / ic_std) if ic_std and ic_std > 0 else np.nan
    win_rate = float(np.sum(arr > 0) / len(arr))
    return {"ic_mean": ic_mean, "ic_std": ic_std, "ic_ir": ic_ir,
            "ic_win_rate": win_rate}


# ──────────────────── IC by Year ────────────────────


def ic_by_year(daily_ics: pd.Series) -> Dict[int, float]:
    """Compute mean IC per year from a DatetimeIndex-indexed IC series.

    Returns:
        Dict mapping year (int) to mean IC (float).
    """
    if daily_ics.empty:
        return {}
    return {int(y): float(g.mean())
            for y, g in daily_ics.groupby(daily_ics.index.year)}


# ──────────────────── Pairwise Correlation ────────────────────


def pairwise_cross_sectional_corr(
    df_a: pd.DataFrame,
    df_b: pd.DataFrame,
    min_obs: int = 30,
) -> Optional[float]:
    """Average daily cross-sectional Spearman rank correlation between two factors.

    Args:
        df_a: Factor A with columns [time, symbol, value].
        df_b: Factor B with columns [time, symbol, value].
        min_obs: Minimum observations per day.

    Returns:
        Mean daily cross-sectional Spearman correlation, or None if insufficient data.
    """
    merged = df_a.merge(df_b, on=["time", "symbol"], suffixes=("_a", "_b"))
    if len(merged) < min_obs:
        return None
    daily_corrs = []
    for _, group in merged.groupby("time"):
        g = group.dropna(subset=["value_a", "value_b"])
        if len(g) < min_obs:
            continue
        corr, _ = spearmanr(g["value_a"], g["value_b"])
        if np.isfinite(corr):
            daily_corrs.append(corr)
    return float(np.mean(daily_corrs)) if daily_corrs else None


# ──────────────────── Quintile Returns ────────────────────


def quintile_returns(
    factor_df: pd.DataFrame,
    returns_df: pd.DataFrame,
    n_quantiles: int = 5,
    min_obs: int = 5,
) -> Tuple[Dict[str, float], List[float]]:
    """Compute quintile (or n-quantile) average returns and daily long-short returns.

    Args:
        factor_df: Flat DataFrame [time, symbol, value].
        returns_df: Flat DataFrame [time, symbol, value] (forward returns).
        n_quantiles: Number of quantile groups.
        min_obs: Minimum observations per day.

    Returns:
        Tuple of (average quintile returns dict, daily long-short return list).
    """
    merged = factor_df.merge(
        returns_df, on=["time", "symbol"], suffixes=("_factor", "_return"),
    )
    merged = merged.dropna(subset=["value_factor", "value_return"])

    if merged.empty:
        return {f"q{i + 1}": np.nan for i in range(n_quantiles)}, []

    daily_qs: Dict[str, List[float]] = {}
    daily_ls: List[float] = []

    for _, group in merged.groupby("time"):
        if len(group) < max(n_quantiles, min_obs):
            continue
        g = group.copy()
        try:
            g["quantile"] = pd.qcut(
                g["value_factor"], n_quantiles, labels=False, duplicates="drop",
            )
        except ValueError:
            continue
        for q in range(n_quantiles):
            q_ret = g.loc[g["quantile"] == q, "value_return"].mean()
            daily_qs.setdefault(f"q{q + 1}", []).append(q_ret)
        q_top = g.loc[g["quantile"] == n_quantiles - 1, "value_return"].mean()
        q_bot = g.loc[g["quantile"] == 0, "value_return"].mean()
        if not np.isnan(q_top) and not np.isnan(q_bot):
            daily_ls.append(q_top - q_bot)

    avg_qs = {k: float(np.nanmean(v)) if v else np.nan
              for k, v in daily_qs.items()}
    return avg_qs, daily_ls


# ──────────────────── Monotonicity ────────────────────


def monotonicity(quantile_returns_dict: Dict[str, float]) -> float:
    """Compute monotonicity of quantile returns (Spearman rank correlation).

    Args:
        quantile_returns_dict: Dict like {"q1": 0.001, "q2": 0.002, ...}.

    Returns:
        Spearman correlation between quantile rank and return, or NaN.
    """
    q_keys = sorted(quantile_returns_dict.keys())
    q_vals = [quantile_returns_dict[k] for k in q_keys
              if not np.isnan(quantile_returns_dict.get(k, np.nan))]
    if len(q_vals) < 3:
        return np.nan
    rho, _ = spearmanr(range(len(q_vals)), q_vals)
    return float(rho) if not np.isnan(rho) else np.nan


# ──────────────────── Half-Life ────────────────────


def estimate_half_life(ic_by_period: Dict[int, float]) -> float:
    """Estimate signal half-life from IC-by-holding-period dict.

    Uses linear interpolation to find the period where absolute IC
    drops to half the 1-day value.

    Args:
        ic_by_period: Dict mapping holding period (days) to mean IC.

    Returns:
        Estimated half-life in days, or NaN if undetermined.
    """
    sorted_h = sorted(ic_by_period.keys())
    if len(sorted_h) < 2:
        return np.nan
    ic_1d = ic_by_period.get(sorted_h[0], np.nan)
    if np.isnan(ic_1d) or abs(ic_1d) < 1e-8:
        return np.nan
    target = abs(ic_1d) / 2.0
    for i in range(1, len(sorted_h)):
        h = sorted_h[i]
        ic_h = abs(ic_by_period.get(h, np.nan))
        if np.isnan(ic_h):
            continue
        if ic_h <= target:
            h_prev = sorted_h[i - 1]
            ic_prev = abs(ic_by_period[h_prev])
            denom = ic_prev - ic_h
            if abs(denom) < 1e-10:
                return float(h)
            frac = (ic_prev - target) / denom
            return float(h_prev + frac * (h - h_prev))
    return np.nan


# ──────────────────── Factor Autocorrelation ────────────────────


def factor_autocorrelation(
    factor_df: pd.DataFrame,
    lags: Optional[List[int]] = None,
    min_obs: int = 10,
    max_dates: int = 50,
) -> List[Dict[str, Any]]:
    """Compute cross-sectional factor autocorrelation at specified lags.

    For each lag, computes the average daily Spearman correlation
    between factor values at time t and t-lag.

    Args:
        factor_df: Flat DataFrame [time, symbol, value].
        lags: List of lag values in days. Default: [1, 2, 3, 5, 10, 15, 20].
        min_obs: Minimum common observations per day pair.
        max_dates: Maximum number of date pairs to sample per lag.

    Returns:
        List of dicts with {lag, corr}.
    """
    if lags is None:
        lags = [1, 2, 3, 5, 10, 15, 20]

    unique_dates = sorted(factor_df["time"].unique())
    date_groups = {
        pd.Timestamp(d): g for d, g in factor_df.groupby("time")
    }

    result = []
    for lag in lags:
        if lag >= len(unique_dates):
            continue

        eligible_indices = list(range(lag, len(unique_dates)))
        if len(eligible_indices) > max_dates:
            rng = np.random.RandomState(42)
            eligible_indices = list(
                rng.choice(eligible_indices, max_dates, replace=False)
            )

        corrs = []
        for idx in eligible_indices:
            date = pd.Timestamp(unique_dates[idx])
            prev_date = pd.Timestamp(unique_dates[idx - lag])

            curr_group = date_groups.get(date)
            prev_group = date_groups.get(prev_date)
            if curr_group is None or prev_group is None:
                continue

            curr = curr_group.set_index("symbol")["value"]
            prev = prev_group.set_index("symbol")["value"]
            common = curr.index.intersection(prev.index)
            if len(common) >= min_obs:
                rho, _ = spearmanr(curr[common], prev[common])
                if np.isfinite(rho):
                    corrs.append(rho)

        if corrs:
            result.append({"lag": lag, "corr": round(float(np.mean(corrs)), 4)})

    return result


# ──────────────────── Distribution Stats ────────────────────


def distribution_stats(factor_df: pd.DataFrame) -> dict:
    """Compute distribution statistics for a factor.

    Args:
        factor_df: Flat DataFrame [time, symbol, value].

    Returns:
        dict with mean, std, skew, kurtosis, coverage, nan_ratio.
    """
    vals = factor_df["value"]
    total = len(vals)
    non_nan = vals.dropna()

    if len(non_nan) < 10:
        return {
            "mean": 0.0, "std": 0.0, "skew": 0.0, "kurtosis": 0.0,
            "coverage": 0.0, "nan_ratio": 1.0,
        }

    nan_ratio = 1 - len(non_nan) / total if total > 0 else 1.0
    return {
        "mean": round(float(non_nan.mean()), 6),
        "std": round(float(non_nan.std()), 6),
        "skew": round(float(skew(non_nan)), 4),
        "kurtosis": round(float(kurtosis(non_nan)), 4),
        "coverage": round(1 - nan_ratio, 4),
        "nan_ratio": round(nan_ratio, 4),
    }


# ──────────────────── Incremental IC ────────────────────


def incremental_ic(
    factor_df: pd.DataFrame,
    returns_df: pd.DataFrame,
    library_factors: Dict[str, pd.DataFrame],
    min_obs: int = 30,
) -> Tuple[Optional[float], Optional[float]]:
    """Compute IC of factor residuals after regressing out library factor exposures.

    For each date, regresses the target factor on all library factors
    (cross-sectional OLS), then computes Spearman IC of residuals vs returns.

    Args:
        factor_df: Target factor [time, symbol, value].
        returns_df: Returns [time, symbol, value].
        library_factors: Dict of factor_id -> DataFrame [time, symbol, value].
        min_obs: Minimum observations per date.

    Returns:
        Tuple of (incremental_ic_mean, incremental_icir), or (None, None).
    """
    if not library_factors:
        return None, None

    target = factor_df.rename(columns={"value": "target"})
    ret = returns_df.rename(columns={"value": "future_return"})

    daily_residual_ics = []

    for date, group in ret.groupby("time"):
        date_target = target[target["time"] == date][["symbol", "target"]]
        lib_vals = date_target[["symbol"]].copy()

        for fid, fdf in library_factors.items():
            fdate = fdf[fdf["time"] == date][["symbol", "value"]].rename(
                columns={"value": fid}
            )
            lib_vals = lib_vals.merge(fdate, on="symbol", how="inner")

        lib_cols = [c for c in lib_vals.columns if c != "symbol"]
        if not lib_cols:
            continue

        if len(lib_vals) < min_obs:
            continue

        date_merged = date_target.merge(lib_vals, on="symbol")
        date_merged = date_merged.merge(
            group[["symbol", "future_return"]].drop_duplicates(), on="symbol"
        )

        if len(date_merged) < min_obs:
            continue

        X = date_merged[lib_cols].values
        y = date_merged["target"].values

        try:
            coeffs, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
            residual = y - X @ coeffs
            if np.std(residual) < 1e-10:
                continue
            corr, _ = spearmanr(residual, date_merged["future_return"].values)
            if np.isfinite(corr):
                daily_residual_ics.append(corr)
        except (np.linalg.LinAlgError, ValueError):
            continue

    if not daily_residual_ics:
        return None, None

    ics = np.array(daily_residual_ics)
    ic_mean = float(np.mean(ics))
    ic_std = float(np.std(ics))
    icir = float(ic_mean / ic_std) if ic_std > 0 else 0.0
    return ic_mean, icir
