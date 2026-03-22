# FactorMiner: Automated Factor Mining System Design

## Overview

Build an automated factor mining system inspired by the FactorMiner paper (arXiv:2602.14670), implementing the Ralph Loop paradigm (Retrieve → Generate → Evaluate → Distill) using Claude Code Skills for agent orchestration, Qlib expression engine for factor computation, and local YAML files for Experience Memory.

**Paper reference**: "FactorMiner: A Self-Evolving Agent with Skills and Experience Memory for Financial Alpha Discovery" (Tsinghua University, 2026)

**Key adaptation from paper**: The paper works on 10-minute frequency A-share data. We adapt to daily frequency with minute-data aggregation support, using Qlib expression engine instead of the paper's custom GPU-accelerated backend.

## Architecture

### System Overview

```
quant_factor_system/
├── data/                          # [KEEP] Existing data layer
│   ├── storage/timescale_storage.py
│   ├── ricequant_source.py
│   └── data_manager.py
│
├── mining/                        # [NEW] Factor mining core
│   ├── __init__.py
│   ├── operators.py               # Qlib operator registry + extensions
│   ├── expression.py              # Expression validation/parsing
│   ├── evaluator.py               # 4-stage validation pipeline
│   ├── library.py                 # Factor library management
│   ├── memory.py                  # Experience Memory read/write
│   ├── data_sync.py               # TimescaleDB → Qlib bin sync
│   └── config.py                  # Mining configuration
│
├── mining/memory/                 # [NEW] Experience Memory storage
│   ├── state.yaml                 # Mining state
│   ├── patterns.yaml              # Successful patterns + forbidden regions
│   ├── insights.yaml              # Strategic insights
│   └── history/                   # Per-batch mining history
│       └── batch_001.yaml
│
├── mining/library/                # [NEW] Factor library
│   ├── library.yaml               # Library index (all admitted factors)
│   └── factors/                   # Per-factor detail records
│       ├── factor_001.yaml
│       └── ...
│
├── mining/candidates/             # [NEW] Temporary candidate storage
│   └── batch_001.yaml
│
├── factors/                       # [REFACTOR] Factor computation layer
│   ├── basic/                     # Keep basic factor definitions
│   ├── processing/                # Keep factor processing
│   └── visualization/             # Keep visualization
│
├── backtest/                      # [KEEP] Backtest engine
├── dashboard/                     # [KEEP] Web interface
└── scripts/                       # [EXTEND] New sync/mining scripts
```

### Data Flow

```
TimescaleDB (price_daily, price_1min)
    │
    ├── data_sync.py ──→ Qlib bin format (~/.qlib/qlib_data/cn_data_1d/)
    │                     Fields: $open, $high, $low, $close, $volume,
    │                             $amount, $vwap, $returns
    │                     + minute aggregates: $intraday_vol, $intraday_skew, etc.
    │
    └── Qlib Expression Engine
        │
        ├── Factor computation: D.features(instruments, fields=[expression])
        │
        └── IC evaluation: Spearman rank correlation with T+1 returns
```

## Ralph Loop: Skills Orchestration

### Skills

| Skill | Purpose | Trigger |
|-------|---------|---------|
| `factor-mine` | Main Ralph Loop entry point | `/factor-mine` |
| `factor-evaluate` | Standalone factor evaluation | `/factor-evaluate <expression>` |
| `memory-review` | Review and adjust Memory | `/memory-review` |
| `factor-library` | Library management | `/factor-library status` |

### Ralph Loop Flow (One Mining Round)

