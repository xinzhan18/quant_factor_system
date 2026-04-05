"""ResearchResult, ExecuteReport, and JudgeReport read/write.

Manages per-batch files under ``batches/<batch_id>/``:
- ``research_result.yaml``
- ``execute_report.yaml``
- ``judge_report.yaml``
"""

from __future__ import annotations

from typing import Any

from .paths import StoragePaths
from .yaml_io import load_yaml, save_yaml


class ResultStore:
    """CRUD for evaluation results, execute reports, and judge reports."""

    def __init__(self, paths: StoragePaths) -> None:
        self._paths = paths

    # ------------------------------------------------------------------
    # result
    # ------------------------------------------------------------------

    def load_result(self, batch_id: str) -> dict[str, Any]:
        return load_yaml(self._paths.result_file(batch_id))

    def save_result(self, batch_id: str, data: dict[str, Any]) -> None:
        data["batch_id"] = batch_id
        save_yaml(self._paths.result_file(batch_id), data)

    # ------------------------------------------------------------------
    # execute report
    # ------------------------------------------------------------------

    def load_execute_report(self, batch_id: str) -> dict[str, Any]:
        return load_yaml(self._paths.execute_report_file(batch_id))

    def save_execute_report(self, batch_id: str, data: dict[str, Any]) -> None:
        data["batch_id"] = batch_id
        save_yaml(self._paths.execute_report_file(batch_id), data)

    # ------------------------------------------------------------------
    # judge report
    # ------------------------------------------------------------------

    def load_judge_report(self, batch_id: str) -> dict[str, Any]:
        return load_yaml(self._paths.judge_report_file(batch_id))

    def save_judge_report(self, batch_id: str, data: dict[str, Any]) -> None:
        data["batch_id"] = batch_id
        save_yaml(self._paths.judge_report_file(batch_id), data)

    # ------------------------------------------------------------------
    # listing
    # ------------------------------------------------------------------

    def list_results(self) -> list[str]:
        """Return batch_ids that have a result file."""
        d = self._paths.batches_dir
        if not d.exists():
            return []
        return sorted(
            p.name
            for p in d.iterdir()
            if p.is_dir() and (p / "research_result.yaml").exists()
        )
