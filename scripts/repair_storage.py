#!/usr/bin/env python3
"""One-time storage repair script.

Fixes:
1. batch_id: manifest → correct batch_id in research_result.yaml and judge_packet.yaml
2. Missing top-level batch_id in manifest.yaml (adds from batch_metadata or dir name)
3. Reports all changes made
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parent.parent
BATCHES_DIR = ROOT / "storage" / "batches"


def load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return {}
    # Result files may have unquoted special chars
    try:
        return yaml.safe_load(text) or {}
    except yaml.YAMLError:
        try:
            return yaml.unsafe_load(text) or {}
        except yaml.YAMLError:
            print(f"  WARNING: {path} has broken YAML, skipping")
            return {}


def save_yaml(path: Path, data: dict) -> None:
    content = yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)
    path.write_text(content, encoding="utf-8")


def fix_batch_id_in_file(path: Path, correct_id: str) -> list[str]:
    """Fix batch_id: manifest at top level."""
    fixes = []
    data = load_yaml(path)
    if not data:
        return fixes

    if data.get("batch_id") == "manifest":
        data["batch_id"] = correct_id
        save_yaml(path, data)
        fixes.append(f"  {path.name}: batch_id 'manifest' → '{correct_id}'")

    return fixes


def fix_nested_batch_id(path: Path, correct_id: str, wrapper_key: str) -> list[str]:
    """Fix batch_id: manifest inside a wrapper key (e.g. judge_packet.batch_id)."""
    fixes = []
    data = load_yaml(path)
    if not data:
        return fixes

    inner = data.get(wrapper_key)
    if isinstance(inner, dict) and inner.get("batch_id") == "manifest":
        inner["batch_id"] = correct_id
        save_yaml(path, data)
        fixes.append(f"  {path.name}: {wrapper_key}.batch_id 'manifest' → '{correct_id}'")

    return fixes


def fix_manifest_batch_id(path: Path, correct_id: str) -> list[str]:
    """Ensure manifest has top-level batch_id."""
    fixes = []
    data = load_yaml(path)
    if not data:
        return fixes

    if "batch_id" not in data:
        # Derive from batch_metadata if available, else from dir name
        nested_id = data.get("batch_metadata", {}).get("batch_id", correct_id)
        data["batch_id"] = nested_id
        # Move batch_id to top of dict
        reordered = {"batch_id": data.pop("batch_id")}
        reordered.update(data)
        save_yaml(path, reordered)
        fixes.append(f"  manifest.yaml: added top-level batch_id='{nested_id}'")

    return fixes


def main() -> None:
    if not BATCHES_DIR.exists():
        print(f"ERROR: {BATCHES_DIR} not found")
        sys.exit(1)

    batch_dirs = sorted(
        d for d in BATCHES_DIR.iterdir()
        if d.is_dir() and d.name.startswith("batch_")
    )
    print(f"Scanning {len(batch_dirs)} batch directories...\n")

    total_fixes = 0
    for batch_dir in batch_dirs:
        batch_id = batch_dir.name
        fixes: list[str] = []

        # 1. Fix research_result.yaml
        result_file = batch_dir / "research_result.yaml"
        if result_file.exists():
            fixes.extend(fix_batch_id_in_file(result_file, batch_id))

        # 2. Fix judge_packet.yaml (top-level and nested)
        packet_file = batch_dir / "judge_packet.yaml"
        if packet_file.exists():
            fixes.extend(fix_batch_id_in_file(packet_file, batch_id))
            fixes.extend(fix_nested_batch_id(packet_file, batch_id, "judge_packet"))

        # 3. judge_report.yaml — skip (correct batch_ids, some have broken YAML syntax)

        # 4. Ensure manifest has top-level batch_id
        manifest_file = batch_dir / "manifest.yaml"
        if manifest_file.exists():
            fixes.extend(fix_manifest_batch_id(manifest_file, batch_id))

        if fixes:
            print(f"[{batch_id}]")
            for f in fixes:
                print(f)
            total_fixes += len(fixes)

    print(f"\n{'='*50}")
    print(f"Total fixes applied: {total_fixes}")

    # Summary: batches with judge_report but possibly not finalized
    print(f"\nBatches with judge_report.yaml:")
    for batch_dir in batch_dirs:
        report_file = batch_dir / "judge_report.yaml"
        if report_file.exists():
            print(f"  {batch_dir.name}")


if __name__ == "__main__":
    main()
