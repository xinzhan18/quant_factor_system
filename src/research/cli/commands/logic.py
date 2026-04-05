"""CLI command: logic — manage market logic hypotheses."""

from __future__ import annotations

import argparse
import logging

from research.storage.paths import StoragePaths
from research.storage.yaml_io import load_yaml

logger = logging.getLogger(__name__)


def cmd_logic(args: argparse.Namespace) -> None:
    paths = StoragePaths()

    if args.logic_action == "list":
        registry = load_yaml(paths.logic_registry_file)
        logics = registry.get("logics", [])
        print(f"Logic Registry: {len(logics)} logics")
        for lg in logics:
            lid = lg.get("logic_id", "?")
            name = lg.get("name", "?")
            status = lg.get("status", "?")
            print(f"  {lid}: {name} [{status}]")
        if not logics:
            print("  (empty — use /factor-logic to create)")

    elif args.logic_action == "schedule":
        snap_dir = paths.logic_dir / "snapshots"
        latest = snap_dir / "latest_schedule_snapshot.yaml"
        if latest.exists():
            schedule = load_yaml(latest)
            active = schedule.get("schedule_snapshot", {}).get("active_pool", [])
            print(f"Active pool: {len(active)} logics")
            for entry in active:
                print(f"  {entry.get('logic_id')}: quota={entry.get('candidate_quota', '?')}")
        else:
            print("No schedule snapshot found. Run /factor-logic schedule first.")
