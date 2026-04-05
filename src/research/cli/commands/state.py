"""CLI command: state — research state overview.

Reads research_state.yaml and prints a consolidated view of the
current research system status: active logics, active routes,
current focus, bottlenecks, and policy flags.
"""

from __future__ import annotations

from pathlib import Path

import yaml


STATE_PATH = Path("storage/state/research_state.yaml")


def cmd_state(args):
    """Show the current research state overview."""
    if not STATE_PATH.exists():
        print(f"Research state file not found: {STATE_PATH}")
        print("Hint: initialize with /logic schedule or /mine.")
        return

    with open(STATE_PATH) as f:
        state = yaml.safe_load(f)

    if not state:
        print("Research state is empty.")
        return

    rs = state.get("research_state", state)

    print("=== Research State ===\n")

    # Current batch
    batch = rs.get("current_batch", "N/A")
    print(f"Current batch: {batch}")

    # Active logics
    active_logics = rs.get("active_logic_ids", [])
    print(f"\nActive logics ({len(active_logics)}):")
    for lid in active_logics:
        print(f"  - {lid}")

    # Active routes
    active_routes = rs.get("active_route_ids", [])
    print(f"\nActive routes ({len(active_routes)}):")
    for rid in active_routes:
        print(f"  - {rid}")

    # Current focus
    focus = rs.get("current_focus", [])
    if focus:
        print("\nCurrent focus:")
        for item in focus:
            print(f"  - {item}")

    # Bottlenecks
    bottlenecks = rs.get("current_bottlenecks", [])
    if bottlenecks:
        print("\nBottlenecks:")
        for bn in bottlenecks:
            print(f"  - {bn}")

    # Policy flags
    flags = rs.get("policy_flags", {})
    if flags:
        print("\nPolicy flags:")
        for key, val in flags.items():
            print(f"  {key}: {val}")

    # Last updated
    updated = rs.get("last_updated_at", "N/A")
    print(f"\nLast updated: {updated}")
