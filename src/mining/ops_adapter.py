"""OpsAdapter — pandas-based operator wrappers for panel DataFrames.

All methods accept pd.Series with (datetime, instrument) MultiIndex.
- Time-series ops: group by 'instrument', compute along the time axis.
- Cross-sectional ops: group by 'datetime', compute across instruments.
- Element-wise ops: apply directly with no groupby.

This module is independent of the Qlib expression engine — it uses pandas
directly so Python factor code can call ops.std(...), ops.cs_rank(...) etc.
without importing Qlib operators or dealing with expression trees.
"""

from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd


class OpsAdapter:
    """Wraps common quantitative operators as Python callables for panel pd.Series."""

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _ts_apply(series: pd.Series, func: Callable, **kwargs) -> pd.Series:
        """Apply a time-series function per instrument.

        Groups by the 'instrument' level and applies *func* to each group.
        The function receives a single-instrument Series and must return a
        Series of the same length.
        """
        return series.groupby(level="instrument", group_keys=False).apply(func, **kwargs)

    # ------------------------------------------------------------------
    # Time-series ops  (per instrument along time axis)
    # ------------------------------------------------------------------

    def std(self, series: pd.Series, window: int) -> pd.Series:
        """Rolling standard deviation per instrument.

        Produces NaN for the first (window-1) observations of each instrument.
        """
        def _func(s: pd.Series) -> pd.Series:
            return s.rolling(window, min_periods=window).std()

        return self._ts_apply(series, _func)

    def mean(self, series: pd.Series, window: int) -> pd.Series:
        """Rolling mean per instrument.

        Produces NaN for the first (window-1) observations of each instrument.
        """
        def _func(s: pd.Series) -> pd.Series:
            return s.rolling(window, min_periods=window).mean()

        return self._ts_apply(series, _func)

    def ts_decay(self, series: pd.Series, window: int) -> pd.Series:
        """Linearly-weighted moving average (WMA) per instrument.

        Weights increase linearly so more-recent values carry more weight:
        w_i = i / sum(1..window), where i=1 is oldest and i=window is newest.
        Produces NaN for the first (window-1) observations of each instrument.
        """
        def _wma(arr: np.ndarray) -> float:
            n = len(arr)
            w = np.arange(1, n + 1, dtype=float)
            return float(np.dot(arr, w) / w.sum())

        def _func(s: pd.Series) -> pd.Series:
            return s.rolling(window, min_periods=window).apply(_wma, raw=True)

        return self._ts_apply(series, _func)

    def ts_auto_corr(self, series: pd.Series, window: int, lag: int = 1) -> pd.Series:
        """Rolling autocorrelation at a given lag, computed per instrument.

        Produces NaN for the first (window-1) observations of each instrument.
        """
        def _autocorr(arr: np.ndarray) -> float:
            if len(arr) <= lag + 1:
                return np.nan
            x, y = arr[:-lag], arr[lag:]
            sx, sy = np.std(x), np.std(y)
            if sx == 0 or sy == 0:
                return 0.0
            cc = np.corrcoef(x, y)
            v = cc[0, 1]
            return float(v) if not np.isnan(v) else 0.0

        def _func(s: pd.Series) -> pd.Series:
            return s.rolling(window, min_periods=window).apply(_autocorr, raw=True)

        return self._ts_apply(series, _func)

    def realized_vol(self, series: pd.Series, window: int) -> pd.Series:
        """Annualized realized volatility (RMS-based) per instrument.

        Computes sqrt(mean(r^2)) over the rolling window, then annualizes by
        multiplying by sqrt(252).  Using the RMS formula (rather than std)
        means constant non-zero returns produce a non-zero realized vol.
        Produces NaN for the first (window-1) observations of each instrument.
        """
        def _rvol(arr: np.ndarray) -> float:
            return float(np.sqrt(np.mean(arr ** 2))) * np.sqrt(252)

        def _func(s: pd.Series) -> pd.Series:
            return s.rolling(window, min_periods=window).apply(_rvol, raw=True)

        return self._ts_apply(series, _func)

    def ewm(self, series: pd.Series, span: int) -> pd.Series:
        """Exponentially weighted mean per instrument.

        Uses pandas ewm with adjust=True. Does not produce leading NaN.
        """
        def _func(s: pd.Series) -> pd.Series:
            return s.ewm(span=span, adjust=True).mean()

        return self._ts_apply(series, _func)

    def hhi(self, series: pd.Series, window: int) -> pd.Series:
        """Herfindahl-Hirschman Index of concentration per instrument.

        HHI = sum(share_i^2) where share_i = value_i / sum(values in window).
        Result is in (0, 1]. Produces NaN for the first (window-1) observations.
        """
        def _hhi_arr(arr: np.ndarray) -> float:
            total = np.nansum(arr)
            if total == 0:
                return np.nan
            shares = arr / total
            return float(np.nansum(shares ** 2))

        def _func(s: pd.Series) -> pd.Series:
            return s.rolling(window, min_periods=window).apply(_hhi_arr, raw=True)

        return self._ts_apply(series, _func)

    def delta(self, series: pd.Series, period: int) -> pd.Series:
        """Difference over *period* steps, computed per instrument.

        Equivalent to series.diff(period) applied within each instrument group.
        The first *period* rows of each instrument will be NaN.
        """
        def _func(s: pd.Series) -> pd.Series:
            return s.diff(period)

        return self._ts_apply(series, _func)

    def ts_argmax(self, series: pd.Series, window: int) -> pd.Series:
        """Rolling position of the maximum within the window, per instrument.

        Returns the 0-based index of the max element within each rolling window.
        Produces NaN for the first (window-1) observations of each instrument.
        """
        def _argmax(arr: np.ndarray) -> float:
            return float(np.argmax(arr))

        def _func(s: pd.Series) -> pd.Series:
            return s.rolling(window, min_periods=window).apply(_argmax, raw=True)

        return self._ts_apply(series, _func)

    def ts_argmin(self, series: pd.Series, window: int) -> pd.Series:
        """Rolling position of the minimum within the window, per instrument.

        Returns the 0-based index of the min element within each rolling window.
        Produces NaN for the first (window-1) observations of each instrument.
        """
        def _argmin(arr: np.ndarray) -> float:
            return float(np.argmin(arr))

        def _func(s: pd.Series) -> pd.Series:
            return s.rolling(window, min_periods=window).apply(_argmin, raw=True)

        return self._ts_apply(series, _func)

    def ts_corr(self, x: pd.Series, y: pd.Series, window: int) -> pd.Series:
        """Rolling Pearson correlation between two panel series, per instrument.

        Both *x* and *y* must have the same (datetime, instrument) MultiIndex.
        Produces NaN for the first (window-1) observations of each instrument.
        """
        # Align the two series just in case
        x, y = x.align(y)

        def _func_x(sx: pd.Series) -> pd.Series:
            inst = sx.index.get_level_values("instrument")[0]
            sy = y.xs(inst, level="instrument")
            return sx.droplevel("instrument").rolling(window, min_periods=window).corr(sy)

        results = []
        for inst, grp in x.groupby(level="instrument"):
            sx = grp.droplevel("instrument")
            sy = y.xs(inst, level="instrument")
            corr = sx.rolling(window, min_periods=window).corr(sy)
            corr.index = pd.MultiIndex.from_product(
                [corr.index, [inst]], names=["datetime", "instrument"]
            )
            results.append(corr)

        return pd.concat(results).sort_index()

    def ts_cov(self, x: pd.Series, y: pd.Series, window: int) -> pd.Series:
        """Rolling covariance between two panel series, per instrument.

        Both *x* and *y* must have the same (datetime, instrument) MultiIndex.
        Produces NaN for the first (window-1) observations of each instrument.
        """
        x, y = x.align(y)

        results = []
        for inst, grp in x.groupby(level="instrument"):
            sx = grp.droplevel("instrument")
            sy = y.xs(inst, level="instrument")
            cov = sx.rolling(window, min_periods=window).cov(sy)
            cov.index = pd.MultiIndex.from_product(
                [cov.index, [inst]], names=["datetime", "instrument"]
            )
            results.append(cov)

        return pd.concat(results).sort_index()

    # ------------------------------------------------------------------
    # Cross-sectional ops  (per date across instruments)
    # ------------------------------------------------------------------

    def cs_rank(self, series: pd.Series) -> pd.Series:
        """Percentile rank of each instrument within its date cross-section.

        Output is in [0, 1].  With N instruments, ranks are evenly spaced as
        0, 1/(N-1), …, 1.  Implemented as (rank - 1) / (N - 1) so the minimum
        always maps to 0 and the maximum always maps to 1.
        """
        def _rank01(s: pd.Series) -> pd.Series:
            n = len(s)
            if n <= 1:
                return pd.Series(0.0, index=s.index)
            r = s.rank(method="average")
            return (r - 1) / (n - 1)

        return series.groupby(level="datetime", group_keys=False).apply(_rank01)

    def cs_zscore(self, series: pd.Series) -> pd.Series:
        """Z-score of each instrument within its date cross-section.

        Output has cross-sectional mean ≈ 0 and std ≈ 1 per date.
        """
        def _zscore(s: pd.Series) -> pd.Series:
            mu = s.mean()
            sigma = s.std()
            if sigma == 0:
                return s * 0.0
            return (s - mu) / sigma

        return series.groupby(level="datetime", group_keys=False).apply(_zscore)

    # ------------------------------------------------------------------
    # Element-wise transforms
    # ------------------------------------------------------------------

    def signed_power(self, series: pd.Series, exp: float) -> pd.Series:
        """sign(x) * |x|^exp — non-linear transform preserving sign."""
        return np.sign(series) * np.abs(series) ** exp

    def tanh(self, series: pd.Series) -> pd.Series:
        """Element-wise hyperbolic tangent; output bounded in (-1, 1)."""
        return np.tanh(series)

    def safe_div(self, x: pd.Series, y: pd.Series) -> pd.Series:
        """Element-wise x/y replacing inf and NaN-from-zero-division with 0.

        Handles two edge cases:
        - nonzero / 0  → inf  → replaced with 0
        - 0 / 0        → NaN  → filled with 0 (only where y == 0)
        Regular NaN values in the input (missing data) are preserved as-is.
        """
        result = x / y
        # Replace inf/-inf (nonzero / zero)
        result = result.replace([np.inf, -np.inf], 0.0)
        # Replace NaN specifically where denominator is zero (0/0 case)
        zero_denom = y == 0
        result = result.where(~zero_denom, other=0.0)
        return result

    def log1p_abs(self, series: pd.Series) -> pd.Series:
        """sign(x) * log(1 + |x|) — signed log-compression."""
        return np.sign(series) * np.log1p(np.abs(series))
