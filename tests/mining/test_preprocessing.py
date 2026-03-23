import logging

import numpy as np
import pandas as pd
import pytest

from mining.config import MiningConfig
from mining.preprocessing import FactorPreprocessor


def _make_index(dates, instruments):
    """Helper: create (datetime, instrument) MultiIndex."""
    return pd.MultiIndex.from_product(
        [pd.to_datetime(dates), instruments],
        names=["datetime", "instrument"],
    )


class TestPreprocessingConfig:
    def test_preprocessing_defaults(self):
        config = MiningConfig()
        assert config.filter_suspend is True
        assert config.filter_limit is True
        assert config.winsorize_method == "mad"
        assert config.winsorize_n == 5.0
        assert config.standardize_method == "zscore"
        assert config.neutralize_mode == "none"

    def test_config_overrides(self):
        config = MiningConfig(
            winsorize_method="sigma",
            winsorize_n=3.0,
            neutralize_mode="both",
        )
        assert config.winsorize_method == "sigma"
        assert config.winsorize_n == 3.0
        assert config.neutralize_mode == "both"


class TestUniverseFilter:
    def test_suspend_filtered(self):
        config = MiningConfig(filter_suspend=True)
        pp = FactorPreprocessor(config)
        idx = _make_index(["2024-01-02"], ["SH600000", "SZ000001"])
        volume = pd.DataFrame({"$volume": [1e6, 0.0]}, index=idx)
        mask = pp.build_tradable_mask(volume=volume)
        assert mask.loc[("2024-01-02", "SH600000")] == True
        assert mask.loc[("2024-01-02", "SZ000001")] == False

    def test_limit_up_filtered(self):
        config = MiningConfig(filter_limit=True)
        pp = FactorPreprocessor(config)
        idx = _make_index(["2024-01-02"], ["SH600000", "SZ000001"])
        close = pd.DataFrame({"$close": [11.0, 20.0]}, index=idx)
        limit_up = pd.DataFrame({"$limit_up": [11.0, 22.0]}, index=idx)
        mask = pp.build_tradable_mask(close=close, limit_up=limit_up)
        assert mask.loc[("2024-01-02", "SH600000")] == False
        assert mask.loc[("2024-01-02", "SZ000001")] == True

    def test_limit_down_filtered(self):
        config = MiningConfig(filter_limit=True)
        pp = FactorPreprocessor(config)
        idx = _make_index(["2024-01-02"], ["SH600000", "SZ000001"])
        close = pd.DataFrame({"$close": [9.0, 20.0]}, index=idx)
        limit_down = pd.DataFrame({"$limit_down": [9.0, 18.0]}, index=idx)
        mask = pp.build_tradable_mask(close=close, limit_down=limit_down)
        assert mask.loc[("2024-01-02", "SH600000")] == False
        assert mask.loc[("2024-01-02", "SZ000001")] == True

    def test_warns_when_filter_enabled_but_data_missing(self, caplog):
        config = MiningConfig(filter_suspend=True, filter_limit=True)
        pp = FactorPreprocessor(config)
        idx = _make_index(["2024-01-02"], ["A", "B"])
        close = pd.DataFrame({"$close": [10.0, 20.0]}, index=idx)
        with caplog.at_level(logging.WARNING):
            mask = pp.build_tradable_mask(close=close)
        assert "filter_suspend enabled but volume data not provided" in caplog.text


class TestFactorCleaning:
    def test_inf_replaced_with_nan(self):
        config = MiningConfig()
        pp = FactorPreprocessor(config)
        idx = _make_index(["2024-01-02"], ["A", "B", "C"])
        factor = pd.DataFrame({"f": [1.0, np.inf, -np.inf]}, index=idx)
        cleaned = pp.clean_factor_values(factor)
        assert np.isnan(cleaned.iloc[1, 0])
        assert np.isnan(cleaned.iloc[2, 0])
        assert cleaned.iloc[0, 0] != 0

    def test_all_nan_no_crash(self):
        config = MiningConfig()
        pp = FactorPreprocessor(config)
        idx = _make_index(["2024-01-02"], ["A", "B", "C"])
        factor = pd.DataFrame({"f": [np.inf, np.nan, -np.inf]}, index=idx)
        cleaned = pp.clean_factor_values(factor)
        assert cleaned["f"].isna().all()

    def test_mad_winsorize(self):
        config = MiningConfig(winsorize_method="mad", winsorize_n=3.0)
        pp = FactorPreprocessor(config)
        np.random.seed(42)
        values = np.random.randn(100)
        values[0] = 100.0
        idx = _make_index(["2024-01-02"], [f"S{i:03d}" for i in range(100)])
        factor = pd.DataFrame({"f": values}, index=idx)
        cleaned = pp.clean_factor_values(factor)
        assert cleaned.iloc[0, 0] < 50.0

    def test_zscore_standardize(self):
        config = MiningConfig(standardize_method="zscore")
        pp = FactorPreprocessor(config)
        values = np.arange(1.0, 101.0)
        idx = _make_index(["2024-01-02"], [f"S{i:03d}" for i in range(100)])
        factor = pd.DataFrame({"f": values}, index=idx)
        cleaned = pp.clean_factor_values(factor)
        col = cleaned.columns[0]
        day_vals = cleaned.loc["2024-01-02", col]
        assert abs(day_vals.mean()) < 0.01
        assert abs(day_vals.std() - 1.0) < 0.1

    def test_rank_standardize(self):
        config = MiningConfig(standardize_method="rank")
        pp = FactorPreprocessor(config)
        values = np.array([100.0, 1.0, 50.0, 25.0, 75.0])
        idx = _make_index(["2024-01-02"], ["A", "B", "C", "D", "E"])
        factor = pd.DataFrame({"f": values}, index=idx)
        cleaned = pp.clean_factor_values(factor)
        col = cleaned.columns[0]
        day_vals = cleaned.loc["2024-01-02", col]
        assert day_vals.loc["A"] > day_vals.loc["B"]


