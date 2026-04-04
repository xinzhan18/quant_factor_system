#!/usr/bin/env python3
"""Generate inventory snapshot of all factor records.

Reads all factor_*.yaml files and outputs:
1. Total count
2. Schema field coverage
3. Per-factor summary (id, name, status, ic, schema gaps)
4. Category distribution

Does NOT modify any files.

Usage:
    PYTHONPATH=src python3 scripts/inventory.py
    PYTHONPATH=src python3 scripts/inventory.py --output docs/migration/inventory_snapshot.yaml
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import yaml
from mining.schema import normalize_metrics


EXPECTED_FIELDS = [
    "id", "name", "expression", "source", "status",
    "evaluation_version", "category", "batch", "admitted_at",
    "long_leg", "metrics",
]
EXPECTED_METRICS = [
    "ic_mean", "ic_ir", "ic_mean_oos", "ic_ir_oos",
    "ic_win_rate", "monotonicity_is", "ls_return", "max_corr",
]


def main():
    parser = argparse.ArgumentParser(description="Factor inventory snapshot")
    parser.add_argument("--library-dir", default="storage/library")
    parser.add_argument("--output", default=None, help="Save snapshot to YAML file")
    args = parser.parse_args()

    factors_dir = Path(args.library_dir) / "factors"
    if not factors_dir.exists():
        print(f"ERROR: {factors_dir} does not exist")
        sys.exit(1)

    factor_files = sorted(factors_dir.glob("factor_*.yaml"))
    print(f"Found {len(factor_files)} factor detail files\n")

    field_counts = {f: 0 for f in EXPECTED_FIELDS}
    metric_counts = {m: 0 for m in EXPECTED_METRICS}
    category_counts = {}
    factors = []

    for p in factor_files:
        with open(p, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        fid = str(data.get("id", "?"))
        name = data.get("name", "?")
        metrics = data.get("metrics", {})
        norm = normalize_metrics(metrics)
        ic = norm.get("ic_mean")

        for fld in EXPECTED_FIELDS:
            if fld in data and data[fld] is not None:
                field_counts[fld] += 1

        for mk in EXPECTED_METRICS:
            if mk in norm and norm[mk] is not None:
                metric_counts[mk] += 1

        cat = data.get("category", "unknown")
        category_counts[cat] = category_counts.get(cat, 0) + 1

        missing = [fld for fld in EXPECTED_FIELDS if fld not in data or data[fld] is None]
        missing_metrics = [m for m in EXPECTED_METRICS if m not in norm or norm[m] is None]

        factors.append({
            "id": fid,
            "name": name,
            "category": cat,
            "ic_mean": round(ic, 4) if ic is not None else None,
            "has_status": "status" in data,
            "has_eval_version": "evaluation_version" in data,
            "has_long_leg": "long_leg" in data,
            "missing_fields": missing,
            "missing_metrics": missing_metrics,
        })

    total = len(factor_files)
    print("=== Schema Field Coverage ===")
    for fld in EXPECTED_FIELDS:
        pct = field_counts[fld] / total * 100
        print(f"  {fld:25s} {field_counts[fld]:3d}/{total}  ({pct:.0f}%)")

    print("\n=== Metrics Coverage (after alias normalization) ===")
    for m in EXPECTED_METRICS:
        pct = metric_counts[m] / total * 100
        print(f"  {m:25s} {metric_counts[m]:3d}/{total}  ({pct:.0f}%)")

    print("\n=== Category Distribution ===")
    for cat, count in sorted(category_counts.items(), key=lambda x: -x[1]):
        print(f"  {cat:25s} {count:3d}")

    print("\n=== Factors with Most Schema Gaps ===")
    gapped = sorted(factors, key=lambda f: len(f["missing_fields"]) + len(f["missing_metrics"]), reverse=True)
    for f in gapped[:10]:
        gap_count = len(f["missing_fields"]) + len(f["missing_metrics"])
        print(f"  [{f['id']}] {f['name']:30s}  gaps={gap_count}  "
              f"fields={f['missing_fields']}")

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "total_factors": total,
            "field_coverage": field_counts,
            "metric_coverage": metric_counts,
            "category_distribution": category_counts,
            "factors": factors,
        }
        with open(output_path, "w", encoding="utf-8") as f:
            yaml.dump(snapshot, f, default_flow_style=False, allow_unicode=True)
        print(f"\nSnapshot saved to {args.output}")


if __name__ == "__main__":
    main()
