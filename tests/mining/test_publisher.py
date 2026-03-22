"""Tests for FactorPublisher."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, call, patch

import numpy as np
import pandas as pd
import pytest

from mining.config import MiningConfig


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_qlib_df(n_dates: int = 5, n_instruments: int = 3, col_name: str = "Rank($close)") -> pd.DataFrame:
    """Build a minimal Qlib-format DataFrame: MultiIndex (datetime, instrument)."""
    dates = pd.bdate_range("2023-01-02", periods=n_dates)
    instruments = [f"SH60000{i}" for i in range(n_instruments)]
    idx = pd.MultiIndex.from_product([dates, instruments], names=["datetime", "instrument"])
    np.random.seed(0)
    return pd.DataFrame({col_name: np.random.randn(len(idx))}, index=idx)


def _make_flat_df(n_rows: int = 10) -> pd.DataFrame:
    """Build a flat (time, symbol, value) DataFrame."""
    dates = pd.bdate_range("2023-01-02", periods=n_rows)
    return pd.DataFrame({
        "time": dates,
        "symbol": "SH600000",
        "value": np.random.randn(n_rows),
    })


@pytest.fixture
def config(tmp_path):
    return MiningConfig(
        memory_dir=str(tmp_path / "memory"),
        library_dir=str(tmp_path / "library"),
        candidates_dir=str(tmp_path / "candidates"),
        train_start="2023-01-01",
        train_end="2023-12-31",
        test_start="2024-01-01",
        test_end="2024-06-30",
    )


@pytest.fixture
def publisher(config):
    from mining.publisher import FactorPublisher
    return FactorPublisher(config)


@pytest.fixture
def mock_conn():
    conn = MagicMock()
    cur = MagicMock()
    conn.cursor.return_value.__enter__ = MagicMock(return_value=cur)
    conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    return conn, cur


# ---------------------------------------------------------------------------
# _to_flat_df
# ---------------------------------------------------------------------------

class TestToFlatDf:
    def test_returns_flat_columns(self, publisher):
        qlib_df = _make_qlib_df()
        flat = publisher._to_flat_df(qlib_df)
        assert list(flat.columns) == ["time", "symbol", "value"]

    def test_row_count_matches(self, publisher):
        qlib_df = _make_qlib_df(n_dates=5, n_instruments=3)
        flat = publisher._to_flat_df(qlib_df)
        assert len(flat) == 5 * 3

    def test_values_preserved(self, publisher):
        qlib_df = _make_qlib_df(n_dates=2, n_instruments=2)
        flat = publisher._to_flat_df(qlib_df)
        # The values in 'value' column must equal the original single column
        original_vals = qlib_df.iloc[:, 0].values
        assert np.allclose(flat["value"].values, original_vals)

    def test_flat_index(self, publisher):
        qlib_df = _make_qlib_df()
        flat = publisher._to_flat_df(qlib_df)
        assert not isinstance(flat.index, pd.MultiIndex)

    def test_symbol_column_contains_instrument(self, publisher):
        qlib_df = _make_qlib_df(n_dates=1, n_instruments=2)
        flat = publisher._to_flat_df(qlib_df)
        assert "SH600000" in flat["symbol"].values
        assert "SH600001" in flat["symbol"].values


# ---------------------------------------------------------------------------
# ensure_tables
# ---------------------------------------------------------------------------

class TestEnsureTables:
    def test_executes_three_statements(self, publisher, mock_conn):
        conn, cur = mock_conn
        publisher.ensure_tables(conn)
        assert cur.execute.call_count == 3

    def test_commits(self, publisher, mock_conn):
        conn, cur = mock_conn
        publisher.ensure_tables(conn)
        conn.commit.assert_called_once()

    def test_creates_mining_factors(self, publisher, mock_conn):
        conn, cur = mock_conn
        publisher.ensure_tables(conn)
        calls_sql = [c.args[0] for c in cur.execute.call_args_list]
        assert any("mining_factors" in sql for sql in calls_sql)

    def test_creates_mining_factor_values(self, publisher, mock_conn):
        conn, cur = mock_conn
        publisher.ensure_tables(conn)
        calls_sql = [c.args[0] for c in cur.execute.call_args_list]
        assert any("mining_factor_values" in sql for sql in calls_sql)

    def test_creates_index(self, publisher, mock_conn):
        conn, cur = mock_conn
        publisher.ensure_tables(conn)
        calls_sql = [c.args[0] for c in cur.execute.call_args_list]
        assert any("idx_mfv_factor_date" in sql for sql in calls_sql)

    def test_idempotent_keyword_present(self, publisher, mock_conn):
        conn, cur = mock_conn
        publisher.ensure_tables(conn)
        calls_sql = [c.args[0] for c in cur.execute.call_args_list]
        assert all("IF NOT EXISTS" in sql for sql in calls_sql)


# ---------------------------------------------------------------------------
# _save_metrics
# ---------------------------------------------------------------------------

class TestSaveMetrics:
    def _make_factor_dict(self):
        return {
            "name": "Test Factor",
            "expression": "Rank($close)",
            "category": "momentum",
            "stage3": {
                "ic_mean_is": 0.060,
                "ic_mean_oos": 0.048,
                "ic_ir_is": 0.72,
                "ic_ir_oos": 0.55,
                "ic_win_rate": 0.63,
                "ls_return": 0.012,
                "monotonicity": 0.9,
            },
        }

    def test_executes_upsert(self, publisher, mock_conn):
        conn, cur = mock_conn
        factor_dict = self._make_factor_dict()
        publisher._save_metrics(conn, "001", factor_dict)
        assert cur.execute.called
        sql = cur.execute.call_args.args[0]
        assert "ON CONFLICT" in sql
        assert "mining_factors" in sql

    def test_passes_factor_id(self, publisher, mock_conn):
        conn, cur = mock_conn
        factor_dict = self._make_factor_dict()
        publisher._save_metrics(conn, "042", factor_dict)
        params = cur.execute.call_args.args[1]
        assert "042" in params

    def test_uses_do_update(self, publisher, mock_conn):
        conn, cur = mock_conn
        publisher._save_metrics(conn, "001", self._make_factor_dict())
        sql = cur.execute.call_args.args[0]
        assert "DO UPDATE" in sql

    def test_ic_mean_computed_as_average(self, publisher, mock_conn):
        """ic_mean should be (ic_mean_is + ic_mean_oos) / 2."""
        conn, cur = mock_conn
        factor_dict = self._make_factor_dict()
        publisher._save_metrics(conn, "001", factor_dict)
        params = cur.execute.call_args.args[1]
        # params[4] is ic_mean (5th positional param)
        expected_ic_mean = (0.060 + 0.048) / 2
        assert abs(params[4] - expected_ic_mean) < 1e-10

    def test_ic_ir_uses_is_value(self, publisher, mock_conn):
        """ic_ir column should use ic_ir_is from stage3."""
        conn, cur = mock_conn
        factor_dict = self._make_factor_dict()
        publisher._save_metrics(conn, "001", factor_dict)
        params = cur.execute.call_args.args[1]
        # params[5] is ic_ir (6th positional param)
        assert params[5] == 0.72


# ---------------------------------------------------------------------------
# _save_values
# ---------------------------------------------------------------------------

class TestSaveValues:
    def test_deletes_before_insert(self, publisher, mock_conn):
        conn, cur = mock_conn
        qlib_df = _make_qlib_df(n_dates=2, n_instruments=2)
        with patch("mining.publisher.execute_values") as mock_ev:
            publisher._save_values(conn, "001", qlib_df)
        # First call should be DELETE
        first_sql = cur.execute.call_args_list[0].args[0]
        assert "DELETE" in first_sql
        assert "mining_factor_values" in first_sql

    def test_delete_uses_factor_id(self, publisher, mock_conn):
        conn, cur = mock_conn
        qlib_df = _make_qlib_df(n_dates=2, n_instruments=2)
        with patch("mining.publisher.execute_values") as mock_ev:
            publisher._save_values(conn, "007", qlib_df)
        delete_params = cur.execute.call_args_list[0].args[1]
        assert "007" in delete_params

    def test_calls_execute_values(self, publisher, mock_conn):
        conn, cur = mock_conn
        qlib_df = _make_qlib_df(n_dates=3, n_instruments=4)
        with patch("mining.publisher.execute_values") as mock_ev:
            publisher._save_values(conn, "001", qlib_df)
        assert mock_ev.called

    def test_execute_values_page_size(self, publisher, mock_conn):
        conn, cur = mock_conn
        qlib_df = _make_qlib_df(n_dates=3, n_instruments=4)
        with patch("mining.publisher.execute_values") as mock_ev:
            publisher._save_values(conn, "001", qlib_df)
        _, kwargs = mock_ev.call_args
        assert kwargs.get("page_size") == 5000

    def test_row_count_matches(self, publisher, mock_conn):
        conn, cur = mock_conn
        n_dates, n_instruments = 4, 5
        qlib_df = _make_qlib_df(n_dates=n_dates, n_instruments=n_instruments)
        captured_rows = []

        def capture(*args, **kwargs):
            captured_rows.extend(args[2])

        with patch("mining.publisher.execute_values", side_effect=capture):
            publisher._save_values(conn, "001", qlib_df)

        assert len(captured_rows) == n_dates * n_instruments


# ---------------------------------------------------------------------------
# publish — end-to-end
# ---------------------------------------------------------------------------

class TestPublish:
    def _factor_dict(self):
        return {
            "name": "Test Factor",
            "expression": "Rank($close)",
            "category": "momentum",
            "stage3": {
                "ic_mean_is": 0.060,
                "ic_mean_oos": 0.048,
                "ic_ir_is": 0.72,
                "ic_ir_oos": 0.55,
                "ic_win_rate": 0.63,
                "ls_return": 0.012,
                "monotonicity": 0.9,
            },
        }

    def test_commit_on_success(self, publisher, mock_conn, tmp_path):
        conn, cur = mock_conn
        with (
            patch.object(publisher, "_get_connection", return_value=conn),
            patch.object(publisher, "ensure_tables"),
            patch.object(publisher, "_save_metrics"),
            patch.object(publisher, "_save_values"),
            patch.object(publisher, "_generate_report", return_value=str(tmp_path / "report.html")),
            patch.object(publisher, "_update_report_path"),
        ):
            publisher.publish("001", self._factor_dict(), _make_qlib_df(), _make_qlib_df())
        # commit called at least once (after DB writes)
        assert conn.commit.call_count >= 1

    def test_rollback_on_error(self, publisher, mock_conn):
        conn, cur = mock_conn
        with (
            patch.object(publisher, "_get_connection", return_value=conn),
            patch.object(publisher, "ensure_tables"),
            patch.object(publisher, "_save_metrics", side_effect=RuntimeError("DB error")),
        ):
            with pytest.raises(RuntimeError, match="DB error"):
                publisher.publish("001", self._factor_dict(), _make_qlib_df(), _make_qlib_df())
        conn.rollback.assert_called_once()

    def test_no_commit_on_error(self, publisher, mock_conn):
        conn, cur = mock_conn
        with (
            patch.object(publisher, "_get_connection", return_value=conn),
            patch.object(publisher, "ensure_tables"),
            patch.object(publisher, "_save_metrics", side_effect=RuntimeError("DB error")),
        ):
            with pytest.raises(RuntimeError):
                publisher.publish("001", self._factor_dict(), _make_qlib_df(), _make_qlib_df())
        conn.commit.assert_not_called()

    def test_report_path_returned(self, publisher, mock_conn, tmp_path):
        conn, cur = mock_conn
        expected_path = str(tmp_path / "report.html")
        with (
            patch.object(publisher, "_get_connection", return_value=conn),
            patch.object(publisher, "ensure_tables"),
            patch.object(publisher, "_save_metrics"),
            patch.object(publisher, "_save_values"),
            patch.object(publisher, "_generate_report", return_value=expected_path),
            patch.object(publisher, "_update_report_path"),
        ):
            result = publisher.publish("001", self._factor_dict(), _make_qlib_df(), _make_qlib_df())
        assert result == expected_path

    def test_combines_is_oos(self, publisher, mock_conn, tmp_path):
        """IS + OOS DataFrames are combined before saving."""
        conn, cur = mock_conn
        is_df = _make_qlib_df(n_dates=5, n_instruments=2)
        oos_df = _make_qlib_df(n_dates=3, n_instruments=2)
        # Give them different dates so no duplicates
        oos_dates = pd.bdate_range("2024-01-02", periods=3)
        oos_df.index = pd.MultiIndex.from_product(
            [oos_dates, ["SH600000", "SH600001"]], names=["datetime", "instrument"]
        )

        saved_values = {}

        def capture_save(c, fid, df):
            saved_values["df"] = df

        with (
            patch.object(publisher, "_get_connection", return_value=conn),
            patch.object(publisher, "ensure_tables"),
            patch.object(publisher, "_save_metrics"),
            patch.object(publisher, "_save_values", side_effect=capture_save),
            patch.object(publisher, "_generate_report", return_value=str(tmp_path / "r.html")),
            patch.object(publisher, "_update_report_path"),
        ):
            publisher.publish("001", self._factor_dict(), is_df, oos_df)

        combined = saved_values["df"]
        assert len(combined) == (5 + 3) * 2

    def test_report_failure_does_not_rollback(self, publisher, mock_conn):
        """Report generation failure is non-transactional — DB writes are committed, method returns gracefully."""
        conn, cur = mock_conn
        with (
            patch.object(publisher, "_get_connection", return_value=conn),
            patch.object(publisher, "ensure_tables"),
            patch.object(publisher, "_save_metrics"),
            patch.object(publisher, "_save_values"),
            patch.object(publisher, "_generate_report", return_value=""),
            patch.object(publisher, "_update_report_path"),
        ):
            result = publisher.publish("001", self._factor_dict(), _make_qlib_df(), _make_qlib_df())
        # Returns empty string, no exception raised
        assert result == ""
        # DB was committed (at least once for the transactional writes), not rolled back
        assert conn.commit.call_count >= 1
        conn.rollback.assert_not_called()


# ---------------------------------------------------------------------------
# _get_connection (lazy init)
# ---------------------------------------------------------------------------

class TestGetConnection:
    def test_lazy_connect(self, publisher):
        mock_conn = MagicMock()
        with patch("psycopg2.connect", return_value=mock_conn) as mock_connect:
            conn1 = publisher._get_connection()
            conn2 = publisher._get_connection()
        # psycopg2.connect called only once
        assert mock_connect.call_count == 1
        assert conn1 is conn2

    def test_uses_connection_string(self, publisher):
        mock_conn = MagicMock()
        expected_cs = publisher.config.system.database.connection_string
        with patch("psycopg2.connect", return_value=mock_conn) as mock_connect:
            publisher._get_connection()
        mock_connect.assert_called_once_with(expected_cs)
