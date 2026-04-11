"""Storage layer: typed YAML I/O, directory registry, and state file access.

Legacy exports (``StoragePaths``, ``load_yaml``, ``load_yaml_any``, ``save_yaml``)
are kept for import compatibility during the refactor. New consumers should
also import :class:`State`, :class:`StateFile`, and :func:`load_yaml_unsafe`.
"""

from .paths import StoragePaths
from .state import InvalidPhaseTransition, InvalidStateSchema, State, StateFile
from .yaml_io import load_yaml, load_yaml_any, load_yaml_unsafe, save_yaml

__all__ = [
    "StoragePaths",
    "State",
    "StateFile",
    "InvalidPhaseTransition",
    "InvalidStateSchema",
    "load_yaml",
    "load_yaml_any",
    "load_yaml_unsafe",
    "save_yaml",
]
