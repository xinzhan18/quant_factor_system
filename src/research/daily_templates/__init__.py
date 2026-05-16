"""Controlled daily factor templates."""

from research.daily_templates.registry import (
    DailyTemplateError,
    get_template,
    list_templates,
    run_template,
)

__all__ = ["DailyTemplateError", "get_template", "list_templates", "run_template"]
