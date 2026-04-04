"""CLI package for factor mining."""

from .main import main

# Convenience re-exports of command functions.
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

__all__ = [
    "main",
    "cmd_forbidden", "cmd_audit", "cmd_logic", "cmd_sync",
    "cmd_evaluate", "cmd_batch", "cmd_probe", "cmd_library",
    "cmd_memory", "cmd_retire",
]
