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

    Fully vectorized: pivots to (date × stock) matrices, ranks cross-sectionally,
    then computes Pearson correlation of ranks (= Spearman IC) via matrix ops.
    No Python for-loop over days.

    Args:
        factor_df: Flat DataFrame [time, symbol, value].
        returns_df: Flat DataFrame [time, symbol, value] (forward returns).
        method: "spearman" (rank IC) or "pearson".
        min_obs: Minimum valid observations per day to include in output.

    Returns:
        pd.Series with DatetimeIndex and IC values.
    """
    merged = factor_df.merge(
        returns_df, on=["time", "symbol"], suffixes=("_factor", "_return"),
    )
    merged = merged.dropna(subset=["value_factor", "value_return"])
    if merged.empty:
        return pd.Series(dtype=float)

    # Pivot to (date × stock) matrices — aligns NaN where data is missing
    factor_wide = merged.pivot(index="time", columns="symbol", values="value_factor")
    returns_wide = merged.pivot(index="time", columns="symbol", values="value_return")

    # Drop days with too few valid observations
    n_valid = factor_wide.notna().sum(axis=1)
    valid_dates = n_valid[n_valid >= min_obs].index
    if valid_dates.empty:
        return pd.Series(dtype=float)
    factor_wide = factor_wide.loc[valid_dates]
    returns_wide = returns_wide.loc[valid_dates]

    if method == "spearman":
        # Cross-sectional rank within each day (axis=1)
        factor_vals = factor_wide.rank(axis=1, na_option="keep")
        returns_vals = returns_wide.rank(axis=1, na_option="keep")
    else:
        factor_vals = factor_wide
        returns_vals = returns_wide

    # Vectorized Pearson correlation per row (day) using numpy matrix ops
    # valid mask: NaN in either column excludes that stock
    valid = factor_vals.notna() & returns_vals.notna()
    n = valid.sum(axis=1).astype(float).values  # shape: (n_days,)

    f = np.where(valid.values, factor_vals.values, np.nan)
    r = np.where(valid.values, returns_vals.values, np.nan)

    # Masked mean per day (nanmean along axis=1)
    mean_f = np.nanmean(f, axis=1, keepdims=True)
    mean_r = np.nanmean(r, axis=1, keepdims=True)

    # Centered values (NaN stays NaN, contributes 0 via nansum)
    f_c = np.where(valid.values, f - mean_f, 0.0)
    r_c = np.where(valid.values, r - mean_r, 0.0)

    # Variance and covariance
    var_f = (f_c ** 2).sum(axis=1) / n
    var_r = (r_c ** 2).sum(axis=1) / n
    cov   = (f_c * r_c).sum(axis=1) / n

    denom = np.sqrt(var_f * var_r)
    ic = np.where(denom > 1e-10, cov / denom, np.nan)

    result = pd.Series(ic, index=factor_wide.index, dtype=float)
    return result.dropna()


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

    Vectorized: uses the same pivot + rank + matrix-Pearson approach as
    daily_cross_sectional_ic, then averages across days.

    Args:
        df_a: Factor A with columns [time, symbol, value].
        df_b: Factor B with columns [time, symbol, value].
        min_obs: Minimum observations per day.

    Returns:
        Mean daily cross-sectional Spearman correlation, or None if insufficient data.
    """
    merged = df_a.merge(df_b, on=["time", "symbol"], suffixes=("_a", "_b"))
    merged = merged.dropna(subset=["value_a", "value_b"])
    if len(merged) < min_obs:
        return None

    # Reuse daily_cross_sectional_ic in Pearson-of-ranks form
    # Build flat DataFrames matching the expected [time, symbol, value] schema
    flat_a = merged[["time", "symbol", "value_a"]].rename(columns={"value_a": "value"})
    flat_b = merged[["time", "symbol", "value_b"]].rename(columns={"value_b": "value"})
    daily_corrs_series = daily_cross_sectional_ic(flat_a, flat_b, method="spearman", min_obs=min_obs)
    if daily_corrs_series.empty:
        return None
    # Placeholder for the old variable name used below
    daily_corrs = daily_corrs_series.dropna().tolist()
    if not daily_corrs:
        return None
    return float(np.mean(daily_corrs)) if daily_corrs else None


# ──────────────────── Quintile Returns ────────────────────