```
User invokes /factor-mine
    │
    ├── Step 1: Memory Retrieval
    │   ├── Read mining/memory/state.yaml      → Current library state
    │   ├── Read mining/memory/patterns.yaml   → Recommended directions + forbidden regions
    │   ├── Read mining/memory/insights.yaml   → Strategic insights
    │   └── Compose search prior prompt context
    │
    ├── Step 2: Guided Generation
    │   ├── Claude generates N candidate factors based on:
    │   │   - Memory context (recommended patterns, forbidden regions)
    │   │   - Operator registry (Qlib expression syntax)
    │   │   - Current library state (domain saturation)
    │   ├── Output format: Qlib Alpha expressions
    │   │   Example: Neg(Rank(Div(Sub($close, $vwap), $vwap)))
    │   │   Category must be one of: vwap, momentum, volatility, volume,
    │   │   regime, efficiency, distribution, trend, candlestick, intraday_agg, other
    │   ├── Write to mining/candidates/batch_XXX.yaml
    │   └── Generates candidates_per_batch candidates (default 8)
    │
    │   Note: The skill prompt template includes instructions for Claude to
    │   read YAML memory files via the Read tool, and to write candidates
    │   via the Write tool. Memory content is loaded into prompt context.
    │
    ├── Step 3: Multi-Stage Evaluation (Python script)
    │   ├── Invoke: python -m mining.evaluator --batch batch_XXX
    │   ├── Stage 1: Fast IC Screening (top-50 by liquidity from universe)
    │   │   └── Filter: |IC_mean| ≥ τ_IC (default 0.03 for daily)
    │   ├── Stage 1.5: Batch Deduplication (intra-batch ρ < θ before library check)
    │   ├── Stage 2: Full Universe Computation + Correlation Check (against library L)
    │   │   ├── Compute factor values on full universe (cached for Stage 4 reuse)
    │   │   └── Filter: max_{g∈L} |ρ(α, g)| < θ (default 0.5)
    │   ├── Stage 2.5: Replacement Check (for Stage 2 rejects)
    │   │   └── Condition: IC_full(α) ≥ 0.05 AND IC_full(α) ≥ 1.3×IC(g*) AND single conflict
    │   │       (uses full-universe IC, not Stage 1 subset IC)
    │   ├── Stage 3: Full Validation (reuse cached factor values)
    │   │   └── Compute full metrics: IC, ICIR, quantile returns, win rate
    │   └── Output: mining/candidates/batch_XXX_result.yaml
    │
    ├── Step 4: Library Update
    │   ├── Read evaluation results
    │   ├── Admitted factors → mining/library/factors/factor_XXX.yaml
    │   └── Update mining/library/library.yaml index
    │
    └── Step 5: Memory Evolution (Distillation)
        ├── Claude analyzes batch results:
        │   ├── Which patterns succeeded? → Update patterns.yaml recommended_directions
        │   ├── Which directions were rejected? → Update patterns.yaml forbidden_regions
        │   └── Any new strategic insights? → Update insights.yaml
        ├── Update state.yaml (library size, domain saturation)
        └── Save batch history to history/batch_XXX.yaml
```

## Experience Memory Design

### state.yaml

```yaml
library:
  size: 0
  target_size: 100
  avg_ic: 0.0
  avg_correlation: 0.0

domain_saturation:
  vwap:          { count: 0, saturation: "low" }
  momentum:      { count: 0, saturation: "low" }
  volatility:    { count: 0, saturation: "low" }
  volume:        { count: 0, saturation: "low" }
  regime:        { count: 0, saturation: "low" }
  efficiency:    { count: 0, saturation: "low" }
  distribution:  { count: 0, saturation: "low" }
  trend:         { count: 0, saturation: "low" }
  candlestick:   { count: 0, saturation: "low" }
  intraday_agg:  { count: 0, saturation: "low" }

mining:
  total_batches: 0
  total_candidates: 0
  total_admitted: 0
  total_rejected: 0
  yield_rate: 0.0
  last_batch_time: null
```

### patterns.yaml

```yaml
recommended_directions:
  - pattern: "Higher Moment Regimes"
    description: "Use Skew/Kurt as IfElse conditions to identify extreme distribution environments for reversal signals"
    success_rate: "high"
    example_factors: []

  - pattern: "Trend Regression Adaptive"
    description: "Use Rsquare/Slope/Resi for adaptive trend regression. High R²→trend follow, Low R²→mean reversion"
    success_rate: "high"
    example_factors: []

  - pattern: "PV Corr Interaction"
    description: "Combine price-volume correlation with amount efficiency or trend operators to capture volume-price coordination"
    success_rate: "high"
    example_factors: []

  - pattern: "Robust Efficiency"
    description: "Use median and other robust statistics to smooth amount efficiency, filtering extreme noise"
    success_rate: "high"
    example_factors: []

  - pattern: "Intraday Aggregation Features"
    description: "Leverage minute-data aggregated features (intraday_vol, intraday_skew, volume_concentration) as inputs for daily factors"
    success_rate: "medium"
    example_factors: []

forbidden_regions:
  - direction: "Simple VWAP Deviation"
    reason: "High correlation with VWAP factor cluster (ρ > 0.5)"
    correlated_factors: []
    correlation: "> 0.5"

  - direction: "Standardized Returns/Amount"
    reason: "Simple return standardization is redundant with existing factors"
    correlated_factors: []
    correlation: "> 0.6"
```

