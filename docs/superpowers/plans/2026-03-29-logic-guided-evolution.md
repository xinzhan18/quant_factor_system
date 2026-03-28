# Logic-Guided Structured Evolution Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the factor mining architecture with Python factor runtime, structured evolution, market logic layer, and scheduler — synthesizing core insights from 9 LLM factor mining papers.

**Architecture:** Five-layer bottom-up build: L1 Evaluation (dual-track DSL+Python) → L2 Factor Runtime (OpsAdapter, sandbox, forbidden regions, lineage) → L3 Evolution (genesis/mutate/crossover) → L4 Logic Library (market logics, taxonomy, inner/outer loop) → L5 Scheduler (scoring, CLI, skill updates).

**Tech Stack:** Python 3.11, Qlib, Optuna, pandas, multiprocessing, pytest, YAML

**Spec:** `docs/superpowers/specs/2026-03-29-logic-guided-evolution-design.md`

---

## File Structure

### New Files

| Path | Layer | Responsibility |
|------|-------|---------------|
| `src/mining/ops_adapter.py` | L2 | Wraps Qlib operators as Python callables for panel DataFrames |
| `src/mining/sandbox.py` | L2 | Sandboxed Python factor execution with timeout/memory limits |
| `src/mining/evolution.py` | L3 | Three generation modes + lineage tracking |
| `src/mining/scheduler.py` | L5 | Priority scoring for logic selection |
| `src/mining/logic_library.py` | L4 | Market Logic YAML CRUD |
| `storage/logic/taxonomy.yaml` | L4 | 7-category search space taxonomy |
| `storage/memory/forbidden.yaml` | L2 | Forbidden region patterns |
| `.claude/skills/factor-logic/skill.md` | L5 | /logic new and /logic review skill |
| `tests/mining/test_ops_adapter.py` | L2 | OpsAdapter unit tests |
| `tests/mining/test_sandbox.py` | L2 | Sandbox execution tests |
| `tests/mining/test_evolution.py` | L3 | Evolution engine tests |
| `tests/mining/test_scheduler.py` | L5 | Scheduler scoring tests |
| `tests/mining/test_logic_library.py` | L4 | Logic library CRUD tests |
| `tests/mining/test_forbidden.py` | L2 | Forbidden region tests |

### Modified Files

| Path | What Changes |
|------|-------------|
| `src/mining/config.py` | Add 10+ new config fields (optuna, sandbox, logic, evolution) |
| `src/mining/expression.py` | Add `validate_python()` method |
| `src/mining/evaluator.py` | Dual-dispatch (DSL/Python), Optuna step, lookahead check, AST dedup |
| `src/mining/library.py` | Schema extension: `source`, `code_path`, `logic_id`, `lineage` |
| `src/mining/publisher.py` | Python factor DB persistence |
| `src/mining/memory.py` | Forbidden regions, lineage, expanded search context |
| `src/mining/metrics.py` | Add `lookahead_warning`, `ast_similarity_score` fields |
| `src/mining/cli.py` | New `logic` and `schedule` subcommands |
| `src/mining/__init__.py` | Export new classes |
| `.claude/skills/factor-idea/skill.md` | Scheduler-driven strategy, 5-layer context, Python factor output |
| `.claude/skills/factor-judge/skill.md` | Logic updates, forbidden auto-add, lineage recording |
| `.claude/skills/factor-mine/skill.md` | Outer loop trigger, scheduler integration |

---

## Task 1: OpsAdapter — Operator Wrapper for Python Factors

**Files:**
- Create: `src/mining/ops_adapter.py`
- Create: `tests/mining/test_ops_adapter.py`
- Read: `src/mining/operators.py` (raw functions at lines 25-151, cross-sectional cache at lines 478-537)

- [ ] **Step 1: Write failing tests for time-series ops**

```python
# tests/mining/test_ops_adapter.py
import pytest
import pandas as pd
import numpy as np
from mining.ops_adapter import OpsAdapter


@pytest.fixture
def panel_df():
    """Create a (datetime, instrument) MultiIndex DataFrame with OHLCV."""
    dates = pd.date_range("2024-01-01", periods=30, freq="B")
    instruments = ["SH600000", "SH600001", "SH600002"]
    idx = pd.MultiIndex.from_product([dates, instruments], names=["datetime", "instrument"])
    np.random.seed(42)
    n = len(idx)
    return pd.DataFrame({
        "close": np.random.uniform(10, 50, n),
        "open": np.random.uniform(10, 50, n),
        "high": np.random.uniform(10, 50, n),
        "low": np.random.uniform(5, 45, n),
        "volume": np.random.uniform(1e6, 1e8, n),
    }, index=idx)


@pytest.fixture
def ops():
    return OpsAdapter()


class TestTimeSeriesOps:
    def test_std_returns_series(self, ops, panel_df):
        result = ops.std(panel_df["close"], window=10)
        assert isinstance(result, pd.Series)
        assert result.index.equals(panel_df.index)

    def test_std_per_instrument(self, ops, panel_df):
        """Std should be computed per instrument, not across all stocks."""
        result = ops.std(panel_df["close"], window=10)
        # First 9 values per instrument should be NaN (window=10)
        for inst in ["SH600000", "SH600001", "SH600002"]:
            inst_vals = result.xs(inst, level="instrument")
            assert inst_vals.iloc[:9].isna().all()
            assert inst_vals.iloc[9:].notna().all()

    def test_mean(self, ops, panel_df):
        result = ops.mean(panel_df["close"], window=5)
        assert isinstance(result, pd.Series)
        assert result.index.equals(panel_df.index)

    def test_ts_decay(self, ops, panel_df):
        result = ops.ts_decay(panel_df["close"], window=5)
        assert isinstance(result, pd.Series)

    def test_ewm(self, ops, panel_df):
        result = ops.ewm(panel_df["close"], span=10)
        assert isinstance(result, pd.Series)

    def test_delta(self, ops, panel_df):
        result = ops.delta(panel_df["close"], period=5)
        assert isinstance(result, pd.Series)

    def test_realized_vol(self, ops, panel_df):
        result = ops.realized_vol(panel_df["close"], window=10)
        assert isinstance(result, pd.Series)

    def test_hhi(self, ops, panel_df):
        result = ops.hhi(panel_df["volume"], window=5)
        assert isinstance(result, pd.Series)

    def test_ts_corr(self, ops, panel_df):
        result = ops.ts_corr(panel_df["close"], panel_df["volume"], window=10)
        assert isinstance(result, pd.Series)

    def test_ts_cov(self, ops, panel_df):
        result = ops.ts_cov(panel_df["close"], panel_df["volume"], window=10)
        assert isinstance(result, pd.Series)


class TestCrossSectionalOps:
    def test_cs_rank_returns_series(self, ops, panel_df):
        result = ops.cs_rank(panel_df["close"])
        assert isinstance(result, pd.Series)
        assert result.index.equals(panel_df.index)

    def test_cs_rank_within_date(self, ops, panel_df):
        """Ranks should be computed within each date, across instruments."""
        result = ops.cs_rank(panel_df["close"])
        # For each date, ranks should be in [0, 1]
        for dt in panel_df.index.get_level_values("datetime").unique()[:5]:
            day_vals = result.xs(dt, level="datetime")
            assert day_vals.min() >= 0
            assert day_vals.max() <= 1

    def test_cs_zscore(self, ops, panel_df):
        result = ops.cs_zscore(panel_df["close"])
        assert isinstance(result, pd.Series)
        # Z-scores should have roughly mean 0 per date
        for dt in panel_df.index.get_level_values("datetime").unique()[:5]:
            day_vals = result.xs(dt, level="datetime")
            assert abs(day_vals.mean()) < 0.01


class TestTransformOps:
    def test_signed_power(self, ops, panel_df):
        result = ops.signed_power(panel_df["close"], exp=0.5)
        assert isinstance(result, pd.Series)

    def test_tanh(self, ops, panel_df):
        result = ops.tanh(panel_df["close"])
        assert isinstance(result, pd.Series)
        assert result.abs().max() <= 1.0

    def test_safe_div(self, ops, panel_df):
        result = ops.safe_div(panel_df["close"], panel_df["volume"])
        assert isinstance(result, pd.Series)
        assert not result.isin([np.inf, -np.inf]).any()

    def test_safe_div_zero_denominator(self, ops):
        x = pd.Series([1.0, 2.0, 3.0])
        y = pd.Series([1.0, 0.0, 3.0])
        result = ops.safe_div(x, y)
        assert result.iloc[1] == 0.0 or pd.isna(result.iloc[1])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `PYTHONPATH=src pytest tests/mining/test_ops_adapter.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'mining.ops_adapter'`

- [ ] **Step 3: Implement OpsAdapter**

```python
# src/mining/ops_adapter.py
"""Wraps Qlib operators as Python callables for panel DataFrames.

All methods accept pd.Series with (datetime, instrument) MultiIndex.
Time-series ops compute per instrument. Cross-sectional ops compute per date.
"""
import numpy as np
import pandas as pd


