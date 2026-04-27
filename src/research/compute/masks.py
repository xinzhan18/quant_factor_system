"""Universe and tradability masks for Phase 2 evaluation.

Raw factor values are intentionally computed on the broad Qlib ``all``
instrument set.  Evaluation metrics apply these masks afterwards so the
same factor cache can be reused across all / CSI300 / CSI1000 views.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


DEFAULT_TRADABILITY_CONFIG: dict[str, Any] = {
    "filter_suspend": True,
    "filter_limit": True,
    "filter_st": True,
    "filter_newly_listed": True,
    "volume_zero_means_suspended": True,
    "amount_zero_means_suspended": True,
    "limit_up_tolerance": 0.999,
    "limit_down_tolerance": 1.001,
    "min_listing_days": 60,
}


def _time_symbol_index(index: pd.MultiIndex) -> tuple[pd.DatetimeIndex, pd.Index]:
    """Return the first two MultiIndex levels as datetime + symbol arrays."""
    if not isinstance(index, pd.MultiIndex) or index.nlevels < 2:
        raise ValueError("expected MultiIndex(datetime, instrument)")
    times = pd.to_datetime(index.get_level_values(0))
    symbols = index.get_level_values(1)
    return pd.DatetimeIndex(times), pd.Index(symbols)


def _first_existing_col(df: pd.DataFrame, names: tuple[str, ...]) -> str | None:
    for name in names:
        if name in df.columns:
            return name
    return None


def build_tradable_mask(
    market_df: pd.DataFrame,
    *,
    stock_status: pd.DataFrame | None = None,
    config: dict[str, Any] | None = None,
) -> pd.Series:
    """Build a PIT daily tradability mask from market + status data.

    Parameters
    ----------
    market_df
        MultiIndex(datetime, instrument) market panel. Expected columns include
        ``$close``, ``$volume``, ``$amount``, ``$limit_up``, ``$limit_down``.
    stock_status
        Optional MultiIndex(datetime, instrument) frame with ``is_st`` and/or
        ``is_suspended`` boolean columns.
    config
        Optional overrides for :data:`DEFAULT_TRADABILITY_CONFIG`.

    Returns
    -------
    pd.Series
        Boolean Series indexed like ``market_df``; ``True`` means eligible for
        cross-sectional evaluation.
    """
    cfg = {**DEFAULT_TRADABILITY_CONFIG, **(config or {})}
    if not isinstance(market_df.index, pd.MultiIndex):
        raise ValueError("market_df must have MultiIndex(datetime, instrument)")

    mask = pd.Series(True, index=market_df.index, name="tradable")

    volume_col = _first_existing_col(market_df, ("$volume", "volume"))
    amount_col = _first_existing_col(market_df, ("$amount", "amount"))
    close_col = _first_existing_col(market_df, ("$close", "close"))
    limit_up_col = _first_existing_col(market_df, ("$limit_up", "limit_up"))
    limit_down_col = _first_existing_col(market_df, ("$limit_down", "limit_down"))

    if cfg.get("filter_suspend", True):
        if cfg.get("volume_zero_means_suspended", True) and volume_col:
            mask &= market_df[volume_col].fillna(0) > 0
        if cfg.get("amount_zero_means_suspended", True) and amount_col:
            mask &= market_df[amount_col].fillna(0) > 0

    if cfg.get("filter_limit", True):
        if close_col and limit_up_col:
            close = market_df[close_col]
            limit_up = market_df[limit_up_col]
            has_limit_up = limit_up.notna() & (limit_up > 0)
            mask &= ~(has_limit_up & (close >= limit_up * float(cfg["limit_up_tolerance"])))
        else:
            logger.warning("tradability: limit-up filter skipped; missing close/limit_up")

        if close_col and limit_down_col:
            close = market_df[close_col]
            limit_down = market_df[limit_down_col]
            has_limit_down = limit_down.notna() & (limit_down > 0)
            mask &= ~(has_limit_down & (close <= limit_down * float(cfg["limit_down_tolerance"])))
        else:
            logger.warning("tradability: limit-down filter skipped; missing close/limit_down")

    if cfg.get("filter_newly_listed", True):
        min_days = int(cfg.get("min_listing_days", 60))
        if min_days > 0:
            times, symbols = _time_symbol_index(market_df.index)
            first_seen = pd.Series(times, index=market_df.index).groupby(symbols).transform("min")
            days_since_listing = (times - pd.DatetimeIndex(first_seen)).days
            mask &= days_since_listing >= min_days

    if stock_status is not None and not stock_status.empty:
        status = stock_status.reindex(market_df.index)
        if cfg.get("filter_st", True) and "is_st" in status.columns:
            mask &= ~status["is_st"].fillna(False).astype(bool)
        if cfg.get("filter_suspend", True) and "is_suspended" in status.columns:
            mask &= ~status["is_suspended"].fillna(False).astype(bool)
    elif cfg.get("filter_st", True):
        logger.info("tradability: ST filter requested but no stock_status provided")

    return mask.fillna(False).astype(bool)


def load_universe_mask(
    universe: str,
    target_index: pd.MultiIndex,
    *,
    qlib_dir: str | Path = "~/.qlib/qlib_data/cn_data_1d",
) -> pd.Series:
    """Load a Qlib instruments file into a boolean mask aligned to *target_index*.

    ``all`` and ``all_tradable`` return all-True masks. Other universe names
    resolve to ``{qlib_dir}/instruments/{universe}.txt`` where each line is
    ``symbol<TAB>start<TAB>end``.
    """
    if universe in {"all", "all_tradable", ""}:
        return pd.Series(True, index=target_index, name=f"universe_{universe or 'all'}")

    if not isinstance(target_index, pd.MultiIndex):
        raise ValueError("target_index must be MultiIndex(datetime, instrument)")

    inst_path = Path(qlib_dir).expanduser() / "instruments" / f"{universe}.txt"
    if not inst_path.exists():
        raise FileNotFoundError(f"universe instruments file not found: {inst_path}")

    intervals: dict[str, list[tuple[pd.Timestamp, pd.Timestamp]]] = {}
    for line in inst_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        sym, start, end = parts[:3]
        intervals.setdefault(sym, []).append((pd.Timestamp(start), pd.Timestamp(end)))

    times, symbols = _time_symbol_index(target_index)
    out = np.zeros(len(target_index), dtype=bool)
    positions_by_symbol = pd.Series(np.arange(len(target_index)), index=symbols).groupby(level=0).agg(list)

    for sym, spans in intervals.items():
        if sym not in positions_by_symbol.index:
            continue
        pos = np.asarray(positions_by_symbol.loc[sym], dtype=int)
        sym_times = times.take(pos)
        keep = np.zeros(len(pos), dtype=bool)
        for start, end in spans:
            keep |= (sym_times >= start) & (sym_times <= end)
        out[pos] = keep

    return pd.Series(out, index=target_index, name=f"universe_{universe}")


def combine_masks(*masks: pd.Series, index: pd.MultiIndex | None = None) -> pd.Series:
    """AND boolean masks together, aligning missing entries to ``False``."""
    if not masks:
        if index is None:
            raise ValueError("combine_masks requires at least one mask or index")
        return pd.Series(True, index=index)
    base_index = index if index is not None else masks[0].index
    result = pd.Series(True, index=base_index)
    for mask in masks:
        result &= mask.reindex(base_index, fill_value=False).astype(bool)
    return result.astype(bool)

