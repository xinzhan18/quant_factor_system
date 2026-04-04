"""Factor values cache loading from pickle files."""
import logging
import pickle
from pathlib import Path

logger = logging.getLogger(__name__)


def load_values_cache(factor_name, candidates_dir):
    """Try to load factor values from pickle cache."""
    cdir = Path(candidates_dir)
    for pkl in sorted(cdir.glob("*_values.pkl"), reverse=True):
        try:
            with open(pkl, "rb") as f:
                cache = pickle.load(f)
            if factor_name in cache:
                logger.info("Loaded factor values from cache: %s", pkl)
                return cache[factor_name]["is"], cache[factor_name]["oos"]
        except Exception:
            continue
    return None, None
