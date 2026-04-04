"""FactorMiner: Automated factor mining with Experience Memory."""

__version__ = "5.0.0"

# Stable public API — import from canonical sub-package locations
from .config import MiningConfig
from .expression import ExpressionValidator, ValidationResult
from .domain.results import BatchResult
from .domain.schema import FactorRecord, normalize_metrics
from .evaluation.gates import apply_hard_gates
from .registry import FactorLibrary
from .memory import ExperienceMemory
from .preprocessing import FactorPreprocessor
from .ops_adapter import OpsAdapter
from .sandbox import run_factor_in_sandbox, SandboxError
from .evolution import EvolutionEngine
from .logic import MarketLogicLibrary, Scheduler

# Evaluator — kept at root level for backward compat
from .evaluator import FactorMiningEvaluator

__all__ = [
    "MiningConfig",
    "ExpressionValidator",
    "ValidationResult",
    "FactorMiningEvaluator",
    "BatchResult",
    "FactorRecord",
    "FactorLibrary",
    "ExperienceMemory",
    "FactorPreprocessor",
    "OpsAdapter",
    "run_factor_in_sandbox",
    "SandboxError",
    "EvolutionEngine",
    "MarketLogicLibrary",
    "Scheduler",
]
