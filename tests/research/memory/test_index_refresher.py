"""Tests for the minimal-MOC INDEX.md regeneration."""

from __future__ import annotations

from pathlib import Path

from research.memory.direction_updater import update_direction_frontmatter
from research.memory.index_refresher import (
    HOT_TOPICS_BEGIN,
    HOT_TOPICS_END,
    collect_admitted_factors,
    collect_direction_stats,
    count_admitted_factors,
    refresh_index,
)
from research.storage.paths import StoragePaths
from research.storage.yaml_io import save_yaml


def _bootstrap(tmp_path: Path) -> StoragePaths:
    paths = StoragePaths(tmp_path)
    paths.ensure_dirs()
    save_yaml(
        paths.state_file,
        {
            "current_batch": None,
            "current_batch_phase": None,
            "last_batch": "batch_001",
            "round": 1,
            "last_activity": "2026-04-22T00:00:00Z",
            "rounds_since_last_consolidation": 1,
        },
    )
    return paths


class TestCollectDirectionStats:
    def test_empty_returns_empty_list(self, tmp_path: Path) -> None:
        paths = _bootstrap(tmp_path)
        assert collect_direction_stats(paths.directions_dir) == []

    def test_reads_frontmatter(self, tmp_path: Path) -> None:
        paths = _bootstrap(tmp_path)
        update_direction_frontmatter(
            paths.direction_file("vol"), batch_id="batch_001", new_admits=["F020"]
        )
        update_direction_frontmatter(
            paths.direction_file("mom"),
            batch_id="batch_002",
            new_admits=["F021", "F022"],
        )
        rows = collect_direction_stats(paths.directions_dir)
        by_id = {r["direction_id"]: r for r in rows}
        assert by_id["vol"]["rounds"] == 1
        assert by_id["vol"]["admits"] == 1
        assert by_id["mom"]["admits"] == 2


class TestCountAdmittedFactors:
    def test_counts_F_yaml_only(self, tmp_path: Path) -> None:
        paths = _bootstrap(tmp_path)
        save_yaml(paths.factors_dir / "F020.yaml", {"factor_id": "F020"})
        save_yaml(paths.factors_dir / "F021.yaml", {"factor_id": "F021"})
        (paths.factors_dir / "notes.md").write_text("notes")
        assert count_admitted_factors(paths.factors_dir) == 2

    def test_skips_retired(self, tmp_path: Path) -> None:
        paths = _bootstrap(tmp_path)
        save_yaml(
            paths.factors_dir / "F020.yaml",
            {"factor_id": "F020", "status": "active"},
        )
        save_yaml(
            paths.factors_dir / "F021.yaml",
            {"factor_id": "F021", "status": "retired"},
        )
        assert count_admitted_factors(paths.factors_dir) == 1


class TestCollectAdmittedFactors:
    def test_sorts_numerically(self, tmp_path: Path) -> None:
        paths = _bootstrap(tmp_path)
        for fid in ("F002", "F010", "F001"):
            save_yaml(
                paths.factors_dir / f"{fid}.yaml",
                {"factor_id": fid, "name": fid.lower(), "direction": "d"},
            )
        rows = collect_admitted_factors(paths.factors_dir)
        assert [r["factor_id"] for r in rows] == ["F001", "F002", "F010"]


