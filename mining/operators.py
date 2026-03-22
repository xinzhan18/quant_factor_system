"""Custom Qlib operator extensions for factor mining."""

from __future__ import annotations

import math
from typing import Callable, Dict

import numpy as np


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

    Weights: w_i = (period - i) / sum(1..period), where i=0 is oldest.
    """
    n = min(len(values), period)
    v = values[-n:]
    weights = np.arange(1, n + 1, dtype=float)
    return float(np.dot(v, weights) / weights.sum())


def exp_op(x: float, clamp: float = 20.0) -> float:
    """Exponential with clamping to prevent overflow."""
    return math.exp(min(x, clamp))


def register_custom_operators() -> Dict[str, Callable]:
    """Register custom operators with Qlib (if available).

    Returns dict of {name: function} for reference.
    Note: Proper Qlib operator registration requires extending ExpressionOps
    base classes. This function provides the raw implementations; full Qlib
    integration requires creating class-based operators (see Qlib docs).
    """
    ops = {
        "SignedPower": signed_power,
        "Tanh": tanh_op,
        "Scale": scale_cs,
        "TsDecay": ts_decay,
        "Exp": exp_op,
    }
    return ops
