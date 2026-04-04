"""Backward-compatible re-export — canonical location is registry.publisher."""
from .registry.publisher import FactorPublisher
# Re-export execute_values for test patch targets
try:
    from psycopg2.extras import execute_values
except ImportError:
    pass
