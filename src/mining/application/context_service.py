"""Search-context composition for the mining pipeline.

Assembles a prompt-ready string from ExperienceMemory, MarketLogicLibrary,
FactorLibrary, and EvolutionEngine -- breaking the reverse dependency that
previously forced memory.py to import those heavier modules.
"""

from __future__ import annotations

import logging
from typing import Dict, List

from mining.config import MiningConfig
from mining.memory import ExperienceMemory

logger = logging.getLogger(__name__)


def compose_search_context(config: MiningConfig) -> str:
    """Compose memory into a prompt-ready string.

    Returns a multi-section string covering:
    1. Current library state and next-round hint
    2. Direction statuses
    3. Taxonomy coverage map (from Logic Library)
    4. Forbidden regions
    5. Active logic evidence
    6. Factor lineage tree
    """
    mem = ExperienceMemory(config)
    sections: List[str] = []

    # --- Section 1: Current library state ---
    state = mem.read_state()
    lib = state.get("library", {})
    state_lines = ["## Current Mining State", f"Library size: {lib.get('size', 0)}"]
    hint = state.get("next_round_hint")
    if hint:
        state_lines.append(f"\nLast round hint: {hint}")
    sections.append("\n".join(state_lines))

    # --- Section 2: Direction statuses ---
    directions = mem.list_directions()
    if directions:
        dir_lines = ["## Direction Statuses"]
        by_status: Dict[str, list] = {}
        for d in directions:
            by_status.setdefault(d["status"], []).append(d)
        for status in ["active", "new", "probing", "exhausted", "blocked", "dead"]:
            if status in by_status:
                names = [
                    f"{d['name']} (IC={d['best_ic']})" if d.get("best_ic") else d["name"]
                    for d in by_status[status]
                ]
                dir_lines.append(f"- **{status}**: {', '.join(names)}")
        sections.append("\n".join(dir_lines))

    # --- Section 3: Taxonomy coverage map (Logic Library) ---
    logic_lib = None
    try:
        from mining.logic_library import MarketLogicLibrary

        logic_lib = MarketLogicLibrary(config.logic_dir)
        coverage = logic_lib.coverage_map()
        if coverage:
            cov_lines = ["## Taxonomy Coverage"]
            for cat, count in sorted(coverage.items()):
                cov_lines.append(f"  {cat}: {count} active logics")
            sections.append("\n".join(cov_lines))
    except Exception:
        pass  # Logic library may not exist yet

    # --- Section 4: Forbidden regions ---
    forbidden = mem.read_forbidden()
    if forbidden:
        forb_lines = ["## Forbidden Regions (DO NOT explore these)"]
        for r in forbidden:
            forb_lines.append(f"  - {r['pattern']} \u2014 {r['reason']}")
        sections.append("\n".join(forb_lines))

    # --- Section 5: Active logic evidence ---
    try:
        if logic_lib is None:
            from mining.logic_library import MarketLogicLibrary

            logic_lib = MarketLogicLibrary(config.logic_dir)
        active = logic_lib.list_logics(status="active")
        if active:
            logic_lines = ["## Active Market Logics"]
            for logic in active:
                s = logic.get("stats", {})
                logic_lines.append(
                    f"  {logic['id']} {logic['name']} "
                    f"[gen={s.get('factors_generated', 0)}, "
                    f"adm={s.get('factors_admitted', 0)}, "
                    f"best_ic={s.get('best_ic', 0):.3f}]"
                )
            sections.append("\n".join(logic_lines))
    except Exception:
        pass

    # --- Section 6: Lineage summary ---
    lineage_text = _get_lineage_summary(config)
    if lineage_text:
        sections.append(f"## Factor Lineage Tree\n{lineage_text}")

    return "\n\n".join(s for s in sections if s)


def _get_lineage_summary(config: MiningConfig) -> str:
    """Format lineage information from library for prompt context."""
    try:
        from mining.library import FactorLibrary

        lib = FactorLibrary(config)
        factors = lib.list_factors()

        # Count factors with lineage
        with_lineage = [f for f in factors if f.get("lineage")]
        if not with_lineage:
            return ""

        from mining.evolution import EvolutionEngine

        engine = EvolutionEngine(MiningConfig())
        return engine.format_lineage_tree(factors)
    except Exception:
        return ""
