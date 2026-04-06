"""Generic typed YAML load/save with atomic writes.

All storage modules use these two helpers so that write-corruption risk is
minimised (write to temp, then ``os.replace``) and load semantics are
consistent (``yaml.safe_load`` everywhere).
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any

import yaml


def load_yaml(path: str | Path) -> dict[str, Any]:
    """Load a YAML file, returning an empty dict if the file is missing or empty."""
    p = Path(path)
    if not p.exists():
        return {}
    text = p.read_text(encoding="utf-8")
    if not text.strip():
        return {}
    data = yaml.safe_load(text)
    if data is None:
        return {}
    if not isinstance(data, dict):
        return {"_raw": data}
    return data


def save_yaml(path: str | Path, data: Any) -> None:
    """Atomically write *data* as YAML.

    Writes to a temporary file in the same directory and then does an
    atomic ``os.replace`` so that a crash mid-write never leaves a
    half-written file.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    content = yaml.dump(
        data,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    )

    # Write to temp file in the same directory for atomic replace.
    fd, tmp_path = tempfile.mkstemp(
        dir=str(p.parent), suffix=".yaml.tmp", prefix=".tmp_"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp_path, str(p))
    except BaseException:
        # Clean up temp file on failure.
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