### insights.yaml

```yaml
insights:
  - insight: "Non-linear combinations (IfElse branching) are more likely to produce orthogonal factors than linear combinations"
    confidence: "high"
    source: "paper finding"

  - insight: "CsRank wrapping can effectively reduce inter-factor correlation"
    confidence: "high"
    source: "paper Appendix G"

  - insight: "Amount efficiency (Returns/Amount) produces signals orthogonal to pure price-based factors"
    confidence: "high"
    source: "paper finding"

  - insight: "Daily frequency VWAP signal space is more limited than intraday; minute-aggregated features may offer more room"
    confidence: "medium"
    source: "hypothesis"
```

### library.yaml

```yaml
thresholds:
  ic_min: 0.03
  correlation_max: 0.5
  replacement_ic_ratio: 1.3
  replacement_ic_min: 0.05

factors: []
```

### Per-factor record (factors/factor_001.yaml)

```yaml
id: "001"
name: "VWAP_Deviation"
formula: "Neg(Rank(Div(Sub($close, $vwap), $vwap)))"
category: "vwap"
batch: "batch_001"
admitted_at: "2026-03-22"

metrics:
  ic_mean: 0.065
  ic_std: 0.078
  ic_ir: 0.82
  ic_win_rate: 0.68
  max_correlation: 0.31
  max_corr_factor: "momentum_20"

quantile_returns:
  q1: -0.038
  q2: -0.012
  q3: 0.002
  q4: 0.018
  q5: 0.042

financial_logic: "VWAP deviation captures mean-reversion to volume-weighted average price. Negative rank means lower factor value → higher expected return (buy when price is below VWAP)."
```

## Evaluation Pipeline

### Pipeline Stages (revised order)

The pipeline has been revised from the paper's 4-stage design to address:
- **Batch dedup before library check** (avoids wasted computation on duplicates)
- **Factor value caching** (Stage 2 full-universe values reused in Stage 3)
- **Consistent IC comparison** (replacement check uses full-universe IC, not subset IC)

```
Stage 1: Fast IC Screening
  → subset universe (top-50 by liquidity from configured universe)
  → filter |IC_mean| ≥ τ_IC

Stage 1.5: Batch Deduplication
  → compute pairwise correlation among Stage 1 survivors (on subset)
  → keep higher-IC factor from each correlated pair (ρ ≥ θ)

Stage 2: Full Universe Computation + Correlation Check
  → compute factor values on FULL universe (results cached in _factor_cache)
  → re-compute IC on full universe → "full_ic" (used for replacement)
  → compute correlation with all library factors
  → filter max|ρ| < θ

Stage 2.5: Replacement Check (on Stage 2 rejects)
  → uses full_ic (from Stage 2), NOT subset IC from Stage 1
  → conflict count = number of library factors with ρ ≥ θ
  → replace if: full_ic ≥ replacement_ic_min AND full_ic ≥ 1.3×IC(g*) AND conflicts == 1

Stage 3: Full Validation (reuses cached factor values)
  → compute: IC/ICIR (in-sample + out-of-sample), quantile returns, win rate
  → in-sample: train_start to train_end
  → out-of-sample: test_start to test_end
```

### Expression Validation

Before any factor evaluation, expressions are validated:

```python
# mining/expression.py

class ExpressionValidator:
    """Validate Qlib factor expressions before computation."""

    def validate(self, expression: str) -> ValidationResult:
        """
        1. Syntax check: parse expression through Qlib's expression parser
           without computing (catches malformed expressions)
        2. Field check: verify all referenced fields ($close, $vwap, etc.)
           exist in the data
        3. Depth check: expression tree depth ≤ MAX_DEPTH (default 10)
           to prevent runaway computation
        4. Safety check: no infinite values possible (wrap Div with safe_div)
        Returns: ValidationResult(valid, errors, warnings)
        """

    def safe_wrap(self, expression: str) -> str:
        """Add safety wrappers (e.g., replace Div with safe_div that handles zero)."""
```

### T+1 Returns Computation

Forward returns are computed as a Qlib expression field, ensuring consistency:

