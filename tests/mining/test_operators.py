"""Tests for custom Qlib operators."""

import numpy as np
import pytest

from mining.operators import (
    signed_power, tanh_op, scale_cs, ts_decay, exp_op,
    sigmoid, softmax_cs, zscore_cs, winsorize,
    ts_momentum, ts_autocorr, realized_vol, amihud_illiq, hhi,
    register_custom_operators,
)


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


class TestSigmoid:
    def test_bounds(self):
        assert 0.0 < sigmoid(100.0) <= 1.0
        assert 0.0 <= sigmoid(-100.0) < 1.0

    def test_midpoint(self):
        assert sigmoid(0.0) == pytest.approx(0.5)


class TestSoftmaxCS:
    def test_sums_to_one(self):
        values = np.array([1.0, 2.0, 3.0])
        result = softmax_cs(values)
        assert result.sum() == pytest.approx(1.0)

    def test_empty(self):
        assert len(softmax_cs(np.array([]))) == 0


class TestZscoreCS:
    def test_standardizes(self):
        values = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
        result = zscore_cs(values)
        assert result.mean() == pytest.approx(0.0, abs=1e-10)
        assert result.std() == pytest.approx(1.0, abs=1e-10)

    def test_single_value(self):
        result = zscore_cs(np.array([5.0]))
        assert result[0] == 0.0


class TestWinsorize:
    def test_clips_outliers(self):
        # Many normal values + one extreme outlier so std isn't dominated by the outlier
        values = np.array([1.0, 2.0, 3.0, 2.5, 1.5, 2.8, 3.2, 1.8, 2.2, 100.0])
        result = winsorize(values, n_sigma=2.0)
        assert result.max() < 100.0

    def test_no_change_within_bounds(self):
        values = np.array([1.0, 2.0, 3.0])
        result = winsorize(values, n_sigma=5.0)
        np.testing.assert_array_almost_equal(result, values)


class TestTsMomentum:
    def test_positive_return(self):
        values = np.array([100.0, 110.0, 120.0])
        result = ts_momentum(values, period=3)
        assert result == pytest.approx(0.2)  # 120/100 - 1

    def test_zero_start(self):
        values = np.array([0.0, 1.0, 2.0])
        assert ts_momentum(values, period=3) == 0.0


class TestTsAutoCorr:
    def test_high_autocorrelation(self):
        values = np.arange(20, dtype=float)  # perfectly trending
        result = ts_autocorr(values, period=20, lag=1)
        assert result > 0.9

    def test_short_series(self):
        values = np.array([1.0, 2.0])
        assert ts_autocorr(values, period=2, lag=1) == 0.0


class TestRealizedVol:
    def test_nonzero(self):
        returns = np.array([0.01, -0.02, 0.015, -0.005, 0.01])
        result = realized_vol(returns, period=5)
        assert result > 0.0

    def test_zero_returns(self):
        returns = np.zeros(5)
        assert realized_vol(returns, period=5) == 0.0


class TestAmihudIlliq:
    def test_basic(self):
        returns = np.array([0.01, -0.02, 0.015])
        volume = np.array([1000.0, 2000.0, 1500.0])
        result = amihud_illiq(returns, volume, period=3)
        assert result > 0.0

    def test_zero_volume(self):
        returns = np.array([0.01, 0.02])
        volume = np.array([0.0, 0.0])
        assert amihud_illiq(returns, volume, period=2) == 0.0


class TestHHI:
    def test_equal_shares(self):
        volume = np.array([100.0, 100.0, 100.0, 100.0])
        result = hhi(volume, period=4)
        assert result == pytest.approx(0.25)  # 4 * (0.25)^2

    def test_concentrated(self):
        volume = np.array([1000.0, 1.0, 1.0, 1.0])
        result = hhi(volume, period=4)
        assert result > 0.9  # dominated by one bar


class TestRegistration:
    def test_register_returns_dict(self):
        ops = register_custom_operators()
        assert "SignedPower" in ops
        assert "Tanh" in ops
        assert "Scale" in ops
        assert "TsDecay" in ops
        assert "Exp" in ops

    def test_register_all_15(self):
        ops = register_custom_operators()
        assert len(ops) == 15
        for name in ["Sigmoid", "Softmax", "Zscore", "Winsorize",
                      "TsMomentum", "TsAutoCorr", "RealizedVol", "TsEntropy",
                      "AmihudIlliq", "HHI"]:
            assert name in ops
