from mining.config import MiningConfig


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
