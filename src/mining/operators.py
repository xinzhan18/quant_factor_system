"""Custom Qlib operator extensions for factor mining.

Provides both raw functions (for standalone use/testing) and Qlib ExpressionOps
class-based operators (for use within the Qlib expression engine).

Operator categories:
  - Non-linear transforms: SignedPower, Tanh, Exp, Sigmoid, Softmax
  - Normalization: Scale (min-max), Zscore, Winsorize
  - Time-series: TsDecay, TsMomentum, TsAutoCorr, RealizedVol
  - Microstructure: AmihudIlliq, HHI (volume concentration)
"""

from __future__ import annotations

import math
from typing import Callable, Dict

import numpy as np

# ---------------------------------------------------------------------------
# Raw functions (standalone use, testing)
# ---------------------------------------------------------------------------


def signed_power(x: float, p: float) -> float:
    """sign(x) * |x|^p — non-linear transformation preserving sign."""
    if x == 0:
        return 0.0
    return math.copysign(abs(x) ** p, x)


def tanh_op(x: float) -> float:
    """Bounded non-linearity."""
    return math.tanh(x)


def scale_cs(values: np.ndarray) -> np.ndarray:
    """Cross-sectional normalization to [-1, 1]."""
    if len(values) <= 1:
        return np.zeros_like(values)
    vmin, vmax = values.min(), values.max()
    if vmax == vmin:
        return np.zeros_like(values)
    return 2.0 * (values - vmin) / (vmax - vmin) - 1.0


def ts_decay(values: np.ndarray, period: int) -> float:
    """Time-decay weighted average. More recent values get higher weight.

    Weights: w_i = i / sum(1..period), where i=1 is oldest and i=period is newest.
    """
    n = min(len(values), period)
    v = values[-n:]
    weights = np.arange(1, n + 1, dtype=float)
    return float(np.dot(v, weights) / weights.sum())


def exp_op(x: float, clamp: float = 20.0) -> float:
    """Exponential with clamping to prevent overflow.

    Upper bound clamped at ``clamp`` (default 20). Very negative inputs
    naturally converge to 0.0 via ``math.exp`` without needing a lower clamp.
    """
    return math.exp(min(x, clamp))


def sigmoid(x: float) -> float:
    """Sigmoid: 1 / (1 + exp(-x)), maps R -> (0, 1)."""
    x_clamped = max(-20.0, min(x, 20.0))
    return 1.0 / (1.0 + math.exp(-x_clamped))


def softmax_cs(values: np.ndarray) -> np.ndarray:
    """Cross-sectional softmax normalization. Output sums to 1."""
    if len(values) == 0:
        return values
    shifted = values - values.max()  # numerical stability
    e = np.exp(shifted)
    return e / e.sum()


def zscore_cs(values: np.ndarray) -> np.ndarray:
    """Cross-sectional z-score: (x - mean) / std."""
    if len(values) <= 1:
        return np.zeros_like(values)
    mean, std = values.mean(), values.std()
    if std == 0:
        return np.zeros_like(values)
    return (values - mean) / std


def winsorize(values: np.ndarray, n_sigma: float = 3.0) -> np.ndarray:
    """Clip values to [mean - n*std, mean + n*std]."""
    if len(values) <= 1:
        return values.copy()
    mean, std = values.mean(), values.std()
    if std == 0:
        return values.copy()
    return np.clip(values, mean - n_sigma * std, mean + n_sigma * std)


def ts_momentum(values: np.ndarray, period: int) -> float:
    """Period return: values[-1] / values[-period] - 1."""
    n = min(len(values), period)
    if n < 1 or values[-n] == 0:
        return 0.0
    return float(values[-1] / values[-n] - 1)


def ts_autocorr(values: np.ndarray, period: int, lag: int = 1) -> float:
    """Autocorrelation of the series at given lag within the window."""
    n = min(len(values), period)
    v = values[-n:]
    if n <= lag + 2:
        return 0.0
    from scipy.stats import pearsonr
    x, y = v[:-lag], v[lag:]
    if np.std(x) == 0 or np.std(y) == 0:
        return 0.0
    corr, _ = pearsonr(x, y)
    return float(corr) if not np.isnan(corr) else 0.0


