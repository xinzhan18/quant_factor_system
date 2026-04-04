"""ResearchResult, ExecuteReport, and JudgeReport read/write.

Manages:
- ``results/<batch_id>_result.yaml``
- ``results/<batch_id>_execute_report.yaml``
- ``results/<batch_id>_judge_report.yaml``

Result files may contain pandas objects, so loading uses ``load_yaml_unsafe``
by default.
"""

from __future__ import annotations

import logging
from typing import List

from research.storage.paths import StoragePaths
from research.storage.yaml_io import load_yaml_unsafe, save_yaml

logger = logging.getLogger(__name__)


class ResultStore:
    """CRUD for evaluation results, execute reports, and judge reports."""

    def __init__(self, paths: StoragePaths) -> None:
        self.paths = paths

    # ------------------------------------------------------------------
    # result
    # ------------------------------------------------------------------
    def load_result(self, batch_id: str) -> dict:
        """Load a batch result (unsafe — may contain pandas objects)."""
        return load_yaml_unsafe(self.paths.batch_result(batch_id))

    def save_result(self, batch_id: str, result: dict) -> None:
        """Persist a batch result."""
        save_yaml(self.paths.batch_result(batch_id), result)

    # ------------------------------------------------------------------
    # execute report
    # ------------------------------------------------------------------
    def load_execute_report(self, batch_id: str) -> dict:
        """Load an execute report (unsafe)."""
        return load_yaml_unsafe(self.paths.batch_execute_report(batch_id))

    def save_execute_report(self, batch_id: str, report: dict) -> None:
        save_yaml(self.paths.batch_execute_report(batch_id), report)

    # ------------------------------------------------------------------
    # judge report
    # ------------------------------------------------------------------
    def load_judge_report(self, batch_id: str) -> dict:
        """Load a judge report (unsafe)."""
        return load_yaml_unsafe(self.paths.batch_judge_report(batch_id))

    def save_judge_report(self, batch_id: str, report: dict) -> None:
        save_yaml(self.paths.batch_judge_report(batch_id), report)

    # ------------------------------------------------------------------
    # listing
    # ------------------------------------------------------------------
    def list_result_batch_ids(self) -> List[str]:
        """Return batch IDs that have a ``_result.yaml`` file."""
        d = self.paths.results_dir
        if not d.exists():
            return []
        ids = []
        for p in d.glob("*_result.yaml"):
            bid = p.stem.replace("_result", "")
            ids.append(bid)
        return sorted(ids)
