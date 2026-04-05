"""CLI command: library — factor library status overview.

Shows library size, grade distribution, category coverage, and
optionally detailed per-factor metrics.
"""

from __future__ import annotations

from mining.config import MiningConfig
from mining.registry import FactorLibrary


def cmd_library(args):
    """Show factor library status."""
    config = MiningConfig()
    lib = FactorLibrary(config)
    factors = lib.list_factors()

    if not factors:
        print("Library is empty.")
        return

    # Summary
    print(f"Library: {len(factors)} factors")

    # Grade distribution
    grades = {}
    for f in factors:
        grade = f.get("grade", "?")
        grades[grade] = grades.get(grade, 0) + 1
    if grades:
        print("\nGrade distribution:")
        for g in ["S", "A", "B", "C", "D", "?"]:
            if g in grades:
                print(f"  {g}: {grades[g]}")

    # Category coverage
    categories = {}
    for f in factors:
        cat = f.get("category", "unknown")
        categories[cat] = categories.get(cat, 0) + 1
    if categories:
        print("\nCategory coverage:")
        for cat, count in sorted(categories.items()):
            bar = "#" * count
            print(f"  {cat:20s} {count:3d} {bar}")

    # Avg IC
    ics = [abs(f.get("ic_mean", 0)) for f in factors if f.get("ic_mean")]
    if ics:
        avg = sum(ics) / len(ics)
        print(f"\nAvg |IC|: {avg:.4f}")

    # Verbose per-factor listing
    if getattr(args, "verbose", False):
        print("\nPer-factor details:")
        for f in factors:
            fid = f.get("id", "?")
            name = f.get("name", "?")
            ic = f.get("ic_mean", "N/A")
            grade = f.get("grade", "?")
            print(f"  [{fid}] {name}: IC={ic}, Grade={grade}")
