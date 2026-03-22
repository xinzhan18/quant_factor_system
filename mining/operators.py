"""Custom Qlib operator extensions for factor mining.

Provides both raw functions (for standalone use/testing) and Qlib ExpressionOps
class-based operators (for use within the Qlib expression engine).
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


# ---------------------------------------------------------------------------
# Qlib ExpressionOps classes (registered with Qlib expression engine)
# ---------------------------------------------------------------------------

_QLIB_AVAILABLE = False
try:
    from qlib.data.ops import PairOperator, ElemOperator, Rolling
    _QLIB_AVAILABLE = True
except ImportError:
    pass


if _QLIB_AVAILABLE:
    class SignedPowerOp(PairOperator):
        """sign(x) * |x|^p — Qlib expression operator.

        Usage in expression: ``SignedPower($close, 0.5)``
        """

        def _execute(self, series_left, series_right):
            return np.sign(series_left) * np.abs(series_left) ** series_right

    class TanhOp(ElemOperator):
        """Bounded tanh non-linearity — Qlib expression operator.

        Usage in expression: ``Tanh($close)``
        """

        def _execute(self, series):
            return np.tanh(series)

    class ExpOp(ElemOperator):
        """Exponential with clamping — Qlib expression operator.

        Usage in expression: ``Exp($close)``
        Clamps input to [-20, 20] to prevent overflow.
        """

        def _execute(self, series):
            clamped = np.clip(series, -20.0, 20.0)
            return np.exp(clamped)

    class ScaleOp(ElemOperator):
        """Cross-sectional normalization to [-1, 1] — Qlib expression operator.

        Usage in expression: ``Scale($close)``
        Note: This operates element-wise on the series; for true cross-sectional
        scaling, use within a cross-sectional context.
        """

        def _execute(self, series):
            vmin, vmax = series.min(), series.max()
            if vmax == vmin:
                return series * 0.0
            return 2.0 * (series - vmin) / (vmax - vmin) - 1.0

    class TsDecayOp(Rolling):
        """Time-decay weighted average — Qlib expression operator.

        Usage in expression: ``TsDecay($close, 10)``
        More recent values get linearly higher weight.
        """

        def _execute(self, series):
            n = len(series)
            weights = np.arange(1, n + 1, dtype=float)
            weights /= weights.sum()
            return np.dot(series, weights)


def register_custom_operators() -> Dict[str, Callable]:
    """Register custom operators with Qlib's expression engine.

    When Qlib is available, registers the class-based operators with Qlib's
    operator registry so they can be used in expression strings like
    ``SignedPower($close, 0.5)``.

    Returns dict of {name: class_or_function} for reference.
    """
    ops: Dict[str, Callable] = {
        "SignedPower": signed_power,
        "Tanh": tanh_op,
        "Scale": scale_cs,
        "TsDecay": ts_decay,
        "Exp": exp_op,
    }

    if _QLIB_AVAILABLE:
        from qlib.data import ops as qlib_ops
        qlib_ops.SignedPower = SignedPowerOp
        qlib_ops.Tanh = TanhOp
        qlib_ops.Exp = ExpOp
        qlib_ops.Scale = ScaleOp
        qlib_ops.TsDecay = TsDecayOp
        ops = {
            "SignedPower": SignedPowerOp,
            "Tanh": TanhOp,
            "Scale": ScaleOp,
            "TsDecay": TsDecayOp,
            "Exp": ExpOp,
        }

    return ops
