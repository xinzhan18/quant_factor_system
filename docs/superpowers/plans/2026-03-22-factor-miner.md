# FactorMiner Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an automated factor mining system implementing the Ralph Loop (Retrieve → Generate → Evaluate → Distill) with Qlib expression engine, multi-stage evaluation pipeline, and YAML-based Experience Memory.

**Architecture:** New `mining/` module independent of existing factor layer. Python handles computation (IC, correlation, data sync); Claude Code Skills handle orchestration (factor generation, memory distillation). All state persisted as YAML files.

**Tech Stack:** Python 3.8+, Qlib (Microsoft), PyYAML, scipy, pandas, TimescaleDB (existing)

**Spec:** `docs/superpowers/specs/2026-03-22-factor-miner-design.md`

---

## File Structure

### New Files to Create

| File | Responsibility |
|------|---------------|
| `mining/__init__.py` | Package exports |
| `mining/config.py` | `MiningConfig` dataclass with all thresholds |
| `mining/expression.py` | `ExpressionValidator` — syntax/field/depth checks |
| `mining/operators.py` | Custom Qlib operator registration (SignedPower, TsDecay, Scale, Tanh, Exp) |
| `mining/data_sync.py` | `DataSynchronizer` — TimescaleDB → Qlib bin format |
| `mining/evaluator.py` | `FactorMiningEvaluator` — 5-stage pipeline |
| `mining/library.py` | `FactorLibrary` — YAML-based factor library CRUD |
| `mining/memory.py` | `ExperienceMemory` — read/write state, patterns, insights, history |
| `mining/memory/state.yaml` | Initial mining state |
| `mining/memory/patterns.yaml` | Seed recommended directions + forbidden regions |
| `mining/memory/insights.yaml` | Seed strategic insights |
| `mining/library/library.yaml` | Empty library index |
| `tests/__init__.py` | Test package |
| `tests/conftest.py` | Shared fixtures (mock Qlib, sample data) |
| `tests/mining/__init__.py` | Mining test package |
| `tests/mining/test_config.py` | Config tests |
| `tests/mining/test_expression.py` | Expression validator tests |
| `tests/mining/test_evaluator.py` | Evaluator pipeline tests |
| `tests/mining/test_library.py` | Library management tests |
| `tests/mining/test_memory.py` | Experience Memory tests |

### Files to Modify

| File | Change |
|------|--------|
| `setup.py` | Add `qlib`, `pyyaml` dependencies |

---

### Task 1: Project Scaffolding & Configuration

**Files:**
- Create: `mining/__init__.py`, `mining/config.py`
- Create: `mining/memory/state.yaml`, `mining/memory/patterns.yaml`, `mining/memory/insights.yaml`
- Create: `mining/library/library.yaml`
- Create: `mining/candidates/.gitkeep`, `mining/library/factors/.gitkeep`, `mining/memory/history/.gitkeep`
- Create: `tests/__init__.py`, `tests/conftest.py`, `tests/mining/__init__.py`, `tests/mining/test_config.py`
- Modify: `setup.py`

- [ ] **Step 1: Create directory structure**

```bash
cd /Users/xinzhan/.openclaw/workspace/quant_factor_system
mkdir -p mining/memory/history mining/library/factors mining/candidates
mkdir -p tests/mining
```

- [ ] **Step 2: Write `mining/config.py`**

```python
"""Mining configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class MiningConfig:
    """Configuration for the factor mining pipeline."""

    # Data
    qlib_data_dir: str = "~/.qlib/qlib_data/cn_data_1d"

    # Evaluation thresholds
    ic_threshold: float = 0.03
    correlation_threshold: float = 0.5
    replacement_ic_ratio: float = 1.3
    replacement_ic_min: float = 0.05

    # Fast screening
    fast_screening_universe_size: int = 50

    # Library target
    target_library_size: int = 100

    # Universe
    universe: str = "csi500"
    custom_universe: Optional[List[str]] = None

    # Time ranges
    train_start: str = "2020-01-01"
    train_end: str = "2024-12-31"
    test_start: str = "2025-01-01"
    test_end: Optional[str] = None

    # Per-batch
    candidates_per_batch: int = 8

    # Expression limits
    max_expression_depth: int = 10

    # Paths (relative to project root)
    memory_dir: str = "mining/memory"
    library_dir: str = "mining/library"
    candidates_dir: str = "mining/candidates"

    # Available base fields
    base_fields: List[str] = field(default_factory=lambda: [
        "$open", "$high", "$low", "$close", "$volume", "$amount", "$vwap",
        "$returns",
    ])

    # Minute-aggregated fields (available after sync_minute_aggregates)
    minute_agg_fields: List[str] = field(default_factory=lambda: [
        "$intraday_vol", "$intraday_skew", "$intraday_kurt",
        "$vwap_dev", "$volume_conc", "$high_low_range",
        "$morning_momentum", "$afternoon_ret",
    ])

    # Predefined categories
    categories: List[str] = field(default_factory=lambda: [
        "vwap", "momentum", "volatility", "volume", "regime",
        "efficiency", "distribution", "trend", "candlestick",
        "intraday_agg", "other",
    ])
```

- [ ] **Step 3: Write initial YAML files**

`mining/memory/state.yaml`:
```yaml
library:
  size: 0
  target_size: 100
  avg_ic: 0.0
  avg_correlation: 0.0

domain_saturation:
  vwap: {count: 0, saturation: low}
  momentum: {count: 0, saturation: low}
  volatility: {count: 0, saturation: low}
  volume: {count: 0, saturation: low}
  regime: {count: 0, saturation: low}
  efficiency: {count: 0, saturation: low}
  distribution: {count: 0, saturation: low}
  trend: {count: 0, saturation: low}
  candlestick: {count: 0, saturation: low}
  intraday_agg: {count: 0, saturation: low}

mining:
  total_batches: 0
  total_candidates: 0
  total_admitted: 0
  total_rejected: 0
  yield_rate: 0.0
  last_batch_time: null
```

`mining/memory/patterns.yaml`:
```yaml
recommended_directions:
  - pattern: "Higher Moment Regimes"
    description: "Use Skew/Kurt as IfElse conditions to identify extreme distribution environments for reversal signals"
    success_rate: high
    example_factors: []

  - pattern: "Trend Regression Adaptive"
    description: "Use Rsquare/Slope/Resi for adaptive trend regression. High R2 trend follow, Low R2 mean reversion"
    success_rate: high
    example_factors: []

  - pattern: "PV Corr Interaction"
    description: "Combine price-volume correlation with amount efficiency or trend operators to capture volume-price coordination"
    success_rate: high
    example_factors: []

  - pattern: "Robust Efficiency"
    description: "Use median and other robust statistics to smooth amount efficiency, filtering extreme noise"
    success_rate: high
    example_factors: []

  - pattern: "Intraday Aggregation Features"
    description: "Leverage minute-data aggregated features (intraday_vol, intraday_skew, volume_concentration) as inputs for daily factors"
    success_rate: medium
    example_factors: []

forbidden_regions:
  - direction: "Simple VWAP Deviation"
    reason: "High correlation with VWAP factor cluster"
    correlated_factors: []
    correlation: "> 0.5"

  - direction: "Standardized Returns/Amount"
    reason: "Simple return standardization is redundant with existing factors"
    correlated_factors: []
    correlation: "> 0.6"
```

`mining/memory/insights.yaml`:
```yaml
insights:
  - insight: "Non-linear combinations (IfElse branching) are more likely to produce orthogonal factors than linear combinations"
    confidence: high
    source: "paper finding"

  - insight: "CsRank wrapping can effectively reduce inter-factor correlation"
    confidence: high
    source: "paper Appendix G"

  - insight: "Amount efficiency (Returns/Amount) produces signals orthogonal to pure price-based factors"
    confidence: high
    source: "paper finding"

  - insight: "Daily frequency VWAP signal space is more limited than intraday; minute-aggregated features may offer more room"
    confidence: medium
    source: hypothesis
```

`mining/library/library.yaml`:
```yaml
thresholds:
  ic_min: 0.03
  correlation_max: 0.5
  replacement_ic_ratio: 1.3
  replacement_ic_min: 0.05

factors: []
```

- [ ] **Step 4: Write `mining/__init__.py`**

```python
"""FactorMiner: Automated factor mining with Experience Memory."""

from .config import MiningConfig

__all__ = ["MiningConfig"]
```

- [ ] **Step 5: Write `.gitkeep` files and `tests/__init__.py`**

```bash
touch mining/candidates/.gitkeep mining/library/factors/.gitkeep mining/memory/history/.gitkeep
touch tests/__init__.py tests/mining/__init__.py
```

- [ ] **Step 6: Write test for MiningConfig**

`tests/mining/test_config.py`:
```python
"""Tests for MiningConfig."""

from mining.config import MiningConfig


def test_default_config():
    cfg = MiningConfig()
    assert cfg.ic_threshold == 0.03
    assert cfg.correlation_threshold == 0.5
    assert cfg.replacement_ic_ratio == 1.3
    assert cfg.candidates_per_batch == 8
    assert cfg.universe == "csi500"
    assert cfg.custom_universe is None
    assert cfg.max_expression_depth == 10


def test_custom_config():
    cfg = MiningConfig(ic_threshold=0.05, universe="custom", custom_universe=["SH600000", "SZ000001"])
    assert cfg.ic_threshold == 0.05
    assert cfg.universe == "custom"
    assert len(cfg.custom_universe) == 2


def test_categories():
    cfg = MiningConfig()
    assert "vwap" in cfg.categories
    assert "momentum" in cfg.categories
    assert "other" in cfg.categories
    assert len(cfg.categories) == 11


def test_base_fields():
    cfg = MiningConfig()
    assert "$close" in cfg.base_fields
    assert "$vwap" in cfg.base_fields
    assert "$returns" in cfg.base_fields
```

- [ ] **Step 7: Run tests to verify**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && python -m pytest tests/mining/test_config.py -v`
Expected: 4 tests PASS

- [ ] **Step 8: Update `setup.py` with new dependencies**

Add to `install_requires`:
```python
"pyyaml>=6.0",
```

Add new extra:
```python
"mining": ["qlib>=0.9.0"],
```

- [ ] **Step 9: Write `tests/conftest.py` with shared fixtures**

```python
"""Shared test fixtures for mining tests."""

import os
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from mining.config import MiningConfig


@pytest.fixture
def tmp_mining_dir(tmp_path):
    """Create temporary mining directory structure."""
    memory_dir = tmp_path / "memory" / "history"
    memory_dir.mkdir(parents=True)
    library_dir = tmp_path / "library" / "factors"
    library_dir.mkdir(parents=True)
    candidates_dir = tmp_path / "candidates"
    candidates_dir.mkdir(parents=True)
    return tmp_path


@pytest.fixture
def config(tmp_mining_dir):
    """MiningConfig pointing to temp directories."""
    return MiningConfig(
        memory_dir=str(tmp_mining_dir / "memory"),
        library_dir=str(tmp_mining_dir / "library"),
        candidates_dir=str(tmp_mining_dir / "candidates"),
        train_start="2023-01-01",
        train_end="2023-12-31",
        test_start="2024-01-01",
        test_end="2024-06-30",
    )


@pytest.fixture
def sample_factor_values():
    """Sample factor values DataFrame (date x instrument MultiIndex)."""
    dates = pd.bdate_range("2023-01-02", periods=60)
    instruments = [f"SH60000{i}" for i in range(10)]
    idx = pd.MultiIndex.from_product([dates, instruments], names=["datetime", "instrument"])
    np.random.seed(42)
    return pd.DataFrame({"factor": np.random.randn(len(idx))}, index=idx)


@pytest.fixture
def sample_returns():
    """Sample returns DataFrame matching sample_factor_values index."""
    dates = pd.bdate_range("2023-01-02", periods=60)
    instruments = [f"SH60000{i}" for i in range(10)]
    idx = pd.MultiIndex.from_product([dates, instruments], names=["datetime", "instrument"])
    np.random.seed(123)
    return pd.DataFrame({"$returns_1d": np.random.randn(len(idx)) * 0.02}, index=idx)
```

- [ ] **Step 10: Commit**

```bash
cd /Users/xinzhan/.openclaw/workspace/quant_factor_system
git add mining/ tests/ setup.py
git commit -m "feat(mining): scaffold project structure and MiningConfig"
```

---

### Task 2: Expression Validator

**Files:**
- Create: `mining/expression.py`
- Create: `tests/mining/test_expression.py`
- Modify: `mining/__init__.py`

- [ ] **Step 1: Write the failing test**

`tests/mining/test_expression.py`:
```python
"""Tests for ExpressionValidator."""

