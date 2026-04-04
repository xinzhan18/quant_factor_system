"""End-to-end tests for Python factor infrastructure (no Qlib/DB required)."""
from __future__ import annotations

import os

import numpy as np
import pandas as pd
import pytest
import yaml

from mining.config import MiningConfig
from mining.domain.similarity import check_lookahead_bias, compute_structural_similarity
from mining.evolution import EvolutionEngine
from mining.expression import ExpressionValidator
from mining.registry import FactorLibrary
from mining.logic import MarketLogicLibrary
from mining.ops_adapter import OpsAdapter
from mining.sandbox import SandboxError, run_factor_in_sandbox
from mining.logic import Scheduler


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def panel_df():
    """Standard test panel DataFrame with (datetime, instrument) MultiIndex."""
    dates = pd.date_range("2024-01-01", periods=30, freq="B")
    instruments = ["SH600000", "SH600001", "SH600002"]
    idx = pd.MultiIndex.from_product(
        [dates, instruments], names=["datetime", "instrument"]
    )
    np.random.seed(42)
    n = len(idx)
    return pd.DataFrame(
        {
            "close": np.random.uniform(10, 50, n),
            "open": np.random.uniform(10, 50, n),
            "high": np.random.uniform(10, 50, n),
            "low": np.random.uniform(5, 45, n),
            "volume": np.random.uniform(1e6, 1e8, n),
        },
        index=idx,
    )


# ---------------------------------------------------------------------------
# TestBatchYAMLFormat
# ---------------------------------------------------------------------------


class TestBatchYAMLFormat:
    """Test that mixed DSL+Python batch YAML parses correctly."""

    def test_mixed_batch_roundtrip(self, tmp_path):
        batch = {
            "batch_id": "test_001",
            "candidates": [
                {
                    "name": "dsl_factor",
                    "type": "dsl",
                    "expression": "Std($close, 20)",
                    "category": "volatility",
                },
                {
                    "name": "py_factor",
                    "type": "python",
                    "source": "python",
                    "code": "return ops.cs_rank(ops.std(df['close'], params['w']))",
                    "params": {"w": 20},
                    "param_space": {"w": [5, 60]},
                    "category": "volatility",
                    "logic_id": "L001",
                },
            ],
        }
        path = tmp_path / "batch.yaml"
        yaml.dump(batch, open(path, "w"))
        loaded = yaml.safe_load(open(path))
        assert len(loaded["candidates"]) == 2
        assert loaded["candidates"][0]["type"] == "dsl"
        assert loaded["candidates"][1]["type"] == "python"
        assert "code" in loaded["candidates"][1]


# ---------------------------------------------------------------------------
# TestPythonFactorPipeline
# ---------------------------------------------------------------------------


class TestPythonFactorPipeline:
    """Test Python factor code → validate → sandbox → result."""

    def test_validate_then_execute(self, panel_df):
        code = "return ops.cs_rank(ops.std(df['close'], 10))"
        # Validate
        v = ExpressionValidator()
        result = v.validate_python(code)
        assert result.valid
        # Execute
        series = run_factor_in_sandbox(code, panel_df, params={}, timeout=30)
        assert isinstance(series, pd.Series)
        assert len(series) == len(panel_df)

    def test_reject_invalid_code(self):
        code = "import os; os.system('rm -rf /')"
        v = ExpressionValidator()
        result = v.validate_python(code)
        assert not result.valid

    def test_ops_extraction_matches_execution(self, panel_df):
        code = "x = ops.std(df['close'], 10)\nreturn ops.cs_rank(x)"
        v = ExpressionValidator()
        ops_calls = v.extract_ops_calls(code)
        assert set(ops_calls) == {"std", "cs_rank"}
        # Also executes successfully
        result = run_factor_in_sandbox(code, panel_df, params={}, timeout=30)
        assert isinstance(result, pd.Series)


# ---------------------------------------------------------------------------
# TestSafetyChecks
# ---------------------------------------------------------------------------


