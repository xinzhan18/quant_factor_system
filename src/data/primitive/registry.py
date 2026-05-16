"""Primitive registry loader."""

from __future__ import annotations

from pathlib import Path

from data.primitive.schema import PrimitiveSpec
from research.storage.yaml_io import load_yaml


class PrimitiveRegistry:
    """Load and resolve primitive specs from a registry directory."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def load_all(self) -> dict[str, PrimitiveSpec]:
        specs: dict[str, PrimitiveSpec] = {}
        if not self.root.exists():
            return specs
        for path in sorted(self.root.glob("*.yaml")):
            data = load_yaml(path)
            if not data:
                continue
            spec = PrimitiveSpec.from_dict(data)
            if spec.feature_id in specs:
                raise ValueError(f"duplicate primitive feature_id: {spec.feature_id}")
            specs[spec.feature_id] = spec
        return specs

    def resolve_many(self, feature_ids: list[str]) -> list[PrimitiveSpec]:
        specs = self.load_all()
        missing = [fid for fid in feature_ids if fid not in specs]
        if missing:
            raise FileNotFoundError(
                f"primitive specs missing from {self.root}: {missing}"
            )
        return [specs[fid] for fid in feature_ids]

