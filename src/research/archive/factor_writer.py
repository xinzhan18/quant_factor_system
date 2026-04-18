"""Factor writer — allocate ``F{id}`` and persist ``vault/factors/F{id}.yaml``.

Allocation rule:

* F{id} is monotonically increasing. The next id is ``max(existing) + 1``.
* Existing file detection scans ``vault/factors/F*.yaml`` — ids never
  reused even after retirement.
* The write is atomic (temp + replace) via ``yaml_io.save_yaml``.

The factor.yaml frontmatter schema:

.. code-block:: yaml

    factor_id: F020
    name: triple_product_80d_pb
    family_tag: fundamental_price_divergence
    source_type: dsl            # or python
    expression: "Mul(Corr(...), ...)"  # dsl only
    python_path: F020_triple_product_80d_pb.py  # python only
    admitted_at: 2026-04-12T10:30:00Z
    admitted_in_batch: batch_103
    status: active
    signal_ref: batches/batch_103/signals/C001.parquet
    direction: fundamental_price_divergence
    mechanism: "..."
    validation_metrics:
      ic_mean: 0.016
      ic_ir: 0.338
      ...
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from research.storage.yaml_io import save_yaml

# First id in a fresh vault
FIRST_FACTOR_ID = 1
_FACTOR_FILE_RE = re.compile(r"^F(\d+)\.yaml$")


class FactorAllocationError(RuntimeError):
    """Raised when a monotonic allocation invariant is violated."""


@dataclass
class AllocatedFactor:
    """The output of :func:`allocate_and_write_factor`."""

    factor_id: str
    yaml_path: Path
    record: dict[str, Any]


def scan_existing_factor_ids(factors_dir: str | Path) -> set[int]:
    """Return the numeric ids (``int(20)`` for ``F020.yaml``) currently on disk.

    Ignores any file that doesn't match ``F\\d+\\.yaml`` — shields the
    allocator from editor swap files, macOS ``.DS_Store``, etc.
    """
    p = Path(factors_dir)
    if not p.exists():
        return set()
    ids: set[int] = set()
    for f in p.iterdir():
        m = _FACTOR_FILE_RE.match(f.name)
        if m:
            ids.add(int(m.group(1)))
    return ids


def allocate_next_factor_id(factors_dir: str | Path) -> str:
    """Return the next monotonically-increasing ``F{id}`` string.

    Empty vault → ``F020`` (first id in the new system).
    Otherwise → ``F{max(existing)+1}``.
    Zero-padded to 3 digits.
    """
    existing = scan_existing_factor_ids(factors_dir)
    if not existing:
        return f"F{FIRST_FACTOR_ID:03d}"
    next_id = max(existing) + 1
    return f"F{next_id:03d}"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_factor_record(
    factor_id: str,
    admit_entry: dict[str, Any],
    manifest_entry: dict[str, Any],
    batch_id: str,
    direction: str,
) -> dict[str, Any]:
    """Compose the ``factor.yaml`` frontmatter dict from inputs.

    Parameters
    ----------
    factor_id
        The allocated F{id} string.
    admit_entry
        The candidate dict from ``result.yaml["candidates"]`` (has all
        the metric fields the record needs).
    manifest_entry
        The candidate dict from ``manifest.yaml["candidates"]`` (has
        the expression / python path that the result dict may not).
    batch_id, direction
        Context keys.
    """
    source_type = admit_entry.get("source_type") or manifest_entry.get("source_type", "dsl")
    record: dict[str, Any] = {
        "factor_id": factor_id,
        "name": admit_entry.get("name") or manifest_entry.get("name") or factor_id,
        "family_tag": direction,
        "source_type": source_type,
        "admitted_at": _now_iso(),
        "admitted_in_batch": batch_id,
        "status": "active",
        "signal_ref": f"batches/{batch_id}/signals/{admit_entry.get('candidate_id', '?')}.parquet",
        "direction": direction,
    }

    if source_type == "dsl":
        record["expression"] = manifest_entry.get(
            "expression", admit_entry.get("expression")
        )
        if manifest_entry.get("canonical"):
            record["canonical"] = manifest_entry["canonical"]
    elif source_type == "python":
        record["python_path"] = manifest_entry.get("path") or admit_entry.get("path")

    # Attach a compact validation snapshot for Phase 4 reporting
    ic = admit_entry.get("ic") or {}
    val = ic.get("validation") or {}
    q_val = (admit_entry.get("quintile") or {}).get("validation") or {}
    record["validation_metrics"] = {
        "ic_mean": val.get("ic_mean"),
        "ic_ir": val.get("ic_ir"),
        "ic_win_rate": val.get("ic_win_rate"),
        "monotonicity": q_val.get("monotonicity"),
        "long_short_mean": q_val.get("ls_mean"),
    }
    record["risk_metrics"] = {
        "style_r_squared": (admit_entry.get("barra") or {}).get("style_r_squared"),
        "alpha_survival_ratio": (admit_entry.get("barra") or {}).get(
            "alpha_survival_ratio"
        ),
    }

    return record


def write_factor_yaml(
    factors_dir: str | Path,
    record: dict[str, Any],
) -> Path:
    """Write *record* to ``factors/{factor_id}.yaml`` atomically.

    Raises :class:`FactorAllocationError` if the file already exists —
    this is the Q39 guard against accidental overwrite of an already-
    admitted factor.
    """
    fid = record["factor_id"]
    path = Path(factors_dir) / f"{fid}.yaml"
    if path.exists():
        raise FactorAllocationError(
            f"{fid} already exists at {path} — allocate_next_factor_id "
            "must monotonically skip existing ids"
        )
    save_yaml(path, record)
    return path


def allocate_and_write_factor(
    factors_dir: str | Path,
    admit_entry: dict[str, Any],
    manifest_entry: dict[str, Any],
    batch_id: str,
    direction: str,
) -> AllocatedFactor:
    """Allocate a fresh id and write the factor.yaml in one call.

    This is the entry point used by ``phases/phase4_archive.py``.
    """
    factor_id = allocate_next_factor_id(factors_dir)
    record = build_factor_record(
        factor_id=factor_id,
        admit_entry=admit_entry,
        manifest_entry=manifest_entry,
        batch_id=batch_id,
        direction=direction,
    )
    yaml_path = write_factor_yaml(factors_dir, record)
    return AllocatedFactor(
        factor_id=factor_id, yaml_path=yaml_path, record=record
    )