def realized_vol(returns: np.ndarray, period: int) -> float:
    """Realized volatility: sqrt(sum(ret^2)) over the window."""
    n = min(len(returns), period)
    v = returns[-n:]
    return float(np.sqrt(np.sum(v ** 2)))


def amihud_illiq(returns: np.ndarray, volume: np.ndarray, period: int) -> float:
    """Amihud illiquidity: mean(|ret| / volume) over the window."""
    n = min(len(returns), min(len(volume), period))
    r = np.abs(returns[-n:])
    vol = volume[-n:]
    mask = vol > 0
    if mask.sum() == 0:
        return 0.0
    return float(np.mean(r[mask] / vol[mask]))


def hhi(volume: np.ndarray, period: int) -> float:
    """Herfindahl-Hirschman Index on volume shares: sum(share_i^2)."""
    n = min(len(volume), period)
    v = volume[-n:]
    total = v.sum()
    if total == 0:
        return 0.0
    shares = v / total
    return float(np.sum(shares ** 2))


# ---------------------------------------------------------------------------
# Qlib ExpressionOps classes (registered with Qlib expression engine)
# ---------------------------------------------------------------------------

from qlib.data.ops import PairOperator, ElemOperator, Rolling, NpElemOperator, NpPairOperator
from qlib.data.base import Expression

import pandas as pd


# --- Non-linear transforms ---

class SignedPowerOp(NpPairOperator):
    """``SignedPower($close, 0.5)`` — sign(x) * |x|^p"""

    def __init__(self, feature_left, feature_right):
        super().__init__(feature_left, feature_right, "power")

    def _load_internal(self, instrument, start_index, end_index, *args):
        if isinstance(self.feature_left, Expression):
            series_left = self.feature_left.load(instrument, start_index, end_index, *args)
        else:
            series_left = self.feature_left
        if isinstance(self.feature_right, Expression):
            series_right = self.feature_right.load(instrument, start_index, end_index, *args)
        else:
            series_right = self.feature_right
        return np.sign(series_left) * np.abs(series_left) ** series_right


class TanhOp(NpElemOperator):
    """``Tanh($close)`` — bounded [-1, 1] non-linearity"""

    def __init__(self, feature):
        super().__init__(feature, "tanh")


class ExpOp(NpElemOperator):
    """``Exp($close)`` — exponential with clamping [-20, 20]"""

    def __init__(self, feature):
        super().__init__(feature, "exp")

    def _load_internal(self, instrument, start_index, end_index, *args):
        series = self.feature.load(instrument, start_index, end_index, *args)
        return np.exp(np.clip(series, -20.0, 20.0))


class SigmoidOp(ElemOperator):
    """``Sigmoid($close)`` — maps R to (0, 1)"""

    def _load_internal(self, instrument, start_index, end_index, *args):
        series = self.feature.load(instrument, start_index, end_index, *args)
        clamped = np.clip(series, -20.0, 20.0)
        return 1.0 / (1.0 + np.exp(-clamped))


class SoftmaxOp(ElemOperator):
    """``Softmax($close)`` — cross-sectional softmax, output sums to 1"""

    def _load_internal(self, instrument, start_index, end_index, *args):
        series = self.feature.load(instrument, start_index, end_index, *args)
        shifted = series - np.nanmax(series.values)
        e = np.exp(shifted)
        s = np.nansum(e.values)
        return e / s if s != 0 else e * 0.0


# --- Normalization ---

class ScaleOp(ElemOperator):
    """``Scale($close)`` — min-max normalization to [-1, 1]"""

    def _load_internal(self, instrument, start_index, end_index, *args):
        series = self.feature.load(instrument, start_index, end_index, *args)
        vmin = np.nanmin(series.values)
        vmax = np.nanmax(series.values)
        if vmax == vmin:
            return series * 0.0
        return 2.0 * (series - vmin) / (vmax - vmin) - 1.0


class ZscoreOp(ElemOperator):
    """``Zscore($close)`` — (x - mean) / std"""

    def _load_internal(self, instrument, start_index, end_index, *args):
        series = self.feature.load(instrument, start_index, end_index, *args)
        mean = np.nanmean(series.values)
        std = np.nanstd(series.values)
        if std == 0:
            return series * 0.0
        return (series - mean) / std


