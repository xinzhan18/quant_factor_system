"""Golden-fixture tests for vectorized_barra (batched OLS via pinv + einsum)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
import yaml

from research.compute.vectorized_barra import compute_barra_exposures

FIXTURES = Path(__file__).parent / "_fixtures"
INPUTS = FIXTURES / "inputs"
OUTPUTS = FIXTURES / "outputs"

# Barra residual IC is sensitive to OLS numerical conditioning; we require
# the batched pinv+einsum implementation to match the legacy per-date
# lstsq implementation to 1e-4 on the golden fixture. Legacy values are
# rounded to 6 decimals in golden.yaml so absolute 1e-5 is tight enough.
STRICT_ATOL = 1e-5


@pytest.fixture(scope="module")
def factor_flat() -> pd.DataFrame:
    return pd.read_parquet(INPUTS / "factor_values.parquet")


@pytest.fixture(scope="module")
def returns_flat() -> pd.DataFrame:
    return pd.read_parquet(INPUTS / "forward_returns.parquet")


@pytest.fixture(scope="module")
def style_matrix() -> pd.DataFrame:
    return pd.read_parquet(INPUTS / "style_matrix.parquet")


@pytest.fixture(scope="module")
def golden() -> dict:
    with open(OUTPUTS / "golden.yaml") as f:
        return yaml.safe_load(f)


class TestBarraEquivalence:
    def test_style_exposures_match_golden(
        self,
        factor_flat: pd.DataFrame,
        style_matrix: pd.DataFrame,
        returns_flat: pd.DataFrame,
        golden: dict,
    ) -> None:
        raw_ic = golden["effect_strength"]["validation"]["ic_mean"]
        result = compute_barra_exposures(
            factor_flat,
            style_matrix,
            returns_flat,
            raw_view_ic=raw_ic,
            min_obs=50,
        )

        g_exp = golden["barra"]["style_exposures"]
        for name, g_value in g_exp.items():
            assert name in result["style_exposures"]
            assert result["style_exposures"][name] == pytest.approx(
                g_value, abs=STRICT_ATOL
            ), f"style_exposures[{name}] mismatch"

    def test_style_r_squared_matches_golden(
        self,
        factor_flat: pd.DataFrame,
        style_matrix: pd.DataFrame,
        returns_flat: pd.DataFrame,
        golden: dict,
    ) -> None:
        raw_ic = golden["effect_strength"]["validation"]["ic_mean"]
        result = compute_barra_exposures(
            factor_flat,
            style_matrix,
            returns_flat,
            raw_view_ic=raw_ic,
            min_obs=50,
        )
        assert result["style_r_squared"] == pytest.approx(
            golden["barra"]["style_r_squared"], abs=STRICT_ATOL
        )

    def test_residual_ic_matches_golden(
        self,
        factor_flat: pd.DataFrame,
        style_matrix: pd.DataFrame,
        returns_flat: pd.DataFrame,
        golden: dict,
    ) -> None:
        raw_ic = golden["effect_strength"]["validation"]["ic_mean"]
        result = compute_barra_exposures(
            factor_flat,
            style_matrix,
            returns_flat,
            raw_view_ic=raw_ic,
            min_obs=50,
        )
        # Golden values are rounded to 6 decimals; require match to 1e-5
        assert result["barra_residual_ic"] == pytest.approx(
            golden["barra"]["barra_residual_ic"], abs=STRICT_ATOL
        )
        assert result["barra_residual_icir"] == pytest.approx(
            golden["barra"]["barra_residual_icir"], abs=STRICT_ATOL
        )

    def test_alpha_survival_matches_golden(
        self,
        factor_flat: pd.DataFrame,
        style_matrix: pd.DataFrame,
        returns_flat: pd.DataFrame,
        golden: dict,
    ) -> None:
        raw_ic = golden["effect_strength"]["validation"]["ic_mean"]
        result = compute_barra_exposures(
            factor_flat,
            style_matrix,
            returns_flat,
            raw_view_ic=raw_ic,
            min_obs=50,
        )
        assert result["alpha_survival_ratio"] == pytest.approx(
            golden["barra"]["alpha_survival_ratio"], abs=1e-3
        )

    def test_dominant_style_matches_golden(
        self,
        factor_flat: pd.DataFrame,
        style_matrix: pd.DataFrame,
        returns_flat: pd.DataFrame,
        golden: dict,
    ) -> None:
        raw_ic = golden["effect_strength"]["validation"]["ic_mean"]
        result = compute_barra_exposures(
            factor_flat,
            style_matrix,
            returns_flat,
            raw_view_ic=raw_ic,
            min_obs=50,
        )
        assert (
            result["dominant_style_exposure"]
            == golden["barra"]["dominant_style_exposure"]
        )

    def test_crowding_risk_matches_golden(
        self,
        factor_flat: pd.DataFrame,
        style_matrix: pd.DataFrame,
        returns_flat: pd.DataFrame,
        golden: dict,
    ) -> None:
        raw_ic = golden["effect_strength"]["validation"]["ic_mean"]
        result = compute_barra_exposures(
            factor_flat,
            style_matrix,
            returns_flat,
            raw_view_ic=raw_ic,
            min_obs=50,
        )
        assert (
            result["style_crowding_risk"] == golden["barra"]["style_crowding_risk"]
        )


class TestBarraEdgeCases:
    def test_empty_factor_returns_sentinel(
        self, style_matrix: pd.DataFrame, returns_flat: pd.DataFrame
    ) -> None:
        empty = pd.DataFrame(columns=["time", "symbol", "value"])
        result = compute_barra_exposures(
            empty, style_matrix, returns_flat, raw_view_ic=0.1
        )
        assert result["style_exposures"] == {}
        assert result["style_r_squared"] is None

    def test_near_zero_raw_ic_survival_none(
        self,
        factor_flat: pd.DataFrame,
        style_matrix: pd.DataFrame,
        returns_flat: pd.DataFrame,
    ) -> None:
        result = compute_barra_exposures(
            factor_flat,
            style_matrix,
            returns_flat,
            raw_view_ic=1e-6,  # below SURVIVAL_RAW_IC_MIN
            min_obs=50,
        )
        assert result["alpha_survival_ratio"] is None
