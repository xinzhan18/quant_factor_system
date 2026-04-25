"""StoragePaths: centralised path registry for the new storage layout.

Layout (see refactor_plan.md §4):

    storage/
      state.yaml                            # current batch + phase + round
      config.yaml                           # system config
      vault/                                # Obsidian vault (Rule B Markdown)
        INDEX.md
        lessons.md
        raw/papers/*.pdf
        raw/paper_extracts/{slug}.md
        papers/{slug}.md
        directions/{tag}.md
        factors/F{id}.{yaml,md}
        _meta/consolidation_log.md
      batches/batch_{NNN}/                  # per-batch immutable archive
        manifest.yaml
        result.yaml
        judge.md
        python_candidates/C{id}.py
        signals/C{id}.parquet
      cache/
        market_daily.parquet
        barra_factors.parquet
        factor_values/{hash}.parquet
      python_factors/F{id}_{name}.py        # admitted Python factors
      _holdout_private/                     # LLM never reads this

Every directory / file path is a property off a configurable root.
:meth:`ensure_dirs` creates the full tree in one call (idempotent).

This module replaces the legacy multi-layer layout (logic/governance/registry/
runtime). Old dirs stay on disk until P7 when they move to ``_legacy/``.
"""

from __future__ import annotations

from pathlib import Path


