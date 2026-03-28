"""Tests for mining.metrics — 6-dimension factor evaluation."""

import numpy as np
import pandas as pd
import pytest
from scipy.stats import spearmanr

from mining.metrics import (
    FactorReportCard,
    _estimate_half_life,
    _monotonicity,
    _quantile_returns,
    _sanitize,
    compute_report_card,
    dim1_predictive_power,
    dim2_robustness,
    dim3_economic_coherence,
    dim4_decay_turnover,
    dim5_distribution,
    dim6_uniqueness,
)


# ──────────────────── Fixtures ────────────────────


@pytest.fixture
def daily_ics_is():
    """Datetime-indexed IC series (in-sample)."""
    dates = pd.bdate_range("2023-01-02", periods=100)
    np.random.seed(42)
    return pd.Series(np.random.randn(100) * 0.05 + 0.03, index=dates)


@pytest.fixture
def daily_ics_oos():
    """Datetime-indexed IC series (out-of-sample)."""
    dates = pd.bdate_range("2024-01-02", periods=50)
    np.random.seed(99)
    return pd.Series(np.random.randn(50) * 0.05 + 0.02, index=dates)


@pytest.fixture
def factor_returns_pair():
    """Matched factor values and returns DataFrames."""
    dates = pd.bdate_range("2023-01-02", periods=60)
    instruments = [f"SH60000{i}" for i in range(20)]
    idx = pd.MultiIndex.from_product([dates, instruments], names=["datetime", "instrument"])
    np.random.seed(42)
    signal = np.random.randn(len(idx))
    factor_df = pd.DataFrame({"factor": signal}, index=idx)
    returns_df = pd.DataFrame({"$returns_1d": signal * 0.3 + np.random.randn(len(idx)) * 0.5}, index=idx)
    return factor_df, returns_df


# ──────────────────── _sanitize ────────────────────


class TestSanitize:
    def test_nan_to_none(self):
        assert _sanitize(float("nan")) is None

    def test_numpy_nan_to_none(self):
        assert _sanitize(np.nan) is None

    def test_float_passthrough(self):
        assert _sanitize(3.14) == 3.14

    def test_numpy_int(self):
        result = _sanitize(np.int64(42))
        assert result == 42
        assert isinstance(result, int)

    def test_numpy_float(self):
        result = _sanitize(np.float64(1.5))
        assert result == 1.5
        assert isinstance(result, float)

    def test_numpy_bool(self):
        result = _sanitize(np.bool_(True))
        assert result is True

    def test_nested_dict(self):
        result = _sanitize({"a": np.nan, "b": np.int64(1), "c": {"d": np.float64(2.5)}})
        assert result == {"a": None, "b": 1, "c": {"d": 2.5}}

    def test_list(self):
        result = _sanitize([np.nan, np.float64(1.0)])
        assert result == [None, 1.0]


# ──────────────────── FactorReportCard ────────────────────


class TestFactorReportCard:
    def test_defaults_are_nan(self):
        rc = FactorReportCard()
        assert np.isnan(rc.ic_mean)
        assert np.isnan(rc.coverage)
        assert rc.max_lib_corr == 0.0

    def test_to_dict_converts_nan_to_none(self):
        rc = FactorReportCard(ic_mean=0.05, ic_std=float("nan"))
        d = rc.to_dict()
        assert d["ic_mean"] == 0.05
        assert d["ic_std"] is None

    def test_to_dict_preserves_dicts(self):
        rc = FactorReportCard(ic_by_year={2023: 0.03, 2024: 0.04})
        d = rc.to_dict()
        assert d["ic_by_year"] == {2023: 0.03, 2024: 0.04}


# ──────────────────── Dimension 1: Predictive Power ────────────────────


class TestDim1PredictivePower:
    def test_basic(self, daily_ics_is):
        result = dim1_predictive_power(daily_ics_is)
        assert result["ic_mean"] > 0
        assert result["ic_std"] > 0
        assert 0 < result["ic_ir"]
        assert 0 < result["ic_win_rate"] <= 1.0
        assert len(result["ic_by_year"]) > 0
        assert len(result["ic_by_month"]) > 0

    def test_empty_series(self):
        result = dim1_predictive_power(pd.Series(dtype=float))
        assert np.isnan(result["ic_mean"])
        assert result["ic_by_year"] == {}

    def test_ic_by_year_keys_are_int(self, daily_ics_is):
        result = dim1_predictive_power(daily_ics_is)
        for k in result["ic_by_year"]:
            assert isinstance(k, int)

    def test_win_rate_range(self, daily_ics_is):
        result = dim1_predictive_power(daily_ics_is)
        assert 0 <= result["ic_win_rate"] <= 1.0


# ──────────────────── Dimension 2: Robustness ────────────────────