```python
# T+1 returns field (computed during data sync and stored as a feature)
# In data_sync.py, we pre-compute and store:
#   $returns_1d = Ref($close, -1) / $close - 1   (forward 1-day return)
#
# In evaluator, IC is computed as:
#   Spearman correlation between factor_values and $returns_1d
#   grouped by date (cross-sectional)
#
# Stock suspensions: NaN returns (excluded from IC calculation)
# Limit-up/down: included but with NaN returns on the following day
#   when the stock cannot be traded
```

### Fast Screening Universe Selection

```python
def _get_fast_screening_universe(self) -> list:
    """
    Select top-N stocks by average daily turnover from the configured universe.
    Rationale: high-liquidity stocks have more reliable price signals,
    making Stage 1 IC screening more representative.
    N = config.fast_screening_universe_size (default 50)
    """
```

### Category Classification

Factor categories are assigned by Claude during generation and must match one of
the predefined categories in `state.yaml.domain_saturation`. If Claude proposes
a new category, it maps to the closest existing one or "other". The skill prompt
includes the category list as a constraint.

Predefined categories: vwap, momentum, volatility, volume, regime, efficiency,
distribution, trend, candlestick, intraday_agg, other.

### Qlib Operator Semantics Note

**Important**: Qlib's `Rank` operator is `CSRankNorm` (cross-sectional rank
normalized to [0,1]). This is the correct mapping for the paper's `CsRank`.
Verify during implementation by checking:
```python
from qlib.data.ops import Rank
# Rank computes percentile rank across all instruments at each timestamp
```
If Qlib's `Rank` is time-series instead of cross-sectional, use `CSRankNorm`
explicitly or register a custom `CsRank` operator.

### mining/evaluator.py

