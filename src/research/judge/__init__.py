"""Research judge -- structured verdict generation for candidates, routes, and logics.

Modules:
    mechanism_alignment:  4-check mechanism alignment assessment
    candidate_judge:      6-dimension candidate verdict (admit/reserve/reject/replace)
    replace_protocol:     5-dimension discrete comparison for factor replacement
    route_judge:          Batch-local route verdict (continue/pause/kill/promote_family)
    logic_judge:          Logic lifecycle recommendation (active/warm/.../dead)
    holdout_review:       Asynchronous holdout review (supportive/neutral/contradictory)
    verdict_builder:      BatchJudgeReport assembly from individual verdicts
"""

from research.judge.mechanism_alignment import MechanismAlignment
from research.judge.candidate_judge import CandidateJudge
from research.judge.replace_protocol import ReplaceProtocol
from research.judge.route_judge import RouteJudge
from research.judge.logic_judge import LogicJudge
from research.judge.holdout_review import HoldoutReview
from research.judge.verdict_builder import VerdictBuilder

__all__ = [
    "MechanismAlignment",
    "CandidateJudge",
    "ReplaceProtocol",
    "RouteJudge",
    "LogicJudge",
    "HoldoutReview",
    "VerdictBuilder",
]
