from __future__ import annotations

from research.idea import build_idea_menu, format_idea_menu_markdown
from research.storage.paths import StoragePaths
from research.storage.yaml_io import save_yaml


def test_build_idea_menu_lists_primitives_and_templates(tmp_path) -> None:
    paths = StoragePaths(tmp_path)
    paths.ensure_dirs()
    save_yaml(
        paths.minute_primitive_registry_dir / "open_30m_volume_share_v1.yaml",
        {
            "feature_id": "open_30m_volume_share_v1",
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
            "status": "active",
        },
    )

    menu = build_idea_menu(paths)

    assert menu["menu_version"] == "v1"
    assert menu["rules"]["prefer_existing_primitives"] is True
    assert menu["rules"]["daily_python_policy"] == "template_only"
    assert menu["available_primitives"][0]["feature_id"] == "open_30m_volume_share_v1"
    assert menu["available_primitives"][0]["available_time"] == "T 15:00"
    assert "open_window_share" in menu["primitive_families"]
    assert "quantile_split_spread" in menu["available_daily_templates"]
    assert "historical_generation_summary" in menu
    assert "daily_python" in menu["allowed_backends"]


def test_format_idea_menu_markdown(tmp_path) -> None:
    paths = StoragePaths(tmp_path)
    paths.ensure_dirs()
    menu = build_idea_menu(paths)
    text = format_idea_menu_markdown(menu)

    assert "# Factor Idea Capability Menu" in text
    assert "## Available Primitives" in text
    assert "## Daily Templates" in text
    assert "## Historical Generation Summary" in text
    assert "quantile_split_spread" in text