```python
@dataclass
class BatchResult:
    """Result of a batch evaluation."""
    admitted: List[dict]
    rejected: List[dict]
    replacements: List[dict]

class FactorMiningEvaluator:
    """Multi-stage factor mining evaluation pipeline using Qlib."""

    def __init__(self, config: MiningConfig):
        self.config = config
        self._factor_cache: Dict[str, pd.DataFrame] = {}  # expression -> values
        self._ensure_qlib_initialized()

    def _ensure_qlib_initialized(self):
        """Initialize Qlib idempotently (safe to call multiple times)."""
        try:
            import qlib
            if not qlib.is_initialized():
                qlib.init(provider_uri=self.config.qlib_data_dir)
        except AttributeError:
            # Older Qlib versions: catch re-init warning
            import qlib
            qlib.init(provider_uri=self.config.qlib_data_dir, exist_ok=True)

    def evaluate_batch(self, candidates: List[dict]) -> BatchResult:
        """Run multi-stage pipeline on a batch of candidate factors."""
        self._factor_cache.clear()

        # Validate expressions first
        valid, invalid = self._validate_expressions(candidates)

        # Stage 1: Fast IC on subset
        stage1_passed = self._fast_ic_screening(valid)

        # Stage 1.5: Intra-batch dedup (before library check, saves computation)
        stage1_deduped = self._batch_dedup(stage1_passed, use_subset=True)

        # Stage 2: Full universe computation + correlation check
        # Factor values computed here are CACHED for Stage 3 reuse
        stage2_passed, stage2_rejected = self._correlation_check(stage1_deduped)

        # Stage 2.5: Replacement check (uses full-universe IC from Stage 2)
        replacements = self._replacement_check(stage2_rejected)

        # Stage 3: Full validation (reuses cached values)
        validated = self._full_validation(stage2_passed)

        all_rejected = invalid + [c for c in valid if c not in stage1_passed] + stage2_rejected
        return BatchResult(admitted=validated, rejected=all_rejected, replacements=replacements)

    def _validate_expressions(self, candidates):
        """Pre-validate all expressions before evaluation."""
        valid, invalid = [], []
        validator = ExpressionValidator()
        for c in candidates:
            result = validator.validate(c["expression"])
            if result.valid:
                valid.append(c)
            else:
                c["validation_error"] = result.errors
                invalid.append(c)
        return valid, invalid

    def _fast_ic_screening(self, candidates):
        """Stage 1: Calculate IC on top-50 liquidity subset."""
        subset = self._get_fast_screening_universe()
        results = []
        for c in candidates:
            try:
                values = self._compute_factor(c["expression"], subset)
                ic_stats = self._compute_ic(values, subset)
                if abs(ic_stats["ic_mean"]) >= self.config.ic_threshold:
                    c["stage1"] = ic_stats
                    results.append(c)
                else:
                    c["stage1"] = {**ic_stats, "rejected": True}
            except Exception as e:
                c["stage1"] = {"error": str(e)}
        return results

    def _correlation_check(self, candidates):
        """Stage 2: Compute on full universe, check correlation with library."""
        library = self._load_library_factors()
        full_universe = self._get_full_universe()
        passed, rejected = [], []
        for c in candidates:
            # Compute on full universe and CACHE
            factor_vals = self._compute_factor(c["expression"], full_universe)
            self._factor_cache[c["expression"]] = factor_vals

            # Re-compute IC on full universe for accurate comparison
            full_ic = self._compute_ic(factor_vals, full_universe)
            c["full_ic"] = full_ic

            # Correlation check
            max_corr, max_corr_factor = self._max_library_correlation(factor_vals, library)
            if max_corr < self.config.correlation_threshold:
                c["stage2"] = {"max_corr": max_corr, "max_corr_factor": max_corr_factor, "passed": True}
                passed.append(c)
            else:
                c["stage2"] = {"max_corr": max_corr, "max_corr_factor": max_corr_factor, "passed": False}
                rejected.append(c)
        return passed, rejected

    def _replacement_check(self, rejected):
        """Stage 2.5: Check if rejected factors can replace weaker library members.
        Uses full-universe IC (c["full_ic"]) for fair comparison with library ICs.
        Conflict = number of library factors with ρ ≥ correlation_threshold.
        """
        replacements = []
        for c in rejected:
            full_ic = abs(c["full_ic"]["ic_mean"])
            if full_ic < self.config.replacement_ic_min:
                continue
            g_star = c["stage2"]["max_corr_factor"]
            g_ic = self._get_library_factor_ic(g_star)
            conflicts = self._count_library_conflicts(c)
            if full_ic >= self.config.replacement_ic_ratio * abs(g_ic) and conflicts == 1:
                replacements.append({"new_factor": c, "replaces": g_star})
        return replacements

    def _count_library_conflicts(self, candidate) -> int:
        """Count library factors with ρ ≥ correlation_threshold."""
        # Uses correlation values computed in Stage 2
        # Returns number of library factors exceeding θ
        ...

    def _batch_dedup(self, candidates, use_subset=False):
        """Remove intra-batch duplicates. Keep higher-IC factor from correlated pairs."""
        if len(candidates) <= 1:
            return candidates
        # Compute pairwise correlation (on subset or full universe)
        # Greedy removal: sort by IC desc, remove later factors that correlate with earlier ones
        ...

    def _full_validation(self, candidates):
        """Stage 3: Full validation. Reuses cached factor values from Stage 2."""
        validated = []
        for c in candidates:
            # Reuse cached values instead of recomputing
            cached_vals = self._factor_cache.get(c["expression"])
            if cached_vals is None:
                cached_vals = self._compute_factor(c["expression"], self._get_full_universe())

            # Compute full metrics (in-sample + out-of-sample)
            full_stats = self._compute_full_metrics(cached_vals)
            c["stage3"] = full_stats
            validated.append(c)
        return validated

    def _compute_factor(self, expression: str, universe: list) -> pd.DataFrame:
        """Use Qlib expression engine to compute factor values."""
        from qlib.data import D
        return D.features(
            instruments=universe,
            fields=[expression],
            start_time=self.config.train_start,
            end_time=self.config.train_end,
        )

    def _compute_ic(self, factor_values: pd.DataFrame, universe: list) -> dict:
        """Compute daily cross-sectional Spearman IC.
        Forward returns: uses pre-computed $returns_1d field from Qlib data.
        Groups by date, computes Spearman correlation per date, then aggregates.
        Returns: ic_mean, ic_std, ic_ir, ic_win_rate, n_days
        """
        from qlib.data import D
        returns = D.features(instruments=universe, fields=["$returns_1d"],
                             start_time=self.config.train_start,
                             end_time=self.config.train_end)
        # Merge factor_values with returns on (datetime, instrument) index
        # For each date: Spearman correlation between factor and returns
        # Aggregate: mean, std, ir, win_rate
        ...

    def _compute_full_metrics(self, factor_values: pd.DataFrame) -> dict:
        """Compute comprehensive metrics including OOS performance.
        Returns:
          - ic_mean_is, ic_ir_is (in-sample: train period)
          - ic_mean_oos, ic_ir_oos (out-of-sample: test period)
          - ic_win_rate
          - quantile_returns: {q1, q2, q3, q4, q5}
          - ls_return (long Q5 - short Q1)
          - monotonicity (perfect ranking = 1.0)
        """
        ...

    def _max_library_correlation(self, factor_vals, library_vals) -> tuple:
        """Compute max cross-sectional Spearman correlation with library.
        For each library factor, compute time-averaged |cross-sectional Spearman ρ|.
        Returns: (max_correlation, most_correlated_factor_id)
        """
        ...
```

