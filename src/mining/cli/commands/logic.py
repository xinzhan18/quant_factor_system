"""CLI command: manage and inspect market logics."""

from __future__ import annotations

import sys

import yaml

from mining.config import MiningConfig
from mining.library import FactorLibrary


def cmd_logic(args):
    """Manage and inspect market logics."""
    from mining.logic_library import MarketLogicLibrary
    from mining.scheduler import Scheduler

    config = MiningConfig()
    lib = MarketLogicLibrary(config.logic_dir)

    if args.logic_action == "list":
        status_filter = getattr(args, "status", None)
        logics = lib.list_logics(status=status_filter)
        if not logics:
            print("No logics found.")
            return
        for l in logics:
            s = l.get("stats", {})
            print(f"  {l['id']} [{l['status']}] {l['name']} "
                  f"(cat={l['category']}, gen={s.get('factors_generated', 0)}, "
                  f"adm={s.get('factors_admitted', 0)})")

    elif args.logic_action == "coverage":
        coverage = lib.coverage_map()
        if not coverage:
            print("No taxonomy loaded.")
            return
        for cat, count in sorted(coverage.items()):
            bar = "#" * count
            print(f"  {cat:20s} {count:3d} {bar}")

    elif args.logic_action == "schedule":
        sched = Scheduler()
        logics = lib.list_logics(status="active")
        if not logics:
            print("No active logics.")
            return
        coverage = lib.coverage_map()
        # Compute avg IC from library
        flib = FactorLibrary(config)
        factors = flib.list_factors()
        avg_ic = sum(abs(f.get("ic_mean", 0)) for f in factors) / max(len(factors), 1)
        scores = sched.score_logics(logics, coverage, avg_ic)
        print("Logic priority scores:")
        for lid, score in scores:
            logic = lib.get(lid)
            name = logic["name"] if logic else "?"
            print(f"  {lid} {name:30s} score={score:+.1f}")
        if sched.should_trigger_outer_loop(logics, coverage, avg_ic):
            print("\n  All scores non-positive — recommend running /logic new (outer loop)")

    elif args.logic_action == "create":
        logic_yaml = yaml.safe_load(sys.stdin)
        if not isinstance(logic_yaml, dict):
            print("ERROR: expected YAML dict from stdin, got:", type(logic_yaml))
            sys.exit(1)
        required = ["name", "category", "hypothesis"]
        missing = [k for k in required if k not in logic_yaml]
        if missing:
            print(f"ERROR: missing required fields: {missing}")
            print(f"Required: {required}")
            sys.exit(1)
        record = lib.create(**logic_yaml)
        print(f"Created logic: {record['id']}")