def quintile_returns(
    factor_df: pd.DataFrame,
    returns_df: pd.DataFrame,
    n_quantiles: int = 5,
    min_obs: int = 5,
) -> Tuple[Dict[str, float], List[float]]:
    """Compute quintile (or n-quantile) average returns and daily long-short returns.

    Fully vectorized: pivots to (date × stock) matrices, assigns quantile buckets
    via cross-sectional rank, then aggregates with numpy masked operations.
    No Python for-loop over dates.

    Args:
        factor_df: Flat DataFrame [time, symbol, value].
        returns_df: Flat DataFrame [time, symbol, value] (forward returns).
        n_quantiles: Number of quantile groups.
        min_obs: Minimum valid observations per day to include.

    Returns:
        Tuple of (average quintile returns dict, daily long-short return list).
    """
    merged = factor_df.merge(
        returns_df, on=["time", "symbol"], suffixes=("_factor", "_return"),
    )
    merged = merged.dropna(subset=["value_factor", "value_return"])
    if merged.empty:
        return {f"q{i + 1}": np.nan for i in range(n_quantiles)}, []

    # Pivot to (date × stock) matrices
    factor_wide = merged.pivot(index="time", columns="symbol", values="value_factor")
    returns_wide = merged.pivot(index="time", columns="symbol", values="value_return")

    # Filter days with enough valid observations
    n_valid = factor_wide.notna().sum(axis=1)
    valid_days = n_valid[n_valid >= max(n_quantiles, min_obs)].index
    if valid_days.empty:
        return {f"q{i + 1}": np.nan for i in range(n_quantiles)}, []
    factor_wide = factor_wide.loc[valid_days]
    returns_wide = returns_wide.loc[valid_days]

    # Cross-sectional quantile assignment: rank(pct=True) → floor to bucket index
    # rank(pct=True) ∈ (0, 1], multiply by n_quantiles → (0, n_quantiles]
    # subtract tiny epsilon to map 1.0 → bucket n_quantiles-1 (not n_quantiles)
    pct = factor_wide.rank(axis=1, pct=True, na_option="keep").values  # (n_days, n_stocks)
    buckets = np.floor(pct * n_quantiles - 1e-9).astype(float)          # 0-indexed
    buckets = np.where(factor_wide.notna().values, buckets, np.nan)     # NaN where missing

    ret_vals = returns_wide.values  # (n_days, n_stocks)

    # Per-quintile mean return across all days
    avg_qs: Dict[str, float] = {}
    for q in range(n_quantiles):
        mask = buckets == q
        q_returns = np.where(mask, ret_vals, np.nan)
        avg_qs[f"q{q + 1}"] = float(np.nanmean(q_returns))

    # Daily long-short: top quintile mean - bottom quintile mean (per day)
    top = np.nanmean(np.where(buckets == n_quantiles - 1, ret_vals, np.nan), axis=1)
    bot = np.nanmean(np.where(buckets == 0, ret_vals, np.nan), axis=1)
    ls = top - bot
    daily_ls: List[float] = ls[np.isfinite(ls)].tolist()

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

    Vectorized: pivots to (date × stock) matrix, then for each lag computes
    Spearman correlation via rank + Pearson matrix ops across all sampled date
    pairs simultaneously — no inner Python loop over dates.

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

    # Pivot to (date × stock) matrix once
    factor_wide = factor_df.pivot(index="time", columns="symbol", values="value")
    n_dates = len(factor_wide)

    # Pre-rank cross-sectionally for all dates (Spearman = Pearson of ranks)
    factor_ranked = factor_wide.rank(axis=1, na_option="keep")  # (n_dates, n_stocks)
    f_np = factor_ranked.values  # numpy array for fast slicing

    result = []
    rng = np.random.RandomState(42)

    for lag in lags:
        if lag >= n_dates:
            continue

        # Select date pair indices (curr_idx, prev_idx=curr_idx-lag)
        eligible = np.arange(lag, n_dates)
        if len(eligible) > max_dates:
            eligible = rng.choice(eligible, max_dates, replace=False)

        # Batch extract: curr[eligible] and prev[eligible-lag]
        curr = f_np[eligible]          # (n_sampled, n_stocks)
        prev = f_np[eligible - lag]    # (n_sampled, n_stocks)

        # Valid mask: both curr and prev must be non-NaN
        valid = ~np.isnan(curr) & ~np.isnan(prev)
        n_valid = valid.sum(axis=1)    # (n_sampled,)

        # Only use date pairs with enough common observations
        ok = n_valid >= min_obs
        if not ok.any():
            continue
        curr, prev, valid, n_valid = curr[ok], prev[ok], valid[ok], n_valid[ok].astype(float)

        # Pearson correlation of already-ranked values = Spearman IC
        # Zero out NaN positions for computation
        c = np.where(valid, curr, 0.0)
        p = np.where(valid, prev, 0.0)

        mean_c = c.sum(axis=1) / n_valid          # (n_pairs,)
        mean_p = p.sum(axis=1) / n_valid
        c_cent = np.where(valid, c - mean_c[:, None], 0.0)
        p_cent = np.where(valid, p - mean_p[:, None], 0.0)

        var_c = (c_cent ** 2).sum(axis=1) / n_valid
        var_p = (p_cent ** 2).sum(axis=1) / n_valid
        cov   = (c_cent * p_cent).sum(axis=1) / n_valid

        denom = np.sqrt(var_c * var_p)
        corrs = np.where(denom > 1e-10, cov / denom, np.nan)
        corrs = corrs[np.isfinite(corrs)]

        if len(corrs) > 0:
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

    Vectorized pre-join: merges all library factors into a single panel once
    (eliminates inner loop over library factors per date), then iterates over
    dates for the unavoidable per-date OLS solve (variable valid-stock sets
    prevent full outer vectorization).

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

    # Pre-join all data into one panel (eliminates inner loop over library factors)
    panel = factor_df.rename(columns={"value": "target"})
    panel = panel.merge(
        returns_df.rename(columns={"value": "future_return"}),
        on=["time", "symbol"], how="inner",
    )
    for fid, fdf in library_factors.items():
        panel = panel.merge(
            fdf[["time", "symbol", "value"]].rename(columns={"value": fid}),
            on=["time", "symbol"], how="inner",
        )

    lib_cols = list(library_factors.keys())
    panel = panel.dropna(subset=["target", "future_return"] + lib_cols)
    if panel.empty:
        return None, None

    daily_residual_ics = []

    for _, group in panel.groupby("time"):
        if len(group) < min_obs:
            continue
        X = group[lib_cols].values          # (n_stocks, n_lib_factors)
        y = group["target"].values          # (n_stocks,)
        ret_vals = group["future_return"].values
        try:
            coeffs, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
            residual = y - X @ coeffs
            if np.std(residual) < 1e-10:
                continue
            corr, _ = spearmanr(residual, ret_vals)
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