## Data Synchronization

### mining/data_sync.py

```python
class DataSynchronizer:
    """Sync TimescaleDB data to Qlib binary format."""

    def __init__(self, db: TimescaleDB, qlib_dir: str = "~/.qlib/qlib_data/cn_data_1d"):
        self.db = db
        self.qlib_dir = Path(qlib_dir).expanduser()

    def sync_daily(self, start: str = "2015-01-01", end: str = None):
        """
        Export TimescaleDB price_daily → Qlib bin format.
        Field mapping:
          price_daily.open   → $open
          price_daily.high   → $high
          price_daily.low    → $low
          price_daily.close  → $close
          price_daily.volume → $volume
          price_daily.amount → $amount
          price_daily.vwap   → $vwap (NULL values filled with (open+high+low+close)/4)
          computed: $returns = close / Ref(close, 1) - 1
          computed: $returns_1d = forward 1-day return (for IC evaluation)

        Qlib instrument format: SH600000 (Shanghai), SZ000001 (Shenzhen)
        Creates instruments file: instruments/all.txt and instruments/csi500.txt
        """

    def sync_minute_aggregates(self, start: str = "2024-01-01"):
        """
        Aggregate 1min data into daily features.
        Features computed:
          $intraday_vol     : std of 1min returns within day
          $intraday_skew    : skewness of 1min returns within day
          $intraday_kurt    : kurtosis of 1min returns within day
          $vwap_dev         : actual VWAP vs simple average deviation
          $volume_conc      : volume Herfindahl concentration index
          $high_low_range   : (high - low) / close
          $morning_momentum : morning session (9:30-11:30) return
          $afternoon_ret    : afternoon session (13:00-15:00) return
        """

    def incremental_update(self):
        """Incremental update: only sync newly added data."""
```

## Operator Registry

### Qlib Built-in Operators (directly available)

| Category | Operators |
|----------|-----------|
| Arithmetic | Add, Sub, Mul, Div, Abs, Log, Power, Sign, Neg |
| Statistical | Mean, Std, Var, Skew, Kurt, Med, Sum, Prod |
| Time-series | Ref, Delta, TsRank, TsMax, TsMin, TsArgMax, TsArgMin |
| Cross-sectional | Rank (= CsRank) |
| Smoothing | EMA, SMA, WMA |
| Regression | Slope, Rsquare, Resi |
| Logical | If (= IfElse), Greater, Less |

### Custom Extensions Needed

Note: Some "missing" operators can be expressed with existing ones:
- `Sqrt(x)` = `Power(x, 0.5)`, `Square(x)` = `Power(x, 2)`
- `Inv(x)` = `Div(1, x)`, `Neg(x)` = `Mul(-1, x)`
- `Corr(x, y, N)` = Qlib has `Correlation` built-in

Truly new operators to register:

| Operator | Definition | Reason |
|----------|-----------|--------|
| SignedPower | sign(x) * \|x\|^p | Non-linear transformation preserving sign |
| TsDecay | Time-decay weighted average | Recency weighting (not just EMA) |
| Scale | Cross-sectional normalization to [-1, 1] | Different from Rank (continuous vs ordinal) |
| Tanh | tanh(x) | Bounded non-linearity |
| Exp | exp(x) | Exponential (use with caution - overflow risk) |

### Base Feature Fields

```
# Price fields (from price_daily)
$open, $high, $low, $close, $volume, $amount, $vwap

# Computed fields
$returns = $close / Ref($close, 1) - 1   # backward-looking, for use in factor expressions
$returns_1d                                # forward 1-day return, for IC evaluation only

# Minute-aggregated fields (from price_1min)
$intraday_vol, $intraday_skew, $intraday_kurt
$vwap_dev, $volume_conc, $high_low_range
$morning_momentum, $afternoon_ret
```

