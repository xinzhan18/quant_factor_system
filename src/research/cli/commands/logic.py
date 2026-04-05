"""CLI command: logic — manage market logic hypotheses (outer loop).

Sub-actions:
  list      — show logic cards with optional status filter
  schedule  — compute priority scores and exploration contract
  propose   — create new logic proposals (reads YAML from stdin)
  review    — review a specific logic card's state and history
"""

from __future__ import annotations

import sys

import yaml

from mining.config import MiningConfig
from mining.registry import FactorLibrary


def cmd_logic(args):
    """Dispatch logic sub-actions."""
    from mining.logic import MarketLogicLibrary, Scheduler

    config = MiningConfig()
    lib = MarketLogicLibrary(config.logic_dir)

    action = args.logic_action

    if action == "list":
        _logic_list(lib, status_filter=getattr(args, "status", None))

    elif action == "schedule":
        _logic_schedule(lib, config)

    elif action == "propose":
        _logic_propose(lib)

    elif action == "review":
        _logic_review(lib, logic_id=getattr(args, "logic_id", None))


def _logic_list(lib, status_filter=None):
    """List all logics, optionally filtered by status."""
    logics = lib.list_logics(status=status_filter)
    if not logics:
        print("No logics found.")
        return
    for logic in logics:
        s = logic.get("stats", {})
        print(f"  {logic['id']} [{logic['status']}] {logic['name']} "
              f"(cat={logic['category']}, gen={s.get('factors_generated', 0)}, "
              f"adm={s.get('factors_admitted', 0)})")


def _logic_schedule(lib, config):
    """Compute priority scores and show exploration contract."""
    sched = Scheduler()
    logics = lib.list_logics(status="active")
    if not logics:
        print("No active logics.")
        return

    coverage = lib.coverage_map()
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
        print("\n  All scores non-positive — recommend running /logic propose (outer loop)")


def _logic_propose(lib):
    """Create a new logic proposal from stdin YAML."""
    logic_yaml = yaml.safe_load(sys.stdin)
    if not isinstance(logic_yaml, dict):
        print(f"ERROR: expected YAML dict from stdin, got: {type(logic_yaml)}")
        sys.exit(1)
    required = ["name", "category", "hypothesis"]
    missing = [k for k in required if k not in logic_yaml]
    if missing:
        print(f"ERROR: missing required fields: {missing}")
        sys.exit(1)
    record = lib.create(**logic_yaml)
    print(f"Created logic: {record['id']}")


def _logic_review(lib, logic_id=None):
    """Review a specific logic card or all logics."""
    if logic_id:
        logic = lib.get(logic_id)
        if not logic:
            print(f"Logic {logic_id} not found.")
            sys.exit(1)
        _print_logic_detail(logic)
    else:
        logics = lib.list_logics()
        for logic in logics:
            _print_logic_detail(logic)
            print("---")


def _print_logic_detail(logic):
    """Print detailed logic card info."""
    print(f"Logic: {logic['id']} — {logic['name']}")
    print(f"  Category: {logic.get('category', 'N/A')}")
    print(f"  Status:   {logic.get('status', 'N/A')}")
    s = logic.get("stats", {})
    print(f"  Stats:    generated={s.get('factors_generated', 0)}, "
          f"admitted={s.get('factors_admitted', 0)}, "
          f"best_ic={s.get('best_ic', 'N/A')}")
    hypothesis = logic.get("hypothesis", {})
    if isinstance(hypothesis, dict):
        print(f"  Thesis:   {hypothesis.get('condition', 'N/A')}")
    elif isinstance(hypothesis, str):
        print(f"  Thesis:   {hypothesis}")
