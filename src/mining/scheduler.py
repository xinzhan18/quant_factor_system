"""Logic scheduling — scores active logics and recommends next exploration targets."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)

# Scoring constants
_UNDERREPRESENTED_THRESHOLD = 2   # category count below this earns bonus
_UNDERREPRESENTED_BONUS = 3
_RECENT_SUCCESS_BONUS = 2
_HIGH_CEILING_BONUS = 1
_MAX_FATIGUE = 5                   # fatigue is capped at this value
_ZERO_CONVERSION_PENALTY = 2      # extra penalty for zero conversion
_ZERO_CONVERSION_MIN_GENERATED = 10
_NEW_LOGIC_DEFAULT_SCORE = 3.0


class Scheduler:
    """Score and rank logics to guide exploration order.

    Each *logic* is a dict with at minimum:
        - logic_id (str)
        - category (str)
        - factors_generated (int)
        - factors_admitted (int)
        - rounds_without_admit (int)
        - best_ic (float | None)
    """

    def score_logics(
        self,
        logics: List[Dict[str, Any]],
        coverage: Dict[str, int],
        library_avg_ic: float,
    ) -> List[Tuple[str, float]]:
        """Score each logic: potential - fatigue.

        Returns a list of (logic_id, score) sorted descending by score.
        """
        results: List[Tuple[str, float]] = []
        for logic in logics:
            logic_id = logic["logic_id"]
            score = self._score_one(logic, coverage, library_avg_ic)
            results.append((logic_id, score))
        results.sort(key=lambda x: x[1], reverse=True)
        return results

    def recommend(
        self,
        logics: List[Dict[str, Any]],
        coverage: Dict[str, int],
        library_avg_ic: float,
        top_n: int = 2,
    ) -> List[Dict[str, Any]]:
        """Return the top-N logics to explore next."""
        scored = self.score_logics(logics, coverage, library_avg_ic)
        top_ids = {logic_id for logic_id, _ in scored[:top_n]}
        # Preserve original dict objects, in score order
        id_to_logic = {l["logic_id"]: l for l in logics}
        return [id_to_logic[lid] for lid, _ in scored[:top_n] if lid in id_to_logic]

    def should_trigger_outer_loop(
        self,
        logics: List[Dict[str, Any]],
        coverage: Dict[str, int],
        library_avg_ic: float,
    ) -> bool:
        """Return True when all active logics have non-positive scores.

        A non-positive score means the system has exhausted useful signal from
        every existing logic and a new outer-loop idea generation pass is needed.
        """
        if not logics:
            return True
        scored = self.score_logics(logics, coverage, library_avg_ic)
        return all(score <= 0 for _, score in scored)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _score_one(
        self,
        logic: Dict[str, Any],
        coverage: Dict[str, int],
        library_avg_ic: float,
    ) -> float:
        """Compute the score for a single logic dict."""
        factors_generated: int = logic.get("factors_generated", 0)

        # New logic — no data yet, grant default score
        if factors_generated == 0:
            return _NEW_LOGIC_DEFAULT_SCORE

        factors_admitted: int = logic.get("factors_admitted", 0)
        rounds_without_admit: int = logic.get("rounds_without_admit", 0)
        best_ic: float | None = logic.get("best_ic")
        category: str = logic.get("category", "")

        # --- Potential ---
        potential = 0.0

        # Underrepresented category bonus
        category_count = coverage.get(category, 0)
        if category_count < _UNDERREPRESENTED_THRESHOLD:
            potential += _UNDERREPRESENTED_BONUS

        # Recent success bonus
        if rounds_without_admit == 0 and factors_admitted > 0:
            potential += _RECENT_SUCCESS_BONUS

        # High ceiling bonus
        if best_ic is not None and abs(best_ic) > library_avg_ic:
            potential += _HIGH_CEILING_BONUS

        # --- Fatigue ---
        fatigue = min(rounds_without_admit, _MAX_FATIGUE)

        # Zero-conversion penalty
        if factors_generated > _ZERO_CONVERSION_MIN_GENERATED and factors_admitted == 0:
            fatigue += _ZERO_CONVERSION_PENALTY

        fatigue = min(fatigue, _MAX_FATIGUE)

        return float(potential - fatigue)