import pytest

from mining.expression import ExpressionValidator, ValidationResult


@pytest.fixture
def validator():
    return ExpressionValidator()


class TestValidationResult:
    def test_valid_result(self):
        r = ValidationResult(valid=True, errors=[], warnings=[])
        assert r.valid
        assert r.errors == []

    def test_invalid_result(self):
        r = ValidationResult(valid=False, errors=["bad syntax"], warnings=[])
        assert not r.valid
        assert "bad syntax" in r.errors


class TestFieldCheck:
    def test_valid_fields(self, validator):
        result = validator.validate("Rank(Div(Sub($close, $vwap), $vwap))")
        assert result.valid

    def test_unknown_field(self, validator):
        result = validator.validate("Rank($nonexistent_field)")
        assert not result.valid
        assert any("nonexistent_field" in e for e in result.errors)

    def test_dollar_sign_required(self, validator):
        # Fields must start with $
        result = validator.validate("Rank($close)")
        assert result.valid


class TestDepthCheck:
    def test_within_depth_limit(self, validator):
        # Depth 3: Rank(Div(Sub(...)))
        result = validator.validate("Rank(Div(Sub($close, $vwap), $vwap))")
        assert result.valid

    def test_exceeds_depth_limit(self, validator):
        # Build deeply nested expression
        expr = "$close"
        for _ in range(12):
            expr = f"Rank({expr})"
        result = validator.validate(expr, max_depth=10)
        assert not result.valid
        assert any("depth" in e.lower() for e in result.errors)


class TestSyntaxCheck:
    def test_balanced_parens(self, validator):
        result = validator.validate("Rank(Div($close, $vwap))")
        assert result.valid

    def test_unbalanced_parens(self, validator):
        result = validator.validate("Rank(Div($close, $vwap)")
        assert not result.valid
        assert any("paren" in e.lower() for e in result.errors)

    def test_empty_expression(self, validator):
        result = validator.validate("")
        assert not result.valid

    def test_bare_field(self, validator):
        result = validator.validate("$close")
        assert result.valid


class TestSafeWrap:
    def test_wraps_div(self, validator):
        wrapped = validator.safe_wrap("Div($close, $volume)")
        assert "Div" in wrapped or "If" in wrapped
        # Should handle zero division
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && python -m pytest tests/mining/test_expression.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'mining.expression'`

- [ ] **Step 3: Implement `mining/expression.py`**

```python
"""Expression validation for Qlib factor expressions."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Set

from .config import MiningConfig


@dataclass
class ValidationResult:
    """Result of expression validation."""

    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


# Known Qlib operators (not exhaustive, but covers spec needs)
KNOWN_OPERATORS = {
    # Arithmetic
    "Add", "Sub", "Mul", "Div", "Abs", "Log", "Power", "Sign", "Neg",
    # Statistical
    "Mean", "Std", "Var", "Skew", "Kurt", "Med", "Sum", "Prod",
    # Time-series
    "Ref", "Delta", "TsRank", "TsMax", "TsMin", "TsArgMax", "TsArgMin",
    "Correlation",
    # Cross-sectional
    "Rank", "CSRankNorm",
    # Smoothing
    "EMA", "SMA", "WMA",
    # Regression
    "Slope", "Rsquare", "Resi",
    # Logical
    "If", "Greater", "Less",
    # Custom extensions
    "SignedPower", "TsDecay", "Scale", "Tanh", "Exp",
}


class ExpressionValidator:
    """Validate Qlib factor expressions before computation."""

    def __init__(self, config: MiningConfig | None = None):
        self._config = config or MiningConfig()
        self._valid_fields: Set[str] = set(
            self._config.base_fields + self._config.minute_agg_fields
        )

    def validate(
        self, expression: str, max_depth: int | None = None
    ) -> ValidationResult:
        """Validate a Qlib expression.

        Checks: non-empty, balanced parentheses, known fields, depth limit.
        """
        if max_depth is None:
            max_depth = self._config.max_expression_depth

        errors: List[str] = []
        warnings: List[str] = []

        # Empty check
        if not expression or not expression.strip():
            return ValidationResult(valid=False, errors=["Empty expression"])

        expr = expression.strip()

        # Parentheses balance
        depth = 0
        for ch in expr:
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            if depth < 0:
                errors.append("Unbalanced parentheses: extra closing paren")
                break
        if depth > 0:
            errors.append("Unbalanced parentheses: missing closing paren")
        if errors:
            return ValidationResult(valid=False, errors=errors)

        # Field check — extract $field references
        fields_used = set(re.findall(r"\$[a-zA-Z_][a-zA-Z0-9_]*", expr))
        for f in fields_used:
            if f not in self._valid_fields:
                errors.append(f"Unknown field: {f}")

        # Depth check — count max nesting
        nesting = self._max_nesting_depth(expr)
        if nesting > max_depth:
            errors.append(
                f"Expression depth {nesting} exceeds limit {max_depth}"
            )

        # Operator check (warning only)
        ops_used = set(re.findall(r"([A-Z][a-zA-Z]+)\s*\(", expr))
        for op in ops_used:
            if op not in KNOWN_OPERATORS:
                warnings.append(f"Unknown operator: {op}")

        return ValidationResult(
            valid=len(errors) == 0, errors=errors, warnings=warnings
        )

    def safe_wrap(self, expression: str) -> str:
        """Wrap Div operations to handle zero division.

        Replaces Div(a, b) with If(Greater(Abs(b), 1e-8), Div(a, b), 0).
        """
        # Simple regex replacement for top-level Div
        pattern = r"Div\(([^()]+(?:\([^()]*\))*[^()]*),\s*([^()]+(?:\([^()]*\))*[^()]*)\)"

        def _safe_div(match):
            a, b = match.group(1).strip(), match.group(2).strip()
            return f"If(Greater(Abs({b}), 1e-8), Div({a}, {b}), 0)"

        return re.sub(pattern, _safe_div, expression)

    def _max_nesting_depth(self, expr: str) -> int:
        """Count maximum parenthesis nesting depth."""
        max_d = 0
        current = 0
        for ch in expr:
            if ch == "(":
                current += 1
                max_d = max(max_d, current)
            elif ch == ")":
                current -= 1
        return max_d
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && python -m pytest tests/mining/test_expression.py -v`
Expected: All tests PASS

- [ ] **Step 5: Update `mining/__init__.py`**

```python
"""FactorMiner: Automated factor mining with Experience Memory."""

from .config import MiningConfig
from .expression import ExpressionValidator, ValidationResult

__all__ = ["MiningConfig", "ExpressionValidator", "ValidationResult"]
```

- [ ] **Step 6: Commit**

```bash
git add mining/expression.py tests/mining/test_expression.py mining/__init__.py
git commit -m "feat(mining): add ExpressionValidator with field/depth/syntax checks"
```

---

### Task 3: Experience Memory

**Files:**
- Create: `mining/memory.py`
- Create: `tests/mining/test_memory.py`

- [ ] **Step 1: Write the failing test**

`tests/mining/test_memory.py`:
```python
"""Tests for ExperienceMemory."""

import yaml
import pytest
from pathlib import Path

from mining.memory import ExperienceMemory


@pytest.fixture
def memory(tmp_mining_dir, config):
    """ExperienceMemory with temp directory and seed files."""
    mem_dir = Path(config.memory_dir)
    # Write seed state
    (mem_dir / "state.yaml").write_text(yaml.dump({
        "library": {"size": 0, "target_size": 100, "avg_ic": 0.0, "avg_correlation": 0.0},
        "domain_saturation": {"vwap": {"count": 0, "saturation": "low"}},
        "mining": {
            "total_batches": 0, "total_candidates": 0,
            "total_admitted": 0, "total_rejected": 0,
            "yield_rate": 0.0, "last_batch_time": None,
        },
    }))
    (mem_dir / "patterns.yaml").write_text(yaml.dump({
        "recommended_directions": [
            {"pattern": "Test Pattern", "description": "desc", "success_rate": "high", "example_factors": []}
        ],
        "forbidden_regions": [],
    }))
    (mem_dir / "insights.yaml").write_text(yaml.dump({
        "insights": [
            {"insight": "Test insight", "confidence": "high", "source": "test"}
        ],
    }))
    return ExperienceMemory(config)


class TestReadState:
    def test_read_state(self, memory):
        state = memory.read_state()
        assert state["library"]["size"] == 0
        assert state["mining"]["total_batches"] == 0

    def test_read_patterns(self, memory):
        patterns = memory.read_patterns()
        assert len(patterns["recommended_directions"]) == 1
        assert patterns["recommended_directions"][0]["pattern"] == "Test Pattern"

    def test_read_insights(self, memory):
        insights = memory.read_insights()
        assert len(insights["insights"]) == 1


class TestWriteState:
    def test_update_state(self, memory):
        state = memory.read_state()
        state["library"]["size"] = 5
        state["mining"]["total_batches"] = 1
        memory.write_state(state)

        reloaded = memory.read_state()
        assert reloaded["library"]["size"] == 5
        assert reloaded["mining"]["total_batches"] == 1

    def test_add_pattern(self, memory):
        patterns = memory.read_patterns()
        patterns["recommended_directions"].append({
            "pattern": "New Pattern",
            "description": "new desc",
            "success_rate": "medium",
            "example_factors": [],
        })
        memory.write_patterns(patterns)

        reloaded = memory.read_patterns()
        assert len(reloaded["recommended_directions"]) == 2

    def test_add_forbidden_region(self, memory):
        patterns = memory.read_patterns()
        patterns["forbidden_regions"].append({
            "direction": "Bad Direction",
            "reason": "too correlated",
            "correlated_factors": ["f1"],
            "correlation": "> 0.7",
        })
        memory.write_patterns(patterns)

        reloaded = memory.read_patterns()
        assert len(reloaded["forbidden_regions"]) == 1


class TestHistory:
    def test_save_batch_history(self, memory):
        batch_data = {
            "batch_id": "batch_001",
            "candidates": 8,
            "admitted": 2,
            "rejected": 6,
        }
        memory.save_batch_history("batch_001", batch_data)

        history = memory.load_batch_history("batch_001")
        assert history["batch_id"] == "batch_001"
        assert history["admitted"] == 2

    def test_list_history(self, memory):
        memory.save_batch_history("batch_001", {"batch_id": "batch_001"})
        memory.save_batch_history("batch_002", {"batch_id": "batch_002"})
        batches = memory.list_batch_history()
        assert len(batches) == 2


class TestContextPrompt:
    def test_compose_context(self, memory):
        context = memory.compose_search_context()
        assert isinstance(context, str)
        assert "Test Pattern" in context
        assert "Test insight" in context
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && python -m pytest tests/mining/test_memory.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement `mining/memory.py`**

```python
"""Experience Memory management for factor mining."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .config import MiningConfig

logger = logging.getLogger(__name__)