class WinsorizeOp(ElemOperator):
    """``Winsorize($close)`` — clip to [mean-3*std, mean+3*std]"""

    def _load_internal(self, instrument, start_index, end_index, *args):
        series = self.feature.load(instrument, start_index, end_index, *args)
        mean = np.nanmean(series.values)
        std = np.nanstd(series.values)
        if std == 0:
            return series
        return series.clip(lower=mean - 3.0 * std, upper=mean + 3.0 * std)


# --- Time-series ---
# NOTE: Rolling._load_internal uses pandas .rolling(N).{func}() by default.
# Custom operators must override _load_internal to apply custom window logic,
# and pass a dummy func string to super().__init__().


class TsDecayOp(Rolling):
    """``TsDecay($close, 10)`` — linearly weighted average, recent values heavier"""

    def __init__(self, feature, N):
        super().__init__(feature, N, "ts_decay")

    def _load_internal(self, instrument, start_index, end_index, *args):
        series = self.feature.load(instrument, start_index, end_index, *args)

        def _apply(arr):
            n = len(arr)
            w = np.arange(1, n + 1, dtype=float)
            return np.dot(arr, w) / w.sum()

        return series.rolling(self.N, min_periods=1).apply(_apply, raw=True)


class TsMomentumOp(Rolling):
    """``TsMomentum($close, 20)`` — period return: last/first - 1"""

    def __init__(self, feature, N):
        super().__init__(feature, N, "ts_momentum")

    def _load_internal(self, instrument, start_index, end_index, *args):
        series = self.feature.load(instrument, start_index, end_index, *args)

        def _apply(arr):
            if len(arr) == 0 or arr[0] == 0:
                return np.nan
            return arr[-1] / arr[0] - 1

        return series.rolling(self.N, min_periods=1).apply(_apply, raw=True)


class TsAutoCorrelation(Rolling):
    """``TsAutoCorr($close, 20)`` — lag-1 autocorrelation of the series"""

    def __init__(self, feature, N):
        super().__init__(feature, N, "ts_autocorr")

    def _load_internal(self, instrument, start_index, end_index, *args):
        series = self.feature.load(instrument, start_index, end_index, *args)

        def _apply(arr):
            if len(arr) < 4:
                return np.nan
            x, y = arr[:-1], arr[1:]
            sx, sy = np.std(x), np.std(y)
            if sx == 0 or sy == 0:
                return 0.0
            return float(np.corrcoef(x, y)[0, 1])

        return series.rolling(self.N, min_periods=4).apply(_apply, raw=True)


class RealizedVolOp(Rolling):
    """``RealizedVol($returns, 20)`` — sqrt(sum(x^2)), realized volatility"""

    def __init__(self, feature, N):
        super().__init__(feature, N, "realized_vol")

    def _load_internal(self, instrument, start_index, end_index, *args):
        series = self.feature.load(instrument, start_index, end_index, *args)
        return series.rolling(self.N, min_periods=1).apply(
            lambda arr: np.sqrt(np.nansum(arr ** 2)), raw=True
        )


class TsEntropyOp(Rolling):
    """``TsEntropy($returns, 20)`` — Shannon entropy of return distribution"""

    def __init__(self, feature, N):
        super().__init__(feature, N, "ts_entropy")

    def _load_internal(self, instrument, start_index, end_index, *args):
        series = self.feature.load(instrument, start_index, end_index, *args)

        def _apply(arr):
            s = arr[~np.isnan(arr)]
            if len(s) < 2:
                return np.nan
            counts, _ = np.histogram(s, bins=min(10, len(s)))
            probs = counts / counts.sum()
            probs = probs[probs > 0]
            return -float(np.sum(probs * np.log(probs)))

        return series.rolling(self.N, min_periods=2).apply(_apply, raw=True)


# --- Rolling extremes & statistics ---

class TsMaxOp(Rolling):
    """``TsMax($close, 20)`` — rolling maximum over N periods"""

    def __init__(self, feature, N):
        super().__init__(feature, N, "ts_max")

    def _load_internal(self, instrument, start_index, end_index, *args):
        series = self.feature.load(instrument, start_index, end_index, *args)
        return series.rolling(self.N, min_periods=1).max()


class TsMinOp(Rolling):
    """``TsMin($close, 20)`` — rolling minimum over N periods"""

    def __init__(self, feature, N):
        super().__init__(feature, N, "ts_min")

    def _load_internal(self, instrument, start_index, end_index, *args):
        series = self.feature.load(instrument, start_index, end_index, *args)
        return series.rolling(self.N, min_periods=1).min()