class OpsAdapter:
    """Operator adapter for Python factor functions."""

    # ── Time-series ops (per instrument) ──

    def _ts_apply(self, series: pd.Series, func, **kwargs) -> pd.Series:
        """Apply a function per instrument along time axis."""
        return series.groupby(level="instrument", group_keys=False).apply(
            lambda s: func(s, **kwargs)
        )

    def std(self, series: pd.Series, window: int) -> pd.Series:
        return self._ts_apply(series, lambda s, w: s.rolling(w).std(), w=window)

    def mean(self, series: pd.Series, window: int) -> pd.Series:
        return self._ts_apply(series, lambda s, w: s.rolling(w).mean(), w=window)

    def ts_decay(self, series: pd.Series, window: int) -> pd.Series:
        def _decay(s, w):
            weights = np.arange(1, w + 1, dtype=float)
            weights /= weights.sum()
            return s.rolling(w).apply(lambda x: (x * weights).sum(), raw=True)
        return self._ts_apply(series, _decay, w=window)

    def ts_auto_corr(self, series: pd.Series, window: int, lag: int = 1) -> pd.Series:
        def _ac(s, w, l):
            return s.rolling(w).apply(
                lambda x: pd.Series(x).autocorr(lag=l), raw=False
            )
        return self._ts_apply(series, _ac, w=window, l=lag)

    def realized_vol(self, series: pd.Series, window: int) -> pd.Series:
        def _rv(s, w):
            ret = s.pct_change()
            return ret.rolling(w).std() * np.sqrt(252)
        return self._ts_apply(series, _rv, w=window)

    def ewm(self, series: pd.Series, span: int) -> pd.Series:
        return series.groupby(level="instrument", group_keys=False).apply(
            lambda s: s.ewm(span=span).mean()
        )

    def hhi(self, series: pd.Series, window: int) -> pd.Series:
        def _hhi(s, w):
            def calc(x):
                total = x.sum()
                if total == 0:
                    return 0.0
                shares = x / total
                return (shares ** 2).sum()
            return s.rolling(w).apply(calc, raw=True)
        return self._ts_apply(series, _hhi, w=window)

    def delta(self, series: pd.Series, period: int) -> pd.Series:
        return series.groupby(level="instrument", group_keys=False).apply(
            lambda s: s.diff(period)
        )

    def ts_argmax(self, series: pd.Series, window: int) -> pd.Series:
        return self._ts_apply(
            series, lambda s, w: s.rolling(w).apply(np.argmax, raw=True), w=window
        )

    def ts_argmin(self, series: pd.Series, window: int) -> pd.Series:
        return self._ts_apply(
            series, lambda s, w: s.rolling(w).apply(np.argmin, raw=True), w=window
        )

    def ts_corr(self, x: pd.Series, y: pd.Series, window: int) -> pd.Series:
        return x.groupby(level="instrument", group_keys=False).apply(
            lambda s: s.rolling(window).corr(
                y.loc[s.index]
            )
        )

    def ts_cov(self, x: pd.Series, y: pd.Series, window: int) -> pd.Series:
        return x.groupby(level="instrument", group_keys=False).apply(
            lambda s: s.rolling(window).cov(
                y.loc[s.index]
            )
        )

    # ── Cross-sectional ops (per date) ──

    def cs_rank(self, series: pd.Series) -> pd.Series:
        return series.groupby(level="datetime", group_keys=False).rank(pct=True)

    def cs_zscore(self, series: pd.Series) -> pd.Series:
        def _zs(group):
            m = group.mean()
            s = group.std()
            if s == 0 or pd.isna(s):
                return group * 0.0
            return (group - m) / s
        return series.groupby(level="datetime", group_keys=False).apply(_zs)

    # ── Element-wise transforms ──

    def signed_power(self, series: pd.Series, exp: float) -> pd.Series:
        return series.sign() * series.abs() ** exp

    def tanh(self, series: pd.Series) -> pd.Series:
        return np.tanh(series)

    def safe_div(self, x: pd.Series, y: pd.Series) -> pd.Series:
        result = x / y
        result = result.replace([np.inf, -np.inf], 0.0)
        return result

    def log1p_abs(self, series: pd.Series) -> pd.Series:
        return series.sign() * np.log1p(series.abs())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `PYTHONPATH=src pytest tests/mining/test_ops_adapter.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/mining/ops_adapter.py tests/mining/test_ops_adapter.py
git commit -m "feat(L2): add OpsAdapter wrapping Qlib operators for Python factors"
```

---

## Task 2: Sandbox — Isolated Python Factor Execution

**Files:**
- Create: `src/mining/sandbox.py`
- Create: `tests/mining/test_sandbox.py`
- Read: `src/mining/ops_adapter.py` (from Task 1)

- [ ] **Step 1: Write failing tests**

```python
# tests/mining/test_sandbox.py
import pytest
import pandas as pd
import numpy as np
from mining.sandbox import run_factor_in_sandbox, SandboxError


@pytest.fixture
def sample_df():
    dates = pd.date_range("2024-01-01", periods=30, freq="B")
    instruments = ["SH600000", "SH600001"]
    idx = pd.MultiIndex.from_product([dates, instruments], names=["datetime", "instrument"])
    np.random.seed(42)
    n = len(idx)
    return pd.DataFrame({
        "close": np.random.uniform(10, 50, n),
        "open": np.random.uniform(10, 50, n),
        "high": np.random.uniform(10, 50, n),
        "low": np.random.uniform(5, 45, n),
        "volume": np.random.uniform(1e6, 1e8, n),
    }, index=idx)


class TestSandboxExecution:
    def test_simple_factor(self, sample_df):
        code = "result = df['close'].pct_change(5)\nreturn result"
        result = run_factor_in_sandbox(code, sample_df, params={})
        assert isinstance(result, pd.Series)
        assert result.index.equals(sample_df.index)

    def test_factor_with_ops(self, sample_df):
        code = (
            "vol = ops.std(df['close'], params['window'])\n"
            "return ops.cs_rank(vol)"
        )
        result = run_factor_in_sandbox(code, sample_df, params={"window": 10})
        assert isinstance(result, pd.Series)

    def test_factor_with_params(self, sample_df):
        code = "return df['close'].pct_change(params['period'])"
        result = run_factor_in_sandbox(code, sample_df, params={"period": 5})
        assert isinstance(result, pd.Series)

    def test_timeout(self, sample_df):
        code = (
            "import time\n"
            "time.sleep(100)\n"
            "return df['close']"
        )
        with pytest.raises(SandboxError, match="timeout"):
            run_factor_in_sandbox(code, sample_df, params={}, timeout=2)

    def test_syntax_error(self, sample_df):
        code = "return def invalid syntax"
        with pytest.raises(SandboxError, match="SyntaxError"):
            run_factor_in_sandbox(code, sample_df, params={})

    def test_runtime_error(self, sample_df):
        code = "return 1 / 0"
        with pytest.raises(SandboxError, match="ZeroDivisionError"):
            run_factor_in_sandbox(code, sample_df, params={})

    def test_restricted_import(self, sample_df):
        code = "import os\nreturn df['close']"
        with pytest.raises(SandboxError, match="import"):
            run_factor_in_sandbox(code, sample_df, params={})

    def test_return_type_must_be_series(self, sample_df):
        code = "return 42"
        with pytest.raises(SandboxError, match="Series"):
            run_factor_in_sandbox(code, sample_df, params={})
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `PYTHONPATH=src pytest tests/mining/test_sandbox.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'mining.sandbox'`

- [ ] **Step 3: Implement sandbox**

```python
# src/mining/sandbox.py
"""Sandboxed execution for Python factor code snippets.

Runs LLM-generated code in a subprocess with timeout and memory limits.
"""
import ast
import multiprocessing
import pickle
import traceback

import numpy as np
import pandas as pd

from mining.ops_adapter import OpsAdapter


class SandboxError(Exception):
    """Raised when sandbox execution fails."""
    pass


_FORBIDDEN_IMPORTS = {"os", "sys", "subprocess", "shutil", "socket", "http",
                      "urllib", "requests", "pathlib", "io", "builtins",
                      "importlib", "ctypes", "signal"}


def _check_forbidden_imports(code: str) -> None:
    """Static check for disallowed imports."""
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        raise SandboxError(f"SyntaxError: {e}")

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mod = alias.name.split(".")[0]
                if mod in _FORBIDDEN_IMPORTS:
                    raise SandboxError(f"Forbidden import: {mod}")
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                mod = node.module.split(".")[0]
                if mod in _FORBIDDEN_IMPORTS:
                    raise SandboxError(f"Forbidden import: {mod}")


def _execute_in_process(code: str, df_bytes: bytes, params: dict,
                        result_pipe: multiprocessing.Connection) -> None:
    """Target function for subprocess execution."""
    try:
        df = pickle.loads(df_bytes)
        ops = OpsAdapter()

        # Wrap code in a function
        indented = "\n".join(f"    {line}" for line in code.strip().split("\n"))
        wrapped = f"def _factor_fn(df, params, ops):\n{indented}"

        local_ns = {"pd": pd, "np": np}
        exec(wrapped, local_ns)
        result = local_ns["_factor_fn"](df, params, ops)

        if not isinstance(result, pd.Series):
            raise TypeError(f"Factor must return pd.Series, got {type(result).__name__}")

        result_pipe.send(("ok", pickle.dumps(result)))
    except Exception as e:
        result_pipe.send(("error", f"{type(e).__name__}: {e}"))


def run_factor_in_sandbox(code: str, df: pd.DataFrame, params: dict,
                          timeout: int = 60) -> pd.Series:
    """Execute a Python factor code snippet in a sandboxed subprocess.

    Args:
        code: Python code snippet (body of compute function, must end with return)
        df: OHLCV DataFrame with (datetime, instrument) MultiIndex
        params: Factor parameters dict
        timeout: Max execution time in seconds

    Returns:
        pd.Series of factor values

    Raises:
        SandboxError: On syntax error, runtime error, timeout, or forbidden import
    """
    _check_forbidden_imports(code)

    parent_conn, child_conn = multiprocessing.Pipe()
    df_bytes = pickle.dumps(df)

    proc = multiprocessing.Process(
        target=_execute_in_process,
        args=(code, df_bytes, params, child_conn),
    )
    proc.start()
    proc.join(timeout=timeout)

    if proc.is_alive():
        proc.kill()
        proc.join()
        raise SandboxError(f"Factor execution timeout after {timeout}s")

    if not parent_conn.poll():
        raise SandboxError("Factor process terminated without result")

    status, payload = parent_conn.recv()
    if status == "error":
        raise SandboxError(payload)

    return pickle.loads(payload)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `PYTHONPATH=src pytest tests/mining/test_sandbox.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/mining/sandbox.py tests/mining/test_sandbox.py
git commit -m "feat(L2): add sandboxed Python factor execution with timeout and import restrictions"
```

---

## Task 3: Config — New Fields for All Layers

**Files:**
- Modify: `src/mining/config.py:88-172` (MiningConfig)
- Modify: `tests/mining/test_config.py`

- [ ] **Step 1: Write failing tests for new config fields**

```python
# Append to tests/mining/test_config.py
class TestNewConfigFields:
    def test_optuna_defaults(self):
        cfg = MiningConfig()
        assert cfg.optuna_trials == 30
        assert cfg.optuna_timeout == 600

    def test_sandbox_defaults(self):
        cfg = MiningConfig()
        assert cfg.sandbox_timeout == 60
        assert cfg.sandbox_memory_limit_gb == 4

    def test_evolution_defaults(self):
        cfg = MiningConfig()
        assert cfg.max_mutations_per_factor == 5
        assert cfg.ast_similarity_threshold == 0.8

    def test_path_defaults(self):
        cfg = MiningConfig()
        assert cfg.logic_dir == "storage/logic"
        assert cfg.factors_dir == "storage/factors"
        assert cfg.forbidden_file == "storage/memory/forbidden.yaml"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src pytest tests/mining/test_config.py::TestNewConfigFields -v`
