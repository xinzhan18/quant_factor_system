"""Registry for controlled daily factor templates."""

from __future__ import annotations

from typing import Callable

import pandas as pd

from research.daily_templates.conditional_rolling_mean import run as run_conditional_rolling_mean
from research.daily_templates.quantile_split_spread import run as run_quantile_split_spread


class DailyTemplateError(ValueError):
    """Raised when a daily template cannot be resolved or executed."""


TemplateFn = Callable[[pd.DataFrame, dict], pd.Series]

_TEMPLATES: dict[str, TemplateFn] = {
    "quantile_split_spread": run_quantile_split_spread,
    "conditional_rolling_mean": run_conditional_rolling_mean,
}

_TEMPLATE_META: dict[str, dict] = {
    "quantile_split_spread": {
        "description": "过去 N 日按 sorter 分位切割，对 value 求 top/bottom 均值差。",
        "required_params": ["value", "sorter", "window"],
        "optional_params": [
            "top_quantile",
            "bottom_quantile",
            "min_count",
            "output",
        ],
        "example": {
            "value": {"expression": "Sub(Div($high,$low),1)"},
            "sorter": {"field": "$close"},
            "window": 20,
            "top_quantile": 0.25,
            "bottom_quantile": 0.25,
            "output": "top_mean_minus_bottom_mean",
        },
    },
    "conditional_rolling_mean": {
        "description": "过去 N 日只保留 condition 为 true 的日期，对 value 求均值。",
        "required_params": ["value", "condition", "window"],
        "optional_params": ["min_count"],
        "example": {
            "value": {"field": "$close"},
            "condition": {"expression": "Gt($turnover_rate,Mean($turnover_rate,20))"},
            "window": 20,
            "min_count": 5,
        },
    },
}


def get_template(name: str) -> TemplateFn:
    try:
        return _TEMPLATES[name]
    except KeyError as exc:
        raise DailyTemplateError(f"unknown daily template: {name}") from exc


def list_templates() -> dict[str, dict]:
    """Return LLM-facing metadata for available daily templates."""
    return {name: dict(meta) for name, meta in sorted(_TEMPLATE_META.items())}


def run_template(name: str, df: pd.DataFrame, params: dict) -> pd.Series:
    try:
        out = get_template(name)(df, params)
    except Exception as exc:  # noqa: BLE001 - template errors become backend errors
        raise DailyTemplateError(f"{name} failed: {type(exc).__name__}: {exc}") from exc
    if not isinstance(out, pd.Series):
        raise DailyTemplateError(f"{name} returned {type(out).__name__}, expected Series")
    if not isinstance(out.index, pd.MultiIndex):
        raise DailyTemplateError(f"{name} must return MultiIndex Series")
    return out.sort_index()
