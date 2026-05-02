"""``research audit field-coverage`` — surface field × atom blind spots.

Walks every ``batches/batch_*/manifest.yaml``, parses each candidate's
``expression`` for ``$field`` mentions and the **outermost atom** wrapping
each, then computes the coverage matrix:

    rows: every ``$field`` in DSL_FIELD_WHITELIST
    cols: 9 standard atom families (CsRank, TsRank, Mean, Std, Skew,
          AnnualChange = Sub(X, Ref(X, ~252)), DeviationFromMA,
          PairwiseRatio = Div(X, Y), CrossFieldCov = Corr/Cov)

Emits ``storage/vault/_meta/field_coverage_{timestamp}.md`` listing:

1. **Untouched fields** (zero atom forms tested across all batches)
2. **Single-atom fields** (only one form tested, baseline gap)
3. **Coverage matrix** (per-field counts)
4. **Recommended baseline candidates** (concrete DSL expressions for
   the highest-priority gaps)

Why this exists: prior consolidations could not see "which 22 fields
× which atoms have been tried" because no specialist aggregated field
usage across batches. Result: 5 fundamental directions all built
**composite** expressions, never single-field baselines, leaving
14/22 new fields with zero atom coverage.

**Does not mutate state** — output is a packet for /factor-idea to
read at design time.
"""

from __future__ import annotations

import argparse
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from research.storage.paths import StoragePaths
from research.storage.yaml_io import load_yaml

# Source of truth for what *should* be covered.
from research.phases.phase1_start import DSL_FIELD_WHITELIST


# Atom families recognised. Order matters for "outermost wins" parsing
# — ``Sub(X, Ref(X, w))`` must be detected before ``Sub`` is otherwise
# attributed to a generic atom.
ATOM_FAMILIES: list[str] = [
    "CsRank",
    "TsRank",
    "Mean",
    "Std",
    "Skew",
    "AnnualChange",       # Sub(X, Ref(X, ≥120))
    "DeviationFromMA",    # Sub(X, Mean(X, w))
    "PairwiseRatio",      # Div(X, Y) where Y is also a $field
    "CrossFieldCov",      # Corr(X, Y, w) / Cov(X, Y, w)
]

# Canonical regexes. The expression strings stored in manifest.yaml
# are already linearised (no whitespace ambiguity) so simple regex
# parsing is sufficient.
_RE_CSRANK = re.compile(r"\bCsRank\s*\(\s*\$(\w+)")
_RE_TSRANK = re.compile(r"\bTsRank\s*\(\s*\$(\w+)")
_RE_MEAN = re.compile(r"\bMean\s*\(\s*\$(\w+)")
_RE_STD = re.compile(r"\bStd\s*\(\s*\$(\w+)")
_RE_SKEW = re.compile(r"\bSkew\s*\(\s*\$(\w+)")
_RE_ANNUAL = re.compile(
    r"\bSub\s*\(\s*\$(\w+)\s*,\s*Ref\s*\(\s*\$\1\s*,\s*(\d+)"
)
_RE_DEV_MA = re.compile(
    r"\bSub\s*\(\s*\$(\w+)\s*,\s*Mean\s*\(\s*\$\1"
)
_RE_PAIR = re.compile(r"\bDiv\s*\(\s*\$(\w+)\s*,\s*\$(\w+)")
_RE_CROSS = re.compile(r"\b(?:Corr|Cov)\s*\(\s*\$(\w+)\s*,\s*\$(\w+)")
# Catch-all $field reference (used for "appears anywhere" stats).
_RE_FIELD = re.compile(r"\$(\w+)")


@dataclass
class CandidateUse:
    batch_id: str
    candidate_id: str
    direction: str
    expression: str
    fields_used: set[str] = field(default_factory=set)
    field_atoms: dict[str, set[str]] = field(default_factory=dict)


def _parse_expression(expr: str) -> dict[str, set[str]]:
    """Map each ``$field`` to the set of atom families it appears under.

    A field may appear multiple times under different atoms; we record
    every wrapping. ``AnnualChange`` requires window ≥ 120 to count
    (lower windows are treated as generic Sub).
    """
    field_atoms: dict[str, set[str]] = defaultdict(set)

    for m in _RE_CSRANK.finditer(expr):
        field_atoms[m.group(1)].add("CsRank")
    for m in _RE_TSRANK.finditer(expr):
        field_atoms[m.group(1)].add("TsRank")
    for m in _RE_MEAN.finditer(expr):
        field_atoms[m.group(1)].add("Mean")
    for m in _RE_STD.finditer(expr):
        field_atoms[m.group(1)].add("Std")
    for m in _RE_SKEW.finditer(expr):
        field_atoms[m.group(1)].add("Skew")
    for m in _RE_ANNUAL.finditer(expr):
        if int(m.group(2)) >= 120:
            field_atoms[m.group(1)].add("AnnualChange")
    for m in _RE_DEV_MA.finditer(expr):
        field_atoms[m.group(1)].add("DeviationFromMA")
    for m in _RE_PAIR.finditer(expr):
        field_atoms[m.group(1)].add("PairwiseRatio")
        field_atoms[m.group(2)].add("PairwiseRatio")
    for m in _RE_CROSS.finditer(expr):
        field_atoms[m.group(1)].add("CrossFieldCov")
        field_atoms[m.group(2)].add("CrossFieldCov")

    return dict(field_atoms)


