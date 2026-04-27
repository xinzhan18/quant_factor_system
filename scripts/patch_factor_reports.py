#!/usr/bin/env python3
"""Surgically patch ``vault/factors/F*.md`` for the recompute v1 results.

Strategy: preserve the rich LLM narrative; prepend an authoritative
"Recompute v1" notice block right after the title. Update frontmatter
fields that drive INDEX/dataview queries.

Inserts:
* Frontmatter updates: status, ic_mean_validation, ic_ir_validation,
  monotonicity_validation, primary_universe, csi300_pass.
* "Recompute v1 Notice" callout: status badge + delta vs old metrics +
  multi-universe table + verdict pointer.

Idempotent: re-running re-renders the notice block in place.
"""

from __future__ import annotations

import argparse
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from research.storage.paths import StoragePaths
from research.storage.yaml_io import load_yaml

logger = logging.getLogger(__name__)


NOTICE_BEGIN = "<!-- BEGIN recompute_v1_notice -->"
NOTICE_END = "<!-- END recompute_v1_notice -->"

STATUS_ICON = {
    "active": "✅",
    "reserve": "⚠️",
    "retired": "⛔",
}


def _fmt_num(value: Any, digits: int = 4) -> str:
    if value is None:
        return "—"
    try:
        f = float(value)
    except (TypeError, ValueError):
        return str(value)
    return f"{f:.{digits}f}"


def _delta(new: float | None, old: float | None) -> str:
    if new is None or old is None:
        return ""
    diff = float(new) - float(old)
    return f" ({diff:+.4f})"


def _build_notice(
    record: dict[str, Any],
    old_metrics: dict[str, Any],
) -> str:
    fid = record["factor_id"]
    status = record.get("status", "active")
    icon = STATUS_ICON.get(status, "•")
    rev = record.get("recompute_reverdict") or {}
    primary = record.get("primary_universe") or "csi1000"
    primary_metrics = record.get("validation_metrics") or {}
    grid = record.get("validation_metrics_by_universe") or {}
    robust = record.get("universe_robustness") or {}
    prov = record.get("recompute_provenance") or {}

    callout_kind = {
        "active": "info",
        "reserve": "warning",
        "retired": "danger",
    }.get(status, "info")

    header = (
        f"> [!{callout_kind}] {icon} Recompute v1 — status: **{status}** "
        f"(primary universe: `{primary}`)"
    )
    body_lines = [header]

    if rev:
        body_lines.append(
            f"> **Reverdict reason**: {rev.get('reason', '—')}\n"
            f"> _Transitioned at {rev.get('transitioned_at', '—')} "
            f"(audit run: `{prov.get('run_name', '—')}`)._"
        )
    else:
        body_lines.append(
            f"> Primary universe metrics still pass CP01 floors. Audit run: "
            f"`{prov.get('run_name', '—')}`."
        )

    # Old vs new headline metrics
    old_ic_ir = old_metrics.get("ic_ir")
    old_mono = old_metrics.get("monotonicity")
    old_ic_mean = old_metrics.get("ic_mean")

    body_lines.append("")
    body_lines.append(
        f"> | Metric | Old (`all_tradable`, no ST mask) | New (`{primary}`, with ST mask) |"
    )
    body_lines.append("> |---|---|---|")
    body_lines.append(
        f"> | IC mean | {_fmt_num(old_ic_mean)} | {_fmt_num(primary_metrics.get('ic_mean'))}{_delta(primary_metrics.get('ic_mean'), old_ic_mean)} |"
    )
    body_lines.append(
        f"> | ICIR | {_fmt_num(old_ic_ir)} | {_fmt_num(primary_metrics.get('ic_ir'))}{_delta(primary_metrics.get('ic_ir'), old_ic_ir)} |"
    )
    body_lines.append(
        f"> | Monotonicity | {_fmt_num(old_mono)} | {_fmt_num(primary_metrics.get('monotonicity'))}{_delta(primary_metrics.get('monotonicity'), old_mono)} |"
    )
    body_lines.append(
        f"> | L/S Sharpe | — | {_fmt_num(primary_metrics.get('long_short_sharpe'))} |"
    )
    body_lines.append(
        f"> | L/S t-stat | — | {_fmt_num(primary_metrics.get('long_short_tstat'))} |"
    )

    body_lines.append("")
    body_lines.append("> ### Multi-Universe Evaluation (basic metrics)")
    body_lines.append("> | Universe | Coverage | IC mean | ICIR | Mono | L/S Sharpe |")
    body_lines.append("> |---|---|---|---|---|---|")
    for uname in ("all_tradable", "csi300", "csi1000"):
        blk = grid.get(uname) or {}
        if "error" in blk:
            body_lines.append(f"> | {uname} | _error_ | — | — | — | — |")
            continue
        is_primary = uname == primary
        marker = "**" if is_primary else ""
        body_lines.append(
            f"> | {marker}{uname}{marker} | {_fmt_num(blk.get('coverage'), 3)} | "
            f"{_fmt_num(blk.get('ic_mean'))} | "
            f"{_fmt_num(blk.get('ic_ir'))} | {_fmt_num(blk.get('monotonicity'))} | "
            f"{_fmt_num(blk.get('long_short_sharpe'))} |"
        )

    csi300_pass = robust.get("csi300_passes_admission_floor")
    csi300_label = "✅ pass" if csi300_pass else "❌ fail"
    body_lines.append("")
    body_lines.append(
        f"> **csi300 robustness**: {csi300_label} "
        f"(floor: `|ICIR|≥0.15 ∧ |mono|≥0.6`). "
        f"icir_robustness_ratio = {_fmt_num(robust.get('icir_robustness_ratio'))}."
    )

    body_lines.append("")
    body_lines.append(
        f"> _下方原始 narrative 基于旧 metric (`all_tradable`, no ST mask)，"
        f"以新 metric 为准，narrative 仅供机制解读参考。_"
    )
    body_lines.append("")
    body_lines.append(
        f"> See [[_meta/recompute_v1_reverdict|Recompute v1 reverdict report]] for full context."
    )

    return "\n".join([NOTICE_BEGIN, "\n".join(body_lines), NOTICE_END])


