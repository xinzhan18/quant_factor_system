"""CLI command: manage forbidden expression patterns."""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

import yaml

from mining.config import MiningConfig
from mining.memory import ExperienceMemory


def cmd_forbidden(args):
    """Manage forbidden expression patterns."""
    config = MiningConfig()
    mem = ExperienceMemory(config)

    if args.forbidden_action == "list":
        regions = mem.read_forbidden()
        if not regions:
            print("No forbidden regions.")
            return
        for r in regions:
            print(f"  {r.get('pattern', '?')} — {r.get('reason', '?')}")

    elif args.forbidden_action in ("suggest", "apply"):
        suggestions = _forbidden_suggest(config)
        if not suggestions:
            print("No forbidden patterns suggested.")
            return
        for s in suggestions:
            print(f"  {s['skeleton']}  (blocker={s['blocker']}, "
                  f"batches={s['batch_count']}, category={s['category']})")
        if args.forbidden_action == "apply":
            for s in suggestions:
                mem.add_forbidden(s["skeleton"], f"auto: blocker={s['blocker']}, "
                                  f"{s['batch_count']} batches")
            print(f"\n{len(suggestions)} patterns written to forbidden.yaml.")


def _forbidden_suggest(config: MiningConfig):
    """Scan result files for Stage 2 corr rejects, find repeated patterns."""
    candidates_dir = Path(config.candidates_dir)
    # key = (skeleton, blocker) → set of batch_ids
    pattern_batches: dict = defaultdict(lambda: {"batches": set(), "category": None})

    for result_file in sorted(candidates_dir.glob("*_result.yaml")):
        try:
            with open(result_file, 'r') as f:
                data = yaml.unsafe_load(f) or {}
        except Exception:
            continue
        batch_id = data.get("batch_id", result_file.stem)
        for r in data.get("rejected", []):
            # Check for Stage 2 corr reject (new structured or old format)
            meta = r.get("reject_meta", {})
            if meta.get("code") == "stage2_corr":
                blocker = meta.get("blocker", "?")
                corr = meta.get("corr", 0)
            elif r.get("stage2", {}).get("passed") is False:
                blocker = r.get("stage2", {}).get("max_corr_factor", "?")
                corr = r.get("stage2", {}).get("max_corr", 0)
            else:
                continue
            expr = r.get("expression", "")
            if not expr:
                continue
            skeleton = re.sub(r'\d+\.?\d*', '*', expr)
            category = r.get("category", "?")
            key = (skeleton, blocker)
            pattern_batches[key]["batches"].add(batch_id)
            pattern_batches[key]["category"] = category

    suggestions = []
    for (skeleton, blocker), info in pattern_batches.items():
        if len(info["batches"]) >= 3:
            suggestions.append({
                "skeleton": skeleton,
                "blocker": blocker,
                "batch_count": len(info["batches"]),
                "category": info["category"],
            })
    return sorted(suggestions, key=lambda s: -s["batch_count"])
