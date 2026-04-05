"""Batch runner: load candidates from YAML and execute the pipeline.

This is the entry point that loads a batch manifest file, constructs
the pipeline with the configured evaluation profile and sample policy,
and writes the results and judge packet to the results directory.

It is the research-system analogue of ``mining.cli.commands.batch``.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import yaml

from .config import EvaluationProfile, load_evaluation_profile, load_sample_policy
from .pipeline import ResearchExecutePipeline

logger = logging.getLogger(__name__)


class BatchRunner:
    """Load a batch manifest and run the research execute pipeline."""

    def __init__(
        self,
        profile_path: Optional[str | Path] = None,
        sample_policy_path: Optional[str | Path] = None,
        batches_dir: Optional[str | Path] = None,
        *,
        compute_signal: Optional[Callable] = None,
        preprocess_signal: Optional[Callable] = None,
        compute_stat_evidence: Optional[Callable] = None,
        compute_redundancy: Optional[Callable] = None,
        compute_feasibility: Optional[Callable] = None,
        risk_engine: Optional[Any] = None,
        use_real_compute: bool = True,
        qlib_dir: str = "~/.qlib/qlib_data/cn_data_1d",
        universe_override: Optional[str] = None,
    ):
        self._profile = load_evaluation_profile(profile_path)
        self._sample_policy = load_sample_policy(sample_policy_path)
        self._batches_dir = Path(batches_dir) if batches_dir else None
        self._risk_engine = risk_engine
        self._compute_kwargs: Dict[str, Any] = {}

        # Universe: CLI override > profile > default
        universe = universe_override or self._profile.get("universe", "csi1000")

        # If no explicit callables provided and use_real_compute is True,
        # wire up the real implementations automatically.
        any_explicit = any(x is not None for x in [
            compute_signal, preprocess_signal, compute_stat_evidence,
            compute_redundancy, compute_feasibility,
        ])

        if not any_explicit and use_real_compute:
            from research.compute.data_provider import DataProvider
            from research.compute.universe import UniverseManager
            from research.execute.compute_implementations import build_real_callables

            provider = DataProvider(
                universe=UniverseManager(universe),
                qlib_dir=qlib_dir,
            )
            self._compute_kwargs = build_real_callables(
                provider,
                sample_policy=self._sample_policy,
            )

            # Also wire up real RiskEngine if not explicitly provided
            if risk_engine is None:
                from research.risk.engine import RiskEngine
                self._risk_engine = RiskEngine(data_provider=provider)
        else:
            if compute_signal is not None:
                self._compute_kwargs["compute_signal"] = compute_signal
            if preprocess_signal is not None:
                self._compute_kwargs["preprocess_signal"] = preprocess_signal
            if compute_stat_evidence is not None:
                self._compute_kwargs["compute_stat_evidence"] = compute_stat_evidence
            if compute_redundancy is not None:
                self._compute_kwargs["compute_redundancy"] = compute_redundancy
            if compute_feasibility is not None:
                self._compute_kwargs["compute_feasibility"] = compute_feasibility

    def run(
        self,
        manifest_path: str | Path,
        search_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Run the pipeline on a batch manifest file.

        Parameters
        ----------
        manifest_path:
            Path to a YAML file containing the batch manifest.  The file
            must have a ``batch_id`` and a ``candidates`` list.
        search_context:
            Optional search context dict with validation exposure counts
            and per-logic/family attempt counts.

        Returns
        -------
        dict
            The ``BatchExecuteResult`` dict returned by the pipeline.
        """
        manifest_path = Path(manifest_path)
        manifest = self._load_manifest(manifest_path)

        batch_id = manifest.get("batch_id", manifest_path.stem)
        candidates = manifest.get("candidates", [])

        if not candidates:
            logger.warning("Batch %s has no candidates", batch_id)
            return {
                "batch_id": batch_id,
                "candidate_results": [],
                "judge_packet": {},
                "summary": {"total_candidates": 0},
            }

        pipeline = ResearchExecutePipeline(
            profile=self._profile,
            sample_policy=self._sample_policy,
            risk_engine=self._risk_engine,
            **self._compute_kwargs,
        )

        result = pipeline.execute_batch(
            batch_id=batch_id,
            candidates=candidates,
            search_context=search_context,
        )

        # Persist results if directories are configured
        self._save_result(batch_id, result)
        self._save_packet(batch_id, result.get("judge_packet", {}))

        return result

    # ----- I/O helpers ----------------------------------------------------
    @staticmethod
    def _load_manifest(path: Path) -> Dict[str, Any]:
        """Load and validate a batch manifest YAML file."""
        if not path.exists():
            raise FileNotFoundError(f"Batch manifest not found: {path}")

        with open(path, "r") as fh:
            data = yaml.safe_load(fh) or {}

        if "candidates" not in data:
            raise ValueError(
                f"Batch manifest {path} is missing 'candidates' key"
            )
        return data

    def _batch_out_dir(self, batch_id: str) -> Optional[Path]:
        if self._batches_dir is None:
            return None
        d = self._batches_dir / batch_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _save_result(self, batch_id: str, result: Dict[str, Any]) -> None:
        d = self._batch_out_dir(batch_id)
        if d is None:
            return
        out = d / "research_result.yaml"
        with open(out, "w") as fh:
            yaml.dump(
                _strip_non_serializable(result),
                fh,
                default_flow_style=False,
                allow_unicode=True,
            )
        logger.info("Saved research result to %s", out)

    def _save_packet(self, batch_id: str, packet: Dict[str, Any]) -> None:
        d = self._batch_out_dir(batch_id)
        if d is None:
            return
        out = d / "judge_packet.yaml"
        with open(out, "w") as fh:
            yaml.dump(
                _strip_non_serializable(packet),
                fh,
                default_flow_style=False,
                allow_unicode=True,
            )
        logger.info("Saved judge packet to %s", out)


def _strip_non_serializable(obj: Any) -> Any:
    """Recursively strip non-YAML-serializable values (e.g. DataFrames)."""
    if isinstance(obj, dict):
        return {k: _strip_non_serializable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_strip_non_serializable(v) for v in obj]
    if isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    # Fall back to string representation for unknown types
    return str(obj)
