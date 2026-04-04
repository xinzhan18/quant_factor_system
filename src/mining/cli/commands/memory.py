"""CLI command: show Experience Memory status."""

from __future__ import annotations

from mining.config import MiningConfig
from mining.memory import ExperienceMemory


def cmd_memory(args):
    """Show Experience Memory status."""
    config = MiningConfig(memory_dir=args.memory_dir)
    mem = ExperienceMemory(config)
    ctx = mem.compose_search_context()
    print(ctx)
