"""BacktestConfig — frozen dataclasses + 3-layer YAML merge + validate."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date as Date
from pathlib import Path
from typing import Any, Literal

from research.storage.paths import StoragePaths
from research.storage.yaml_io import load_yaml


@dataclass(frozen=True)
class RebalanceConfig:
    freq_days: int
    anchor: str  # 'monday' | 'first_trade_day' | YYYY-MM-DD


@dataclass(frozen=True)
class PortfolioConfig:
    holdings_n: int
    weight_scheme: Literal["equal", "rank", "ic_weighted"]
    max_single_weight: float


@dataclass(frozen=True)
class MatchingConfig:
    match_price: Literal["open", "close"]
    price_adjust: Literal["hfq", "qfq", "none"]


@dataclass(frozen=True)
class StampScheduleEntry:
    from_date: Date
    to_date: Date
    sell_bps: float


@dataclass(frozen=True)
class CostConfig:
    stamp_schedule: tuple[StampScheduleEntry, ...]
    commission_bps: float
    slippage_bps: float
    min_commission_cny: float

    def stamp_bps_at(self, dt: Date) -> float:
        for e in self.stamp_schedule:
            if e.from_date <= dt <= e.to_date:
                return e.sell_bps
        raise ValueError(f"no stamp schedule covers {dt}")


@dataclass(frozen=True)
class CapitalConfig:
    allow_intraday_netting: bool


@dataclass(frozen=True)
class FilterConfig:
    block_st: bool
    block_suspended: bool
    block_limit_up_at_buy: bool
    block_limit_down_at_sell: bool
    cooldown_days_after_unsuspend: int
    newly_listed_days: int
    stale_position_days_max: int


@dataclass(frozen=True)
class PeriodsConfig:
    train: tuple[Date, Date]
    val: tuple[Date, Date]
    holdout: tuple[Date, Date]
    run: tuple[str, ...]


@dataclass(frozen=True)
class BenchmarkConfig:
    kind: Literal["csi1000_total_return", "csi1000_equal_weight_tradable"]


@dataclass(frozen=True)
class OutputConfig:
    save_trades: bool
    save_positions: bool
    figs: tuple[str, ...]


@dataclass(frozen=True)
class BacktestConfig:
    universe: str
    initial_capital: float
    signal_recompute: bool
    rebalance: RebalanceConfig
    portfolio: PortfolioConfig
    matching: MatchingConfig
    cost: CostConfig
    capital: CapitalConfig
    filters: FilterConfig
    periods: PeriodsConfig
    benchmark: BenchmarkConfig
    output: OutputConfig

    def validate(self) -> None:
        if self.rebalance.freq_days < 2:
            raise ValueError(
                f"rebalance.freq_days must be >= 2 (T+1 enforcement); got {self.rebalance.freq_days}"
            )
        valid_run = {"train", "val", "holdout"}
        if not set(self.periods.run).issubset(valid_run):
            raise ValueError(
                f"periods.run must be subset of {valid_run}; got {self.periods.run}"
            )
        if self.initial_capital <= 0:
            raise ValueError("initial_capital must be > 0")


def _deep_merge(base: dict, overlay: dict) -> dict:
    """Recursively merge overlay into base; overlay wins."""
    out = dict(base)
    for k, v in overlay.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def _per_factor_path(factor_id: str) -> Path:
    return StoragePaths().factors_dir / f"{factor_id}.backtest.yaml"


def _build_from_dict(d: dict) -> BacktestConfig:
    stamp = tuple(
        StampScheduleEntry(
            from_date=e["from"], to_date=e["to"], sell_bps=float(e["sell_bps"])
        )
        for e in d["cost"]["stamp_schedule"]
    )
    return BacktestConfig(
        universe=d["universe"],
        initial_capital=float(d["initial_capital"]),
        signal_recompute=bool(d["signal_recompute"]),
        rebalance=RebalanceConfig(**d["rebalance"]),
        portfolio=PortfolioConfig(**d["portfolio"]),
        matching=MatchingConfig(**d["matching"]),
        cost=CostConfig(
            stamp_schedule=stamp,
            commission_bps=float(d["cost"]["commission_bps"]),
            slippage_bps=float(d["cost"]["slippage_bps"]),
            min_commission_cny=float(d["cost"]["min_commission_cny"]),
        ),
        capital=CapitalConfig(**d["capital"]),
        filters=FilterConfig(**d["filters"]),
        periods=PeriodsConfig(
            train=tuple(d["periods"]["train"]),
            val=tuple(d["periods"]["val"]),
            holdout=tuple(d["periods"]["holdout"]),
            run=tuple(d["periods"]["run"]),
        ),
        benchmark=BenchmarkConfig(**d["benchmark"]),
        output=OutputConfig(
            save_trades=d["output"]["save_trades"],
            save_positions=d["output"]["save_positions"],
            figs=tuple(d["output"]["figs"]),
        ),
    )


def load_default_config(
    factor_id: str,
    cli_overrides: dict | None = None,
    config_path: str | Path = "storage/config.yaml",
) -> BacktestConfig:
    base = load_yaml(config_path)["backtest"]["defaults"]
    pf_path = _per_factor_path(factor_id)
    pf = load_yaml(pf_path) if pf_path.exists() else {}
    cli = cli_overrides or {}
    merged = _deep_merge(_deep_merge(base, pf), cli)
    cfg = _build_from_dict(merged)
    cfg.validate()
    return cfg
