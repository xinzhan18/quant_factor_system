"""Tests for direction frontmatter surgical update."""

from __future__ import annotations

from pathlib import Path

import yaml

from research.memory.direction_updater import (
    sync_status_from_judge,
    update_direction_frontmatter,
)


def _read_fm(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    end = text.find("\n---", 4)
    return yaml.safe_load(text[4:end])


class TestFirstUpdate:
    def test_creates_file_with_skeleton_and_auto_promotes_on_admit(
        self, tmp_path: Path
    ) -> None:
        path = tmp_path / "dirs" / "fp_divergence.md"
        fm = update_direction_frontmatter(
            path,
            batch_id="batch_001",
            new_admits=["F020", "F021"],
            goal="Probe fundamental × price divergence on csi1000",
        )
        assert path.exists()
        assert fm["direction_id"] == "fp_divergence"
        # Auto-promotion: first admit flips exploring → productive in-place.
        assert fm["status"] == "productive"
        assert fm["rounds"] == 1
        assert fm["admits"] == 2
        assert fm["members"] == ["F020", "F021"]
        assert fm["last_batch"] == "batch_001"
        assert fm["last_admits"] == ["F020", "F021"]
        assert "last_activity" in fm
        assert "created_at" in fm
        assert fm["created_batch"] == "batch_001"
        assert fm["last_goal"].startswith("Probe")

    def test_creates_file_without_admits_stays_exploring(
        self, tmp_path: Path
    ) -> None:
        path = tmp_path / "dirs" / "fp_divergence.md"
        fm = update_direction_frontmatter(
            path,
            batch_id="batch_001",
            new_admits=[],
            goal="Initial probe",
        )
        assert fm["status"] == "exploring"


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


class TestSyncStatusFromJudge:
    """Bug 5/6 — reconcile LLM judge narrative with frontmatter + threads."""

    def _seed(self, path: Path, status: str, body: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            f"---\ndirection_id: {path.stem}\nstatus: {status}\nrounds: 1\nadmits: 0\n---\n{body}",
            encoding="utf-8",
        )

    def test_dead_transition_flips_status_and_closes_threads(
        self, tmp_path: Path
    ) -> None:
        path = tmp_path / "asym.md"
        self._seed(
            path,
            "exploring",
            "\n## Threads\n### T001: foo [◉ ACTIVE]\n\n### T002: bar [◉ ACTIVE]\n",
        )
        judge = (
            "## 方向级反思\n"
            "direction status `exploring → dead` — 首批即 hard_gate。\n"
        )
        sync_status_from_judge(path, judge_body=judge, batch_id="batch_028")
        fm = _read_fm(path)
        body = path.read_text(encoding="utf-8")
        assert fm["status"] == "dead"
        assert "[◉ ACTIVE]" not in body
        assert body.count("[✗ DISPROVEN batch_028]") == 2

    def test_saturated_transition_keeps_threads(self, tmp_path: Path) -> None:
        path = tmp_path / "ohlc.md"
        self._seed(
            path,
            "productive",
            "\n### T001: foo [◉ ACTIVE]\n",
        )
        judge = "Direction status `productive → saturated`. 信号家族穷尽。\n"
        sync_status_from_judge(path, judge_body=judge, batch_id="batch_021")
        fm = _read_fm(path)
        body = path.read_text(encoding="utf-8")
        assert fm["status"] == "saturated"
        # Saturated does NOT auto-close threads (direction may reopen later)
        assert "[◉ ACTIVE]" in body

    def test_first_batch_dead_shortcut(self, tmp_path: Path) -> None:
        path = tmp_path / "asym.md"
        self._seed(
            path,
            "exploring",
            "\n### T001: up-only [◉ ACTIVE]\n### T002: down-only [◉ ACTIVE]\n",
        )
        judge = "direction 首批 dead — 3/3 hard_gate sign_flip。\n"
        sync_status_from_judge(path, judge_body=judge, batch_id="batch_028")
        fm = _read_fm(path)
        body = path.read_text(encoding="utf-8")
        assert fm["status"] == "dead"
        assert "[◉ ACTIVE]" not in body

    def test_noop_when_no_transition_phrase(self, tmp_path: Path) -> None:
        path = tmp_path / "amt.md"
        self._seed(path, "productive", "\nSome narrative without transitions.\n")
        sync_status_from_judge(
            path, judge_body="候选 C001 admit. 下批继续。", batch_id="batch_002"
        )
        fm = _read_fm(path)
        assert fm["status"] == "productive"  # unchanged

    def test_disallowed_transition_ignored(self, tmp_path: Path) -> None:
        """productive → exploring is not in the allowed set — Python should not apply it."""
        path = tmp_path / "foo.md"
        self._seed(path, "productive", "\n")
        sync_status_from_judge(
            path,
            judge_body="direction status `productive → exploring`",
            batch_id="batch_010",
        )
        fm = _read_fm(path)
        assert fm["status"] == "productive"

    def test_status_already_dead_still_closes_leftover_active_threads(
        self, tmp_path: Path
    ) -> None:
        """When LLM flipped status to dead by hand but forgot the thread markers."""
        path = tmp_path / "rm.md"
        self._seed(path, "dead", "\n### T001: foo [◉ ACTIVE]\n")
        sync_status_from_judge(
            path,
            judge_body="direction `exploring → dead` — rate form 失败。",
            batch_id="batch_029",
        )
        body = path.read_text(encoding="utf-8")
        assert "[◉ ACTIVE]" not in body
        assert "[✗ DISPROVEN batch_029]" in body

    def test_bare_arrow_saturated_recognised(self, tmp_path: Path) -> None:
        path = tmp_path / "bar.md"
        self._seed(path, "productive", "\n")
        sync_status_from_judge(
            path, judge_body="方向首次 → saturated。", batch_id="batch_015"
        )
        fm = _read_fm(path)
        assert fm["status"] == "saturated"
