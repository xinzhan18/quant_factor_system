"""Shared YAML and timestamp helpers for the logic sub-package."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import yaml

# Canonical timestamp format used throughout the logic module
_TS_FMT = "%Y-%m-%d %H:%M:%S"


def now_ts() -> str:
    """Return the current time as a canonical timestamp string."""
    return datetime.now().strftime(_TS_FMT)


def dump_yaml(path: Path, data: Dict[str, Any]) -> None:
    """Write *data* as YAML to *path* with standard formatting."""
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(
            data,
            f,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )
