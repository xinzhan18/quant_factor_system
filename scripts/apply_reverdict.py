#!/usr/bin/env python3
"""Apply mechanical status transitions from the recompute v1 reverdict.

Reads ``_meta/recompute_v1_reverdict.md`` decisions and updates
``vault/factors/F*.yaml`` ``status`` field plus a structured
``recompute_reverdict`` block. The LLM judge can later re-promote or
permanent-retire any factor; this script only handles the obvious
mechanical drops.
"""

from __future__ import annotations

import argparse
import logging
from datetime import datetime, timezone

from research.storage.paths import StoragePaths
from research.storage.yaml_io import load_yaml, save_yaml

logger = logging.getLogger(__name__)


# Reverdict on primary universe = all_tradable (config.universes.primary).
# Floor: |ICIR| ≥ 0.15, |mono| ≥ 0.6, |IC_OOS| ≥ 0.008, mono·IC sign agree.
# (factor_id, new_status, reason)
DECISIONS: list[tuple[str, str, str]] = [
    ("F003", "retired", "all_tradable mono 1.0→0.40 under tradable_mask_v1 (PIT ST mask exposed reliance on ST reverse returns); below CP01 mono floor 0.6"),
    ("F010", "reserve", "all_tradable mono 1.0→0.40; overnight_return_persistence_5d ICIR 0.29 still respectable but no longer monotone"),
    ("F011", "reserve", "all_tradable mono 1.0→0.40; overnight_return_persistence_3d co-failed with F010 (same family, same regime)"),
    ("F013", "retired", "all_tradable mono 0.6→0.40, IC_OOS 0.0094 just above floor; signal incoherent under ST/suspend mask"),
    ("F014", "retired", "all_tradable mono 0.6→-0.6 (sign flip!) + IC_OOS 0.0044 below floor + ICIR 0.097→0.035; vwap_overnight_spread fully degenerate"),
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    paths = StoragePaths()
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    for fid, new_status, reason in DECISIONS:
        yaml_path = paths.factor_yaml_file(fid)
        record = load_yaml(yaml_path) or {}
        old_status = record.get("status", "active")
        record["status"] = new_status
        record["recompute_reverdict"] = {
            "old_status": old_status,
            "new_status": new_status,
            "reason": reason,
            "transitioned_at": timestamp,
            "audit_run": "tradable_mask_v1_st",
        }
        if new_status == "retired":
            record["retired_at"] = timestamp
        elif new_status == "reserve":
            record["reserved_at"] = timestamp

        if args.dry_run:
            logger.info("[dry-run] %s: %s → %s (%s)", fid, old_status, new_status, reason)
        else:
            save_yaml(yaml_path, record)
            logger.info("%s: %s → %s", fid, old_status, new_status)


if __name__ == "__main__":
    main()
