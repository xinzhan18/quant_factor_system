"""Tests for DataSynchronizer."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from mining.data_sync import DataSynchronizer


@pytest.fixture
def mock_db():
    """Mock TimescaleDB instance."""
    db = MagicMock()
    dates = pd.bdate_range("2023-01-02", periods=10)
    symbols = ["SH600000", "SZ000001"]
    rows = []
    for sym in symbols:
        for dt in dates:
            rows.append({
                "symbol": sym, "time": dt,
                "open": 10.0, "high": 10.5, "low": 9.5,
                "close": 10.2, "volume": 1e6, "amount": 1e7,
            })
    db.query_price.return_value = pd.DataFrame(rows)
    return db


@pytest.fixture
def syncer(mock_db, tmp_path):
    return DataSynchronizer(db=mock_db, qlib_dir=str(tmp_path / "qlib_data"))


class TestSyncDaily:
    def test_creates_directory_structure(self, syncer, tmp_path):
        syncer.sync_daily()
        qlib_dir = tmp_path / "qlib_data"
        assert (qlib_dir / "calendars").exists()
        assert (qlib_dir / "instruments").exists()
        assert (qlib_dir / "features").exists()

    def test_creates_calendar(self, syncer, tmp_path):
        syncer.sync_daily()
        cal_file = tmp_path / "qlib_data" / "calendars" / "day.txt"
        assert cal_file.exists()
        lines = cal_file.read_text().strip().split("\n")
        assert len(lines) == 10  # 10 trading days

    def test_creates_instruments(self, syncer, tmp_path):
        syncer.sync_daily()
        inst_file = tmp_path / "qlib_data" / "instruments" / "all.txt"
        assert inst_file.exists()
        content = inst_file.read_text()
        assert "SH600000" in content
        assert "SZ000001" in content

    def test_creates_feature_files(self, syncer, tmp_path):
        syncer.sync_daily()
        features_dir = tmp_path / "qlib_data" / "features"
        # Should have directories for each symbol
        assert (features_dir / "SH600000").exists()
        assert (features_dir / "SZ000001").exists()


class TestForwardReturns:
    def test_returns_1d_formula(self, syncer, mock_db, tmp_path):
        """Verify forward returns: close_tomorrow / close_today - 1."""
        dates = pd.bdate_range("2023-01-02", periods=3)
        rows = [
            {"symbol": "SH600000", "time": dates[0], "open": 10, "high": 11, "low": 9, "close": 10.0, "volume": 1e6, "amount": 1e7},
            {"symbol": "SH600000", "time": dates[1], "open": 10, "high": 11, "low": 9, "close": 12.0, "volume": 1e6, "amount": 1e7},
            {"symbol": "SH600000", "time": dates[2], "open": 10, "high": 11, "low": 9, "close": 11.0, "volume": 1e6, "amount": 1e7},
        ]
        mock_db.query_price.return_value = pd.DataFrame(rows)
        syncer.sync_daily()

        # Read back returns_1d binary for SH600000
        import struct
        bin_path = tmp_path / "qlib_data" / "features" / "SH600000" / "returns_1d.day.bin"
        assert bin_path.exists()
        with open(bin_path, "rb") as f:
            vals = []
            while True:
                chunk = f.read(4)
                if not chunk:
                    break
                vals.append(struct.unpack("<f", chunk)[0])

        # Day 0: forward return = 12.0/10.0 - 1 = 0.2
        assert abs(vals[0] - 0.2) < 0.01
        # Day 1: forward return = 11.0/12.0 - 1 ≈ -0.0833
        assert abs(vals[1] - (-1.0/12.0)) < 0.01


class TestMinuteAggregates:
    def test_sync_minute_creates_features(self, tmp_path):
        """Verify minute aggregate features are created."""
        mock_db = MagicMock()
        dates = pd.date_range("2023-01-02 09:30", periods=120, freq="1min")
        rows = []
        for dt in dates:
            rows.append({
                "symbol": "SH600000", "time": dt,
                "open": 10.0, "high": 10.1, "low": 9.9,
                "close": 10.0 + np.random.randn() * 0.1,
                "volume": 1000 + np.random.randint(0, 500),
                "amount": 10000,
            })
        mock_db.query_price.return_value = pd.DataFrame(rows)

        syncer = DataSynchronizer(db=mock_db, qlib_dir=str(tmp_path / "qlib_data"))
        # Create calendar first
        (tmp_path / "qlib_data" / "calendars").mkdir(parents=True)
        (tmp_path / "qlib_data" / "calendars" / "day.txt").write_text("2023-01-02\n")
        syncer.sync_minute_aggregates(start="2023-01-02")

        features_dir = tmp_path / "qlib_data" / "features" / "SH600000"
        assert (features_dir / "intraday_vol.day.bin").exists()
        assert (features_dir / "volume_conc.day.bin").exists()


class TestSymbolConversion:
    def test_to_qlib_format(self):
        assert DataSynchronizer.to_qlib_symbol("600000.SH") == "SH600000"
        assert DataSynchronizer.to_qlib_symbol("000001.SZ") == "SZ000001"
        assert DataSynchronizer.to_qlib_symbol("SH600000") == "SH600000"
