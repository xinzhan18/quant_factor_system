from __future__ import annotations

from research.memory.generation_logic import build_generation_logic_summary
from research.storage.paths import StoragePaths
from research.storage.yaml_io import save_yaml


def test_generation_logic_summary_counts_backends_templates_and_primitives(
    tmp_path,
) -> None:
    paths = StoragePaths(tmp_path)
    paths.ensure_dirs()
    save_yaml(
        paths.factors_dir / "F001.yaml",
        {
            "factor_id": "F001",
            "status": "active",
            "source_type": "daily_python",
            "primitive_dependencies": ["open_30m_volume_share_v1"],
            "factor_ir": {
                "factor_logic": {
                    "backend": "daily_python",
                    "template": "quantile_split_spread",
                }
            },
        },
    )
    save_yaml(
        paths.factors_dir / "F002.yaml",
        {
            "factor_id": "F002",
            "status": "active",
            "source_type": "dsl",
            "backend_provenance": {"backend": "qlib"},
        },
    )

    summary = build_generation_logic_summary(paths)

    assert summary["backend_counts"] == {"daily_python": 1, "qlib": 1}
    assert summary["daily_template_counts"] == {"quantile_split_spread": 1}
    assert summary["primitive_usage_counts"] == {"open_30m_volume_share_v1": 1}
    assert summary["template_to_factors"]["quantile_split_spread"] == ["F001"]
    assert summary["primitive_to_factors"]["open_30m_volume_share_v1"] == ["F001"]
