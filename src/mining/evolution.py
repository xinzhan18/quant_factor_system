"""Evolution engine for structured factor generation.

Three generation modes:
  - genesis   : create new factors from logic/ideas
  - mutate    : modify an existing library factor
  - crossover : merge two factors from different categories
"""

from __future__ import annotations

import logging
import random
from typing import Any, Dict, List, Optional

from .config import MiningConfig

logger = logging.getLogger(__name__)


class EvolutionEngine:
    """Provides structured factor generation guidance for the mining pipeline."""

    def __init__(self, config: MiningConfig) -> None:
        self._config = config

    # ------------------------------------------------------------------
    # Mode suggestions
    # ------------------------------------------------------------------

    def suggest_mode(self, library_size: int) -> dict[str, float]:
        """Return genesis/mutate/crossover probability ratios based on library size.

        Small library (<30): exploration dominant — genesis=0.6, mutate=0.3, crossover=0.1
        Medium library (30-60): balanced — genesis=0.4, mutate=0.4, crossover=0.2
        Large library (60+): exploitation dominant — genesis=0.2, mutate=0.5, crossover=0.3
        """
        if library_size < 30:
            return {"genesis": 0.6, "mutate": 0.3, "crossover": 0.1}
        elif library_size <= 60:
            return {"genesis": 0.4, "mutate": 0.4, "crossover": 0.2}
        else:
            return {"genesis": 0.2, "mutate": 0.5, "crossover": 0.3}

    # ------------------------------------------------------------------
    # Mutation target selection
    # ------------------------------------------------------------------

    def select_mutation_target(
        self,
        factors: List[Dict[str, Any]],
        lineage: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Pick a factor from *factors* to mutate.

        Selection rules:
        - Skip factors whose mutation count (from *lineage*) has reached
          config.max_mutations_per_factor.
        - Weight remaining candidates by abs(ic_mean); discount factors that
          were mutated without producing any admitted child (success_count == 0
          for non-zero mutation count).
        - Use weighted random selection; return None when no eligible candidates
          remain.
        """
        max_mutations = self._config.max_mutations_per_factor

        candidates = []
        weights = []

        for factor in factors:
            factor_id = factor.get("id", "")
            lin = lineage.get(factor_id, {})
            mutation_count = lin.get("mutation_count", 0)

            # Respect hard cap
            if mutation_count >= max_mutations:
                continue

            ic_mean = factor.get("ic_mean") or 0.0
            base_weight = abs(ic_mean)

            # Discount: if mutations were attempted but yielded no success
            success_count = lin.get("success_count", 0)
            if mutation_count > 0 and success_count == 0:
                base_weight *= 0.3

            # Keep a small floor so any eligible factor can be chosen
            weight = max(base_weight, 1e-6)

            candidates.append(factor)
            weights.append(weight)

        if not candidates:
            return None

        chosen = random.choices(candidates, weights=weights, k=1)[0]
        return chosen

    # ------------------------------------------------------------------
    # Crossover pair selection
    # ------------------------------------------------------------------

    def select_crossover_pair(
        self,
        factors: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Select two factors for crossover.

        Preference is given to pairs from *different* categories so the
        resulting factor inherits diverse traits.  Falls back to any two
        distinct factors when only one category is present.

        Returns a list of exactly two factor dicts, or an empty list if fewer
        than two factors are provided.
        """
        if len(factors) < 2:
            return []

        # Try to find a pair from different categories first
        categories: Dict[str, List[Dict[str, Any]]] = {}
        for f in factors:
            cat = f.get("category", "other")
            categories.setdefault(cat, []).append(f)

        multi_category = [cat for cat, members in categories.items() if len(members) >= 1]

        if len(multi_category) >= 2:
            # Pick two distinct categories at random, then pick one factor each
            cat_a, cat_b = random.sample(multi_category, 2)
            factor_a = random.choice(categories[cat_a])
            factor_b = random.choice(categories[cat_b])
            return [factor_a, factor_b]

        # Fallback: all factors in one category — pick any two distinct ones
        choices = random.sample(factors, 2)
        return choices

    # ------------------------------------------------------------------
    # Lineage tree formatting
    # ------------------------------------------------------------------

    def format_lineage_tree(self, factors: List[Dict[str, Any]]) -> str:
        """Render the factor lineage as an indented text tree.

        Each factor may carry a ``lineage.parents`` list of parent factor IDs.
        The tree is rendered depth-first with 2-space indentation per level.
        Factors with no parents are shown as roots.

        Returns a non-empty string (falls back to a flat list when no lineage
        info is present).
        """
        if not factors:
            return "(no factors)"

        # Build lookup: id → factor
        by_id: Dict[str, Dict[str, Any]] = {}
        for f in factors:
            fid = f.get("id", "")
            if fid:
                by_id[fid] = f

        # Build children map: parent_id → [child_id, ...]
        children: Dict[str, List[str]] = {fid: [] for fid in by_id}
        all_children: set[str] = set()

        for fid, f in by_id.items():
            parents = (f.get("lineage") or {}).get("parents") or []
            if isinstance(parents, str):
                parents = [parents]
            for parent_id in parents:
                if parent_id in children:
                    children[parent_id].append(fid)
                    all_children.add(fid)

        roots = [fid for fid in by_id if fid not in all_children]
        # Also include factors not in by_id that are referenced but absent —
        # ignore them; just use the ids we know about.

        lines: List[str] = []

        def _label(fid: str) -> str:
            f = by_id.get(fid, {})
            name = f.get("name", fid)
            ic = f.get("ic_mean")
            if ic is not None:
                return f"{fid}: {name} (IC={ic:.3f})"
            return f"{fid}: {name}"

        def _render(fid: str, depth: int) -> None:
            prefix = "  " * depth
            lines.append(f"{prefix}{_label(fid)}")
            for child_id in sorted(children.get(fid, [])):
                _render(child_id, depth + 1)

        for root_id in sorted(roots):
            _render(root_id, 0)

        # Render any orphaned children that weren't reachable from roots
        rendered = set()
        for line in lines:
            # Extract id from label (format "  ...id: ...")
            stripped = line.lstrip()
            colon_pos = stripped.find(":")
            if colon_pos > 0:
                rendered.add(stripped[:colon_pos])

        for fid in sorted(by_id):
            if fid not in rendered:
                lines.append(_label(fid))

        return "\n".join(lines) if lines else "(no factors)"

    # ------------------------------------------------------------------
    # Lineage statistics
    # ------------------------------------------------------------------

    def compute_lineage_stats(self, factors: list[dict]) -> dict[str, dict]:
        """Compute per-factor mutation counts from lineage data.

        Returns: {factor_id: {"mutation_count": N, "admitted": M}}
        """
        stats = {}
        for f in factors:
            fid = f.get("id", "")
            stats[fid] = {"mutation_count": 0, "admitted": 0}

        for f in factors:
            lineage = f.get("lineage") or {}
            parents = lineage.get("parents", [])
            for pid in parents:
                if pid in stats:
                    stats[pid]["mutation_count"] += 1
                    # If this child was admitted, count it
                    if f.get("status", "active") == "active":
                        stats[pid]["admitted"] += 1

        return stats