def collect_uses(paths: StoragePaths) -> list[CandidateUse]:
    """Walk every batch manifest, parse expressions, return uses."""
    uses: list[CandidateUse] = []
    batches_dir = paths.vault_dir / "batches"
    if not batches_dir.exists():
        return uses

    for batch_path in sorted(batches_dir.glob("batch_*")):
        if not batch_path.is_dir():
            continue
        manifest_path = batch_path / "manifest.yaml"
        if not manifest_path.exists():
            continue
        try:
            manifest = load_yaml(manifest_path)
        except Exception:
            continue
        direction = manifest.get("direction", "unknown")
        for c in manifest.get("candidates", []) or []:
            expr = (c.get("expression") or "").replace("\n", " ")
            if not expr:
                continue
            fields_used = set(_RE_FIELD.findall(expr))
            field_atoms = _parse_expression(expr)
            uses.append(
                CandidateUse(
                    batch_id=batch_path.name,
                    candidate_id=c.get("candidate_id", "?"),
                    direction=direction,
                    expression=expr,
                    fields_used=fields_used,
                    field_atoms=field_atoms,
                )
            )
    return uses


def build_matrix(uses: list[CandidateUse]) -> dict[str, dict[str, int]]:
    """Aggregate field → atom → count of candidates that exercise it."""
    matrix: dict[str, dict[str, int]] = {
        f.lstrip("$"): {a: 0 for a in ATOM_FAMILIES}
        for f in DSL_FIELD_WHITELIST
    }
    for u in uses:
        for fld, atoms in u.field_atoms.items():
            if fld not in matrix:
                # Field not in current whitelist (e.g. removed); skip.
                continue
            for a in atoms:
                matrix[fld][a] += 1
    return matrix


# Recommended baseline expressions per atom family. Used to surface
# concrete next-step candidates for any 0-coverage cell. Window 60d
# is the default — F024/F025 confirm 60d is the sweet spot.
def _baseline_expr(field_name: str, atom: str) -> str:
    f = f"${field_name}"
    if atom == "CsRank":
        return f"CsRank({f})"
    if atom == "TsRank":
        return f"TsRank({f}, 60)"
    if atom == "Mean":
        return f"Sub({f}, Mean({f}, 60))"
    if atom == "Std":
        return f"Std({f}, 60)"
    if atom == "Skew":
        return f"Skew({f}, 60)"
    if atom == "AnnualChange":
        return f"Sub({f}, Ref({f}, 252))"
    if atom == "DeviationFromMA":
        return f"Sub({f}, Mean({f}, 252))"
    if atom == "PairwiseRatio":
        return f"Div({f}, $close)"  # generic ratio — caller substitutes
    if atom == "CrossFieldCov":
        return f"Corr({f}, $close, 60)"
    return f"# unknown atom {atom}"


