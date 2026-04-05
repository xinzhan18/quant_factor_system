#!/usr/bin/env python3
"""Create the new storage/ directory tree with seed YAML files."""

import sys
from pathlib import Path

import yaml

DIRS = [
    "state",
    "logic/proposals", "logic/reviews", "logic/cards", "logic/snapshots",
    "registry/factors", "registry/families",
    "policy",
    "ledger",
    "packets",
    "memory",
    "results",
    "candidates",
    "notes",
    "evaluation_profiles",
    "evidence/vault/factors", "evidence/vault/assets", "evidence/vault/batches",
]

SEED_FILES = {
    "state/research_state.yaml": {
        "research_state": {
            "current_batch": None,
            "sample_policy": {
                "version": "research_sample_v3",
                "data_start": "2015-01-01",
                "active_train_range": ["2015-01-01", "2021-12-31"],
                "active_validation_range": ["2022-01-01", "2023-12-31"],
                "support_validation_windows": [
                    {"window_id": "val_2020_2021", "range": ["2020-01-01", "2021-12-31"]},
                    {"window_id": "val_2021_2022", "range": ["2021-01-01", "2022-12-31"]},
                    {"window_id": "val_2022_2023", "range": ["2022-01-01", "2023-12-31"]},
                ],
                "holdout_pool_range": ["2024-01-01", "2025-12-31"],
            },
            "active_logic_ids": [],
            "active_experiment_groups": [],
            "current_focus": [],
            "current_bottlenecks": [],
            "current_validation_window_id": "val_2022_2023",
            "policy_flags": {"prefer_dsl": True, "vectorization_required": True},
            "last_updated_at": None,
        }
    },
    "state/pending_holdout_queue.yaml": {"pending_holdout_queue": []},
    "logic/registry.yaml": {"logics": []},
    "registry/factors/index.yaml": {"factors": []},
    "registry/families/family_registry.yaml": {"families": []},
    "policy/capability_registry.yaml": {
        "dsl_operators": [
            "Ref", "Mean", "Sum", "Std", "Var", "Rank", "Count", "Delta",
            "Max", "Min", "Corr", "Cov", "Abs", "Log", "Mul", "Add", "Sub",
            "Div", "Greater", "Less", "If", "IdxMax", "IdxMin", "WMA", "EMA",
        ],
        "base_fields": [
            "$open", "$high", "$low", "$close", "$volume", "$amount",
            "$pe_ratio", "$pb_ratio", "$ps_ratio",
            "$market_cap", "$circ_market_cap", "$turnover_rate",
        ],
        "python_constraints": {"max_lines": 30, "max_branches": 3, "max_params": 3},
    },
    "policy/implementation_policy.yaml": {
        "prefer_dsl": True,
        "vectorization_required": True,
        "neutralization_default": "cap_industry",
    },
    "policy/failure_taxonomy.yaml": {
        "failure_types": [
            "weak_validation_effect", "high_pairwise_overlap", "high_family_overlap",
            "implementation_blocked", "performance_rejected", "validation_instability",
            "size_drift", "style_repackaging", "sign_flip_detected",
            "feasibility_poor", "mechanism_drifted",
        ]
    },
    "policy/policy_upgrade_ledger.yaml": {"policy_upgrade_candidates": []},
    "ledger/search_ledger.yaml": {
        "search_ledger": {
            "by_logic": {},
            "by_family": {},
            "by_experiment_tag": {},
            "discovery_candidates": [],
        }
    },
    "ledger/batch_usage.yaml": {"batches": []},
    "ledger/holdout_review_ledger.yaml": {"holdout_reviews": []},
    "ledger/write_audit_log.yaml": {"entries": []},
    "memory/forbidden.yaml": {"forbidden_patterns": []},
    "evaluation_profiles/research_eval_v1.yaml": {
        "evaluation_profile": {
            "profile_id": "research_eval_v1",
            "universe_profile": "csi1000",
            "tradability_profile": "cn_t1_limit_v1",
            "preprocess_profile": "default_rank_v1",
            "neutralization_profile": "cap_industry_v1",
            "delay": 1,
            "holding_horizon": 5,
            "primary_pipeline": ["universe_mask", "tradability_mask", "winsorize", "zscore_or_rank", "neutralization"],
            "auxiliary_views": ["raw_view", "cap_industry_neutral_view", "barra_residual_view"],
        }
    },
}


def init_storage(root: Path) -> None:
    storage = root / "storage"
    for d in DIRS:
        (storage / d).mkdir(parents=True, exist_ok=True)

    for rel_path, data in SEED_FILES.items():
        p = storage / rel_path
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w") as f:
            yaml.safe_dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    # Mining lessons placeholder
    notes = storage / "notes" / "mining-lessons.md"
    if not notes.exists():
        notes.write_text("# Mining Lessons\n\nAccumulated knowledge from factor research.\n")

    print(f"Initialized new storage at {storage}")
    print(f"  {len(DIRS)} directories, {len(SEED_FILES)} seed files")


if __name__ == "__main__":
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
    init_storage(root)
