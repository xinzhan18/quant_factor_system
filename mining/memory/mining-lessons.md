# Factor Mining — Problems & Lessons Learned

## 1. Engineering Problems

### 1.1 Qlib Operator System
- **Problem**: Used `Operators.register()` which internally maps `cls.__name__` → fails when class name differs from expression name
- **Fix**: Direct injection `Operators._ops[name] = cls`
- **Problem**: `Neg`, `TsRank`, `TsMax`, `TsMin`, `SMA`, `Correlation` NOT registered in pyqlib 0.9.7
- **Fix**: Alternatives: `Mul(x,-1)` for Neg, `Rank(x,N)` for TsRank, `Max(x,N)` for TsMax, `Corr` for Correlation

### 1.2 Custom Operator Implementation
- Rolling ops must override `_load_internal()` and call `super().__init__(feature, N, func_name)`
- NpElemOperator for element-wise ops (e.g., `Tanh`)
- PairOperator/SignedPower must handle numeric args — check `isinstance(feature, Expression)` before `.load()`
- **C.kernels = 1 mandatory** — multiprocessing workers don't inherit `_ops` registry

### 1.3 Data Pipeline
- `D.instruments('all')` returns `{'market': 'all'}` dict, not stock codes — pass to `D.features()` then extract from index
- `$amount` and `$vwap` fields are zero — data source didn't populate these
- evaluate_batch returns `BatchResult` (dataclass with `.admitted`, `.rejected`, `.replacements`) — NOT iterable directly
- evaluate_batch does NOT persist results to library.yaml — must call `lib.admit()` separately

### 1.4 YAML Serialization
- Result YAML files may contain pandas DataFrame objects under `_factor_values`
- `yaml.safe_load` fails → use `yaml.unsafe_load` or avoid serializing DataFrames
- Factor replacement via `lib.replace()` stores `ic_mean: null` if metrics dict key is `ic_mean_is` instead of `ic_mean` — manual fix needed

## 2. Mining Strategy Problems

### 2.1 Blind Exploration vs Systematic Inclusion (Most Costly Mistake)
- **Wasted effort**: Batches 002-006 ran without proper context, used wrong operator names (`Correlation` → `Corr`, `TsMax` → `Max`)
- **Wasted effort**: Batches 010-017 (78 candidates, 0 admissions) explored random constructions when classic Alpha101 factors hadn't been tried
- **Lesson**: ALWAYS start with known good factors (Alpha101, Barra, technical indicators), THEN explore novel constructions
- **Lesson**: Systematic translation of published factor libraries first; creative mining second

### 2.2 Threshold Management
- Original corr_max=0.5 was too strict — rejected rank_ret_times_rank_vol at corr=0.501
- Relaxing to 0.7 enabled 12 additional admissions from Alpha101 batch
- **Lesson**: Start with looser thresholds (0.7), tighten later when library is large
- **Lesson**: Always inspect near-misses (corr 0.45-0.55) — small threshold changes have big impact

### 2.3 Stage 1 IC Inflation
- 50-stock, ~14-day Stage 1 screening shows inflated IC values
- `consecutive_up_score` had IC=0.104 on 14 days but IC=0.009 on full 1092 days
- **Lesson**: Never trust Stage 1 IC for absolute values — only use for relative ranking/filtering
- **Lesson**: Stage 1 should filter obvious garbage, not identify winners

## 3. A-Share Market Insights

### 3.1 Volatility Dominance ("Black Hole" Effect)
- Factor 001 (std_returns_20, IC=-0.058) correlates 0.6-0.9 with ALL strong signals
- Low vol anomaly is THE fundamental alpha in A-shares daily OHLCV
- All measures (Std, MAD, RealizedVol, AmihudIlliq, IQR, Q90) are essentially the same signal
- **Dividing by volatility DESTROYS signal** — `range_over_vol` IC=-0.008, `resi_over_vol` IC=-0.004

### 3.2 OHLCV Signal Space Boundaries
- After 24 factors admitted from 260+ candidates screened, diminishing returns severe
- Daily OHLCV has ~3-4 independent signal dimensions: volatility, volume patterns, candlestick geometry, short-term reversal
- Long momentum (>20d) is essentially dead in A-shares: return_60d IC=-0.009
- Autocorrelation, entropy, kurtosis (standalone) are all noise: |IC| < 0.01

### 3.3 What Works
- **Candlestick geometry**: Williams %R variant (IC=+0.070), upper shadow ratio (IC=+0.035)
- **Volatility**: std_returns_20 (IC=-0.058), ATR (IC=-0.044)
- **Volume**: pv_corr_times_vol (IC=-0.052), rank_ret*rank_vol (IC=-0.041)
- **Regime switching**: vol_regime_reversal (IC=-0.044) — MUST use asymmetric payloads
- **Alpha101 composites**: alpha024 (IC=+0.049), alpha038 (IC=+0.035), alpha023 (IC=+0.030)
- **Signed nonlinear**: SignedPower(ret, 0.5) (IC=-0.032)

### 3.4 Symmetric IfElse Trap
- `If(cond, x, Mul(x, -1))` always produces identical values regardless of condition → corr=1.0
- MUST use asymmetric payloads: different signals in each branch

## 4. Alpha101 Translation Notes

### 4.1 Translatable (~45 of 101)
- Cross-sectional `rank()` → time-series `Rank(x, 60)` (60-day rolling percentile)
- `ts_rank(x, d)` → `Rank(x, d)`
- `delay(x, d)` → `Ref(x, d)`
- `ts_argmax/ts_argmin` → `IdxMax/IdxMin`
- `sum(x, d)` → `Sum(x, d)`, `mean(x, d)` → `Mean(x, d)`
- `sign(x)` → `Sign(x)`, `abs(x)` → `Abs(x)`

### 4.2 Not Translatable (~55 of 101)
- ~35 require `$vwap` (adv20 * vwap combinations)
- ~18 require industry neutralization or `IndNeutralize()`
- ~2 require market cap weighting
- Cannot be implemented until additional data sources are added

### 4.3 Alpha101 Yield
- 60 candidates → 12 admitted + 1 replacement = 21.7% yield (vs 5.9% for blind mining)
- Strongest: williams_r_variant (IC=+0.070), alpha024 (IC=+0.049)
- Classic formulas significantly outperform random constructions

## 5. Process Lessons

1. **Baseline first**: Screen known good factors before creative exploration
2. **Classic libraries are gold**: Alpha101 yield (21.7%) >> blind mining (5.9%)
3. **Loose thresholds initially**: corr_max=0.7 enables comprehensive coverage; tighten later
4. **Persist immediately**: evaluate_batch doesn't auto-persist — call lib.admit() right after
5. **Check near-misses**: Factors at corr=0.45-0.55 may be admitted with small threshold changes
6. **Verify operator availability**: Test operators with trivial expressions BEFORE building complex formulas
7. **Stage 1 IC is noisy**: 50-stock/14-day IC can be 10x inflated vs full universe
8. **Vol is everything**: In A-shares, nearly all strong daily signals are volatility proxies
9. **Don't normalize by vol**: Dividing strong signals by Std(ret) destroys predictive power
10. **Track explicitly**: Maintain library.yaml, state.yaml, and insights.yaml — evaluate_batch results are ephemeral
