"""Sync ``factors/F*.md`` frontmatter fields from ``factors/F*.yaml`` truth.

The YAML file is the authoritative source for a factor's lifecycle state
(``status: active | retired``). The Markdown file carries the human/LLM
report plus a frontmatter echo that Obsidian Bases can query.

Because the retire path historically only touches the YAML, the MD
frontmatter can drift (``decision: admit`` stays set but YAML moves to
``status: retired``). This module pushes the YAML-side lifecycle fields
into the MD frontmatter every refresh, so the ``factors.base`` view
always matches truth.

Synced keys:

* ``status`` (active | retired)
* ``duplicate_of`` (if present in YAML)

Existing keys are overwritten only when their value diverges from YAML;
unrelated keys are left untouched.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from research.storage.paths import StoragePaths
from research.storage.yaml_io import load_yaml

_FM_RE = re.compile(r"\A(---\s*\n)(?P<fm>.*?)(\n---\s*\n)", re.DOTALL)

_SYNCED_KEYS = ("status", "duplicate_of")


def _upsert_key(fm_text: str, key: str, value: Any) -> str:
    """Insert or update ``key: value`` inside the frontmatter text block."""
    # yaml.safe_dump a single-key dict to get properly quoted scalar
    rendered = yaml.safe_dump({key: value}, default_flow_style=False).strip()
    pattern = re.compile(rf"(?m)^{re.escape(key)}:.*$")
    if pattern.search(fm_text):
        return pattern.sub(rendered, fm_text, count=1)
    return fm_text.rstrip("\n") + "\n" + rendered


def sync_factor_md_frontmatter(yaml_path: Path, md_path: Path) -> bool:
    """Push YAML lifecycle fields into the matching MD frontmatter.

    Returns True if the MD file was modified, False if already in sync
    or if either file is missing.
    """
    if not yaml_path.exists() or not md_path.exists():
        return False
    yaml_fm = load_yaml(yaml_path) or {}
    if not isinstance(yaml_fm, dict):
        return False

    text = md_path.read_text(encoding="utf-8")
    m = _FM_RE.match(text)
    if m is None:
        return False
    fm_text = m.group("fm")

    new_fm_text = fm_text
    for key in _SYNCED_KEYS:
        if key not in yaml_fm:
            continue
        value = yaml_fm[key]
        new_fm_text = _upsert_key(new_fm_text, key, value)

    if new_fm_text == fm_text:
        return False

    new_text = m.group(1) + new_fm_text + m.group(3) + text[m.end():]
    md_path.write_text(new_text, encoding="utf-8")
    return True


def sync_all_factor_md(paths: StoragePaths) -> tuple[int, int]:
    """Run ``sync_factor_md_frontmatter`` across every ``F*.yaml`` in the vault.

    Returns ``(total_seen, total_touched)``.
    """
    total = 0
    touched = 0
    for yp in sorted(paths.factors_dir.glob("F*.yaml")):
        fid = yp.stem
        mp = paths.factor_md_file(fid)
        total += 1
        if sync_factor_md_frontmatter(yp, mp):
            touched += 1
    return total, touched
