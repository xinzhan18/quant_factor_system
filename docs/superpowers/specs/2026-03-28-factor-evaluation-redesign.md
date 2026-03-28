# Factor Evaluation Redesign: 6-Dimension Metrics + LLM Admission

## Problem

Current evaluation pipeline computes 8 metrics in Stage 3 but uses **none** of them for admission decisions. A factor that passes Stage 1 IC screening (|IC| >= 0.03 on 50 stocks) and Stage 2 correlation check automatically gets admitted — even if OOS IC is negative, monotonicity is zero, or long-short returns reverse.

## Solution

1. **Stage 3 becomes a comprehensive metrics computation station** — produces a 6-dimension "report card" with ~30 metrics
2. **No hardcoded admission threshold in Stage 3** — all screening candidates are returned as `screened` (not `admitted`)
3. **LLM in Ralph Loop skill reviews the report card** and makes admission decisions with reasoning

## Architecture

```
候选因子
  │
  ▼
Stage 0: 表达式语法校验 ─── 失败 → rejected        (硬规则, 不变)
  │
  ▼
Stage 1: 快筛 IC (50 stocks) ─── |IC| < 0.03 → rejected  (硬规则, 不变)
  │
  ▼
Stage 1.5: 批内去重 ─── corr >= 0.7 → 留 IC 高的     (硬规则, 不变)
  │
  ▼
Stage 2: 因子库相关性 ─── corr >= 0.7 → rejected/替换  (硬规则, 不变)
  │
  ▼
Stage 2.5: 替换检查                                   (硬规则, 不变)
  │
  ▼
Stage 3: 6 维指标计算 → 生成 FactorReportCard          (新: 只算不判)
  │
  ▼
返回 BatchResult(screened=[...], rejected=[...], replacements=[...])
  │
  ▼
factor-mine skill: LLM 审判 → 录取 / 淘汰 / 替换 + 理由  (新)
```

## Stage 3: FactorReportCard

### Data Structure

```python
@dataclass
class FactorReportCard:
    """6-dimension evaluation report card for a single factor."""

    # --- Dimension 1: Predictive Power ---
    ic_mean: float              # Daily cross-sectional Spearman IC mean
    ic_std: float               # IC standard deviation
    ic_ir: float                # IC information ratio (ic_mean / ic_std)
    ic_win_rate: float          # Fraction of days with IC > 0
    ic_by_year: Dict[int, float]    # {2020: 0.04, 2021: 0.03, ...}
    ic_by_month: Dict[int, float]   # {1: 0.03, 2: 0.01, ..., 12: 0.04}

    # --- Dimension 2: Robustness ---
    ic_mean_oos: float          # Out-of-sample IC mean
    ic_ir_oos: float            # Out-of-sample ICIR
    oos_decay_ratio: float      # ic_mean_oos / ic_mean (>0.8 robust, <0.5 overfit)
    ic_autocorr: float          # IC series lag-1 autocorrelation
    ic_max_drawdown: float      # Max drawdown of cumulative daily IC
    worst_quarter_ic: float     # IC of worst calendar quarter
    best_quarter_ic: float      # IC of best calendar quarter

    # --- Dimension 3: Economic Coherence ---
    quantile_returns_is: Dict[str, float]   # IS quintile returns {q1: -.002, ...}
    quantile_returns_oos: Dict[str, float]  # OOS quintile returns
    monotonicity_is: float      # IS quintile monotonicity (Spearman)
    monotonicity_oos: float     # OOS quintile monotonicity
    ls_return: float            # Long-short return (Q5 - Q1)
    ls_tstat: float             # Long-short t-statistic
    ic_sign_consistent: bool    # IS and OOS IC have same sign

    # --- Dimension 4: Decay & Turnover ---
    ic_decay: Dict[int, float]  # IC at different horizons {1: 0.035, 5: 0.028, 10: 0.015, 20: 0.005}
    half_life_days: float       # Estimated days until IC halves
    factor_turnover: float      # Daily average rank change rate
    factor_autocorr: float      # Factor value lag-1 autocorrelation (cross-sectional avg)

    # --- Dimension 5: Coverage & Distribution ---
    coverage: float             # Fraction of non-NaN values
    zero_ratio: float           # Fraction of zero values
    factor_skew: float          # Cross-sectional skewness (time-averaged)
    factor_kurt: float          # Cross-sectional kurtosis (time-averaged)
    extreme_ratio: float        # Fraction of values beyond 3σ (pre-winsorize)

    # --- Dimension 6: Uniqueness ---
    max_lib_corr: float         # Max correlation with any library factor
    max_corr_factor_id: str     # ID of most correlated library factor
    lib_corr_profile: Dict[str, float]  # Correlation with each library factor
    incremental_ic: float       # Residual IC after regressing out library factors
    expression_depth: int       # Expression nesting depth
```

