"""Tests for PriceView (uses synthetic parquet via tmp_path)."""
from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from research.backtest.data_view import PriceView


def test_from_dataframe_normalizes_dollar_prefix(synthetic_panel):
    # synthetic_panel uses bare names; verify $-prefixed cols also work
    df = synthetic_panel.copy()
    df.columns = [f"${c}" if not c.startswith("$") else c for c in df.columns]
    v = PriceView.from_dataframe(df)
    assert "open" in v._df.columns
    assert "$open" not in v._df.columns


def test_snapshot_ts_returns_max(synthetic_panel):
    v = PriceView.from_dataframe(synthetic_panel)
    assert v.snapshot_ts.date() == date(2024, 6, 28)


def test_slice_eod_returns_required_cols(synthetic_panel):
    v = PriceView.from_dataframe(synthetic_panel)
    df = v.slice_eod(date(2024, 6, 26), ["A", "B"])
    for col in ["open", "high", "low", "close", "volume", "amount", "limit_up", "limit_down"]:
        assert col in df.columns
    assert len(df) == 2


def test_slice_eod_missing_symbol_omitted(synthetic_panel):
    v = PriceView.from_dataframe(synthetic_panel)
    df = v.slice_eod(date(2024, 6, 26), ["A", "DOES_NOT_EXIST"])
    assert "DOES_NOT_EXIST" not in df.index
    assert "A" in df.index


def test_slice_eod_missing_date_returns_empty(synthetic_panel):
    v = PriceView.from_dataframe(synthetic_panel)
    df = v.slice_eod(date(2099, 1, 1), ["A"])
    assert df.empty


def test_slice_panel_inclusive(synthetic_panel):
    v = PriceView.from_dataframe(synthetic_panel)
    df = v.slice_panel(date(2024, 6, 24), date(2024, 6, 26), ["A"])
    assert len(df) == 3   # Mon, Tue, Wed


def test_from_parquet_roundtrip(synthetic_panel, tmp_path):
    path = tmp_path / "test.parquet"
    synthetic_panel.to_parquet(path)
    v = PriceView.from_parquet(path)
    assert v.snapshot_ts.date() == date(2024, 6, 28)
    df = v.slice_eod(date(2024, 6, 26), ["A"])
    assert "close" in df.columns


def test_from_parquet_rejects_non_multiindex(tmp_path):
    path = tmp_path / "flat.parquet"
    pd.DataFrame({"x": [1, 2, 3]}).to_parquet(path)
    with pytest.raises(ValueError, match="MultiIndex"):
        PriceView.from_parquet(path)
