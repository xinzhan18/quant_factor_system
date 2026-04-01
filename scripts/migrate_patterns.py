#!/usr/bin/env python3
"""Migrate patterns.yaml to per-direction .md files.

One-time migration script. Run before first /mine under new system.

Usage:
    cd /Users/xinzhan/.openclaw/workspace/quant_factor_system
    PYTHONPATH=src python3 scripts/migrate_patterns.py [--dry-run]
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

import yaml

MEMORY_DIR = Path("storage/memory")
PATTERNS_PATH = MEMORY_DIR / "patterns.yaml"
DIRECTIONS_DIR = MEMORY_DIR / "directions"
INDEX_PATH = MEMORY_DIR / "directions.yaml"
STATE_PATH = MEMORY_DIR / "state.yaml"


def slugify(name: str) -> str:
    """Convert direction name to filename-safe slug."""
    slug = name.lower().strip()
    slug = re.sub(r'[^a-z0-9]+', '_', slug)
    slug = slug.strip('_')
    return slug


def render_md(frontmatter: dict, body: str) -> str:
    fm = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True, sort_keys=False)
    return f"---\n{fm}---\n\n{body}"


def determine_status(rec: dict, state: dict) -> str:
    """Derive status from patterns.yaml note and state.yaml domain_saturation."""
    note = rec.get("note", "").lower()
    if "blocked" in note:
        return "blocked"
    # Check domain_saturation in state.yaml
    sat = state.get("domain_saturation", {})
    for domain, info in sat.items():
        if domain.lower() in rec.get("pattern", "").lower():
            s = info.get("saturation", "")
            if s == "exhausted":
                return "dead"
            if s == "saturated":
                return "exhausted"
    sr = rec.get("success_rate", "")
    if sr == "high":
        return "active"
    return "active"


def migrate_recommended(patterns: dict, state: dict, dry_run: bool) -> list:
    """Migrate recommended_directions to direction files."""
    directions = []
    for rec in patterns.get("recommended_directions", []):
        name = slugify(rec["pattern"])
        status = determine_status(rec, state)

        factors = rec.get("example_factors", [])
        parent = factors[0] if factors else None

        fm = {
            "name": name,
            "status": status,
            "category": _guess_category(rec),
            "source": "baseline",
            "parent_factor": parent,
            "attempts": len(factors),
            "best_ic": None,
            "last_batch": None,
            "priority": "high" if rec.get("success_rate") == "high" else "medium",
            "created": str(date.today()),
        }

        body_parts = [rec.get("description", "")]
        body_parts.append(f"\n## Rationale\n{rec.get('note', '')}")
        if factors:
            body_parts.append(f"\n## Related Factors\n{', '.join(factors)}")
        body_parts.append("\n## Probe Records\n")
        body_parts.append("\n## Candidate History\n")
        body = "\n".join(body_parts)

        if dry_run:
            print(f"  [REC] {name} → status={status}")
        else:
            path = DIRECTIONS_DIR / f"{name}.md"
            path.write_text(render_md(fm, body), encoding="utf-8")

        directions.append(fm)
    return directions


def migrate_forbidden(patterns: dict, existing_slugs: set, dry_run: bool) -> list:
    """Migrate forbidden_regions to direction files with status=dead."""
    directions = []
    for fb in patterns.get("forbidden_regions", []):
        direction_text = fb.get("direction", "")

        # Skip generic engineering constraints — they stay in mining-lessons.md
        reason_lower = fb.get("reason", "").lower()
        if ("operator" in direction_text.lower() and "not registered" in reason_lower) or \
                ("not registered" in reason_lower and "expressions using" in direction_text.lower()):
            if dry_run:
                print(f"  [SKIP] Engineering constraint: {direction_text[:60]}...")
            continue
        if "symmetric ifel" in direction_text.lower():
            if dry_run:
                print(f"  [SKIP] Engineering constraint: {direction_text[:60]}...")
            continue
        if "producing mostly zeros" in direction_text.lower():
            if dry_run:
                print(f"  [SKIP] Engineering constraint: {direction_text[:60]}...")
            continue

        name = slugify(direction_text[:60])

        # If a recommended direction already covers this, append to it instead
        if name in existing_slugs:
            if dry_run:
                print(f"  [MERGE] {name} — append forbidden info to existing")
            continue

        fm = {
            "name": name,
            "status": "dead",
            "category": "other",
            "source": "baseline",
            "parent_factor": None,
            "attempts": 0,
            "best_ic": None,
            "last_batch": None,
            "priority": "none",
            "created": str(date.today()),
        }

        corr_factors = fb.get("correlated_factors", [])
        body = f"{direction_text}\n\n## Why Dead\n{fb.get('reason', '')}"
        if corr_factors:
            body += f"\n\nCorrelated with: {', '.join(corr_factors)}"
        if fb.get("correlation"):
            body += f"\nCorrelation: {fb['correlation']}"
        body += "\n\n## Probe Records\n\n## Candidate History\n"

        if dry_run:
            print(f"  [DEAD] {name}")
        else:
            path = DIRECTIONS_DIR / f"{name}.md"
            path.write_text(render_md(fm, body), encoding="utf-8")

        directions.append(fm)
    return directions


def simplify_state(dry_run: bool):
    """Remove domain_saturation from state.yaml, add next_round_hint."""
    state = yaml.safe_load(STATE_PATH.read_text(encoding="utf-8")) or {}
    if "domain_saturation" in state:
        if dry_run:
            print("  [STATE] Would remove domain_saturation, add next_round_hint")
        else:
            del state["domain_saturation"]
            state["next_round_hint"] = None
            STATE_PATH.write_text(
                yaml.dump(state, default_flow_style=False, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )


def build_index(all_directions: list, dry_run: bool):
    """Write directions.yaml index."""
    index = [{
        "name": d["name"],
        "status": d["status"],
        "priority": d["priority"],
        "category": d["category"],
        "attempts": d["attempts"],
        "best_ic": d["best_ic"],
    } for d in all_directions]

    if dry_run:
        print(f"\n  [INDEX] Would write {len(index)} entries to directions.yaml")
    else:
        INDEX_PATH.write_text(
            yaml.dump(index, default_flow_style=False, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )


def _guess_category(rec: dict) -> str:
    """Guess category from pattern name."""
    name = rec.get("pattern", "").lower()
    if "volat" in name or "atr" in name:
        return "volatility"
    if "volume" in name or "pv" in name:
        return "volume"
    if "range" in name or "intraday" in name or "candlestick" in name:
        return "candlestick"
    if "regime" in name:
        return "regime"
    if "alpha101" in name:
        return "composite"
    if "momentum" in name or "overnight" in name:
        return "momentum"
    if "trend" in name or "resi" in name or "regression" in name:
        return "trend"
    if "distribution" in name or "tail" in name:
        return "distribution"
    if "efficiency" in name:
        return "efficiency"
    return "other"


def main():
    parser = argparse.ArgumentParser(description="Migrate patterns.yaml to direction files")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be done")
    args = parser.parse_args()

    if not PATTERNS_PATH.exists():
        print(f"Error: {PATTERNS_PATH} not found")
        sys.exit(1)

    patterns = yaml.safe_load(PATTERNS_PATH.read_text(encoding="utf-8")) or {}
    state = yaml.safe_load(STATE_PATH.read_text(encoding="utf-8")) or {} if STATE_PATH.exists() else {}

    if not args.dry_run:
        DIRECTIONS_DIR.mkdir(parents=True, exist_ok=True)

    print("=== Migrating recommended_directions ===")
    rec_dirs = migrate_recommended(patterns, state, args.dry_run)
    rec_slugs = {d["name"] for d in rec_dirs}

    print("\n=== Migrating forbidden_regions ===")
    fb_dirs = migrate_forbidden(patterns, rec_slugs, args.dry_run)

    all_dirs = rec_dirs + fb_dirs

    print("\n=== Building index ===")
    build_index(all_dirs, args.dry_run)

    print("\n=== Simplifying state.yaml ===")
    simplify_state(args.dry_run)

    print(f"\nDone. {len(rec_dirs)} recommended + {len(fb_dirs)} forbidden = {len(all_dirs)} direction files.")
    if not args.dry_run:
        print(f"Verify results in {DIRECTIONS_DIR}/ and {INDEX_PATH}")
        print(f"Then delete {PATTERNS_PATH} manually when satisfied.")
    else:
        print("(dry run — no files written)")


if __name__ == "__main__":
    main()
