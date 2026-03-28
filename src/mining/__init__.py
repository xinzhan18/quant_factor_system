"""FactorMiner: Automated factor mining with Experience Memory."""

__version__ = "4.1.0"

from .config import MiningConfig
from .expression import ExpressionValidator, ValidationResult
from .evaluator import FactorMiningEvaluator, BatchResult
from .library import FactorLibrary
from .memory import ExperienceMemory
from .preprocessing import FactorPreprocessor
from data.qlib_sync import DataSynchronizer
from .ops_adapter import OpsAdapter
from .sandbox import run_factor_in_sandbox, SandboxError
from .evolution import EvolutionEngine
from .scheduler import Scheduler
from .logic_library import MarketLogicLibrary

__all__ = [
    "MiningConfig",
    "ExpressionValidator",
    "ValidationResult",
    "FactorMiningEvaluator",
    "BatchResult",
    "FactorLibrary",
    "ExperienceMemory",
    "FactorPreprocessor",
    "DataSynchronizer",
    "OpsAdapter",
    "run_factor_in_sandbox",
    "SandboxError",
    "EvolutionEngine",
    "Scheduler",
    "MarketLogicLibrary",
]
