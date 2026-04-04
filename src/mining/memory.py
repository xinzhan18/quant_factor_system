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
        self._config = config  # stored for logic_dir and other path references
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

    # --- Typed history (eval / admission subdirectories) ---

    @property
    def _eval_history_dir(self) -> Path:
        d = self._history_dir / "eval"
        d.mkdir(parents=True, exist_ok=True)
        return d

    @property
    def _admission_history_dir(self) -> Path:
        d = self._history_dir / "admission"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def save_eval_history(self, batch_id: str, data: Dict[str, Any]) -> None:
        self._write_yaml(self._eval_history_dir / f"{batch_id}.yaml", data)

    def save_admission_history(self, batch_id: str, data: Dict[str, Any]) -> None:
        self._write_yaml(self._admission_history_dir / f"{batch_id}.yaml", data)

    def list_eval_history(self) -> List[str]:
        return sorted(p.stem for p in self._eval_history_dir.glob("batch_*.yaml"))

    def list_admission_history(self) -> List[str]:
        return sorted(p.stem for p in self._admission_history_dir.glob("batch_*.yaml"))

    # --- Direction audit ---

    def audit_directions(self, candidates_dir: str) -> List[Dict[str, Any]]:
        """Compare recorded direction states vs actual batch participation.

        Returns a list of mismatch dicts (read-only, does not modify files).
        """
        mismatches: List[Dict[str, Any]] = []
        directions = self.list_directions()

        # Count actual participation from batch files
        actual_counts: Dict[str, set] = {}
        cdir = Path(candidates_dir)
        for batch_file in cdir.glob("batch_*.yaml"):
            if "_result" in batch_file.name or "_values" in batch_file.name:
                continue
            try:
                with open(batch_file) as f:
                    batch = yaml.safe_load(f) or {}
                batch_id = batch.get("batch_id", batch_file.stem)
                for c in batch.get("candidates", []):
                    d = c.get("direction", "")
                    if d:
                        actual_counts.setdefault(d, set()).add(batch_id)
            except Exception:
                continue

        for d in directions:
            name = d["name"]
            recorded = d.get("attempts", 0)
            actual = len(actual_counts.get(name, set()))

            if recorded != actual:
                mismatches.append({
                    "direction": name,
                    "recorded_attempts": recorded,
                    "observed_attempts": actual,
                    "status": d["status"],
                    "flag": "attempts_mismatch",
                })
            if recorded == 0 and d["status"] in ("exhausted", "dead"):
                mismatches.append({
                    "direction": name,
                    "recorded_attempts": recorded,
                    "observed_attempts": actual,
                    "status": d["status"],
                    "flag": "zero_attempts_terminal_status",
                })
        return mismatches

    def compose_search_context(self) -> str:
        """Deprecated -- use mining.application.context_service.compose_search_context()."""
        from mining.application.context_service import compose_search_context
        return compose_search_context(self._config)

    def get_lineage_summary(self) -> str:
        """Deprecated -- use mining.application.context_service."""
        from mining.application.context_service import _get_lineage_summary
        return _get_lineage_summary(self._config)

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

    # ------------------------------------------------------------------
    # Forbidden regions
    # ------------------------------------------------------------------

    def read_forbidden(self) -> list[dict]:
        """Read all forbidden regions from forbidden.yaml."""
        data = self._read_yaml(self._dir / "forbidden.yaml")
        return data.get("forbidden_regions", [])

    def add_forbidden(self, pattern: str, reason: str) -> None:
        """Add a new forbidden region pattern."""
        from datetime import date

        regions = self.read_forbidden()
        regions.append({
            "pattern": pattern,
            "reason": reason,
            "added": str(date.today()),
        })
        self._write_yaml(self._dir / "forbidden.yaml", {"forbidden_regions": regions})

    def check_forbidden(self, expression: str) -> str | None:
        """Check if expression matches any forbidden region.

        Returns the reason string if matched, or None if the expression is
        not forbidden.  Pattern syntax: ``*`` matches ``[\\w.]+``.
        """
        for entry in self.read_forbidden():
            raw = entry.get("pattern", "")
            # Escape the pattern except for our wildcard placeholder
            escaped = re.escape(raw).replace(r"\*", r"[\w.]+")
            if re.search(escaped, expression):
                return entry.get("reason", "")
        return None

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
