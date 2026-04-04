"""CLI command: show Experience Memory status."""

from __future__ import annotations

from mining.application.context_service import compose_search_context
from mining.config import MiningConfig


def cmd_memory(args):
    """Show Experience Memory status."""
    config = MiningConfig(memory_dir=args.memory_dir)
    ctx = compose_search_context(config)
    print(ctx)
