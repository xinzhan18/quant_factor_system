"""Generic YAML I/O helpers with atomic writes.

* :func:`load_yaml` — safe load (no arbitrary Python objects).
* :func:`save_yaml` — atomic write via temp-file + ``os.replace``.
* :func:`load_yaml_unsafe` — for result files that may contain pandas objects.
"""

from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path
from typing import Any, List, Union

import yaml

logger = logging.getLogger(__name__)

PathLike = Union[str, Path]


def load_yaml(path: PathLike) -> dict:
    """Load a YAML file using ``yaml.safe_load``.

    Returns an empty dict when the file does not exist or is empty.
    """
    path = Path(path)
    if not path.exists():
        logger.debug("YAML file not found, returning empty dict: %s", path)
        return {}
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return {}
    data = yaml.safe_load(text)
    return data if isinstance(data, dict) else {}


def save_yaml(path: PathLike, data: Any) -> None:
    """Atomically write *data* as YAML.

    Writes to a temporary file in the same directory, then uses
    ``os.replace`` to swap it in — ensuring readers never see a
    partially-written file.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fd, tmp_path = tempfile.mkstemp(
        dir=str(path.parent),
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            yaml.safe_dump(
                data,
                fh,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )
        os.replace(tmp_path, str(path))
        logger.debug("Saved YAML: %s", path)
    except BaseException:
        # Clean up the temp file on any error.
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def load_yaml_unsafe(path: PathLike) -> dict:
    """Load a YAML file with ``yaml.unsafe_load``.

    Use this **only** for result files that may embed pandas objects or
    other non-standard Python types.  Returns an empty dict when the
    file does not exist or is empty.
    """
    path = Path(path)
    if not path.exists():
        logger.debug("YAML file not found, returning empty dict: %s", path)
        return {}
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return {}
    data = yaml.unsafe_load(text)
    return data if isinstance(data, dict) else {}


# ------------------------------------------------------------------
# Collection helpers shared across stores
# ------------------------------------------------------------------

def upsert_list(items: list, entry: dict, key: str) -> None:
    """Insert or replace *entry* in *items*, matching on *key*.

    Modifies *items* in place.
    """
    match_val = entry[key]
    for i, existing in enumerate(items):
        if existing.get(key) == match_val:
            items[i] = entry
            return
    items.append(entry)


def glob_stems(directory: Path, pattern: str = "*.yaml") -> List[str]:
    """Return sorted stem names for files matching *pattern* in *directory*.

    Returns an empty list when the directory does not exist.
    """
    if not directory.exists():
        return []
    return sorted(p.stem for p in directory.glob(pattern))
