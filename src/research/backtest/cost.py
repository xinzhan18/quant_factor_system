"""CostModel — pure function compute_cost (commission + slippage + stamp)."""
from __future__ import annotations

from datetime import date
from typing import Literal

from research.backtest.config import CostConfig


def compute_cost(
    side: Literal["buy", "sell"],
    price: float,
    shares: int,
    dt: date,
    config: CostConfig,
) -> float:
    """Total cost in CNY for one fill.

    - Commission: ``commission_bps`` × notional, floored at ``min_commission_cny``.
    - Slippage: ``slippage_bps`` × notional.
    - Stamp tax: only on sells, looked up via ``config.stamp_bps_at(dt)``.
    """
    notional = price * shares
    commission = max(notional * config.commission_bps / 1e4, config.min_commission_cny)
    slippage = notional * config.slippage_bps / 1e4
    stamp = notional * config.stamp_bps_at(dt) / 1e4 if side == "sell" else 0.0
    return commission + slippage + stamp