class TestDim2Robustness:
    def test_basic(self, daily_ics_is, daily_ics_oos):
        result = dim2_robustness(daily_ics_is, daily_ics_oos)
        assert not np.isnan(result["ic_mean_oos"])
        assert not np.isnan(result["oos_decay_ratio"])
        assert not np.isnan(result["ic_autocorr"])
        assert not np.isnan(result["ic_max_drawdown"])
        assert not np.isnan(result["worst_quarter_ic"])
        assert not np.isnan(result["best_quarter_ic"])
        assert result["worst_quarter_ic"] <= result["best_quarter_ic"]

    def test_empty_oos(self, daily_ics_is):
        result = dim2_robustness(daily_ics_is, pd.Series(dtype=float))
        assert np.isnan(result["ic_mean_oos"])
        assert np.isnan(result["ic_ir_oos"])

    def test_oos_decay_ratio_positive_when_same_sign(self):
        dates_is = pd.bdate_range("2023-01-02", periods=50)
        dates_oos = pd.bdate_range("2024-01-02", periods=20)
        ics_is = pd.Series(np.ones(50) * 0.05, index=dates_is)
        ics_oos = pd.Series(np.ones(20) * 0.03, index=dates_oos)
        result = dim2_robustness(ics_is, ics_oos)
        assert result["oos_decay_ratio"] == pytest.approx(0.6, abs=0.01)


# ──────────────────── _monotonicity ────────────────────


class TestMonotonicity:
    def test_perfect_increasing(self):
        q = {"q1": 0.01, "q2": 0.02, "q3": 0.03, "q4": 0.04, "q5": 0.05}
        assert _monotonicity(q) == pytest.approx(1.0)

    def test_perfect_decreasing(self):
        q = {"q1": 0.05, "q2": 0.04, "q3": 0.03, "q4": 0.02, "q5": 0.01}
        assert _monotonicity(q) == pytest.approx(-1.0)

    def test_nan_if_too_few(self):
        assert np.isnan(_monotonicity({"q1": 0.01, "q2": 0.02}))

    def test_with_nan_values(self):
        q = {"q1": 0.01, "q2": float("nan"), "q3": 0.03, "q4": 0.04, "q5": 0.05}
        result = _monotonicity(q)
        assert not np.isnan(result)


# ──────────────────── Dimension 3: Economic Coherence ────────────────────


class TestDim3EconomicCoherence:
    def test_basic(self, factor_returns_pair):
        factor_df, returns_df = factor_returns_pair
        result = dim3_economic_coherence(
            factor_df, returns_df, factor_df, returns_df,
            ic_mean_is=0.03, ic_mean_oos=0.02,
        )
        assert "quantile_returns_is" in result
        assert "monotonicity_is" in result
        assert "ls_tstat" in result
        assert result["ic_sign_consistent"] is True

    def test_sign_inconsistent(self, factor_returns_pair):
        factor_df, returns_df = factor_returns_pair
        result = dim3_economic_coherence(
            factor_df, returns_df, factor_df, returns_df,
            ic_mean_is=0.03, ic_mean_oos=-0.02,
        )
        assert result["ic_sign_consistent"] is False

    def test_sign_consistent_both_positive(self, factor_returns_pair):
        factor_df, returns_df = factor_returns_pair
        result = dim3_economic_coherence(
            factor_df, returns_df, factor_df, returns_df,
            ic_mean_is=0.03, ic_mean_oos=0.01,
        )
        assert result["ic_sign_consistent"] is True


# ──────────────────── _estimate_half_life ────────────────────


class TestEstimateHalfLife:
    def test_linear_decay(self):
        ic_decay = {1: 0.10, 5: 0.05, 10: 0.02, 20: 0.01}
        hl = _estimate_half_life(ic_decay)
        assert 1 < hl < 10  # half of 0.10 is 0.05, which is at h=5

    def test_immediate_half(self):
        ic_decay = {1: 0.10, 5: 0.04}
        hl = _estimate_half_life(ic_decay)
        assert hl == pytest.approx(5.0 * (0.10 - 0.05) / (0.10 - 0.04) + 1.0 * (1 - (0.10 - 0.05) / (0.10 - 0.04)),
                                   abs=0.5)

    def test_nan_if_single_horizon(self):
        assert np.isnan(_estimate_half_life({1: 0.05}))

    def test_nan_if_zero_ic(self):
        assert np.isnan(_estimate_half_life({1: 0.0, 5: 0.0}))

    def test_nan_if_no_crossover(self):
        # IC never decays below half
        ic_decay = {1: 0.10, 5: 0.09, 10: 0.08, 20: 0.07}
        hl = _estimate_half_life(ic_decay)
        assert np.isnan(hl)


# ──────────────────── Dimension 4: Decay & Turnover ────────────────────