## Configuration

### mining/config.py

```python
@dataclass
class MiningConfig:
    # Data
    qlib_data_dir: str = "~/.qlib/qlib_data/cn_data_1d"

    # Evaluation thresholds
    ic_threshold: float = 0.03           # Daily IC admission threshold
    correlation_threshold: float = 0.5    # Max correlation threshold
    replacement_ic_ratio: float = 1.3     # Replacement IC multiplier
    replacement_ic_min: float = 0.05      # Replacement minimum IC

    # Fast screening
    fast_screening_universe_size: int = 50

    # Library target
    target_library_size: int = 100

    # Universe
    universe: str = "csi500"              # Default universe
    custom_universe: Optional[List[str]] = None  # Custom stock pool

    # Time ranges
    train_start: str = "2020-01-01"
    train_end: str = "2024-12-31"
    test_start: str = "2025-01-01"
    test_end: str = None                  # Up to today

    # Per-batch
    candidates_per_batch: int = 8
```

## Evaluation Output Format

### batch_XXX_result.yaml

```yaml
batch_id: "batch_001"
timestamp: "2026-03-22T14:30:00"
universe: "csi500"

candidates:
  - name: "VWAP_Deviation"
    expression: "Neg(Rank(Div(Sub($close, $vwap), $vwap)))"
    category: "vwap"
    stage1: { passed: true, ic_mean: 0.065, ic_ir: 0.82 }
    stage2: { passed: true, max_corr: 0.31, max_corr_factor: "momentum_20" }
    stage3: { passed: true }
    stage3:
      ic_mean: 0.062
      ic_std: 0.078
      ic_ir: 0.79
      ic_win_rate: 0.68
      q5_return: 0.042
      q1_return: -0.038
      ls_return: 0.080
    result: "admitted"

  - name: "Simple_Returns_Rank"
    expression: "Rank(Ref($close, 5) / $close - 1)"
    category: "momentum"
    stage1: { passed: true, ic_mean: 0.045 }
    stage2: { passed: false, max_corr: 0.72, max_corr_factor: "momentum_5d" }
    result: "rejected"
    rejection_reason: "High correlation with momentum_5d (ρ=0.72)"

summary:
  total_candidates: 8
  stage1_passed: 6
  stage1_5_after_dedup: 5
  stage2_passed: 3
  stage2_rejected: 2
  replacements: 0
  stage3_passed: 3
  admitted: 3
  yield_rate: 0.375
```

## Key Design Decisions

1. **Qlib expression engine** over custom operators: Mature, fast, well-documented. 90% of paper's operators are built-in.

2. **Daily frequency primary** with minute aggregation: Lower computational cost, simpler evaluation. Minute aggregates ($intraday_vol, $intraday_skew, etc.) bring high-frequency information into daily factors.

3. **Claude Code Skills** for orchestration: Human-in-the-loop by default. Claude does high-level reasoning (factor generation, memory distillation), Python scripts do computation (IC, correlation).

4. **YAML files for Memory**: Simple, human-readable, version-controlled. No need for vector databases or complex retrieval — Claude reads the full memory as prompt context.

5. **5-10 candidates per batch** (vs paper's 40): Claude generates higher-quality candidates than random/GP methods, so fewer candidates needed.

6. **IC threshold 0.03 for daily** (vs paper's 0.04 for 10-min): Daily frequency has lower IC magnitudes than intraday, so threshold is adjusted down.

7. **Gradual refactoring**: Keep existing data layer, backtest, dashboard. New `mining/` module is independent and can be developed without breaking anything.

## Dependencies

New dependencies to add:
- `qlib` (Microsoft Qlib framework)
- `pyyaml` (YAML read/write, likely already available)

## Risk & Mitigation

| Risk | Mitigation |
|------|-----------|
| Qlib expression syntax may differ from paper's operators | Map operators carefully; extend Qlib with custom ops where needed |
| TimescaleDB → Qlib sync complexity | Start with daily data only; add minute aggregates incrementally |
| Claude may generate invalid expressions | Validate expressions before evaluation; catch and report errors |
| Memory YAML files grow too large | Periodic consolidation via Memory Evolution; keep history/ separate |
| IC threshold may be too low/high for daily | Start with 0.03, adjust based on early results |