class TsRankOp(Rolling):
    """``TsRank($close, 20)`` — time-series percentile rank (0-1) over N periods"""

    def __init__(self, feature, N):
        super().__init__(feature, N, "ts_rank")

    def _load_internal(self, instrument, start_index, end_index, *args):
        series = self.feature.load(instrument, start_index, end_index, *args)

        def _apply(arr):
            n = len(arr)
            if n < 2:
                return 0.5
            # Rank of last value among window values
            return float((arr < arr[-1]).sum()) / (n - 1)

        return series.rolling(self.N, min_periods=2).apply(_apply, raw=True)


class TsSkewOp(Rolling):
    """``TsSkew($close, 20)`` — rolling skewness over N periods"""

    def __init__(self, feature, N):
        super().__init__(feature, N, "ts_skew")

    def _load_internal(self, instrument, start_index, end_index, *args):
        series = self.feature.load(instrument, start_index, end_index, *args)
        return series.rolling(self.N, min_periods=3).skew()


class TsKurtOp(Rolling):
    """``TsKurt($close, 20)`` — rolling excess kurtosis over N periods"""

    def __init__(self, feature, N):
        super().__init__(feature, N, "ts_kurt")

    def _load_internal(self, instrument, start_index, end_index, *args):
        series = self.feature.load(instrument, start_index, end_index, *args)
        return series.rolling(self.N, min_periods=4).kurt()


class WMAOp(Rolling):
    """``WMA($close, 20)`` — linearly weighted moving average (same as TsDecay but clearer name)"""

    def __init__(self, feature, N):
        super().__init__(feature, N, "wma")

    def _load_internal(self, instrument, start_index, end_index, *args):
        series = self.feature.load(instrument, start_index, end_index, *args)

        def _apply(arr):
            n = len(arr)
            w = np.arange(1, n + 1, dtype=float)
            return np.dot(arr, w) / w.sum()

        return series.rolling(self.N, min_periods=1).apply(_apply, raw=True)


# --- Microstructure ---


class AmihudIlliqOp(Rolling):
    """``AmihudIlliq($returns, 20)`` — mean(|x|) as illiquidity proxy

    Note: True Amihud requires |return|/volume. This simplified version
    uses |return| only. For the full version, use PairRolling with volume.
    """

    def __init__(self, feature, N):
        super().__init__(feature, N, "amihud_illiq")

    def _load_internal(self, instrument, start_index, end_index, *args):
        series = self.feature.load(instrument, start_index, end_index, *args)
        return series.abs().rolling(self.N, min_periods=1).mean()


class HHIOp(Rolling):
    """``HHI($volume, 20)`` — Herfindahl index of volume concentration"""

    def __init__(self, feature, N):
        super().__init__(feature, N, "hhi")

    def _load_internal(self, instrument, start_index, end_index, *args):
        series = self.feature.load(instrument, start_index, end_index, *args)

        def _apply(arr):
            total = np.nansum(arr)
            if total == 0:
                return np.nan
            shares = arr / total
            return np.nansum(shares ** 2)

        return series.rolling(self.N, min_periods=1).apply(_apply, raw=True)


# --- Cross-sectional operators ---
# These load ALL instruments' data to compute cross-sectional statistics.
# First call per expression is slow (builds cache), subsequent calls are instant.

# Shared cache and calendar for all cross-sectional operators
_CS_CACHE: Dict[str, Dict[str, Dict[int, float]]] = {}
_CAL_MAP: Dict = None


def _get_cal_map():
    global _CAL_MAP
    if _CAL_MAP is None:
        from qlib.data import D
        cal = D.calendar(start_time='2015-01-01', end_time='2026-12-31')
        _CAL_MAP = {d: i for i, d in enumerate(cal)}
    return _CAL_MAP


