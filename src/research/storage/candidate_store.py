"""BatchManifest and IdeaReport read/write.

Manages per-batch files under ``batches/<batch_id>/``:
- ``manifest.yaml`` (batch manifest / candidate list)
- ``idea_report.yaml``
"""

from __future__ import annotations

from typing import Any

from .paths import StoragePaths
from .yaml_io import load_yaml, save_yaml


class CandidateStore:
    """CRUD for batch manifests and idea reports."""

    def __init__(self, paths: StoragePaths) -> None:
        self._paths = paths

    # ------------------------------------------------------------------
    # batch manifest
    # ------------------------------------------------------------------

    def load_manifest(self, batch_id: str) -> dict[str, Any]:
        return load_yaml(self._paths.batch_manifest_file(batch_id))

    def save_manifest(self, batch_id: str, data: dict[str, Any]) -> None:
        data["batch_id"] = batch_id
        save_yaml(self._paths.batch_manifest_file(batch_id), data)

    # ------------------------------------------------------------------
    # idea report
    # ------------------------------------------------------------------

    def load_idea_report(self, batch_id: str) -> dict[str, Any]:
        return load_yaml(self._paths.idea_report_file(batch_id))

    def save_idea_report(self, batch_id: str, data: dict[str, Any]) -> None:
        data["batch_id"] = batch_id
        save_yaml(self._paths.idea_report_file(batch_id), data)

    # ------------------------------------------------------------------
    # listing
    # ------------------------------------------------------------------

    def list_manifests(self) -> list[str]:
        """Return batch_ids that have a manifest file."""
        d = self._paths.batches_dir
        if not d.exists():
            return []
        return sorted(
            p.name
            for p in d.iterdir()
            if p.is_dir() and (p / "manifest.yaml").exists()
        )
