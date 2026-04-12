"""Tests for Phase 1 START + DESIGN (DSL / Python / dedup / freeze)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from research.phases.phase1_start import (
    MIN_BATCH_GOAL_LENGTH,
    Phase1FreezeError,
    canonicalize_expression,
    check_duplicate_expression,
    freeze_manifest,
    validate_batch_goal,
    validate_dsl_expression,
    validate_python_candidate,
)
from research.storage.yaml_io import load_yaml


class TestValidateDslExpression:
    def test_empty_rejected(self) -> None:
        assert "empty_expression" in validate_dsl_expression("")
        assert "empty_expression" in validate_dsl_expression("   ")

    def test_clean_expression_passes(self) -> None:
        assert validate_dsl_expression("Std($close, 20)") == []

    def test_unknown_operator_rejected(self) -> None:
        reasons = validate_dsl_expression("Frobnicate($close, 20)")
        assert any("unknown_operator:Frobnicate" in r for r in reasons)

    def test_unavailable_operator_rejected(self) -> None:
        reasons = validate_dsl_expression("Neg($close)")
        assert any("unavailable_operator:Neg" in r for r in reasons)

    def test_unknown_field_rejected(self) -> None:
        reasons = validate_dsl_expression("Std($unknown_field, 20)")
        assert any("unknown_field:$unknown_field" in r for r in reasons)

    def test_forbidden_vwap(self) -> None:
        reasons = validate_dsl_expression("Mul($vwap, $volume)")
        assert any("forbidden_field:$vwap" in r for r in reasons)

    def test_constant_expression_rejected(self) -> None:
        reasons = validate_dsl_expression("Log(2)")
        assert "constant_expression" in reasons

    def test_unbalanced_parens(self) -> None:
        assert "unbalanced_parentheses" in validate_dsl_expression("Std($close, 20")
        assert "unbalanced_parentheses" in validate_dsl_expression("Std($close, 20))")

    def test_too_deep_expression(self) -> None:
        expr = "Mul(" * 12 + "$close" + ")" * 12
        reasons = validate_dsl_expression(expr)
        assert any("expression_too_deep" in r for r in reasons)


class TestCanonicalize:
    def test_whitespace_stripped(self) -> None:
        c1 = canonicalize_expression("Mul($close, 20)")
        c2 = canonicalize_expression("Mul(  $close  ,  20  )")
        assert c1 == c2

    def test_commutative_mul_equivalent(self) -> None:
        c1 = canonicalize_expression("Mul($close, $volume)")
        c2 = canonicalize_expression("Mul($volume, $close)")
        assert c1 == c2

    def test_commutative_add_equivalent(self) -> None:
        c1 = canonicalize_expression("Add($high, $low)")
        c2 = canonicalize_expression("Add($low, $high)")
        assert c1 == c2

    def test_non_commutative_sub_not_equivalent(self) -> None:
        c1 = canonicalize_expression("Sub($close, $open)")
        c2 = canonicalize_expression("Sub($open, $close)")
        assert c1 != c2

    def test_nested_commutative(self) -> None:
        c1 = canonicalize_expression("Mul(Add($high, $low), $volume)")
        c2 = canonicalize_expression("Mul($volume, Add($low, $high))")
        assert c1 == c2


class TestCheckDuplicate:
    def test_matches_exactly(self) -> None:
        existing = ["Mul($close,$volume)", "Std($close,20)"]
        assert check_duplicate_expression("Mul($close,$volume)", existing)

    def test_miss(self) -> None:
        existing = ["Mul($close,$volume)"]
        assert not check_duplicate_expression("Std($close,20)", existing)


class TestValidateBatchGoal:
    def test_empty_rejected(self) -> None:
        assert "empty_batch_goal" in validate_batch_goal(None)
        assert "empty_batch_goal" in validate_batch_goal("")
        assert "empty_batch_goal" in validate_batch_goal("   ")

    def test_too_short_rejected(self) -> None:
        reasons = validate_batch_goal("short")
        assert any("batch_goal_too_short" in r for r in reasons)

    def test_long_enough_passes(self) -> None:
        goal = "Verify low-volatility + high-turnover cross signal on csi1000"
        assert len(goal) >= MIN_BATCH_GOAL_LENGTH
        assert validate_batch_goal(goal) == []


class TestValidatePythonCandidate:
    def _write(self, tmp_path: Path, body: str) -> Path:
        p = tmp_path / "cand.py"
        p.write_text(body, encoding="utf-8")
        return p

    def test_good_candidate_passes(self, tmp_path: Path) -> None:
        p = self._write(
            tmp_path,
            "import pandas as pd\n"
            "REQUIRED_FIELDS=['$close']\nVECTORIZED=True\n"
            "def compute(df: pd.DataFrame) -> pd.Series:\n"
            "    return df['$close']\n",
        )
        assert validate_python_candidate(p) == []

    def test_forbidden_import_rejected(self, tmp_path: Path) -> None:
        p = self._write(
            tmp_path,
            "import subprocess\n"
            "REQUIRED_FIELDS=['$close']\nVECTORIZED=True\n"
            "def compute(df): return df['$close']\n",
        )
        reasons = validate_python_candidate(p)
        assert any("python_contract" in r for r in reasons)

    def test_missing_file_rejected(self, tmp_path: Path) -> None:
        reasons = validate_python_candidate(tmp_path / "nope.py")
        assert reasons != []


class TestFreezeManifest:
    def _good_candidate(self, **overrides: Any) -> dict[str, Any]:
        base: dict[str, Any] = {
            "candidate_id": "C001",
            "source_type": "dsl",
            "expression": "Std($close, 20)",
        }
        base.update(overrides)
        return base

    def _goal(self) -> str:
        return "Probe cross-sectional volatility as short-horizon alpha on csi1000."

    def test_clean_freeze(self, tmp_path: Path) -> None:
        manifest_path = tmp_path / "batch_test" / "manifest.yaml"
        report = freeze_manifest(
            batch_id="batch_test",
            direction="volatility",
            batch_goal=self._goal(),
            candidates=[
                self._good_candidate(candidate_id="C001"),
                self._good_candidate(
                    candidate_id="C002", expression="Mul($close, $volume)"
                ),
            ],
            existing_canonicals=[],
            manifest_path=manifest_path,
        )

        assert report.all_passed
        assert report.manifest_path == manifest_path
        assert manifest_path.exists()

        loaded = load_yaml(manifest_path)
        assert loaded["batch_id"] == "batch_test"
        assert loaded["direction"] == "volatility"
        assert loaded["sample_policy_version"] == "v3"
        assert len(loaded["candidates"]) == 2
        # canonical captured for DSL candidates
        assert loaded["candidates"][0]["canonical"]

    def test_too_short_goal_raises(self, tmp_path: Path) -> None:
        with pytest.raises(Phase1FreezeError, match="batch_goal"):
            freeze_manifest(
                "batch_test",
                "vol",
                "tiny",
                [self._good_candidate()],
                existing_canonicals=[],
                manifest_path=tmp_path / "manifest.yaml",
            )

    def test_bad_candidate_raises_with_report(self, tmp_path: Path) -> None:
        try:
            freeze_manifest(
                "batch_test",
                "vol",
                self._goal(),
                [
                    self._good_candidate(candidate_id="C001"),
                    self._good_candidate(candidate_id="C002", expression="Neg($close)"),
                ],
                existing_canonicals=[],
                manifest_path=tmp_path / "manifest.yaml",
            )
        except Phase1FreezeError as exc:
            # The report is attached as the second arg
            report = exc.args[1]
            assert report.candidates[0].passed is True
            assert report.candidates[1].passed is False
            assert any(
                "unavailable_operator:Neg" in r
                for r in report.candidates[1].reasons
            )
        else:
            pytest.fail("expected Phase1FreezeError")

    def test_library_dedup_rejected(self, tmp_path: Path) -> None:
        # F001 is already in the library as canonical Mul($close,$volume)
        existing = [canonicalize_expression("Mul($close, $volume)")]
        with pytest.raises(Phase1FreezeError, match="duplicate"):
            freeze_manifest(
                "batch_test",
                "vol",
                self._goal(),
                [
                    # C001 submits it in the opposite order — should still dedupe
                    self._good_candidate(candidate_id="C001", expression="Mul($volume, $close)"),
                ],
                existing_canonicals=existing,
                manifest_path=tmp_path / "manifest.yaml",
            )

    def test_in_batch_dedup_rejected(self, tmp_path: Path) -> None:
        with pytest.raises(Phase1FreezeError, match="duplicate_within_batch"):
            freeze_manifest(
                "batch_test",
                "vol",
                self._goal(),
                [
                    self._good_candidate(candidate_id="C001", expression="Mul($close, $volume)"),
                    self._good_candidate(candidate_id="C002", expression="Mul($volume, $close)"),
                ],
                existing_canonicals=[],
                manifest_path=tmp_path / "manifest.yaml",
            )

    def test_manifest_is_atomic(self, tmp_path: Path) -> None:
        manifest_path = tmp_path / "batch_atomic" / "manifest.yaml"
        report = freeze_manifest(
            "batch_atomic",
            "vol",
            self._goal(),
            [self._good_candidate()],
            existing_canonicals=[],
            manifest_path=manifest_path,
        )
        assert report.all_passed
        # No temp files hanging around
        leftover = list(manifest_path.parent.glob(".tmp_*"))
        assert leftover == []

    def test_python_candidate_freeze(self, tmp_path: Path) -> None:
        py_path = tmp_path / "F999.py"
        py_path.write_text(
            "import pandas as pd\n"
            "REQUIRED_FIELDS=['$close']\nVECTORIZED=True\n"
            "def compute(df: pd.DataFrame) -> pd.Series:\n"
            "    return df['$close']\n",
            encoding="utf-8",
        )
        manifest_path = tmp_path / "batch_py" / "manifest.yaml"
        report = freeze_manifest(
            "batch_py",
            "py_direction",
            self._goal(),
            [
                {
                    "candidate_id": "C001",
                    "source_type": "python",
                    "path": str(py_path),
                }
            ],
            existing_canonicals=[],
            manifest_path=manifest_path,
        )
        assert report.all_passed
        loaded = load_yaml(manifest_path)
        assert loaded["candidates"][0]["source_type"] == "python"
        assert loaded["candidates"][0]["path"] == str(py_path)

    def test_manifest_pass_through_fields(self, tmp_path: Path) -> None:
        """Plan says rationale + parent_batch/parent_candidate_id/transformation
        are pass-through fields on candidates."""
        manifest_path = tmp_path / "batch_pt" / "manifest.yaml"
        report = freeze_manifest(
            batch_id="batch_pt",
            direction="volatility",
            batch_goal=self._goal(),
            candidates=[
                {
                    "candidate_id": "C001",
                    "source_type": "dsl",
                    "expression": "Std($close, 20)",
                    "rationale": "Test vol clustering under high turnover",
                    "parent_batch": "batch_101",
                    "parent_candidate_id": "C004",
                    "transformation": "extend_lookback_60d_to_80d",
                },
            ],
            existing_canonicals=[],
            manifest_path=manifest_path,
        )
        assert report.all_passed
        loaded = load_yaml(manifest_path)
        c = loaded["candidates"][0]
        assert c["rationale"].startswith("Test")
        assert c["parent_batch"] == "batch_101"
        assert c["parent_candidate_id"] == "C004"
        assert c["transformation"] == "extend_lookback_60d_to_80d"
