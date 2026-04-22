"""Top-level CLI router for ``python -m research``.

Subcommands map to the 5-phase architecture + utility commands:

    research mine [--once] [--direction TAG] [--dsl-only]
    research execute BATCH_ID
    research judge BATCH_ID pre-hint
    research judge BATCH_ID audit
    research archive BATCH_ID
    research consolidate [--target TARGET] [--dry-run]
    research commit BATCH_ID
    research commit-report FACTOR_ID
    research cache refresh {all|market_daily|barra_factors|universes}
    research cache status
    research audit mt-budget [--direction TAG]
    research audit reports|links|state|failures|duplicates
    research state [set KEY VALUE | rollback]
    research holdout-review [--factor FID]
    research factor retire FID
    research report-pack FID
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="research",
        description="Factor research CLI — 5-phase autonomous mining loop",
    )
    sub = parser.add_subparsers(dest="command")

    # ── mine (Phase 1-5 loop) ─────────────────────────────────────────
    mine_p = sub.add_parser("mine", help="Run autonomous mine loop")
    mine_p.add_argument("--once", action="store_true", help="Run exactly one batch")
    mine_p.add_argument("--direction", type=str, default=None, help="Force direction")
    mine_p.add_argument("--dsl-only", action="store_true", help="Reject Python candidates")

    # ── single-phase CLIs ─────────────────────────────────────────────
    exec_p = sub.add_parser("execute", help="Phase 2 — vectorized compute")
    exec_p.add_argument("batch_id")

    judge_p = sub.add_parser("judge", help="Phase 3 — checkpoint judge")
    judge_p.add_argument("batch_id", nargs="?", default=None)
    judge_p.add_argument("judge_sub", nargs="?", default=None,
                         choices=["pre-hint", "audit"],
                         help="Sub-step: pre-hint (write _hints.yaml) or audit")

    archive_p = sub.add_parser("archive", help="Phase 4 — factor archive + commit")
    archive_p.add_argument("batch_id")

    cons_p = sub.add_parser("consolidate", help="Phase 5 — memory consolidation")
    cons_p.add_argument("--target", type=str, default=None,
                        help="lessons | directions | direction:{tag}")
    cons_p.add_argument("--dry-run", action="store_true")

    # ── commit ────────────────────────────────────────────────────────
    commit_p = sub.add_parser("commit", help="Git commit for a batch")
    commit_p.add_argument("batch_id")

    commitr_p = sub.add_parser("commit-report", help="Git commit for factor report")
    commitr_p.add_argument("factor_id")

    # ── cache ─────────────────────────────────────────────────────────
    cache_p = sub.add_parser("cache", help="Cache management")
    cache_sub = cache_p.add_subparsers(dest="cache_cmd", required=True)

    ref_p = cache_sub.add_parser("refresh", help="Rebuild a cache layer")
    ref_p.add_argument("target", choices=["all", "market_daily", "barra_factors", "universes"])

    cache_sub.add_parser("status", help="Print cache sizes and staleness")
    cache_sub.add_parser("purge", help="Delete all factor_values cache")

    # ── audit ─────────────────────────────────────────────────────────
    from research.cli.audit import register_audit_subcommand
    register_audit_subcommand(sub)

    # ── state ─────────────────────────────────────────────────────────
    state_p = sub.add_parser("state", help="View or modify system state")
    state_p.add_argument(
        "state_action",
        nargs="?",
        default=None,
        choices=["set", "rollback", "reset", "next-batch-id", None],
    )
    state_p.add_argument("key", nargs="?")
    state_p.add_argument("value", nargs="?")
    state_p.add_argument(
        "--confirm",
        action="store_true",
        help="Required for destructive actions (e.g. reset).",
    )

    # ── doctor (health check + reconciliation) ────────────────────────
    sub.add_parser(
        "doctor",
        help="Cross-check state.yaml ↔ vault consistency, print fix recipe",
    )

    # ── memory (LLM-visible markdown maintenance) ─────────────────────
    mem_p = sub.add_parser("memory", help="Vault memory maintenance")
    mem_sub = mem_p.add_subparsers(dest="memory_cmd", required=True)
    mem_sub.add_parser(
        "refresh-index", help="Regenerate INDEX.md lower auto-section"
    )
    snap_p = mem_sub.add_parser(
        "snapshot",
        help="Dump aggregated markdown (directions/factors/batches) — "
        "LLM-friendly, mirrors Bases filter logic",
    )
    snap_p.add_argument(
        "--section",
        choices=("all", "directions", "factors", "batches"),
        default="all",
        help="Which section(s) to render (default: all)",
    )
    snap_p.add_argument(
        "--recent",
        type=int,
        default=None,
        help="For batches section: cap to last N entries (default: unlimited)",
    )

    # ── phase1 (freeze manifest) ──────────────────────────────────────
    p1_p = sub.add_parser("phase1", help="Phase 1 START+DESIGN helpers")
    p1_sub = p1_p.add_subparsers(dest="phase1_cmd", required=True)
    fz_p = p1_sub.add_parser(
        "freeze",
        help="Freeze manifest from a YAML spec (allocate batch_id, "
        "begin_batch, refresh INDEX)",
    )
    fz_p.add_argument(
        "spec",
        help="Path to a YAML file: {direction, batch_goal, "
        "active_threads_referenced, candidates}",
    )

    # ── holdout ───────────────────────────────────────────────────────
    ho_p = sub.add_parser("holdout-review", help="Run holdout review (isolated)")
    ho_p.add_argument("--factor", type=str, default=None,
                      help="Single factor id, or all active")

    # ── factor management ─────────────────────────────────────────────
    fac_p = sub.add_parser("factor", help="Factor lifecycle")
    fac_sub = fac_p.add_subparsers(dest="factor_cmd", required=True)
    ret_p = fac_sub.add_parser("retire", help="Retire a factor")
    ret_p.add_argument("factor_id")

    # ── report-pack (standalone, for /factor-report) ──────────────────
    rp_p = sub.add_parser("report-pack", help="Generate report packet for a factor")
    rp_p.add_argument("factor_id")

    # ── report cleanup-packets ────────────────────────────────────────
    rc_p = sub.add_parser(
        "report",
        help="Report packet / factor.md utilities",
    )
    rc_sub = rc_p.add_subparsers(dest="report_cmd", required=True)
    rc_cp = rc_sub.add_parser(
        "cleanup-packets",
        help="Delete _packets/report_packet_F{id}.md once factor.md exists",
    )
    rc_cp.add_argument(
        "--dry-run", action="store_true",
        help="Show what would be deleted without touching anything",
    )
    rc_cp.add_argument(
        "--skip-batch", default=None,
        help="Leave this batch's packets intact (e.g. batch currently dispatching subagents)",
    )

    # ── parse + dispatch ──────────────────────────────────────────────
    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        sys.exit(0)

    _dispatch(args)


# ─────────────────────────────────────────────────────────────────────
# Dispatcher — lazy imports so startup is fast
# ─────────────────────────────────────────────────────────────────────

def _dispatch(args: argparse.Namespace) -> None:
    cmd = args.command

    if cmd == "mine":
        _cmd_mine(args)
    elif cmd == "execute":
        _cmd_execute(args)
    elif cmd == "judge":
        _cmd_judge(args)
    elif cmd == "archive":
        _cmd_archive(args)
    elif cmd == "consolidate":
        _cmd_consolidate(args)
    elif cmd == "commit":
        _cmd_commit(args)
    elif cmd == "commit-report":
        _cmd_commit_report(args)
    elif cmd == "cache":
        _cmd_cache(args)
    elif cmd == "audit":
        # Handled by audit.py's own dispatch
        from research.cli.audit import dispatch_audit
        dispatch_audit(args)
    elif cmd == "state":
        _cmd_state(args)
    elif cmd == "doctor":
        _cmd_doctor(args)
    elif cmd == "memory":
        _cmd_memory(args)
    elif cmd == "phase1":
        _cmd_phase1(args)
    elif cmd == "holdout-review":
        _cmd_holdout(args)
    elif cmd == "factor":
        _cmd_factor(args)
    elif cmd == "report-pack":
        _cmd_report_pack(args)
    elif cmd == "report":
        _cmd_report(args)
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)


# ─────────────────────────────────────────────────────────────────────
# Command handlers (thin wrappers around phase modules)
# ─────────────────────────────────────────────────────────────────────

def _cmd_mine(args: argparse.Namespace) -> None:
    print(
        f"mine: once={args.once} direction={args.direction} "
        f"dsl_only={args.dsl_only}"
    )
    print("(Not yet wired to LLM callbacks — run via /factor-mine skill)")


def _cmd_execute(args: argparse.Namespace) -> None:
    """Phase 2 EXECUTE — loads data via data_bridge, runs vectorized compute."""
    from research.compute.data_bridge import build_phase2_inputs, init_qlib
    from research.phases.phase2_execute import run_phase2
    from research.storage.paths import StoragePaths
    from research.storage.yaml_io import load_yaml
    from research.storage.state import StateFile

    paths = StoragePaths()
    batch_id = args.batch_id
    manifest = load_yaml(paths.batch_manifest_file(batch_id))
    if not manifest:
        print(f"manifest.yaml not found for {batch_id}", file=sys.stderr)
        sys.exit(1)

    config = load_yaml(paths.config_file) or {}
    state_file = StateFile(paths.state_file)
    state_file.transition_phase("executing")

    phase2_inputs = build_phase2_inputs(batch_id, manifest, paths, config)
    result = run_phase2(phase2_inputs, paths.batch_result_file(batch_id))

    state_file.transition_phase("judged")
    print(f"Phase 2 done: {result['n_ok']}/{result['n_candidates']} ok, {result['n_errors']} errors")


def _cmd_judge(args: argparse.Namespace) -> None:
    from research.storage.paths import StoragePaths
    from research.storage.yaml_io import load_yaml, load_yaml_unsafe

    paths = StoragePaths()
    batch_id = args.batch_id
    judge_sub = args.judge_sub

    if judge_sub == "pre-hint":
        from research.checkpoints.hard_gates import HardGatesConfig
        from research.checkpoints.mt_budget import MtBudgetConfig
        from research.phases.phase3_judge import (
            Phase3PreHintInputs,
            run_phase3_prehint,
        )

        manifest = load_yaml(paths.batch_manifest_file(batch_id))
        direction = manifest.get("direction", "unknown")

        config = load_yaml(paths.config_file) or {}
        mt_raw = config.get("thresholds", {}).get("mt_budget", {})
        weights = mt_raw.pop("weights", {})
        mt_flat = {**mt_raw}
        for k, v in weights.items():
            mt_flat[f"weight_{k}"] = v
        mt_flat.pop("adjusted_strength_discount", None)  # not in MtBudgetConfig
        mt_cfg = MtBudgetConfig(**mt_flat)

        hg_raw = config.get("thresholds", {}).get("hard_gates", {})
        hg_cfg = HardGatesConfig.from_config_dict(hg_raw)

        inputs = Phase3PreHintInputs(
            batch_id=batch_id,
            direction=direction,
            batch_dir=paths.batch_dir(batch_id),
            batches_root=paths.batches_dir,
            hints_path=paths.batch_hints_file(batch_id),
            factors_dir=paths.factors_dir,
            hard_gates_config=hg_cfg,
            mt_budget_config=mt_cfg,
        )
        result = run_phase3_prehint(inputs)
        n_cands = len(result.hints["per_candidate"])
        n_fail = sum(
            1 for e in result.hints["per_candidate"].values()
            if not e.get("hard_gate", {}).get("passed")
        )
        print(
            f"Wrote {result.hints_path} ({n_cands} candidates, "
            f"{n_fail} hard-gate fail)"
        )

    elif judge_sub == "audit":
        from research.checkpoints.audit import JudgeAuditError, audit_batch_judge

        hints_path = paths.batch_hints_file(batch_id)
        if not hints_path.exists():
            print(
                f"Audit FAILED: _hints.yaml missing at {hints_path} — run 'judge pre-hint' first",
                file=sys.stderr,
            )
            sys.exit(1)

        result = load_yaml_unsafe(paths.batch_result_file(batch_id))
        hints = load_yaml(hints_path)
        manifest = load_yaml(paths.batch_manifest_file(batch_id))
        direction = manifest.get("direction", "unknown")
        try:
            parsed = audit_batch_judge(
                paths.batch_dir(batch_id),
                result,
                hints,
                direction_path=paths.direction_file(direction),
                index_path=paths.vault_index_file,
            )
            n = len(parsed.candidates)
            print(f"Audit PASSED: {n} candidate md files + judge.md verified")
        except JudgeAuditError as exc:
            print(f"Audit FAILED: {exc}", file=sys.stderr)
            sys.exit(1)

    else:
        print(f"judge: batch_id={batch_id}")
        print(
            "Run 'judge pre-hint' first, then write candidates/*.md + judge.md, "
            "then 'judge audit'."
        )


def _cmd_archive(args: argparse.Namespace) -> None:
    from pathlib import Path
    from research.phases.phase4_archive import Phase4Inputs, run_phase4_archive
    from research.storage.paths import StoragePaths
    from research.storage.yaml_io import load_yaml

    paths = StoragePaths()
    batch_id = args.batch_id
    manifest = load_yaml(paths.batch_manifest_file(batch_id))
    if not manifest:
        print(f"manifest.yaml not found for {batch_id}", file=sys.stderr)
        sys.exit(1)

    direction = manifest.get("direction", "unknown")

    def _chart_builder(factor_id: str, _assets_dir: Path) -> list[str]:
        from report.render import render_factor

        manifest = render_factor(factor_id, storage_root=paths.root)
        return list(manifest.get("charts", {}).keys())

    inputs = Phase4Inputs(
        batch_id=batch_id,
        direction=direction,
        paths=paths,
        repo_root=Path("."),
        chart_builder=_chart_builder,
        # report_callback stays None — the /factor-mine loop dispatches
        # the /factor-report subagent, not this CLI.
    )
    result = run_phase4_archive(inputs)
    n = len(result.admitted)
    print(f"Phase 4 done: {n} factors archived — {[a.factor_id for a in result.admitted]}")
    if result.admitted:
        print(
            f"\n⚠️  {n} factor.md file(s) still empty until /factor-report runs. "
            f"LLM orchestrator must dispatch:"
        )
        for a in result.admitted:
            print(f"   → /factor-report {a.factor_id}")
        print(
            "   Then verify: each vault/factors/F{id}.md is non-empty with '# F{id}' H1.\n"
            "   (factor-mine skill Phase 4 Step 5 has the enforcement contract.)"
        )


def _cmd_consolidate(args: argparse.Namespace) -> None:
    from pathlib import Path
    from research.phases.phase5_consolidate import (
        ConsolidationTrigger, Phase5Inputs, check_triggers,
        preconditions_ok, prepack_consolidation, run_phase5_consolidation,
    )
    from research.storage.paths import StoragePaths
    from research.storage.state import StateFile
    from research.storage.yaml_io import load_yaml

    paths = StoragePaths()
    state_file = StateFile(paths.state_file)

    if args.dry_run:
        packets = prepack_consolidation(paths)
        print(f"Dry run: {len(packets)} packets would be written")
        for k, p in packets.items():
            print(f"  {k}: {p}")
        return

    failures = preconditions_ok(state_file, Path("."))
    if failures:
        for f in failures:
            print(f"Precondition failed: {f}", file=sys.stderr)
        sys.exit(1)

    trigger = ConsolidationTrigger(reason="manual_trigger")
    inputs = Phase5Inputs(
        paths=paths,
        repo_root=Path("."),
        trigger=trigger,
        rewrite_callback=None,  # CLI mode — no LLM rewrite, just pre-pack + stats refresh
    )
    result = run_phase5_consolidation(inputs)
    print(f"Consolidation done: {len(result.targets)} targets, {len(result.rewritten)} rewritten")


def _cmd_commit(args: argparse.Namespace) -> None:
    import re
    import yaml as _yaml
    from research.archive.commit import (
        build_commit_message, create_commit, stage_files,
    )
    from research.storage.paths import StoragePaths
    from research.storage.yaml_io import load_yaml

    paths = StoragePaths()
    batch_id = args.batch_id
    repo_root = paths.root.resolve().parent

    judge_path = paths.batch_judge_file(batch_id)
    manifest_path = paths.batch_manifest_file(batch_id)
    if not judge_path.exists():
        print(f"Commit failed: judge.md not found at {judge_path}", file=sys.stderr)
        sys.exit(1)
    if not manifest_path.exists():
        print(f"Commit failed: manifest.yaml not found at {manifest_path}", file=sys.stderr)
        sys.exit(1)

    m = re.match(r"^---\n(.*?)\n---", judge_path.read_text(), re.DOTALL)
    if not m:
        print(f"Commit failed: judge.md missing YAML frontmatter", file=sys.stderr)
        sys.exit(1)
    judge_fm = _yaml.safe_load(m.group(1)) or {}

    summary = judge_fm.get("batch_summary", {}) or {}
    n_admit = int(summary.get("admit", 0))
    n_reserve = int(summary.get("reserve", 0))
    n_reject = int(summary.get("reject", 0))
    direction = judge_fm.get("direction") or ""

    manifest = load_yaml(manifest_path) or {}
    batch_goal = manifest.get("batch_goal", "")

    admit_names = {
        c.get("factor_name")
        for c in (judge_fm.get("candidates") or [])
        if c.get("verdict") == "admit" and c.get("factor_name")
    }
    factor_ids: list[str] = []
    if paths.factors_dir.exists():
        for yml in sorted(paths.factors_dir.glob("F*.yaml")):
            data = load_yaml(yml) or {}
            if data.get("batch_id") == batch_id and data.get("name") in admit_names:
                factor_ids.append(data.get("id") or yml.stem)

    message = build_commit_message(
        batch_id=batch_id,
        direction=direction,
        n_admit=n_admit,
        n_reserve=n_reserve,
        n_reject=n_reject,
        factor_ids=factor_ids,
        batch_goal=batch_goal,
    )

    files: list[Path] = [
        paths.state_file,
        paths.vault_index_file,
        paths.direction_file(direction) if direction else None,
        paths.batch_manifest_file(batch_id),
        paths.batch_result_file(batch_id),
        paths.batch_hints_file(batch_id),
        paths.batch_judge_file(batch_id),
    ]
    files = [f for f in files if f is not None]

    cand_dir = paths.batch_candidates_dir(batch_id)
    if cand_dir.exists():
        files.extend(sorted(cand_dir.glob("*.md")))
    packets_dir = paths.batch_packets_dir(batch_id)
    if packets_dir.exists():
        files.extend(sorted(packets_dir.glob("*.md")))
    for fid in factor_ids:
        files.append(paths.factor_yaml_file(fid))
        adir = paths.factor_assets_dir(fid)
        if adir.exists():
            files.extend(sorted(adir.glob("*.png")))
            rj = adir / "report.json"
            if rj.exists():
                files.append(rj)

    try:
        staged = stage_files(repo_root, files)
        result = create_commit(
            repo_root=repo_root,
            message=message,
            staged_files=staged,
        )
        print(f"Committed: {result.commit_hash[:8]} {result.message.splitlines()[0]}")
    except Exception as exc:
        print(f"Commit failed: {exc}", file=sys.stderr)
        sys.exit(1)


def _cmd_commit_report(args: argparse.Namespace) -> None:
    """Commit the deep-report artefacts for a single factor.

    Called by the ``/factor-report`` subagent after it has written:

    * ``storage/vault/factors/F{id}.md`` — LLM-authored narrative
    * ``storage/vault/factors/F{id}/*.png`` — chart PNGs from the
      ``report.render`` pipeline
    * ``storage/vault/factors/F{id}/report.json`` — scalar manifest

    The phase4 ``[mine]`` commit intentionally does not stage these —
    the subagent runs asynchronously and the artefacts typically don't
    exist yet at phase4 commit time. Without this command they sit
    untracked on disk, which is how F011 / F009 updates / F010 assets
    all ended up outside git history.
    """
    from research.archive.commit import create_commit, stage_files
    from research.storage.paths import StoragePaths
    from research.storage.yaml_io import load_yaml

    paths = StoragePaths()
    fid = args.factor_id
    repo_root = paths.root.resolve().parent

    yaml_path = paths.factor_yaml_file(fid)
    if not yaml_path.exists():
        print(f"commit-report failed: {yaml_path} does not exist", file=sys.stderr)
        sys.exit(1)

    md_path = paths.factor_md_file(fid)
    assets_dir = paths.factor_assets_dir(fid)
    if not md_path.exists():
        print(f"commit-report failed: {md_path} missing (report not written)",
              file=sys.stderr)
        sys.exit(1)

    data = load_yaml(yaml_path) or {}
    name = data.get("name", fid)

    # Try to pull grade / score from the factor MD frontmatter — these come
    # from the report builder, not the admission record.
    grade: str | None = None
    score: float | None = None
    import re
    mtext = md_path.read_text(encoding="utf-8")
    m = re.match(r"\A---\s*\n(?P<fm>.*?)\n---\s*\n", mtext, re.DOTALL)
    if m:
        import yaml as _yaml
        mdfm = _yaml.safe_load(m.group("fm")) or {}
        g = mdfm.get("composite_grade")
        if isinstance(g, str) and g.strip():
            grade = g.strip()
        s = mdfm.get("composite_score")
        try:
            score = float(s) if s is not None else None
        except (TypeError, ValueError):
            score = None

    grade_bit = ""
    if grade:
        grade_bit = f" ({grade}"
        if score is not None:
            grade_bit += f"/{score:.1f}"
        grade_bit += ")"
    message = f"[report] {fid} {name} — deep report{grade_bit}"

    files: list[Path] = [md_path]
    if assets_dir.exists():
        files.extend(sorted(assets_dir.glob("*.png")))
        rj = assets_dir / "report.json"
        if rj.exists():
            files.append(rj)

    try:
        staged = stage_files(repo_root, files)
    except Exception as exc:
        print(f"commit-report failed to stage: {exc}", file=sys.stderr)
        sys.exit(1)

    if not staged:
        # Nothing to commit — report artefacts already match HEAD.
        print(f"commit-report: {fid} — no changes to commit")
        return

    try:
        result = create_commit(repo_root=repo_root, message=message, staged_files=staged)
        print(f"Committed: {result.commit_hash[:8]} {message}")
    except Exception as exc:
        print(f"commit-report failed: {exc}", file=sys.stderr)
        sys.exit(1)


def _cmd_cache(args: argparse.Namespace) -> None:
    sub = args.cache_cmd
    if sub == "refresh":
        from research.compute.data_bridge import (
            init_qlib, load_market_data, build_barra_style_matrix,
        )
        from research.storage.paths import StoragePaths
        from research.storage.yaml_io import load_yaml

        paths = StoragePaths()
        config = load_yaml(paths.config_file) or {}
        qlib_dir = config.get("qlib_data_dir", "~/.qlib/qlib_data/cn_data_1d")
        init_qlib(qlib_dir)

        sample = config.get("sample_policy", {})
        full_end = sample.get("validation_range", ["2022-01-01", "2023-12-31"])[1]

        target = args.target
        if target in ("all", "market_daily"):
            load_market_data(
                start="2015-01-01", end=full_end,
                cache_path=paths.market_daily_cache,
            )
            print(f"Refreshed {paths.market_daily_cache}")
        if target in ("all", "barra_factors"):
            build_barra_style_matrix(
                start="2015-01-01", end=full_end,
                cache_path=paths.barra_factors_cache,
            )
            print(f"Refreshed {paths.barra_factors_cache}")
    elif sub == "status":
        from research.storage.paths import StoragePaths
        paths = StoragePaths()
        for name, path in [
            ("market_daily", paths.market_daily_cache),
            ("barra_factors", paths.barra_factors_cache),
            ("factor_values/", paths.factor_values_cache_dir),
        ]:
            if path.exists():
                if path.is_dir():
                    n = len(list(path.glob("*.parquet")))
                    print(f"  {name}: {n} files")
                else:
                    mb = path.stat().st_size / 1024 / 1024
                    print(f"  {name}: {mb:.1f} MB")
            else:
                print(f"  {name}: (missing)")
    elif sub == "purge":
        print("cache purge: (stub)")


def _cmd_state(args: argparse.Namespace) -> None:
    from research.storage.state import StateFile
    from research.storage.paths import StoragePaths

    paths = StoragePaths()
    sf = StateFile(paths.state_file)

    if args.state_action is None:
        state = sf.read()
        print("=== Research State ===")
        for k, v in state.to_dict().items():
            print(f"  {k}: {v}")
    elif args.state_action == "next-batch-id":
        print(sf.next_batch_id())
    elif args.state_action == "reset":
        if not getattr(args, "confirm", False):
            print(
                "Refusing: 'state reset' is destructive. Pass --confirm "
                "to clear current_batch / phase / round counters.",
                file=sys.stderr,
            )
            sys.exit(1)
        new = sf.reset()
        print("State reset to idle:")
        for k, v in new.to_dict().items():
            print(f"  {k}: {v}")
    elif args.state_action == "set":
        if not args.key or args.value is None:
            print("Usage: research state set KEY VALUE", file=sys.stderr)
            sys.exit(1)
        # Parse a handful of typed values; YAML literal is the escape hatch.
        import yaml
        try:
            typed = yaml.safe_load(args.value)
        except yaml.YAMLError:
            typed = args.value
        sf.update(**{args.key: typed})
        print(f"state set {args.key} = {typed!r}")
    elif args.state_action == "rollback":
        print("state rollback: (stub — will git reset --hard HEAD^)")


def _cmd_doctor(args: argparse.Namespace) -> None:
    """Cross-check state ↔ vault and print a punch list of fixes."""
    from research.storage.state import (
        InvalidStateSchema,
        StateFile,
    )
    from research.storage.paths import StoragePaths

    paths = StoragePaths()
    findings: list[str] = []
    suggestions: list[str] = []

    # 1. state.yaml parses.
    sf = StateFile(paths.state_file)
    try:
        state = sf.read()
    except InvalidStateSchema as exc:
        print(f"FAIL: state.yaml malformed — {exc}")
        print("  Fix: research state reset --confirm")
        sys.exit(2)

    # 2. current_batch (if set) has a manifest on disk.
    if state.current_batch:
        mf = paths.batch_manifest_file(state.current_batch)
        if not mf.exists():
            findings.append(
                f"state.current_batch={state.current_batch} but {mf} is missing"
            )
            suggestions.append(
                "research state reset --confirm  # vault has been wiped"
            )

    # 3. last_batch (if set) has a manifest on disk.
    if state.last_batch:
        mf = paths.batch_manifest_file(state.last_batch)
        if not mf.exists():
            findings.append(
                f"state.last_batch={state.last_batch} but {mf} is missing"
            )

    # 4. batches/ dir round-count ↔ state.round sanity.
    batch_dirs = (
        sorted(paths.batches_dir.glob("batch_*"))
        if paths.batches_dir.exists()
        else []
    )
    if state.round == 0 and batch_dirs:
        findings.append(
            f"state.round=0 but {len(batch_dirs)} batch dirs exist"
        )
    if state.round > 0 and not batch_dirs:
        findings.append(
            f"state.round={state.round} but no batch dirs on disk"
        )

    # 4b. Orphan batch dirs past state.last_batch (phase1 freeze aborts
    #     can leave empty dirs; archives can be interrupted mid-write).
    from research.storage.state import _batch_id_to_int  # type: ignore
    if state.last_batch and batch_dirs:
        last_n = _batch_id_to_int(state.last_batch)
        orphans: list[str] = []
        for d in batch_dirs:
            try:
                n = _batch_id_to_int(d.name)
            except ValueError:
                continue
            # Allow current_batch to exceed last_batch; anything above both
            # without a manifest is orphan.
            current_n = (
                _batch_id_to_int(state.current_batch)
                if state.current_batch else last_n
            )
            if n > max(last_n, current_n):
                if not paths.batch_manifest_file(d.name).exists():
                    orphans.append(d.name)
        if orphans:
            findings.append(
                f"{len(orphans)} orphan batch dir(s) past last_batch: "
                + ", ".join(orphans)
            )
            suggestions.append(
                "rm -rf " + " ".join(
                    str(paths.batch_dir(o)) for o in orphans[:3]
                ) + ("  # orphans" if len(orphans) <= 3 else
                     "  # plus others")
            )

    # 5. directions/*.md exist for direction_tags referenced in state.
    dirs_on_disk = (
        [p.stem for p in paths.directions_dir.glob("*.md")]
        if paths.directions_dir.exists()
        else []
    )
    # 6. Orphan factor.yaml without diagnostics dir.
    #    Prefers new `diagnostics_ref` (dir of parquets); falls back to
    #    legacy `signal_ref` (single parquet) for records pre-rename.
    orphan_factors: list[str] = []
    if paths.factors_dir.exists():
        for yml in paths.factors_dir.glob("F*.yaml"):
            from research.storage.yaml_io import load_yaml as _ly
            data = _ly(yml) or {}
            ref = data.get("diagnostics_ref") or data.get("signal_ref")
            if not ref:
                continue
            target = paths.root / ref
            if not target.exists():
                orphan_factors.append(f"{yml.stem} → {ref}")
    if orphan_factors:
        findings.append(
            f"{len(orphan_factors)} factor(s) with missing diagnostics: "
            + ", ".join(orphan_factors[:5])
            + ("..." if len(orphan_factors) > 5 else "")
        )

    # Report
    print("=== research doctor ===")
    print(f"state:")
    for k, v in state.to_dict().items():
        print(f"  {k}: {v}")
    print(f"directions on disk: {len(dirs_on_disk)}")
    print(f"batch dirs on disk: {len(batch_dirs)}")
    factors_on_disk = (
        len(list(paths.factors_dir.glob("F*.yaml")))
        if paths.factors_dir.exists()
        else 0
    )
    print(f"factor yamls on disk: {factors_on_disk}")
    print()
    if not findings:
        print("OK — no inconsistencies detected.")
        return
    print(f"Found {len(findings)} inconsistency(ies):")
    for f in findings:
        print(f"  - {f}")
    if suggestions:
        print()
        print("Suggested fixes:")
        for s in suggestions:
            print(f"  $ {s}")
    sys.exit(1)


def _cmd_memory(args: argparse.Namespace) -> None:
    if args.memory_cmd == "refresh-index":
        from research.memory.index_refresher import refresh_index
        from research.storage.state import StateFile
        from research.storage.paths import StoragePaths

        paths = StoragePaths()
        state = StateFile(paths.state_file).read()
        path = refresh_index(paths, round_counter=state.round)
        print(f"INDEX refreshed: {path}")
    elif args.memory_cmd == "snapshot":
        from research.memory.snapshot import render_snapshot
        from research.storage.paths import StoragePaths

        paths = StoragePaths()
        sections = (
            ("directions", "factors", "batches")
            if args.section == "all"
            else (args.section,)
        )
        print(render_snapshot(paths, sections=sections, recent_batches=args.recent))


def _cmd_phase1(args: argparse.Namespace) -> None:
    if args.phase1_cmd == "freeze":
        from research.phases.phase1_start import (
            Phase1FreezeError,
            start_phase1,
        )
        from research.storage.yaml_io import load_yaml

        spec_path = Path(args.spec) if isinstance(args.spec, str) else args.spec
        spec = load_yaml(Path(spec_path))
        if not spec:
            print(f"spec file empty or missing: {spec_path}", file=sys.stderr)
            sys.exit(1)
        required = {"direction", "batch_goal", "candidates"}
        missing = required - set(spec)
        if missing:
            print(
                f"spec missing required keys: {sorted(missing)}",
                file=sys.stderr,
            )
            sys.exit(1)
        try:
            report = start_phase1(
                direction=spec["direction"],
                batch_goal=spec["batch_goal"],
                candidates=spec["candidates"],
                active_threads_referenced=spec.get(
                    "active_threads_referenced"
                ),
            )
        except Phase1FreezeError as exc:
            print(f"phase1 freeze FAILED: {exc.args[0]}", file=sys.stderr)
            sys.exit(1)
        print(
            f"phase1 freeze OK: {report.batch_id} / "
            f"{len([c for c in report.candidates if c.passed])}/"
            f"{len(report.candidates)} candidates passed"
        )
        print(f"  manifest: {report.manifest_path}")


def _import_path_module() -> Any:  # (unused — kept for legacy imports)
    return None


def _cmd_holdout(args: argparse.Namespace) -> None:
    print(f"holdout-review: factor={args.factor}")
    print("(Stub — will compute holdout metrics in _holdout_private/)")


def _cmd_factor(args: argparse.Namespace) -> None:
    if args.factor_cmd == "retire":
        print(f"factor retire: {args.factor_id}")
        print("(Stub — will set status=retired in vault/factors/F{id}.yaml)")


def _cmd_report_pack(args: argparse.Namespace) -> None:
    print(f"report-pack: {args.factor_id}")
    print("(Stub — will generate _packets/report_packet_F{id}.md)")


def _cmd_report(args: argparse.Namespace) -> None:
    from research.archive.report_packer import cleanup_finished_packets
    from research.storage.paths import StoragePaths

    paths = StoragePaths(root=Path("storage"))
    if args.report_cmd == "cleanup-packets":
        deleted = cleanup_finished_packets(
            paths,
            skip_batch=args.skip_batch,
            dry_run=args.dry_run,
        )
        verb = "would delete" if args.dry_run else "deleted"
        if not deleted:
            print("no finished packets to clean.")
            return
        print(f"{verb} {len(deleted)} packet(s):")
        for p in deleted:
            try:
                rel = p.relative_to(paths.root)
            except ValueError:
                rel = p
            print(f"  - {rel}")
    else:
        raise SystemExit(f"unknown report subcommand: {args.report_cmd!r}")
