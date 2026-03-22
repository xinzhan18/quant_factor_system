"""Integration test: full mining pipeline without Qlib."""

from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pandas as pd
import pytest
import yaml

from mining.config import MiningConfig
from mining.evaluator import FactorMiningEvaluator, BatchResult
from mining.expression import ExpressionValidator
from mining.library import FactorLibrary
from mining.memory import ExperienceMemory


@pytest.fixture
def full_setup(tmp_mining_dir, config):
    """Set up a complete mining environment."""
    # Write seed YAML files
    mem_dir = Path(config.memory_dir)
    lib_dir = Path(config.library_dir)

    (mem_dir / "state.yaml").write_text(yaml.dump({
        "library": {"size": 0, "target_size": 100, "avg_ic": 0.0, "avg_correlation": 0.0},
        "domain_saturation": {cat: {"count": 0, "saturation": "low"} for cat in config.categories},
        "mining": {"total_batches": 0, "total_candidates": 0, "total_admitted": 0,
                   "total_rejected": 0, "yield_rate": 0.0, "last_batch_time": None},
    }))
    (mem_dir / "patterns.yaml").write_text(yaml.dump({
        "recommended_directions": [
            {"pattern": "Test", "description": "test", "success_rate": "high", "example_factors": []}
        ],
        "forbidden_regions": [],
    }))
    (mem_dir / "insights.yaml").write_text(yaml.dump({
        "insights": [{"insight": "test", "confidence": "high", "source": "test"}],
    }))
    (lib_dir / "library.yaml").write_text(yaml.dump({
        "thresholds": {"ic_min": 0.03, "correlation_max": 0.5},
        "factors": [],
    }))

    return config


def test_end_to_end(full_setup):
    """Test: validate -> evaluate -> admit -> update memory."""
    config = full_setup

    # 1. Validate expression
    validator = ExpressionValidator(config)
    result = validator.validate("Rank(Div(Sub($close, $vwap), $vwap))")
    assert result.valid

    # 2. Evaluate (mocked Qlib)
    dates = pd.bdate_range("2023-01-02", periods=30)
    instruments = [f"SH60000{i}" for i in range(10)]
    idx = pd.MultiIndex.from_product([dates, instruments], names=["datetime", "instrument"])
    np.random.seed(42)
    signal = np.random.randn(len(idx))

    with patch.object(FactorMiningEvaluator, "_ensure_qlib_initialized"), \
         patch.object(FactorMiningEvaluator, "_compute_factor_qlib") as mock_factor, \
         patch.object(FactorMiningEvaluator, "_get_returns_qlib") as mock_returns, \
         patch.object(FactorMiningEvaluator, "_get_fast_screening_universe", return_value=instruments), \
         patch.object(FactorMiningEvaluator, "_get_full_universe", return_value=instruments):

        mock_factor.return_value = pd.DataFrame({"factor": signal}, index=idx)
        mock_returns.return_value = pd.DataFrame(
            {"$returns_1d": signal + np.random.randn(len(idx)) * 0.2}, index=idx)

        evaluator = FactorMiningEvaluator(config)
        batch = [{"name": "VWAP_Dev", "expression": "Rank(Div(Sub($close, $vwap), $vwap))", "category": "vwap"}]
        result = evaluator.evaluate_batch(batch)

    assert isinstance(result, BatchResult)

    # 3. Admit to library
    library = FactorLibrary(config)
    for c in result.admitted:
        factor_id = library.admit({
            "name": c["name"],
            "expression": c["expression"],
            "category": c.get("category", "other"),
            "batch": "batch_001",
            "metrics": c.get("full_ic", {}),
        })
        assert factor_id is not None

    # 4. Update memory
    memory = ExperienceMemory(config)
    state = memory.read_state()
    state["library"]["size"] = library.size
    state["mining"]["total_batches"] = 1
    state["mining"]["total_candidates"] = len(batch)
    state["mining"]["total_admitted"] = len(result.admitted)
    memory.write_state(state)

    # Verify
    reloaded = memory.read_state()
    assert reloaded["mining"]["total_batches"] == 1

    # 5. Memory context should include library info
    ctx = memory.compose_search_context()
    assert "Library size:" in ctx