### Computation Details

#### Dimension 1: Predictive Power

`ic_by_year` and `ic_by_month` are computed by grouping the daily IC series by year/month and averaging within each group. These use the same daily IC values already computed for `ic_mean` — no additional factor computation needed.

#### Dimension 2: Robustness

- `oos_decay_ratio`: Simple division `ic_mean_oos / ic_mean`. Handle division by zero (ic_mean ≈ 0) by returning NaN.
- `ic_autocorr`: `np.corrcoef(ic_series[:-1], ic_series[1:])[0, 1]` on the daily IC array.
- `ic_max_drawdown`: Compute cumulative sum of daily IC, then max drawdown of that curve.
- `worst_quarter_ic` / `best_quarter_ic`: Group daily IC by calendar quarter `(year, quarter)`, average within each, return min/max.

#### Dimension 3: Economic Coherence

- `quantile_returns_oos`: Same as IS quantile computation but on OOS period.
- `ls_tstat`: Compute daily long-short returns (Q5 mean - Q1 mean per day), then `t = mean(daily_ls) / (std(daily_ls) / sqrt(n_days))`.
- `ic_sign_consistent`: `sign(ic_mean) == sign(ic_mean_oos)`.

#### Dimension 4: Decay & Turnover

- `ic_decay`: Compute IC against forward returns at horizons 1d, 5d, 10d, 20d. Requires computing multi-horizon forward returns: `Ref($close, -h) / $close - 1` for each horizon `h`.
- `half_life_days`: Fit exponential decay `IC(h) = IC(1) * exp(-h/τ)` to `ic_decay` values. Half-life = `τ * ln(2)`. If non-monotonic decay, use linear interpolation.
- `factor_turnover`: For each day, compute Spearman correlation of factor ranks between day t and t-1. Turnover = `1 - mean(daily_rank_corr)`.
- `factor_autocorr`: Same rank correlation, just report the mean directly.

#### Dimension 5: Coverage & Distribution

All computed from the raw factor DataFrame before preprocessing:
- `coverage`: `1 - (n_nan / n_total)`
- `zero_ratio`: `n_zero / n_total`
- `factor_skew` / `factor_kurt`: Cross-sectional skew/kurt per day, then time-averaged.
- `extreme_ratio`: Count values where `|z_score| > 3` divided by total non-NaN values.

#### Dimension 6: Uniqueness

- `lib_corr_profile`: Already computed as `_lib_correlations` in Stage 2 — just expose it in the report card.
- `incremental_ic`: For each day, regress the factor's cross-sectional values on all library factor values, take residuals, compute IC of residuals vs returns. Average across days. **Expensive** — O(n_library * n_stocks * n_days). Skip if library is empty.
- `expression_depth`: Already available from `ExpressionValidator`.

### Performance Budget

Current Stage 3 takes ~5 min per factor (full universe computation + IS/OOS split).

New computation costs (per factor):
- Dimension 1 (ic_by_year/month): ~0s (groupby on existing IC series)
- Dimension 2 (robustness): ~0s (statistics on existing IC series)
- Dimension 3 (OOS quantiles, t-stat): ~30s (OOS factor values already computed)
- Dimension 4 (decay): ~2 min (3 additional forward-return horizons × IC computation)
- Dimension 5 (distribution): ~0s (statistics on existing factor values)
- Dimension 6 (incremental IC): ~1-3 min (regression, depends on library size)

**Total**: ~8-10 min per factor (up from ~5 min). For a batch of 8, ~60-80 min total.

## BatchResult Changes

```python
@dataclass
class BatchResult:
    screened: List[Dict[str, Any]]      # Passed Stage 1-2, has full FactorReportCard
    rejected: List[Dict[str, Any]]      # Failed Stage 0/1/2
    replacements: List[Dict[str, Any]]  # Stage 2.5 replacement candidates (also have report cards)

    def to_dict(self) -> Dict[str, Any]:
        """Serializable output for YAML."""
        ...
```

Key change: `admitted` → `screened`. Nothing is "admitted" until LLM decides.

Each factor dict in `screened` will contain:
```python
{
    "name": "factor_name",
    "expression": "Qlib_expression",
    "category": "category",
    "stage1": {...},         # Quick screening IC
    "stage2": {...},         # Correlation check result
    "report_card": {...},    # Full 6-dimension FactorReportCard as dict
}
```

