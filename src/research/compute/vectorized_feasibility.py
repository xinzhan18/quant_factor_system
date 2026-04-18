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


def compute_liquidity_coverage(
    abs_weights: pd.DataFrame,
    amount_data: pd.DataFrame,
    *,
    window: int = 20,
    pct: float = 0.30,
) -> float:
    """Time-averaged liquidity coverage ratio in ``[0, 1]``.

    A stock is "liquid" when its ``rolling(window).median()`` of ``$amount``
    is at or above the cross-sectional ``pct`` percentile on that date.
    """
    amt_col = amount_data.columns[0]

    # Rolling median per instrument
    liq20 = (
        amount_data[amt_col]
        .groupby(level=1)
        .transform(lambda s: s.rolling(window, min_periods=1).median())
    )

    # Cross-sectional percentile threshold per date.
    # Using groupby(level=0).transform(quantile) would also work but is
    # slower than a one-liner via .quantile and map.
    thresholds = liq20.groupby(level=0).quantile(pct)
    threshold_aligned = liq20.index.get_level_values(0).map(thresholds)

    liquid_flag = pd.Series(
        liq20.values >= threshold_aligned.values,
        index=liq20.index,
    )

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

    Vectorized via ``groupby(level=0).apply`` on a per-date Series. The
    legacy version also used apply — tail concentration is inherently
    ranked-per-date so a small apply is unavoidable without rewriting in
    pure numpy. ``top_k`` is typically ≤ 20 so this is fast in practice.
    """
    w_col = abs_weights.columns[0]

    def _date_tail(group: pd.Series) -> float:
        total = group.sum()
        if total == 0:
            return float("nan")
        top = group.nlargest(min(top_k, len(group))).sum()
        return top / total

    per_date = abs_weights[w_col].groupby(level=0).apply(_date_tail)
    return float(per_date.mean())


# ---------------------------------------------------------------------------
# Small-cap concentration
# ---------------------------------------------------------------------------


def compute_small_cap_concentration(
    abs_weights: pd.DataFrame,
    market_cap: pd.DataFrame,
    *,
    pct: float = 0.30,
) -> float:
    """Weight fraction in small-cap stocks, time-averaged."""
    cap_col = market_cap.columns[0]
    w_col = abs_weights.columns[0]

    cap = market_cap[cap_col]

    thresholds = cap.groupby(level=0).quantile(pct)
    threshold_aligned = cap.index.get_level_values(0).map(thresholds)
    small_flag = pd.Series(
        cap.values <= threshold_aligned.values, index=cap.index
    )

    return _weighted_flag_ratio(abs_weights[w_col], small_flag)


# ---------------------------------------------------------------------------
# Half-life and holding period
# ---------------------------------------------------------------------------


def compute_signal_half_life(signal: pd.DataFrame, *, max_lag: int = 20) -> float:
    """Estimate **signal** half-life from mean autocorrelation decay.

    For each instrument, compute per-lag autocorrelation of the signal.
    Average across instruments per lag; the half-life is the first lag
    where mean autocorrelation drops below 0.5, or ``max_lag`` if it
    never does.

    Naming note: this is the *signal* persistence half-life (a property
    of the factor time-series itself). The *IC-decay* half-life (a
    property of the factor's forward-return relationship) lives in
    ``research.compute.vectorized_ic.compute_ic_half_life``.
    """
    col = signal.columns[0]
    acf_by_lag: dict[int, list[float]] = {lag: [] for lag in range(1, max_lag + 1)}

    for _inst, group in signal[col].groupby(level=1):
        series = group.droplevel(1).dropna()
        if len(series) < max_lag + 5:
            continue
        arr = series.values
        if np.var(arr) == 0:
            continue
        for lag in range(1, max_lag + 1):
            corr = np.corrcoef(arr[:-lag], arr[lag:])[0, 1]
            if np.isfinite(corr):
                acf_by_lag[lag].append(corr)

    for lag in range(1, max_lag + 1):
        vals = acf_by_lag[lag]
        if not vals:
            continue
        mean_acf = float(np.mean(vals))
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
