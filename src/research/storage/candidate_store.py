"""BatchManifest and IdeaReport read/write.

Manages:
- ``candidates/<batch_id>.yaml`` — the batch manifest
- ``candidates/<batch_id>_idea_report.yaml`` — the idea report
"""

from __future__ import annotations

import logging
from typing import List

from research.storage.paths import StoragePaths
from research.storage.yaml_io import load_yaml, save_yaml

logger = logging.getLogger(__name__)


class CandidateStore:
    """CRUD for batch manifests and idea reports."""

    def __init__(self, paths: StoragePaths) -> None:
        self.paths = paths

    # ------------------------------------------------------------------
    # batch manifest
    # ------------------------------------------------------------------
    def load_manifest(self, batch_id: str) -> dict:
        """Load a batch manifest."""
        return load_yaml(self.paths.batch_manifest(batch_id))

    def save_manifest(self, batch_id: str, manifest: dict) -> None:
        """Persist a batch manifest."""
        save_yaml(self.paths.batch_manifest(batch_id), manifest)

    # ------------------------------------------------------------------
    # idea report
    # ------------------------------------------------------------------
    def load_idea_report(self, batch_id: str) -> dict:
        """Load an idea report for a batch."""
        return load_yaml(self.paths.batch_idea_report(batch_id))

    def save_idea_report(self, batch_id: str, report: dict) -> None:
        """Persist an idea report."""
        save_yaml(self.paths.batch_idea_report(batch_id), report)

    # ------------------------------------------------------------------
    # listing
    # ------------------------------------------------------------------
    def list_batch_ids(self) -> List[str]:
        """Return batch IDs inferred from manifest files on disk.

        Looks for files matching ``<batch_id>.yaml`` that do *not* end
        with ``_idea_report``.
        """
        d = self.paths.candidates_dir
        if not d.exists():
            return []
        ids = []
        for p in d.glob("*.yaml"):
            stem = p.stem
            if stem.endswith("_idea_report"):
                continue
            ids.append(stem)
        return sorted(ids)
