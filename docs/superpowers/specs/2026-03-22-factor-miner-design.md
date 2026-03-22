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
    │   ├── Write to mining/candidates/batch_XXX.yaml
    │   └── Generates 5-10 candidates per batch
    │
    ├── Step 3: Multi-Stage Evaluation (Python script)
    │   ├── Invoke: python -m mining.evaluator --batch batch_XXX
    │   ├── Stage 1: Fast IC Screening (50-stock subset)
    │   │   └── Filter: |IC_mean| ≥ τ_IC (default 0.03 for daily)
    │   ├── Stage 2: Correlation Check (against library L)
    │   │   └── Filter: max_{g∈L} |ρ(α, g)| < θ (default 0.5)
    │   ├── Stage 2.5: Replacement Check (for Stage 2 rejects)
    │   │   └── Condition: IC(α) ≥ 0.05 AND IC(α) ≥ 1.3×IC(g*) AND single conflict
    │   ├── Stage 3: Batch Deduplication (intra-batch ρ < θ)
    │   ├── Stage 4: Full Validation (complete asset set + time range)
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

## 4-Stage Evaluation Pipeline

### mining/evaluator.py

```python
class FactorMiningEvaluator:
    """4-stage factor mining evaluation pipeline using Qlib."""

    def __init__(self, config: MiningConfig):
        self.config = config
        # Initialize Qlib
        qlib.init(provider_uri=config.qlib_data_dir)

    def evaluate_batch(self, candidates: List[dict]) -> BatchResult:
        """Run 4-stage pipeline on a batch of candidate factors."""
        # Stage 1: Fast IC on small subset
        stage1_passed = self._fast_ic_screening(candidates)
        # Stage 2: Correlation with library
        stage2_passed, stage2_rejected = self._correlation_check(stage1_passed)
        # Stage 2.5: Replacement for rejects
        replacements = self._replacement_check(stage2_rejected)
        # Stage 3: Intra-batch dedup
        stage3_passed = self._batch_dedup(stage2_passed)
        # Stage 4: Full validation
        validated = self._full_validation(stage3_passed)
        return BatchResult(admitted=validated, rejected=stage2_rejected, replacements=replacements)

    def _fast_ic_screening(self, candidates):
        """Stage 1: Calculate IC on small asset subset."""
        subset = self._get_fast_screening_universe()
        results = []
        for c in candidates:
            try:
                values = self._compute_factor(c["expression"], subset)
                ic_stats = self._compute_ic(values)
                if abs(ic_stats["ic_mean"]) >= self.config.ic_threshold:
                    c["stage1"] = ic_stats
                    results.append(c)
            except Exception as e:
                c["stage1"] = {"error": str(e)}
        return results

    def _correlation_check(self, candidates):
        """Stage 2: Check cross-sectional correlation with library."""
        library = self._load_library_factors()
        passed, rejected = [], []
        for c in candidates:
            factor_vals = self._compute_factor(c["expression"], self._get_full_universe())
            max_corr, max_corr_factor = self._max_library_correlation(factor_vals, library)
            if max_corr < self.config.correlation_threshold:
                c["stage2"] = {"max_corr": max_corr, "max_corr_factor": max_corr_factor, "passed": True}
                passed.append(c)
            else:
                c["stage2"] = {"max_corr": max_corr, "max_corr_factor": max_corr_factor, "passed": False}
                rejected.append(c)
        return passed, rejected

    def _replacement_check(self, rejected):
        """Stage 2.5: Check if rejected factors can replace weaker library members."""
        replacements = []
        for c in rejected:
            if abs(c["stage1"]["ic_mean"]) < self.config.replacement_ic_min:
                continue
            g_star = c["stage2"]["max_corr_factor"]
            g_ic = self._get_library_factor_ic(g_star)
            conflicts = self._count_library_conflicts(c)
            if (abs(c["stage1"]["ic_mean"]) >= self.config.replacement_ic_ratio * abs(g_ic)
                    and conflicts == 1):
                replacements.append({"new_factor": c, "replaces": g_star})
        return replacements

    def _batch_dedup(self, candidates):
        """Stage 3: Remove intra-batch duplicates."""
        if len(candidates) <= 1:
            return candidates
        # Compute pairwise correlation, keep higher-IC factor in each correlated pair
        ...

    def _full_validation(self, candidates):
        """Stage 4: Full validation on complete asset set."""
        universe = self._get_full_universe()
        validated = []
        for c in candidates:
            values = self._compute_factor(c["expression"], universe)
            full_stats = self._compute_full_metrics(values)
            c["stage4"] = full_stats
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

    def _compute_ic(self, factor_values: pd.DataFrame) -> dict:
        """Compute daily cross-sectional Spearman IC."""
        # Merge with T+1 returns
        # Group by date, compute Spearman correlation
        # Return ic_mean, ic_std, ic_ir, ic_win_rate
        ...

    def _max_library_correlation(self, factor_vals, library_vals) -> tuple:
        """Compute max cross-sectional Spearman correlation with library."""
        # For each library factor, compute time-averaged cross-sectional correlation
        # Return (max_correlation, most_correlated_factor_id)
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
          price_daily.vwap   → $vwap
          computed: $returns = close / Ref(close, 1) - 1
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

| Operator | Definition | Reason |
|----------|-----------|--------|
| SignedPower | sign(x) * \|x\|^p | Non-linear transformation |
| TsDecay | Time-decay weighted average | Recency weighting |
| Scale | Normalize to [-1, 1] cross-sectionally | Cross-sectional normalization |
| Corr | Rolling correlation between two series | Price-volume correlation |
| Inv | 1/x | Inverse transformation |
| Sqrt | sqrt(x) | Square root |
| Square | x^2 | Square |
| Exp | exp(x) | Exponential |
| Tanh | tanh(x) | Bounded non-linearity |

### Base Feature Fields

```
# Price fields (from price_daily)
$open, $high, $low, $close, $volume, $amount, $vwap

# Computed fields
$returns = $close / Ref($close, 1) - 1

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
    custom_universe: List[str] = None     # Custom stock pool

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
    stage4:
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
  stage2_passed: 3
  stage2_rejected: 3
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
