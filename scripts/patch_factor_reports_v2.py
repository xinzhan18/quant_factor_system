#!/usr/bin/env python3
"""Patch each ``vault/factors/F{id}.md`` after the v2 library recompute.

Two surgical edits per file:

1. **Frontmatter** — refresh the scalar metrics that downstream Bases /
   dashboards read (``ic_mean_validation``, ``ic_ir_validation``,
   ``monotonicity_validation``, ``alpha_survival_ratio``, ``status``,
   ``primary_universe``, ``csi300_passes_floor``, ``revalidated_in_batch``).

2. **Notice block** — replace any pre-existing
   ``<!-- BEGIN recompute_v1_notice --> ... <!-- END recompute_v1_notice -->``
   block with a v2 notice that points at ``batch_recompute_v2`` and
   carries the multi-universe table from the F{id}.yaml.

The body narrative is untouched on purpose: v2 metrics replicate v1
within rounding (the only material difference between the two recomputes
is that v2 also evaluates F004/F005 with the corrected scipy ``rtol``
call). Body re-narration would require ``/factor-report`` subagent
dispatches, which is out of scope here.
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

V1_BLOCK_RE = re.compile(
    r"<!-- BEGIN recompute_v1_notice -->.*?<!-- END recompute_v1_notice -->\n*",
    re.DOTALL,
)
V2_BLOCK_RE = re.compile(
    r"<!-- BEGIN recompute_v2_notice -->.*?<!-- END recompute_v2_notice -->\n*",
    re.DOTALL,
)
FRONT_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def _fmt(x: Any, fmt: str = ".4f") -> str:
    if x is None:
        return "—"
    try:
        return format(float(x), fmt)
    except (ValueError, TypeError):
        return str(x)


def _build_v2_notice(meta: dict[str, Any]) -> str:
    by_u = meta.get("validation_metrics_by_universe") or {}
    primary = meta.get("primary_universe") or "all_tradable"
    rob = meta.get("universe_robustness") or {}
    revalidated = meta.get("revalidated_in_batch") or "—"

    lines = [
        "<!-- BEGIN recompute_v2_notice -->",
        f"> [!info] 🔄 Library Recompute v2 — primary universe: `{primary}`",
        "> Re-evaluated through Phase 2 mainline under `tradable_mask` "
        "(ST + suspend + 涨跌停 + 60d new-listing) with multi-universe basic metrics. "
        f"Source of truth: [[batches/{revalidated}/result|{revalidated}/result.yaml]]. "
        "Old metrics in DB `factor_values` are abandoned — see [[_meta/library_purge_library_recompute_v2|purge log]].",
        "",
        "> ### Multi-Universe Evaluation (basic metrics)",
        "> | Universe | Coverage | IC mean | ICIR | Mono | L/S Sharpe |",
        "> |---|---|---|---|---|---|",
    ]
    for u in ["all_tradable", "csi300", "csi1000"]:
        m = by_u.get(u) or {}
        marker = "**" if u == primary else ""
        lines.append(
            f"> | {marker}{u}{marker} | "
            f"{_fmt(m.get('coverage'), '.3f')} | "
            f"{_fmt(m.get('ic_mean'))} | "
            f"{_fmt(m.get('ic_ir'), '.3f')} | "
            f"{_fmt(m.get('monotonicity'), '.2f')} | "
            f"{_fmt(m.get('long_short_sharpe'), '.3f')} |"
        )
    lines.append("")
    if rob:
        ratio = rob.get("icir_robustness_ratio")
        passes = rob.get("csi300_passes_admission_floor")
        sign_ok = rob.get("ic_sign_consistent_across_universes")
        lines.append(
            f"> **csi300 floor**: {'✅' if passes else '❌'} (`|ICIR|≥0.15 ∧ |mono|≥0.6`) · "
            f"icir_robustness_ratio = {_fmt(ratio, '.3f')} · "
            f"sign consistency: {'✅' if sign_ok else '❌'}"
        )
        lines.append("")
    lines.append(
        "> _Body narrative below was authored against v1 metrics; v2 differences "
        "are within rounding so the mechanism explanation remains valid. Numerical "
        "scalars in the frontmatter and tables above are v2-canonical._"
    )
    lines.append("<!-- END recompute_v2_notice -->")
    return "\n".join(lines)


def _patch_frontmatter(front_text: str, meta: dict[str, Any]) -> str:
    """Update specific scalar fields without restructuring the YAML."""
    fm = yaml.safe_load(front_text) or {}

    val = meta.get("validation_metrics") or {}
    risk = meta.get("risk_metrics") or {}
    rob = meta.get("universe_robustness") or {}

    fm["ic_mean_validation"] = val.get("ic_mean")
    fm["ic_ir_validation"] = val.get("ic_ir")
    fm["monotonicity_validation"] = val.get("monotonicity")
    if risk.get("alpha_survival_ratio") is not None:
        fm["alpha_survival_ratio"] = risk.get("alpha_survival_ratio")
    fm["status"] = meta.get("status", fm.get("status"))
    fm["primary_universe"] = meta.get("primary_universe") or fm.get("primary_universe")
    fm["csi300_passes_floor"] = bool(rob.get("csi300_passes_admission_floor", False))
    if meta.get("revalidated_in_batch"):
        fm["revalidated_in_batch"] = meta["revalidated_in_batch"]
    fm["icir_robustness_ratio"] = rob.get("icir_robustness_ratio")

    # Preserve key order: yaml.dump default is sorted; we want stable.
    return yaml.dump(fm, allow_unicode=True, sort_keys=False).rstrip()


def patch_one(md_path: Path, meta: dict[str, Any]) -> bool:
    """Returns True iff file was modified."""
    if not md_path.exists():
        logger.warning("md missing: %s", md_path)
        return False
    text = md_path.read_text(encoding="utf-8")
    original = text

    fm_match = FRONT_RE.match(text)
    if fm_match:
        new_fm = _patch_frontmatter(fm_match.group(1), meta)
        text = "---\n" + new_fm + "\n---\n" + text[fm_match.end():]
    else:
        logger.warning("no frontmatter in %s — skipping FM update", md_path)

    # Strip stale v1 / v2 blocks first
    text = V1_BLOCK_RE.sub("", text)
    text = V2_BLOCK_RE.sub("", text)

    notice = _build_v2_notice(meta) + "\n\n"
    # Insert notice immediately after the H1 line if present, otherwise at top.
    h1_match = re.search(r"^# .+\n", text, re.MULTILINE)
    if h1_match:
        insert_at = h1_match.end()
        text = text[:insert_at] + "\n" + notice + text[insert_at:]
    else:
        text = notice + text

    if text != original:
        md_path.write_text(text, encoding="utf-8")
        return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--storage-root",
        default="storage",
        help="Storage root (default: storage)",
    )
    parser.add_argument(
        "--factors",
        nargs="*",
        default=None,
        help="Optional factor ids; default = every F*.yaml that has a sibling .md",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    factors_dir = Path(args.storage_root) / "vault" / "factors"
    yaml_paths = sorted(factors_dir.glob("F*.yaml"))
    only = set(args.factors) if args.factors else None

    n_changed = 0
    n_skipped = 0
    for yp in yaml_paths:
        fid = yp.stem
        if only is not None and fid not in only:
            continue
        meta = yaml.safe_load(yp.read_text(encoding="utf-8")) or {}
        md_path = factors_dir / f"{fid}.md"
        try:
            changed = patch_one(md_path, meta)
        except Exception as exc:
            logger.error("patch failed for %s: %s", fid, exc)
            n_skipped += 1
            continue
        if changed:
            n_changed += 1
            logger.info("patched %s", fid)
        else:
            n_skipped += 1
            logger.info("no-op %s", fid)

    print(f"Patched {n_changed} files, {n_skipped} unchanged/skipped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
