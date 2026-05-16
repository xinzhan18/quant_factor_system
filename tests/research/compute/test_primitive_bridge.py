from __future__ import annotations

import pandas as pd

from research.compute.primitive_bridge import (
    collect_primitive_dependencies,
    ensure_primitives_materialized,
)
from research.ir import normalize_manifest
from research.storage.paths import StoragePaths
from research.storage.yaml_io import save_yaml


def _minute_frame() -> pd.DataFrame:
    rows = []
    for ts in pd.date_range("2024-01-02 09:30", periods=11, freq="1min"):
        rows.append(
            {
                "time": ts,
                "symbol": "SH600000",
                "open": 10.0,
                "high": 10.2,
                "low": 9.9,
                "close": 10.1,
                "volume": 100.0,
                "amount": 1000.0,
            }
        )
    return pd.DataFrame(rows)


def test_collect_primitive_dependencies_dedupes() -> None:
    manifest = {
        "candidates": [
            {"candidate_id": "C001", "primitive_dependencies": ["a", "b"]},
            {"candidate_id": "C002", "primitive_dependencies": ["a"]},
        ]
    }
    assert collect_primitive_dependencies(manifest) == ["a", "b"]


def test_ensure_primitives_materialized_cache_hit_on_second_run(tmp_path) -> None:
    paths = StoragePaths(tmp_path)
    paths.ensure_dirs()
    save_yaml(
        paths.minute_primitive_registry_dir / "open_10m_ret_v1.yaml",
        {
            "feature_id": "open_10m_ret_v1",
            "source_type": "minute_bar",
            "source_freq": "1min",
            "output_freq": "daily",
            "template": "window_return",
            "params": {"window": "09:30-09:40"},
            "data_policy": {"min_bars": 8},
        },
    )
    manifest = {
        "candidates": [
            {
                "candidate_id": "C001",
                "source_type": "dsl",
                "expression": "Rank($open_10m_ret_v1)",
                "primitive_dependencies": ["open_10m_ret_v1"],
            }
        ]
    }
    data = _minute_frame()
    calls = {"n": 0}

    def loader(start, end, columns):
        calls["n"] += 1
        return data[columns]

    config = {"qlib_data_dir": str(tmp_path / "qlib_exp")}
    first = ensure_primitives_materialized(
        manifest, paths, config, "2024-01-02", "2024-01-02", minute_loader=loader
    )
    second = ensure_primitives_materialized(
        manifest, paths, config, "2024-01-02", "2024-01-02", minute_loader=loader
    )

    assert first["features"]["open_10m_ret_v1"]["status"] == "materialized"
    assert second["features"]["open_10m_ret_v1"]["status"] == "cache_hit"
    assert calls["n"] == 1
    assert (tmp_path / "qlib_exp" / "features" / "SH600000" / "open_10m_ret_v1.day.bin").exists()


def test_ensure_primitives_materialized_supports_proposed_primitives(tmp_path) -> None:
    paths = StoragePaths(tmp_path)
    paths.ensure_dirs()
    manifest = {
        "proposed_primitives": [
            {
                "feature_id": "open_10m_ret_tmp",
                "source_type": "minute_bar",
                "source_freq": "1min",
                "output_freq": "daily",
                "template": "window_return",
                "params": {"window": "09:30-09:40"},
                "data_policy": {"min_bars": 8},
            }
        ],
        "candidates": [
            {
                "candidate_id": "C001",
                "source_type": "dsl",
                "expression": "Rank($open_10m_ret_tmp)",
                "primitive_dependencies": ["open_10m_ret_tmp"],
            }
        ],
    }
    data = _minute_frame()

    def loader(start, end, columns):
        return data[columns]

    out = ensure_primitives_materialized(
        manifest,
        paths,
        {"qlib_data_dir": str(tmp_path / "qlib_exp")},
        "2024-01-02",
        "2024-01-02",
        minute_loader=loader,
    )

    assert out["features"]["open_10m_ret_tmp"]["status"] == "materialized"
    assert (tmp_path / "qlib_exp" / "features" / "SH600000" / "open_10m_ret_tmp.day.bin").exists()


def test_ensure_primitives_materialized_uses_nested_primitive_config(tmp_path) -> None:
    paths = StoragePaths(tmp_path)
    paths.ensure_dirs()
    save_yaml(
        paths.minute_primitive_registry_dir / "open_10m_ret_v1.yaml",
        {
            "feature_id": "open_10m_ret_v1",
            "source_type": "minute_bar",
            "source_freq": "1min",
            "output_freq": "daily",
            "template": "window_return",
            "params": {"window": "09:30-09:40"},
            "data_policy": {"min_bars": 8},
        },
    )
    minute_path = tmp_path / "minute.parquet"
    _minute_frame().to_parquet(minute_path)
    qlib_dir = tmp_path / "qlib_nested"
    manifest = {
        "candidates": [
            {
                "candidate_id": "C001",
                "source_type": "dsl",
                "expression": "Rank($open_10m_ret_v1)",
                "primitive_dependencies": ["open_10m_ret_v1"],
            }
        ]
    }

    out = ensure_primitives_materialized(
        manifest,
        paths,
        {
            "qlib_data_dir": str(tmp_path / "qlib_base"),
            "primitive": {
                "minute_parquet": str(minute_path),
                "qlib_data_dir": str(qlib_dir),
            },
        },
        "2024-01-02",
        "2024-01-02",
    )

    assert out["qlib_data_dir"] == str(qlib_dir)
    assert (qlib_dir / "features" / "SH600000" / "open_10m_ret_v1.day.bin").exists()


def test_ir_manifest_dependencies_feed_primitive_bridge() -> None:
    manifest = normalize_manifest(
        {
            "candidates": [
                {
                    "candidate_id": "C001",
                    "ir_version": "v1",
                    "data_logic": {
                        "primitive_dependencies": ["open_30m_volume_share_v1"]
                    },
                    "factor_logic": {
                        "backend": "qlib",
                        "expression": "CsRank($open_30m_volume_share_v1)",
                    },
                }
            ]
        }
    )

    assert collect_primitive_dependencies(manifest) == ["open_30m_volume_share_v1"]
