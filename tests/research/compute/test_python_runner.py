"""Tests for python_runner (R8 Python factor escape hatch)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from research.compute.python_runner import (
    PythonFactorContractError,
    load_python_candidate,
    run_python_factor,
)


def _good_factor_source() -> str:
    return """
from __future__ import annotations
import numpy as np
import pandas as pd

REQUIRED_FIELDS = ["$close", "$volume"]
VECTORIZED = True


def compute(df: pd.DataFrame) -> pd.Series:
    close = df["$close"]
    volume = df["$volume"]
    return (close - close.groupby(level=0).mean()) * np.sign(volume)
"""


def _build_market_df(n_dates: int = 5, n_stocks: int = 4) -> pd.DataFrame:
    dates = pd.bdate_range("2024-01-02", periods=n_dates)
    stocks = [f"SYM{i:02d}" for i in range(n_stocks)]
    idx = pd.MultiIndex.from_product(
        [dates, stocks], names=["time", "symbol"]
    )
    rng = np.random.default_rng(0)
    return pd.DataFrame(
        {
            "$close": rng.uniform(10, 100, size=len(idx)),
            "$volume": rng.uniform(1e5, 1e7, size=len(idx)),
        },
        index=idx,
    )


@pytest.fixture
def good_factor(tmp_path: Path) -> Path:
    p = tmp_path / "good.py"
    p.write_text(_good_factor_source(), encoding="utf-8")
    return p


class TestLoadValidModule:
    def test_loads_and_reports_metadata(self, good_factor: Path) -> None:
        loaded = load_python_candidate(good_factor)
        assert loaded.required_fields == ["$close", "$volume"]
        assert loaded.vectorized is True
        assert callable(loaded.module.compute)

    def test_run_returns_series(self, good_factor: Path) -> None:
        loaded = load_python_candidate(good_factor)
        df = _build_market_df()
        out = run_python_factor(loaded, df)
        assert isinstance(out, pd.Series)
        assert isinstance(out.index, pd.MultiIndex)
        assert out.shape == (len(df),)


class TestAstWhitelist:
    def test_forbidden_import_subprocess(self, tmp_path: Path) -> None:
        p = tmp_path / "bad.py"
        p.write_text(
            "import subprocess\n"
            "REQUIRED_FIELDS=['$close']\nVECTORIZED=True\n"
            "def compute(df): return df['$close']\n",
            encoding="utf-8",
        )
        with pytest.raises(PythonFactorContractError, match="forbidden import"):
            load_python_candidate(p)

    def test_forbidden_import_os(self, tmp_path: Path) -> None:
        p = tmp_path / "bad.py"
        p.write_text(
            "import os\n"
            "REQUIRED_FIELDS=['$close']\nVECTORIZED=True\n"
            "def compute(df): return df['$close']\n",
            encoding="utf-8",
        )
        with pytest.raises(PythonFactorContractError, match="forbidden import"):
            load_python_candidate(p)

    def test_forbidden_call_eval(self, tmp_path: Path) -> None:
        p = tmp_path / "bad.py"
        p.write_text(
            "REQUIRED_FIELDS=['$close']\nVECTORIZED=True\n"
            "def compute(df):\n"
            "    x = eval('1+1')\n"
            "    return df['$close']\n",
            encoding="utf-8",
        )
        with pytest.raises(PythonFactorContractError, match="forbidden call 'eval"):
            load_python_candidate(p)

    def test_forbidden_call_open(self, tmp_path: Path) -> None:
        p = tmp_path / "bad.py"
        p.write_text(
            "REQUIRED_FIELDS=['$close']\nVECTORIZED=True\n"
            "def compute(df):\n"
            "    f = open('/tmp/x')\n"
            "    return df['$close']\n",
            encoding="utf-8",
        )
        with pytest.raises(PythonFactorContractError, match="forbidden call 'open"):
            load_python_candidate(p)

    def test_forbidden_getattr(self, tmp_path: Path) -> None:
        p = tmp_path / "bad.py"
        p.write_text(
            "REQUIRED_FIELDS=['$close']\nVECTORIZED=True\n"
            "def compute(df):\n"
            "    getattr(df, '__class__')\n"
            "    return df['$close']\n",
            encoding="utf-8",
        )
        with pytest.raises(
            PythonFactorContractError, match="attribute manipulation"
        ):
            load_python_candidate(p)

    def test_syntax_error(self, tmp_path: Path) -> None:
        p = tmp_path / "bad.py"
        # Truly invalid — unmatched paren cannot be parsed by ast.parse
        p.write_text("def compute(df:\n    return df\n", encoding="utf-8")
        with pytest.raises(PythonFactorContractError, match="syntax error"):
            load_python_candidate(p)


class TestModuleContract:
    def test_missing_required_fields(self, tmp_path: Path) -> None:
        p = tmp_path / "bad.py"
        p.write_text(
            "VECTORIZED=True\n"
            "def compute(df): return df\n",
            encoding="utf-8",
        )
        with pytest.raises(
            PythonFactorContractError, match="REQUIRED_FIELDS"
        ):
            load_python_candidate(p)

    def test_required_fields_not_list(self, tmp_path: Path) -> None:
        p = tmp_path / "bad.py"
        p.write_text(
            "REQUIRED_FIELDS='$close'\nVECTORIZED=True\n"
            "def compute(df): return df\n",
            encoding="utf-8",
        )
        with pytest.raises(PythonFactorContractError, match="must be a list"):
            load_python_candidate(p)

    def test_required_field_missing_dollar_prefix(
        self, tmp_path: Path
    ) -> None:
        p = tmp_path / "bad.py"
        p.write_text(
            "REQUIRED_FIELDS=['close']\nVECTORIZED=True\n"
            "def compute(df): return df\n",
            encoding="utf-8",
        )
        with pytest.raises(PythonFactorContractError, match="\\$.*prefixed"):
            load_python_candidate(p)

    def test_vectorized_false_rejected(self, tmp_path: Path) -> None:
        p = tmp_path / "bad.py"
        p.write_text(
            "REQUIRED_FIELDS=['$close']\nVECTORIZED=False\n"
            "def compute(df): return df['$close']\n",
            encoding="utf-8",
        )
        with pytest.raises(
            PythonFactorContractError, match="VECTORIZED must be True"
        ):
            load_python_candidate(p)

    def test_compute_wrong_signature(self, tmp_path: Path) -> None:
        p = tmp_path / "bad.py"
        p.write_text(
            "REQUIRED_FIELDS=['$close']\nVECTORIZED=True\n"
            "def compute(df, extra): return df['$close']\n",
            encoding="utf-8",
        )
        with pytest.raises(
            PythonFactorContractError, match="exactly one argument"
        ):
            load_python_candidate(p)


class TestRunPythonFactor:
    def test_missing_column_raises(self, good_factor: Path) -> None:
        loaded = load_python_candidate(good_factor)
        df = _build_market_df()
        df = df.drop(columns=["$volume"])
        with pytest.raises(
            PythonFactorContractError, match="missing columns"
        ):
            run_python_factor(loaded, df)

    def test_non_series_return_raises(self, tmp_path: Path) -> None:
        p = tmp_path / "bad.py"
        p.write_text(
            "import pandas as pd\n"
            "REQUIRED_FIELDS=['$close']\nVECTORIZED=True\n"
            "def compute(df): return 42\n",
            encoding="utf-8",
        )
        loaded = load_python_candidate(p)
        df = _build_market_df()
        with pytest.raises(
            PythonFactorContractError, match="must return pd.Series"
        ):
            run_python_factor(loaded, df)

    def test_flat_index_return_raises(self, tmp_path: Path) -> None:
        p = tmp_path / "bad.py"
        p.write_text(
            "import pandas as pd\n"
            "REQUIRED_FIELDS=['$close']\nVECTORIZED=True\n"
            "def compute(df): return pd.Series([1,2,3])\n",
            encoding="utf-8",
        )
        loaded = load_python_candidate(p)
        df = _build_market_df()
        with pytest.raises(
            PythonFactorContractError, match="MultiIndex"
        ):
            run_python_factor(loaded, df)
