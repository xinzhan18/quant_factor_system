"""CLI command: probe — lightweight IC check on train period only."""

from __future__ import annotations

import argparse
import logging

logger = logging.getLogger(__name__)


def cmd_probe(args: argparse.Namespace) -> None:
    from research.compute.data_provider import DataProvider
    from research.compute.universe import UniverseManager
    from research.execute.config import load_research_config
    from core.factor_stats import daily_cross_sectional_ic, ic_summary, multiindex_to_flat

    # Load from central config, allow CLI overrides
    config = load_research_config()
    universe_name = args.universe or config.get("universe", "csi1000")
    probe_cfg = config.get("probe", {})
    start = args.start or probe_cfg.get("start", "2019-01-01")
    end = args.end or probe_cfg.get("end", "2023-12-31")
    qlib_dir = getattr(args, "qlib_dir", None) or config.get("qlib_data_dir", "~/.qlib/qlib_data/cn_data_1d")

    universe = UniverseManager(universe_name)
    provider = DataProvider(universe=universe, qlib_dir=qlib_dir)

    print(f"Probing: {args.expression}")
    print(f"Universe: {universe_name} | Period: {start} ~ {end}")

    factor_mi = provider.get_factor_values(args.expression, start, end)
    returns_mi = provider.get_returns(start, end, horizon=5)

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
