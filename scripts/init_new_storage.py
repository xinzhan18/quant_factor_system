#!/usr/bin/env python3
"""Create the new storage/ directory tree with seed YAML files."""

import sys
from pathlib import Path

import yaml

DIRS = [
    "state",
    "logic/proposals", "logic/reviews", "logic/cards", "logic/snapshots",
    "registry/factors", "registry/families",
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
        "current_batch": None,
        "current_batch_phase": None,
        "active_logic_ids": [],
        "pending_holdout_count": 0,
        "last_completed_batch": None,
        "last_updated_at": None,
    },
    "state/pending_holdout_queue.yaml": {"pending_holdout_queue": []},
    "logic/registry.yaml": {"logics": []},
    "registry/factors/index.yaml": {"factors": []},
    "registry/families/family_registry.yaml": {"families": []},
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
