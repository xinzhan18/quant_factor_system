#!/usr/bin/env python3
"""Migrate existing factor records to canonical schema.

Default mode is dry-run (report only). Explicit --apply to mutate.

Changes per factor:
- Normalize metric aliases (ic_mean_is -> ic_mean, etc.)
- Fill source=dsl if missing
- Fill status=legacy if missing (NOT active -- deliberate)
- Fill evaluation_version=v1 (all existing factors)
- Infer long_leg from ic_mean sign
- Zero-pad IDs (9 -> 009)
- Verify filename matches ID

Then rebuilds library.yaml index from detail files.

Usage:
    PYTHONPATH=src python3 scripts/migrate_schema.py            # dry-run (default)
    PYTHONPATH=src python3 scripts/migrate_schema.py --apply    # mutate files
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import yaml
from mining.domain.schema import FactorRecord, normalize_metrics


def migrate_factor(data: dict, path: Path) -> tuple[dict, list[str]]:
    """Normalize a single factor detail record. Returns (data, changes)."""
    changes = []

    # 1. Zero-pad ID
    raw_id = data.get("id", "")
    padded_id = f"{int(raw_id):03d}"
    if str(raw_id) != padded_id:
        data["id"] = padded_id
        changes.append(f"id: {raw_id} -> {padded_id}")

    # 2. Normalize metrics
    raw_metrics = data.get("metrics", {})
    norm_metrics = normalize_metrics(raw_metrics)
    if norm_metrics != raw_metrics:
        changes.append("metrics aliases resolved")
        data["metrics"] = norm_metrics

    # 3. Fill missing source
    if "source" not in data:
        data["source"] = "dsl"
        changes.append("added source=dsl")

    # 4. Fill missing status -- LEGACY, not active
    if "status" not in data:
        data["status"] = "legacy"
        changes.append("added status=legacy")

    # 5. All existing factors are v1
    if "evaluation_version" not in data:
        data["evaluation_version"] = "v1"
        changes.append("added evaluation_version=v1")

    # 6. Infer long_leg
    if "long_leg" not in data:
        ic = data["metrics"].get("ic_mean")
        if ic is not None:
            data["long_leg"] = "high" if ic >= 0 else "low"
            changes.append(f"inferred long_leg={data['long_leg']}")

    # 7. Verify filename matches ID
    expected_name = f"factor_{data['id']}.yaml"
    if path.name != expected_name:
        changes.append(f"WARNING: filename {path.name} != expected {expected_name}")

    return data, changes


def rebuild_index(factors_dir: Path, index_path: Path, dry_run: bool) -> None:
    """Rebuild library.yaml index from detail files (detail = truth source)."""
    existing = {}
    if index_path.exists():
        with open(index_path, "r", encoding="utf-8") as f:
            existing = yaml.safe_load(f) or {}

    entries = []
    for p in sorted(factors_dir.glob("factor_*.yaml")):
        # Skip history directory
        if "history" in str(p):
            continue
        with open(p, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        rec = FactorRecord.for_migration(
            id=f"{int(data['id']):03d}",
            name=data["name"],
            expression=data.get("expression"),
            category=data.get("category", "other"),
            batch=data.get("batch", "unknown"),
            source=data.get("source", "dsl"),
            status=data.get("status", "legacy"),
            evaluation_version=data.get("evaluation_version", "v1"),
            long_leg=data.get("long_leg"),
            metrics=data.get("metrics", {}),
        )
        entries.append(rec.to_index_dict())

    index_data = {
        "thresholds": existing.get("thresholds", {}),
        "factors": entries,
    }

    if dry_run:
        statuses = {}
        for e in entries:
            s = e.get("status", "?")
            statuses[s] = statuses.get(s, 0) + 1
        print(f"\nIndex would have {len(entries)} entries: {statuses}")
    else:
        with open(index_path, "w", encoding="utf-8") as f:
            yaml.dump(index_data, f, default_flow_style=False,
                      allow_unicode=True, sort_keys=False)
        print(f"\nRebuilt {index_path}: {len(entries)} factors")


def main():
    parser = argparse.ArgumentParser(description="Migrate factor records to canonical schema")
    parser.add_argument("--apply", action="store_true",
                        help="Apply changes (default is dry-run)")
    parser.add_argument("--library-dir", default="storage/registry")
    args = parser.parse_args()
    dry_run = not args.apply

    if dry_run:
        print("=== DRY RUN (no files will be modified) ===\n")
    else:
        print("=== APPLYING MIGRATION ===\n")

    lib_dir = Path(args.library_dir)
    factors_dir = lib_dir / "factors"
    index_path = lib_dir / "library.yaml"

    if not factors_dir.exists():
        print(f"ERROR: {factors_dir} does not exist")
        sys.exit(1)

    factor_files = sorted(f for f in factors_dir.glob("factor_*.yaml")
                          if "history" not in str(f))
    print(f"Found {len(factor_files)} factor files\n")

    total_changes = 0
    for p in factor_files:
        with open(p, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        data, changes = migrate_factor(data, p)
        if changes:
            total_changes += len(changes)
            print(f"  {p.name}: {', '.join(changes)}")
            if not dry_run:
                # Rename file if filename doesn't match padded ID
                expected_name = f"factor_{data['id']}.yaml"
                if p.name != expected_name:
                    new_path = p.parent / expected_name
                    p.rename(new_path)
                    print(f"    RENAMED {p.name} -> {expected_name}")
                    p = new_path
                with open(p, "w", encoding="utf-8") as f:
                    yaml.dump(data, f, default_flow_style=False,
                              allow_unicode=True, sort_keys=False)

    print(f"\nTotal changes: {total_changes}")
    rebuild_index(factors_dir, index_path, dry_run)


if __name__ == "__main__":
    main()