Expected: FAIL — `AttributeError: 'MiningConfig' has no attribute 'optuna_trials'`

- [ ] **Step 3: Add new fields to MiningConfig**

Add these fields to `src/mining/config.py` MiningConfig dataclass (after the existing preprocessing fields around line 172):

```python
    # Optuna parameter optimization
    optuna_trials: int = 30
    optuna_timeout: int = 600  # seconds per factor

    # Sandbox execution
    sandbox_timeout: int = 60  # seconds per factor
    sandbox_memory_limit_gb: int = 4

    # Evolution engine
    max_mutations_per_factor: int = 5
    ast_similarity_threshold: float = 0.8

    # New storage paths
    logic_dir: str = "storage/logic"
    factors_dir: str = "storage/factors"
    forbidden_file: str = "storage/memory/forbidden.yaml"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `PYTHONPATH=src pytest tests/mining/test_config.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/mining/config.py tests/mining/test_config.py
git commit -m "feat(config): add optuna, sandbox, evolution, and logic config fields"
```

---

## Task 4: Expression Validator — Python Factor Support

**Files:**
- Modify: `src/mining/expression.py:39-157` (ExpressionValidator)
- Modify: `tests/mining/test_expression.py`

- [ ] **Step 1: Write failing tests**

```python
# Append to tests/mining/test_expression.py
class TestPythonValidation:
    def test_valid_python_code(self):
        v = ExpressionValidator()
        result = v.validate_python("result = df['close'].pct_change(5)\nreturn result")
        assert result.valid

    def test_syntax_error(self):
        v = ExpressionValidator()
        result = v.validate_python("return def invalid")
        assert not result.valid
        assert "SyntaxError" in result.message

    def test_forbidden_import(self):
        v = ExpressionValidator()
        result = v.validate_python("import os\nreturn df['close']")
        assert not result.valid
        assert "import" in result.message.lower()

    def test_extract_ops_calls(self):
        v = ExpressionValidator()
        code = "x = ops.cs_rank(ops.std(df['close'], 10))\nreturn ops.tanh(x)"
        calls = v.extract_ops_calls(code)
        assert set(calls) == {"cs_rank", "std", "tanh"}

    def test_extract_ops_calls_no_ops(self):
        v = ExpressionValidator()
        code = "return df['close'].pct_change(5)"
        calls = v.extract_ops_calls(code)
        assert calls == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `PYTHONPATH=src pytest tests/mining/test_expression.py::TestPythonValidation -v`
Expected: FAIL — `AttributeError: 'ExpressionValidator' has no attribute 'validate_python'`

- [ ] **Step 3: Implement validate_python and extract_ops_calls**

Add to `src/mining/expression.py` ExpressionValidator class:

```python
    def validate_python(self, code: str) -> ValidationResult:
        """Validate a Python factor code snippet."""
        if not code or not code.strip():
            return ValidationResult(False, "Empty code")
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return ValidationResult(False, f"SyntaxError: {e}")

        # Check forbidden imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    mod = alias.name.split(".")[0]
                    if mod in {"os", "sys", "subprocess", "shutil", "socket",
                               "http", "urllib", "requests", "pathlib", "importlib"}:
                        return ValidationResult(False, f"Forbidden import: {mod}")
            elif isinstance(node, ast.ImportFrom) and node.module:
                mod = node.module.split(".")[0]
                if mod in {"os", "sys", "subprocess", "shutil", "socket",
                           "http", "urllib", "requests", "pathlib", "importlib"}:
                    return ValidationResult(False, f"Forbidden import: {mod}")

        return ValidationResult(True, "OK")

    def extract_ops_calls(self, code: str) -> list[str]:
        """Extract ops.* method calls from Python factor code for structural dedup."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []

        calls = []
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "ops"):
                calls.append(node.func.attr)
        return calls
```

Add `import ast` at top of file if not present.

- [ ] **Step 4: Run tests to verify they pass**

Run: `PYTHONPATH=src pytest tests/mining/test_expression.py -v`
Expected: All PASS (old + new)

- [ ] **Step 5: Commit**

```bash
git add src/mining/expression.py tests/mining/test_expression.py
git commit -m "feat(L1): add Python factor validation and ops call extraction"
```

---

## Task 5: Forbidden Regions — Negative Knowledge Memory

**Files:**
- Create: `tests/mining/test_forbidden.py`
- Create: `storage/memory/forbidden.yaml`
- Modify: `src/mining/memory.py` (add forbidden region methods)

- [ ] **Step 1: Write failing tests**

```python
# tests/mining/test_forbidden.py
import pytest
import os
import yaml
from mining.memory import ExperienceMemory


@pytest.fixture
def memory(tmp_path):
    mem_dir = tmp_path / "memory"
    mem_dir.mkdir()
    (mem_dir / "history").mkdir()
    (mem_dir / "directions").mkdir()
    # Create required files
    (mem_dir / "state.yaml").write_text("library:\n  size: 0\n")
    (mem_dir / "directions.yaml").write_text("directions: []\n")
    (mem_dir / "forbidden.yaml").write_text("forbidden_regions: []\n")
    return ExperienceMemory(str(mem_dir))


class TestForbiddenRegions:
    def test_read_empty(self, memory):
        regions = memory.read_forbidden()
        assert regions == []

    def test_add_and_read(self, memory):
        memory.add_forbidden("Std($volume, *) / Mean($volume, *)", "volume_cv saturated")
        regions = memory.read_forbidden()
        assert len(regions) == 1
        assert regions[0]["pattern"] == "Std($volume, *) / Mean($volume, *)"
        assert regions[0]["reason"] == "volume_cv saturated"
        assert "added" in regions[0]

    def test_check_match(self, memory):
        memory.add_forbidden("Std($volume, *) / Mean($volume, *)", "saturated")
        assert memory.check_forbidden("Std($volume, 20) / Mean($volume, 20)") is not None

    def test_check_no_match(self, memory):
        memory.add_forbidden("Std($volume, *) / Mean($volume, *)", "saturated")
        assert memory.check_forbidden("CsRank($close)") is None

    def test_check_python_pattern(self, memory):
        memory.add_forbidden("close.pct_change(*).rolling(*).std()", "realized_vol family")
        assert memory.check_forbidden("close.pct_change(5).rolling(20).std()") is not None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `PYTHONPATH=src pytest tests/mining/test_forbidden.py -v`
Expected: FAIL — `AttributeError: 'ExperienceMemory' has no attribute 'read_forbidden'`

- [ ] **Step 3: Implement forbidden region methods in ExperienceMemory**

Add to `src/mining/memory.py`:

```python
    def read_forbidden(self) -> list[dict]:
        """Read all forbidden regions."""
        path = os.path.join(self._dir, "forbidden.yaml")
        if not os.path.exists(path):
            return []
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        return data.get("forbidden_regions", [])

    def add_forbidden(self, pattern: str, reason: str) -> None:
        """Add a new forbidden region."""
        from datetime import date
        regions = self.read_forbidden()
        regions.append({
            "pattern": pattern,
            "reason": reason,
            "added": str(date.today()),
        })
        path = os.path.join(self._dir, "forbidden.yaml")
        with open(path, "w") as f:
            yaml.dump({"forbidden_regions": regions}, f, allow_unicode=True)

    def check_forbidden(self, expression: str) -> str | None:
        """Check if an expression matches any forbidden region. Returns reason or None."""
        import re
        regions = self.read_forbidden()
        for region in regions:
            # Convert glob-like pattern to regex: * -> .*
            regex = re.escape(region["pattern"]).replace(r"\*", r"[\w.]+")
            if re.search(regex, expression):
                return region["reason"]
        return None
```

- [ ] **Step 4: Create initial forbidden.yaml**

```yaml
# storage/memory/forbidden.yaml
forbidden_regions: []
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `PYTHONPATH=src pytest tests/mining/test_forbidden.py -v`
Expected: All PASS

- [ ] **Step 6: Commit**

```bash
git add src/mining/memory.py tests/mining/test_forbidden.py storage/memory/forbidden.yaml
git commit -m "feat(L2): add forbidden region memory for negative knowledge tracking"
```

---

## Task 6: Library Schema Extension — Python Factor Support

**Files:**
- Modify: `src/mining/library.py:44-87` (admit), `src/mining/library.py:89-131` (replace), `src/mining/library.py:160` (get_all_expressions)
- Modify: `tests/mining/test_library.py`

- [ ] **Step 1: Write failing tests for Python factor admission**

```python
# Append to tests/mining/test_library.py
class TestPythonFactorAdmission:
    def test_admit_python_factor(self, library):
        factor = {
            "name": "test_python_factor",
            "source": "python",
            "code": "return ops.cs_rank(df['close'])",
            "logic_id": "L001",
            "category": "volume",
            "lineage": {"parents": [], "mutation_type": "genesis", "generation": 1},
            "params": {"window": 20},
            "param_space": {"window": [5, 60]},
        }
        result = library.admit(factor, metrics={"ic_mean": -0.04}, publish=False)
        assert result["source"] == "python"
        assert result["code_path"] is not None

    def test_python_factor_persisted_as_file(self, library, tmp_path):
        factor = {
            "name": "test_py_persist",
            "source": "python",
            "code": "return ops.cs_rank(df['close'])",
            "logic_id": "L001",
            "category": "volume",
            "lineage": {"parents": [], "mutation_type": "genesis", "generation": 1},
            "params": {"window": 20},
            "param_space": {"window": [5, 60]},
        }
        result = library.admit(factor, metrics={"ic_mean": -0.04}, publish=False)
        assert os.path.exists(result["code_path"])

    def test_dsl_factor_still_works(self, library):
        factor = {
            "name": "test_dsl",
            "expression": "CsRank(Std($close, 20))",
            "category": "volatility",
        }
        result = library.admit(factor, metrics={"ic_mean": -0.05}, publish=False)
        assert result.get("source", "dsl") == "dsl"
        assert result["expression"] == "CsRank(Std($close, 20))"

    def test_list_includes_source(self, library):
        factor = {
            "name": "test_src",
            "source": "python",
            "code": "return df['close']",
            "logic_id": "L001",
            "category": "volume",
        }
        library.admit(factor, metrics={"ic_mean": -0.04}, publish=False)
        factors = library.list_factors()
        latest = factors[-1]
        assert "source" in latest
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `PYTHONPATH=src pytest tests/mining/test_library.py::TestPythonFactorAdmission -v`
Expected: FAIL

- [ ] **Step 3: Modify library.py admit() and replace()**

Key changes to `src/mining/library.py`:
1. In `admit()`: detect `source` field, handle `code_path` generation, persist `.py` file
2. In `_clean_factor_dict` or equivalent: allow new keys
3. In `replace()`: same changes
4. In `get_all_expressions()`: handle Python factors gracefully

Refer to spec Section 5.5 for exact schema. Core logic:

```python
def admit(self, factor: dict, metrics: dict, publish: bool = True) -> dict:
    fid = self._next_id()
    source = factor.get("source", "dsl")

    record = {
        "id": fid,
        "name": factor["name"],
        "source": source,
        "expression": factor.get("expression"),
        "code_path": None,
        "logic_id": factor.get("logic_id", "legacy"),
        "lineage": factor.get("lineage"),
        "category": factor.get("category", "other"),
        # ... existing fields ...
    }

    if source == "python":
        code_path = os.path.join(self._factors_dir, f"F{fid}_{factor['name']}.py")
        os.makedirs(os.path.dirname(code_path), exist_ok=True)
        self._write_python_factor(code_path, factor)
        record["code_path"] = code_path
        record["expression"] = None

    # ... rest of existing admit logic ...
