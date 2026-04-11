"""Tests for direction frontmatter surgical update."""

from __future__ import annotations

from pathlib import Path

import yaml

from research.memory.direction_updater import update_direction_frontmatter


def _read_fm(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    end = text.find("\n---", 4)
    return yaml.safe_load(text[4:end])


class TestFirstUpdate:
    def test_creates_file_with_skeleton(self, tmp_path: Path) -> None:
        path = tmp_path / "dirs" / "fp_divergence.md"
        fm = update_direction_frontmatter(
            path,
            batch_id="batch_001",
            new_admits=["F020", "F021"],
            goal="Probe fundamental × price divergence on csi1000",
        )
        assert path.exists()
        assert fm["direction_id"] == "fp_divergence"
        assert fm["rounds"] == 1
        assert fm["admits"] == 2
        assert fm["members"] == ["F020", "F021"]
        assert fm["last_batch"] == "batch_001"
        assert fm["last_admits"] == ["F020", "F021"]
        assert "last_activity" in fm
        assert fm["last_goal"].startswith("Probe")


class TestIncrementalUpdate:
    def test_increments_counters(self, tmp_path: Path) -> None:
        path = tmp_path / "fp.md"
        update_direction_frontmatter(
            path, batch_id="batch_001", new_admits=["F020"]
        )
        update_direction_frontmatter(
            path, batch_id="batch_002", new_admits=["F021", "F022"]
        )
        fm = _read_fm(path)
        assert fm["rounds"] == 2
        assert fm["admits"] == 3
        assert fm["members"] == ["F020", "F021", "F022"]
        assert fm["last_batch"] == "batch_002"
        assert fm["last_admits"] == ["F021", "F022"]

    def test_members_deduped(self, tmp_path: Path) -> None:
        path = tmp_path / "fp.md"
        update_direction_frontmatter(
            path, batch_id="batch_001", new_admits=["F020"]
        )
        # Weird case: same id re-admitted (shouldn't happen but be safe)
        update_direction_frontmatter(
            path, batch_id="batch_002", new_admits=["F020", "F021"]
        )
        fm = _read_fm(path)
        assert fm["members"] == ["F020", "F021"]

    def test_preserves_body(self, tmp_path: Path) -> None:
        path = tmp_path / "fp.md"
        path.write_text(
            "---\n"
            "direction_id: fp\n"
            "rounds: 5\n"
            "admits: 3\n"
            "members: [F020, F021, F022]\n"
            "---\n"
            "\n# fp_divergence\n\n## Hypothesis\n\nLLM-written narrative here.\n"
            "\n## Thread T001\n\nMore prose.\n",
            encoding="utf-8",
        )
        update_direction_frontmatter(
            path, batch_id="batch_006", new_admits=["F023"]
        )
        text = path.read_text(encoding="utf-8")
        # Body prose preserved verbatim
        assert "LLM-written narrative here." in text
        assert "## Thread T001" in text
        # Counters incremented
        fm = _read_fm(path)
        assert fm["rounds"] == 6
        assert fm["admits"] == 4
        assert fm["members"] == ["F020", "F021", "F022", "F023"]