class TestSafetyChecks:
    """Test lookahead detection and structural dedup."""

    def test_lookahead_catches_negative_shift(self):
        assert check_lookahead_bias("return df['close'].shift(-5)") is True
        assert check_lookahead_bias("return df['close'].shift(5)") is False

    def test_structural_similarity(self):
        c1 = "return ops.cs_rank(ops.std(df['close'], 20))"
        c2 = "return ops.cs_rank(ops.std(df['high'], 10))"
        assert compute_structural_similarity(c1, c2) == 1.0

        c3 = "return ops.hhi(df['volume'], 10)"
        assert compute_structural_similarity(c1, c3) == 0.0


# ---------------------------------------------------------------------------
# TestLibraryAdmission
# ---------------------------------------------------------------------------


class TestLibraryAdmission:
    """Test Python factor admission to library."""

    def test_python_factor_full_admission(self, tmp_path):
        config = MiningConfig(
            library_dir=str(tmp_path / "library"),
            python_factors_dir=str(tmp_path / "python_factors"),
        )
        os.makedirs(config.library_dir)
        # Create empty library index
        index = {
            "thresholds": {"ic": 0.03, "correlation": 0.7},
            "factors": [],
        }
        yaml.dump(
            index,
            open(os.path.join(config.library_dir, "library.yaml"), "w"),
        )

        lib = FactorLibrary(config)
        factor = {
            "name": "test_python",
            "source": "python",
            "code": "return ops.cs_rank(df['close'])",
            "params": {"w": 20},
            "param_space": {"w": [5, 60]},
            "logic_id": "L001",
            "category": "volume",
            "lineage": {
                "parents": [],
                "mutation_type": "genesis",
                "generation": 1,
            },
            "metrics": {"ic_mean": -0.04},
        }
        fid = lib.admit(factor)
        assert fid is not None

        # Verify it's in the index
        factors = lib.list_factors()
        admitted = [f for f in factors if f.get("source") == "python"]
        assert len(admitted) == 1


# ---------------------------------------------------------------------------
# TestLogicAndScheduler
# ---------------------------------------------------------------------------


class TestLogicAndScheduler:
    """Test logic library + scheduler integration."""

    def test_create_logic_then_schedule(self, tmp_path):
        logic_dir = str(tmp_path / "logic")
        os.makedirs(logic_dir)
        # Write taxonomy
        taxonomy = {
            "categories": {
                "volatility": "vol",
                "volume_price": "vp",
                "market_structure": "ms",
            }
        }
        yaml.dump(taxonomy, open(os.path.join(logic_dir, "taxonomy.yaml"), "w"))

        lib = MarketLogicLibrary(logic_dir)
        lib.create(
            name="vol_breakout",
            category="volume_price",
            hypothesis={
                "condition": "x",
                "behavior": "y",
                "timeframe": "5d",
                "direction": "long",
            },
        )
        lib.create(
            name="mean_revert",
            category="volatility",
            hypothesis={
                "condition": "a",
                "behavior": "b",
                "timeframe": "10d",
                "direction": "short",
            },
        )

        sched = Scheduler()
        # MarketLogicLibrary records use "id"; Scheduler expects "logic_id".
        # Bridge by adding the "logic_id" alias from the stored "id" field.
        raw_logics = lib.list_logics(status="active")
        logics = [
            {**r, "logic_id": r["id"], **r.get("stats", {})}
            for r in raw_logics
        ]
        coverage = lib.coverage_map()
        recs = sched.recommend(logics, coverage, 0.035, top_n=2)
        assert len(recs) == 2


# ---------------------------------------------------------------------------
# TestEvolutionModes
# ---------------------------------------------------------------------------


class TestEvolutionModes:
    """Test evolution engine mode selection."""

    def test_mode_ratio_adapts(self):
        engine = EvolutionEngine(MiningConfig())
        small = engine.suggest_mode(10)
        large = engine.suggest_mode(80)
        assert small["genesis"] > large["genesis"]
        assert large["mutate"] > small["mutate"]
