"""Custom Qlib operator extensions for the research pipeline.

Rewrite of ``mining.operators`` with identical Qlib operator classes and
the same registration mechanism (``Operators._ops[name] = cls``).

Operator categories:
  - Non-linear transforms: SignedPower, Tanh, Exp, Sigmoid, Softmax
  - Normalization: Scale, Zscore, Winsorize
  - Time-series: TsDecay, TsMomentum, TsAutoCorr, RealizedVol, TsEntropy
  - Rolling extremes: TsMax, TsMin, TsRank, TsSkew, TsKurt, WMA
  - Microstructure: AmihudIlliq, HHI
  - Cross-sectional: CsRank, CsZscore, CsDemean

IMPORTANT: After calling ``register_custom_operators()`` you must also
set ``C.kernels = 1`` — worker processes do not inherit the ``_ops`` registry.
"""

from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd

from qlib.data.ops import (
    ElemOperator,
    NpElemOperator,
    NpPairOperator,
    Rolling,
)
from qlib.data.base import Expression


# ===================================================================
# Non-linear transforms
# ===================================================================


class SignedPowerOp(NpPairOperator):
    """``SignedPower($close, 0.5)`` -- sign(x) * |x|^p"""

    def __init__(self, feature_left, feature_right):
        super().__init__(feature_left, feature_right, "power")

    def _load_internal(self, instrument, start_index, end_index, *args):
        series_left = (
            self.feature_left.load(instrument, start_index, end_index, *args)
            if isinstance(self.feature_left, Expression)
            else self.feature_left
        )
        series_right = (
            self.feature_right.load(instrument, start_index, end_index, *args)
            if isinstance(self.feature_right, Expression)
            else self.feature_right
        )
        return np.sign(series_left) * np.abs(series_left) ** series_right


class TanhOp(NpElemOperator):
    """``Tanh($close)`` -- bounded [-1, 1] non-linearity"""

    def __init__(self, feature):
        super().__init__(feature, "tanh")


class ExpOp(NpElemOperator):
    """``Exp($close)`` -- exponential with clamping [-20, 20]"""

    def __init__(self, feature):
        super().__init__(feature, "exp")

    def _load_internal(self, instrument, start_index, end_index, *args):
        series = self.feature.load(instrument, start_index, end_index, *args)
        return np.exp(np.clip(series, -20.0, 20.0))


class SigmoidOp(ElemOperator):
    """``Sigmoid($close)`` -- maps R to (0, 1)"""

    def _load_internal(self, instrument, start_index, end_index, *args):
        series = self.feature.load(instrument, start_index, end_index, *args)
        clamped = np.clip(series, -20.0, 20.0)
        return 1.0 / (1.0 + np.exp(-clamped))


class SoftmaxOp(ElemOperator):
    """``Softmax($close)`` -- cross-sectional softmax, output sums to 1"""

    def _load_internal(self, instrument, start_index, end_index, *args):
        series = self.feature.load(instrument, start_index, end_index, *args)
        shifted = series - np.nanmax(series.values)
        e = np.exp(shifted)
        s = np.nansum(e.values)
        return e / s if s != 0 else e * 0.0


# ===================================================================
# Normalization
# ===================================================================


class ScaleOp(ElemOperator):
    """``Scale($close)`` -- min-max normalization to [-1, 1]"""

    def _load_internal(self, instrument, start_index, end_index, *args):
        series = self.feature.load(instrument, start_index, end_index, *args)
        vmin = np.nanmin(series.values)
        vmax = np.nanmax(series.values)
        if vmax == vmin:
            return series * 0.0
        return 2.0 * (series - vmin) / (vmax - vmin) - 1.0


class ZscoreOp(ElemOperator):
    """``Zscore($close)`` -- (x - mean) / std"""

    def _load_internal(self, instrument, start_index, end_index, *args):
        series = self.feature.load(instrument, start_index, end_index, *args)
        mean = np.nanmean(series.values)
        std = np.nanstd(series.values)
        if std == 0:
            return series * 0.0
        return (series - mean) / std