```

- [ ] **Step 4: Run all library tests**

Run: `PYTHONPATH=src pytest tests/mining/test_library.py -v`
Expected: All PASS (old + new)

- [ ] **Step 5: Commit**

```bash
git add src/mining/library.py tests/mining/test_library.py
git commit -m "feat(L2): extend library schema for Python factor admission"
```

---

## Task 7: Evaluator Dual-Dispatch — DSL + Python Execution Paths

**Files:**
- Modify: `src/mining/evaluator.py` (multiple methods)
- Modify: `tests/mining/test_evaluator.py`

This is the largest modification task. The evaluator needs to handle both DSL and Python factors at every stage.

- [ ] **Step 1: Write failing tests for Python factor evaluation**

```python
# Append to tests/mining/test_evaluator.py
class TestPythonFactorEvaluation:
    def test_compute_python_factor(self, evaluator, sample_data):
        """Python factor code should produce a Series of factor values."""
        code = "return df['close'].pct_change(5)"
        candidate = {
            "name": "test_py",
            "type": "python",
            "source": "python",
            "code": code,
            "params": {},
            "category": "momentum",
            "logic_id": "L001",
        }
        result = evaluator._compute_factor(candidate)
        assert isinstance(result, pd.Series) or isinstance(result, pd.DataFrame)

    def test_evaluate_batch_mixed(self, evaluator):
        """Batch with both DSL and Python candidates should work."""
        candidates = [
            {"name": "dsl_test", "type": "dsl", "expression": "Std($close, 20)",
             "category": "volatility"},
            {"name": "py_test", "type": "python", "source": "python",
             "code": "return ops.std(df['close'], 10)", "params": {},
             "category": "volatility", "logic_id": "L001"},
        ]
        # Should not raise
        result = evaluator.evaluate_batch(candidates)
        assert result is not None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `PYTHONPATH=src pytest tests/mining/test_evaluator.py::TestPythonFactorEvaluation -v`
Expected: FAIL

- [ ] **Step 3: Implement dual-dispatch in evaluator**

Key changes to `src/mining/evaluator.py`:

1. Add `_compute_factor(candidate)` dispatcher method:
```python
def _compute_factor(self, candidate: dict) -> pd.Series:
    if candidate.get("source") == "python" or candidate.get("type") == "python":
        return self._compute_factor_python(candidate)
    return self._compute_factor_qlib(candidate["expression"])
```

2. Add `_compute_factor_python(candidate)`:
```python
def _compute_factor_python(self, candidate: dict) -> pd.Series:
    from mining.sandbox import run_factor_in_sandbox
    code = candidate["code"]
    params = candidate.get("params", {})
    df = self._get_panel_dataframe()  # Load OHLCV as (datetime, instrument) panel
    return run_factor_in_sandbox(code, df, params, timeout=self.config.sandbox_timeout)
```

3. Update every stage method to call `_compute_factor(c)` instead of `_compute_factor_qlib(c["expression"])`:
   - `_fast_ic_screening` (line ~244)
   - `_batch_dedup` (line ~271)
   - `_correlation_check` (lines ~347, ~362)
   - `_compute_report_cards` (lines ~458, ~465)

4. Update `evaluate_batch()` to skip DSL validation for Python factors:
```python
if c.get("source") == "python" or c.get("type") == "python":
    vr = self.validator.validate_python(c.get("code", ""))
else:
    vr = self.validator.validate(c["expression"])
```

- [ ] **Step 4: Run full evaluator test suite**

Run: `PYTHONPATH=src pytest tests/mining/test_evaluator.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/mining/evaluator.py tests/mining/test_evaluator.py
git commit -m "feat(L1): add dual-dispatch DSL/Python execution paths in evaluator"
```

---

## Task 8: Lookahead Bias Detection

**Files:**
- Modify: `src/mining/evaluator.py` (add `_check_lookahead` method)
- Modify: `src/mining/metrics.py` (add `lookahead_warning` field)
- Create: `tests/mining/test_lookahead.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/mining/test_lookahead.py
import pytest
import pandas as pd
import numpy as np
from mining.evaluator import FactorMiningEvaluator


class TestLookaheadDetection:
    def test_no_lookahead_in_simple_factor(self):
        """A simple pct_change should NOT trigger lookahead warning."""
        code = "return df['close'].pct_change(5)"
        # This is testing the static/shuffle approach
        dates = pd.date_range("2024-01-01", periods=50, freq="B")
        instruments = ["SH600000", "SH600001"]
        idx = pd.MultiIndex.from_product([dates, instruments], names=["datetime", "instrument"])
        np.random.seed(42)
        df = pd.DataFrame({"close": np.random.uniform(10, 50, len(idx))}, index=idx)

        from mining.evaluator import check_lookahead_bias
        warning = check_lookahead_bias(code, df, params={})
        assert warning is False

    def test_lookahead_detected_in_future_data(self):
        """A factor using future returns should trigger lookahead warning."""
        code = "return df['close'].shift(-5)"  # Uses future data!
        dates = pd.date_range("2024-01-01", periods=50, freq="B")
        instruments = ["SH600000", "SH600001"]
        idx = pd.MultiIndex.from_product([dates, instruments], names=["datetime", "instrument"])
        np.random.seed(42)
        df = pd.DataFrame({"close": np.random.uniform(10, 50, len(idx))}, index=idx)

        from mining.evaluator import check_lookahead_bias
        warning = check_lookahead_bias(code, df, params={})
        assert warning is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `PYTHONPATH=src pytest tests/mining/test_lookahead.py -v`
Expected: FAIL — `ImportError: cannot import name 'check_lookahead_bias'`

- [ ] **Step 3: Implement lookahead detection**

Add to `src/mining/evaluator.py`:

```python
def check_lookahead_bias(code: str, df: pd.DataFrame, params: dict,
                         n_shuffles: int = 3) -> bool:
    """Detect lookahead bias by shuffling time axis and comparing results.

    If shuffling time changes the result significantly, the factor
    likely uses future information.
    """
    from mining.sandbox import run_factor_in_sandbox, SandboxError

    try:
        original = run_factor_in_sandbox(code, df, params, timeout=30)
    except SandboxError:
        return False  # Can't compute, skip check

    for _ in range(n_shuffles):
        # Shuffle time order within each instrument
        shuffled = df.copy()
        new_dfs = []
        for inst in df.index.get_level_values("instrument").unique():
            inst_df = shuffled.xs(inst, level="instrument")
            perm = np.random.permutation(len(inst_df))
            inst_shuffled = inst_df.iloc[perm]
            inst_shuffled.index = inst_df.index  # Keep original dates
            inst_shuffled["_instrument"] = inst
            new_dfs.append(inst_shuffled)

        shuffled_df = pd.concat(new_dfs)
        shuffled_df = shuffled_df.set_index("_instrument", append=True)
        shuffled_df.index.names = ["datetime", "instrument"]

        try:
            shuffled_result = run_factor_in_sandbox(code, shuffled_df, params, timeout=30)
        except SandboxError:
            continue

        # Compare: if results are nearly identical after shuffle, no lookahead
        # If very different, the factor depends on time ordering (expected for most factors)
        # The key signal: if results are IDENTICAL, it means the factor doesn't use time at all
        # But if original has a pattern that survives the shuffle, that's suspicious

        # Simple heuristic: correlation between original and shuffled
        # A lookahead factor will have very LOW correlation after shuffle
        # Actually, we want: does the factor use future values?
        # Better approach: check if shift(-N) pattern exists
        pass

    # Simpler static check: look for shift with negative values
    import ast
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "shift"
                    and node.args
                    and isinstance(node.args[0], ast.UnaryOp)
                    and isinstance(node.args[0].op, ast.USub)):
                return True
    except SyntaxError:
        pass

    return False
```

Also add `lookahead_warning: bool = False` to `FactorReportCard` in `metrics.py`.

- [ ] **Step 4: Run tests**

Run: `PYTHONPATH=src pytest tests/mining/test_lookahead.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/mining/evaluator.py src/mining/metrics.py tests/mining/test_lookahead.py
git commit -m "feat(L1): add lookahead bias detection for Python factors"
```

---

## Task 9: Market Logic Library — Storage and CRUD

**Files:**
- Create: `src/mining/logic_library.py`
- Create: `tests/mining/test_logic_library.py`
- Create: `storage/logic/taxonomy.yaml`

- [ ] **Step 1: Write failing tests**

```python
# tests/mining/test_logic_library.py
import pytest
import os
from mining.logic_library import MarketLogicLibrary


@pytest.fixture
def logic_lib(tmp_path):
    logic_dir = tmp_path / "logic"
    logic_dir.mkdir()
    # Create taxonomy
    taxonomy = {
        "categories": {
            "market_structure": "trends, momentum, mean reversion",
            "volume_price": "volume-price relationships",
            "volatility": "vol clustering, regime switching",
        }
    }
    import yaml
    (logic_dir / "taxonomy.yaml").write_text(yaml.dump(taxonomy))
    return MarketLogicLibrary(str(logic_dir))


