"""LLM-facing capability menu for /factor-idea."""

from __future__ import annotations

from typing import Any

import yaml

from data.primitive import PrimitiveRegistry
from research.daily_templates import list_templates
from research.memory.generation_logic import build_generation_logic_summary
from research.storage.paths import StoragePaths

PRIMITIVE_FAMILIES: dict[str, dict[str, Any]] = {
    "open_window_share": {
        "template": "window_share",
        "description": "开盘窗口成交量/成交额占全天比例，衡量早盘交易集中度。",
        "allowed_params": {
            "field": ["volume", "amount"],
            "numerator_window": [
                "09:30-09:35",
                "09:30-09:40",
                "09:30-10:00",
                "09:30-10:30",
            ],
            "denominator_window": ["09:30-15:00"],
        },
    },
    "tail_window_share": {
        "template": "window_share",
        "description": "尾盘窗口成交量/成交额占全天比例，衡量尾盘拥挤。",
        "allowed_params": {
            "field": ["volume", "amount"],
            "numerator_window": ["14:30-15:00", "14:40-15:00"],
            "denominator_window": ["09:30-15:00"],
        },
    },
    "window_return": {
        "template": "window_return",
        "description": "指定日内窗口收益或绝对收益。",
        "allowed_params": {
            "window": ["09:30-09:40", "09:30-10:00", "14:30-15:00"],
            "abs": [False, True],
        },
    },
    "intraday_distribution": {
        "template": "distribution_stats",
        "description": "日内分钟收益分布统计，如波动、偏度、峰度。",
        "allowed_params": {
            "field": ["ret_1m"],
            "stat": ["std", "skew", "kurt"],
        },
    },
    "masked_return_by_volume": {
        "template": "masked_return_mean",
        "description": "在放量/方向性分钟条件下聚合分钟收益。",
        "allowed_params": {
            "window": ["09:30-15:00"],
            "mask": ["ret_1m>0 and volume_z>1", "ret_1m<0 and volume_z>1"],
            "reducer": ["mean", "negative_mean"],
        },
    },
    "price_volume_corr": {
        "template": "price_volume_corr",
        "description": "日内分钟价格变化与成交量/成交额相关性。",
        "allowed_params": {
            "window": ["09:30-15:00", "09:30-10:00", "14:30-15:00"],
            "price_field": ["close"],
            "flow_field": ["volume", "amount"],
        },
    },
}


def build_idea_menu(paths: StoragePaths) -> dict[str, Any]:
    """Build the capability menu consumed by /factor-idea."""
    registry = PrimitiveRegistry(paths.minute_primitive_registry_dir)
    specs = registry.load_all()
    primitives: list[dict[str, Any]] = []
    for fid, spec in sorted(specs.items()):
        primitives.append(
            {
                "feature_id": fid,
                "source_type": spec.source_type,
                "source_freq": spec.source_freq,
                "output_freq": spec.output_freq,
                "template": spec.template,
                "params": dict(spec.params),
                "available_time": spec.time_semantics.get("available_time"),
                "status": spec.status,
                "spec_hash": spec.spec_hash,
            }
        )

    return {
        "menu_version": "v1",
        "rules": {
            "prefer_existing_primitives": True,
            "new_primitive_policy": "proposal_only",
            "max_new_primitives_per_batch": 3,
            "daily_python_policy": "template_only",
            "free_python_policy": "escape_hatch_only",
        },
        "available_primitives": primitives,
        "primitive_families": PRIMITIVE_FAMILIES,
        "available_daily_templates": list_templates(),
        "historical_generation_summary": build_generation_logic_summary(paths),
        "allowed_backends": ["qlib", "daily_python", "python"],
    }


def format_idea_menu_markdown(menu: dict[str, Any]) -> str:
    """Render a compact markdown packet for LLM consumption."""
    parts: list[str] = [
        "# Factor Idea Capability Menu",
        "",
        "## Rules",
        "",
        _yaml_block(menu.get("rules") or {}),
        "",
        "## Available Primitives",
        "",
        _yaml_block({"available_primitives": menu.get("available_primitives") or []}),
        "",
        "## Primitive Families",
        "",
        _yaml_block({"primitive_families": menu.get("primitive_families") or {}}),
        "",
        "## Daily Templates",
        "",
        _yaml_block({"available_daily_templates": menu.get("available_daily_templates") or {}}),
        "",
        "## Historical Generation Summary",
        "",
        _yaml_block(
            {
                "historical_generation_summary": menu.get(
                    "historical_generation_summary"
                )
                or {}
            }
        ),
        "",
        "## Allowed Backends",
        "",
        _yaml_block({"allowed_backends": menu.get("allowed_backends") or []}),
        "",
    ]
    return "\n".join(parts)


def _yaml_block(data: dict[str, Any]) -> str:
    body = yaml.safe_dump(
        data,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
    ).rstrip()
    return f"```yaml\n{body}\n```"
