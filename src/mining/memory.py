"""Experience Memory management for factor mining."""

from __future__ import annotations

import logging
import re
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
        self._directions_dir = self._dir / "directions"
        self._directions_dir.mkdir(parents=True, exist_ok=True)
        self._directions_index = self._dir / "directions.yaml"

    def read_state(self) -> Dict[str, Any]:
        return self._read_yaml(self._dir / "state.yaml")

    def read_patterns(self) -> Dict[str, Any]:
        return self._read_yaml(self._dir / "patterns.yaml")

    def write_state(self, data: Dict[str, Any]) -> None:
        self._write_yaml(self._dir / "state.yaml", data)

    def write_patterns(self, data: Dict[str, Any]) -> None:
        self._write_yaml(self._dir / "patterns.yaml", data)

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
        # 挖掘经验教训从 mining-lessons.md 加载（叙事性内容，由 skill 直接读取）
        return "\n".join(parts)

    def list_directions(self) -> List[Dict[str, Any]]:
        """Read directions.yaml index. Rebuilds from files if index missing."""
        if self._directions_index.exists():
            with open(self._directions_index, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or []
        return self._rebuild_directions_index()

    def read_direction(self, name: str) -> tuple:
        """Read a direction file. Returns (frontmatter_dict, body_str)."""
        path = self._directions_dir / f"{name}.md"
        if not path.exists():
            raise FileNotFoundError(f"Direction not found: {name}")
        text = path.read_text(encoding="utf-8")
        return self._parse_frontmatter(text)

    def write_direction(self, name: str, frontmatter: Dict[str, Any], body: str = "") -> None:
        """Write a direction file and update index."""
        path = self._directions_dir / f"{name}.md"
        text = self._render_frontmatter(frontmatter, body)
        path.write_text(text, encoding="utf-8")
        self._sync_index()

    def update_direction(self, name: str, **updates) -> None:
        """Update frontmatter fields of a direction file."""
        meta, body = self.read_direction(name)
        meta.update(updates)
        self.write_direction(name, meta, body)

    def append_to_direction(self, name: str, text: str) -> None:
        """Append text to the body of a direction file."""
        meta, body = self.read_direction(name)
        body = body.rstrip() + "\n" + text
        self.write_direction(name, meta, body)

    def _parse_frontmatter(self, text: str) -> tuple:
        """Parse YAML frontmatter from markdown. Returns (dict, body_str)."""
        match = re.match(r'^---\n(.*?)\n---\n?(.*)', text, re.DOTALL)
        if not match:
            return {}, text
        fm = yaml.safe_load(match.group(1)) or {}
        body = match.group(2).lstrip('\n')  # strip separator artifact
        return fm, body

    def _render_frontmatter(self, meta: Dict[str, Any], body: str) -> str:
        """Render frontmatter + body into markdown string."""
        fm = yaml.dump(meta, default_flow_style=False, allow_unicode=True, sort_keys=False)
        return f"---\n{fm}---\n\n{body}"

    def _sync_index(self) -> None:
        """Rebuild directions.yaml from all direction files."""
        index = self._rebuild_directions_index()
        self._write_yaml(self._directions_index, index)

    def _rebuild_directions_index(self) -> List[Dict[str, Any]]:
        """Scan direction files and build index."""
        index = []
        for path in sorted(self._directions_dir.glob("*.md")):
            meta, _ = self._parse_frontmatter(path.read_text(encoding="utf-8"))
            if meta:
                index.append({
                    "name": meta.get("name", path.stem),
                    "status": meta.get("status", "new"),
                    "priority": meta.get("priority", "medium"),
                    "category": meta.get("category", "other"),
                    "attempts": meta.get("attempts", 0),
                    "best_ic": meta.get("best_ic"),
                })
        return index

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
