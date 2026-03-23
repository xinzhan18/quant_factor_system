import pytest
import numpy as np
import pandas as pd
from unittest.mock import MagicMock
from data.qlib_sync import DataSynchronizer


class TestAuxFieldSync:
    """Test that auxiliary fields are synced to Qlib format."""

    def _make_mock_db(self):
        db = MagicMock()
        db.query_price.return_value = pd.DataFrame({
            "time": pd.date_range("2024-01-02", periods=3).repeat(2),
            "symbol": ["600000.SH", "000001.SZ"] * 3,
            "open": [10.0, 20.0] * 3,
            "high": [11.0, 21.0] * 3,
            "low": [9.0, 19.0] * 3,
            "close": [10.5, 20.5] * 3,
            "volume": [1e6, 2e6] * 3,
            "amount": [1e7, 2e7] * 3,
            "limit_up": [11.55, 22.55] * 3,
            "limit_down": [9.45, 18.45] * 3,
        })
        return db

    def test_limit_prices_synced(self, tmp_path):
        qlib_dir = tmp_path / "qlib_data"
        db = self._make_mock_db()
        sync = DataSynchronizer(db, qlib_dir=str(qlib_dir))
        sync.sync_daily(start="2024-01-02", end="2024-01-04")

        # limit_up.day.bin should exist
        bin_path = qlib_dir / "features" / "SH600000" / "limit_up.day.bin"
        assert bin_path.exists()

        bin_path_down = qlib_dir / "features" / "SH600000" / "limit_down.day.bin"
        assert bin_path_down.exists()

    def test_missing_limit_fields_graceful(self, tmp_path):
        """When DB has no limit fields, sync still works without them."""
        qlib_dir = tmp_path / "qlib_data"
        db = MagicMock()
        db.query_price.return_value = pd.DataFrame({
            "time": pd.date_range("2024-01-02", periods=2).repeat(1),
            "symbol": ["600000.SH"] * 2,
            "open": [10.0, 10.5],
            "high": [11.0, 11.5],
            "low": [9.0, 9.5],
            "close": [10.5, 11.0],
            "volume": [1e6, 1e6],
            "amount": [1e7, 1e7],
        })
        sync = DataSynchronizer(db, qlib_dir=str(qlib_dir))
        sync.sync_daily(start="2024-01-02", end="2024-01-03")

        # close.day.bin exists, limit_up does not
        assert (qlib_dir / "features" / "SH600000" / "close.day.bin").exists()
        assert not (qlib_dir / "features" / "SH600000" / "limit_up.day.bin").exists()
