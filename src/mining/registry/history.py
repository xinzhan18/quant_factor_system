"""Factor history archival."""
import logging
import shutil
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


def archive_detail(factors_dir, factor_id):
    """Archive a factor detail YAML to factors/history/ before overwrite."""
    detail_path = Path(factors_dir) / f"factor_{factor_id}.yaml"
    if not detail_path.exists():
        return
    history_dir = Path(factors_dir) / "history"
    history_dir.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = f"factor_{factor_id}__replaced_{ts}.yaml"
    shutil.copy2(str(detail_path), str(history_dir / archive_name))
    logger.info("Archived %s → history/%s", detail_path.name, archive_name)
