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

from qlib.data.ops import PairOperator, ElemOperator, Rolling, NpElemOperator


# --- Non-linear transforms ---

class SignedPowerOp(PairOperator):
    """``SignedPower($close, 0.5)`` — sign(x) * |x|^p"""

    def _execute(self, series_left, series_right):
        return np.sign(series_left) * np.abs(series_left) ** series_right


class TanhOp(NpElemOperator):
    """``Tanh($close)`` — bounded [-1, 1] non-linearity"""

    def _execute(self, series):
        return np.tanh(series)


class ExpOp(NpElemOperator):
    """``Exp($close)`` — exponential with clamping [-20, 20]"""

    def _execute(self, series):
        return np.exp(np.clip(series, -20.0, 20.0))


class SigmoidOp(NpElemOperator):
    """``Sigmoid($close)`` — maps R to (0, 1)"""

    def _execute(self, series):
        clamped = np.clip(series, -20.0, 20.0)
        return 1.0 / (1.0 + np.exp(-clamped))


class SoftmaxOp(NpElemOperator):
    """``Softmax($close)`` — cross-sectional softmax, output sums to 1"""

    def _execute(self, series):
        shifted = series - np.nanmax(series)
        e = np.exp(shifted)
        s = np.nansum(e)
        return e / s if s != 0 else e * 0.0


# --- Normalization ---

class ScaleOp(NpElemOperator):
    """``Scale($close)`` — min-max normalization to [-1, 1]"""

    def _execute(self, series):
        vmin, vmax = np.nanmin(series), np.nanmax(series)
        if vmax == vmin:
            return series * 0.0
        return 2.0 * (series - vmin) / (vmax - vmin) - 1.0


class ZscoreOp(NpElemOperator):
    """``Zscore($close)`` — (x - mean) / std"""

    def _execute(self, series):
        mean = np.nanmean(series)
        std = np.nanstd(series)
        if std == 0:
            return series * 0.0
        return (series - mean) / std


class WinsorizeOp(NpElemOperator):
    """``Winsorize($close)`` — clip to [mean-3*std, mean+3*std]"""

    def _execute(self, series):
        mean = np.nanmean(series)
        std = np.nanstd(series)
        if std == 0:
            return series
        return np.clip(series, mean - 3.0 * std, mean + 3.0 * std)


# --- Time-series ---

class TsDecayOp(Rolling):
    """``TsDecay($close, 10)`` — linearly weighted average, recent values heavier"""

    def _execute(self, series):
        n = len(series)
        weights = np.arange(1, n + 1, dtype=float)
        weights /= weights.sum()
        return np.dot(series, weights)


class TsMomentumOp(Rolling):
    """``TsMomentum($close, 20)`` — period return: last/first - 1"""

    def _execute(self, series):
        if len(series) == 0 or series[0] == 0:
            return np.nan
        return series[-1] / series[0] - 1


class TsAutoCorrelation(Rolling):
    """``TsAutoCorr($close, 20)`` — lag-1 autocorrelation of the series"""

    def _execute(self, series):
        if len(series) < 4:
            return np.nan
        x, y = series[:-1], series[1:]
        std_x, std_y = np.std(x), np.std(y)
        if std_x == 0 or std_y == 0:
            return 0.0
        return float(np.corrcoef(x, y)[0, 1])


class RealizedVolOp(Rolling):
    """``RealizedVol($returns, 20)`` — sqrt(sum(x^2)), realized volatility"""

    def _execute(self, series):
        return np.sqrt(np.nansum(series ** 2))


class TsEntropyOp(Rolling):
    """``TsEntropy($returns, 20)`` — Shannon entropy of return distribution"""

    def _execute(self, series):
        s = series[~np.isnan(series)]
        if len(s) < 2:
            return np.nan
        # Discretize into 10 bins
        counts, _ = np.histogram(s, bins=min(10, len(s)))
        probs = counts / counts.sum()
        probs = probs[probs > 0]
        return -float(np.sum(probs * np.log(probs)))


# --- Microstructure ---

class AmihudIlliqOp(Rolling):
    """``AmihudIlliq($returns, 20)`` — mean(|x|) as illiquidity proxy

    Note: True Amihud requires |return|/volume. This simplified version
    uses |return| only. For the full version, use PairRolling with volume.
    """

    def _execute(self, series):
        return np.nanmean(np.abs(series))


class HHIOp(Rolling):
    """``HHI($volume, 20)`` — Herfindahl index of volume concentration"""

    def _execute(self, series):
        total = np.nansum(series)
        if total == 0:
            return np.nan
        shares = series / total
        return np.nansum(shares ** 2)


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
    # Microstructure
    "AmihudIlliq": AmihudIlliqOp,
    "HHI": HHIOp,
}


def register_custom_operators() -> Dict[str, type]:
    """Register all custom operators with Qlib's expression engine.

    Injects operator classes into ``qlib.data.ops`` module namespace so they
    can be used in expression strings like ``Zscore(TsDecay($close, 10))``.

    Returns dict of {name: class} for reference.
    """
    from qlib.data import ops as qlib_ops
    for name, cls in _CUSTOM_OPS.items():
        setattr(qlib_ops, name, cls)
    return dict(_CUSTOM_OPS)