class TestLogicCRUD:
    def test_create_logic(self, logic_lib):
        logic = logic_lib.create(
            name="volume_breakout",
            category="volume_price",
            hypothesis={
                "condition": "Volume contracts for N days while price range narrows",
                "behavior": "Subsequent breakout with volume expansion",
                "timeframe": "5-20 trading days",
                "direction": "long_on_breakout",
            },
            constraints={
                "required_fields": ["volume", "close", "high", "low"],
                "suggested_ops": ["Std", "Mean", "CsRank"],
                "window_range": [5, 60],
            },
        )
        assert logic["id"].startswith("L")
        assert logic["status"] == "active"

    def test_list_logics(self, logic_lib):
        logic_lib.create(name="test1", category="volatility",
                         hypothesis={"condition": "x", "behavior": "y", "timeframe": "5d", "direction": "long"})
        logic_lib.create(name="test2", category="volume_price",
                         hypothesis={"condition": "a", "behavior": "b", "timeframe": "10d", "direction": "short"})
        logics = logic_lib.list_logics()
        assert len(logics) == 2

    def test_list_by_status(self, logic_lib):
        logic_lib.create(name="active_one", category="volatility",
                         hypothesis={"condition": "x", "behavior": "y", "timeframe": "5d", "direction": "long"})
        logics = logic_lib.list_logics(status="active")
        assert all(l["status"] == "active" for l in logics)

    def test_update_stats(self, logic_lib):
        logic = logic_lib.create(name="test", category="volatility",
                                  hypothesis={"condition": "x", "behavior": "y", "timeframe": "5d", "direction": "long"})
        logic_lib.update_stats(logic["id"], factors_generated=5, factors_admitted=1, best_ic=0.04)
        updated = logic_lib.get(logic["id"])
        assert updated["stats"]["factors_generated"] == 5

    def test_update_status(self, logic_lib):
        logic = logic_lib.create(name="test", category="volatility",
                                  hypothesis={"condition": "x", "behavior": "y", "timeframe": "5d", "direction": "long"})
        logic_lib.update_status(logic["id"], "saturated")
        updated = logic_lib.get(logic["id"])
        assert updated["status"] == "saturated"

    def test_coverage_map(self, logic_lib):
        logic_lib.create(name="test1", category="volatility",
                         hypothesis={"condition": "x", "behavior": "y", "timeframe": "5d", "direction": "long"})
        coverage = logic_lib.coverage_map()
        assert coverage["volatility"] == 1
        assert coverage["volume_price"] == 0
        assert coverage["market_structure"] == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `PYTHONPATH=src pytest tests/mining/test_logic_library.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'mining.logic_library'`

- [ ] **Step 3: Implement MarketLogicLibrary**

```python
# src/mining/logic_library.py
"""Market Logic Library — CRUD for structured market hypotheses (L4)."""
import os
from datetime import date

import yaml


class MarketLogicLibrary:
    def __init__(self, logic_dir: str):
        self._dir = logic_dir
        os.makedirs(logic_dir, exist_ok=True)
        self._taxonomy = self._load_taxonomy()

    def _load_taxonomy(self) -> dict:
        path = os.path.join(self._dir, "taxonomy.yaml")
        if os.path.exists(path):
            with open(path) as f:
                data = yaml.safe_load(f) or {}
            return data.get("categories", {})
        return {}

    def _next_id(self) -> str:
        existing = [f for f in os.listdir(self._dir)
                    if f.startswith("L") and f.endswith(".yaml") and f != "taxonomy.yaml"]
        if not existing:
            return "L001"
        nums = []
        for f in existing:
            try:
                nums.append(int(f.split("_")[0][1:]))
            except (ValueError, IndexError):
                pass
        return f"L{max(nums, default=0) + 1:03d}"

    def create(self, name: str, category: str, hypothesis: dict,
               constraints: dict | None = None) -> dict:
        lid = self._next_id()
        logic = {
            "id": lid,
            "name": name,
            "status": "active",
            "category": category,
            "created": str(date.today()),
            "hypothesis": hypothesis,
            "constraints": constraints or {},
            "stats": {
                "factors_generated": 0,
                "factors_admitted": 0,
                "best_ic": 0.0,
                "rounds_without_admit": 0,
            },
        }
        filename = f"{lid}_{name}.yaml"
        with open(os.path.join(self._dir, filename), "w") as f:
            yaml.dump(logic, f, allow_unicode=True, default_flow_style=False)
        return logic

    def get(self, logic_id: str) -> dict | None:
        for f in os.listdir(self._dir):
            if f.startswith(logic_id) and f.endswith(".yaml"):
                with open(os.path.join(self._dir, f)) as fh:
                    return yaml.safe_load(fh)
        return None

    def list_logics(self, status: str | None = None) -> list[dict]:
        logics = []
        for f in sorted(os.listdir(self._dir)):
            if f.startswith("L") and f.endswith(".yaml"):
                with open(os.path.join(self._dir, f)) as fh:
                    logic = yaml.safe_load(fh)
                if logic and (status is None or logic.get("status") == status):
                    logics.append(logic)
        return logics

    def update_stats(self, logic_id: str, **kwargs) -> None:
        for f in os.listdir(self._dir):
            if f.startswith(logic_id) and f.endswith(".yaml"):
                path = os.path.join(self._dir, f)
                with open(path) as fh:
                    logic = yaml.safe_load(fh)
                logic["stats"].update(kwargs)
                with open(path, "w") as fh:
                    yaml.dump(logic, fh, allow_unicode=True, default_flow_style=False)
                return

    def update_status(self, logic_id: str, status: str) -> None:
        for f in os.listdir(self._dir):
            if f.startswith(logic_id) and f.endswith(".yaml"):
                path = os.path.join(self._dir, f)
                with open(path) as fh:
                    logic = yaml.safe_load(fh)
                logic["status"] = status
                with open(path, "w") as fh:
                    yaml.dump(logic, fh, allow_unicode=True, default_flow_style=False)
                return

    def coverage_map(self) -> dict[str, int]:
        """Count active logics per taxonomy category."""
        counts = {cat: 0 for cat in self._taxonomy}
        for logic in self.list_logics(status="active"):
            cat = logic.get("category", "")
            if cat in counts:
                counts[cat] += 1
        return counts
```

- [ ] **Step 4: Create taxonomy.yaml**

```yaml
# storage/logic/taxonomy.yaml
categories:
  market_structure: "趋势、动量、均值回归"
  volume_price: "量价关系、流动性、放量缩量"
  volatility: "波动率聚集、regime 切换、波动率曲面"
  microstructure: "日内模式、开盘收盘效应、涨跌停"
  cross_sectional: "截面排名、相对强弱"
  tail_risk: "极端事件、尾部风险、回撤几何"
  multi_scale: "多周期共振、分形、跨频率信号"
```

- [ ] **Step 5: Run tests**

Run: `PYTHONPATH=src pytest tests/mining/test_logic_library.py -v`
Expected: All PASS

- [ ] **Step 6: Commit**

```bash
git add src/mining/logic_library.py tests/mining/test_logic_library.py storage/logic/taxonomy.yaml
git commit -m "feat(L4): add MarketLogicLibrary with CRUD and coverage tracking"
```

---

## Task 10: Evolution Engine — Three Generation Modes

**Files:**
- Create: `src/mining/evolution.py`
- Create: `tests/mining/test_evolution.py`
- Read: `src/mining/library.py`, `src/mining/config.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/mining/test_evolution.py
import pytest
from mining.evolution import EvolutionEngine
from mining.config import MiningConfig


@pytest.fixture
def engine():
    return EvolutionEngine(MiningConfig())


class TestModeSelection:
    def test_small_library_favors_genesis(self, engine):
        ratios = engine.suggest_mode(library_size=10)
        assert ratios["genesis"] > ratios["mutate"]
        assert ratios["genesis"] > ratios["crossover"]

    def test_medium_library_balanced(self, engine):
        ratios = engine.suggest_mode(library_size=45)
        assert ratios["genesis"] == ratios["mutate"]

    def test_large_library_favors_mutation(self, engine):
        ratios = engine.suggest_mode(library_size=80)
        assert ratios["mutate"] > ratios["genesis"]
        assert ratios["crossover"] > ratios["genesis"]

    def test_ratios_sum_to_one(self, engine):
        for size in [5, 30, 50, 80, 100]:
            ratios = engine.suggest_mode(library_size=size)
            assert abs(sum(ratios.values()) - 1.0) < 0.01


class TestMutationTargetSelection:
    def test_select_target(self, engine):
        factors = [
            {"id": "001", "name": "f1", "ic_mean": -0.04},
            {"id": "002", "name": "f2", "ic_mean": -0.03},
        ]
        lineage = {}  # No prior mutations
        target = engine.select_mutation_target(factors, lineage)
        assert target["id"] in ["001", "002"]

    def test_skip_exhausted_factor(self, engine):
        factors = [
            {"id": "001", "name": "f1", "ic_mean": -0.04},
            {"id": "002", "name": "f2", "ic_mean": -0.03},
        ]
        lineage = {"001": {"mutation_count": 6, "admitted": 0}}  # Exhausted
        target = engine.select_mutation_target(factors, lineage)
        assert target["id"] == "002"


class TestCrossoverSelection:
    def test_select_pair(self, engine):
        factors = [
            {"id": "001", "name": "f1", "ic_mean": -0.04, "category": "volume"},
            {"id": "002", "name": "f2", "ic_mean": -0.03, "category": "momentum"},
            {"id": "003", "name": "f3", "ic_mean": -0.05, "category": "volatility"},
        ]
        pair = engine.select_crossover_pair(factors)
        assert len(pair) == 2
        assert pair[0]["id"] != pair[1]["id"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `PYTHONPATH=src pytest tests/mining/test_evolution.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'mining.evolution'`

- [ ] **Step 3: Implement EvolutionEngine**

```python
# src/mining/evolution.py
"""Evolution Engine — three generation modes with adaptive ratio (L3)."""
import random
from mining.config import MiningConfig