class TestDim4DecayTurnover:
    def test_basic(self, factor_returns_pair):
        factor_df, _ = factor_returns_pair
        dates = pd.bdate_range("2023-01-02", periods=60)
        daily_ics_1d = pd.Series(np.random.randn(60) * 0.05, index=dates)
        daily_ics_5d = pd.Series(np.random.randn(60) * 0.03, index=dates)
        result = dim4_decay_turnover({1: daily_ics_1d, 5: daily_ics_5d}, factor_df)
        assert 1 in result["ic_decay"]
        assert 5 in result["ic_decay"]
        assert not np.isnan(result["factor_turnover"])
        assert not np.isnan(result["factor_autocorr"])
        assert 0 <= result["factor_autocorr"] <= 1.0 or result["factor_autocorr"] < 0

    def test_empty_horizons(self, factor_returns_pair):
        factor_df, _ = factor_returns_pair
        result = dim4_decay_turnover({}, factor_df)
        assert result["ic_decay"] == {}
        assert np.isnan(result["half_life_days"])


# ──────────────────── Dimension 5: Distribution ────────────────────


class TestDim5Distribution:
    def test_basic(self, factor_returns_pair):
        factor_df, _ = factor_returns_pair
        result = dim5_distribution(factor_df)
        assert 0.9 < result["coverage"] <= 1.0
        assert result["zero_ratio"] >= 0
        assert not np.isnan(result["factor_skew"])
        assert not np.isnan(result["factor_kurt"])
        assert result["extreme_ratio"] >= 0

    def test_empty(self):
        empty_df = pd.DataFrame({"factor": []},
                                index=pd.MultiIndex.from_tuples([], names=["datetime", "instrument"]))
        result = dim5_distribution(empty_df)
        assert np.isnan(result["coverage"])


# ──────────────────── Dimension 6: Uniqueness ────────────────────


class TestDim6Uniqueness:
    def test_no_library(self, factor_returns_pair):
        factor_df, returns_df = factor_returns_pair
        result = dim6_uniqueness(
            factor_df, returns_df,
            lib_values={}, lib_corr_profile={},
            stage2_info={"max_corr": 0.2, "max_corr_factor": "001"},
            expression_depth=3,
        )
        assert result["max_lib_corr"] == 0.2
        assert result["max_corr_factor_id"] == "001"
        assert result["expression_depth"] == 3
        assert np.isnan(result["incremental_ic"])

    def test_with_library(self, factor_returns_pair):
        factor_df, returns_df = factor_returns_pair
        np.random.seed(77)
        lib_vals = pd.DataFrame(
            {"lib_factor": np.random.randn(len(factor_df))}, index=factor_df.index,
        )
        result = dim6_uniqueness(
            factor_df, returns_df,
            lib_values={"001": lib_vals},
            lib_corr_profile={"001": 0.3},
            stage2_info={"max_corr": 0.3, "max_corr_factor": "001"},
            expression_depth=2,
        )
        assert not np.isnan(result["incremental_ic"])
        assert result["lib_corr_profile"] == {"001": 0.3}


# ──────────────────── _quantile_returns ────────────────────


class TestQuantileReturns:
    def test_basic(self, factor_returns_pair):
        factor_df, returns_df = factor_returns_pair
        q_rets, daily_ls = _quantile_returns(factor_df, returns_df)
        assert "q1" in q_rets
        assert "q5" in q_rets
        assert len(daily_ls) > 0

    def test_empty(self):
        empty_factor = pd.DataFrame({"f": []},
                                    index=pd.MultiIndex.from_tuples([], names=["datetime", "instrument"]))
        empty_ret = pd.DataFrame({"r": []},
                                 index=pd.MultiIndex.from_tuples([], names=["datetime", "instrument"]))
        q_rets, daily_ls = _quantile_returns(empty_factor, empty_ret)
        assert len(daily_ls) == 0


# ──────────────────── compute_report_card (integration) ────────────────────


class TestComputeReportCard:
    def test_integration(self, daily_ics_is, daily_ics_oos, factor_returns_pair):
        factor_df, returns_df = factor_returns_pair
        rc = compute_report_card(
            daily_ics_is=daily_ics_is,
            daily_ics_oos=daily_ics_oos,
            factor_vals_is=factor_df,
            factor_vals_oos=factor_df,
            returns_is=returns_df,
            returns_oos=returns_df,
            daily_ics_by_horizon={1: daily_ics_is},
            lib_values={},
            lib_corr_profile={},
            stage2_info={},
            expression_depth=3,
        )
        assert isinstance(rc, FactorReportCard)
        assert not np.isnan(rc.ic_mean)
        assert not np.isnan(rc.coverage)
        assert rc.expression_depth == 3

        # to_dict should be serializable
        d = rc.to_dict()
        assert isinstance(d, dict)
        assert "ic_mean" in d
        assert "report_card" not in d  # no nesting
