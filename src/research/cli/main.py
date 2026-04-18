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
    state_p.add_argument("state_action", nargs="?", default=None,
                         choices=["set", "rollback", None])
    state_p.add_argument("key", nargs="?")
    state_p.add_argument("value", nargs="?")

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
    elif cmd == "holdout-review":
        _cmd_holdout(args)
    elif cmd == "factor":
        _cmd_factor(args)
    elif cmd == "report-pack":
        _cmd_report_pack(args)
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
    from research.archive.commit import create_commit
    from research.storage.paths import StoragePaths
    paths = StoragePaths()
    try:
        result = create_commit(
            batch_id=args.batch_id,
            paths=paths,
        )
        print(f"Committed: {result.commit_hash[:8]} {result.message.splitlines()[0]}")
    except Exception as exc:
        print(f"Commit failed: {exc}", file=sys.stderr)
        sys.exit(1)


def _cmd_commit_report(args: argparse.Namespace) -> None:
    print(f"commit-report: factor_id={args.factor_id}")
    print("(Stub — called by report subagent on completion)")


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
    if args.state_action is None:
        sf = StateFile(paths.state_file)
        state = sf.read()
        print("=== Research State ===")
        for k, v in state.to_dict().items():
            print(f"  {k}: {v}")
    elif args.state_action == "set":
        if not args.key or not args.value:
            print("Usage: research state set KEY VALUE", file=sys.stderr)
            sys.exit(1)
        print(f"state set {args.key} = {args.value}: (stub)")
    elif args.state_action == "rollback":
        print("state rollback: (stub — will git reset --hard HEAD^)")


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
