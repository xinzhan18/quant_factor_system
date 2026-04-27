#!/usr/bin/env python3
"""Recompute the entire factor library through the Phase 2 mainline.

Loops every ``vault/factors/F*.yaml`` candidate through the canonical
``data_bridge.build_phase2_inputs → phase2_execute.run_phase2`` path
under the current ``tradable_mask`` (incl. ST + suspend + 涨跌停 +
new-listing 60d), then runs CP01 hard_gates and either:

  * **PASS** → updates F*.yaml with fresh validation/risk/multi-universe
    blocks and stamps ``revalidated_in_batch=batch_recompute_v2``;
  * **FAIL** → physically deletes ``F{id}.{yaml,md}``, ``F{id}/`` assets,
    and any ``python_factors/F{id}_*.py`` files.

Old DB ``factor_values`` rows (``factor_001..``) are not consulted —
they are mining_v1 leftovers and will be dropped separately.
"""

from __future__ import annotations

import argparse
import logging
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from research.checkpoints.hard_gates import HardGatesConfig, evaluate_hard_gates
from research.compute.data_bridge import build_phase2_inputs
from research.phases.phase2_execute import run_phase2
from research.storage.paths import StoragePaths
from research.storage.yaml_io import load_yaml, save_yaml

logger = logging.getLogger(__name__)

DEFAULT_BATCH_ID = "batch_recompute_v2"
DEFAULT_RUN_NAME = "library_recompute_v2"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def collect_candidates(
    paths: StoragePaths, only: list[str] | None = None
) -> list[dict[str, Any]]:
    """Build the manifest candidates list from every F*.yaml in vault.

    ``only`` — optional explicit list of factor ids (e.g. ``["F004", "F005"]``);
    ``None`` selects every yaml in the directory.
    """
    candidates: list[dict[str, Any]] = []
    only_set = set(only) if only else None
    for yaml_path in sorted(paths.factors_dir.glob("F*.yaml")):
        if only_set is not None and yaml_path.stem not in only_set:
            continue
        meta = load_yaml(yaml_path) or {}
        fid = meta.get("factor_id", yaml_path.stem)
        source_type = meta.get("source_type", "dsl")
        cand: dict[str, Any] = {
            "candidate_id": fid,
            "source_type": source_type,
            "name": meta.get("name", fid),
            "direction": meta.get("direction", meta.get("family_tag", "unknown")),
            "prior_status": meta.get("status", "active"),
        }
        if source_type == "dsl":
            cand["expression"] = meta.get("expression", "")
        else:
            cand["path"] = meta.get("python_path", "")
        candidates.append(cand)
    return candidates


def update_factor_yaml(
    paths: StoragePaths,
    fid: str,
    cand_result: dict[str, Any],
    batch_id: str,
    run_name: str = DEFAULT_RUN_NAME,
) -> None:
    """Write fresh metrics into F{fid}.yaml (preserves frontmatter)."""
    yaml_path = paths.factor_yaml_file(fid)
    record = load_yaml(yaml_path) or {}

    ic = cand_result.get("ic") or {}
    val_ic = ic.get("validation") or {}
    quintile = cand_result.get("quintile") or {}
    q_val = quintile.get("validation") or {}
    ls_val = ((quintile.get("ls_stats") or {}).get("validation")) or {}
    barra = cand_result.get("barra") or {}

    record["validation_metrics"] = {
        "coverage": cand_result.get("coverage"),
        "ic_mean": val_ic.get("ic_mean"),
        "ic_ir": val_ic.get("ic_ir"),
        "ic_win_rate": val_ic.get("ic_win_rate"),
        "monotonicity": q_val.get("monotonicity"),
        "long_short_mean": q_val.get("ls_mean"),
        "long_short_sharpe": ls_val.get("sharpe"),
        "long_short_tstat": ls_val.get("tstat"),
        "long_short_max_dd": ls_val.get("max_dd"),
    }
    record["risk_metrics"] = {
        "style_r_squared": barra.get("style_r_squared"),
        "alpha_survival_ratio": barra.get("alpha_survival_ratio"),
    }
    if "validation_metrics_by_universe" in cand_result:
        record["validation_metrics_by_universe"] = cand_result[
            "validation_metrics_by_universe"
        ]
    if "universe_robustness" in cand_result:
        record["universe_robustness"] = cand_result["universe_robustness"]
        record["primary_universe"] = cand_result["universe_robustness"].get(
            "primary_universe"
        )
    record["revalidated_in_batch"] = batch_id
    record["diagnostics_ref"] = (
        cand_result.get("diagnostics_relpath")
        or f"cache/batch_diagnostics/{batch_id}/{fid}"
    )
    record["recompute_provenance"] = {
        "run_name": run_name,
        "applied_at": _now_iso(),
        "batch_id": batch_id,
        "result_relpath": f"vault/batches/{batch_id}/result.yaml",
    }
    record["status"] = "active"
    record.pop("reverdict_status", None)
    save_yaml(yaml_path, record)


