#!/usr/bin/env python3
"""Migrate old library.yaml + per-factor YAMLs into the new registry format.

Reads:
    storage_archive/registry/library.yaml          (old index)
    storage_archive/registry/factors/factor_*.yaml  (old detail files)

Writes:
    storage/registry/factors/index.yaml             (new index)
    storage/registry/factors/factor_*.yaml          (new detail files, enriched)

Run from project root after archive_old_storage.py and init_new_storage.py:
    python scripts/migrate_factor_registry.py
"""

import sys
from pathlib import Path

import yaml


def _load_yaml(path: Path) -> dict:
    """Load YAML, using unsafe_load for old files that may contain pandas objects."""
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.unsafe_load(fh) or {}


def _dump_yaml(data: dict, path: Path) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        yaml.safe_dump(data, fh, sort_keys=False, allow_unicode=True)


def _migrate_factor(old_detail: dict) -> dict:
    """Convert an old factor detail dict to the new schema."""
    new = {}
    # Carry forward all existing fields
    for key in (
        "factor_id", "name", "expression", "source_type", "category",
        "status", "evaluation_version", "metrics", "admitted_at",
        "replaced_by", "replacement_history",
    ):
        if key in old_detail:
            new[key] = old_detail[key]

    # Add new required fields with defaults
    new.setdefault("source_type", "dsl")
    new.setdefault("logic_id", None)
    new.setdefault("route_id", None)
    new.setdefault("family_id", None)
    new.setdefault("lineage", {
        "parent_logic": None,
        "parent_routes": [],
        "parent_factors": [],
        "mutation_type": "legacy_migration",
    })
    new.setdefault("evaluation_profile", None)
    new.setdefault("style_summary", None)

    return new


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    archive = root / "storage_archive"
    new_storage = root / "storage"

    if not archive.exists():
        print("ERROR: storage_archive/ not found. Run archive_old_storage.py first.")
        sys.exit(1)

    if not new_storage.exists():
        print("ERROR: storage/ not found. Run init_new_storage.py first.")
        sys.exit(1)

    # Load old library index
    old_library_path = archive / "registry" / "library.yaml"
    if not old_library_path.exists():
        print(f"ERROR: {old_library_path} not found.")
        sys.exit(1)

    old_library = _load_yaml(old_library_path)
    old_factors_list = old_library.get("factors", [])
    print(f"Found {len(old_factors_list)} factors in old library index.")

    # Build new index and migrate detail files
    new_index_entries = []
    migrated = 0
    skipped = 0

    old_factors_dir = archive / "registry" / "factors"
    new_factors_dir = new_storage / "registry" / "factors"
    new_factors_dir.mkdir(parents=True, exist_ok=True)

    for entry in old_factors_list:
        fid = entry.get("factor_id", entry.get("id", ""))
        name = entry.get("name", "")

        # Try to load detail YAML (handles both zero-padded and bare IDs)
        detail_path = old_factors_dir / f"factor_{fid}.yaml"
        if not detail_path.exists():
            # Try with common zero-padding variants
            for pad in (fid.zfill(3), fid.zfill(2)):
                candidate = old_factors_dir / f"factor_{pad}.yaml"
                if candidate.exists():
                    detail_path = candidate
                    break

        if detail_path.exists():
            old_detail = _load_yaml(detail_path)
            new_detail = _migrate_factor(old_detail)
            out_path = new_factors_dir / detail_path.name
            _dump_yaml(new_detail, out_path)
            migrated += 1
        else:
            skipped += 1
            print(f"  SKIP: no detail file for {fid} ({name})")

        new_index_entries.append({
            "factor_id": fid,
            "name": name,
            "logic_id": None,
            "route_id": None,
            "category": entry.get("category", None),
        })

    # Write new index
    index_path = new_factors_dir / "index.yaml"
    _dump_yaml({"factors": new_index_entries}, index_path)

    print(f"Migration complete: {migrated} detail files migrated, {skipped} skipped.")
    print(f"New index written to {index_path}")


if __name__ == "__main__":
    main()
