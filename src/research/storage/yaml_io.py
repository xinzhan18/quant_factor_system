"""Atomic YAML I/O for the research storage tree.

Two load variants exist by design:

* :func:`load_yaml` — safe, for config/state/manifest files. Rejects arbitrary
  Python objects embedded via ``!!python/object``. This is what you want for
  90% of reads.
* :func:`load_yaml_unsafe` — trusted, for ``result.yaml`` which may contain
  pandas DataFrames / numpy arrays persisted by the compute layer. Only call
  this on files we wrote ourselves.

Writes always go through :func:`save_yaml` which uses temp-file + ``os.replace``
for atomicity so a crash mid-write cannot leave a half-written file.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any

import yaml


def load_yaml_any(path: str | Path) -> Any:
    """Safe-load a YAML file, returning an empty dict if missing/empty."""
    p = Path(path)
    if not p.exists():
        return {}
    text = p.read_text(encoding="utf-8")
    if not text.strip():
        return {}
    data = yaml.safe_load(text)
    if data is None:
        return {}
    return data


def load_yaml(path: str | Path) -> dict[str, Any]:
    """Safe-load a YAML file, coercing non-mapping content into ``{"_raw": ...}``."""
    data = load_yaml_any(path)
    if not isinstance(data, dict):
        return {"_raw": data}
    return data


def load_yaml_unsafe(path: str | Path) -> dict[str, Any]:
    """Unsafe-load a YAML file (allows pickled Python objects).

    Use ONLY for files we wrote ourselves — primarily ``result.yaml`` which
    embeds pandas DataFrames from the compute layer. Never call this on
    config / state / manifest / judge files.

    Returns empty dict if the file is missing or empty. Coerces non-mapping
    content into ``{"_raw": ...}``.
    """
    p = Path(path)
    if not p.exists():
        return {}
    text = p.read_text(encoding="utf-8")
    if not text.strip():
        return {}
    data = yaml.unsafe_load(text)
    if data is None:
        return {}
    if not isinstance(data, dict):
        return {"_raw": data}
    return data


def save_yaml(path: str | Path, data: Any) -> None:
    """Atomically write *data* as YAML.

    Writes to a temporary file in the same directory, then ``os.replace``'s it
    onto the target so a crash mid-write cannot leave a half-written file.
    Parent directories are created on demand.

    Uses ``default_flow_style=False`` (block style), ``allow_unicode=True``
    (Chinese in notes), and ``sort_keys=False`` (preserve insertion order so
    schemas stay human-readable).
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    content = yaml.dump(
        data,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    )

    fd, tmp_path = tempfile.mkstemp(
        dir=str(p.parent), suffix=".yaml.tmp", prefix=".tmp_"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp_path, str(p))
    except BaseException:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