def _build_cs_cache(expr_key: str, agg_func: str) -> Dict[str, Dict[int, float]]:
    """Build cross-sectional cache: {instrument: {cal_idx: value}}"""
    cache_key = f"{agg_func}:{expr_key}"
    if cache_key in _CS_CACHE:
        return _CS_CACHE[cache_key]

    from qlib.data import D
    cal_map = _get_cal_map()

    inst_dict = D.instruments('all')
    all_df = D.features(inst_dict, fields=[expr_key],
                        start_time='2015-01-01', end_time='2026-12-31')
    flat = all_df.reset_index()
    flat.columns = ['instrument', 'datetime', 'value']

    if agg_func == 'rank':
        flat['result'] = flat.groupby('datetime')['value'].rank(pct=True)
    elif agg_func == 'zscore':
        g = flat.groupby('datetime')['value']
        flat['result'] = (flat['value'] - g.transform('mean')) / g.transform('std')
    elif agg_func == 'demean':
        flat['result'] = flat['value'] - flat.groupby('datetime')['value'].transform('mean')
    else:
        flat['result'] = flat['value']

    cache = {}
    for inst, grp in flat.groupby('instrument'):
        idx_val = {}
        for dt, val in zip(grp['datetime'], grp['result']):
            cal_idx = cal_map.get(dt)
            if cal_idx is not None and not np.isnan(val):
                idx_val[cal_idx] = val
        cache[inst] = idx_val

    _CS_CACHE[cache_key] = cache
    return cache


def _extract_from_cache(cache, instrument, series):
    """Extract cached values for a specific instrument, aligned to series index."""
    inst_data = cache.get(instrument, {})
    result = pd.Series(np.nan, index=series.index)
    for idx in series.index:
        if idx in inst_data:
            result[idx] = inst_data[idx]
    return result


class CsRankOp(ElemOperator):
    """``CsRank($pe_ratio)`` — cross-sectional percentile rank (0-1) among all stocks per day."""

    def _load_internal(self, instrument, start_index, end_index, *args):
        series = self.feature.load(instrument, start_index, end_index, *args)
        cache = _build_cs_cache(str(self.feature), 'rank')
        return _extract_from_cache(cache, instrument, series)


class CsZscoreOp(ElemOperator):
    """``CsZscore($pe_ratio)`` — cross-sectional z-score: (x - mean) / std per day."""

    def _load_internal(self, instrument, start_index, end_index, *args):
        series = self.feature.load(instrument, start_index, end_index, *args)
        cache = _build_cs_cache(str(self.feature), 'zscore')
        return _extract_from_cache(cache, instrument, series)


class CsDemeanOp(ElemOperator):
    """``CsDemean($pe_ratio)`` — cross-sectional de-mean: x - mean per day."""

    def _load_internal(self, instrument, start_index, end_index, *args):
        series = self.feature.load(instrument, start_index, end_index, *args)
        cache = _build_cs_cache(str(self.feature), 'demean')
        return _extract_from_cache(cache, instrument, series)


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

# All custom operator classes, keyed by their expression name
_CUSTOM_OPS: Dict[str, type] = {
    # Non-linear
    "SignedPower": SignedPowerOp,
    "Tanh": TanhOp,
    "Exp": ExpOp,
    "Sigmoid": SigmoidOp,
    "Softmax": SoftmaxOp,
    # Normalization
    "Scale": ScaleOp,
    "Zscore": ZscoreOp,
    "Winsorize": WinsorizeOp,
    # Time-series
    "TsDecay": TsDecayOp,
    "TsMomentum": TsMomentumOp,
    "TsAutoCorr": TsAutoCorrelation,
    "RealizedVol": RealizedVolOp,
    "TsEntropy": TsEntropyOp,
    # Rolling extremes & statistics
    "TsMax": TsMaxOp,
    "TsMin": TsMinOp,
    "TsRank": TsRankOp,
    "TsSkew": TsSkewOp,
    "TsKurt": TsKurtOp,
    "WMA": WMAOp,
    # Microstructure
    "AmihudIlliq": AmihudIlliqOp,
    "HHI": HHIOp,
    # Cross-sectional
    "CsRank": CsRankOp,
    "CsZscore": CsZscoreOp,
    "CsDemean": CsDemeanOp,
}


def register_custom_operators() -> Dict[str, type]:
    """Register all custom operators with Qlib's expression engine.

    Directly inserts into ``Operators._ops`` dict keyed by expression name
    (e.g. ``TsDecay``) rather than class name (``TsDecayOp``), since
    ``Operators.register()`` uses ``cls.__name__`` which doesn't match.

    Returns dict of {name: class} for reference.
    """
    from qlib.data.ops import Operators
    for name, cls in _CUSTOM_OPS.items():
        Operators._ops[name] = cls
    return dict(_CUSTOM_OPS)
