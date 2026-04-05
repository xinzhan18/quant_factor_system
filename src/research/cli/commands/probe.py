"""CLI command: probe — lightweight IC check on train period only."""

from __future__ import annotations

import argparse
import logging

logger = logging.getLogger(__name__)


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("probe", help="Lightweight IC probe (train only)")
    p.add_argument("expression", help="Qlib DSL expression")
    p.add_argument("--universe", default="csi1000")
    p.add_argument("--start", default="2015-01-01")
    p.add_argument("--end", default="2021-12-31")
    p.set_defaults(func=cmd_probe)


def cmd_probe(args: argparse.Namespace) -> None:
    from research.compute.data_provider import DataProvider
    from research.compute.universe import UniverseManager
    from core.factor_stats import daily_cross_sectional_ic, ic_summary, multiindex_to_flat

    universe = UniverseManager(args.universe)
    provider = DataProvider(universe=universe)

    print(f"Probing: {args.expression}")
    print(f"Universe: {args.universe} | Period: {args.start} ~ {args.end}")

    factor_mi = provider.get_factor_values(args.expression, args.start, args.end)
    returns_mi = provider.get_returns(args.start, args.end, horizon=5)

    factor_flat = multiindex_to_flat(factor_mi)
    returns_flat = multiindex_to_flat(returns_mi)

    ic_series = daily_cross_sectional_ic(factor_flat, returns_flat)
    if ic_series.empty:
        print("FAIL: no valid IC computed")
        return

    stats = ic_summary(ic_series)
    ic_mean = stats.get("ic_mean", 0)
    ic_ir = stats.get("ic_ir", 0)
    win_rate = stats.get("ic_win_rate", 0)

    print(f"\nIC Mean: {ic_mean:.4f}")
    print(f"IC IR:   {ic_ir:.4f}")
    print(f"Win Rate:{win_rate:.2%}")

    if abs(ic_mean) < 0.005:
        print("\nVerdict: FAIL (no signal)")
    elif abs(ic_mean) < 0.01:
        print("\nVerdict: RESERVE (weak signal)")
    else:
        print("\nVerdict: PASS")
