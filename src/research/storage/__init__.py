"""Storage layer for the research system.

Provides typed YAML I/O, path management, and CRUD stores for every
persistent object in the research pipeline.
"""

from research.storage.paths import StoragePaths
from research.storage.yaml_io import load_yaml, save_yaml, load_yaml_unsafe

__all__ = [
    "StoragePaths",
    "load_yaml",
    "save_yaml",
    "load_yaml_unsafe",
]