def render_report(
    matrix: dict[str, dict[str, int]],
    uses: list[CandidateUse],
) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out: list[str] = []
    out.append(f"# Field × Atom Coverage Audit — {now}")
    out.append("")
    out.append(
        f"**Whitelist size**: {len(DSL_FIELD_WHITELIST)} fields · "
        f"**Atom families tracked**: {len(ATOM_FAMILIES)} · "
        f"**Candidates scanned**: {len(uses)} across "
        f"{len({u.batch_id for u in uses})} batches"
    )
    out.append("")

    # 1. Untouched fields (any-atom count == 0)
    untouched: list[str] = []
    single_atom: list[tuple[str, str]] = []
    for fld, row in matrix.items():
        total = sum(row.values())
        nonzero_atoms = [a for a, c in row.items() if c > 0]
        if total == 0:
            untouched.append(fld)
        elif len(nonzero_atoms) == 1:
            single_atom.append((fld, nonzero_atoms[0]))

    out.append("## 1. Untouched fields (zero atom coverage)")
    out.append("")
    if untouched:
        out.append(
            f"**{len(untouched)}** fields have **never** appeared as "
            "a direct atom argument in any candidate. These are pure "
            "blind spots.\n"
        )
        for fld in sorted(untouched):
            out.append(f"- `${fld}`")
    else:
        out.append("_None — every whitelisted field has been touched._")
    out.append("")

    # 2. Single-atom fields
    out.append("## 2. Single-atom fields (one form tested only)")
    out.append("")
    if single_atom:
        out.append(
            f"**{len(single_atom)}** fields have been tried under **only one** "
            "atom family. Other atom forms are unverified.\n"
        )
        for fld, atom in sorted(single_atom):
            out.append(f"- `${fld}` — only `{atom}`")
    else:
        out.append("_None — every used field has ≥2 atom forms tested._")
    out.append("")

    # 3. Full matrix
    out.append("## 3. Coverage matrix")
    out.append("")
    header = "| Field | " + " | ".join(ATOM_FAMILIES) + " | Σ |"
    sep = "|---|" + "|".join(["---"] * len(ATOM_FAMILIES)) + "|---|"
    out.append(header)
    out.append(sep)
    # Sort by total ascending — least covered first.
    rows_sorted = sorted(
        matrix.items(), key=lambda kv: (sum(kv[1].values()), kv[0])
    )
    for fld, row in rows_sorted:
        cells = [
            (str(row[a]) if row[a] > 0 else "·") for a in ATOM_FAMILIES
        ]
        total = sum(row.values())
        out.append(
            f"| `${fld}` | " + " | ".join(cells) + f" | {total} |"
        )
    out.append("")

    # 4. Recommended baseline candidates for the highest-priority gaps
    out.append("## 4. Recommended baseline candidates")
    out.append("")
    out.append(
        "For each untouched field, run a `CsRank` + `TsRank-60` baseline "
        "**before** any composite. For single-atom fields, fill the most "
        "informative remaining atom (`AnnualChange` for fundamentals, "
        "`Std/Skew` for price-volume).\n"
    )
    out.append("### Untouched-field baselines (priority: highest)")
    out.append("")
    if untouched:
        for fld in sorted(untouched):
            out.append(f"- `${fld}`:")
            out.append(f"  - `{_baseline_expr(fld, 'CsRank')}`")
            out.append(f"  - `{_baseline_expr(fld, 'TsRank')}`")
            out.append(f"  - `{_baseline_expr(fld, 'AnnualChange')}`")
    else:
        out.append("_No untouched fields._")
    out.append("")
    out.append("### Single-atom baselines (priority: medium)")
    out.append("")
    if single_atom:
        for fld, tested in sorted(single_atom):
            missing = [a for a in ("CsRank", "TsRank", "AnnualChange") if a != tested]
            for a in missing[:2]:  # cap suggestions per field
                out.append(f"- `${fld}` ({tested} done, missing {a}): `{_baseline_expr(fld, a)}`")
    else:
        out.append("_No single-atom fields._")
    out.append("")
    return "\n".join(out) + "\n"


def _run_audit_field_coverage(args: argparse.Namespace) -> None:
    storage_root = Path(getattr(args, "storage_root", "storage"))
    paths = StoragePaths(storage_root)
    uses = collect_uses(paths)
    matrix = build_matrix(uses)
    report = render_report(matrix, uses)

    if args.dry_run:
        print(report)
        return

    out_dir = paths.vault_dir / "_meta"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = out_dir / f"field_coverage_{stamp}.md"
    out_path.write_text(report, encoding="utf-8")
    # Also write a stable-name copy so downstream skills can reference
    # ``vault/_meta/field_coverage_latest.md`` without the timestamp.
    latest_path = out_dir / "field_coverage_latest.md"
    latest_path.write_text(report, encoding="utf-8")

    untouched = sum(
        1 for fld, row in matrix.items() if sum(row.values()) == 0
    )
    single = sum(
        1
        for fld, row in matrix.items()
        if 0 < len([a for a, c in row.items() if c > 0]) <= 1
    )
    print(f"Wrote {out_path}")
    print(f"  also: {latest_path}")
    print(
        f"  untouched_fields={untouched}  single_atom_fields={single}  "
        f"candidates_scanned={len(uses)}"
    )


def register_audit_field_coverage(audit_sub: argparse._SubParsersAction) -> None:
    """Attach ``research audit field-coverage`` to the ``audit`` group."""
    p = audit_sub.add_parser(
        "field-coverage",
        help="Surface $field × atom blind spots across every batch manifest",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print report to stdout instead of writing to storage/vault/_meta/",
    )
    p.set_defaults(func=_run_audit_field_coverage)
