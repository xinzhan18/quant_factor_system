"""StoragePaths: centralised path registry for the new storage layout.

Layout (see refactor_plan.md §4):

    storage/
      state.yaml                            # current batch + phase + round
      config.yaml                           # system config
      vault/                                # Obsidian vault (Rule B Markdown)
        INDEX.md
        lessons.md
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

    @property
    def consolidation_log_file(self) -> Path:
        return self.vault_meta_dir / "consolidation_log.md"

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
        """Scratch dir for LLM pre-pack packets. Cleaned after each batch."""
        return self.batch_dir(batch_id) / "_packets"

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
