"""Composite factor scorer — 6-dimension scoring with letter grades."""
from __future__ import annotations


class CompositeScorer:
    """Score a factor across 6 dimensions and compute a composite grade."""

    # Grade scale: score → letter
    _GRADE_SCALE = [
        (90, "A"), (80, "A-"), (75, "B+"), (65, "B"), (60, "B-"),
        (55, "C+"), (45, "C"), (35, "C-"), (0, "D"),
    ]

    @staticmethod
    def score_to_grade(score: float) -> str:
        for threshold, grade in CompositeScorer._GRADE_SCALE:
            if score >= threshold:
                return grade
        return "D"

    @staticmethod
    def _interpolate(value: float, lo: float, hi: float, score_lo: float, score_hi: float) -> float:
        """Linear interpolation of value within [lo, hi] → [score_lo, score_hi], clamped."""
        if hi == lo:
            return score_hi
        t = (value - lo) / (hi - lo)
        t = max(0.0, min(1.0, t))
        return score_lo + t * (score_hi - score_lo)

    def _score_predictive_power(self, ic_mean_abs: float) -> float:
        if ic_mean_abs >= 0.08:
            return self._interpolate(ic_mean_abs, 0.08, 0.15, 80, 100)
        if ic_mean_abs >= 0.05:
            return self._interpolate(ic_mean_abs, 0.05, 0.08, 55, 79)
        if ic_mean_abs >= 0.03:
            return self._interpolate(ic_mean_abs, 0.03, 0.05, 35, 54)
        return self._interpolate(ic_mean_abs, 0.0, 0.03, 0, 34)

    def _score_monotonicity(self, monotonicity: float) -> float:
        m = abs(monotonicity)
        if m >= 0.8:
            return self._interpolate(m, 0.8, 1.0, 80, 100)
        if m >= 0.6:
            return self._interpolate(m, 0.6, 0.8, 55, 79)
        if m >= 0.4:
            return self._interpolate(m, 0.4, 0.6, 35, 54)
        return self._interpolate(m, 0.0, 0.4, 0, 34)

    def _score_stability(self, ic_is: float, ic_oos: float) -> float:
        if ic_is == 0:
            return 0
        delta = abs(ic_is - ic_oos) / abs(ic_is)
        if delta < 0.10:
            return self._interpolate(delta, 0.0, 0.10, 100, 80)
        if delta < 0.25:
            return self._interpolate(delta, 0.10, 0.25, 79, 55)
        if delta < 0.50:
            return self._interpolate(delta, 0.25, 0.50, 54, 35)
        return self._interpolate(delta, 0.50, 1.0, 34, 0)

    def _score_decay_resistance(self, ic_1d: float, ic_20d: float) -> float:
        if ic_1d == 0:
            return 0
        ratio = abs(ic_20d) / abs(ic_1d)
        if ratio >= 0.7:
            return self._interpolate(ratio, 0.7, 1.0, 80, 100)
        if ratio >= 0.5:
            return self._interpolate(ratio, 0.5, 0.7, 55, 79)
        if ratio >= 0.3:
            return self._interpolate(ratio, 0.3, 0.5, 35, 54)
        return self._interpolate(ratio, 0.0, 0.3, 0, 34)

    def _score_capacity(self, coverage: float) -> float:
        if coverage >= 0.95:
            return self._interpolate(coverage, 0.95, 1.0, 80, 100)
        if coverage >= 0.85:
            return self._interpolate(coverage, 0.85, 0.95, 55, 79)
        if coverage >= 0.70:
            return self._interpolate(coverage, 0.70, 0.85, 35, 54)
        return self._interpolate(coverage, 0.0, 0.70, 0, 34)

    def _score_uniqueness(self, max_corr: float) -> float:
        if max_corr < 0.3:
            return self._interpolate(max_corr, 0.0, 0.3, 100, 80)
        if max_corr < 0.5:
            return self._interpolate(max_corr, 0.3, 0.5, 79, 55)
        if max_corr < 0.7:
            return self._interpolate(max_corr, 0.5, 0.7, 54, 35)
        return self._interpolate(max_corr, 0.7, 1.0, 34, 0)

    def compute(
        self,
        ic_mean: float,
        monotonicity: float,
        ic_is: float,
        ic_oos: float,
        ic_1d: float,
        ic_20d: float,
        coverage: float,
        max_library_corr: float,
    ) -> dict:
        dims = [
            {"name": "Predictive Power", "score": round(self._score_predictive_power(abs(ic_mean)), 1)},
            {"name": "Monotonicity", "score": round(self._score_monotonicity(monotonicity), 1)},
            {"name": "Stability", "score": round(self._score_stability(ic_is, ic_oos), 1)},
            {"name": "Decay Resistance", "score": round(self._score_decay_resistance(ic_1d, ic_20d), 1)},
            {"name": "Capacity", "score": round(self._score_capacity(coverage), 1)},
            {"name": "Uniqueness", "score": round(self._score_uniqueness(max_library_corr), 1)},
        ]
        for d in dims:
            d["grade"] = self.score_to_grade(d["score"])
        avg = sum(d["score"] for d in dims) / len(dims)
        return {
            "dimensions": dims,
            "composite": {"score": round(avg, 1), "grade": self.score_to_grade(avg)},
        }
