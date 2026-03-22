"""Register extracted factors into TimescaleDB metadata and factor tables."""

from __future__ import annotations

import logging
from typing import Dict, Optional

from ...data.storage.timescale_storage import TimescaleDB

from .factor_extractor import FactorInfo

logger = logging.getLogger(__name__)


class FactorRegister:
    """Register factor config and create factor storage table in TimescaleDB."""

    def __init__(self, db: Optional[TimescaleDB] = None) -> None:
        self.db = db or TimescaleDB()
        self._logger = logger

    def register(self, factor_info: FactorInfo) -> Dict[str, str]:
        """
        Register a factor in DB and create its data table.

        Returns:
            simple status dict
        """
        self._logger.info("Registering factor: %s", factor_info.name)

        try:
            self.db.create_factor_table(factor_info.name)
        except Exception as exc:
            self._logger.warning("Failed to create factor table for %s: %s", factor_info.name, exc)

        if getattr(self.db, "_conn", None) is None:
            self._logger.info("TimescaleDB simulation mode: skipped factor_config upsert")
            return {"name": factor_info.name, "status": "simulated"}

        try:
            with self.db.connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS factor_config (
                        name TEXT PRIMARY KEY,
                        display_name TEXT,
                        category TEXT,
                        frequency TEXT,
                        storage_type TEXT,
                        description TEXT,
                        created_at TIMESTAMP DEFAULT NOW(),
                        updated_at TIMESTAMP DEFAULT NOW()
                    );
                    """
                )
                cursor.execute(
                    """
                    INSERT INTO factor_config
                    (name, display_name, category, frequency, storage_type, description, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
                    ON CONFLICT (name) DO UPDATE SET
                        display_name = EXCLUDED.display_name,
                        category = EXCLUDED.category,
                        frequency = EXCLUDED.frequency,
                        storage_type = EXCLUDED.storage_type,
                        description = EXCLUDED.description,
                        updated_at = NOW();
                    """,
                    (
                        factor_info.name,
                        factor_info.display_name,
                        factor_info.category,
                        factor_info.frequency,
                        "narrow" if factor_info.frequency in {"minute", "1min"} else "wide",
                        factor_info.description,
                    ),
                )
            self._logger.info("Factor registered: %s", factor_info.name)
            return {"name": factor_info.name, "status": "registered"}
        except Exception as exc:
            self._logger.exception("Failed to register factor %s: %s", factor_info.name, exc)
            return {"name": factor_info.name, "status": "failed", "error": str(exc)}