class WinsorizeOp(ElemOperator):
    """``Winsorize($close)`` -- clip to [mean-3*std, mean+3*std]"""

    def _load_internal(self, instrument, start_index, end_index, *args):
        series = self.feature.load(instrument, start_index, end_index, *args)
        mean = np.nanmean(series.values)
        std = np.nanstd(series.values)
        if std == 0:
            return series
        return series.clip(lower=mean - 3.0 * std, upper=mean + 3.0 * std)


# ===================================================================
# Time-series
# ===================================================================


class TsDecayOp(Rolling):
    """``TsDecay($close, 10)`` -- linearly weighted average, recent values heavier"""

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
    """``TsMomentum($close, 20)`` -- period return: last/first - 1"""

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
    """``TsAutoCorr($close, 20)`` -- lag-1 autocorrelation"""

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
    """``RealizedVol($returns, 20)`` -- sqrt(sum(x^2))"""

    def __init__(self, feature, N):
        super().__init__(feature, N, "realized_vol")

    def _load_internal(self, instrument, start_index, end_index, *args):
        series = self.feature.load(instrument, start_index, end_index, *args)
        return series.rolling(self.N, min_periods=1).apply(
            lambda arr: np.sqrt(np.nansum(arr**2)), raw=True
        )


class TsEntropyOp(Rolling):
    """``TsEntropy($returns, 20)`` -- Shannon entropy of return distribution"""

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


# ===================================================================
# Rolling extremes and statistics
# ===================================================================


class TsMaxOp(Rolling):
    """``TsMax($close, 20)`` -- rolling maximum"""

    def __init__(self, feature, N):
        super().__init__(feature, N, "ts_max")

    def _load_internal(self, instrument, start_index, end_index, *args):
        series = self.feature.load(instrument, start_index, end_index, *args)
        return series.rolling(self.N, min_periods=1).max()


class TsMinOp(Rolling):
    """``TsMin($close, 20)`` -- rolling minimum"""

    def __init__(self, feature, N):
        super().__init__(feature, N, "ts_min")

    def _load_internal(self, instrument, start_index, end_index, *args):
        series = self.feature.load(instrument, start_index, end_index, *args)
        return series.rolling(self.N, min_periods=1).min()


class TsRankOp(Rolling):
    """``TsRank($close, 20)`` -- time-series percentile rank (0-1)"""

    def __init__(self, feature, N):
        super().__init__(feature, N, "ts_rank")

    def _load_internal(self, instrument, start_index, end_index, *args):
        series = self.feature.load(instrument, start_index, end_index, *args)

        def _apply(arr):
            n = len(arr)
            if n < 2:
                return 0.5
            return float((arr < arr[-1]).sum()) / (n - 1)

        return series.rolling(self.N, min_periods=2).apply(_apply, raw=True)


class TsSkewOp(Rolling):
    """``TsSkew($close, 20)`` -- rolling skewness"""

    def __init__(self, feature, N):
        super().__init__(feature, N, "ts_skew")

    def _load_internal(self, instrument, start_index, end_index, *args):
        series = self.feature.load(instrument, start_index, end_index, *args)
        return series.rolling(self.N, min_periods=3).skew()


class TsKurtOp(Rolling):
    """``TsKurt($close, 20)`` -- rolling excess kurtosis"""

    def __init__(self, feature, N):
        super().__init__(feature, N, "ts_kurt")

    def _load_internal(self, instrument, start_index, end_index, *args):
        series = self.feature.load(instrument, start_index, end_index, *args)
        return series.rolling(self.N, min_periods=4).kurt()


class WMAOp(Rolling):
    """``WMA($close, 20)`` -- linearly weighted moving average"""

    def __init__(self, feature, N):
        super().__init__(feature, N, "wma")

    def _load_internal(self, instrument, start_index, end_index, *args):
        series = self.feature.load(instrument, start_index, end_index, *args)

        def _apply(arr):
            n = len(arr)
            w = np.arange(1, n + 1, dtype=float)
            return np.dot(arr, w) / w.sum()

        return series.rolling(self.N, min_periods=1).apply(_apply, raw=True)


# ===================================================================
# Microstructure
# ===================================================================


class AmihudIlliqOp(Rolling):
    """``AmihudIlliq($returns, 20)`` -- mean(|x|) illiquidity proxy"""

    def __init__(self, feature, N):
        super().__init__(feature, N, "amihud_illiq")

    def _load_internal(self, instrument, start_index, end_index, *args):
        series = self.feature.load(instrument, start_index, end_index, *args)
        return series.abs().rolling(self.N, min_periods=1).mean()


