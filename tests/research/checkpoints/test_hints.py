"""Tests for Phase 3 hints builder (_hints.yaml producer)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from research.checkpoints.hints import build_hints, write_hints


def _good_candidate(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "candidate_id": "C001",
        "expression": "Std($close, 20)",
        "source_type": "dsl",
        "coverage": 0.95,
        "compute_error": None,
        "ic": {
            "train": {"ic_mean": 0.015, "ic_ir": 0.32},
            "validation": {"ic_mean": 0.013, "ic_ir": 0.30},
            "train_validation_decay": 0.87,
        },
        "quintile": {
            "train": {"monotonicity": 0.95},
            "validation": {"monotonicity": 0.92},
        },
    }
    base.update(overrides)
    return base


def _result(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    return {"candidates": candidates}


class TestBuildHintsStructure:
    def test_top_level_keys(self, tmp_path: Path) -> None:
        hints = build_hints(
            batch_id="batch_001",
            direction="timing_signals",
            result=_result([_good_candidate()]),
            batches_dir=tmp_path / "batches",
        )
        assert set(hints.keys()) == {
            "batch_id",
            "direction",
            "generated_at",
            "mt_counts",
            "per_candidate",
        }
        assert hints["batch_id"] == "batch_001"
        assert hints["direction"] == "timing_signals"

    def test_mt_counts_zero_when_no_history(self, tmp_path: Path) -> None:
        hints = build_hints(
            batch_id="batch_001",
            direction="timing_signals",
            result=_result([_good_candidate()]),
            batches_dir=tmp_path / "batches",
        )
        mc = hints["mt_counts"]
        assert mc["cumulative_candidates"] == 0
        assert mc["direction_candidates"] == 0
        assert mc["validation_exposure"] == 0
        assert mc["n_batches_scanned"] == 0

    def test_per_candidate_keys_match_candidate_ids(self, tmp_path: Path) -> None:
        hints = build_hints(
            batch_id="batch_001",
            direction="timing_signals",
            result=_result([
                _good_candidate(candidate_id="C001"),
                _good_candidate(candidate_id="C002"),
                _good_candidate(candidate_id="C003"),
            ]),
            batches_dir=tmp_path / "batches",
        )
        assert set(hints["per_candidate"].keys()) == {"C001", "C002", "C003"}


class TestHardGateHint:
    def test_passing_candidate_records_passed_true(self, tmp_path: Path) -> None:
        hints = build_hints(
            batch_id="batch_001",
            direction="timing_signals",
            result=_result([_good_candidate()]),
            batches_dir=tmp_path / "batches",
        )
        entry = hints["per_candidate"]["C001"]
        assert entry["hard_gate"]["passed"] is True
        assert entry["hard_gate"]["reasons"] == []

    def test_failing_candidate_records_reasons(self, tmp_path: Path) -> None:
        c = _good_candidate(coverage=0.5)
        hints = build_hints(
            batch_id="batch_001",
            direction="timing_signals",
            result=_result([c]),
            batches_dir=tmp_path / "batches",
        )
        entry = hints["per_candidate"]["C001"]
        assert entry["hard_gate"]["passed"] is False
        assert any("coverage" in r for r in entry["hard_gate"]["reasons"])


class TestMtBudgetHint:
    def test_included_for_passing_gate(self, tmp_path: Path) -> None:
        hints = build_hints(
            batch_id="batch_001",
            direction="timing_signals",
            result=_result([_good_candidate()]),
            batches_dir=tmp_path / "batches",
        )
        mt = hints["per_candidate"]["C001"]["mt_budget"]
        assert set(mt.keys()) == {"score", "bucket", "terms", "search_adjusted"}
        assert mt["bucket"] in {"low", "medium", "high"}
        assert set(mt["terms"].keys()) == {"family", "direction", "exposure"}
        assert set(mt["search_adjusted"].keys()) == {"raw", "adjusted", "bucket"}

    def test_omitted_for_failing_gate(self, tmp_path: Path) -> None:
        c = _good_candidate(coverage=0.5)
        hints = build_hints(
            batch_id="batch_001",
            direction="timing_signals",
            result=_result([c]),
            batches_dir=tmp_path / "batches",
        )
        entry = hints["per_candidate"]["C001"]
        assert "mt_budget" not in entry

    def test_omitted_for_compute_error(self, tmp_path: Path) -> None:
        c = _good_candidate(compute_error="ValueError: x")
        hints = build_hints(
            batch_id="batch_001",
            direction="timing_signals",
            result=_result([c]),
            batches_dir=tmp_path / "batches",
        )
        entry = hints["per_candidate"]["C001"]
        assert entry["hard_gate"]["passed"] is False
        assert "mt_budget" not in entry


class TestMtCountsWithHistory:
    def _write_manifest(
        self,
        batches_dir: Path,
        batch_id: str,
        direction: str,
        n_candidates: int,
        has_judge: bool,
    ) -> None:
        bdir = batches_dir / batch_id
        bdir.mkdir(parents=True, exist_ok=True)
        manifest = {
            "batch_id": batch_id,
            "direction": direction,
            "candidates": [{"candidate_id": f"C{i:03d}"} for i in range(1, n_candidates + 1)],
        }
        (bdir / "manifest.yaml").write_text(
            yaml.dump(manifest, sort_keys=False), encoding="utf-8"
        )
        if has_judge:
            (bdir / "judge.md").write_text("# stub\n", encoding="utf-8")

    def test_scans_judged_only_and_attributes_direction(self, tmp_path: Path) -> None:
        batches_dir = tmp_path / "batches"
        # 3 prior judged batches for target direction, 2 for another, 1 unjudged
        self._write_manifest(batches_dir, "batch_001", "timing_signals", 5, True)
        self._write_manifest(batches_dir, "batch_002", "timing_signals", 4, True)
        self._write_manifest(batches_dir, "batch_003", "other", 6, True)
        self._write_manifest(batches_dir, "batch_004", "other", 3, True)
        self._write_manifest(batches_dir, "batch_005", "timing_signals", 5, False)

        hints = build_hints(
            batch_id="batch_006",
            direction="timing_signals",
            result=_result([_good_candidate()]),
            batches_dir=batches_dir,
        )
        mc = hints["mt_counts"]
        # Judged only: 4 batches scanned; cumulative = 5+4+6+3 = 18
        assert mc["n_batches_scanned"] == 4
        assert mc["cumulative_candidates"] == 18
        # direction counters: 5 + 4 = 9
        assert mc["direction_candidates"] == 9
        assert mc["validation_exposure"] == 4


class TestWriteHintsRoundtrip:
    def test_writes_yaml_and_roundtrips(self, tmp_path: Path) -> None:
        hints = build_hints(
            batch_id="batch_001",
            direction="timing_signals",
            result=_result([_good_candidate()]),
            batches_dir=tmp_path / "batches",
        )
        out = tmp_path / "batch_001" / "_hints.yaml"
        write_hints(out, hints)
        assert out.exists()
        loaded = yaml.safe_load(out.read_text(encoding="utf-8"))
        assert loaded["batch_id"] == "batch_001"
        assert loaded["per_candidate"]["C001"]["hard_gate"]["passed"] is True


# ---------------------------------------------------------------------------
# NEW in this round: gate_results detail + flattened rubric metrics +
# nearest_factor_expression lookup.
# ---------------------------------------------------------------------------


def _full_candidate(**overrides: Any) -> dict[str, Any]:
    """Candidate with every block the v3 schema produces so build_hints can
    extract CP04/CP05/CP06 metrics without None-filling."""
    base = _good_candidate()
    base.update(
        {
            "quintile": {
                "train": {"monotonicity": 0.95},
                "validation": {"monotonicity": 0.92},
                "ls_stats": {
                    "train": {"tstat": 2.9},
                    "validation": {"tstat": 3.89},
                },
            },
            "stability": {
                "split_stability": {
                    "sign_consistency": 1.0,
                    "dispersion": 0.21,
                }
            },
            "uniqueness": {
                "max_lib_corr": 0.30,
                "is_near_duplicate": False,
                "nearest_factor_id": "F005",
                "incremental_ic": 0.013,
            },
            "barra": {
                "style_r_squared": 0.08,
                "alpha_survival_ratio": 0.69,
                "barra_residual_ic": 0.013,
                "dominant_style_exposure": "vol_20d",
            },
            "distribution": {"extreme_ratio": 0.008},
        }
    )
    base.update(overrides)
    return base


class TestGateResults:
    def test_gate_results_present_when_passed(self, tmp_path: Path) -> None:
        hints = build_hints(
            batch_id="batch_001",
            direction="timing_signals",
            result=_result([_full_candidate()]),
            batches_dir=tmp_path / "batches",
        )
        gr = hints["per_candidate"]["C001"]["hard_gate"]["gate_results"]
        # All 8 gates listed
        expected = {
            "compute_error",
            "coverage",
            "sign_flip",
            "forbidden",
            "ic_oos_min",
            "oos_decay",
            "mono_flip",
            "near_duplicate",
        }
        assert set(gr.keys()) == expected
        assert gr["coverage"]["passed"] is True
        assert gr["coverage"]["value"] == 0.95
        assert gr["coverage"]["threshold"] == 0.80
        assert gr["near_duplicate"]["nearest"] == "F005"

    def test_gate_results_surfaces_failing_value(self, tmp_path: Path) -> None:
        c = _full_candidate(coverage=0.5)
        hints = build_hints(
            batch_id="batch_001",
            direction="timing_signals",
            result=_result([c]),
            batches_dir=tmp_path / "batches",
        )
        gr = hints["per_candidate"]["C001"]["hard_gate"]["gate_results"]
        assert gr["coverage"]["passed"] is False
        assert gr["coverage"]["value"] == 0.5

    def test_gate_results_for_compute_error_only_shows_compute_error_and_forbidden(
        self, tmp_path: Path
    ) -> None:
        c = _full_candidate(compute_error="ValueError: boom")
        hints = build_hints(
            batch_id="batch_001",
            direction="timing_signals",
            result=_result([c]),
            batches_dir=tmp_path / "batches",
        )
        gr = hints["per_candidate"]["C001"]["hard_gate"]["gate_results"]
        # Only compute_error + forbidden are ran on compute_error; downstream
        # metric gates skipped (no key added).
        assert gr["compute_error"]["passed"] is False
        assert gr["compute_error"]["error"].startswith("ValueError")
        assert "coverage" not in gr


class TestFlattenedMetrics:
    def test_all_four_cp_blocks_populated(self, tmp_path: Path) -> None:
        hints = build_hints(
            batch_id="batch_001",
            direction="timing_signals",
            result=_result([_full_candidate()]),
            batches_dir=tmp_path / "batches",
        )
        m = hints["per_candidate"]["C001"]["metrics"]
        # CP03
        assert m["cp03"]["ic_oos"] == 0.013
        assert m["cp03"]["icir_oos"] == 0.30
        assert m["cp03"]["ls_tstat_oos"] == 3.89
        # CP04
        assert m["cp04"]["style_r_squared"] == 0.08
        assert m["cp04"]["alpha_survival_ratio"] == 0.69
        assert m["cp04"]["dominant_style_exposure"] == "vol_20d"
        assert m["cp04"]["extreme_ratio"] == 0.008
        # CP05
        assert m["cp05"]["max_lib_corr"] == 0.30
        assert m["cp05"]["is_near_duplicate"] is False
        assert m["cp05"]["nearest_factor_id"] == "F005"
        assert m["cp05"]["incremental_ic"] == 0.013
        # CP06
        assert m["cp06"]["sign_consistency"] == 1.0
        assert m["cp06"]["train_validation_decay"] == 0.87

    def test_expression_and_coverage_mirrored_at_candidate_level(
        self, tmp_path: Path
    ) -> None:
        hints = build_hints(
            batch_id="batch_001",
            direction="timing_signals",
            result=_result([_full_candidate()]),
            batches_dir=tmp_path / "batches",
        )
        entry = hints["per_candidate"]["C001"]
        assert entry["expression"] == "Std($close, 20)"
        assert entry["coverage"] == 0.95

    def test_metrics_all_null_when_blocks_missing(self, tmp_path: Path) -> None:
        """Skeletal candidate (no barra/uniqueness/distribution blocks)
        must still have metrics with None values — never crash."""
        hints = build_hints(
            batch_id="batch_001",
            direction="timing_signals",
            result=_result([_good_candidate()]),  # no barra / uniqueness / ...
            batches_dir=tmp_path / "batches",
        )
        m = hints["per_candidate"]["C001"]["metrics"]
        assert m["cp04"]["style_r_squared"] is None
        assert m["cp05"]["nearest_factor_id"] is None
        assert m["cp05"]["is_near_duplicate"] is False  # coerced from missing


class TestNearestExpressionLookup:
    def test_resolves_from_factor_yaml(self, tmp_path: Path) -> None:
        factors = tmp_path / "factors"
        factors.mkdir()
        (factors / "F005.yaml").write_text(
            yaml.dump({"factor_id": "F005", "expression": "Mul($turnover, $pb)"}),
            encoding="utf-8",
        )
        hints = build_hints(
            batch_id="batch_001",
            direction="timing_signals",
            result=_result([_full_candidate()]),
            batches_dir=tmp_path / "batches",
            factors_dir=factors,
        )
        cp05 = hints["per_candidate"]["C001"]["metrics"]["cp05"]
        assert cp05["nearest_factor_expression"] == "Mul($turnover, $pb)"

    def test_null_when_factor_yaml_missing(self, tmp_path: Path) -> None:
        factors = tmp_path / "factors"
        factors.mkdir()  # empty
        hints = build_hints(
            batch_id="batch_001",
            direction="timing_signals",
            result=_result([_full_candidate()]),
            batches_dir=tmp_path / "batches",
            factors_dir=factors,
        )
        cp05 = hints["per_candidate"]["C001"]["metrics"]["cp05"]
        assert cp05["nearest_factor_expression"] is None

    def test_null_when_factors_dir_not_provided(self, tmp_path: Path) -> None:
        hints = build_hints(
            batch_id="batch_001",
            direction="timing_signals",
            result=_result([_full_candidate()]),
            batches_dir=tmp_path / "batches",
            # factors_dir omitted
        )
        cp05 = hints["per_candidate"]["C001"]["metrics"]["cp05"]
        assert cp05["nearest_factor_expression"] is None


class TestExpandedMetricsCoverage:
    """Verify metrics covers every result.yaml field the LLM may reference —
    rubric core + IS/OOS comparison + style_exposures + all_correlations +
    ic_by_year + split detail + feasibility block."""

    def _rich_candidate(self) -> dict[str, Any]:
        """Candidate with every field populated so we can assert extraction."""
        return {
            "candidate_id": "C001",
            "expression": "Std($close, 20)",
            "coverage": 0.95,
            "compute_error": None,
            "ic": {
                "train": {
                    "ic_mean": 0.018,
                    "ic_std": 0.11,
                    "ic_ir": 0.35,
                    "ic_win_rate": 0.55,
                    "n_days": 1598,
                },
                "validation": {
                    "ic_mean": 0.013,
                    "ic_std": 0.12,
                    "ic_ir": 0.30,
                    "ic_win_rate": 0.52,
                    "n_days": 476,
                },
                "sign_consistent": True,
                "train_validation_decay": 0.87,
                "by_year": {2020: 0.015, 2021: 0.012, 2022: 0.011},
                "autocorr_lag1": -0.025,
                "cum_ic_max_drawdown": -34.69,
                "worst_quarter": -0.05,
                "best_quarter": 0.04,
                "half_life_days": 7.2,
            },
            "quintile": {
                "train": {
                    "q1": -0.0001,
                    "q2": 0.0003,
                    "q3": 0.0008,
                    "q4": 0.0005,
                    "q5": 0.0012,
                    "monotonicity": 0.95,
                    "ls_mean": 0.0013,
                },
                "validation": {
                    "q1": -0.00038,
                    "q2": 0.00023,
                    "q3": 0.00074,
                    "q4": -0.00050,
                    "q5": -0.00029,
                    "monotonicity": 0.92,
                    "ls_mean": 0.00009,
                },
                "ls_stats": {
                    "train": {"tstat": 3.2, "sharpe": 1.4, "max_dd": -0.08},
                    "validation": {
                        "tstat": 3.89,
                        "sharpe": 1.6,
                        "sortino": 2.1,
                        "calmar": 1.1,
                        "max_dd": -0.10,
                        "mean": 0.0003,
                    },
                },
            },
            "stability": {
                "split_stability": {
                    "sign_consistency": 1.0,
                    "dispersion": 0.21,
                    "split_ic_means": [0.011, 0.014, 0.013, 0.015],
                    "n_splits": 4,
                }
            },
            "uniqueness": {
                "max_lib_corr": 0.30,
                "is_near_duplicate": False,
                "exceeds_threshold": False,
                "nearest_factor_id": "F005",
                "incremental_ic": 0.013,
                "all_correlations": {"F001": 0.10, "F002": 0.13, "F005": -0.25},
            },
            "barra": {
                "style_r_squared": 0.08,
                "alpha_survival_ratio": 0.69,
                "barra_residual_ic": 0.013,
                "barra_residual_icir": 0.28,
                "dominant_style_exposure": "vol_20d",
                "style_crowding_risk": "medium",
                "style_exposures": {
                    "vol_20d": 0.45,
                    "log_circ_cap": 0.05,
                    "book_to_price": 0.12,
                },
            },
            "distribution": {
                "extreme_ratio": 0.008,
                "skew": 0.11,
                "kurt": -0.68,
                "zero_ratio": 0.06,
            },
            "feasibility": {
                "turnover_mean": 1.01,
                "liquidity_coverage": 0.68,
                "tail_concentration": 0.01,
                "small_cap_concentration": 0.29,
                "signal_half_life": 6.0,
                "signal_autocorr_lag1": 0.87,
                "rebalance_stress": {
                    "rebalance_stress_proxy": 0.01,
                    "rebalance_stress_bucket": "low",
                },
            },
        }

    def test_cp03_includes_is_counterparts_and_ls_detail(self, tmp_path: Path) -> None:
        hints = build_hints(
            batch_id="batch_001",
            direction="timing_signals",
            result=_result([self._rich_candidate()]),
            batches_dir=tmp_path / "batches",
        )
        cp03 = hints["per_candidate"]["C001"]["metrics"]["cp03"]
        # IS counterparts
        assert cp03["ic_is"] == 0.018
        assert cp03["icir_is"] == 0.35
        assert cp03["ic_win_rate_oos"] == 0.52
        # OOS ls detail
        assert cp03["ls_sharpe_oos"] == 1.6
        assert cp03["ls_sortino_oos"] == 2.1
        assert cp03["ls_calmar_oos"] == 1.1
        assert cp03["ls_max_dd_oos"] == -0.10
        # IS ls for comparison
        assert cp03["ls_sharpe_is"] == 1.4
        assert cp03["ls_tstat_is"] == 3.2

    def test_cp04_includes_style_exposures_and_distribution(
        self, tmp_path: Path
    ) -> None:
        hints = build_hints(
            batch_id="batch_001",
            direction="timing_signals",
            result=_result([self._rich_candidate()]),
            batches_dir=tmp_path / "batches",
        )
        cp04 = hints["per_candidate"]["C001"]["metrics"]["cp04"]
        assert cp04["style_exposures"] == {
            "vol_20d": 0.45,
            "log_circ_cap": 0.05,
            "book_to_price": 0.12,
        }
        assert cp04["style_crowding_risk"] == "medium"
        assert cp04["barra_residual_icir"] == 0.28
        assert cp04["distribution_skew"] == 0.11
        assert cp04["distribution_kurt"] == -0.68
        assert cp04["distribution_zero_ratio"] == 0.06

    def test_cp05_includes_all_correlations(self, tmp_path: Path) -> None:
        hints = build_hints(
            batch_id="batch_001",
            direction="timing_signals",
            result=_result([self._rich_candidate()]),
            batches_dir=tmp_path / "batches",
        )
        cp05 = hints["per_candidate"]["C001"]["metrics"]["cp05"]
        assert cp05["all_correlations"] == {"F001": 0.10, "F002": 0.13, "F005": -0.25}
        assert cp05["exceeds_threshold"] is False

    def test_cp06_includes_by_year_quarter_and_split_detail(
        self, tmp_path: Path
    ) -> None:
        hints = build_hints(
            batch_id="batch_001",
            direction="timing_signals",
            result=_result([self._rich_candidate()]),
            batches_dir=tmp_path / "batches",
        )
        cp06 = hints["per_candidate"]["C001"]["metrics"]["cp06"]
        assert cp06["ic_by_year"] == {2020: 0.015, 2021: 0.012, 2022: 0.011}
        assert cp06["worst_quarter_ic"] == -0.05
        assert cp06["best_quarter_ic"] == 0.04
        assert cp06["split_ic_means"] == [0.011, 0.014, 0.013, 0.015]
        assert cp06["split_dispersion"] == 0.21
        assert cp06["n_splits"] == 4

    def test_feasibility_block_present(self, tmp_path: Path) -> None:
        hints = build_hints(
            batch_id="batch_001",
            direction="timing_signals",
            result=_result([self._rich_candidate()]),
            batches_dir=tmp_path / "batches",
        )
        feas = hints["per_candidate"]["C001"]["metrics"]["feasibility"]
        assert feas["turnover_mean"] == 1.01
        assert feas["liquidity_coverage"] == 0.68
        assert feas["small_cap_concentration"] == 0.29
        assert feas["rebalance_stress"]["rebalance_stress_bucket"] == "low"

    def test_missing_blocks_yield_empty_dicts_not_crashes(self, tmp_path: Path) -> None:
        """Skeletal candidate — style_exposures / all_correlations / ic_by_year
        must come back as empty dicts / lists, not None, so LLM can iterate."""
        hints = build_hints(
            batch_id="batch_001",
            direction="timing_signals",
            result=_result([_good_candidate()]),
            batches_dir=tmp_path / "batches",
        )
        m = hints["per_candidate"]["C001"]["metrics"]
        assert m["cp04"]["style_exposures"] == {}
        assert m["cp05"]["all_correlations"] == {}
        assert m["cp06"]["ic_by_year"] == {}
        assert m["cp06"]["split_ic_means"] == []
        assert m["feasibility"]["rebalance_stress"] == {}

    def test_cp03_monotonicity_and_quintile_returns_extracted(
        self, tmp_path: Path
    ) -> None:
        """New in this round: rank-order evidence (monotonicity + per-bucket
        returns) must live in cp03 alongside the core IC/ICIR/ls_tstat."""
        hints = build_hints(
            batch_id="batch_001",
            direction="timing_signals",
            result=_result([self._rich_candidate()]),
            batches_dir=tmp_path / "batches",
        )
        cp03 = hints["per_candidate"]["C001"]["metrics"]["cp03"]
        # Monotonicity IS + OOS
        assert cp03["monotonicity_is"] == 0.95
        assert cp03["monotonicity_oos"] == 0.92
        # Quintile returns: q1..q5 only (no monotonicity / ls_mean sibling fields)
        assert cp03["quintile_returns_is"] == {
            "q1": -0.0001, "q2": 0.0003, "q3": 0.0008, "q4": 0.0005, "q5": 0.0012,
        }
        assert cp03["quintile_returns_oos"] == {
            "q1": -0.00038, "q2": 0.00023, "q3": 0.00074, "q4": -0.00050, "q5": -0.00029,
        }
        # ls_mean from quintile block (IS + OOS)
        assert cp03["ls_mean_is"] == 0.0013
        assert cp03["ls_mean_oos"] == 0.00009
        # IC variance + sample size
        assert cp03["ic_std_is"] == 0.11
        assert cp03["ic_std_oos"] == 0.12
        assert cp03["n_days_is"] == 1598
        assert cp03["n_days_oos"] == 476
        assert cp03["ic_win_rate_is"] == 0.55

    def test_cp06_autocorr_drawdown_and_sign_consistent(
        self, tmp_path: Path
    ) -> None:
        """New in this round: CP06 exposes IC time-series properties."""
        hints = build_hints(
            batch_id="batch_001",
            direction="timing_signals",
            result=_result([self._rich_candidate()]),
            batches_dir=tmp_path / "batches",
        )
        cp06 = hints["per_candidate"]["C001"]["metrics"]["cp06"]
        assert cp06["ic_autocorr_lag1"] == -0.025
        assert cp06["cum_ic_max_drawdown"] == -34.69
        assert cp06["sign_consistent"] is True

    def test_feasibility_includes_ic_half_life(self, tmp_path: Path) -> None:
        """New in this round: ic.half_life_days is relocated under feasibility
        (distinct from feasibility.signal_half_life)."""
        candidate = self._rich_candidate()
        candidate["feasibility"] = {"signal_half_life": 6.0, "rebalance_stress": {}}
        hints = build_hints(
            batch_id="batch_001",
            direction="timing_signals",
            result=_result([candidate]),
            batches_dir=tmp_path / "batches",
        )
        feas = hints["per_candidate"]["C001"]["metrics"]["feasibility"]
        assert feas["ic_half_life_days"] == 7.2
        assert feas["signal_half_life"] == 6.0  # distinct field
