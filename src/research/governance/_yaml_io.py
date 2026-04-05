"""Shared atomic YAML I/O helpers for the governance module."""

from __future__ import annotations

import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List

import yaml


def atomic_yaml_write(path: Path, data: Any) -> None:
    """Write *data* to *path* via temp-file + os.replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            yaml.safe_dump(
                data,
                fh,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )
        os.replace(tmp, str(path))
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def safe_yaml_load_list(path: Path) -> List[dict]:
    """Load a YAML file that should contain a list; return [] on absence/empty."""
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return []
    data = yaml.safe_load(text)
    if data is None:
        return []
    if not isinstance(data, list):
        return []
    return data


def now_iso() -> str:
    """UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()
