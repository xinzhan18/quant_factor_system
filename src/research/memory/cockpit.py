"""LLM cockpit — derived situation + next-action recommendations.

The cockpit is the LLM's startup briefing: it answers three questions
from a single ``Read INDEX.md`` call:

1. **Where am I?** — state.phase, last_batch, round counter.
2. **What just happened?** — last batch outcome + last direction status.
3. **What should I do next?** — ordered recommendations derived from
   DAG rules, consolidation triggers, subagent verification, zero-admit
   streaks.

All inputs are computed deterministically from ``state.yaml`` +
``config.yaml`` + frontmatter scans, so ``refresh_index`` produces
byte-identical output when nothing changed. The cockpit does NOT
duplicate data already in ``snapshot`` (that's for row-level inspection);
it produces DIRECTIVES.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from research.storage.paths import StoragePaths
from research.storage.yaml_io import load_yaml

COCKPIT_BEGIN = "<!-- BEGIN COCKPIT -->"
COCKPIT_END = "<!-- END COCKPIT -->"

_FM_RE = re.compile(r"\A---\s*\n(?P<fm>.*?)\n---\s*\n?", re.DOTALL)
_NON_ACTIVE_DIR_STATUSES = {"dead", "merged", "archived"}
_ZERO_ADMIT_STREAK_THRESHOLD = 3


def _read_fm(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    m = _FM_RE.match(path.read_text(encoding="utf-8"))
    if m is None:
        return {}
    data = yaml.safe_load(m.group("fm"))
    return data if isinstance(data, dict) else {}


@dataclass
class CockpitAssessment:
    phase: str | None = None
    current_batch: str | None = None
    round_counter: int = 0
    last_batch: str | None = None
    last_batch_direction: str | None = None
    last_batch_admit: int = 0
    last_batch_reserve: int = 0
    last_batch_reject: int = 0
    last_batch_total: int = 0
    last_direction_status: str | None = None
    last_direction_rounds: int = 0
    last_direction_admits: int = 0
    rounds_since_consolidation: int = 0
    consolidation_triggers: list[str] = field(default_factory=list)
    empty_factor_mds: list[str] = field(default_factory=list)
    zero_admit_streak: int = 0
    active_directions: int = 0
    recommended_actions: list[str] = field(default_factory=list)


def _detect_empty_factor_mds(paths: StoragePaths) -> list[str]:
    """F*.yaml exists (Phase 4 committed) but F*.md empty or missing H1
    → ``/factor-report`` subagent silently failed."""
    offenders: list[str] = []
    if not paths.factors_dir.exists():
        return offenders
    for yp in sorted(paths.factors_dir.glob("F*.yaml")):
        data = load_yaml(yp) or {}
        if not isinstance(data, dict):
            continue
        if data.get("status") == "retired":
            continue
        md = yp.with_suffix(".md")
        if not md.exists():
            offenders.append(yp.stem)
            continue
        text = md.read_text(encoding="utf-8")
        if not text.strip() or f"# {yp.stem}" not in text:
            offenders.append(yp.stem)
    return offenders


def _compute_zero_admit_streak(paths: StoragePaths) -> int:
    """Count consecutive most-recent batches with admit_count == 0. Stops
    at the first batch with any admit. Reserved batches count as zero-admit."""
    if not paths.batches_dir.exists():
        return 0
    streak = 0
    for batch_dir in sorted(
        paths.batches_dir.iterdir(), key=lambda p: p.name, reverse=True
    ):
        if not batch_dir.is_dir():
            continue
        fm = _read_fm(batch_dir / "judge.md")
        if not fm:
            continue
        admit = int(fm.get("admit_count", 0) or 0)
        if admit > 0:
            break
        streak += 1
    return streak


def _count_active_directions(paths: StoragePaths) -> int:
    if not paths.directions_dir.exists():
        return 0
    count = 0
    for md in paths.directions_dir.glob("*.md"):
        fm = _read_fm(md)
        if fm.get("status") not in _NON_ACTIVE_DIR_STATUSES:
            count += 1
    return count


def _check_consolidation_triggers(
    paths: StoragePaths,
    config: dict[str, Any],
    rounds_since: int,
    active_dirs: int,
) -> list[str]:
    triggers: list[str] = []
    auto = (config.get("consolidation") or {}).get("auto_triggers") or {}
    th_rounds = int(auto.get("rounds_since_last", 10))
    th_lessons = int(auto.get("lessons_max_lines", 400))
    th_direction = int(auto.get("direction_max_lines", 500))
    th_active = int(auto.get("total_active_directions", 20))

    if rounds_since >= th_rounds:
        triggers.append(f"rounds_since_last={rounds_since} ≥ {th_rounds}")

    lessons = paths.vault_lessons_file
    if lessons.exists():
        n = sum(1 for _ in lessons.read_text(encoding="utf-8").splitlines())
        if n >= th_lessons:
            triggers.append(f"lessons.md={n} lines ≥ {th_lessons}")

    if paths.directions_dir.exists():
        for md in paths.directions_dir.glob("*.md"):
            n = sum(1 for _ in md.read_text(encoding="utf-8").splitlines())
            if n >= th_direction:
                triggers.append(f"{md.name}={n} lines ≥ {th_direction}")
                break

    if active_dirs >= th_active:
        triggers.append(f"active_directions={active_dirs} ≥ {th_active}")

    return triggers


_PHASE_RESUME = {
    "designed": "Phase 2 — `research execute {current_batch}`",
    "executing": "Phase 2 中断 — 重跑 `research execute {current_batch}` (幂等)",
    "judged": "Phase 3 — 调 `/factor-judge`",
    "archived": "Phase 4 — 调 `research archive {current_batch}` + dispatch `/factor-report`",
}


def _build_recommendations(a: CockpitAssessment) -> list[str]:
    """Ordered directives — highest priority first. Each line is what the
    LLM should execute next; first match wins for "where to go now".
    """
    recs: list[str] = []

    if a.phase and a.phase != "null":
        template = _PHASE_RESUME.get(a.phase, f"phase={a.phase} (按 DAG 续跑)")
        recs.append(
            f"🔄 **断点续跑**：state.phase=`{a.phase}` → "
            + template.format(current_batch=a.current_batch or "?")
        )
        return recs

    if a.empty_factor_mds:
        recs.append(
            f"⚠️ **修空报告**：{', '.join(a.empty_factor_mds)} 的 `.md` 为空或缺 H1 "
            "→ 对每个 F{id} 重新 dispatch `/factor-report` subagent"
        )

    if a.consolidation_triggers:
        recs.append(
            f"📚 **触发 consolidation**：{'; '.join(a.consolidation_triggers)} "
            "→ 先调 `/factor-consolidate`，再进 Phase 1"
        )

    calibration_armed = (
        a.zero_admit_streak >= _ZERO_ADMIT_STREAK_THRESHOLD
    )
    if calibration_armed:
        recs.append(
            f"🧪 **阈值校准**：连续 {a.zero_admit_streak} 批零 admit → "
            "先按 `lessons.md#Threshold Calibration` 扫 reserve 候选识别错杀；"
            "确认有库空间独立错杀 → 调阈；否则继续"
        )

    if not recs:
        if a.last_batch_admit > 0 and a.last_direction_status not in {
            "saturated",
            "dead",
            "merged",
            "archived",
        }:
            recs.append(
                f"▶️ **继续同方向**：`{a.last_batch_direction}` 上批 admit="
                f"{a.last_batch_admit}/{a.last_batch_total}，读 "
                f"`directions/{a.last_batch_direction}.md` 看 active threads 决定下一个 thread"
            )
        else:
            recs.append(
                "🆕 **选新方向**：`snapshot --recent 10` 从 `status=productive/exploring` "
                "里挑 rounds 最少；或读 `lessons.md` 的 Promising Unexplored"
            )

    recs.append(
        "🧭 **硬性前置**："
        "`research doctor`（drift 检测）→ `snapshot`（数据）→ "
        "读目标 `directions/{tag}.md` → 进 `/factor-idea`"
    )
    return recs


def assess(paths: StoragePaths, config: dict[str, Any] | None = None) -> CockpitAssessment:
    """Gather all cockpit inputs. Pure function of on-disk state."""
    a = CockpitAssessment()

    state = load_yaml(paths.state_file) or {}
    if isinstance(state, dict):
        raw_phase = state.get("current_batch_phase")
        a.phase = raw_phase if raw_phase else None
        a.current_batch = state.get("current_batch")
        a.round_counter = int(state.get("round", 0) or 0)
        a.last_batch = state.get("last_batch")
        a.rounds_since_consolidation = int(
            state.get("rounds_since_last_consolidation", 0) or 0
        )

    if a.last_batch:
        judge_fm = _read_fm(paths.batches_dir / a.last_batch / "judge.md")
        if judge_fm:
            a.last_batch_direction = judge_fm.get("direction")
            a.last_batch_admit = int(judge_fm.get("admit_count", 0) or 0)
            a.last_batch_reserve = int(judge_fm.get("reserve_count", 0) or 0)
            a.last_batch_reject = int(judge_fm.get("reject_count", 0) or 0)
            a.last_batch_total = int(judge_fm.get("candidate_count", 0) or 0)

    if a.last_batch_direction:
        dir_fm = _read_fm(paths.directions_dir / f"{a.last_batch_direction}.md")
        if dir_fm:
            a.last_direction_status = dir_fm.get("status")
            a.last_direction_rounds = int(dir_fm.get("rounds", 0) or 0)
            a.last_direction_admits = int(dir_fm.get("admits", 0) or 0)

    a.active_directions = _count_active_directions(paths)
    a.empty_factor_mds = _detect_empty_factor_mds(paths)
    a.zero_admit_streak = _compute_zero_admit_streak(paths)

    cfg = config if config is not None else (load_yaml(paths.config_file) or {})
    a.consolidation_triggers = _check_consolidation_triggers(
        paths, cfg, a.rounds_since_consolidation, a.active_directions
    )

    a.recommended_actions = _build_recommendations(a)
    return a


def render_cockpit_block(a: CockpitAssessment) -> str:
    """Render the cockpit markdown — sentinel-bounded, for embedding in INDEX."""
    lines = [COCKPIT_BEGIN, "", "> [!note]+ 🧭 LLM Cockpit"]
    phase_label = f"`{a.phase}`" if a.phase else "`null` (idle)"
    current = f"current_batch=`{a.current_batch}`" if a.current_batch else "no batch in flight"
    lines.append(
        f"> **状态** · round=**{a.round_counter}** · phase={phase_label} · {current}"
    )

    if a.last_batch:
        status_bit = (
            f" · direction.status=`{a.last_direction_status}`"
            if a.last_direction_status
            else ""
        )
        lines.append(
            f"> **上一批** · [[batches/{a.last_batch}/judge|{a.last_batch}]] "
            f"→ [[directions/{a.last_batch_direction}]] · "
            f"admit=**{a.last_batch_admit}**/{a.last_batch_total} "
            f"(reserve={a.last_batch_reserve}, reject={a.last_batch_reject}){status_bit}"
        )
    else:
        lines.append("> **上一批** · —（全新 vault）")

    streak_bit = (
        f" · zero-admit streak=**{a.zero_admit_streak}**"
        if a.zero_admit_streak > 0
        else ""
    )
    lines.append(
        f"> **健康** · rounds_since_consolidation=**{a.rounds_since_consolidation}** "
        f"· active_directions=**{a.active_directions}**{streak_bit}"
    )

    warnings: list[str] = []
    if a.empty_factor_mds:
        warnings.append(f"空 factor.md: {', '.join(a.empty_factor_mds)}")
    if a.consolidation_triggers:
        warnings.append("consolidation 触发: " + "; ".join(a.consolidation_triggers))
    if warnings:
        lines.append("> **⚠️ 预警** · " + " · ".join(warnings))

    lines.append(">")
    lines.append("> **🎯 下一步（按优先级）**")
    for i, rec in enumerate(a.recommended_actions, 1):
        lines.append(f"> {i}. {rec}")
    lines.append("")
    lines.append(COCKPIT_END)
    return "\n".join(lines)


def render(paths: StoragePaths, config: dict[str, Any] | None = None) -> str:
    """One-shot: assess + render. Exposed for tests / CLI."""
    return render_cockpit_block(assess(paths, config))