class TestRefreshIndex:
    def test_creates_minimal_moc(self, tmp_path: Path) -> None:
        paths = _bootstrap(tmp_path)
        if paths.vault_index_file.exists():
            paths.vault_index_file.unlink()
        refresh_index(paths, round_counter=1)
        text = paths.vault_index_file.read_text(encoding="utf-8")
        # Frontmatter
        assert text.startswith("---\n")
        assert "round: 1" in text
        assert "last_batch: batch_001" in text
        # Title + MOC callout
        assert "# 🗺️ Factor Research Index" in text
        assert "> [!info] MOC" in text
        # Three base embeds
        assert "![[_bases/directions.base]]" in text
        assert "![[_bases/factors.base]]" in text
        assert "![[_bases/recent_batches.base]]" in text
        # LLM-owned hot topics sentinel
        assert HOT_TOPICS_BEGIN in text
        assert HOT_TOPICS_END in text
        # System status footer
        assert "> [!abstract]- 系统状态" in text

    def test_idempotent_modulo_timestamp(self, tmp_path: Path) -> None:
        paths = _bootstrap(tmp_path)
        refresh_index(paths, round_counter=1)
        first = paths.vault_index_file.read_text(encoding="utf-8")
        refresh_index(paths, round_counter=1)
        second = paths.vault_index_file.read_text(encoding="utf-8")
        # The only byte-level drift allowed is the generated_at line.
        import re
        stripped = re.compile(r"^generated_at: .*$", re.MULTILINE)
        assert stripped.sub("generated_at: X", first) == stripped.sub(
            "generated_at: X", second
        )

    def test_preserves_llm_hot_topics_block(self, tmp_path: Path) -> None:
        paths = _bootstrap(tmp_path)
        paths.vault_index_file.write_text(
            "---\nround: 1\nlast_batch: batch_001\n---\n\n"
            "# Old INDEX\n\n"
            f"{HOT_TOPICS_BEGIN}\n"
            "> [!warning]+ 🔥 Hot Topics（LLM 维护）\n"
            "> - 🔴 **P001 keep me** · dirs: vol → avoid duplicate\n"
            f"{HOT_TOPICS_END}\n",
            encoding="utf-8",
        )
        refresh_index(paths, round_counter=1)
        text = paths.vault_index_file.read_text(encoding="utf-8")
        assert "P001 keep me" in text
        assert text.count(HOT_TOPICS_BEGIN) == 1
        assert text.count(HOT_TOPICS_END) == 1

    def test_frontmatter_counts_match_sources(self, tmp_path: Path) -> None:
        paths = _bootstrap(tmp_path)
        # 2 directions (one dead, one active) + 1 factor
        update_direction_frontmatter(
            paths.direction_file("live"),
            batch_id="batch_001",
            new_admits=["F001"],
        )
        dead = paths.direction_file("dead")
        dead.write_text(
            "---\ndirection_id: dead\nstatus: dead\npriority: low\n"
            "rounds: 1\nadmits: 0\nlast_batch: batch_000\nmembers: []\n---\n# dead\n",
            encoding="utf-8",
        )
        save_yaml(paths.factors_dir / "F001.yaml", {"factor_id": "F001"})
        refresh_index(paths, round_counter=1)
        text = paths.vault_index_file.read_text(encoding="utf-8")
        assert "total_active_directions: 1" in text
        assert "total_factors_admitted: 1" in text

    def test_cockpit_surfaces_pending_raw_papers(self, tmp_path: Path) -> None:
        paths = _bootstrap(tmp_path)
        (paths.vault_raw_papers_dir / "Factor Miner.pdf").write_bytes(b"%PDF-1.4 fake")
        refresh_index(paths, round_counter=1)
        text = paths.vault_index_file.read_text(encoding="utf-8")
        assert "待 intake papers: factor_miner" in text
        assert "📄 **新论文待 intake**" in text
        assert (
            "PYTHONPATH=src python3 scripts/extract_paper_pdf.py --pdf "
            "'storage/vault/raw/papers/Factor Miner.pdf'"
        ) in text
        assert "target=`storage/vault/papers/factor_miner.md`" in text

    def test_syncs_factor_md_status_from_yaml(self, tmp_path: Path) -> None:
        paths = _bootstrap(tmp_path)
        save_yaml(
            paths.factors_dir / "F001.yaml",
            {"factor_id": "F001", "status": "retired"},
        )
        (paths.factors_dir / "F001.md").write_text(
            "---\nid: F001\ndecision: admit\nstatus: active\n---\n# F001\n",
            encoding="utf-8",
        )
        refresh_index(paths, round_counter=1)
        md_text = (paths.factors_dir / "F001.md").read_text(encoding="utf-8")
        assert "status: retired" in md_text
        assert "status: active" not in md_text