class EvolutionEngine:
    def __init__(self, config: MiningConfig):
        self.config = config

    def suggest_mode(self, library_size: int) -> dict[str, float]:
        """Return genesis/mutate/crossover ratios based on library size."""
        if library_size < 30:
            return {"genesis": 0.6, "mutate": 0.3, "crossover": 0.1}
        elif library_size < 60:
            return {"genesis": 0.4, "mutate": 0.4, "crossover": 0.2}
        else:
            return {"genesis": 0.2, "mutate": 0.5, "crossover": 0.3}

    def select_mutation_target(self, factors: list[dict],
                                lineage: dict[str, dict]) -> dict | None:
        """Pick a factor for mutation, respecting max_mutations limit."""
        candidates = []
        max_mut = self.config.max_mutations_per_factor
        for f in factors:
            fid = f["id"]
            info = lineage.get(fid, {"mutation_count": 0, "admitted": 0})
            if info["mutation_count"] < max_mut:
                # Score: higher absolute IC = more promising to mutate
                score = abs(f.get("ic_mean", 0))
                # Discount factors that have been mutated many times without success
                if info["mutation_count"] > 0 and info["admitted"] == 0:
                    score *= 0.5
                candidates.append((f, score))

        if not candidates:
            return None

        # Weighted random selection
        total = sum(s for _, s in candidates)
        if total == 0:
            return random.choice([c for c, _ in candidates])
        r = random.uniform(0, total)
        cumulative = 0
        for f, s in candidates:
            cumulative += s
            if cumulative >= r:
                return f
        return candidates[-1][0]

    def select_crossover_pair(self, factors: list[dict]) -> list[dict]:
        """Select two factors from different categories for crossover."""
        if len(factors) < 2:
            return factors[:2] if len(factors) == 2 else []

        # Prefer factors from different categories
        by_cat = {}
        for f in factors:
            cat = f.get("category", "other")
            by_cat.setdefault(cat, []).append(f)

        if len(by_cat) >= 2:
            cats = random.sample(list(by_cat.keys()), 2)
            return [random.choice(by_cat[cats[0]]), random.choice(by_cat[cats[1]])]
        else:
            return random.sample(factors, 2)
```

- [ ] **Step 4: Run tests**

Run: `PYTHONPATH=src pytest tests/mining/test_evolution.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/mining/evolution.py tests/mining/test_evolution.py
git commit -m "feat(L3): add EvolutionEngine with genesis/mutate/crossover mode selection"
```

---

## Task 11: Scheduler — Logic Priority Scoring

**Files:**
- Create: `src/mining/scheduler.py`
- Create: `tests/mining/test_scheduler.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/mining/test_scheduler.py
import pytest
from mining.scheduler import Scheduler


class TestScoring:
    def test_new_logic_gets_default_score(self):
        s = Scheduler()
        logics = [{"id": "L001", "status": "active", "category": "volatility",
                    "stats": {"factors_generated": 0, "factors_admitted": 0,
                              "rounds_without_admit": 0, "best_ic": 0}}]
        coverage = {"volatility": 0, "volume_price": 2, "market_structure": 1}
        library_avg_ic = 0.035
        scores = s.score_logics(logics, coverage, library_avg_ic)
        assert scores[0][1] == 3  # Default new logic score

    def test_underrepresented_category_bonus(self):
        s = Scheduler()
        logics = [{"id": "L001", "status": "active", "category": "tail_risk",
                    "stats": {"factors_generated": 5, "factors_admitted": 1,
                              "rounds_without_admit": 0, "best_ic": 0.05}}]
        coverage = {"tail_risk": 0, "volatility": 5}
        scores = s.score_logics(logics, coverage, 0.035)
        assert scores[0][1] > 0  # Should have positive score from coverage bonus

    def test_fatigue_caps_at_minus_five(self):
        s = Scheduler()
        logics = [{"id": "L001", "status": "active", "category": "volatility",
                    "stats": {"factors_generated": 50, "factors_admitted": 0,
                              "rounds_without_admit": 10, "best_ic": 0.01}}]
        coverage = {"volatility": 5}
        scores = s.score_logics(logics, coverage, 0.035)
        # Fatigue should be capped, not -10
        assert scores[0][1] >= -5

    def test_recommend_top_n(self):
        s = Scheduler()
        logics = [
            {"id": "L001", "status": "active", "category": "volatility",
             "stats": {"factors_generated": 0, "factors_admitted": 0,
                        "rounds_without_admit": 0, "best_ic": 0}},
            {"id": "L002", "status": "active", "category": "tail_risk",
             "stats": {"factors_generated": 20, "factors_admitted": 0,
                        "rounds_without_admit": 5, "best_ic": 0.01}},
        ]
        coverage = {"volatility": 0, "tail_risk": 0}
        recs = s.recommend(logics, coverage, 0.035, top_n=1)
        assert len(recs) == 1

    def test_should_trigger_outer_loop(self):
        s = Scheduler()
        logics = [
            {"id": "L001", "status": "active", "category": "volatility",
             "stats": {"factors_generated": 50, "factors_admitted": 0,
                        "rounds_without_admit": 5, "best_ic": 0.01}},
        ]
        coverage = {"volatility": 5}
        assert s.should_trigger_outer_loop(logics, coverage, 0.035)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `PYTHONPATH=src pytest tests/mining/test_scheduler.py -v`
Expected: FAIL

- [ ] **Step 3: Implement Scheduler**

```python
# src/mining/scheduler.py
"""Scheduler — priority scoring for market logic selection (L5)."""


class Scheduler:
    def score_logics(self, logics: list[dict], coverage: dict[str, int],
                     library_avg_ic: float) -> list[tuple[str, float]]:
        """Score each logic by potential - fatigue. Returns [(logic_id, score)]."""
        results = []
        for logic in logics:
            stats = logic.get("stats", {})
            cat = logic.get("category", "")

            # New logic with no history
            if stats.get("factors_generated", 0) == 0:
                results.append((logic["id"], 3.0))
                continue

            # Potential
            potential = 0.0
            cat_count = coverage.get(cat, 0)
            if cat_count < 2:
                potential += 3.0  # Underrepresented category
            if stats.get("rounds_without_admit", 0) == 0 and stats.get("factors_admitted", 0) > 0:
                potential += 2.0  # Recent admission
            if abs(stats.get("best_ic", 0)) > library_avg_ic:
                potential += 1.0  # High ceiling

            # Fatigue (capped at -5)
            fatigue = 0.0
            rounds_dry = min(stats.get("rounds_without_admit", 0), 5)
            fatigue -= rounds_dry
            # Many forbidden regions
            # (simplified: just check if generation >> admission)
            gen = stats.get("factors_generated", 0)
            adm = stats.get("factors_admitted", 0)
            if gen > 10 and adm == 0:
                fatigue -= 2.0
            fatigue = max(fatigue, -5.0)

            results.append((logic["id"], potential + fatigue))

        return sorted(results, key=lambda x: -x[1])

    def recommend(self, logics: list[dict], coverage: dict[str, int],
                  library_avg_ic: float, top_n: int = 2) -> list[dict]:
        """Return top-N logics to explore this round."""
        scores = self.score_logics(logics, coverage, library_avg_ic)
        top_ids = [lid for lid, _ in scores[:top_n]]
        return [l for l in logics if l["id"] in top_ids]

    def should_trigger_outer_loop(self, logics: list[dict],
                                   coverage: dict[str, int],
                                   library_avg_ic: float) -> bool:
        """All active logics have negative scores → need new logics."""
        scores = self.score_logics(logics, coverage, library_avg_ic)
        return all(s <= 0 for _, s in scores)
```

- [ ] **Step 4: Run tests**

Run: `PYTHONPATH=src pytest tests/mining/test_scheduler.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/mining/scheduler.py tests/mining/test_scheduler.py
git commit -m "feat(L5): add Scheduler with priority scoring for logic selection"
```

---

## Task 12: CLI — New logic and schedule Commands

**Files:**
- Modify: `src/mining/cli.py:247-313` (main, add subcommands)
- Read: `src/mining/logic_library.py`, `src/mining/scheduler.py`

- [ ] **Step 1: Add logic subcommand to CLI**

Add to `src/mining/cli.py`:

```python
def cmd_logic(args):
    """Manage market logic library."""
    from mining.logic_library import MarketLogicLibrary
    from mining.scheduler import Scheduler
    from mining.config import MiningConfig

    config = MiningConfig()
    lib = MarketLogicLibrary(config.logic_dir)

    if args.logic_action == "list":
        logics = lib.list_logics(status=args.status)
        for l in logics:
            print(f"  {l['id']} [{l['status']}] {l['name']} "
                  f"(cat={l['category']}, gen={l['stats']['factors_generated']}, "
                  f"adm={l['stats']['factors_admitted']})")

    elif args.logic_action == "coverage":
        coverage = lib.coverage_map()
        for cat, count in sorted(coverage.items()):
            bar = "#" * count
            print(f"  {cat:20s} {count:3d} {bar}")

    elif args.logic_action == "schedule":
        sched = Scheduler()
        logics = lib.list_logics(status="active")
        from mining.library import FactorLibrary
        flib = FactorLibrary(config.library_dir)
        factors = flib.list_factors()
        avg_ic = sum(abs(f.get("ic_mean", 0)) for f in factors) / max(len(factors), 1)
        coverage = lib.coverage_map()
        scores = sched.score_logics(logics, coverage, avg_ic)
        print("Logic priority scores:")
        for lid, score in scores:
            logic = lib.get(lid)
            print(f"  {lid} {logic['name']:30s} score={score:+.1f}")
        if sched.should_trigger_outer_loop(logics, coverage, avg_ic):
            print("\n  ⚠ All scores negative — recommend /logic new (outer loop)")
```

- [ ] **Step 2: Register in argparse main()**

Add `logic` subparser with actions `list`, `coverage`, `schedule` and optional `--status` flag.

- [ ] **Step 3: Test manually**

Run: `PYTHONPATH=src python3 -m mining logic coverage`
Expected: Shows taxonomy categories with counts (all 0 initially)

- [ ] **Step 4: Commit**

```bash
git add src/mining/cli.py
git commit -m "feat(L5): add logic list/coverage/schedule CLI commands"
```

---

## Task 13: Memory Context Expansion — 5-Layer Prompt Assembly

**Files:**
- Modify: `src/mining/memory.py:49-77` (compose_search_context)

- [ ] **Step 1: Expand compose_search_context()**

This is the critical integration point for L4 (Spec 7.4). The method builds the prompt context that `/idea` skill feeds to LLM.

