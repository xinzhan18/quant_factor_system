#!/usr/bin/env python3
<<<<<<< HEAD
"""Create the new ``storage/`` directory tree with seed YAML files.

Idempotent: directories and seed files are only created if missing.

Usage::

    python scripts/init_new_storage.py                     # default root
    python scripts/init_new_storage.py --root storage_new  # custom root
=======
"""Create the new storage/ directory tree with seed YAML files.

Run from project root:
    python scripts/init_new_storage.py

Or provide an explicit root (useful for testing):
    python scripts/init_new_storage.py /tmp/test_storage
>>>>>>> worktree-agent-a1d4eeec
"""

from __future__ import annotations

<<<<<<< HEAD
import argparse
import sys
from pathlib import Path

# Allow running as a standalone script; add src/ to path for imports.
_project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_project_root / "src"))

from research.storage.paths import StoragePaths  # noqa: E402
from research.storage.yaml_io import save_yaml  # noqa: E402


# ------------------------------------------------------------------
# Seed data: minimal valid content for each YAML file
# ------------------------------------------------------------------

_SEEDS: dict[str, dict] = {
    "research_state": {
        "research_state": {
            "current_batch": None,
            "active_logic_ids": [],
            "current_focus": [],
            "current_bottlenecks": [],
            "policy_flags": {
                "prefer_dsl": True,
                "python_only_helper_based": True,
                "vectorization_required": True,
            },
            "last_updated_at": None,
        }
    },
    "pending_holdout_queue": {"pending": []},
    "logic_registry": {"logics": []},
    "factor_index": {"factors": []},
    "family_registry": {"families": []},
    "capability_registry": {
        "fields": [
            "$open", "$high", "$low", "$close",
            "$volume", "$amount",
            "$pe_ratio", "$pb_ratio", "$ps_ratio",
            "$market_cap", "$circ_market_cap", "$turnover_rate",
        ],
        "unavailable_operators": ["Neg", "TsRank", "TsMax", "TsMin", "SMA"],
        "notes": ["$vwap is zero in current data -- do not use"],
    },
    "implementation_policy": {
        "default": {
            "prefer_dsl": True,
            "python_only_helper_based": True,
            "vectorization_required": True,
        },
        "python_allowed_if": [
            "route_requires_multi_stage_pipeline",
            "route_requires_multi_state_logic",
            "dsl_expression_unnatural",
        ],
        "python_discouraged_if": [
            "simple_breakout",
            "simple_reversal",
            "simple_rank_spread",
            "only_window_variation",
        ],
    },
    "failure_taxonomy": {
        "failure_types": [
            "weak_signal",
            "high_overlap",
            "hard_gate_rejected",
            "implementation_blocked",
            "performance_rejected",
            "helper_required",
            "regime_mismatch",
            "unstable_oos",
            "size_drift",
            "style_repackaging",
        ]
    },
    "policy_upgrade_ledger": {"upgrades": []},
    "search_ledger": {
        "by_logic": {},
        "by_family": {},
        "by_experiment_tag": {},
    },
    "batch_usage": {"batches": {}},
    "holdout_review_ledger": {"reviews": []},
    "write_audit_log": {"entries": []},
    "forbidden": {"forbidden_patterns": []},
    "research_eval_v1": {
        "profile_id": "research_eval_v1",
        "universe": "all_a_share",
        "train_end": "2023-12-31",
        "test_start": "2024-01-01",
        "ic_threshold": 0.01,
        "correlation_threshold": 0.7,
    },
}

# Map seed key -> (StoragePaths attribute name for the file path)
_SEED_MAP: dict[str, str] = {
    "research_state": "research_state_file",
    "pending_holdout_queue": "pending_holdout_queue_file",
    "logic_registry": "logic_registry_file",
    "factor_index": "factor_index_file",
    "family_registry": "family_registry_file",
    "capability_registry": "capability_registry_file",
    "implementation_policy": "implementation_policy_file",
    "failure_taxonomy": "failure_taxonomy_file",
    "policy_upgrade_ledger": "policy_upgrade_ledger_file",
    "search_ledger": "search_ledger_file",
    "batch_usage": "batch_usage_file",
    "holdout_review_ledger": "holdout_review_ledger_file",
    "write_audit_log": "write_audit_log_file",
    "forbidden": "forbidden_file",
    "research_eval_v1": "research_eval_v1_file",
}


def init_storage(root: str = "storage") -> None:
    paths = StoragePaths(root)
    paths.ensure_dirs()

    # Write seed files (only if missing)
    for seed_key, attr_name in _SEED_MAP.items():
        file_path = getattr(paths, attr_name)
        if not file_path.exists():
            save_yaml(file_path, _SEEDS[seed_key])
            print(f"  created {file_path}")
        else:
            print(f"  exists  {file_path}")

    # Create notes/mining-lessons.md placeholder
    notes_file = paths.notes_dir / "mining-lessons.md"
    if not notes_file.exists():
        notes_file.write_text("# Mining Lessons\n\nCollected experience notes.\n", encoding="utf-8")
        print(f"  created {notes_file}")
    else:
        print(f"  exists  {notes_file}")

    print(f"\nStorage initialised at: {paths.root.resolve()}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialise the new research storage tree")
    parser.add_argument("--root", default="storage", help="Storage root (default: storage)")
    args = parser.parse_args()
    init_storage(root=args.root)
=======
import sys
from datetime import datetime
from pathlib import Path

import yaml


# ---------------------------------------------------------------------------
# Directory tree
# ---------------------------------------------------------------------------

DIRS = [
    "state",
    "logic/proposals",
    "logic/reviews",
    "logic/cards",
    "logic/snapshots",
    "registry/factors",
    "registry/families",
    "policy",
    "ledger",
    "packets",
    "memory",
    "results",
    "candidates",
    "notes",
    "evaluation_profiles",
    "evidence/vault/factors",
    "evidence/vault/assets",
    "evidence/vault/batches",
]


# ---------------------------------------------------------------------------
# Seed files — each entry is (relative_path, data_dict | raw_text)
# ---------------------------------------------------------------------------

def _seed_files() -> list[tuple[str, object]]:
    """Return a list of (relative_path, content) pairs.

    Content is either a dict (dumped as YAML) or a str (written verbatim).
    """
    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    return [
        # -- state/ ----------------------------------------------------------
        (
            "state/research_state.yaml",
            {
                "research_state": {
                    "current_batch": None,
                    "sample_policy": {
                        "version": "v3",
                        "train": "2015-2021",
                        "validation": "2022-2023",
                        "support_windows": ["2015-2018", "2019-2021"],
                        "holdout": "2024-2025",
                    },
                    "active_logic_ids": [],
                    "validation_window_id": "val_2022_2023",
                    "policy_flags": {
                        "prefer_dsl": True,
                        "vectorization_required": True,
                    },
                    "last_updated_at": now,
                },
            },
        ),
        (
            "state/pending_holdout_queue.yaml",
            {"pending_holdout_queue": []},
        ),
        # -- logic/ -----------------------------------------------------------
        (
            "logic/registry.yaml",
            {"logics": []},
        ),
        # -- registry/ --------------------------------------------------------
        (
            "registry/factors/index.yaml",
            {"factors": []},
        ),
        (
            "registry/families/family_registry.yaml",
            {"families": []},
        ),
        # -- policy/ ----------------------------------------------------------
        (
            "policy/capability_registry.yaml",
            {
                "dsl_operators": [
                    "Ref", "Mean", "Sum", "Std", "Var", "Skew", "Kurt",
                    "Max", "Min", "Med", "Mad", "Rank", "Count", "Delta",
                    "Slope", "Rsquare", "Resi", "WMA", "EMA", "Corr", "Cov",
                    "Abs", "Sign", "Log", "Power", "Mul", "Add", "Sub",
                    "Div", "Greater", "Less", "And", "Or", "Not", "If",
                    "IdxMax", "IdxMin",
                ],
                "base_fields": [
                    "$open", "$high", "$low", "$close",
                    "$volume", "$amount",
                    "$pe_ratio", "$pb_ratio", "$ps_ratio",
                    "$market_cap", "$circ_market_cap", "$turnover_rate",
                ],
                "python_constraints": {
                    "vectorization_required": True,
                    "no_groupby_apply": True,
                    "no_iterrows": True,
                },
            },
        ),
        (
            "policy/implementation_policy.yaml",
            {
                "default": {
                    "prefer_dsl": True,
                    "vectorization_required": True,
                    "neutralization_default": "cap_industry",
                },
                "python_allowed_if": [
                    "route_requires_multi_stage_pipeline",
                    "route_requires_multi_state_logic",
                    "dsl_expression_unnatural",
                    "route_is_repair_or_decorrelate",
                    "helper_backed_complex_logic",
                ],
                "python_discouraged_if": [
                    "simple_breakout",
                    "simple_reversal",
                    "simple_rank_spread",
                    "only_window_variation",
                ],
            },
        ),
        (
            "policy/failure_taxonomy.yaml",
            {
                "failure_types": [
                    "weak_validation_effect",
                    "high_pairwise_overlap",
                    "hard_gate_rejected",
                    "implementation_blocked",
                    "performance_rejected",
                    "helper_required",
                    "regime_mismatch",
                    "unstable_oos",
                    "size_drift",
                    "style_repackaging",
                ],
            },
        ),
        (
            "policy/policy_upgrade_ledger.yaml",
            {"candidates": []},
        ),
        # -- ledger/ ----------------------------------------------------------
        (
            "ledger/search_ledger.yaml",
            {
                "by_logic": {},
                "by_family": {},
                "by_experiment_tag": {},
                "discovery_candidates": [],
            },
        ),
        (
            "ledger/batch_usage.yaml",
            {"batches": []},
        ),
        (
            "ledger/holdout_review_ledger.yaml",
            {"reviews": []},
        ),
        (
            "ledger/write_audit_log.yaml",
            {"entries": []},
        ),
        # -- memory/ ----------------------------------------------------------
        (
            "memory/forbidden.yaml",
            {"forbidden_patterns": []},
        ),
        # -- evaluation_profiles/ ---------------------------------------------
        (
            "evaluation_profiles/research_eval_v1.yaml",
            {
                "profile_id": "research_eval_v1",
                "universe": "csi1000",
                "tradability": "cn_t1_limit_v1",
                "preprocess": "default_rank_v1",
                "neutralization": "cap_industry_v1",
                "delay": 1,
                "horizon": 5,
                "pipeline": [
                    {
                        "stage": "probe",
                        "description": "Lightweight IC-only check, training period, full universe",
                    },
                    {
                        "stage": "stage1",
                        "description": "Fast IC screening on stock subset",
                    },
                    {
                        "stage": "stage2",
                        "description": "Full-universe IC, Sharpe, IC IR with correlation gate",
                    },
                    {
                        "stage": "stage3",
                        "description": "Out-of-sample IC, quintile returns, long-short, monotonicity",
                    },
                ],
                "auxiliary_views": [
                    "barra_residual_ic",
                    "style_drift_check",
                    "turnover_analysis",
                ],
            },
        ),
        # -- notes/ -----------------------------------------------------------
        (
            "notes/mining-lessons.md",
            "# Mining Lessons\n\nPlaceholder for accumulated mining lessons.\n",
        ),
    ]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def _dump_yaml(data: dict, path: Path) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        yaml.safe_dump(data, fh, sort_keys=False, allow_unicode=True)


def init_storage(root: Path) -> None:
    storage = root / "storage"
    if storage.exists():
        print(f"WARNING: {storage} already exists — seeding into it anyway.")

    # Create directories
    for d in DIRS:
        p = storage / d
        p.mkdir(parents=True, exist_ok=True)

    # Write seed files
    seed_files = _seed_files()
    for rel_path, content in seed_files:
        p = storage / rel_path
        p.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, str):
            p.write_text(content, encoding="utf-8")
        else:
            _dump_yaml(content, p)

    print(f"Initialized new storage tree at {storage}")
    print(f"  {len(DIRS)} directories created")
    print(f"  {len(seed_files)} seed files written")


def main() -> None:
    if len(sys.argv) > 1:
        root = Path(sys.argv[1]).resolve()
    else:
        root = Path(__file__).resolve().parent.parent

    init_storage(root)
>>>>>>> worktree-agent-a1d4eeec


if __name__ == "__main__":
    main()
