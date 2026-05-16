from __future__ import annotations

import pytest

from research.ir import FactorIRValidationError, normalize_candidate, normalize_manifest
from research.ir.validator import validate_factor_ir


def test_legacy_dsl_candidate_normalizes_to_qlib_ir() -> None:
    ir = normalize_candidate(
        {
            "candidate_id": "C001",
            "source_type": "dsl",
            "expression": "CsRank($close)",
            "primitive_dependencies": ["open_30m_volume_share_v1"],
            "rationale": "test rationale",
        }
    )

    assert ir.candidate_id == "C001"
    assert ir.ir_version == "v1"
    assert ir.factor_logic.backend == "qlib"
    assert ir.factor_logic.expression == "CsRank($close)"
    assert ir.data_logic.primitive_dependencies == ["open_30m_volume_share_v1"]
    assert ir.hypothesis == "test rationale"
    assert validate_factor_ir(ir) == []


def test_ir_candidate_normalizes_to_execution_candidate() -> None:
    manifest = {
        "batch_id": "batch_test",
        "candidates": [
            {
                "candidate_id": "C001",
                "ir_version": "v1",
                "hypothesis": "早盘成交集中代表拥挤交易。",
                "data_logic": {
                    "primitive_dependencies": ["open_30m_volume_share_v1"]
                },
                "factor_logic": {
                    "backend": "qlib",
                    "expression": "CsRank($open_30m_volume_share_v1)",
                },
                "expected_sign": "negative",
                "label": {"horizon": 1, "decision_time": "T+1 open"},
            }
        ],
    }

    normalized = normalize_manifest(manifest)
    cand = normalized["candidates"][0]
    assert normalized["ir_version"] == "v1"
    assert normalized["factor_ir"][0]["factor_logic"]["backend"] == "qlib"
    assert cand["source_type"] == "dsl"
    assert cand["expression"] == "CsRank($open_30m_volume_share_v1)"
    assert cand["primitive_dependencies"] == ["open_30m_volume_share_v1"]
    assert cand["factor_logic"]["backend"] == "qlib"


def test_legacy_python_candidate_normalizes_to_python_backend() -> None:
    normalized = normalize_manifest(
        {
            "candidates": [
                {
                    "candidate_id": "C001",
                    "source_type": "python",
                    "path": "storage/vault/batches/batch_x/C001.py",
                }
            ]
        }
    )

    cand = normalized["candidates"][0]
    assert cand["source_type"] == "python"
    assert cand["path"].endswith("C001.py")
    assert cand["factor_logic"]["backend"] == "python"


def test_unknown_backend_raises_validation_error() -> None:
    with pytest.raises(FactorIRValidationError, match="unknown_backend"):
        normalize_manifest(
            {
                "candidates": [
                    {
                        "candidate_id": "C001",
                        "ir_version": "v1",
                        "factor_logic": {"backend": "spark", "expression": "$close"},
                    }
                ]
            }
        )


def test_unknown_daily_template_raises_validation_error() -> None:
    with pytest.raises(FactorIRValidationError, match="unknown_daily_template"):
        normalize_manifest(
            {
                "candidates": [
                    {
                        "candidate_id": "C001",
                        "ir_version": "v1",
                        "factor_logic": {
                            "backend": "daily_python",
                            "template": "freeform_script",
                        },
                    }
                ]
            }
        )