## CLI Changes

```bash
# Default: compute metrics only, save to result YAML (no admission)
python3 -m mining batch batch_XXX.yaml

# Auto-admit all screened factors (skip LLM, backward compatible)
python3 -m mining batch batch_XXX.yaml --admit
```

When `--admit` is used, all `screened` factors are admitted directly (same as current behavior, for automation/testing).

Without `--admit`, the result YAML contains full report cards for LLM review in the skill.

## Skill Integration (factor-mine.md)

### Step 4: Evaluate (modified)

```bash
python3 -m mining batch mining/candidates/batch_XXX.yaml
```

Note: NO `--admit` flag. Results saved to `batch_XXX_result.yaml` with full report cards.

### Step 5: LLM Review & Admit (new)

Read `batch_XXX_result.yaml`. For each `screened` factor, print the report card and make a judgment.

**LLM must output structured judgment for each factor:**

```
=== 因子审判: {name} ===
表达式: {expression}
类别: {category}

预测力: IC={ic_mean:.4f}, ICIR={ic_ir:.2f}, 逐年趋势={ic_by_year}
稳健性: OOS衰减比={oos_decay_ratio:.2f}, 最差季度={worst_quarter_ic:.4f}, IC回撤={ic_max_drawdown:.4f}
经济性: 单调性IS={monotonicity_is:.2f}/OOS={monotonicity_oos:.2f}, 多空t={ls_tstat:.2f}, 符号一致={ic_sign_consistent}
衰减:   半衰期={half_life_days:.1f}天, 换手率={factor_turnover:.3f}
分布:   覆盖率={coverage:.1%}, 零值={zero_ratio:.1%}, 偏度={factor_skew:.2f}
唯一性: 最大库相关={max_lib_corr:.3f}({max_corr_factor_id}), 增量IC={incremental_ic:.4f}

判定: [录取 / 淘汰 / 替换 factor_XXX]
理由: [2-3句具体理由，引用报告卡中的数字]
```

**LLM judgment guidelines (embedded in skill):**

Red flags (should normally reject):
- `ic_sign_consistent = False` (IS/OOS direction flip)
- `oos_decay_ratio < 0.3` (severe overfitting)
- `coverage < 0.5` (too many missing values)
- `monotonicity_oos` opposite sign from `monotonicity_is`
- `half_life_days < 1` (signal dies before you can trade it)

Strong signals (favor admission):
- `ic_ir > 0.15` with `oos_decay_ratio > 0.7`
- `ls_tstat > 2.0` (statistically significant)
- `monotonicity_is > 0.8` and `monotonicity_oos > 0.5`
- `incremental_ic > 0.02` (genuine new information)
- Low `expression_depth` with high IC (Occam's razor)

These are **guidelines**, not rules. The LLM weighs all dimensions holistically.

After judgment, for each admitted factor:
```python
from mining.library import FactorLibrary
from mining.config import MiningConfig

lib = FactorLibrary(MiningConfig())
factor['metrics'] = _normalize_metrics(factor['report_card'])
lib.admit(factor)
```

## File Changes

| File | Change |
|------|--------|
| `mining/evaluator.py` | Add `FactorReportCard` dataclass; refactor `_full_validation` into `_compute_report_card`; add dimension computation methods; rename `admitted` → `screened` in `BatchResult` |
| `mining/config.py` | Add `decay_horizons: List[int] = [1, 5, 10, 20]` config |
| `mining/cli.py` | Update `cmd_batch` to handle `screened` instead of `admitted`; update `_normalize_metrics` for report card format |
| `.claude/skills/factor-mine.md` | Rewrite Steps 4-6 for LLM review flow; add judgment guidelines and report card template |
| `tests/mining/test_evaluator.py` | Add tests for new metrics; update for `screened` rename |

## Testing Strategy

1. **Unit tests for each dimension**: Mock factor/return DataFrames, verify each metric computation
2. **Integration test**: Run a known factor through full pipeline, verify report card completeness
3. **Edge cases**: Empty factor values, single-stock days, NaN-heavy data, zero-IC factors
4. **Backward compatibility**: `--admit` flag still works, auto-admits all screened

## Migration

Existing `factor_XXX.yaml` files in the library keep their current metrics format. New admissions will have the full report card stored under `metrics`. The `get_factor_ic()` method already handles both `ic_mean` and `ic_mean_is` keys.