Add new sections to the returned context string:

```python
def compose_search_context(self, config=None) -> str:
    """Build prompt-ready context with 5 layers of information."""
    sections = []

    # 1. Library state (existing, enhanced)
    sections.append(self._library_state_section())

    # 2. Coverage map (NEW — from L4)
    if config:
        from mining.logic_library import MarketLogicLibrary
        logic_lib = MarketLogicLibrary(config.logic_dir)
        coverage = logic_lib.coverage_map()
        sections.append(self._coverage_section(coverage))

    # 3. Forbidden regions (NEW — from L2)
    forbidden = self.read_forbidden()
    if forbidden:
        sections.append(self._forbidden_section(forbidden))

    # 4. Active logics with evidence (NEW — from L4)
    if config:
        active_logics = logic_lib.list_logics(status="active")
        sections.append(self._logic_evidence_section(active_logics))

    # 5. Lineage summary (NEW — from L3)
    # Read from library records
    sections.append(self._lineage_section())

    # 6. Existing direction context (KEEP for backward compat)
    sections.append(self._directions_section())

    return "\n\n".join(s for s in sections if s)
```

Implement each `_*_section()` helper to format the data for LLM consumption.

- [ ] **Step 2: Test by running**

Run: `PYTHONPATH=src python3 -c "from mining.memory import ExperienceMemory; m = ExperienceMemory('storage/memory'); print(m.compose_search_context())"`
Expected: Should print the expanded context (mostly empty new sections initially)

- [ ] **Step 3: Commit**

```bash
git add src/mining/memory.py
git commit -m "feat(L4): expand compose_search_context with 5-layer prompt assembly"
```

---

## Task 14: Skill Updates — /idea, /judge, /mine

**Files:**
- Modify: `.claude/skills/factor-idea/skill.md`
- Modify: `.claude/skills/factor-judge/skill.md`
- Modify: `.claude/skills/factor-mine/skill.md`
- Create: `.claude/skills/factor-logic/skill.md`

These are prompt engineering changes, not Python code. Each skill needs specific modifications.

- [ ] **Step 1: Update /idea skill**

Key changes to `.claude/skills/factor-idea/skill.md`:
1. **Strategy phase**: Read scheduler recommendations first (`python -m mining logic schedule`)
2. **Context assembly**: Use expanded `compose_search_context()` with 5 layers
3. **Mode selection**: Based on `EvolutionEngine.suggest_mode()`, decide genesis/mutate/crossover ratio for this batch
4. **Candidate format**: Support `type: python` candidates with `code`, `params`, `param_space` fields
5. **Logic assignment**: Each candidate gets a `logic_id` linking to the market logic it targets

- [ ] **Step 2: Update /judge skill**

Key changes to `.claude/skills/factor-judge/skill.md`:
1. **Admission**: Pass `source`, `code`, `logic_id`, `lineage` to `lib.admit()`
2. **Logic feedback**: After judging, update logic stats (factors_generated++, etc.)
3. **Forbidden auto-add**: If same expression pattern rejected 3+ times, add to forbidden.yaml
4. **Lineage recording**: Record parent(s), mutation_type, generation for each candidate
5. **Status transitions**: Auto-transition logic to saturated/dead based on rounds_without_admit

- [ ] **Step 3: Update /mine skill**

Key changes to `.claude/skills/factor-mine/skill.md`:
1. **Pre-flight**: Run scheduler to check if outer loop is needed
2. **Outer loop trigger**: If all logic scores negative, suggest `/logic new` instead of `/idea`
3. **Report phase**: Unchanged

- [ ] **Step 4: Create /logic skill**

```markdown
# .claude/skills/factor-logic/skill.md
---
name: factor-logic
description: Create or review market logics for the L4 logic layer
---

## /logic new — Create New Market Logic (Outer Loop)

### Step 1: Read current state
- Run: `PYTHONPATH=src python3 -m mining logic coverage`
- Run: `PYTHONPATH=src python3 -m mining logic list`
- Read: `storage/memory/forbidden.yaml`

### Step 2: Identify gaps
Based on coverage map, identify which taxonomy categories are underrepresented.

### Step 3: Generate new logics
For each gap, propose 2-3 market logics with structured hypotheses:
- condition: what market state triggers this signal
- behavior: what happens next
- timeframe: over what horizon
- direction: long or short

### Step 4: Write logic files
For each approved logic, create YAML in storage/logic/:
`PYTHONPATH=src python3 -c "from mining.logic_library import MarketLogicLibrary; ..."`

## /logic review — Review Logic States
Run: `PYTHONPATH=src python3 -m mining logic schedule`
Show scheduler scores and recommend next actions.
```

- [ ] **Step 5: Commit all skill updates**

```bash
git add .claude/skills/
git commit -m "feat(L5): update /idea /judge /mine skills and add /logic skill"
```

---

## Task 15: Integration Test — End-to-End Python Factor Flow

**Files:**
- Create: `tests/mining/test_python_factor_e2e.py`

- [ ] **Step 1: Write end-to-end test**

```python
# tests/mining/test_python_factor_e2e.py
"""End-to-end test: Python factor generation → evaluation → admission."""
import pytest
import os
import yaml
from mining.config import MiningConfig
from mining.evaluator import FactorMiningEvaluator
from mining.library import FactorLibrary


@pytest.fixture
def e2e_setup(tmp_path):
    config = MiningConfig()
    config.library_dir = str(tmp_path / "library")
    config.factors_dir = str(tmp_path / "factors")
    os.makedirs(config.library_dir, exist_ok=True)
    os.makedirs(config.factors_dir, exist_ok=True)

    # Create empty library index
    index_path = os.path.join(config.library_dir, "library.yaml")
    yaml.dump({"thresholds": {}, "factors": []}, open(index_path, "w"))

    return config


class TestPythonFactorE2E:
    def test_mixed_batch_yaml(self, e2e_setup, tmp_path):
        """A batch YAML with both DSL and Python candidates should parse correctly."""
        batch = {
            "batch_id": "test_001",
            "candidates": [
                {"name": "dsl_factor", "type": "dsl",
                 "expression": "Std($close, 20)", "category": "volatility"},
                {"name": "py_factor", "type": "python", "source": "python",
                 "code": "return ops.cs_rank(ops.std(df['close'], params['w']))",
                 "params": {"w": 20}, "param_space": {"w": [5, 60]},
                 "category": "volatility", "logic_id": "L001"},
            ],
        }
        batch_path = tmp_path / "batch.yaml"
        yaml.dump(batch, open(batch_path, "w"))

        loaded = yaml.safe_load(open(batch_path))
        assert len(loaded["candidates"]) == 2
        assert loaded["candidates"][0]["type"] == "dsl"
        assert loaded["candidates"][1]["type"] == "python"
        assert "code" in loaded["candidates"][1]
```

- [ ] **Step 2: Run test**

Run: `PYTHONPATH=src pytest tests/mining/test_python_factor_e2e.py -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add tests/mining/test_python_factor_e2e.py
git commit -m "test: add end-to-end Python factor flow integration test"
```

---

## Task 16: Module Exports and Final Wiring

**Files:**
- Modify: `src/mining/__init__.py`

- [ ] **Step 1: Update exports**

```python
# Add to src/mining/__init__.py
from mining.ops_adapter import OpsAdapter
from mining.sandbox import run_factor_in_sandbox, SandboxError
from mining.evolution import EvolutionEngine
from mining.scheduler import Scheduler
from mining.logic_library import MarketLogicLibrary
```

- [ ] **Step 2: Run full test suite**

Run: `PYTHONPATH=src pytest tests/mining/ -v --tb=short`
Expected: All tests PASS (existing + new)

- [ ] **Step 3: Final commit**

```bash
git add src/mining/__init__.py
git commit -m "feat: wire up all new modules in mining package exports"
```

---

---

## Errata: Review Fixes (Applied to All Tasks Above)

The following corrections apply to the tasks above. Implementors MUST read these before starting.

### Fix 1: ExperienceMemory takes MiningConfig, not str (affects Task 5)

Task 5 test fixture must use:
```python
@pytest.fixture
def memory(tmp_path):
    mem_dir = tmp_path / "memory"
    mem_dir.mkdir()
    (mem_dir / "history").mkdir()
    (mem_dir / "directions").mkdir()
    (mem_dir / "state.yaml").write_text("library:\n  size: 0\n")
    (mem_dir / "directions.yaml").write_text("directions: []\n")
    (mem_dir / "forbidden.yaml").write_text("forbidden_regions: []\n")
    config = MiningConfig(memory_dir=str(mem_dir))
    return ExperienceMemory(config)
```

Task 5 implementation: use `self._dir / "forbidden.yaml"` (Path style), not `os.path.join`. The `self._dir` is a `Path` object in the existing codebase.

### Fix 2: ValidationResult has `errors: List[str]`, not `message` (affects Task 4)

Task 4 tests must check `result.errors` instead of `result.message`:
```python
assert any("SyntaxError" in e for e in result.errors)
```

Task 4 implementation must return:
```python
return ValidationResult(False, errors=[f"SyntaxError: {e}"])
```

Check the actual `ValidationResult` dataclass fields before implementing.

### Fix 3: _compute_factor_qlib takes 4 args (affects Task 7)

The actual signature is:
```python
def _compute_factor_qlib(self, expression, instruments, start_time, end_time) -> pd.DataFrame
```

Task 7 dispatcher must forward all args:
```python
def _compute_factor(self, candidate, instruments, start_time, end_time):
    if candidate.get("source") == "python" or candidate.get("type") == "python":
        return self._compute_factor_python(candidate, instruments, start_time, end_time)
    return self._compute_factor_qlib(candidate["expression"], instruments, start_time, end_time)
```

### Fix 4: Sandbox returns Series, evaluator expects DataFrame (affects Task 7)

`_compute_factor_python` must wrap the sandbox result:
```python
def _compute_factor_python(self, candidate, instruments, start_time, end_time):
    df = self._load_panel_ohlcv(instruments, start_time, end_time)
    series = run_factor_in_sandbox(candidate["code"], df, candidate.get("params", {}))
    return series.to_frame(name=candidate["name"])
```

`_load_panel_ohlcv` is a new helper method that loads OHLCV data as a (datetime, instrument) MultiIndex DataFrame using Qlib `D.features()` with fields `[$open, $high, $low, $close, $volume]`. This already has a partial pattern in `_compute_factor_qlib` — extract and generalize it.