class HHIOp(Rolling):
    """``HHI($volume, 20)`` -- Herfindahl index of volume concentration"""

    def __init__(self, feature, N):
        super().__init__(feature, N, "hhi")

    def _load_internal(self, instrument, start_index, end_index, *args):
        series = self.feature.load(instrument, start_index, end_index, *args)

        def _apply(arr):
            total = np.nansum(arr)
            if total == 0:
                return np.nan
            shares = arr / total
            return np.nansum(shares**2)

        return series.rolling(self.N, min_periods=1).apply(_apply, raw=True)


# ===================================================================
# Cross-sectional operators
# ===================================================================

_CS_CACHE: Dict[str, Dict[str, Dict[int, float]]] = {}
_CAL_MAP: Dict = None


def _get_cal_map():
    global _CAL_MAP
    if _CAL_MAP is None:
        from qlib.data import D

        cal = D.calendar(start_time="2015-01-01", end_time="2026-12-31")
        _CAL_MAP = {d: i for i, d in enumerate(cal)}
    return _CAL_MAP


def _build_cs_cache(expr_key: str, agg_func: str) -> Dict[str, Dict[int, float]]:
    """Build cross-sectional cache: {instrument: {cal_idx: value}}"""
    cache_key = f"{agg_func}:{expr_key}"
    if cache_key in _CS_CACHE:
        return _CS_CACHE[cache_key]

    from qlib.data import D

    cal_map = _get_cal_map()
    inst_dict = D.instruments("all")
    all_df = D.features(
        inst_dict,
        fields=[expr_key],
        start_time="2015-01-01",
        end_time="2026-12-31",
    )
    flat = all_df.reset_index()
    flat.columns = ["instrument", "datetime", "value"]

    if agg_func == "rank":
        flat["result"] = flat.groupby("datetime")["value"].rank(pct=True)
    elif agg_func == "zscore":
        g = flat.groupby("datetime")["value"]
        flat["result"] = (flat["value"] - g.transform("mean")) / g.transform("std")
    elif agg_func == "demean":
        flat["result"] = flat["value"] - flat.groupby("datetime")["value"].transform(
            "mean"
        )
    else:
        flat["result"] = flat["value"]

    cache: Dict[str, Dict[int, float]] = {}
    for inst, grp in flat.groupby("instrument"):
        idx_val: Dict[int, float] = {}
        for dt, val in zip(grp["datetime"], grp["result"]):
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
    """``CsRank($pe_ratio)`` -- cross-sectional percentile rank (0-1)"""

    def _load_internal(self, instrument, start_index, end_index, *args):
        series = self.feature.load(instrument, start_index, end_index, *args)
        cache = _build_cs_cache(str(self.feature), "rank")
        return _extract_from_cache(cache, instrument, series)


class CsZscoreOp(ElemOperator):
    """``CsZscore($pe_ratio)`` -- cross-sectional z-score per day"""

    def _load_internal(self, instrument, start_index, end_index, *args):
        series = self.feature.load(instrument, start_index, end_index, *args)
        cache = _build_cs_cache(str(self.feature), "zscore")
        return _extract_from_cache(cache, instrument, series)


class CsDemeanOp(ElemOperator):
    """``CsDemean($pe_ratio)`` -- cross-sectional de-mean per day"""

    def _load_internal(self, instrument, start_index, end_index, *args):
        series = self.feature.load(instrument, start_index, end_index, *args)
        cache = _build_cs_cache(str(self.feature), "demean")
        return _extract_from_cache(cache, instrument, series)


# ===================================================================
# Registration
# ===================================================================

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

    Inserts into ``Operators._ops`` keyed by expression name (e.g. ``TsDecay``)
    rather than class name, since ``Operators.register()`` uses ``cls.__name__``.

    IMPORTANT: After calling this, set ``C.kernels = 1`` to prevent
    multiprocessing workers from losing the registered operators.

    Returns dict of {name: class} for reference.
    """
    from qlib.data.ops import Operators

    for name, cls in _CUSTOM_OPS.items():
        Operators._ops[name] = cls
    return dict(_CUSTOM_OPS)
