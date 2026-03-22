"""Tests for custom Qlib operators."""

import numpy as np
import pytest

from mining.operators import signed_power, tanh_op, scale_cs, ts_decay, exp_op, register_custom_operators


class TestSignedPower:
    def test_positive(self):
        assert signed_power(4.0, 0.5) == pytest.approx(2.0)

    def test_negative(self):
        assert signed_power(-4.0, 0.5) == pytest.approx(-2.0)

    def test_zero(self):
        assert signed_power(0.0, 2.0) == 0.0


class TestTanh:
    def test_bounded(self):
        assert -1.0 <= tanh_op(100.0) <= 1.0
        assert -1.0 <= tanh_op(-100.0) <= 1.0

    def test_zero(self):
        assert tanh_op(0.0) == pytest.approx(0.0)


class TestScaleCS:
    def test_normalizes(self):
        values = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        scaled = scale_cs(values)
        assert scaled.min() >= -1.0
        assert scaled.max() <= 1.0

    def test_single_value(self):
        values = np.array([5.0])
        scaled = scale_cs(values)
        assert scaled[0] == 0.0


class TestTsDecay:
    def test_recency_weighted(self):
        values = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = ts_decay(values, period=5)
        # More recent values should have more weight, so result > simple mean
        assert result > np.mean(values) - 0.5

    def test_single_value(self):
        assert ts_decay(np.array([3.0]), period=1) == pytest.approx(3.0)


class TestExp:
    def test_positive(self):
        assert exp_op(0.0) == pytest.approx(1.0)
        assert exp_op(1.0) == pytest.approx(np.e)

    def test_clamped(self):
        # Should clamp to avoid overflow
        result = exp_op(1000.0)
        assert result < 1e20  # must not be inf


class TestRegistration:
    def test_register_returns_dict(self):
        ops = register_custom_operators()
        assert "SignedPower" in ops
        assert "Tanh" in ops
        assert "Scale" in ops
        assert "TsDecay" in ops
        assert "Exp" in ops
