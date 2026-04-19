"""``research audit reserves`` — reassess historical reserve candidates.

Walks every ``batches/batch_*/`` directory, reads each candidate's past
verdict from ``judge.md`` frontmatter, and for every candidate whose
verdict is ``reserve``:

1. **Re-evaluate hard gates** under the **current** ``config.yaml`` —
   picks up magnitude-gated ``mono_sign_flip``, any relaxed thresholds,
   blacklist changes, etc.
2. **Compare CP04 alpha_survival** against the **direction-aware**
   ``alpha_surv_min`` floor, now resolved per direction.
3. **Flag "flip candidates"** — reserves whose current gate status +
   structural indicators suggest they would be admitted under today's
   rubric (needs LLM re-judgment to finalize).

Emits a single markdown audit report at
``storage/vault/_meta/reserve_audit_{timestamp}.md`` listing every
reserve, its old/new gate status, and the actionable next step.

**Does not mutate state** — no verdict rewrites, no admission. The LLM
(via ``/factor-judge`` re-invocation) remains the only authority on
admit/reject per R2. This command's output is the packet that drives
a batch of re-judgment runs.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from research.checkpoints.hard_gates import HardGatesConfig, evaluate_hard_gates
from research.checkpoints.hints import resolve_alpha_surv_min
from research.storage.paths import StoragePaths
from research.storage.yaml_io import load_yaml, load_yaml_unsafe


# ``judge.md`` frontmatter has candidates laid out as either compact YAML::
#     - {candidate_id: C001, verdict: admit, factor_name: amount_cv_10}
# or expanded::
#     - candidate_id: C001
#       verdict: reserve
_CAND_LINE_RE = re.compile(
    r"candidate_id:\s*(C\d+).*?verdict:\s*(\w+)", re.DOTALL
)


@dataclass
class ReserveRow:
    batch_id: str
    direction: str
    candidate_id: str
    expression: str
    old_verdict: str  # always "reserve" here but kept for clarity
    old_hard_gate_passed: bool | None
    new_hard_gate_passed: bool
    new_hard_gate_reasons: list[str]
    ic_oos: float | None
    icir_oos: float | None
    ls_tstat_oos: float | None
    alpha_survival_ratio: float | None
    alpha_surv_min_threshold: float
    alpha_survival_tier: str  # clean | borderline | poor (under direction threshold)
    max_lib_corr: float | None
    incremental_ic: float | None
    mono_oos: float | None
    sign_consistency: float | None
    suggested_action: str = "re-judge"
    # ``suggested_action``:
    #   - "re-judge" → flip candidate (gates now pass + alpha_surv clean/border)
    #   - "still-reserve" → gates now pass but CP04 still poor
    #   - "drop" → gates now reject (should have been rejected at commit time)
    #   - "rejudge-cp-change" → gate status unchanged but CP04 tier shifted
    flags: list[str] = field(default_factory=list)


def _parse_judge_verdicts(judge_md: Path) -> dict[str, dict[str, str]]:
    """Parse ``judge.md`` frontmatter into ``{cid: {verdict, factor_name?}}``.

    Tolerates both the compact flow-style list and the block-style list.
    Ignores anything that's not a candidate row.
    """
    if not judge_md.exists():
        return {}
    text = judge_md.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}
    fm_text = m.group(1)
    # Safe for our narrow schema — no unsafe tags in judge frontmatter.
    try:
        import yaml as _yaml
        fm = _yaml.safe_load(fm_text) or {}
    except Exception:
        return {}
    out: dict[str, dict[str, str]] = {}
    for c in (fm.get("candidates") or []):
        if not isinstance(c, dict):
            continue
        cid = c.get("candidate_id")
        if not cid:
            continue
        out[str(cid)] = {
            "verdict": str(c.get("verdict") or ""),
            "factor_name": str(c.get("factor_name") or "") or "",
            "hard_gate_reason": str(c.get("hard_gate_reason") or "") or "",
        }
    return out


def _find_candidate(result: dict[str, Any], cid: str) -> dict[str, Any] | None:
    for c in result.get("candidates", []) or []:
        if c.get("candidate_id") == cid:
            return c
    return None


def _classify_alpha_surv(ratio: float | None, threshold: float) -> str:
    if ratio is None:
        return "unknown"
    band = 0.10  # width of the "borderline" band above the threshold
    if ratio >= threshold + band:
        return "clean"
    if ratio >= threshold:
        return "borderline"
    return "poor"


def _new_hard_gate_status(
    result: dict[str, Any], cid: str, hg_cfg: HardGatesConfig
) -> tuple[bool, list[str]]:
    gates = evaluate_hard_gates(result, hg_cfg)
    for g in gates:
        if g.candidate_id == cid:
            return g.passed, list(g.reasons)
    return False, ["candidate not found in result.yaml"]


def _suggest_action(
    new_passed: bool,
    alpha_tier: str,
    mono_oos: float | None,
    ic_oos: float | None,
) -> tuple[str, list[str]]:
    flags: list[str] = []
    if not new_passed:
        return "drop", ["gates now reject under current thresholds"]
    # Gates pass. What does CP04 say under direction-aware threshold?
    if alpha_tier == "clean":
        if ic_oos is not None and abs(ic_oos) >= 0.015:
            flags.append("ic_oos_clean")
        if mono_oos is not None and abs(mono_oos) >= 0.8:
            flags.append("mono_strong")
        return "re-judge", flags
    if alpha_tier == "borderline":
        flags.append("alpha_surv_borderline")
        return "re-judge", flags
    if alpha_tier == "poor":
        flags.append("alpha_surv_poor_under_threshold")
        return "still-reserve", flags
    return "re-judge", flags


def collect_reserves(paths: StoragePaths) -> list[ReserveRow]:
    """Scan all batches for reserve candidates and re-evaluate each."""
    cfg = load_yaml(paths.config_file) or {}
    thresholds = cfg.get("thresholds") or {}
    hg_cfg = HardGatesConfig.from_config_dict(thresholds.get("hard_gates") or {})

    rows: list[ReserveRow] = []
    batches_dir = paths.batches_dir
    if not batches_dir.exists():
        return rows
    for batch_dir in sorted(batches_dir.iterdir()):
        if not batch_dir.is_dir():
            continue
        result_file = batch_dir / "result.yaml"
        judge_file = batch_dir / "judge.md"
        manifest_file = batch_dir / "manifest.yaml"
        if not (result_file.exists() and judge_file.exists()):
            continue

        manifest = load_yaml(manifest_file) or {}
        direction = manifest.get("direction") or "unknown"
        verdicts = _parse_judge_verdicts(judge_file)
        result = load_yaml_unsafe(result_file) or {}

        alpha_surv_min = resolve_alpha_surv_min(direction, thresholds)

        for cid, v in verdicts.items():
            if v.get("verdict") != "reserve":
                continue
            cand = _find_candidate(result, cid)
            if cand is None:
                continue
            new_passed, new_reasons = _new_hard_gate_status(result, cid, hg_cfg)

            ic = cand.get("ic") or {}
            val_ic = ic.get("validation") or {}
            quintile = cand.get("quintile") or {}
            q_val = quintile.get("validation") or {}
            ls_val = (quintile.get("ls_stats") or {}).get("validation") or {}
            barra = cand.get("barra") or {}
            uniq = cand.get("uniqueness") or {}
            stability = cand.get("stability") or {}
            split = stability.get("split_stability") or {}

            asr = barra.get("alpha_survival_ratio")
            alpha_tier = _classify_alpha_surv(asr, alpha_surv_min)

            action, flags = _suggest_action(
                new_passed=new_passed,
                alpha_tier=alpha_tier,
                mono_oos=q_val.get("monotonicity"),
                ic_oos=val_ic.get("ic_mean"),
            )

            rows.append(
                ReserveRow(
                    batch_id=batch_dir.name,
                    direction=direction,
                    candidate_id=cid,
                    expression=str(cand.get("expression") or "")[:120],
                    old_verdict="reserve",
                    old_hard_gate_passed=None,  # pre-hint files not always kept
                    new_hard_gate_passed=new_passed,
                    new_hard_gate_reasons=new_reasons,
                    ic_oos=val_ic.get("ic_mean"),
                    icir_oos=val_ic.get("ic_ir"),
                    ls_tstat_oos=ls_val.get("tstat"),
                    alpha_survival_ratio=asr,
                    alpha_surv_min_threshold=alpha_surv_min,
                    alpha_survival_tier=alpha_tier,
                    max_lib_corr=uniq.get("max_lib_corr"),
                    incremental_ic=uniq.get("incremental_ic"),
                    mono_oos=q_val.get("monotonicity"),
                    sign_consistency=split.get("sign_consistency"),
                    suggested_action=action,
                    flags=flags,
                )
            )
    return rows


def _fmt(v: Any, digits: int = 3) -> str:
    if v is None:
        return "—"
    if isinstance(v, float):
        return f"{v:.{digits}f}"
    return str(v)


def render_report(rows: list[ReserveRow]) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out: list[str] = []
    out.append(f"# Reserve Re-Judgement Audit — {now}")
    out.append("")
    out.append(
        f"**Reserves scanned**: {len(rows)} across "
        f"{len({r.batch_id for r in rows})} batches"
    )
    by_action: dict[str, int] = {}
    for r in rows:
        by_action[r.suggested_action] = by_action.get(r.suggested_action, 0) + 1
    out.append(
        "**Actions**: "
        + " · ".join(f"{k}={v}" for k, v in sorted(by_action.items()))
    )
    out.append("")
    out.append("## Flip Candidates (suggest re-judge → admit/reserve)")
    out.append("")
    out.append(
        "| Batch | C | Direction | IC_OOS | ICIR | ls_t | Mono | alpha_surv (tier@threshold) | max_corr | incr_ic | flags |"
    )
    out.append(
        "|---|---|---|---|---|---|---|---|---|---|---|"
    )
    flip_rows = [r for r in rows if r.suggested_action == "re-judge"]
    for r in sorted(flip_rows, key=lambda x: (x.batch_id, x.candidate_id)):
        alpha_col = (
            f"{_fmt(r.alpha_survival_ratio)} "
            f"({r.alpha_survival_tier}@{r.alpha_surv_min_threshold:.2f})"
        )
        out.append(
            "| "
            + " | ".join(
                [
                    r.batch_id,
                    r.candidate_id,
                    r.direction,
                    _fmt(r.ic_oos, 4),
                    _fmt(r.icir_oos, 3),
                    _fmt(r.ls_tstat_oos, 2),
                    _fmt(r.mono_oos, 2),
                    alpha_col,
                    _fmt(r.max_lib_corr, 3),
                    _fmt(r.incremental_ic, 4),
                    ", ".join(r.flags) or "—",
                ]
            )
            + " |"
        )
    out.append("")
    out.append("## Still-Reserve (CP04 now explicitly poor under direction threshold)")
    out.append("")
    still = [r for r in rows if r.suggested_action == "still-reserve"]
    for r in sorted(still, key=lambda x: (x.batch_id, x.candidate_id)):
        out.append(
            f"- **{r.batch_id}/{r.candidate_id}** ({r.direction}) — "
            f"alpha_surv={_fmt(r.alpha_survival_ratio)} "
            f"< threshold={r.alpha_surv_min_threshold:.2f}; "
            f"IC={_fmt(r.ic_oos, 4)}, mono={_fmt(r.mono_oos, 2)}"
        )
    out.append("")
    out.append("## Drops (current hard-gates now reject)")
    out.append("")
    drops = [r for r in rows if r.suggested_action == "drop"]
    for r in sorted(drops, key=lambda x: (x.batch_id, x.candidate_id)):
        out.append(
            f"- **{r.batch_id}/{r.candidate_id}** ({r.direction}) — "
            + "; ".join(r.new_hard_gate_reasons)
        )
    out.append("")
    out.append("## Expression Reference")
    out.append("")
    for r in sorted(rows, key=lambda x: (x.batch_id, x.candidate_id)):
        out.append(f"- `{r.batch_id}/{r.candidate_id}` → `{r.expression}`")
    out.append("")
    return "\n".join(out) + "\n"


def _run_audit_reserves(args: argparse.Namespace) -> None:
    storage_root = Path(getattr(args, "storage_root", "storage"))
    paths = StoragePaths(storage_root)
    rows = collect_reserves(paths)
    report = render_report(rows)

    if args.dry_run:
        print(report)
        return

    out_dir = paths.vault_dir / "_meta"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = out_dir / f"reserve_audit_{stamp}.md"
    out_path.write_text(report, encoding="utf-8")
    print(f"Wrote {out_path}")
    print(f"  reserves={len(rows)}  "
          f"flips={sum(1 for r in rows if r.suggested_action == 'rejudge-cp-change' or r.suggested_action == 're-judge')}")


def register_audit_reserves(audit_sub: argparse._SubParsersAction) -> None:
    """Attach ``research audit reserves`` to the ``audit`` subparser group."""
    p = audit_sub.add_parser(
        "reserves",
        help="Re-evaluate historical reserve candidates under current thresholds",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print report to stdout instead of writing to storage/vault/_meta/",
    )
    p.set_defaults(func=_run_audit_reserves)
