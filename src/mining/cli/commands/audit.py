"""CLI command: audit direction states (read-only report)."""

from __future__ import annotations

from mining.config import MiningConfig
from mining.memory import ExperienceMemory


def cmd_audit(args):
    """Audit direction states (read-only report)."""
    config = MiningConfig()
    mem = ExperienceMemory(config)
    mismatches = mem.audit_directions(config.candidates_dir)
    if not mismatches:
        print("All direction states consistent.")
        return
    print(f"Found {len(mismatches)} mismatches:")
    for m in mismatches:
        print(f"  [{m['flag']}] {m['direction']}: "
              f"recorded={m['recorded_attempts']}, observed={m['observed_attempts']}, "
              f"status={m['status']}")
