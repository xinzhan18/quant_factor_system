"""JudgePacket and ContextSnapshot read/write.

Manages per-batch files under ``batches/<batch_id>/``:
- ``judge_packet.yaml``
- ``context_snapshot.yaml``
"""

from __future__ import annotations

from typing import Any

from .paths import StoragePaths
from .yaml_io import load_yaml, save_yaml


class PacketStore:
    """CRUD for judge packets and context snapshots."""

    def __init__(self, paths: StoragePaths) -> None:
        self._paths = paths

    # ------------------------------------------------------------------
    # judge_packet
    # ------------------------------------------------------------------

    def load_judge_packet(self, batch_id: str) -> dict[str, Any]:
        data = load_yaml(self._paths.judge_packet_file(batch_id))
        # Unwrap nested judge_packet: key if present (newer format)
        if "judge_packet" in data and isinstance(data["judge_packet"], dict):
            return data["judge_packet"]
        return data

    def save_judge_packet(self, batch_id: str, data: dict[str, Any]) -> None:
        data["batch_id"] = batch_id
        save_yaml(self._paths.judge_packet_file(batch_id), data)

    # ------------------------------------------------------------------
    # context_snapshot
    # ------------------------------------------------------------------

    def load_context_snapshot(self, batch_id: str) -> dict[str, Any]:
        return load_yaml(self._paths.context_snapshot_file(batch_id))

    def save_context_snapshot(self, batch_id: str, data: dict[str, Any]) -> None:
        data["batch_id"] = batch_id
        save_yaml(self._paths.context_snapshot_file(batch_id), data)

    # ------------------------------------------------------------------
    # listing
    # ------------------------------------------------------------------

    def list_packets(self) -> list[str]:
        """Return batch_ids that have judge packets."""
        d = self._paths.batches_dir
        if not d.exists():
            return []
        return sorted(
            p.name
            for p in d.iterdir()
            if p.is_dir() and (p / "judge_packet.yaml").exists()
        )
