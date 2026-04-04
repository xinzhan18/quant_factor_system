"""JudgePacket and ContextSnapshot read/write.

Manages ``packets/<packet_id>.yaml``.
"""

from __future__ import annotations

import logging
from typing import List

from research.storage.paths import StoragePaths
from research.storage.yaml_io import glob_stems, load_yaml, save_yaml

logger = logging.getLogger(__name__)


class PacketStore:
    """CRUD for judge packets and context snapshots."""

    def __init__(self, paths: StoragePaths) -> None:
        self.paths = paths

    def load(self, packet_id: str) -> dict:
        """Load a single packet."""
        return load_yaml(self.paths.packet(packet_id))

    def save(self, packet_id: str, packet: dict) -> None:
        """Persist a single packet."""
        save_yaml(self.paths.packet(packet_id), packet)

    def list_ids(self) -> List[str]:
        """Return packet IDs (filenames without .yaml) sorted by name."""
        return glob_stems(self.paths.packets_dir)
