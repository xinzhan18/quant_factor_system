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

    Pivots flat ``[time, symbol, value]`` inputs to wide and delegates
    to :func:`daily_cross_sectional_ic_from_wides`.
    """
    merged = factor_df.merge(
        returns_df, on=["time", "symbol"], suffixes=("_factor", "_return"),
    )
    merged = merged.dropna(subset=["value_factor", "value_return"])
    if merged.empty:
        return pd.Series(dtype=float)
    factor_wide = merged.pivot(index="time", columns="symbol", values="value_factor")
    returns_wide = merged.pivot(index="time", columns="symbol", values="value_return")
    return daily_cross_sectional_ic_from_wides(
        factor_wide, returns_wide, method=method, min_obs=min_obs,
    )


def daily_cross_sectional_ic_from_wides(
    factor_wide: pd.DataFrame,
    returns_wide: pd.DataFrame,
    method: str = "spearman",
    min_obs: int = 30,
) -> pd.Series:
    """Pre-pivoted variant of :func:`daily_cross_sectional_ic`.

    Both inputs are wide (date × symbol). Different grids are handled by
    intersecting dates/columns and applying a joint-validity mask — the
    output matches what the merged-flat path produces, which lets Phase 2
    cache per-horizon returns wides once per batch and pivot the
    candidate's factor once across all 5 horizons × 2 splits.
    """
    common_dates = factor_wide.index.intersection(returns_wide.index)
    common_cols = factor_wide.columns.intersection(returns_wide.columns)
    if len(common_dates) == 0 or len(common_cols) == 0:
        return pd.Series(dtype=float)
    fw = factor_wide.loc[common_dates, common_cols]
    rw = returns_wide.loc[common_dates, common_cols]

    # Joint validity (matches the merged-flat path's dropna semantics)
    joint = fw.notna() & rw.notna()
    n_valid = joint.sum(axis=1)
    valid_dates = n_valid[n_valid >= min_obs].index
    if valid_dates.empty:
        return pd.Series(dtype=float)
    fw = fw.loc[valid_dates].where(joint.loc[valid_dates])
    rw = rw.loc[valid_dates].where(joint.loc[valid_dates])

    if method == "spearman":
        factor_vals = fw.rank(axis=1, na_option="keep")
        returns_vals = rw.rank(axis=1, na_option="keep")
    else:
        factor_vals = fw
        returns_vals = rw

    valid = factor_vals.notna() & returns_vals.notna()
    n = valid.sum(axis=1).astype(float).values

    f = np.where(valid.values, factor_vals.values, np.nan)
    r = np.where(valid.values, returns_vals.values, np.nan)

    mean_f = np.nanmean(f, axis=1, keepdims=True)
    mean_r = np.nanmean(r, axis=1, keepdims=True)

    f_c = np.where(valid.values, f - mean_f, 0.0)
    r_c = np.where(valid.values, r - mean_r, 0.0)

    var_f = (f_c ** 2).sum(axis=1) / n
    var_r = (r_c ** 2).sum(axis=1) / n
    cov   = (f_c * r_c).sum(axis=1) / n

    denom = np.sqrt(var_f * var_r)
    ic = np.where(denom > 1e-10, cov / denom, np.nan)

    result = pd.Series(ic, index=valid_dates, dtype=float)
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
) -> Tuple[Dict[str, float], List[float], pd.DataFrame]:
    """Compute quintile (or n-quantile) average returns, daily long-short
    returns, and per-quintile daily return series.

    Fully vectorized: pivots to (date × stock) matrices, assigns quantile
    buckets via cross-sectional rank, then aggregates with numpy masked
    operations. No Python for-loop over dates.

    Args:
        factor_df: Flat DataFrame [time, symbol, value].
        returns_df: Flat DataFrame [time, symbol, value] (forward returns).
        n_quantiles: Number of quantile groups.
        min_obs: Minimum valid observations per day to include.

    Returns:
        Tuple of
        * average per-quintile returns dict (``{"q1", ..., "qN"}``)
        * daily long-short return list (dropped NaN)
        * per-quintile daily DataFrame (date × ``q1..qN`` columns).
          Empty DataFrame when inputs are empty.
    """
    empty_df = pd.DataFrame(columns=[f"q{i + 1}" for i in range(n_quantiles)])
    merged = factor_df.merge(
        returns_df, on=["time", "symbol"], suffixes=("_factor", "_return"),
    )
    merged = merged.dropna(subset=["value_factor", "value_return"])
    if merged.empty:
        return (
            {f"q{i + 1}": np.nan for i in range(n_quantiles)},
            [],
            empty_df,
        )

    # Pivot to (date × stock) matrices
    factor_wide = merged.pivot(index="time", columns="symbol", values="value_factor")
    returns_wide = merged.pivot(index="time", columns="symbol", values="value_return")

    # Filter days with enough valid observations
    n_valid = factor_wide.notna().sum(axis=1)
    valid_days = n_valid[n_valid >= max(n_quantiles, min_obs)].index
    if valid_days.empty:
        return (
            {f"q{i + 1}": np.nan for i in range(n_quantiles)},
            [],
            empty_df,
        )
    factor_wide = factor_wide.loc[valid_days]
    returns_wide = returns_wide.loc[valid_days]

    # Cross-sectional quantile assignment: rank(pct=True) → floor to bucket index
    # rank(pct=True) ∈ (0, 1], multiply by n_quantiles → (0, n_quantiles]
    # subtract tiny epsilon to map 1.0 → bucket n_quantiles-1 (not n_quantiles)
    pct = factor_wide.rank(axis=1, pct=True, na_option="keep").values  # (n_days, n_stocks)
    buckets = np.floor(pct * n_quantiles - 1e-9).astype(float)          # 0-indexed
    buckets = np.where(factor_wide.notna().values, buckets, np.nan)     # NaN where missing

    ret_vals = returns_wide.values  # (n_days, n_stocks)

    import warnings
    avg_qs: Dict[str, float] = {}
    per_q_daily_cols = {}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)  # all-NaN slice
        for q in range(n_quantiles):
            mask = buckets == q
            q_returns = np.where(mask, ret_vals, np.nan)
            avg_qs[f"q{q + 1}"] = float(np.nanmean(q_returns))
            per_q_daily_cols[f"q{q + 1}"] = np.nanmean(q_returns, axis=1)

    per_q_daily = pd.DataFrame(
        per_q_daily_cols, index=pd.Index(valid_days, name="datetime")
    )

    # Daily long-short: top quintile mean - bottom quintile mean (per day)
    top = per_q_daily[f"q{n_quantiles}"].to_numpy()
    bot = per_q_daily["q1"].to_numpy()
    ls = top - bot
    daily_ls: List[float] = ls[np.isfinite(ls)].tolist()

    return avg_qs, daily_ls, per_q_daily


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
    """Compute IC of factor residuals after regressing out library exposures.

    Pivots every flat input ([time, symbol, value]) to a wide (date ×
    symbol) frame and delegates to :func:`incremental_ic_from_wides`.
    See that function for the math + numerical details.
    """
    if not library_factors:
        return None, None

    target_wide = factor_df.set_index(["time", "symbol"])["value"].unstack(level=-1)
    ret_wide = returns_df.set_index(["time", "symbol"])["value"].unstack(level=-1)
    lib_wides = {
        fid: library_factors[fid].set_index(["time", "symbol"])["value"].unstack(-1)
        for fid in library_factors
    }
    return incremental_ic_from_wides(target_wide, ret_wide, lib_wides, min_obs=min_obs)


def incremental_ic_from_wides(
    target_wide: pd.DataFrame,
    ret_wide: pd.DataFrame,
    lib_wides: Dict[str, pd.DataFrame],
    min_obs: int = 30,
) -> Tuple[Optional[float], Optional[float]]:
    """Pre-pivoted variant of :func:`incremental_ic`.

    Fully batched: stacks library wides into a (D, S, K) tensor, solves
    ``K+I·λ ridged`` normal equations per date with a single
    ``np.linalg.solve`` call, computes residuals via einsum, then gets
    daily cross-sectional Spearman via ranked Pearson.

    Per-date valid-stock mask is realised by NaN→0 on ``X`` and ``y`` —
    dropped stocks contribute zero to ``XᵀX`` and ``Xᵀy`` so the solve is
    equivalent to dropping them. Ridge (λ = 1e-4 · mean_diag(XᵀX)) keeps
    the solve stable as the library grows and K approaches S.

    Use this directly when callers can amortize the pivots across many
    candidates (the Phase 2 batch runner caches lib + returns wides
    once per batch, so 51 lib unstacks + 1 returns unstack happen once
    instead of N_candidates times).
    """
    if not lib_wides:
        return None, None

    lib_cols = list(lib_wides.keys())

    # Align all on the intersection of dates × symbols
    dates = target_wide.index
    symbols = target_wide.columns
    for f in (ret_wide, *lib_wides.values()):
        dates = dates.intersection(f.index)
        symbols = symbols.intersection(f.columns)
    if len(dates) == 0 or len(symbols) == 0:
        return None, None

    target = target_wide.loc[dates, symbols].to_numpy(dtype=float)   # (D, S)
    ret = ret_wide.loc[dates, symbols].to_numpy(dtype=float)         # (D, S)
    X = np.stack(
        [lib_wides[fid].loc[dates, symbols].to_numpy(dtype=float)
         for fid in lib_cols],
        axis=-1,
    )  # (D, S, K)

    # Joint validity mask
    mask = np.isfinite(target) & np.isfinite(ret) & np.all(np.isfinite(X), axis=-1)
    n_valid = mask.sum(axis=1)                   # (D,)
    keep_day = n_valid >= min_obs
    if not keep_day.any():
        return None, None

    # Zero out invalid rows — they then contribute nothing to XᵀX / Xᵀy
    target_z = np.where(mask, target, 0.0)
    X_z = np.where(mask[..., None], X, 0.0)

    # Normal equations batched across dates
    XtX = np.einsum("dsi,dsj->dij", X_z, X_z)    # (D, K, K)
    Xty = np.einsum("dsi,ds->di", X_z, target_z)  # (D, K)

    # Scale-invariant ridge: λ_d = 1e-4 · mean(diag(XᵀX_d))
    K = len(lib_cols)
    diag_mean = np.einsum("dii->d", XtX) / max(K, 1)
    lam = 1e-4 * diag_mean                        # (D,)
    XtX += lam[:, None, None] * np.eye(K)

    # Batched solve. For dates that fail we fall back to NaN below.
    beta = np.full((XtX.shape[0], K), np.nan)
    valid_idx = np.where(keep_day)[0]
    if valid_idx.size > 0:
        # numpy's batched solve wants b shape (..., M, N); we want N=1 per
        # date so reshape and squeeze.
        b_batched = Xty[valid_idx, :, None]                          # (n, K, 1)
        try:
            solved = np.linalg.solve(XtX[valid_idx], b_batched)      # (n, K, 1)
            beta[valid_idx] = solved[..., 0]
        except np.linalg.LinAlgError:
            # Fall back to lstsq per date for the problematic batch
            for d in valid_idx:
                try:
                    beta[d], *_ = np.linalg.lstsq(XtX[d], Xty[d], rcond=None)
                except np.linalg.LinAlgError:
                    continue

    # Residuals and masked residuals for rank correlation
    resid = target - np.einsum("dsi,di->ds", X, np.nan_to_num(beta, nan=0.0))
    resid = np.where(mask, resid, np.nan)

    # Per-date cross-sectional Spearman = Pearson(rank(resid), rank(ret))
    # Using the same rank-corr pattern as vectorized_redundancy._rank_corr_timeseries.
    # Rank per row, NaN preserved.
    resid_df = pd.DataFrame(resid, index=dates, columns=symbols)
    ret_df = pd.DataFrame(np.where(mask, ret, np.nan), index=dates, columns=symbols)
    resid_r = resid_df.rank(axis=1, method="average").to_numpy(dtype=float)
    ret_r = ret_df.rank(axis=1, method="average").to_numpy(dtype=float)

    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        mr = np.nanmean(resid_r, axis=1, keepdims=True)
        mt = np.nanmean(ret_r, axis=1, keepdims=True)
        dr = resid_r - mr
        dt = ret_r - mt
        num = np.nansum(dr * dt, axis=1)
        den = np.sqrt(np.nansum(dr * dr, axis=1)) * np.sqrt(np.nansum(dt * dt, axis=1))
    with np.errstate(invalid="ignore", divide="ignore"):
        corr = np.where(den > 0, num / den, np.nan)

    # Drop dates that didn't satisfy min_obs OR whose residual was
    # degenerate (std ~ 0) OR whose pearson is non-finite.
    corr = np.where(keep_day, corr, np.nan)
    valid = np.isfinite(corr)
    if not valid.any():
        return None, None

    ics = corr[valid]
    ic_mean = float(np.mean(ics))
    ic_std = float(np.std(ics))
    icir = float(ic_mean / ic_std) if ic_std > 0 else 0.0
    return ic_mean, icir