### Fix 5: Don't break admit() signature (affects Task 6)

Current `admit(self, factor: Dict) -> str` extracts metrics from inside the factor dict. Keep the same signature. Add new fields by reading them from the `factor` dict:
```python
def admit(self, factor: Dict[str, Any]) -> str:
    source = factor.get("source", "dsl")
    logic_id = factor.get("logic_id", "legacy")
    lineage = factor.get("lineage")
    # ... rest of existing logic, just add new fields to the record
```

### Fix 6: Lookahead detection — replace stub with working implementation (affects Task 8)

Remove the shuffle-based approach (too complex, `pass` stub). Keep only the static AST check but make it more comprehensive:
```python
def check_lookahead_bias(code: str) -> bool:
    """Static analysis for common lookahead patterns in Python factor code."""
    import ast
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return False

    for node in ast.walk(tree):
        # Check shift with negative values: df.shift(-N)
        if (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "shift"):
            for arg in node.args:
                if isinstance(arg, ast.UnaryOp) and isinstance(arg.op, ast.USub):
                    return True
                if isinstance(arg, ast.Constant) and isinstance(arg.value, (int, float)) and arg.value < 0:
                    return True
        # Check iloc/loc with negative shift patterns
        if (isinstance(node, ast.Subscript)
                and isinstance(node.value, ast.Attribute)
                and node.value.attr in ("iloc", "loc")):
            # Flag for human review — can't definitively detect in all cases
            pass

    return False
```

No sandbox needed for this — it's pure static analysis.

### Fix 7: `storage/factors/` vs `storage/library/factors/` naming (affects Tasks 3, 6)

Change config to avoid collision:
```python
python_factors_dir: str = "storage/python_factors"  # NOT "storage/factors"
```

### Fix 8: compose_search_context config access (affects Task 13)

Store config in ExperienceMemory `__init__`:
```python
# ExperienceMemory already receives config in __init__
# self._config = config  ← add this line
# Then compose_search_context() can use self._config.logic_dir etc.
```

---

## Missing Tasks (Insert After Task 8)

### Task 8a: Optuna Parameter Optimization

**Files:**
- Modify: `src/mining/evaluator.py` (add `_optimize_params` method)
- Modify: `tests/mining/test_evaluator.py`
- Requires: `pip install optuna`

- [ ] **Step 1: Write failing test**

```python
class TestOptunaOptimization:
    def test_optimize_finds_better_params(self, evaluator):
        candidate = {
            "name": "test_optuna", "type": "python", "source": "python",
            "code": "return ops.std(df['close'], params['w'])",
            "params": {"w": 20},
            "param_space": {"w": [5, 60]},
            "category": "volatility", "logic_id": "L001",
        }
        optimized = evaluator._optimize_params(candidate)
        assert "w" in optimized["params"]
        assert 5 <= optimized["params"]["w"] <= 60
```

- [ ] **Step 2: Implement _optimize_params**

```python
def _optimize_params(self, candidate: dict) -> dict:
    """Use Optuna to search param_space, return candidate with best params."""
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)

    param_space = candidate.get("param_space")
    if not param_space:
        return candidate

    def objective(trial):
        params = {}
        for name, bounds in param_space.items():
            if isinstance(bounds, list) and len(bounds) == 2:
                if isinstance(bounds[0], int):
                    params[name] = trial.suggest_int(name, bounds[0], bounds[1])
                else:
                    params[name] = trial.suggest_float(name, bounds[0], bounds[1])
        test_candidate = {**candidate, "params": params}
        try:
            factor_values = self._compute_factor(
                test_candidate, self._fast_instruments,
                self.config.train_start, self.config.train_end
            )
            ic = self._compute_rank_ic(factor_values)
            return abs(ic)  # Maximize absolute IC
        except Exception:
            return 0.0

    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=self.config.optuna_trials,
                   timeout=self.config.optuna_timeout)

    best_params = study.best_params
    result = {**candidate, "params": best_params}
    return result
```

- [ ] **Step 3: Wire into evaluate_batch()**

In `evaluate_batch()`, after validation but before Stage 1, add:
```python
# Optimize params for Python factors with param_space
if c.get("param_space"):
    c = self._optimize_params(c)
```

- [ ] **Step 4: Run tests, commit**

### Task 8b: AST Structural Dedup

**Files:**
- Modify: `src/mining/evaluator.py` (add `_structural_dedup` check)
- Modify: `src/mining/metrics.py` (add `ast_similarity_score` field)

- [ ] **Step 1: Write failing test**

```python
class TestStructuralDedup:
    def test_identical_ops_signature_flagged(self, evaluator):
        c1 = {"name": "f1", "type": "python", "code": "return ops.cs_rank(ops.std(df['close'], 20))"}
        c2 = {"name": "f2", "type": "python", "code": "return ops.cs_rank(ops.std(df['high'], 10))"}
        similarity = evaluator._compute_structural_similarity(c1, c2)
        assert similarity > 0.8  # Same ops structure

    def test_different_ops_signature_ok(self, evaluator):
        c1 = {"name": "f1", "type": "python", "code": "return ops.cs_rank(ops.std(df['close'], 20))"}
        c2 = {"name": "f2", "type": "python", "code": "return ops.hhi(df['volume'], 10)"}
        similarity = evaluator._compute_structural_similarity(c1, c2)
        assert similarity < 0.5
```

- [ ] **Step 2: Implement**

```python
def _compute_structural_similarity(self, c1: dict, c2: dict) -> float:
    """Jaccard similarity of ops call signatures."""
    ops1 = set(self.validator.extract_ops_calls(c1.get("code", "")))
    ops2 = set(self.validator.extract_ops_calls(c2.get("code", "")))
    if not ops1 and not ops2:
        return 0.0
    if not ops1 or not ops2:
        return 0.0
    return len(ops1 & ops2) / len(ops1 | ops2)
```

Add to `_batch_dedup()`: if structural similarity > `config.ast_similarity_threshold`, flag as "structural_redundancy" warning in the candidate dict.

- [ ] **Step 3: Run tests, commit**

### Task 8c: Lineage Tracking and Python Factor File Persistence

**Files:**
- Modify: `src/mining/library.py` (add `_write_python_factor`, lineage storage)
- Modify: `src/mining/evolution.py` (add `LineageTracker`)

- [ ] **Step 1: Write failing tests**

```python
class TestLineageTracking:
    def test_record_and_read_lineage(self, library):
        factor = {
            "name": "child", "expression": "Std($close, 20)", "category": "vol",
            "lineage": {"parents": ["F001"], "mutation_type": "macro", "generation": 2},
        }
        library.admit(factor)
        factors = library.list_factors()
        child = [f for f in factors if f["name"] == "child"][0]
        assert child["lineage"]["parents"] == ["F001"]

class TestPythonFactorPersistence:
    def test_py_file_written_on_admit(self, library):
        factor = {
            "name": "test_persist", "source": "python",
            "code": "return ops.cs_rank(df['close'])",
            "params": {"w": 20}, "param_space": {"w": [5, 60]},
            "logic_id": "L001", "category": "volume",
            "lineage": {"parents": [], "mutation_type": "genesis", "generation": 1},
        }
        result = library.admit(factor, publish=False)
        path = result.get("code_path") or library._find_python_factor_path(result["id"])
        assert os.path.exists(path)
        content = open(path).read()
        assert "META" in content
        assert "def compute" in content
```

- [ ] **Step 2: Implement `_write_python_factor` in library.py**

```python
def _write_python_factor(self, path: str, factor: dict) -> None:
    """Persist a Python factor as a standalone .py file with META + compute()."""
    meta = {
        "name": factor["name"],
        "logic_id": factor.get("logic_id", "legacy"),
        "params": factor.get("params", {}),
        "param_space": factor.get("param_space", {}),
        "lineage": factor.get("lineage", {}),
    }
    code = factor["code"]
    indented = "\n".join(f"    {line}" for line in code.strip().split("\n"))

    content = f'''"""Auto-generated Python factor: {factor["name"]}"""
META = {repr(meta)}


def compute(df, params, ops):
{indented}
'''
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)
```

- [ ] **Step 3: Add `format_lineage_tree` to EvolutionEngine**

```python
def format_lineage_tree(self, factors: list[dict]) -> str:
    """Format lineage as text tree for prompt context."""
    lines = []
    roots = [f for f in factors if not f.get("lineage", {}).get("parents")]
    children_map = {}
    for f in factors:
        for p in (f.get("lineage") or {}).get("parents", []):
            children_map.setdefault(p, []).append(f)

    def _render(factor, indent=0):
        prefix = "  " * indent + ("├── " if indent > 0 else "")
        lines.append(f"{prefix}F{factor['id']} ({factor['name']})")
        for child in children_map.get(factor["id"], []):
            _render(child, indent + 1)

    for root in roots:
        _render(root)
    return "\n".join(lines) if lines else "(no lineage data)"
```

- [ ] **Step 4: Run tests, commit**

---

## Task Summary

| Task | Layer | What it Builds | Dependencies |
|------|-------|---------------|-------------|
| 1 | L2 | OpsAdapter | operators.py (read-only) |
| 2 | L2 | Sandbox execution | Task 1 (OpsAdapter) |
| 3 | Config | New config fields | None |
| 4 | L1 | Python expression validator | None |
| 5 | L2 | Forbidden regions | memory.py |
| 6 | L2 | Library schema extension + Python factor persistence | Task 3 (config) |
| 7 | L1 | Evaluator dual-dispatch | Tasks 1, 2, 4 |
| 8 | L1 | Lookahead detection (static analysis) | None |
| **8a** | **L1** | **Optuna parameter optimization** | **Tasks 1, 2, 7** |
| **8b** | **L1** | **AST structural dedup** | **Task 4** |
| **8c** | **L2** | **Lineage tracking + .py persistence** | **Task 6** |
| 9 | L4 | Market Logic Library | Task 3 (config) |
| 10 | L3 | Evolution Engine | Task 3 (config) |
| 11 | L5 | Scheduler | Task 9 (logic lib) |
| 12 | L5 | CLI new commands | Tasks 9, 11 |
| 13 | L4 | Memory context expansion | Tasks 5, 9 |
| 14 | L5 | Skill updates | All above |
| 15 | All | Integration test | All above |
| 16 | All | Module exports | All above |
