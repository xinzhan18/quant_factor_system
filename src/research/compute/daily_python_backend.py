"""Backend for controlled daily Python templates."""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from research.daily_templates import run_template
from research.daily_templates.expression import extract_fields

logger = logging.getLogger(__name__)


def run_daily_python_candidate(
    candidate: dict[str, Any],
    market_df: pd.DataFrame,
    *,
    start: str,
    end: str,
) -> pd.Series:
    """Execute a ``backend=daily_python`` candidate.

    Missing fields are loaded from the active Qlib provider.  This lets daily
    templates consume primitive fields after Pre-Phase2 materialization.
    """
    logic = candidate.get("factor_logic") or {}
    template = str(logic.get("template") or "")
    params = dict(logic.get("params") or {})
    if not template:
        raise ValueError("daily_python candidate missing template")
    if not params:
        raise ValueError("daily_python candidate missing params")

    df = _ensure_template_fields(market_df, params, start=start, end=end)
    out = run_template(template, df, params)
    out.name = candidate.get("candidate_id") or "value"
    return out


def _ensure_template_fields(
    market_df: pd.DataFrame,
    params: dict[str, Any],
    *,
    start: str,
    end: str,
) -> pd.DataFrame:
    fields = extract_fields(params)
    missing = [field for field in fields if field not in market_df.columns]
    if not missing:
        return market_df
    extra = _load_qlib_fields(missing, start=start, end=end)
    merged = market_df.join(extra, how="left")
    still_missing = [field for field in fields if field not in merged.columns]
    if still_missing:
        raise ValueError(f"daily_python missing fields: {still_missing}")
    return merged


def _load_qlib_fields(fields: list[str], *, start: str, end: str) -> pd.DataFrame:
    from qlib.data import D

    inst_dict = D.instruments("all")
    df = D.features(inst_dict, fields=fields, start_time=start, end_time=end)
    if isinstance(df.index, pd.MultiIndex):
        df = df.swaplevel()
        df.index.names = ["datetime", "instrument"]
        df = df.sort_index()
    df.columns = fields
    logger.info("daily_python loaded missing Qlib fields: %s", fields)
    return df
