"""Experience Memory management for factor mining."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List

import yaml

from .config import MiningConfig

logger = logging.getLogger(__name__)


class ExperienceMemory:
    """Read/write YAML-based Experience Memory."""

    def __init__(self, config: MiningConfig):
        self._dir = Path(config.memory_dir)
        self._history_dir = self._dir / "history"
        self._history_dir.mkdir(parents=True, exist_ok=True)

    def read_state(self) -> Dict[str, Any]:
        return self._read_yaml(self._dir / "state.yaml")

    def read_patterns(self) -> Dict[str, Any]:
        return self._read_yaml(self._dir / "patterns.yaml")

    def read_insights(self) -> Dict[str, Any]:
        return self._read_yaml(self._dir / "insights.yaml")

    def write_state(self, data: Dict[str, Any]) -> None:
        self._write_yaml(self._dir / "state.yaml", data)

    def write_patterns(self, data: Dict[str, Any]) -> None:
        self._write_yaml(self._dir / "patterns.yaml", data)

    def write_insights(self, data: Dict[str, Any]) -> None:
        self._write_yaml(self._dir / "insights.yaml", data)

    def save_batch_history(self, batch_id: str, data: Dict[str, Any]) -> None:
        self._write_yaml(self._history_dir / f"{batch_id}.yaml", data)

    def load_batch_history(self, batch_id: str) -> Dict[str, Any]:
        return self._read_yaml(self._history_dir / f"{batch_id}.yaml")

    def list_batch_history(self) -> List[str]:
        return sorted(p.stem for p in self._history_dir.glob("batch_*.yaml"))

    def compose_search_context(self) -> str:
        """Compose Memory into a prompt-ready string for Claude."""
        parts = []
        state = self.read_state()
        parts.append("## Current Mining State")
        parts.append(f"Library size: {state.get('library', {}).get('size', 0)}")
        sat = state.get("domain_saturation", {})
        if sat:
            sat_lines = [f"  - {k}: {v.get('count', 0)} factors ({v.get('saturation', 'low')})" for k, v in sat.items()]
            parts.append("Domain saturation:\n" + "\n".join(sat_lines))
        patterns = self.read_patterns()
        rec = patterns.get("recommended_directions", [])
        if rec:
            parts.append("\n## Recommended Directions")
            for p in rec:
                parts.append(f"- **{p['pattern']}** ({p.get('success_rate', 'unknown')}): {p['description']}")
        forbidden = patterns.get("forbidden_regions", [])
        if forbidden:
            parts.append("\n## Forbidden Regions (AVOID)")
            for f in forbidden:
                parts.append(f"- {f['direction']}: {f['reason']}")
        insights = self.read_insights()
        ins_list = insights.get("insights", [])
        if ins_list:
            parts.append("\n## Strategic Insights")
            for i in ins_list:
                parts.append(f"- [{i.get('confidence', '?')}] {i['insight']}")
        return "\n".join(parts)

    def _read_yaml(self, path: Path) -> Dict[str, Any]:
        if not path.exists():
            logger.warning("Memory file not found: %s", path)
            return {}
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def _write_yaml(self, path: Path, data: Dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