class TestReturnMasking:
    def test_untradable_returns_masked(self):
        config = MiningConfig()
        pp = FactorPreprocessor(config)
        idx = _make_index(["2024-01-02"], ["A", "B", "C"])
        returns = pd.DataFrame({"$returns_1d": [0.05, 0.03, -0.02]}, index=idx)
        mask = pd.Series([True, False, True], index=idx)
        masked = pp.mask_returns(returns, mask)
        assert masked.iloc[0, 0] == pytest.approx(0.05)
        assert np.isnan(masked.iloc[1, 0])
        assert masked.iloc[2, 0] == pytest.approx(-0.02)


class TestNeutralization:
    def test_market_cap_neutralize(self):
        config = MiningConfig(neutralize_mode="market_cap")
        pp = FactorPreprocessor(config)
        np.random.seed(42)
        n = 200
        market_cap = np.exp(np.random.randn(n) * 0.5 + 10)
        factor_vals = np.log(market_cap) + np.random.randn(n) * 0.1
        idx = _make_index(["2024-01-02"], [f"S{i:03d}" for i in range(n)])
        factor = pd.DataFrame({"f": factor_vals}, index=idx)
        mcap = pd.DataFrame({"$market_cap": market_cap}, index=idx)
        neutralized = pp.neutralize(factor, market_cap=mcap)
        col = neutralized.columns[0]
        day_vals = neutralized.loc["2024-01-02", col].values
        from scipy.stats import spearmanr
        corr, _ = spearmanr(day_vals, np.log(market_cap))
        assert abs(corr) < 0.15

    def test_no_neutralize_when_disabled(self):
        config = MiningConfig(neutralize_mode="none")
        pp = FactorPreprocessor(config)
        idx = _make_index(["2024-01-02"], ["A", "B", "C"])
        factor = pd.DataFrame({"f": [1.0, 2.0, 3.0]}, index=idx)
        result = pp.neutralize(factor)
        pd.testing.assert_frame_equal(result, factor)

    def test_neutralize_warns_when_data_missing(self, caplog):
        config = MiningConfig(neutralize_mode="market_cap")
        pp = FactorPreprocessor(config)
        idx = _make_index(["2024-01-02"], ["A", "B", "C"])
        factor = pd.DataFrame({"f": [1.0, 2.0, 3.0]}, index=idx)
        with caplog.at_level(logging.WARNING):
            result = pp.neutralize(factor)
        pd.testing.assert_frame_equal(result, factor)


class TestPreprocessForIC:
    def test_full_pipeline(self):
        config = MiningConfig(
            filter_suspend=True, filter_limit=True,
            winsorize_method="mad", standardize_method="zscore",
            neutralize_mode="none",
        )
        pp = FactorPreprocessor(config)
        idx = _make_index(["2024-01-02"], ["A", "B", "C", "D"])
        raw_factor = pd.DataFrame({"f": [1.0, np.inf, 3.0, 100.0]}, index=idx)
        raw_returns = pd.DataFrame({"$returns_1d": [0.05, 0.03, -0.02, 0.01]}, index=idx)
        volume = pd.DataFrame({"$volume": [1e6, 0.0, 1e6, 1e6]}, index=idx)
        close = pd.DataFrame({"$close": [10.0, 20.0, 10.0, 10.0]}, index=idx)
        limit_up = pd.DataFrame({"$limit_up": [11.0, 22.0, 10.0, 11.0]}, index=idx)
        clean_f, clean_r = pp.preprocess_for_ic(
            factor=raw_factor, returns=raw_returns,
            volume=volume, close=close, limit_up=limit_up,
        )
        # B suspended -> returns NaN
        assert np.isnan(clean_r.loc[("2024-01-02", "B")].iloc[0])
        # C at limit-up (close == limit_up) -> returns NaN
        assert np.isnan(clean_r.loc[("2024-01-02", "C")].iloc[0])
        # A normal -> returns preserved
        assert clean_r.loc[("2024-01-02", "A")].iloc[0] == pytest.approx(0.05)
        # inf in B factor -> NaN
        assert np.isnan(clean_f.loc[("2024-01-02", "B")].iloc[0])
