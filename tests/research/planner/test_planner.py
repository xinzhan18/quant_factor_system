from __future__ import annotations

import pytest

from research.planner import ExecutionPlanner, PlannerError
from research.storage.paths import StoragePaths
from research.storage.yaml_io import save_yaml


def _paths(tmp_path) -> StoragePaths:
    paths = StoragePaths(tmp_path)
    paths.ensure_dirs()
    return paths


def _write_primitive(paths: StoragePaths, feature_id: str = "open_30m_volume_share_v1") -> None:
    save_yaml(
        paths.minute_primitive_registry_dir / f"{feature_id}.yaml",
        {
            "feature_id": feature_id,
            "source_type": "minute_bar",
            "source_freq": "1min",
            "output_freq": "daily",
            "template": "window_share",
            "params": {
                "field": "volume",
                "numerator_window": "09:30-10:00",
                "denominator_window": "09:30-15:00",
            },
            "time_semantics": {"available_time": "T 15:00"},
        },
    )


def test_planner_noop_for_legacy_daily_qlib_candidate(tmp_path) -> None:
    paths = _paths(tmp_path)
    manifest = {
        "candidates": [
            {
                "candidate_id": "C001",
                "source_type": "dsl",
                "expression": "CsRank($close)",
            }
        ]
    }

    plan = ExecutionPlanner(
        manifest, paths, {}, start="2024-01-02", end="2024-01-31"
    ).build()

    assert plan.errors == []
    assert plan.primitive_tasks == []
    assert len(plan.qlib_tasks) == 1
    assert plan.qlib_tasks[0].expression == "CsRank($close)"
    assert plan.normalized_manifest["candidates"][0]["factor_logic"]["backend"] == "qlib"


def test_planner_builds_primitive_task_with_loader_config(tmp_path) -> None:
    paths = _paths(tmp_path)
    _write_primitive(paths)
    manifest = {
        "candidates": [
            {
                "candidate_id": "C001",
                "source_type": "dsl",
                "expression": "CsRank($open_30m_volume_share_v1)",
                "primitive_dependencies": ["open_30m_volume_share_v1"],
            }
        ]
    }

    plan = ExecutionPlanner(
        manifest,
        paths,
        {"primitive": {"minute_parquet": str(tmp_path / "minute.parquet")}},
        start="2024-01-02",
        end="2024-01-31",
    ).build()

    assert plan.errors == []
    assert len(plan.primitive_tasks) == 1
    task = plan.primitive_tasks[0]
    assert task.feature_id == "open_30m_volume_share_v1"
    assert task.status == "cache_miss"
    assert task.backend == "minute_bar_materializer"
    assert task.available_time == "T 15:00"


def test_planner_rejects_cache_miss_without_loader(tmp_path) -> None:
    paths = _paths(tmp_path)
    _write_primitive(paths)
    manifest = {
        "candidates": [
            {
                "candidate_id": "C001",
                "source_type": "dsl",
                "expression": "CsRank($open_30m_volume_share_v1)",
                "primitive_dependencies": ["open_30m_volume_share_v1"],
            }
        ]
    }

    with pytest.raises(PlannerError, match="primitive_cache_miss_without_loader"):
        ExecutionPlanner(
            manifest, paths, {}, start="2024-01-02", end="2024-01-31"
        ).build()


def test_planner_rejects_referenced_primitive_not_declared(tmp_path) -> None:
    paths = _paths(tmp_path)
    _write_primitive(paths)
    manifest = {
        "candidates": [
            {
                "candidate_id": "C001",
                "source_type": "dsl",
                "expression": "CsRank($open_30m_volume_share_v1)",
            }
        ]
    }

    with pytest.raises(PlannerError, match="primitive_referenced_but_not_declared"):
        ExecutionPlanner(
            manifest, paths, {}, start="2024-01-02", end="2024-01-31"
        ).build()


def test_planner_groups_daily_python_task(tmp_path) -> None:
    paths = _paths(tmp_path)
    manifest = {
        "candidates": [
            {
                "candidate_id": "C001",
                "ir_version": "v1",
                "factor_logic": {
                    "backend": "daily_python",
                    "template": "quantile_split_spread",
                    "params": {"window": 20},
                },
            }
        ]
    }

    plan = ExecutionPlanner(
        manifest, paths, {}, start="2024-01-02", end="2024-01-31"
    ).build()

    assert plan.errors == []
    assert plan.qlib_tasks == []
    assert len(plan.daily_python_tasks) == 1
    assert plan.daily_python_tasks[0].template == "quantile_split_spread"