_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def _split_frontmatter(text: str) -> tuple[str, str]:
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return "", text
    return m.group(0), text[m.end():]


def _patch_frontmatter(fm: str, record: dict[str, Any]) -> str:
    """Update specific frontmatter keys without disturbing the rest."""
    primary = record.get("validation_metrics") or {}
    robust = record.get("universe_robustness") or {}
    updates = {
        "status": record.get("status", "active"),
        "primary_universe": record.get("primary_universe", "csi1000"),
        "ic_mean_validation": primary.get("ic_mean"),
        "ic_ir_validation": primary.get("ic_ir"),
        "monotonicity_validation": primary.get("monotonicity"),
        "csi300_passes_floor": robust.get("csi300_passes_admission_floor"),
    }
    lines = fm.split("\n")
    out: list[str] = []
    seen: set[str] = set()
    for line in lines:
        m = re.match(r"^(\w+):\s*(.*)$", line)
        if m and m.group(1) in updates:
            key = m.group(1)
            value = updates[key]
            seen.add(key)
            out.append(f"{key}: {_fmt_yaml_scalar(value)}")
        else:
            out.append(line)
    # Insert keys not yet present (before the closing ---)
    closing_idx = len(out) - 2 if out and out[-1] == "" and out[-2] == "---" else len(out) - 1
    for key, value in updates.items():
        if key in seen:
            continue
        out.insert(closing_idx, f"{key}: {_fmt_yaml_scalar(value)}")
        closing_idx += 1
    return "\n".join(out)


def _fmt_yaml_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return f"{value}"
    return str(value)


def _strip_existing_notice(body: str) -> str:
    pattern = re.compile(
        re.escape(NOTICE_BEGIN) + r".*?" + re.escape(NOTICE_END) + r"\n*",
        re.DOTALL,
    )
    return pattern.sub("", body)


def patch_report(
    md_path: Path,
    yaml_record: dict[str, Any],
    audit_record: dict[str, Any],
) -> None:
    text = md_path.read_text(encoding="utf-8")
    fm, body = _split_frontmatter(text)
    if not fm:
        logger.warning("%s: no frontmatter found, skipping", md_path.name)
        return
    fm_new = _patch_frontmatter(fm, yaml_record)
    body = _strip_existing_notice(body)

    notice = _build_notice(yaml_record, audit_record.get("old_validation_metrics") or {})

    title_match = re.search(r"^(# .+?)\n", body, re.MULTILINE)
    if title_match:
        insert_at = title_match.end()
        body = body[:insert_at] + "\n" + notice + "\n" + body[insert_at:]
    else:
        body = notice + "\n\n" + body

    md_path.write_text(fm_new + body, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-name", default="tradable_mask_v1_st")
    parser.add_argument("--factors", nargs="*", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    paths = StoragePaths()
    audit_dir = paths.cache_dir / "recompute_audit" / args.run_name

    targets = (
        [paths.factor_yaml_file(fid).with_suffix(".md") for fid in args.factors]
        if args.factors
        else sorted(paths.factors_dir.glob("F*.md"))
    )

    for md_path in targets:
        fid = md_path.stem
        yaml_path = md_path.with_suffix(".yaml")
        audit_path = audit_dir / f"{fid}.yaml"
        if not yaml_path.exists() or not audit_path.exists():
            logger.warning("missing yaml/audit for %s — skipped", fid)
            continue
        record = load_yaml(yaml_path) or {}
        audit_record = load_yaml(audit_path) or {}
        if args.dry_run:
            logger.info("[dry-run] would patch %s", md_path.name)
            continue
        patch_report(md_path, record, audit_record)
        logger.info("patched %s", md_path.name)


if __name__ == "__main__":
    main()