def delete_factor(paths: StoragePaths, fid: str) -> list[str]:
    """Physical delete of every artifact for a factor. Returns paths removed."""
    deleted: list[str] = []
    for p in [paths.factor_yaml_file(fid), paths.factor_md_file(fid)]:
        if p.exists():
            p.unlink()
            deleted.append(str(p))
    sub_dir = paths.factor_assets_dir(fid)
    if sub_dir.exists() and sub_dir.is_dir():
        shutil.rmtree(sub_dir)
        deleted.append(str(sub_dir))
    for p in paths.python_factors_dir.glob(f"{fid}_*.py"):
        p.unlink()
        deleted.append(str(p))
    return deleted


def write_purge_log(
    paths: StoragePaths,
    decisions: list[dict[str, Any]],
    batch_id: str,
    run_name: str = DEFAULT_RUN_NAME,
) -> Path:
    """Write a purge log to vault/_meta/library_purge_<run_name>.md."""
    log_path = paths.vault_meta_dir / f"library_purge_{run_name}.md"
    n_keep = sum(1 for d in decisions if d["action"] == "KEEP")
    n_del = sum(1 for d in decisions if d["action"] == "DELETE")
    lines = [
        "---",
        "title: Library Purge v2 — Phase 2 mainline recompute under tradable_mask",
        f"generated_at: {_now_iso()}",
        f"batch_id: {batch_id}",
        f"run_name: {run_name}",
        "primary_universe: all_tradable",
        "secondary_universes: [csi300, csi1000]",
        f"n_evaluated: {len(decisions)}",
        f"n_kept: {n_keep}",
        f"n_deleted: {n_del}",
        "---",
        "",
        "# Library Purge v2",
        "",
        "> [!danger]+ 系统级清算",
        "> 全部 23 个因子通过 Phase 2 mainline 重算，启用 `tradability.filter_limit=true`",
        "> （涨跌停 mask）。CP01 hard_gates 决定 keep/delete。DB `factor_values` 老表",
        "> （`factor_001..factor_045`，mining_v1 遗留）已视为无效，单独 DROP。",
        "",
        f"**Result**: {n_keep} kept, {n_del} deleted",
        "",
        "## Decisions",
        "",
        "| Factor | Name | Action | Coverage | IC mean | ICIR | Mono | L/S Sharpe | csi300 mono | csi1000 mono | Reasons |",
        "|--------|------|--------|----------|---------|------|------|------------|-------------|--------------|---------|",
    ]

    def _fmt(x: Any, fmt: str = ".4f") -> str:
        if x is None:
            return "—"
        try:
            return format(float(x), fmt)
        except (ValueError, TypeError):
            return str(x)

    for d in decisions:
        by_u = d.get("by_universe") or {}
        csi300_mono = (by_u.get("csi300") or {}).get("monotonicity")
        csi1000_mono = (by_u.get("csi1000") or {}).get("monotonicity")
        lines.append(
            f"| {d['factor_id']} | {d['name']} | **{d['action']}** | "
            f"{_fmt(d.get('coverage'), '.3f')} | "
            f"{_fmt(d.get('ic_mean'))} | {_fmt(d.get('ic_ir'), '.3f')} | "
            f"{_fmt(d.get('monotonicity'), '.2f')} | "
            f"{_fmt(d.get('long_short_sharpe'), '.3f')} | "
            f"{_fmt(csi300_mono, '.2f')} | {_fmt(csi1000_mono, '.2f')} | "
            f"{'; '.join(d.get('reasons') or []) or 'passed'} |"
        )

    lines.extend(["", "## Deletion artifacts", ""])
    for d in decisions:
        if d["action"] == "DELETE" and d.get("deleted_paths"):
            lines.append(f"- **{d['factor_id']}** ({d['name']}):")
            for p in d["deleted_paths"]:
                lines.append(f"  - `{p}`")

    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return log_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--storage-root",
        default="storage",
        help="Storage root directory (default: storage)",
    )
    parser.add_argument(
        "--log-level", default="INFO", help="Logging level (default: INFO)"
    )
    parser.add_argument(
        "--batch-id",
        default=DEFAULT_BATCH_ID,
        help=f"Output batch id (default: {DEFAULT_BATCH_ID}); use a distinct id for surgical re-runs",
    )
    parser.add_argument(
        "--run-name",
        default=DEFAULT_RUN_NAME,
        help="Provenance label written into recompute_provenance",
    )
    parser.add_argument(
        "--factors",
        nargs="*",
        default=None,
        help="Optional explicit factor ids (e.g. F004 F005); default = all F*.yaml",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    paths = StoragePaths(args.storage_root)
    config = load_yaml(paths.config_file) or {}
    batch_id = args.batch_id
    run_name = args.run_name

    candidates = collect_candidates(paths, only=args.factors)
    if not candidates:
        logger.error(
            "No factors found in %s (filter=%s)", paths.factors_dir, args.factors
        )
        return 1
    logger.info(
        "Collected %d factors for recompute (batch_id=%s)", len(candidates), batch_id
    )

    batch_dir = paths.batch_dir(batch_id)
    batch_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "batch_id": batch_id,
        "intent": "Recompute factor library through Phase 2 mainline under tradable_mask (incl. limit-up/down).",
        "generated_at": _now_iso(),
        "run_name": run_name,
        "candidates": candidates,
    }
    manifest_path = paths.batch_manifest_file(batch_id)
    save_yaml(manifest_path, manifest)
    logger.info("Wrote manifest: %s", manifest_path)

    inputs = build_phase2_inputs(batch_id, manifest, paths, config)
    # Self-correlation noise: candidates ARE the library. Skip uniqueness.
    inputs.library_signals = {}

    result_path = paths.batch_result_file(batch_id)
    result = run_phase2(inputs, result_path)
    logger.info(
        "Phase 2 wrote %s (%d candidates, %d errors)",
        result_path,
        result["n_candidates"],
        result["n_errors"],
    )

    hard_cfg = HardGatesConfig.from_config_dict(
        config.get("thresholds", {}).get("hard_gates", {})
    )
    gate_results = evaluate_hard_gates(result, hard_cfg)
    name_by_fid = {c["candidate_id"]: c.get("name", c["candidate_id"]) for c in candidates}

    decisions: list[dict[str, Any]] = []
    for cand, gate in zip(result["candidates"], gate_results):
        fid = cand["candidate_id"]
        ic_val = (cand.get("ic") or {}).get("validation") or {}
        q_val = (cand.get("quintile") or {}).get("validation") or {}
        ls_val = (
            ((cand.get("quintile") or {}).get("ls_stats") or {}).get("validation")
            or {}
        )
        decision: dict[str, Any] = {
            "factor_id": fid,
            "name": name_by_fid.get(fid, fid),
            "coverage": cand.get("coverage"),
            "ic_mean": ic_val.get("ic_mean"),
            "ic_ir": ic_val.get("ic_ir"),
            "monotonicity": q_val.get("monotonicity"),
            "long_short_sharpe": ls_val.get("sharpe"),
            "by_universe": cand.get("validation_metrics_by_universe", {}),
            "passed": gate.passed,
            "reasons": gate.reasons,
        }
        if gate.passed:
            update_factor_yaml(paths, fid, cand, batch_id, run_name)
            decision["action"] = "KEEP"
            logger.info(
                "KEEP %s: cov=%.3f IC=%.4f ICIR=%.3f mono=%s",
                fid,
                cand.get("coverage") or 0.0,
                ic_val.get("ic_mean") or 0.0,
                ic_val.get("ic_ir") or 0.0,
                q_val.get("monotonicity"),
            )
        else:
            deleted = delete_factor(paths, fid)
            decision["action"] = "DELETE"
            decision["deleted_paths"] = deleted
            logger.warning("DELETE %s: %s", fid, "; ".join(gate.reasons))
        decisions.append(decision)

    log_path = write_purge_log(paths, decisions, batch_id, run_name)
    logger.info("Wrote purge log: %s", log_path)

    n_keep = sum(1 for d in decisions if d["action"] == "KEEP")
    n_del = sum(1 for d in decisions if d["action"] == "DELETE")
    print(f"\nSummary: {n_keep} kept / {n_del} deleted (total {len(decisions)})")
    print(f"Manifest: {manifest_path}")
    print(f"Result:   {result_path}")
    print(f"Purge log: {log_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