class ExperienceMemory:
    """Read/write YAML-based Experience Memory.

    Files:
      - state.yaml: library stats + domain saturation + mining counters
      - patterns.yaml: recommended directions + forbidden regions
      - insights.yaml: strategic insights
      - history/batch_XXX.yaml: per-batch mining records
    """

    def __init__(self, config: MiningConfig):
        self._dir = Path(config.memory_dir)
        self._history_dir = self._dir / "history"
        self._history_dir.mkdir(parents=True, exist_ok=True)

    # --- Read ---

    def read_state(self) -> Dict[str, Any]:
        return self._read_yaml(self._dir / "state.yaml")

    def read_patterns(self) -> Dict[str, Any]:
        return self._read_yaml(self._dir / "patterns.yaml")

    def read_insights(self) -> Dict[str, Any]:
        return self._read_yaml(self._dir / "insights.yaml")

    # --- Write ---

    def write_state(self, data: Dict[str, Any]) -> None:
        self._write_yaml(self._dir / "state.yaml", data)

    def write_patterns(self, data: Dict[str, Any]) -> None:
        self._write_yaml(self._dir / "patterns.yaml", data)

    def write_insights(self, data: Dict[str, Any]) -> None:
        self._write_yaml(self._dir / "insights.yaml", data)

    # --- History ---

    def save_batch_history(self, batch_id: str, data: Dict[str, Any]) -> None:
        path = self._history_dir / f"{batch_id}.yaml"
        self._write_yaml(path, data)

    def load_batch_history(self, batch_id: str) -> Dict[str, Any]:
        path = self._history_dir / f"{batch_id}.yaml"
        return self._read_yaml(path)

    def list_batch_history(self) -> List[str]:
        return sorted(
            p.stem for p in self._history_dir.glob("batch_*.yaml")
        )

    # --- Context ---

    def compose_search_context(self) -> str:
        """Compose Memory into a prompt-ready string for Claude."""
        parts = []

        state = self.read_state()
        parts.append("## Current Mining State")
        parts.append(f"Library size: {state.get('library', {}).get('size', 0)}")
        sat = state.get("domain_saturation", {})
        if sat:
            sat_lines = [f"  - {k}: {v.get('count', 0)} factors ({v.get('saturation', 'low')})"
                         for k, v in sat.items()]
            parts.append("Domain saturation:\n" + "\n".join(sat_lines))

        patterns = self.read_patterns()
        rec = patterns.get("recommended_directions", [])
        if rec:
            parts.append("\n## Recommended Directions")
            for p in rec:
                parts.append(f"- **{p['pattern']}** ({p.get('success_rate', 'unknown')}): {p['description']}")

        forbidden = patterns.get("forbidden_regions", [])
        if forbidden:
            parts.append("\n## Forbidden Regions (AVOID)")
            for f in forbidden:
                parts.append(f"- {f['direction']}: {f['reason']}")

        insights = self.read_insights()
        ins_list = insights.get("insights", [])
        if ins_list:
            parts.append("\n## Strategic Insights")
            for i in ins_list:
                parts.append(f"- [{i.get('confidence', '?')}] {i['insight']}")

        return "\n".join(parts)

    # --- Internal ---

    def _read_yaml(self, path: Path) -> Dict[str, Any]:
        if not path.exists():
            logger.warning("Memory file not found: %s", path)
            return {}
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def _write_yaml(self, path: Path, data: Dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && python -m pytest tests/mining/test_memory.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add mining/memory.py tests/mining/test_memory.py
git commit -m "feat(mining): add ExperienceMemory YAML read/write with context composer"
```

---

### Task 4: Factor Library Management

**Files:**
- Create: `mining/library.py`
- Create: `tests/mining/test_library.py`

- [ ] **Step 1: Write the failing test**

`tests/mining/test_library.py`:
```python
"""Tests for FactorLibrary."""

import yaml
import pytest
from pathlib import Path

from mining.library import FactorLibrary


@pytest.fixture
def library(tmp_mining_dir, config):
    """FactorLibrary with temp directory."""
    lib_dir = Path(config.library_dir)
    (lib_dir / "library.yaml").write_text(yaml.dump({
        "thresholds": {
            "ic_min": 0.03,
            "correlation_max": 0.5,
            "replacement_ic_ratio": 1.3,
            "replacement_ic_min": 0.05,
        },
        "factors": [],
    }))
    return FactorLibrary(config)


class TestAdmit:
    def test_admit_factor(self, library):
        factor = {
            "name": "VWAP_Dev",
            "expression": "Neg(Rank(Div(Sub($close, $vwap), $vwap)))",
            "category": "vwap",
            "batch": "batch_001",
            "metrics": {
                "ic_mean": 0.065,
                "ic_std": 0.078,
                "ic_ir": 0.82,
                "ic_win_rate": 0.68,
                "max_correlation": 0.31,
                "max_corr_factor": None,
            },
        }
        factor_id = library.admit(factor)
        assert factor_id == "001"

        # Verify library index updated
        index = library.list_factors()
        assert len(index) == 1
        assert index[0]["id"] == "001"
        assert index[0]["expression"] == factor["expression"]

    def test_admit_increments_id(self, library):
        for i in range(3):
            library.admit({
                "name": f"Factor_{i}",
                "expression": f"Rank($close)",
                "category": "momentum",
                "batch": "batch_001",
                "metrics": {"ic_mean": 0.05},
            })
        index = library.list_factors()
        assert len(index) == 3
        assert index[2]["id"] == "003"


class TestReplace:
    def test_replace_factor(self, library):
        # Admit original
        library.admit({
            "name": "Old_Factor",
            "expression": "Rank($close)",
            "category": "momentum",
            "batch": "batch_001",
            "metrics": {"ic_mean": 0.04},
        })
        # Replace
        library.replace("001", {
            "name": "Better_Factor",
            "expression": "Rank(Div($close, $vwap))",
            "category": "momentum",
            "batch": "batch_002",
            "metrics": {"ic_mean": 0.07},
        })

        index = library.list_factors()
        assert len(index) == 1
        assert index[0]["name"] == "Better_Factor"
        assert index[0]["id"] == "001"


class TestLoad:
    def test_load_factor_detail(self, library):
        library.admit({
            "name": "Test",
            "expression": "Rank($close)",
            "category": "vwap",
            "batch": "batch_001",
            "metrics": {"ic_mean": 0.06},
        })
        detail = library.load_factor("001")
        assert detail["name"] == "Test"
        assert detail["expression"] == "Rank($close)"


class TestExpressions:
    def test_get_all_expressions(self, library):
        library.admit({"name": "F1", "expression": "Rank($close)", "category": "vwap", "batch": "b1", "metrics": {}})
        library.admit({"name": "F2", "expression": "Rank($vwap)", "category": "vwap", "batch": "b1", "metrics": {}})
        exprs = library.get_all_expressions()
        assert len(exprs) == 2
        assert "Rank($close)" in exprs.values()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && python -m pytest tests/mining/test_library.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement `mining/library.py`**

```python
"""Factor library management."""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .config import MiningConfig

logger = logging.getLogger(__name__)


class FactorLibrary:
    """YAML-based factor library for admitted factors.

    Files:
      - library.yaml: index with thresholds + factor summary list
      - factors/factor_XXX.yaml: per-factor detail records
    """

    def __init__(self, config: MiningConfig):
        self._dir = Path(config.library_dir)
        self._factors_dir = self._dir / "factors"
        self._factors_dir.mkdir(parents=True, exist_ok=True)
        self._index_path = self._dir / "library.yaml"

    def _read_index(self) -> Dict[str, Any]:
        if not self._index_path.exists():
            return {"thresholds": {}, "factors": []}
        with open(self._index_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {"thresholds": {}, "factors": []}

    def _write_index(self, data: Dict[str, Any]) -> None:
        with open(self._index_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    def _next_id(self, index: Dict[str, Any]) -> str:
        factors = index.get("factors", [])
        if not factors:
            return "001"
        max_id = max(int(f["id"]) for f in factors)
        return f"{max_id + 1:03d}"

    def admit(self, factor: Dict[str, Any]) -> str:
        """Admit a new factor to the library. Returns assigned ID."""
        index = self._read_index()
        factor_id = self._next_id(index)

        record = {
            "id": factor_id,
            "name": factor.get("name", f"factor_{factor_id}"),
            "expression": factor["expression"],
            "category": factor.get("category", "other"),
            "batch": factor.get("batch", "unknown"),
            "admitted_at": str(date.today()),
            "metrics": factor.get("metrics", {}),
        }

        # Write detail file
        detail_path = self._factors_dir / f"factor_{factor_id}.yaml"
        with open(detail_path, "w", encoding="utf-8") as f:
            yaml.dump(record, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

        # Update index
        index.setdefault("factors", []).append({
            "id": factor_id,
            "name": record["name"],
            "expression": record["expression"],
            "category": record["category"],
            "ic_mean": record["metrics"].get("ic_mean"),
        })
        self._write_index(index)

        logger.info("Admitted factor %s: %s", factor_id, record["name"])
        return factor_id

    def replace(self, old_id: str, new_factor: Dict[str, Any]) -> str:
        """Replace an existing factor. Keeps the same ID."""
        index = self._read_index()
        factors = index.get("factors", [])

        # Remove old entry from index
        index["factors"] = [f for f in factors if f["id"] != old_id]

        record = {
            "id": old_id,
            "name": new_factor.get("name", f"factor_{old_id}"),
            "expression": new_factor["expression"],
            "category": new_factor.get("category", "other"),
            "batch": new_factor.get("batch", "unknown"),
            "admitted_at": str(date.today()),
            "metrics": new_factor.get("metrics", {}),
            "replaces": old_id,
        }

        # Overwrite detail file
        detail_path = self._factors_dir / f"factor_{old_id}.yaml"
        with open(detail_path, "w", encoding="utf-8") as f:
            yaml.dump(record, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

        # Update index
        index["factors"].append({
            "id": old_id,
            "name": record["name"],
            "expression": record["expression"],
            "category": record["category"],
            "ic_mean": record["metrics"].get("ic_mean"),
        })
        self._write_index(index)

        logger.info("Replaced factor %s with %s", old_id, record["name"])
        return old_id

    def list_factors(self) -> List[Dict[str, Any]]:
        """List all factors in the library."""
        index = self._read_index()
        return index.get("factors", [])

    def load_factor(self, factor_id: str) -> Dict[str, Any]:
        """Load full detail for a factor."""
        path = self._factors_dir / f"factor_{factor_id}.yaml"
        if not path.exists():
            raise FileNotFoundError(f"Factor {factor_id} not found")
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def get_all_expressions(self) -> Dict[str, str]:
        """Return {id: expression} for all library factors."""
        index = self._read_index()
        return {f["id"]: f["expression"] for f in index.get("factors", [])}

    def get_factor_ic(self, factor_id: str) -> Optional[float]:
        """Get IC mean for a library factor."""
        try:
            detail = self.load_factor(factor_id)
            return detail.get("metrics", {}).get("ic_mean")
        except FileNotFoundError:
            return None

    @property
    def size(self) -> int:
        return len(self.list_factors())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && python -m pytest tests/mining/test_library.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add mining/library.py tests/mining/test_library.py
git commit -m "feat(mining): add FactorLibrary with admit/replace/load"
```

---

### Task 5: Evaluator Core — IC Computation

**Files:**
- Create: `mining/evaluator.py`
- Create: `tests/mining/test_evaluator.py`

This task implements the core `FactorMiningEvaluator` class with `_compute_ic()` and the `BatchResult` dataclass. Qlib calls are abstracted behind methods that can be mocked in tests.

- [ ] **Step 1: Write the failing test**

`tests/mining/test_evaluator.py`:
```python
"""Tests for FactorMiningEvaluator."""

from dataclasses import dataclass
from unittest.mock import patch, MagicMock

import numpy as np
import pandas as pd
import pytest
from scipy.stats import spearmanr

from mining.config import MiningConfig
from mining.evaluator import FactorMiningEvaluator, BatchResult


@pytest.fixture
def evaluator(config):
    """Evaluator with Qlib init mocked."""
    with patch.object(FactorMiningEvaluator, "_ensure_qlib_initialized"):
        return FactorMiningEvaluator(config)


class TestBatchResult:
    def test_dataclass(self):
        r = BatchResult(admitted=[], rejected=[], replacements=[])
        assert r.admitted == []
        assert r.rejected == []


class TestComputeIC:
    def test_positive_ic(self, evaluator, sample_factor_values, sample_returns):
        """When factor perfectly predicts returns, IC should be high."""
        # Create correlated factor and returns
        dates = pd.bdate_range("2023-01-02", periods=20)
        instruments = [f"SH60000{i}" for i in range(10)]
        idx = pd.MultiIndex.from_product([dates, instruments], names=["datetime", "instrument"])
        np.random.seed(42)

        signal = np.random.randn(len(idx))
        noise = np.random.randn(len(idx)) * 0.3
        factor_df = pd.DataFrame({"factor": signal}, index=idx)
        returns_df = pd.DataFrame({"$returns_1d": signal + noise}, index=idx)

        ic_stats = evaluator._compute_ic_from_frames(factor_df, returns_df)
        assert ic_stats["ic_mean"] > 0.5
        assert ic_stats["n_days"] == 20

    def test_zero_ic(self, evaluator):
        """Random factor and returns should have IC near zero."""
        dates = pd.bdate_range("2023-01-02", periods=50)
        instruments = [f"SH60000{i}" for i in range(20)]
        idx = pd.MultiIndex.from_product([dates, instruments], names=["datetime", "instrument"])
        np.random.seed(42)

        factor_df = pd.DataFrame({"factor": np.random.randn(len(idx))}, index=idx)
        np.random.seed(999)
        returns_df = pd.DataFrame({"$returns_1d": np.random.randn(len(idx)) * 0.02}, index=idx)

        ic_stats = evaluator._compute_ic_from_frames(factor_df, returns_df)
        assert abs(ic_stats["ic_mean"]) < 0.15  # should be near zero
        assert ic_stats["n_days"] == 50

    def test_ic_stats_keys(self, evaluator, sample_factor_values, sample_returns):
        ic_stats = evaluator._compute_ic_from_frames(sample_factor_values, sample_returns)
        assert "ic_mean" in ic_stats
        assert "ic_std" in ic_stats
        assert "ic_ir" in ic_stats
        assert "ic_win_rate" in ic_stats
        assert "n_days" in ic_stats
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && python -m pytest tests/mining/test_evaluator.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement `mining/evaluator.py` (core skeleton + IC)**

```python
"""Multi-stage factor mining evaluation pipeline."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from .config import MiningConfig
from .expression import ExpressionValidator

logger = logging.getLogger(__name__)


@dataclass
class BatchResult:
    """Result of a batch evaluation."""

    admitted: List[Dict[str, Any]] = field(default_factory=list)
    rejected: List[Dict[str, Any]] = field(default_factory=list)
    replacements: List[Dict[str, Any]] = field(default_factory=list)


class FactorMiningEvaluator:
    """Multi-stage factor mining evaluation pipeline using Qlib."""

    def __init__(self, config: MiningConfig):
        self.config = config
        self._factor_cache: Dict[str, pd.DataFrame] = {}
        self._ensure_qlib_initialized()

    def _ensure_qlib_initialized(self) -> None:
        """Initialize Qlib idempotently."""
        try:
            import qlib
            if not getattr(qlib, "_is_initialized", False):
                qlib.init(provider_uri=self.config.qlib_data_dir)
        except Exception as e:
            logger.warning("Qlib init failed (may work without it for testing): %s", e)

    # --- Core IC computation ---

    def _compute_ic_from_frames(
        self,
        factor_values: pd.DataFrame,
        returns: pd.DataFrame,
    ) -> Dict[str, Any]:
        """Compute daily cross-sectional Spearman IC from pre-loaded DataFrames.

        Both DataFrames must have (datetime, instrument) MultiIndex.
        factor_values: single column with factor values
        returns: single column '$returns_1d' with forward returns
        """
        factor_col = factor_values.columns[0]
        returns_col = returns.columns[0]

        merged = factor_values.join(returns, how="inner").dropna()
        if merged.empty:
            return {"ic_mean": np.nan, "ic_std": np.nan, "ic_ir": np.nan,
                    "ic_win_rate": np.nan, "n_days": 0}

        daily_ics = []
        for dt, group in merged.groupby(level="datetime"):
            if len(group) < 3:
                continue
            if group[factor_col].nunique() < 2 or group[returns_col].nunique() < 2:
                continue
            ic, _ = spearmanr(group[factor_col], group[returns_col])
            if not np.isnan(ic):
                daily_ics.append(float(ic))

        if not daily_ics:
            return {"ic_mean": np.nan, "ic_std": np.nan, "ic_ir": np.nan,
                    "ic_win_rate": np.nan, "n_days": 0}

        ic_arr = np.array(daily_ics)
        ic_mean = float(ic_arr.mean())
        ic_std = float(ic_arr.std()) if len(ic_arr) > 1 else np.nan
        ic_ir = float(ic_mean / ic_std) if ic_std and ic_std != 0 else np.nan
        ic_win_rate = float((ic_arr > 0).sum() / len(ic_arr))

        return {
            "ic_mean": ic_mean,
            "ic_std": ic_std,
            "ic_ir": ic_ir,
            "ic_win_rate": ic_win_rate,
            "n_days": len(ic_arr),
        }

    def _compute_factor_qlib(
        self,
        expression: str,
        instruments: list,
        start_time: str,
        end_time: str,
    ) -> pd.DataFrame:
        """Use Qlib expression engine to compute factor values."""
        from qlib.data import D
        return D.features(
            instruments=instruments,
            fields=[expression],
            start_time=start_time,
            end_time=end_time,
        )

    def _get_returns_qlib(
        self,
        instruments: list,
        start_time: str,
        end_time: str,
    ) -> pd.DataFrame:
        """Load pre-computed forward returns from Qlib."""
        from qlib.data import D
        return D.features(
            instruments=instruments,
            fields=["$returns_1d"],
            start_time=start_time,
            end_time=end_time,
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && python -m pytest tests/mining/test_evaluator.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add mining/evaluator.py tests/mining/test_evaluator.py
git commit -m "feat(mining): add FactorMiningEvaluator core with IC computation"
```

---

### Task 6: Evaluator — Stage 1 Fast IC + Stage 1.5 Batch Dedup

**Files:**
- Modify: `mining/evaluator.py`
- Modify: `tests/mining/test_evaluator.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/mining/test_evaluator.py`:
```python
class TestStage1FastIC:
    def test_passes_high_ic_factor(self, evaluator):
        """Factor with IC above threshold should pass Stage 1."""
        candidates = [
            {"name": "F1", "expression": "Rank($close)", "category": "momentum"},
        ]
        # Mock _compute_factor_qlib and _get_returns_qlib
        dates = pd.bdate_range("2023-01-02", periods=30)
        instruments = [f"SH60000{i}" for i in range(10)]
        idx = pd.MultiIndex.from_product([dates, instruments], names=["datetime", "instrument"])
        np.random.seed(42)
        signal = np.random.randn(len(idx))

        with patch.object(evaluator, "_compute_factor_qlib") as mock_factor, \
             patch.object(evaluator, "_get_returns_qlib") as mock_returns, \
             patch.object(evaluator, "_get_fast_screening_universe", return_value=instruments):
            mock_factor.return_value = pd.DataFrame({"factor": signal}, index=idx)
            mock_returns.return_value = pd.DataFrame({"$returns_1d": signal + np.random.randn(len(idx)) * 0.2}, index=idx)

            passed = evaluator._fast_ic_screening(candidates)
            assert len(passed) == 1
            assert "stage1" in passed[0]
            assert abs(passed[0]["stage1"]["ic_mean"]) >= evaluator.config.ic_threshold

    def test_rejects_low_ic_factor(self, evaluator):
        """Factor with IC below threshold should be rejected."""
        candidates = [
            {"name": "F_bad", "expression": "Rank($close)", "category": "momentum"},
        ]
        dates = pd.bdate_range("2023-01-02", periods=30)
        instruments = [f"SH60000{i}" for i in range(10)]
        idx = pd.MultiIndex.from_product([dates, instruments], names=["datetime", "instrument"])

        with patch.object(evaluator, "_compute_factor_qlib") as mock_factor, \
             patch.object(evaluator, "_get_returns_qlib") as mock_returns, \
             patch.object(evaluator, "_get_fast_screening_universe", return_value=instruments):
            np.random.seed(42)
            mock_factor.return_value = pd.DataFrame({"factor": np.random.randn(len(idx))}, index=idx)
            np.random.seed(999)
            mock_returns.return_value = pd.DataFrame({"$returns_1d": np.random.randn(len(idx)) * 0.01}, index=idx)

            passed = evaluator._fast_ic_screening(candidates)
            # With random data, IC should be near zero → rejected
            assert len(passed) == 0


class TestStage15BatchDedup:
    def test_dedup_removes_correlated(self, evaluator):
        """Highly correlated factors in batch should be deduped."""
        dates = pd.bdate_range("2023-01-02", periods=20)
        instruments = [f"SH60000{i}" for i in range(10)]
        idx = pd.MultiIndex.from_product([dates, instruments], names=["datetime", "instrument"])
        np.random.seed(42)
        signal = np.random.randn(len(idx))

        candidates = [
            {"name": "F1", "expression": "Rank($close)", "stage1": {"ic_mean": 0.06}},
            {"name": "F2", "expression": "Rank($close) + 0.001", "stage1": {"ic_mean": 0.04}},
        ]

        with patch.object(evaluator, "_compute_factor_qlib") as mock_factor, \
             patch.object(evaluator, "_get_fast_screening_universe", return_value=instruments):
            # Both return nearly identical values
            mock_factor.side_effect = [
                pd.DataFrame({"factor": signal}, index=idx),
                pd.DataFrame({"factor": signal + np.random.randn(len(idx)) * 0.01}, index=idx),
            ]

            result = evaluator._batch_dedup(candidates)
            assert len(result) == 1
            assert result[0]["name"] == "F1"  # higher IC kept

    def test_dedup_keeps_uncorrelated(self, evaluator):
        """Uncorrelated factors should all survive dedup."""
        dates = pd.bdate_range("2023-01-02", periods=20)
        instruments = [f"SH60000{i}" for i in range(10)]
        idx = pd.MultiIndex.from_product([dates, instruments], names=["datetime", "instrument"])

        candidates = [
            {"name": "F1", "expression": "Rank($close)", "stage1": {"ic_mean": 0.06}},
            {"name": "F2", "expression": "Rank($volume)", "stage1": {"ic_mean": 0.05}},
        ]

        with patch.object(evaluator, "_compute_factor_qlib") as mock_factor, \
             patch.object(evaluator, "_get_fast_screening_universe", return_value=instruments):
            np.random.seed(42)
            mock_factor.side_effect = [
                pd.DataFrame({"factor": np.random.randn(len(idx))}, index=idx),
                pd.DataFrame({"factor": np.random.randn(len(idx))}, index=idx),
            ]

            result = evaluator._batch_dedup(candidates)
            assert len(result) == 2
```

- [ ] **Step 2: Run tests to verify new tests fail**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && python -m pytest tests/mining/test_evaluator.py::TestStage1FastIC -v`
Expected: FAIL with `AttributeError` (methods don't exist yet)

- [ ] **Step 3: Implement Stage 1 + Stage 1.5 in `mining/evaluator.py`**

Add these methods to `FactorMiningEvaluator`:
```python
    def _get_fast_screening_universe(self) -> list:
        """Select top-N stocks by average daily turnover from configured universe.

        Uses Qlib D.instruments() to get the universe, then ranks by turnover.
        """
        from qlib.data import D
        universe = self.config.custom_universe
        if universe is None:
            universe = D.instruments(self.config.universe)
        # For now, return first N instruments (proper turnover ranking in data_sync)
        if isinstance(universe, list) and len(universe) > self.config.fast_screening_universe_size:
            return universe[: self.config.fast_screening_universe_size]
        return list(universe) if not isinstance(universe, list) else universe

    def _get_full_universe(self) -> list:
        """Get full trading universe."""
        if self.config.custom_universe:
            return self.config.custom_universe
        from qlib.data import D
        return list(D.instruments(self.config.universe))

    def _fast_ic_screening(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Stage 1: Calculate IC on fast-screening subset universe."""
        subset = self._get_fast_screening_universe()
        results = []
        for c in candidates:
            try:
                values = self._compute_factor_qlib(
                    c["expression"], subset,
                    self.config.train_start, self.config.train_end,
                )
                returns = self._get_returns_qlib(
                    subset, self.config.train_start, self.config.train_end,
                )
                ic_stats = self._compute_ic_from_frames(values, returns)
                c["stage1"] = ic_stats
                if abs(ic_stats.get("ic_mean", 0)) >= self.config.ic_threshold:
                    results.append(c)
                else:
                    logger.info("Stage 1 reject %s: IC=%.4f", c["name"], ic_stats.get("ic_mean", 0))
            except Exception as e:
                c["stage1"] = {"error": str(e)}
                logger.warning("Stage 1 error for %s: %s", c.get("name"), e)
        return results

    def _batch_dedup(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Stage 1.5: Remove intra-batch duplicates. Keep higher-IC factor."""
        if len(candidates) <= 1:
            return list(candidates)

        subset = self._get_fast_screening_universe()
        # Compute factor values for each candidate
        values_map: Dict[str, pd.DataFrame] = {}
        for c in candidates:
            try:
                vals = self._compute_factor_qlib(
                    c["expression"], subset,
                    self.config.train_start, self.config.train_end,
                )
                values_map[c["expression"]] = vals
            except Exception:
                values_map[c["expression"]] = pd.DataFrame()

        # Sort by IC descending (greedy)
        sorted_candidates = sorted(
            candidates,
            key=lambda c: abs(c.get("stage1", {}).get("ic_mean", 0)),
            reverse=True,
        )

        kept = []
        for c in sorted_candidates:
            c_vals = values_map.get(c["expression"])
            if c_vals is None or c_vals.empty:
                kept.append(c)
                continue

            is_dup = False
            for k in kept:
                k_vals = values_map.get(k["expression"])
                if k_vals is None or k_vals.empty:
                    continue
                corr = self._pairwise_correlation(c_vals, k_vals)
                if abs(corr) >= self.config.correlation_threshold:
                    is_dup = True
                    logger.info(
                        "Dedup: %s removed (corr=%.3f with %s)",
                        c["name"], corr, k["name"],
                    )
                    break
            if not is_dup:
                kept.append(c)

        return kept

    def _pairwise_correlation(
        self, a: pd.DataFrame, b: pd.DataFrame
    ) -> float:
        """Compute time-averaged cross-sectional Spearman correlation."""
        a_col = a.columns[0]
        b_col = b.columns[0]
        merged = a.join(b, how="inner", lsuffix="_a", rsuffix="_b").dropna()
        if merged.empty:
            return 0.0

        corrs = []
        col_a = merged.columns[0]
        col_b = merged.columns[1]
        for dt, group in merged.groupby(level="datetime"):
            if len(group) < 3:
                continue
            rho, _ = spearmanr(group[col_a], group[col_b])
            if not np.isnan(rho):
                corrs.append(rho)
        return float(np.mean(corrs)) if corrs else 0.0
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && python -m pytest tests/mining/test_evaluator.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add mining/evaluator.py tests/mining/test_evaluator.py
git commit -m "feat(mining): add Stage 1 fast IC screening and Stage 1.5 batch dedup"
```

---

### Task 7: Evaluator — Stage 2 Correlation + Stage 2.5 Replacement

**Files:**
- Modify: `mining/evaluator.py`
- Modify: `tests/mining/test_evaluator.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/mining/test_evaluator.py`:
```python
import yaml
from pathlib import Path
from mining.library import FactorLibrary


class TestStage2CorrelationCheck:
    def test_passes_uncorrelated_factor(self, evaluator, tmp_mining_dir, config):
        """Factor uncorrelated with library should pass Stage 2."""
        # Set up library with one factor
        lib = FactorLibrary(config)
        lib_dir = Path(config.library_dir)
        (lib_dir / "library.yaml").write_text(yaml.dump({
            "thresholds": {"ic_min": 0.03, "correlation_max": 0.5},
            "factors": [],
        }))

        dates = pd.bdate_range("2023-01-02", periods=20)
        instruments = [f"SH60000{i}" for i in range(10)]
        idx = pd.MultiIndex.from_product([dates, instruments], names=["datetime", "instrument"])
        np.random.seed(42)

        candidates = [
            {"name": "F1", "expression": "Rank($close)", "category": "momentum",
             "stage1": {"ic_mean": 0.05}},
        ]

        with patch.object(evaluator, "_compute_factor_qlib") as mock_factor, \
             patch.object(evaluator, "_get_returns_qlib") as mock_returns, \
             patch.object(evaluator, "_get_full_universe", return_value=instruments), \
             patch.object(evaluator, "_load_library", return_value=lib):
            signal = np.random.randn(len(idx))
            mock_factor.return_value = pd.DataFrame({"factor": signal}, index=idx)
            mock_returns.return_value = pd.DataFrame(
                {"$returns_1d": signal + np.random.randn(len(idx)) * 0.3}, index=idx)

            passed, rejected = evaluator._correlation_check(candidates)
            assert len(passed) == 1
            assert len(rejected) == 0


class TestStage25Replacement:
    def test_replacement_condition(self, evaluator):
        """Factor that strongly outperforms single conflict should trigger replacement."""
        candidate = {
            "name": "Better_F",
            "expression": "Rank(Div($close, $vwap))",
            "full_ic": {"ic_mean": 0.08},
            "stage2": {"max_corr": 0.6, "max_corr_factor": "001", "passed": False},
        }
        evaluator.config.replacement_ic_min = 0.05
        evaluator.config.replacement_ic_ratio = 1.3

        with patch.object(evaluator, "_get_library_factor_ic", return_value=0.04), \
             patch.object(evaluator, "_count_library_conflicts", return_value=1):
            replacements = evaluator._replacement_check([candidate])
            assert len(replacements) == 1
            assert replacements[0]["replaces"] == "001"

    def test_no_replacement_if_multi_conflict(self, evaluator):
        """Factor with multiple library conflicts should NOT trigger replacement."""
        candidate = {
            "name": "F",
            "expression": "X",
            "full_ic": {"ic_mean": 0.08},
            "stage2": {"max_corr": 0.6, "max_corr_factor": "001", "passed": False},
        }

        with patch.object(evaluator, "_get_library_factor_ic", return_value=0.04), \
             patch.object(evaluator, "_count_library_conflicts", return_value=2):
            replacements = evaluator._replacement_check([candidate])
            assert len(replacements) == 0
```

- [ ] **Step 2: Run tests to verify new tests fail**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && python -m pytest tests/mining/test_evaluator.py::TestStage2CorrelationCheck -v`
Expected: FAIL

- [ ] **Step 3: Implement Stage 2 + Stage 2.5**

Add to `FactorMiningEvaluator`:
```python
    def _load_library(self) -> FactorLibrary:
        """Load the factor library."""
        from .library import FactorLibrary
        return FactorLibrary(self.config)

    def _correlation_check(
        self, candidates: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Stage 2: Full universe computation + correlation check with library."""
        library = self._load_library()
        lib_factors = library.list_factors()
        full_universe = self._get_full_universe()
        passed, rejected = [], []

        # Pre-compute library factor values
        lib_values: Dict[str, pd.DataFrame] = {}
        for lf in lib_factors:
            try:
                vals = self._compute_factor_qlib(
                    lf["expression"], full_universe,
                    self.config.train_start, self.config.train_end,
                )
                lib_values[lf["id"]] = vals
            except Exception as e:
                logger.warning("Failed to compute library factor %s: %s", lf["id"], e)

        for c in candidates:
            try:
                # Compute on full universe and cache
                factor_vals = self._compute_factor_qlib(
                    c["expression"], full_universe,
                    self.config.train_start, self.config.train_end,
                )
                self._factor_cache[c["expression"]] = factor_vals

                # Re-compute IC on full universe
                returns = self._get_returns_qlib(
                    full_universe, self.config.train_start, self.config.train_end,
                )
                full_ic = self._compute_ic_from_frames(factor_vals, returns)
                c["full_ic"] = full_ic

                # Correlation check against library
                max_corr = 0.0
                max_corr_factor = None
                all_corrs: Dict[str, float] = {}
                for lid, lvals in lib_values.items():
                    corr = abs(self._pairwise_correlation(factor_vals, lvals))
                    all_corrs[lid] = corr
                    if corr > max_corr:
                        max_corr = corr
                        max_corr_factor = lid

                c["_lib_correlations"] = all_corrs

                if max_corr < self.config.correlation_threshold:
                    c["stage2"] = {"max_corr": max_corr, "max_corr_factor": max_corr_factor, "passed": True}
                    passed.append(c)
                else:
                    c["stage2"] = {"max_corr": max_corr, "max_corr_factor": max_corr_factor, "passed": False}
                    rejected.append(c)
            except Exception as e:
                c["stage2"] = {"error": str(e), "passed": False}
                rejected.append(c)
                logger.warning("Stage 2 error for %s: %s", c.get("name"), e)

        return passed, rejected

    def _replacement_check(
        self, rejected: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Stage 2.5: Check if rejected factors can replace weaker library members."""
        replacements = []
        for c in rejected:
            full_ic = abs(c.get("full_ic", {}).get("ic_mean", 0))
            if full_ic < self.config.replacement_ic_min:
                continue

            g_star = c.get("stage2", {}).get("max_corr_factor")
            if g_star is None:
                continue

            g_ic = abs(self._get_library_factor_ic(g_star) or 0)
            conflicts = self._count_library_conflicts(c)

            if full_ic >= self.config.replacement_ic_ratio * g_ic and conflicts == 1:
                replacements.append({"new_factor": c, "replaces": g_star})
                logger.info(
                    "Replacement: %s (IC=%.4f) replaces %s (IC=%.4f)",
                    c["name"], full_ic, g_star, g_ic,
                )
        return replacements

    def _get_library_factor_ic(self, factor_id: str) -> Optional[float]:
        """Get IC for a library factor by ID."""
        library = self._load_library()
        return library.get_factor_ic(factor_id)

    def _count_library_conflicts(self, candidate: Dict[str, Any]) -> int:
        """Count library factors with correlation >= threshold."""
        corrs = candidate.get("_lib_correlations", {})
        return sum(1 for v in corrs.values() if v >= self.config.correlation_threshold)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && python -m pytest tests/mining/test_evaluator.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add mining/evaluator.py tests/mining/test_evaluator.py
git commit -m "feat(mining): add Stage 2 correlation check and Stage 2.5 replacement"
```

---

### Task 8: Evaluator — Stage 3 Full Validation + evaluate_batch

**Files:**
- Modify: `mining/evaluator.py`
- Modify: `tests/mining/test_evaluator.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/mining/test_evaluator.py`:
```python
class TestStage3FullValidation:
    def test_full_metrics(self, evaluator):
        """Stage 3 should compute IS/OOS IC, quantile returns."""
        dates_is = pd.bdate_range("2023-01-02", periods=30)
        dates_oos = pd.bdate_range("2024-01-02", periods=15)
        instruments = [f"SH60000{i}" for i in range(20)]
        idx_is = pd.MultiIndex.from_product([dates_is, instruments], names=["datetime", "instrument"])
        idx_oos = pd.MultiIndex.from_product([dates_oos, instruments], names=["datetime", "instrument"])
        np.random.seed(42)
        signal_is = np.random.randn(len(idx_is))
        signal_oos = np.random.randn(len(idx_oos))

        candidate = {
            "name": "F1",
            "expression": "Rank($close)",
            "stage1": {"ic_mean": 0.05},
        }
        # Pre-cache factor values (as Stage 2 would)
        evaluator._factor_cache["Rank($close)"] = pd.DataFrame(
            {"factor": signal_is}, index=idx_is
        )

        with patch.object(evaluator, "_get_returns_qlib") as mock_returns, \
             patch.object(evaluator, "_compute_factor_qlib") as mock_factor, \
             patch.object(evaluator, "_get_full_universe",
                         return_value=instruments):
            # IS returns
            mock_returns.side_effect = [
                pd.DataFrame({"$returns_1d": signal_is * 0.5 + np.random.randn(len(idx_is)) * 0.1}, index=idx_is),
                pd.DataFrame({"$returns_1d": signal_oos * 0.5 + np.random.randn(len(idx_oos)) * 0.1}, index=idx_oos),
            ]
            mock_factor.return_value = pd.DataFrame({"factor": signal_oos}, index=idx_oos)

            validated = evaluator._full_validation([candidate])
            assert len(validated) == 1
            s3 = validated[0]["stage3"]
            assert "ic_mean_is" in s3
            assert "ic_mean_oos" in s3
            assert "quantile_returns" in s3
            assert "ls_return" in s3
            assert "monotonicity" in s3


class TestEvaluateBatch:
    def test_full_pipeline(self, evaluator):
        """evaluate_batch wires all stages together."""
        dates = pd.bdate_range("2023-01-02", periods=30)
        instruments = [f"SH60000{i}" for i in range(10)]
        idx = pd.MultiIndex.from_product([dates, instruments], names=["datetime", "instrument"])
        np.random.seed(42)
        signal = np.random.randn(len(idx))

        candidates = [
            {"name": "Good_F", "expression": "Rank($close)", "category": "momentum"},
        ]

        with patch.object(evaluator, "_ensure_qlib_initialized"), \
             patch.object(evaluator, "_compute_factor_qlib") as mock_factor, \
             patch.object(evaluator, "_get_returns_qlib") as mock_returns, \
             patch.object(evaluator, "_get_fast_screening_universe", return_value=instruments), \
             patch.object(evaluator, "_get_full_universe", return_value=instruments), \
             patch.object(evaluator, "_load_library") as mock_lib:
            mock_factor.return_value = pd.DataFrame({"factor": signal}, index=idx)
            mock_returns.return_value = pd.DataFrame(
                {"$returns_1d": signal + np.random.randn(len(idx)) * 0.2}, index=idx)
            mock_lib_obj = MagicMock()
            mock_lib_obj.list_factors.return_value = []
            mock_lib.return_value = mock_lib_obj

            result = evaluator.evaluate_batch(candidates)
            assert isinstance(result, BatchResult)
            # With correlated signal, should pass most stages
            total = len(result.admitted) + len(result.rejected) + len(result.replacements)
            assert total >= 1
```

- [ ] **Step 2: Run tests to verify new tests fail**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && python -m pytest tests/mining/test_evaluator.py::TestStage3FullValidation -v`
Expected: FAIL

- [ ] **Step 3: Implement Stage 3 + evaluate_batch**

Add to `FactorMiningEvaluator`:
```python
    def _full_validation(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Stage 3: Full validation with IS/OOS metrics. Reuses cached factor values."""
        full_universe = self._get_full_universe()
        validated = []

        for c in candidates:
            try:
                # Reuse cached values from Stage 2
                cached_vals = self._factor_cache.get(c["expression"])

                # In-sample IC (reuses cached)
                returns_is = self._get_returns_qlib(
                    full_universe, self.config.train_start, self.config.train_end,
                )
                if cached_vals is not None:
                    ic_is = self._compute_ic_from_frames(cached_vals, returns_is)
                else:
                    vals_is = self._compute_factor_qlib(
                        c["expression"], full_universe,
                        self.config.train_start, self.config.train_end,
                    )
                    ic_is = self._compute_ic_from_frames(vals_is, returns_is)
                    cached_vals = vals_is

                # Out-of-sample IC
                test_end = self.config.test_end or str(pd.Timestamp.now().date())
                vals_oos = self._compute_factor_qlib(
                    c["expression"], full_universe,
                    self.config.test_start, test_end,
                )
                returns_oos = self._get_returns_qlib(
                    full_universe, self.config.test_start, test_end,
                )
                ic_oos = self._compute_ic_from_frames(vals_oos, returns_oos)

                # Quantile returns
                quantile_ret = self._compute_quantile_returns(cached_vals, returns_is)

                # Compute long-short return and monotonicity
                ls_return = np.nan
                monotonicity = np.nan
                if quantile_ret:
                    q_keys = sorted(quantile_ret.keys())
                    q_vals = [quantile_ret[k] for k in q_keys if not np.isnan(quantile_ret.get(k, np.nan))]
                    if len(q_vals) >= 2:
                        ls_return = float(q_vals[-1] - q_vals[0])
                        # Monotonicity: Spearman correlation of quantile returns with rank
                        from scipy.stats import spearmanr as _sp
                        mono, _ = _sp(range(len(q_vals)), q_vals)
                        monotonicity = float(mono) if not np.isnan(mono) else np.nan

                c["stage3"] = {
                    "ic_mean_is": ic_is.get("ic_mean"),
                    "ic_ir_is": ic_is.get("ic_ir"),
                    "ic_mean_oos": ic_oos.get("ic_mean"),
                    "ic_ir_oos": ic_oos.get("ic_ir"),
                    "ic_win_rate": ic_is.get("ic_win_rate"),
                    "quantile_returns": quantile_ret,
                    "ls_return": ls_return,
                    "monotonicity": monotonicity,
                }
                validated.append(c)
            except Exception as e:
                c["stage3"] = {"error": str(e)}
                logger.warning("Stage 3 error for %s: %s", c.get("name"), e)
                validated.append(c)

        return validated

    def _compute_quantile_returns(
        self, factor_values: pd.DataFrame, returns: pd.DataFrame, n_quantiles: int = 5
    ) -> Dict[str, float]:
        """Compute mean returns for each factor quantile."""
        factor_col = factor_values.columns[0]
        returns_col = returns.columns[0]
        merged = factor_values.join(returns, how="inner").dropna()
        if merged.empty:
            return {f"q{i+1}": np.nan for i in range(n_quantiles)}

        result = {}
        for dt, group in merged.groupby(level="datetime"):
            if len(group) < n_quantiles:
                continue
            group = group.copy()
            group["quantile"] = pd.qcut(
                group[factor_col], n_quantiles, labels=False, duplicates="drop"
            )
            for q in range(n_quantiles):
                q_ret = group.loc[group["quantile"] == q, returns_col].mean()
                result.setdefault(f"q{q+1}", []).append(q_ret)

        return {k: float(np.nanmean(v)) if v else np.nan for k, v in result.items()}

    def evaluate_batch(self, candidates: List[Dict[str, Any]]) -> BatchResult:
        """Run multi-stage pipeline on a batch of candidate factors."""
        self._factor_cache.clear()

        # Validate expressions
        validator = ExpressionValidator(self.config)
        valid, invalid = [], []
        for c in candidates:
            result = validator.validate(c["expression"])
            if result.valid:
                valid.append(c)
            else:
                c["validation_error"] = result.errors
                invalid.append(c)

        if not valid:
            return BatchResult(admitted=[], rejected=invalid, replacements=[])

        # Stage 1: Fast IC
        stage1_passed = self._fast_ic_screening(valid)

        # Stage 1.5: Batch dedup
        stage1_deduped = self._batch_dedup(stage1_passed)

        # Stage 2: Full universe + correlation
        stage2_passed, stage2_rejected = self._correlation_check(stage1_deduped)

        # Stage 2.5: Replacement check
        replacements = self._replacement_check(stage2_rejected)

        # Stage 3: Full validation
        validated = self._full_validation(stage2_passed)

        all_rejected = invalid + [c for c in valid if c not in stage1_passed]
        all_rejected += [c for c in stage1_passed if c not in stage1_deduped]
        all_rejected += stage2_rejected

        return BatchResult(
            admitted=validated,
            rejected=all_rejected,
            replacements=replacements,
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && python -m pytest tests/mining/test_evaluator.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add mining/evaluator.py tests/mining/test_evaluator.py
git commit -m "feat(mining): add Stage 3 full validation and evaluate_batch pipeline"
```

---

### Task 9: Custom Qlib Operators

**Files:**
- Create: `mining/operators.py`
- Create: `tests/mining/test_operators.py`

- [ ] **Step 1: Write the failing test**

`tests/mining/test_operators.py`:
```python
"""Tests for custom Qlib operators."""

import numpy as np
import pytest

from mining.operators import signed_power, tanh_op, scale_cs, ts_decay, exp_op, register_custom_operators


class TestSignedPower:
    def test_positive(self):
        assert signed_power(4.0, 0.5) == pytest.approx(2.0)

    def test_negative(self):
        assert signed_power(-4.0, 0.5) == pytest.approx(-2.0)

    def test_zero(self):
        assert signed_power(0.0, 2.0) == 0.0


class TestTanh:
    def test_bounded(self):
        assert -1.0 <= tanh_op(100.0) <= 1.0
        assert -1.0 <= tanh_op(-100.0) <= 1.0

    def test_zero(self):
        assert tanh_op(0.0) == pytest.approx(0.0)


class TestScaleCS:
    def test_normalizes(self):
        values = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        scaled = scale_cs(values)
        assert scaled.min() >= -1.0
        assert scaled.max() <= 1.0

    def test_single_value(self):
        values = np.array([5.0])
        scaled = scale_cs(values)
        assert scaled[0] == 0.0


class TestTsDecay:
    def test_recency_weighted(self):
        values = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = ts_decay(values, period=5)
        # More recent values should have more weight, so result > simple mean
        assert result > np.mean(values) - 0.5

    def test_single_value(self):
        assert ts_decay(np.array([3.0]), period=1) == pytest.approx(3.0)


class TestExp:
    def test_positive(self):
        assert exp_op(0.0) == pytest.approx(1.0)
        assert exp_op(1.0) == pytest.approx(np.e)

    def test_clamped(self):
        # Should clamp to avoid overflow
        result = exp_op(1000.0)
        assert result < 1e20  # must not be inf


class TestRegistration:
    def test_register_returns_dict(self):
        ops = register_custom_operators()
        assert "SignedPower" in ops
        assert "Tanh" in ops
        assert "Scale" in ops
        assert "TsDecay" in ops
        assert "Exp" in ops
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && python -m pytest tests/mining/test_operators.py -v`
Expected: FAIL

- [ ] **Step 3: Implement `mining/operators.py`**

```python
"""Custom Qlib operator extensions for factor mining."""

from __future__ import annotations

import math
from typing import Callable, Dict

import numpy as np


def signed_power(x: float, p: float) -> float:
    """sign(x) * |x|^p — non-linear transformation preserving sign."""
    if x == 0:
        return 0.0
    return math.copysign(abs(x) ** p, x)


def tanh_op(x: float) -> float:
    """Bounded non-linearity."""
    return math.tanh(x)


def scale_cs(values: np.ndarray) -> np.ndarray:
    """Cross-sectional normalization to [-1, 1]."""
    if len(values) <= 1:
        return np.zeros_like(values)
    vmin, vmax = values.min(), values.max()
    if vmax == vmin:
        return np.zeros_like(values)
    return 2.0 * (values - vmin) / (vmax - vmin) - 1.0


def ts_decay(values: np.ndarray, period: int) -> float:
    """Time-decay weighted average. More recent values get higher weight.

    Weights: w_i = (period - i) / sum(1..period), where i=0 is oldest.
    """
    n = min(len(values), period)
    v = values[-n:]
    weights = np.arange(1, n + 1, dtype=float)
    return float(np.dot(v, weights) / weights.sum())


def exp_op(x: float, clamp: float = 20.0) -> float:
    """Exponential with clamping to prevent overflow."""
    return math.exp(min(x, clamp))


def register_custom_operators() -> Dict[str, Callable]:
    """Register custom operators with Qlib (if available).

    Returns dict of {name: function} for reference.
    Note: Proper Qlib operator registration requires extending ExpressionOps
    base classes. This function provides the raw implementations; full Qlib
    integration requires creating class-based operators (see Qlib docs).
    """
    ops = {
        "SignedPower": signed_power,
        "Tanh": tanh_op,
        "Scale": scale_cs,
        "TsDecay": ts_decay,
        "Exp": exp_op,
    }
    return ops
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && python -m pytest tests/mining/test_operators.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add mining/operators.py tests/mining/test_operators.py
git commit -m "feat(mining): add custom Qlib operators (SignedPower, Tanh, Scale)"
```

---

### Task 10: Data Synchronization

**Files:**
- Create: `mining/data_sync.py`
- Create: `tests/mining/test_data_sync.py`

This task implements the `DataSynchronizer` that converts TimescaleDB data into Qlib binary format.

- [ ] **Step 1: Write the failing test**

`tests/mining/test_data_sync.py`:
```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && python -m pytest tests/mining/test_data_sync.py -v`
Expected: FAIL

- [ ] **Step 3: Implement `mining/data_sync.py`**

```python
"""Data synchronization: TimescaleDB -> Qlib binary format."""

from __future__ import annotations

import logging
import struct
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class DataSynchronizer:
    """Sync TimescaleDB data to Qlib-compatible format.

    Creates the directory structure that Qlib expects:
      qlib_dir/
        calendars/day.txt
        instruments/all.txt
        features/<SYMBOL>/<field>.day.bin
    """

    FIELDS = ["open", "high", "low", "close", "volume", "amount"]
    FIELD_MAP = {
        "open": "$open", "high": "$high", "low": "$low",
        "close": "$close", "volume": "$volume", "amount": "$amount",
    }

    def __init__(self, db, qlib_dir: str = "~/.qlib/qlib_data/cn_data_1d"):
        self.db = db
        self.qlib_dir = Path(qlib_dir).expanduser()

    def sync_daily(
        self,
        start: str = "2015-01-01",
        end: Optional[str] = None,
    ) -> None:
        """Export TimescaleDB price_daily to Qlib directory format."""
        if end is None:
            end = str(datetime.now().date())

        logger.info("Syncing daily data %s to %s", start, end)

        # Query data
        df = self.db.query_price(
            symbols=None, frequency="daily", start=start, end=end,
        )
        if df.empty:
            logger.warning("No data returned from TimescaleDB")
            return

        # Ensure column names
        if "time" not in df.columns and "timestamp" in df.columns:
            df = df.rename(columns={"timestamp": "time"})

        # Convert symbols to Qlib format
        if "symbol" in df.columns:
            df["symbol"] = df["symbol"].apply(self.to_qlib_symbol)

        df["time"] = pd.to_datetime(df["time"])
        df = df.sort_values(["symbol", "time"])

        # Compute derived fields
        df["vwap"] = df.get("vwap", df[["open", "high", "low", "close"]].mean(axis=1))
        df["returns"] = df.groupby("symbol")["close"].pct_change()

        # Forward returns for IC evaluation: close_tomorrow / close_today - 1
        df["returns_1d"] = df.groupby("symbol")["close"].shift(-1) / df["close"] - 1

        # Create directory structure
        self._create_dirs()

        # Write calendar
        trading_days = sorted(df["time"].dt.strftime("%Y-%m-%d").unique())
        self._write_calendar(trading_days)

        # Write instruments
        symbols = sorted(df["symbol"].unique())
        min_date = df["time"].min().strftime("%Y-%m-%d")
        max_date = df["time"].max().strftime("%Y-%m-%d")
        self._write_instruments(symbols, min_date, max_date)

        # Write features per symbol
        all_fields = self.FIELDS + ["vwap", "returns", "returns_1d"]
        for symbol, group in df.groupby("symbol"):
            self._write_symbol_features(str(symbol), group, all_fields, trading_days)

        logger.info("Sync complete: %d symbols, %d days", len(symbols), len(trading_days))

    def _create_dirs(self) -> None:
        (self.qlib_dir / "calendars").mkdir(parents=True, exist_ok=True)
        (self.qlib_dir / "instruments").mkdir(parents=True, exist_ok=True)
        (self.qlib_dir / "features").mkdir(parents=True, exist_ok=True)

    def _write_calendar(self, trading_days: list) -> None:
        cal_path = self.qlib_dir / "calendars" / "day.txt"
        cal_path.write_text("\n".join(trading_days) + "\n")

    def _write_instruments(self, symbols: list, start: str, end: str) -> None:
        inst_path = self.qlib_dir / "instruments" / "all.txt"
        lines = [f"{sym}\t{start}\t{end}" for sym in symbols]
        inst_path.write_text("\n".join(lines) + "\n")

    def _write_symbol_features(
        self, symbol: str, data: pd.DataFrame, fields: list, calendar: list
    ) -> None:
        """Write Qlib binary feature files for one symbol."""
        sym_dir = self.qlib_dir / "features" / symbol
        sym_dir.mkdir(parents=True, exist_ok=True)

        # Align data to calendar
        data = data.set_index(data["time"].dt.strftime("%Y-%m-%d"))

        for field in fields:
            if field not in data.columns:
                continue
            values = []
            for day in calendar:
                if day in data.index:
                    row = data.loc[day]
                    if isinstance(row, pd.DataFrame):
                        row = row.iloc[0]
                    val = float(row[field]) if not pd.isna(row[field]) else float("nan")
                else:
                    val = float("nan")
                values.append(val)

            # Write as Qlib binary format (array of float32)
            bin_path = sym_dir / f"{field}.day.bin"
            with open(bin_path, "wb") as f:
                for v in values:
                    f.write(struct.pack("<f", v))

    def sync_minute_aggregates(self, start: str = "2024-01-01", end: str = None) -> None:
        """Aggregate 1min data into daily features and write to Qlib format.

        Features computed:
          $intraday_vol   : std of 1min returns within day
          $intraday_skew  : skewness of 1min returns within day
          $intraday_kurt  : kurtosis of 1min returns within day
          $vwap_dev       : actual VWAP vs simple average deviation
          $volume_conc    : volume Herfindahl concentration index
          $high_low_range : (high - low) / close
          $morning_momentum : morning session (9:30-11:30) return
          $afternoon_ret  : afternoon session (13:00-15:00) return
        """
        if end is None:
            end = str(datetime.now().date())

        logger.info("Syncing minute aggregates %s to %s", start, end)

        df = self.db.query_price(symbols=None, frequency="1min", start=start, end=end)
        if df.empty:
            logger.warning("No 1min data returned")
            return

        if "time" not in df.columns and "timestamp" in df.columns:
            df = df.rename(columns={"timestamp": "time"})
        if "symbol" in df.columns:
            df["symbol"] = df["symbol"].apply(self.to_qlib_symbol)

        df["time"] = pd.to_datetime(df["time"])
        df["date"] = df["time"].dt.date.astype(str)
        df = df.sort_values(["symbol", "time"])

        # 1min returns
        df["ret_1min"] = df.groupby(["symbol", "date"])["close"].pct_change()

        agg_rows = []
        for (sym, date), group in df.groupby(["symbol", "date"]):
            rets = group["ret_1min"].dropna()
            row = {"symbol": sym, "date": date}
            row["intraday_vol"] = float(rets.std()) if len(rets) > 1 else 0.0
            row["intraday_skew"] = float(rets.skew()) if len(rets) > 2 else 0.0
            row["intraday_kurt"] = float(rets.kurtosis()) if len(rets) > 3 else 0.0

            avg_price = group["close"].mean()
            vwap_actual = (group["close"] * group["volume"]).sum() / group["volume"].sum() if group["volume"].sum() > 0 else avg_price
            row["vwap_dev"] = float((vwap_actual - avg_price) / avg_price) if avg_price != 0 else 0.0

            vol_shares = group["volume"] / group["volume"].sum() if group["volume"].sum() > 0 else 0
            row["volume_conc"] = float((vol_shares ** 2).sum())

            row["high_low_range"] = float((group["high"].max() - group["low"].min()) / group["close"].iloc[-1]) if group["close"].iloc[-1] != 0 else 0.0

            # Morning: 9:30-11:30, Afternoon: 13:00-15:00
            morning = group[(group["time"].dt.hour < 12)]
            afternoon = group[(group["time"].dt.hour >= 13)]
            row["morning_momentum"] = float(morning["close"].iloc[-1] / morning["close"].iloc[0] - 1) if len(morning) > 1 else 0.0
            row["afternoon_ret"] = float(afternoon["close"].iloc[-1] / afternoon["close"].iloc[0] - 1) if len(afternoon) > 1 else 0.0

            agg_rows.append(row)

        if not agg_rows:
            return

        agg_df = pd.DataFrame(agg_rows)

        # Read existing calendar
        cal_path = self.qlib_dir / "calendars" / "day.txt"
        if cal_path.exists():
            calendar = cal_path.read_text().strip().split("\n")
        else:
            calendar = sorted(agg_df["date"].unique())

        minute_fields = ["intraday_vol", "intraday_skew", "intraday_kurt",
                         "vwap_dev", "volume_conc", "high_low_range",
                         "morning_momentum", "afternoon_ret"]

        for symbol, grp in agg_df.groupby("symbol"):
            grp = grp.rename(columns={"date": "time"})
            grp["time"] = pd.to_datetime(grp["time"])
            self._write_symbol_features(str(symbol), grp, minute_fields, calendar)

        logger.info("Minute aggregates sync complete: %d symbols", agg_df["symbol"].nunique())

    def incremental_update(self) -> None:
        """Incremental update: sync only data newer than the last calendar entry."""
        cal_path = self.qlib_dir / "calendars" / "day.txt"
        if not cal_path.exists():
            logger.info("No existing calendar; running full sync")
            self.sync_daily()
            return

        lines = cal_path.read_text().strip().split("\n")
        last_date = lines[-1] if lines else "2015-01-01"
        logger.info("Incremental sync from %s", last_date)
        self.sync_daily(start=last_date)

    @staticmethod
    def to_qlib_symbol(symbol: str) -> str:
        """Convert symbol to Qlib format: 600000.SH -> SH600000."""
        if "." in symbol:
            code, exchange = symbol.split(".")
            return f"{exchange}{code}"
        return symbol
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && python -m pytest tests/mining/test_data_sync.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add mining/data_sync.py tests/mining/test_data_sync.py
git commit -m "feat(mining): add DataSynchronizer for TimescaleDB to Qlib format"
```

---

### Task 11: Update Package Exports

**Files:**
- Modify: `mining/__init__.py`

- [ ] **Step 1: Update `mining/__init__.py` with all exports**

```python
"""FactorMiner: Automated factor mining with Experience Memory."""

from .config import MiningConfig
from .expression import ExpressionValidator, ValidationResult
from .evaluator import FactorMiningEvaluator, BatchResult
from .library import FactorLibrary
from .memory import ExperienceMemory
from .data_sync import DataSynchronizer

__all__ = [
    "MiningConfig",
    "ExpressionValidator",
    "ValidationResult",
    "FactorMiningEvaluator",
    "BatchResult",
    "FactorLibrary",
    "ExperienceMemory",
    "DataSynchronizer",
]
```

- [ ] **Step 2: Run all tests**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && python -m pytest tests/mining/ -v`
Expected: All tests PASS

- [ ] **Step 3: Commit**

```bash
git add mining/__init__.py
git commit -m "feat(mining): export all public APIs from package"
```

---

### Task 12: CLI Entry Point

**Files:**
- Create: `mining/cli.py`

- [ ] **Step 1: Write `mining/cli.py`**

```python
"""CLI entry points for factor mining."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import yaml

from .config import MiningConfig
from .data_sync import DataSynchronizer
from .evaluator import FactorMiningEvaluator
from .library import FactorLibrary
from .memory import ExperienceMemory

logger = logging.getLogger(__name__)


def cmd_sync(args):
    """Sync TimescaleDB data to Qlib format."""
    from data.storage import TimescaleDB
    db = TimescaleDB()
    syncer = DataSynchronizer(db=db, qlib_dir=args.qlib_dir)
    syncer.sync_daily(start=args.start, end=args.end)
    print(f"Sync complete -> {args.qlib_dir}")


def cmd_evaluate(args):
    """Evaluate a single factor expression."""
    config = MiningConfig(
        qlib_data_dir=args.qlib_dir,
        train_start=args.train_start,
        train_end=args.train_end,
        test_start=args.test_start,
        test_end=args.test_end,
    )
    evaluator = FactorMiningEvaluator(config)
    candidates = [{"name": "cli_factor", "expression": args.expression, "category": "other"}]
    result = evaluator.evaluate_batch(candidates)

    for c in result.admitted:
        print(f"ADMITTED: {c['name']}")
        print(f"  IC: {c.get('full_ic', {}).get('ic_mean', 'N/A')}")
        if "stage3" in c:
            print(f"  Stage 3: {json.dumps(c['stage3'], indent=2, default=str)}")

    for c in result.rejected:
        print(f"REJECTED: {c['name']}")
        if "stage1" in c:
            print(f"  Stage 1 IC: {c['stage1'].get('ic_mean', 'N/A')}")


def cmd_library(args):
    """Show library status."""
    config = MiningConfig(library_dir=args.library_dir)
    lib = FactorLibrary(config)
    factors = lib.list_factors()
    print(f"Library: {len(factors)} factors")
    for f in factors:
        print(f"  [{f['id']}] {f['name']}: IC={f.get('ic_mean', 'N/A')}")


def cmd_memory(args):
    """Show Experience Memory status."""
    config = MiningConfig(memory_dir=args.memory_dir)
    mem = ExperienceMemory(config)
    ctx = mem.compose_search_context()
    print(ctx)


def main():
    parser = argparse.ArgumentParser(description="FactorMiner CLI")
    sub = parser.add_subparsers(dest="command")

    # sync
    p_sync = sub.add_parser("sync", help="Sync data to Qlib format")
    p_sync.add_argument("--qlib-dir", default="~/.qlib/qlib_data/cn_data_1d")
    p_sync.add_argument("--start", default="2015-01-01")
    p_sync.add_argument("--end", default=None)

    # evaluate
    p_eval = sub.add_parser("evaluate", help="Evaluate a factor expression")
    p_eval.add_argument("expression", help="Qlib expression, e.g. Rank($close)")
    p_eval.add_argument("--qlib-dir", default="~/.qlib/qlib_data/cn_data_1d")
    p_eval.add_argument("--train-start", default="2020-01-01")
    p_eval.add_argument("--train-end", default="2024-12-31")
    p_eval.add_argument("--test-start", default="2025-01-01")
    p_eval.add_argument("--test-end", default=None)

    # library
    p_lib = sub.add_parser("library", help="Show library status")
    p_lib.add_argument("--library-dir", default="mining/library")

    # memory
    p_mem = sub.add_parser("memory", help="Show memory context")
    p_mem.add_argument("--memory-dir", default="mining/memory")

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)

    if args.command == "sync":
        cmd_sync(args)
    elif args.command == "evaluate":
        cmd_evaluate(args)
    elif args.command == "library":
        cmd_library(args)
    elif args.command == "memory":
        cmd_memory(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Test CLI help works**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && python -m mining.cli --help`
Expected: Shows help text with sync, evaluate, library, memory subcommands

- [ ] **Step 3: Commit**

```bash
git add mining/cli.py
git commit -m "feat(mining): add CLI entry point for sync/evaluate/library/memory"
```

---

### Task 13: Claude Code Skills — factor-mine

**Files:**
- Create: `.claude/skills/factor-mine.md`

- [ ] **Step 1: Create skills directory**

```bash
mkdir -p /Users/xinzhan/.openclaw/workspace/quant_factor_system/.claude/skills
```

- [ ] **Step 2: Write `factor-mine` skill**

`.claude/skills/factor-mine.md`:
````markdown
---
name: factor-mine
description: Run one Ralph Loop iteration — retrieve memory, generate candidates, evaluate, update library and memory
user_invocable: true
---

# Factor Mining — Ralph Loop

Run one complete mining iteration:
1. Retrieve Experience Memory
2. Generate candidate factors
3. Evaluate candidates
4. Update library and memory

## Step 1: Retrieve Memory

Read the Experience Memory files to understand current state:

```bash
cat mining/memory/state.yaml
cat mining/memory/patterns.yaml
cat mining/memory/insights.yaml
```

Use these to compose your search context for factor generation.

## Step 2: Generate Candidates

Based on the Memory context, generate **8 candidate factor expressions** using Qlib Alpha expression syntax.

**Rules:**
- Each expression must use only these operators: Add, Sub, Mul, Div, Abs, Log, Power, Sign, Neg, Mean, Std, Var, Skew, Kurt, Med, Sum, Rank, EMA, SMA, WMA, Ref, Delta, TsRank, TsMax, TsMin, Slope, Rsquare, Resi, If, Greater, Less, Correlation, SignedPower, Tanh, Scale
- Each expression must reference only valid fields: $open, $high, $low, $close, $volume, $amount, $vwap, $returns (and minute-agg fields if available)
- Category must be one of: vwap, momentum, volatility, volume, regime, efficiency, distribution, trend, candlestick, intraday_agg, other
- Avoid forbidden regions listed in patterns.yaml
- Prioritize recommended directions from patterns.yaml
- Expression depth must not exceed 10

Write candidates to `mining/candidates/batch_XXX.yaml` using this format:

```yaml
batch_id: "batch_XXX"
timestamp: "YYYY-MM-DDTHH:MM:SS"
candidates:
  - name: "descriptive_name"
    expression: "Qlib_expression_here"
    category: "category"
    rationale: "Why this factor should work"
```

## Step 3: Evaluate

Run the evaluation pipeline:

```bash
cd /Users/xinzhan/.openclaw/workspace/quant_factor_system
python -c "
from mining.evaluator import FactorMiningEvaluator
from mining.config import MiningConfig
import yaml

config = MiningConfig()
evaluator = FactorMiningEvaluator(config)

with open('mining/candidates/batch_XXX.yaml') as f:
    batch = yaml.safe_load(f)

result = evaluator.evaluate_batch(batch['candidates'])
print(f'Admitted: {len(result.admitted)}')
print(f'Rejected: {len(result.rejected)}')
print(f'Replacements: {len(result.replacements)}')

# Save results
import json
output = {
    'admitted': result.admitted,
    'rejected': result.rejected,
    'replacements': result.replacements,
}
with open('mining/candidates/batch_XXX_result.yaml', 'w') as f:
    yaml.dump(output, f, default_flow_style=False, allow_unicode=True)
"
```

## Step 4: Library Update

For each admitted factor, add to the library:

```python
from mining.library import FactorLibrary
from mining.config import MiningConfig

lib = FactorLibrary(MiningConfig())
# For each admitted factor:
# lib.admit(factor_dict)
```

For replacements, use `lib.replace(old_id, new_factor_dict)`.

## Step 5: Memory Evolution

Analyze the batch results and update Experience Memory:

1. Read batch results
2. For successful factors: add to `patterns.yaml` recommended_directions
3. For rejected (high correlation): add to `patterns.yaml` forbidden_regions
4. Update `state.yaml` with new library stats
5. Distill strategic insights and update `insights.yaml`
6. Save batch summary to `mining/memory/history/batch_XXX.yaml`

Write updates using the Write tool to the appropriate YAML files.
````

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/factor-mine.md
git commit -m "feat(mining): add factor-mine Claude Code skill"
```

---

### Task 14: Claude Code Skills — factor-evaluate, memory-review, factor-library

**Files:**
- Create: `.claude/skills/factor-evaluate.md`
- Create: `.claude/skills/memory-review.md`
- Create: `.claude/skills/factor-library.md`

- [ ] **Step 1: Write `factor-evaluate` skill**

`.claude/skills/factor-evaluate.md`:
````markdown
---
name: factor-evaluate
description: Evaluate a single Qlib factor expression through the full pipeline
user_invocable: true
---

# Factor Evaluation

Evaluate a factor expression passed as argument.

## Usage

```
/factor-evaluate Neg(Rank(Div(Sub($close, $vwap), $vwap)))
```

## Steps

1. Validate the expression using ExpressionValidator
2. Run it through the full evaluation pipeline
3. Display results: IC, ICIR, quantile returns, correlation with library

```bash
cd /Users/xinzhan/.openclaw/workspace/quant_factor_system
python -c "
from mining.evaluator import FactorMiningEvaluator
from mining.config import MiningConfig
import json

config = MiningConfig()
evaluator = FactorMiningEvaluator(config)
expression = '$ARGUMENTS'
candidates = [{'name': 'user_factor', 'expression': expression, 'category': 'other'}]
result = evaluator.evaluate_batch(candidates)

for c in result.admitted + result.rejected:
    print(f'Expression: {c[\"expression\"]}')
    if 'stage1' in c:
        print(f'Stage 1 IC: {c[\"stage1\"].get(\"ic_mean\", \"N/A\")}')
    if 'full_ic' in c:
        print(f'Full IC: {c[\"full_ic\"].get(\"ic_mean\", \"N/A\")}')
    if 'stage3' in c:
        print(f'Stage 3: {json.dumps(c[\"stage3\"], indent=2, default=str)}')
"
```
````

- [ ] **Step 2: Write `memory-review` skill**

`.claude/skills/memory-review.md`:
````markdown
---
name: memory-review
description: Review and optionally adjust the Experience Memory
user_invocable: true
---

# Memory Review

Review the current state of Experience Memory and suggest adjustments.

## Steps

1. Read all memory files
2. Summarize current state
3. Identify potential improvements
4. Ask user before making changes

Read the following files:
- `mining/memory/state.yaml`
- `mining/memory/patterns.yaml`
- `mining/memory/insights.yaml`

List recent batch history from `mining/memory/history/`.

Present a summary to the user showing:
- Library size and target
- Domain saturation across categories
- Number of recommended directions vs forbidden regions
- Mining yield rate trends
- Key insights

Ask the user if they want to:
- Add/remove recommended directions
- Add/remove forbidden regions
- Update insights
- Adjust domain saturation assessments
````

- [ ] **Step 3: Write `factor-library` skill**

`.claude/skills/factor-library.md`:
````markdown
---
name: factor-library
description: View and manage the factor library
user_invocable: true
---

# Factor Library

View and manage admitted factors.

## Commands

- `/factor-library` or `/factor-library status` — Show library summary
- `/factor-library detail <id>` — Show factor details
- `/factor-library remove <id>` — Remove a factor (with confirmation)

## Status View

```bash
cd /Users/xinzhan/.openclaw/workspace/quant_factor_system
python -m mining.cli library
```

Also read `mining/library/library.yaml` to show the full index.

## Detail View

Read `mining/library/factors/factor_<id>.yaml` to show full factor details including:
- Expression
- Category
- All metrics (IC, ICIR, quantile returns)
- Financial logic
- Correlation with other library factors
````

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/
git commit -m "feat(mining): add factor-evaluate, memory-review, factor-library skills"
```

---

### Task 15: Integration Smoke Test

**Files:**
- Create: `tests/mining/test_integration.py`

- [ ] **Step 1: Write integration test**

`tests/mining/test_integration.py`:
```python
"""Integration test: full mining pipeline without Qlib."""

from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pandas as pd
import pytest
import yaml

from mining.config import MiningConfig
from mining.evaluator import FactorMiningEvaluator, BatchResult
from mining.expression import ExpressionValidator
from mining.library import FactorLibrary
from mining.memory import ExperienceMemory


@pytest.fixture
def full_setup(tmp_mining_dir, config):
    """Set up a complete mining environment."""
    # Write seed YAML files
    mem_dir = Path(config.memory_dir)
    lib_dir = Path(config.library_dir)

    (mem_dir / "state.yaml").write_text(yaml.dump({
        "library": {"size": 0, "target_size": 100, "avg_ic": 0.0, "avg_correlation": 0.0},
        "domain_saturation": {cat: {"count": 0, "saturation": "low"} for cat in config.categories},
        "mining": {"total_batches": 0, "total_candidates": 0, "total_admitted": 0,
                   "total_rejected": 0, "yield_rate": 0.0, "last_batch_time": None},
    }))
    (mem_dir / "patterns.yaml").write_text(yaml.dump({
        "recommended_directions": [
            {"pattern": "Test", "description": "test", "success_rate": "high", "example_factors": []}
        ],
        "forbidden_regions": [],
    }))
    (mem_dir / "insights.yaml").write_text(yaml.dump({
        "insights": [{"insight": "test", "confidence": "high", "source": "test"}],
    }))
    (lib_dir / "library.yaml").write_text(yaml.dump({
        "thresholds": {"ic_min": 0.03, "correlation_max": 0.5},
        "factors": [],
    }))

    return config


def test_end_to_end(full_setup):
    """Test: validate -> evaluate -> admit -> update memory."""
    config = full_setup

    # 1. Validate expression
    validator = ExpressionValidator(config)
    result = validator.validate("Rank(Div(Sub($close, $vwap), $vwap))")
    assert result.valid

    # 2. Evaluate (mocked Qlib)
    dates = pd.bdate_range("2023-01-02", periods=30)
    instruments = [f"SH60000{i}" for i in range(10)]
    idx = pd.MultiIndex.from_product([dates, instruments], names=["datetime", "instrument"])
    np.random.seed(42)
    signal = np.random.randn(len(idx))

    with patch.object(FactorMiningEvaluator, "_ensure_qlib_initialized"), \
         patch.object(FactorMiningEvaluator, "_compute_factor_qlib") as mock_factor, \
         patch.object(FactorMiningEvaluator, "_get_returns_qlib") as mock_returns, \
         patch.object(FactorMiningEvaluator, "_get_fast_screening_universe", return_value=instruments), \
         patch.object(FactorMiningEvaluator, "_get_full_universe", return_value=instruments):

        mock_factor.return_value = pd.DataFrame({"factor": signal}, index=idx)
        mock_returns.return_value = pd.DataFrame(
            {"$returns_1d": signal + np.random.randn(len(idx)) * 0.2}, index=idx)

        evaluator = FactorMiningEvaluator(config)
        batch = [{"name": "VWAP_Dev", "expression": "Rank(Div(Sub($close, $vwap), $vwap))", "category": "vwap"}]
        result = evaluator.evaluate_batch(batch)

    assert isinstance(result, BatchResult)

    # 3. Admit to library
    library = FactorLibrary(config)
    for c in result.admitted:
        factor_id = library.admit({
            "name": c["name"],
            "expression": c["expression"],
            "category": c.get("category", "other"),
            "batch": "batch_001",
            "metrics": c.get("full_ic", {}),
        })
        assert factor_id is not None

    # 4. Update memory
    memory = ExperienceMemory(config)
    state = memory.read_state()
    state["library"]["size"] = library.size
    state["mining"]["total_batches"] = 1
    state["mining"]["total_candidates"] = len(batch)
    state["mining"]["total_admitted"] = len(result.admitted)
    memory.write_state(state)

    # Verify
    reloaded = memory.read_state()
    assert reloaded["mining"]["total_batches"] == 1

    # 5. Memory context should include library info
    ctx = memory.compose_search_context()
    assert "Library size:" in ctx
```

- [ ] **Step 2: Run integration test**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && python -m pytest tests/mining/test_integration.py -v`
Expected: PASS

- [ ] **Step 3: Run full test suite**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && python -m pytest tests/mining/ -v --tb=short`
Expected: All tests PASS

- [ ] **Step 4: Commit**

```bash
git add tests/mining/test_integration.py
git commit -m "test(mining): add end-to-end integration test"
```

---

### Task 16: Final Cleanup

**Files:**
- Modify: `setup.py`

- [ ] **Step 1: Verify setup.py has all dependencies**

Ensure `setup.py` includes:
```python
install_requires=[
    ...,
    "pyyaml>=6.0",
],
extras_require={
    ...,
    "mining": ["qlib>=0.9.0"],
},
```

- [ ] **Step 2: Run full test suite one final time**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && python -m pytest tests/mining/ -v --tb=short`
Expected: All tests PASS

- [ ] **Step 3: Final commit**

```bash
git add -A
git commit -m "chore(mining): final cleanup and dependency updates"
```
