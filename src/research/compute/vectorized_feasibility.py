"""Vectorized feasibility metrics — Phase 2 interface.

Consolidates what the legacy ``research.feasibility.*`` subpackage split
across five files into one module of pure functions. The legacy code had
three ``for date in dates`` loops (proxy portfolio weight assignment,
turnover computation, weighted_flag_ratio) and a ``groupby().apply()``
in ``compute_tail_concentration`` — all replaced here with broadcasting
and ``groupby(level=0).agg/.transform``.

Pipeline:

1. :func:`build_proxy_portfolio` — long top N%, short bottom N% per date,
   equal-weight within each leg → returns ``(long_weights, short_weights,
   abs_weights, turnover)``.
2. :func:`compute_liquidity_coverage` — fraction of weight in liquid stocks
   (liq20 ≥ cross-sectional 30th percentile), time-averaged.
3. :func:`compute_tail_concentration` — sum of top-k weights / total,
   time-averaged.
4. :func:`compute_small_cap_concentration` — fraction of weight in
   small-caps (market cap ≤ 30th pct), time-averaged.
5. :func:`compute_signal_half_life` — first lag where mean signal
   autocorrelation drops below 0.5. **Distinct from IC-decay half-life**
   (``research.compute.vectorized_ic.compute_ic_half_life``) — this is a
   persistence measure of the raw signal, not of its forward IC.
6. :func:`compute_signal_autocorr_lag1` — lag-1 cross-sectional factor
   autocorrelation, exposed as a standalone metric for the judge packet.
7. :func:`compute_rebalance_stress` — raw ``turnover × tail / max(lcr, 0.10)``
   scalar. The judge LLM, not Python, interprets it — no bucket label.

All functions consume MultiIndex(datetime, instrument) DataFrames with a
single value column, matching the legacy feasibility API so golden tests
can verify numerical equivalence.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from core.factor_stats import factor_autocorrelation, multiindex_to_flat


# ---------------------------------------------------------------------------
# Proxy portfolio (vectorized)
# ---------------------------------------------------------------------------


@dataclass
class ProxyPortfolio:
    """Container for proxy portfolio outputs (same shape as legacy)."""

    long_weights: pd.DataFrame
    short_weights: pd.DataFrame
    abs_weights: pd.DataFrame
    turnover: pd.Series


def build_proxy_portfolio(
    signal: pd.DataFrame,
    tradable_mask: pd.DataFrame,
    *,
    long_pct: float = 0.20,
    short_pct: float = 0.20,
) -> ProxyPortfolio:
    """Construct equal-weight long-short proxy portfolio (vectorized).

    Per rebalance date:

    * rank the signal cross-sectionally among tradable stocks
    * long top ``long_pct`` fraction, short bottom ``short_pct`` fraction
    * equal-weight within each leg

    Vectorization differences vs legacy:

    * **Weight assignment**: pivot signal to wide, ``rank(axis=1)`` all
      rows at once, compute ``n_long = max(floor(n_valid * long_pct), 1)``
      per row, then build masks via broadcasting — no ``groupby().apply``.
    * **Turnover**: compute total weight = long + short as a wide frame,
      then ``wide.diff().abs().sum(axis=1)`` gives per-date turnover in
      one vectorized pass — no per-date for-loop. First row uses
      ``wide.iloc[0].abs().sum()`` (full investment counts).
    """
    sig_col = signal.columns[0]
    mask_col = tradable_mask.columns[0]

    # Align & mask untradable to NaN
    sig = signal[sig_col].where(tradable_mask[mask_col].astype(bool))

    # Pivot to wide (date × symbol)
    sig_wide = sig.unstack(level=-1)

    # Cross-sectional rank — NaN stays NaN, method="first" breaks ties in
    # column order (matches legacy behavior)
    ranks = sig_wide.rank(axis=1, method="first", na_option="keep")
    n_valid = sig_wide.notna().sum(axis=1)  # (n_dates,)

    # Per-row n_long / n_short with floor(n*pct) clamped to ≥1.
    # Dates with <2 valid stocks are flagged and get zero weights.
    n_long = np.maximum(np.floor(n_valid * long_pct).astype(int), 1)
    n_short = np.maximum(np.floor(n_valid * short_pct).astype(int), 1)

    # Row-broadcasted boundaries
    long_bound = (n_valid - n_long).to_numpy()[:, None]  # (n_dates, 1)
    short_bound = n_short.to_numpy()[:, None]
    rank_vals = ranks.to_numpy()

    long_mask_wide = rank_vals > long_bound
    short_mask_wide = rank_vals <= short_bound

    # Dates with fewer than 2 tradable stocks: zero out both legs
    skip_row = (n_valid < 2).to_numpy()[:, None]
    long_mask_wide = long_mask_wide & ~skip_row
    short_mask_wide = short_mask_wide & ~skip_row

    # Weights: 1/n_long on long side, -1/n_short on short side.
    # Use 1/n_long broadcast across the row.
    long_per_name = (1.0 / n_long.to_numpy())[:, None]
    short_per_name = (-1.0 / n_short.to_numpy())[:, None]

    long_wide = np.where(long_mask_wide, long_per_name, 0.0)
    short_wide = np.where(short_mask_wide, short_per_name, 0.0)

    long_wide_df = pd.DataFrame(
        long_wide, index=sig_wide.index, columns=sig_wide.columns
    )
    short_wide_df = pd.DataFrame(
        short_wide, index=sig_wide.index, columns=sig_wide.columns
    )

    # Drop rows / symbols that are all zero (keep only rebalance dates
    # where we actually have positions). This matches legacy behavior of
    # only keeping dates with valid signal.
    # We keep only (date, symbol) pairs that appear in either leg.
    has_position = (long_wide_df != 0.0) | (short_wide_df != 0.0)

    long_series = long_wide_df[has_position].stack(future_stack=True)
    short_series = short_wide_df[has_position].stack(future_stack=True)
    long_series.name = "weight"
    short_series.name = "weight"
    long_series.index.names = ["datetime", "instrument"]
    short_series.index.names = ["datetime", "instrument"]
    # Drop NaN rows created by stack where has_position was False
    long_series = long_series.dropna()
    short_series = short_series.dropna()

    long_weights = long_series.to_frame("weight")
    short_weights = short_series.to_frame("weight")

    abs_series = long_series.abs() + short_series.abs()
    abs_weights = abs_series.to_frame("weight")

    # Vectorized turnover: total net weight per (date, symbol), diff along
    # date axis, absolute value, sum per date. First date = full investment
    # (row abs-sum), matching legacy semantics.
    total_wide = long_wide_df + short_wide_df
    # Drop any entirely-empty row so turnover only runs on actual rebalances
    active_rows = total_wide.abs().sum(axis=1) > 0
    total_wide = total_wide.loc[active_rows]

    diff = total_wide.diff()
    # First row: legacy counts full absolute investment as "opening turnover"
    diff.iloc[0] = total_wide.iloc[0]
    turnover = diff.abs().sum(axis=1)
    turnover.name = "turnover"
    turnover.index.name = "datetime"

    return ProxyPortfolio(
        long_weights=long_weights,
        short_weights=short_weights,
        abs_weights=abs_weights,
        turnover=turnover,
    )


# ---------------------------------------------------------------------------
# Weighted flag ratio (shared helper, vectorized)
# ---------------------------------------------------------------------------


def _weighted_flag_ratio(weights: pd.Series, flag: pd.Series) -> float:
    """Time-averaged fraction of weight in flagged positions.

    Vectorized via ``groupby(level=0)``.sum instead of the legacy per-date
    for-loop.
    """
    w = weights.astype(float)
    f = flag.astype(bool)
    common = w.index.intersection(f.index)
    if len(common) == 0:
        return 0.0
    w = w.loc[common]
    f = f.loc[common]

    w_flagged = w.where(f, 0.0)
    per_date_total = w.groupby(level=0).sum()
    per_date_flagged = w_flagged.groupby(level=0).sum()

    # Drop dates where total weight is zero
    ok = per_date_total != 0
    if not ok.any():
        return 0.0
    ratios = per_date_flagged[ok] / per_date_total[ok]
    return float(ratios.mean())


# ---------------------------------------------------------------------------
# Liquidity coverage
# ---------------------------------------------------------------------------


def compute_liquid_flag(
    amount_data: pd.DataFrame,
    *,
    window: int = 20,
    pct: float = 0.30,
) -> pd.Series:
    """Per (date, symbol) liquid flag — does not depend on any candidate.

    A stock is "liquid" on date d if its ``rolling(window).median()`` of
    ``$amount`` ending at d is ≥ the cross-sectional ``pct`` percentile
    of that median across all stocks on d. Build once per batch and reuse
    across every candidate's :func:`compute_liquidity_coverage` call —
    rolling-median + per-date quantile dominate the feasibility step.
    """
    amt_col = amount_data.columns[0]

    liq20 = (
        amount_data[amt_col]
        .groupby(level=1)
        .transform(lambda s: s.rolling(window, min_periods=1).median())
    )
    thresholds = liq20.groupby(level=0).quantile(pct)
    threshold_aligned = liq20.index.get_level_values(0).map(thresholds)
    return pd.Series(
        liq20.values >= threshold_aligned.values,
        index=liq20.index,
    )


def compute_liquidity_coverage(
    abs_weights: pd.DataFrame,
    liquid_flag: pd.Series,
) -> float:
    """Time-averaged liquidity coverage ratio in ``[0, 1]``.

    Pass the precomputed ``liquid_flag`` from :func:`compute_liquid_flag`
    (built once per batch from ``amount_data``).
    """
    w_col = abs_weights.columns[0]
    return _weighted_flag_ratio(abs_weights[w_col], liquid_flag)


# ---------------------------------------------------------------------------
# Tail concentration (top-k weight sum)
# ---------------------------------------------------------------------------


def compute_tail_concentration(
    abs_weights: pd.DataFrame,
    *,
    top_k: int = 10,
) -> float:
    """Top-k absolute weight sum, time-averaged.

    Vectorized via ``unstack`` to a (date × symbol) wide frame and a
    ``np.partition`` along axis=1 to extract the top-k per row in one
    pass — replaces the legacy ``groupby(level=0).apply(nlargest)``
    Python-per-date loop.
    """
    w_col = abs_weights.columns[0]
    wide = abs_weights[w_col].unstack(level=-1)
    arr = wide.to_numpy()  # (D, S), NaN where no position
    arr = np.where(np.isfinite(arr), arr, 0.0)

    totals = arr.sum(axis=1)
    keep = totals > 0
    if not keep.any():
        return float("nan")

    n_cols = arr.shape[1]
    k = min(top_k, n_cols)
    if k >= n_cols:
        top_sums = arr.sum(axis=1)
    else:
        # np.partition pushes the top-k values to the last k columns
        # (unsorted within), which is exactly what we need to sum.
        partitioned = np.partition(arr, n_cols - k, axis=1)
        top_sums = partitioned[:, n_cols - k:].sum(axis=1)

    ratios = np.where(keep, top_sums / np.where(keep, totals, 1), np.nan)
    finite = ratios[np.isfinite(ratios)]
    if finite.size == 0:
        return float("nan")
    return float(finite.mean())


# ---------------------------------------------------------------------------
# Small-cap concentration
# ---------------------------------------------------------------------------


def compute_small_cap_flag(
    market_cap: pd.DataFrame,
    *,
    pct: float = 0.30,
) -> pd.Series:
    """Per (date, symbol) small-cap flag — does not depend on any candidate.

    A stock is "small-cap" on date d if its market cap is ≤ the
    cross-sectional ``pct`` percentile on d. Build once per batch and
    reuse across every candidate's :func:`compute_small_cap_concentration`
    call.
    """
    cap_col = market_cap.columns[0]
    cap = market_cap[cap_col]
    thresholds = cap.groupby(level=0).quantile(pct)
    threshold_aligned = cap.index.get_level_values(0).map(thresholds)
    return pd.Series(
        cap.values <= threshold_aligned.values, index=cap.index
    )


def compute_small_cap_concentration(
    abs_weights: pd.DataFrame,
    small_cap_flag: pd.Series,
) -> float:
    """Weight fraction in small-cap stocks, time-averaged.

    Pass the precomputed ``small_cap_flag`` from
    :func:`compute_small_cap_flag` (built once per batch from
    ``market_cap``).
    """
    w_col = abs_weights.columns[0]
    return _weighted_flag_ratio(abs_weights[w_col], small_cap_flag)


# ---------------------------------------------------------------------------
# Half-life and holding period
# ---------------------------------------------------------------------------


def compute_signal_half_life(signal: pd.DataFrame, *, max_lag: int = 20) -> float:
    """Estimate **signal** half-life from mean autocorrelation decay.

    For each instrument, compute per-lag autocorrelation of the signal
    (after per-instrument dropna so ``lag=k`` means ``k observed dates
    apart``). Average across instruments per lag; the half-life is the
    first lag where mean autocorrelation drops below 0.5, or ``max_lag``
    if it never does.

    Naming note: this is the *signal* persistence half-life (a property
    of the factor time-series itself). The *IC-decay* half-life (a
    property of the factor's forward-return relationship) lives in
    ``research.compute.vectorized_ic.compute_ic_half_life``.

    Vectorization: per-instrument observed series are stacked into a
    ragged 2D array padded with NaN to a common length. Each lag's
    Pearson is computed on the padded panel via nan-aware reductions —
    one numpy pass per lag instead of (n_symbols × max_lag) inlined
    Python correlations.
    """
    col = signal.columns[0]
    sig_wide = signal[col].unstack(level=-1)
    arr = sig_wide.to_numpy()  # (D, S)

    if arr.shape[0] < max_lag + 5:
        return float(max_lag)

    finite_mask = np.isfinite(arr)
    n_finite_per_sym = finite_mask.sum(axis=0)

    # Compute variance per symbol over only its observed values, matching
    # legacy ``np.var(series.dropna())``. NaN-safe: if a symbol has no
    # observations, var stays 0 → filtered.
    with np.errstate(invalid="ignore"):
        var_per_sym = np.nanvar(arr, axis=0)

    keep_sym = (n_finite_per_sym >= max_lag + 5) & (var_per_sym > 0)
    if not keep_sym.any():
        return float(max_lag)

    # Build per-instrument observed series as a ragged padded array:
    # for each kept symbol, push its non-NaN values to the leading rows
    # and pad the tail with NaN. Result has shape (max_obs, n_kept) where
    # max_obs = max non-NaN count among kept symbols. Ranks/lags below
    # then operate over OBSERVED indices, matching legacy semantics.
    arr_keep = arr[:, keep_sym]
    finite_keep = finite_mask[:, keep_sym]

    n_per_sym = n_finite_per_sym[keep_sym]
    max_obs = int(n_per_sym.max())

    # Sort each column so finite values come first. argsort with -mask
    # places True (=mask) before False, so np.take_along_axis using the
    # sorted indices brings observed rows to the top.
    # Use stable sort to preserve the temporal order of observations.
    order = np.argsort(~finite_keep, axis=0, kind="stable")  # (D, S')
    obs_arr = np.take_along_axis(arr_keep, order, axis=0)[:max_obs, :]
    # Tail beyond each symbol's n_obs is non-finite garbage from the
    # original NaN cells (now sorted to the bottom but possibly within
    # max_obs for shorter series); explicitly mask via per-symbol cutoff.
    row_idx = np.arange(max_obs)[:, None]                    # (max_obs, 1)
    valid_obs = row_idx < n_per_sym[None, :]                 # (max_obs, S')
    obs_arr = np.where(valid_obs, obs_arr, np.nan)

    for lag in range(1, max_lag + 1):
        x = obs_arr[lag:, :]
        y = obs_arr[:-lag, :]
        m = np.isfinite(x) & np.isfinite(y)
        n_pair = m.sum(axis=0).astype(float)
        ok = n_pair > 0
        if not ok.any():
            continue
        with np.errstate(invalid="ignore"):
            x_clean = np.where(m, x, 0.0)
            y_clean = np.where(m, y, 0.0)
            sum_x = x_clean.sum(axis=0)
            sum_y = y_clean.sum(axis=0)
            mean_x = np.where(ok, sum_x / np.where(ok, n_pair, 1), 0.0)
            mean_y = np.where(ok, sum_y / np.where(ok, n_pair, 1), 0.0)
            xc = np.where(m, x - mean_x[None, :], 0.0)
            yc = np.where(m, y - mean_y[None, :], 0.0)
            cov = (xc * yc).sum(axis=0) / np.where(ok, n_pair, 1)
            var_x = (xc * xc).sum(axis=0) / np.where(ok, n_pair, 1)
            var_y = (yc * yc).sum(axis=0) / np.where(ok, n_pair, 1)
            denom = np.sqrt(var_x * var_y)
            corr = np.where(denom > 0, cov / denom, np.nan)
        finite_corr = corr[np.isfinite(corr)]
        if finite_corr.size == 0:
            continue
        mean_acf = float(finite_corr.mean())
        if mean_acf < 0.5:
            return float(lag)

    return float(max_lag)


def compute_signal_autocorr_lag1(
    signal: pd.DataFrame, *, max_dates: int = 50, min_obs: int = 10
) -> float | None:
    """Mean cross-sectional lag-1 factor autocorrelation.

    Delegates to ``core.factor_stats.factor_autocorrelation`` with
    ``lags=[1]`` and returns the single scalar. ``None`` when the input
    is too sparse to compute.
    """
    if signal is None or signal.empty:
        return None
    flat = multiindex_to_flat(signal)
    if flat.empty:
        return None
    out = factor_autocorrelation(
        flat, lags=[1], min_obs=min_obs, max_dates=max_dates
    )
    if not out:
        return None
    corr = out[0].get("corr")
    if corr is None or not np.isfinite(corr):
        return None
    return round(float(corr), 6)


# ---------------------------------------------------------------------------
# Rebalance stress
# ---------------------------------------------------------------------------


def compute_rebalance_stress(
    turnover: float,
    tail_concentration: float,
    liquidity_coverage_ratio: float,
) -> float:
    """Raw rebalance-stress scalar ``turnover × tail / max(lcr, 0.10)``."""
    lcr_safe = max(liquidity_coverage_ratio, 0.10)
    return float(turnover * tail_concentration / lcr_safe)
