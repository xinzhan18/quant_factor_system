"""CLI command: logic — manage market logic hypotheses."""

from __future__ import annotations

import argparse
import logging

from research.storage.paths import StoragePaths

logger = logging.getLogger(__name__)


def cmd_logic(args: argparse.Namespace) -> None:
    paths = StoragePaths()

    if args.logic_action == "list":
        from research.logic.cards import LogicCardStore

        store = LogicCardStore(paths.root)
        cards = store.list_cards()
        if hasattr(args, "status") and args.status:
            cards = [c for c in cards if c.status == args.status]
        label = f" [{args.status}]" if hasattr(args, "status") and args.status else ""
        print(f"Logic Cards{label}: {len(cards)} found")
        for card in cards:
            print(f"  {card.logic_id}: {card.name} [{card.status}] priority={card.priority}")
        if not cards:
            print("  (none — use /factor-logic to create)")

    elif args.logic_action == "schedule":
        from research.logic.cards import LogicCardStore
        from research.logic.scheduler import LogicScheduler

        store = LogicCardStore(paths.root)
        cards = store.list_cards()
        if not cards:
            print("No logic cards found. Use /factor-logic to create.")
            return

        scheduler = LogicScheduler()
        result = scheduler.generate_schedule(cards)

        print(f"Schedule generated at {result.generated_at}")
        print(f"\nActive pool ({len(result.active_pool)}):")
        for b in result.active_pool:
            print(f"  {b.logic_id}: score={b.score:.4f} quota={b.candidate_quota}")
        print(f"\nWarm pool ({len(result.warm_pool)}):")
        for b in result.warm_pool:
            print(f"  {b.logic_id}: score={b.score:.4f}")
        if result.parked_pool or result.blocked_pool:
            print(f"\nParked ({len(result.parked_pool)}), Blocked ({len(result.blocked_pool)})")
        if result.global_saturation_signal:
            print(f"\n** GLOBAL SATURATION: {result.global_saturation_signal['reason']}")
