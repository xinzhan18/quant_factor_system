"""JudgePacket and ContextSnapshot read/write.

Manages per-batch files under ``packets/``:
- ``<batch_id>_judge_packet.yaml``
- ``<batch_id>_context_snapshot.yaml``
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
        return load_yaml(self._paths.judge_packet_file(batch_id))

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
        d = self._paths.packets_dir
        if not d.exists():
            return []
        return sorted(
            p.stem.replace("_judge_packet", "")
            for p in d.glob("*_judge_packet.yaml")
        )
