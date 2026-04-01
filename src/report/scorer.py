"""CompositeScorer -- 7-dimension S-curve factor scoring with radar chart."""
from __future__ import annotations
import math
import plotly.graph_objects as go
from report.charts.theme import apply_theme


def s_curve_score(x: float, midpoint: float, k: float) -> float:
    """Sigmoid scoring: ~50 at midpoint, approaches 0/100 at extremes."""
    return 100.0 / (1.0 + math.exp(-k * (x - midpoint)))


def robustness_score(ic_is: float, ic_oos: float) -> float:
    """OOS robustness: lower IC drift = higher score."""
    if abs(ic_is) < 0.01:
        return 50.0  # neutral when IC_IS near zero
    drift = abs(ic_oos - ic_is) / abs(ic_is)
    return max(0.0, 100.0 * (1.0 - drift))


class CompositeScorer:
    """Score a factor across 7 dimensions and compute a weighted composite grade."""

    # (dimension_name, weight)
    WEIGHTS = [
        ("Predictive Power", 0.25),
        ("Signal Stability", 0.20),
        ("Profitability", 0.15),
        ("Monotonicity", 0.10),
        ("OOS Robustness", 0.15),
        ("Uniqueness", 0.10),
        ("Decay Resistance", 0.05),
    ]

    _GRADE_SCALE = [(90, "S"), (75, "A"), (60, "B"), (45, "C"), (0, "D")]

    @staticmethod
    def score_to_grade(score: float) -> str:
        for threshold, grade in CompositeScorer._GRADE_SCALE:
            if score >= threshold:
                return grade
        return "D"

    def compute(self, *, rank_ic_oos, icir_oos, ls_sharpe, monotonicity,
                ic_is, ic_oos, max_corr, ic_1d, ic_20d) -> dict:
        """Compute 7-dimension factor score.

        All parameters are keyword-only. Pass None when data unavailable.

        Returns:
            dict with dimensions, composite_score, composite_grade,
            library_rank, library_total.
        """
        dimensions = []

        # 1. Predictive Power
        pp = s_curve_score(abs(rank_ic_oos), midpoint=0.03, k=92) if rank_ic_oos is not None else 50
        dimensions.append(self._dim("Predictive Power", pp,
            data_available=rank_ic_oos is not None))

        # 2. Signal Stability
        ss = s_curve_score(abs(icir_oos), midpoint=0.3, k=9.2) if icir_oos is not None else 50
        dimensions.append(self._dim("Signal Stability", ss,
            data_available=icir_oos is not None))

        # 3. Profitability
        dimensions.append(self._dim("Profitability",
            s_curve_score(ls_sharpe, midpoint=0.5, k=4.6) if ls_sharpe is not None else 50,
            data_available=ls_sharpe is not None))

        # 4. Monotonicity
        mono_score = min(100, abs(monotonicity) * 100) if monotonicity is not None else 50
        dimensions.append(self._dim("Monotonicity", mono_score,
            data_available=monotonicity is not None))

        # 5. OOS Robustness
        rob = robustness_score(ic_is, ic_oos) if (ic_is is not None and ic_oos is not None) else 50
        dimensions.append(self._dim("OOS Robustness", rob,
            data_available=(ic_is is not None and ic_oos is not None)))

        # 6. Uniqueness: score = max(0, 100 * (1 - max_corr / 0.7))
        if max_corr is not None:
            uniq = max(0.0, min(100.0, 100.0 * (1.0 - max_corr / 0.7)))
        else:
            uniq = 50.0
        dimensions.append(self._dim("Uniqueness", uniq, data_available=max_corr is not None))

        # 7. Decay Resistance: linear 0->0, 0.7+->100
        if ic_1d is not None and ic_20d is not None and abs(ic_1d) > 0.001:
            ratio = abs(ic_20d) / abs(ic_1d)
            decay = min(100.0, ratio / 0.7 * 100)
        else:
            decay = 50.0
        dimensions.append(self._dim("Decay Resistance", decay,
            data_available=(ic_1d is not None and ic_20d is not None)))

        # Weighted composite
        composite = sum(d["score"] * w for d, (_, w) in zip(dimensions, self.WEIGHTS))

        return {
            "dimensions": dimensions,
            "composite_score": round(composite, 1),
            "composite_grade": self.score_to_grade(composite),
            "library_rank": None,   # populated by builder after scoring all factors
            "library_total": None,  # populated by builder after scoring all factors
        }

    def _dim(self, name, score, data_available=True):
        return {
            "name": name,
            "score": round(score if data_available else 50.0, 1),
            "data_available": data_available,
        }

    def generate_charts(self, result: dict) -> dict:
        """Generate radar chart from compute() result."""
        dims = result["dimensions"]
        names = [d["name"] for d in dims]
        scores = [d["score"] for d in dims]

        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=scores + [scores[0]],
            theta=names + [names[0]],
            fill="toself",
            name="Score",
        ))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])))
        apply_theme(fig)
        return {"radar": fig}