class StoragePaths:
    """Centralised path registry for the research storage tree.

    Construct with a root directory. All paths are derived lazily so tests
    can point at ``tmp_path`` without creating the real tree.
    """

    def __init__(self, root: str | Path = "storage") -> None:
        self.root = Path(root)

    # ------------------------------------------------------------------
    # Top-level files
    # ------------------------------------------------------------------

    @property
    def state_file(self) -> Path:
        return self.root / "state.yaml"

    @property
    def config_file(self) -> Path:
        return self.root / "config.yaml"

    # ------------------------------------------------------------------
    # Vault (Obsidian root — directly under storage/, no evidence/ wrapper)
    # ------------------------------------------------------------------

    @property
    def vault_dir(self) -> Path:
        return self.root / "vault"

    @property
    def vault_index_file(self) -> Path:
        return self.vault_dir / "INDEX.md"

    @property
    def vault_lessons_file(self) -> Path:
        return self.vault_dir / "lessons.md"

    @property
    def vault_raw_dir(self) -> Path:
        return self.vault_dir / "raw"

    @property
    def vault_raw_papers_dir(self) -> Path:
        return self.vault_raw_dir / "papers"

    @property
    def vault_raw_paper_extracts_dir(self) -> Path:
        return self.vault_raw_dir / "paper_extracts"

    @property
    def vault_papers_dir(self) -> Path:
        return self.vault_dir / "papers"

    def paper_file(self, paper_slug: str) -> Path:
        return self.vault_papers_dir / f"{paper_slug}.md"

    def paper_assets_dir(self, paper_slug: str) -> Path:
        return self.vault_papers_dir / paper_slug

    def paper_extract_file(self, paper_slug: str) -> Path:
        return self.vault_raw_paper_extracts_dir / f"{paper_slug}.md"

    @property
    def directions_dir(self) -> Path:
        return self.vault_dir / "directions"

    def direction_file(self, direction: str) -> Path:
        return self.directions_dir / f"{direction}.md"

    @property
    def factors_dir(self) -> Path:
        return self.vault_dir / "factors"

    def factor_yaml_file(self, factor_id: str) -> Path:
        return self.factors_dir / f"{factor_id}.yaml"

    def factor_md_file(self, factor_id: str) -> Path:
        return self.factors_dir / f"{factor_id}.md"

    def factor_assets_dir(self, factor_id: str) -> Path:
        return self.factors_dir / factor_id

    @property
    def vault_meta_dir(self) -> Path:
        return self.vault_dir / "_meta"

    # ------------------------------------------------------------------
    # Batches (inside vault — Obsidian-visible for wikilink connectivity)
    # ------------------------------------------------------------------

    @property
    def batches_dir(self) -> Path:
        return self.vault_dir / "batches"

    def batch_dir(self, batch_id: str) -> Path:
        return self.batches_dir / batch_id

    def batch_manifest_file(self, batch_id: str) -> Path:
        return self.batch_dir(batch_id) / "manifest.yaml"

    def batch_result_file(self, batch_id: str) -> Path:
        return self.batch_dir(batch_id) / "result.yaml"

    def batch_judge_file(self, batch_id: str) -> Path:
        return self.batch_dir(batch_id) / "judge.md"

    def batch_python_candidates_dir(self, batch_id: str) -> Path:
        return self.batch_dir(batch_id) / "python_candidates"

    def batch_signals_dir(self, batch_id: str) -> Path:
        return self.batch_dir(batch_id) / "signals"

    def batch_signal_file(self, batch_id: str, candidate_id: str) -> Path:
        return self.batch_signals_dir(batch_id) / f"{candidate_id}.parquet"

    def batch_packets_dir(self, batch_id: str) -> Path:
        """Scratch dir for report packets (Phase 4).

        Packets are deleted lazily: whenever a later Phase 4 runs, it calls
        ``cleanup_finished_packets`` which removes
        ``report_packet_F{id}.md`` files whose ``factors/F{id}.md`` now
        exists (subagent wrote it). The current batch's packets are
        preserved (subagents may still be reading them). Also exposed via
        ``research report cleanup-packets`` for manual runs.
        """
        return self.batch_dir(batch_id) / "_packets"

    def batch_hints_file(self, batch_id: str) -> Path:
        """Phase 3 Python-only hints: hard_gate results + MT counts + per-candidate mt_budget."""
        return self.batch_dir(batch_id) / "_hints.yaml"

    def batch_candidates_dir(self, batch_id: str) -> Path:
        """Per-candidate judge markdown files (one per candidate_id)."""
        return self.batch_dir(batch_id) / "candidates"

    def batch_candidate_md_file(self, batch_id: str, candidate_id: str) -> Path:
        return self.batch_candidates_dir(batch_id) / f"{candidate_id}.md"

    # ------------------------------------------------------------------
    # Cache
    # ------------------------------------------------------------------

    @property
    def cache_dir(self) -> Path:
        return self.root / "cache"

    @property
    def market_daily_cache(self) -> Path:
        return self.cache_dir / "market_daily.parquet"

    @property
    def barra_factors_cache(self) -> Path:
        return self.cache_dir / "barra_factors.parquet"

    @property
    def factor_values_cache_dir(self) -> Path:
        return self.cache_dir / "factor_values"

    def factor_value_cache_file(self, key: str) -> Path:
        return self.factor_values_cache_dir / f"{key}.parquet"

    # Per-candidate diagnostic arrays (Q1..Qn daily, IC daily, long-short daily)
    # — lives under cache/ so it's regenerable; pruned by retention policy.
    @property
    def batch_diagnostics_root(self) -> Path:
        return self.cache_dir / "batch_diagnostics"

    def batch_diagnostics_dir(self, batch_id: str) -> Path:
        return self.batch_diagnostics_root / batch_id

    def candidate_diagnostics_dir(
        self, batch_id: str, candidate_id: str
    ) -> Path:
        return self.batch_diagnostics_dir(batch_id) / candidate_id

    # ------------------------------------------------------------------
    # Python factors (admitted, source-of-truth implementation)
    # ------------------------------------------------------------------

    @property
    def python_factors_dir(self) -> Path:
        return self.root / "python_factors"

    def python_factor_file(self, factor_id: str, name: str) -> Path:
        return self.python_factors_dir / f"{factor_id}_{name}.py"

    # ------------------------------------------------------------------
    # Holdout (physically isolated)
    # ------------------------------------------------------------------

    @property
    def holdout_private_dir(self) -> Path:
        """LLM is forbidden to read from this directory."""
        return self.root / "_holdout_private"

    def holdout_review_file(self, date_iso: str) -> Path:
        return self.holdout_private_dir / f"review_{date_iso}.md"

    # ------------------------------------------------------------------
    # Directory creation
    # ------------------------------------------------------------------

    def all_dirs(self) -> list[Path]:
        """All directories that must exist in a bootstrapped storage tree.

        Does NOT include per-batch dirs (those are created on demand in Phase 1).
        """
        return [
            self.vault_dir,
            self.vault_raw_dir,
            self.vault_raw_papers_dir,
            self.vault_raw_paper_extracts_dir,
            self.vault_papers_dir,
            self.directions_dir,
            self.factors_dir,
            self.vault_meta_dir,
            self.batches_dir,
            self.cache_dir,
            self.factor_values_cache_dir,
            self.python_factors_dir,
            self.holdout_private_dir,
        ]

    def ensure_dirs(self) -> None:
        """Create every directory in the storage tree (idempotent)."""
        for d in self.all_dirs():
            d.mkdir(parents=True, exist_ok=True)
