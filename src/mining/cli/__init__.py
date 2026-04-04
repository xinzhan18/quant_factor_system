"""CLI package for factor mining."""

from .main import main

# Backward-compatible re-exports: tests and other code may import
# command functions and config directly from mining.cli.
# These will be removed in Task 1.3 when test imports are updated.
from .commands.forbidden import cmd_forbidden
from .commands.audit import cmd_audit
from .commands.logic import cmd_logic
from .commands.sync import cmd_sync
from .commands.evaluate import cmd_evaluate
from .commands.batch import cmd_batch
from .commands.probe import cmd_probe
from .commands.library import cmd_library
from .commands.memory import cmd_memory
from .commands.retire import cmd_retire
from mining.config import MiningConfig

__all__ = [
    "main",
    "cmd_forbidden", "cmd_audit", "cmd_logic", "cmd_sync",
    "cmd_evaluate", "cmd_batch", "cmd_probe", "cmd_library",
    "cmd_memory", "cmd_retire",
    "MiningConfig",
]
