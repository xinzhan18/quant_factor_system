# Factor Report Redesign — Professional Quant Research Report

**Date**: 2026-03-28
**Status**: Draft
**Scope**: Redesign the factor report system from a senior quant analyst's perspective

## Problem Statement

The current factor report has four systemic issues:
1. **Missing analysis dimensions**: No risk attribution, no turnover/cost analysis, no industry/size stratification, no market regime conditioning
2. **Calculation deficiencies**: IC only uses Spearman, no significance testing, no ICIR breakdown, quintile analysis lacks risk adjustment, decay analysis is oversimplified
3. **Narrative/structure issues**: LLM-generated analysis is template-driven, lacks analytical depth, doesn't anchor on decision questions
4. **Unreliable composite scoring**: 6 dimensions with arbitrary linear interpolation, uniqueness dimension hardcoded to 0.0, weights not justified

## Design Goals

- **Decision-driven**: Each report chapter answers a specific decision question a PM/researcher would ask
- **Graceful degradation**: Missing data dimensions show placeholders, not blank sections
- **Horizontally comparable**: Standardized structure and scoring enables cross-factor comparison
- **Three use cases**: Factor library inspection, research knowledge accumulation, team/PM reporting
- **Output**: Unified Obsidian Markdown + PNG (HTML pipeline deprecated)

## Report Structure

### 0. Factor Identity Card

**Purpose**: Quick reference and one-line verdict.

**Content**:
- Basic info: ID, name, expression, category, source batch, admission date
- KPI summary table: IC_IS, IC_OOS, ICIR, monotonicity, composite score, grade
- One-line conclusion (LLM-generated): must include IC value, grade, top strength, and top risk

**Frontmatter** (YAML):
```yaml
id: "011"
name: williams_r_variant
category: candlestick
expression: "Div(Sub(Mul(2, $close), $low), Sub($high, $low))"
batch: alpha101_batch_4
admitted_at: 2026-03-24
ic_mean_is: 0.0707
ic_mean_oos: 0.0815
icir: 0.5614
monotonicity: 0.9
composite_score: 72.5
composite_grade: B
data_level: L0
tags: [factor, candlestick]
```

### 1. Predictive Power — "How strong is this signal?"

**Analyzer**: `ICAnalyzer` (rewrite)

**Metrics**:
| Metric | IS | OOS |
|--------|----|----|
| RankIC (Spearman) | mean ± std | mean ± std |
| IC (Pearson) | mean ± std | mean ± std |
| ICIR | value | value |
| IC > 0 win rate | % | % |
| \|IC\| > 0.02 significant rate | % | % |
| t-statistic (H0: IC=0) | value (p-value) | value (p-value) |

**Computation changes from current**:
- Add Pearson IC alongside Spearman RankIC
- Add t-test for IC significance (scipy.stats.ttest_1samp)
- Compute ICIR separately for IS and OOS periods
- Replace hardcoded ±11% return clip with MAD-based adaptive clip: `median ± 5 * MAD` (MAD = median absolute deviation). The multiplier 5 is a config parameter. This adapts to the actual return distribution rather than using a fixed threshold.
- Forward return period configurable (default: 1 day)

**Charts** (5):
1. `ic_timeseries` — Daily IC line with IS/OOS split + 20/60-day moving average + ±0.02 reference lines
2. `ic_distribution` — IS vs OOS overlaid histogram with box plot
3. `rolling_ic` — 20/60/120-day rolling IC
4. `cumulative_ic` — Cumulative sum of daily IC
5. `monthly_heatmap` — Month × Year IC heatmap (RdBu_r)

**Verdict**: One-line LLM summary anchored on the question "How strong is this signal?"

### 2. Profitability — "Can this signal make money?"

**Analyzer**: `ProfitAnalyzer` (upgrade from `GroupReturnsAnalyzer`)

**Metrics**:
| Metric | Q1 | Q2 | Q3 | Q4 | Q5 | L/S |
|--------|----|----|----|----|----|----|
| Annualized return | | | | | | |
| Annualized volatility | | | | | | |
| Sharpe ratio | | | | | | |
| Sortino ratio | | | | | | |
| Calmar ratio | | | | | | |
| Max drawdown | | | | | | |
| Max DD duration (days) | | | | | | |

**Additional metrics**:
- Monotonicity: Spearman rank correlation between group rank and mean return
- Page's trend test p-value (`scipy.stats.page_trend_test`) — non-parametric monotonic trend test. Reshape daily quintile returns into a (dates × quintiles) matrix where columns are ordered Q1→Q5, then test for increasing trend. More appropriate than Jonckheere-Terpstra (which is not available in scipy).
- Annual group return breakdown (year × quintile matrix)
- Long contribution vs Short contribution decomposition

**Computation changes from current**:
- Add Sortino ratio: `annualized_return / annualized_downside_deviation` (downside_deviation = std of negative returns only, annualized by √252)
- Add Calmar ratio: `annualized_return / |max_drawdown|`
- Add max drawdown duration: number of trading days from peak to recovery (or peak to end if no recovery)
- Add Page's trend test (`scipy.stats.page_trend_test`) for monotonicity significance
- Add annual decomposition of group returns
- Add long/short contribution analysis

**Charts** (5):
1. `quintile_bar` — Annualized returns by quintile (RdYlGn)
2. `cumulative_returns` — Cumulative return curves for all 5 groups + L/S
3. `long_short` — L/S cumulative return with drawdown shading
4. `is_vs_oos_bar` — IS vs OOS grouped bar comparison
5. `annual_group_returns` — Year × Quintile heatmap (NEW)

**Verdict**: One-line on "Can this signal make money?"

### 3. Risk Attribution — "Is this alpha or beta?"

**Analyzer**: `RiskAttributor` (NEW, data-gated)

**Data requirement**: L1 (industry + market cap classification)

**Metrics (when data available)**:
- Barra-style factor exposure: size, momentum, volatility, liquidity, beta, residual_vol
- Industry exposure: top 3 over/underweight industries
- Purified alpha: IC after removing style factor exposures (OLS residualization)
- Purified alpha ICIR

**When data NOT available (L0)**:
- Qualitative analysis only (LLM analyzes the factor expression to infer likely style exposures)
- Show `> [!info] 风险归因需要行业和市值数据` callout
- Scoring uses neutral score (50)

**Charts (when available)** (2):
1. `style_exposure` — Horizontal bar chart of Barra factor exposures
2. `purified_ic_comparison` — Before/after purification IC time series

### 4. Conditional Analysis — "When does this signal work?"

**Analyzer**: `ConditionalAnalyzer` (NEW, partially data-gated)

**L0 analysis (OHLCV only)**:
- **Market regime**: Define using market breadth indicator (equal-weight universe mean return, 60-day cumulative). Note: this is NOT a CSI300 proxy — it captures broad market breadth skewed toward small/mid caps. Thresholds are initial defaults; validate by checking resulting regime distribution (target ~25% bull / 50% range / 25% bear):
  - Bull: > +10%
  - Bear: < -10%
  - Range-bound: otherwise
- **Volatility regime**: 20-day realized volatility of universe, split at median into High/Low
- For each regime: compute IC mean, ICIR, and group return spread

**L1 analysis (+ industry/market cap)**:
- Market cap stratification: Large (top 30%), Mid (30-70%), Small (bottom 30%) — IC per bucket
- Industry stratification: IC per industry (Shenwan L1)

**Annual IC decomposition**: Already exists but enhanced with market regime labels

**Charts** (2):
1. `conditional_ic` — Grouped bar: IC by market regime + volatility regime (NEW)
2. `annual_ic_decomposition` — Annual IC bars with regime color coding (enhanced existing)

**Verdict**: "When should you use/avoid this factor?"

### 5. Decay & Tradability — "How long does the signal last? How much capital can it handle?"

**Analyzer**: `DecayAnalyzer` (upgrade)

**Metrics**:
| Holding Period | IC | IC Ratio (vs 1d) |
|---------------|-----|------------------|
| 1d | | 1.00 |
| 2d | | |
| 5d | | |
| 10d | | |
| 20d | | |
| 60d | | |

**Additional metrics**:
- Half-life (days): first period where IC ratio ≤ 0.5
- Optimal rebalancing frequency: inferred from IC decay curve
- Factor autocorrelation at lags [1, 2, 3, 5, 10, 15, 20]
- Factor coverage: % non-NaN, time series
- Factor distribution stats: mean, std, skew, kurtosis (IS + OOS)

**Computation changes from current**:
- Add 2-day holding period
- Add explicit optimal rebalancing recommendation
- Merge distribution analysis into this chapter (was separate module)
- [Reserved for L2]: Turnover estimation, transaction cost analysis

**Charts** (4):
1. `ic_decay` — Bar chart of IC by holding period + decay curve overlay
2. `autocorrelation` — Lag vs autocorrelation line chart
3. `distribution` — IS vs OOS factor value histogram overlay
4. `coverage` — Daily coverage % time series

**Verdict**: "Recommended rebalancing frequency: X days"

### 6. Uniqueness — "Does the library still need this factor?"

**Analyzer**: `UniquenessAnalyzer` (NEW, replaces hardcoded 0.0)

**Computation**:
1. Load all admitted factor values from DB (factor_values table)
2. For each pair (this factor, library factor): compute cross-sectional rank correlation, then average across dates
3. Output: sorted correlation list, top-5 most correlated
4. Incremental IC: regress this factor's values on all library factor values (cross-sectional OLS per date), then compute IC of residuals

**Metrics**:
- Max correlation to library: value + which factor
- Top-5 correlated factors list
- Incremental IC (after removing library factor exposures)
- Incremental ICIR

**Charts** (1):
1. `correlation_bar` — Horizontal bar chart of correlations with all library factors, sorted descending (NEW)

**Verdict**: "Correlation with F0XX is 0.YY — [redundant/provides incremental value]"

### 7. Composite Score

**Analyzer**: `CompositeScorer` (rewrite)

**7-Dimension Scoring**:

| Dimension | Source Metric | Scoring Function | Weight |
|-----------|--------------|-----------------|--------|
| Predictive Power | \|RankIC_OOS\| | S-curve: midpoint=0.03, k=92 | 25% |
| Signal Stability | ICIR_OOS | S-curve: midpoint=0.3, k=9.2 | 20% |
| Profitability | L/S Sharpe | S-curve: midpoint=0.5, k=4.6 | 15% |
| Monotonicity | \|Spearman rank corr\| | Linear: 0→0, 1.0→100 | 10% |
| OOS Robustness | IC drift ratio | Inverse S-curve (see below) | 15% |
| Uniqueness | max_corr | Inverse linear: 0→100, 0.7→57, 1.0→0 | 10% |
| Decay Resistance | IC_20d / IC_1d | Linear: 0→0, 0.7+→100 | 5% |

**S-curve scoring function**:
```python
def s_curve_score(x, midpoint, k):
    """Sigmoid scoring: score ≈ 50 at midpoint, approaches 0/100 at extremes."""
    return 100.0 / (1.0 + math.exp(-k * (x - midpoint)))
```
Deriving k: given midpoint (x where score=50) and x_high (x where score≈99), solve `k = ln(99) / (x_high - midpoint)`:
- Predictive Power: midpoint=0.03, x_high=0.08 → k = ln(99)/0.05 ≈ 92
- Signal Stability: midpoint=0.3, x_high=0.8 → k = ln(99)/0.5 ≈ 9.2
- Profitability: midpoint=0.5, x_high=1.5 → k = ln(99)/1.0 ≈ 4.6

**OOS Robustness scoring**:
```python
def robustness_score(ic_is, ic_oos):
    """Inverse scoring: lower drift = higher score."""
    if abs(ic_is) < 0.01:  # edge case: IC_IS near zero
        return 50.0  # neutral — can't assess drift meaningfully
    drift = abs(ic_oos - ic_is) / abs(ic_is)
    return max(0, 100.0 * (1.0 - drift))  # 0% drift→100, 100% drift→0
```

**Uniqueness scoring**: Use max_corr directly with inverse linear mapping. `score = max(0, 100 * (1 - max_corr / 0.7))` capped at 100. This gives: max_corr=0 → 100, max_corr=0.35 → 50, max_corr=0.7 → 0. Factors at the admission threshold (corr=0.7) score 0, fully unique factors score 100. Good dynamic range for the library.

**Data-missing handling**: Dimensions without data use score=50 (neutral), marked with dashed line on radar chart.

**Grade scale**: S(90+) / A(75-89) / B(60-74) / C(45-59) / D(<45)

**Library ranking**: Show this factor's rank out of N admitted factors.

**Charts** (1):
1. `radar` — 7-dimension radar chart, dashed lines for data-missing dimensions

### 8. LLM Narrative Analysis

**Framework**: Each analysis chapter gets a narrative section driven by:

```yaml
narrative_config:
  identity:
    task: "One-line summary: is this factor worth attention?"
    constraint: "Must include IC value, grade, top strength, and top risk"

  predictive_power:
    task: "Answer: Is this signal strong? Is it stable?"
    constraint: "Must compare IS vs OOS IC and ICIR, interpret significance test results"

  profitability:
    task: "Answer: Can the signal make money? How much?"
    constraint: "Must analyze L/S return sources (long vs short contribution), discuss A-share short-selling constraints"

  risk_attribution:
    task: "Answer: Is the return from alpha or beta?"
    constraint: "If data missing, do qualitative analysis based on factor expression"

  conditional:
    task: "Answer: When should you use/avoid this factor?"
    constraint: "Must give concrete usage recommendations, not just describe phenomena"

  decay_tradability:
    task: "Answer: How often to rebalance? How much capital?"
    constraint: "Give explicit rebalancing recommendation based on half-life"

  uniqueness:
    task: "Answer: Does the library still need this factor?"
    constraint: "If high correlation, must discuss incremental contribution"

  critical_review:
    task: "Take the opposing view: find the most likely failure modes"
    constraint: "At least 3 specific risk points, each with data support. Maintain sharp/witty tone."
```

**Narrative quality anchors**:
- Lead with **conclusion**, not description ("IC decayed 30% OOS — signal is unstable" NOT "We observe that IC changed from X to Y")
- Each paragraph must cite at least 2 specific numbers from report_data.json
- Critical review maintains "毒舌" style but must be data-driven
- All narratives in Chinese with English technical terms

## Data Degradation Strategy

```
L0: OHLCV (current) → Ch1, Ch2, Ch4(regime+vol), Ch5, Ch6 fully available
L1: + industry/market_cap → Ch3(simplified Barra), Ch4(industry+size stratification)
L2: + turnover/amount → Ch3(full), Ch5(cost estimation)
L3: + minute-level → Ch5(market impact)
```

**Rules**:
- Missing modules in `report_data.json` set to `null`
- LLM narrative skips null modules but does qualitative analysis where possible
- Scoring uses neutral score (50) for missing dimensions, radar chart uses dashed lines
- Each missing section shows Obsidian callout: `> [!info] 数据待补充：需要 [具体数据] 才能解锁此分析`

## Chart Specification

**Total**: 20 charts per factor (14 existing redesigned + 6 new), of which 2 are data-gated (L1+). At L0 data level: 18 charts.

| # | Chart | Chapter | Format | Size |
|---|-------|---------|--------|------|
| 1 | ic_timeseries | Ch1 | PNG | 900×400@2x |
| 2 | ic_distribution | Ch1 | PNG | 900×400@2x |
| 3 | rolling_ic | Ch1 | PNG | 900×400@2x |
| 4 | cumulative_ic | Ch1 | PNG | 900×400@2x |
| 5 | monthly_heatmap | Ch1 | PNG | 900×400@2x |
| 6 | quintile_bar | Ch2 | PNG | 900×400@2x |
| 7 | cumulative_returns | Ch2 | PNG | 900×400@2x |
| 8 | long_short | Ch2 | PNG | 900×400@2x |
| 9 | is_vs_oos_bar | Ch2 | PNG | 900×400@2x |
| 10 | annual_group_returns | Ch2 | PNG | 900×400@2x (NEW) |
| 11 | style_exposure | Ch3 | PNG | 900×400@2x (NEW, data-gated) |
| 12 | purified_ic | Ch3 | PNG | 900×400@2x (NEW, data-gated) |
| 13 | conditional_ic | Ch4 | PNG | 900×400@2x (NEW) |
| 14 | annual_ic | Ch4 | PNG | 900×400@2x |
| 15 | ic_decay | Ch5 | PNG | 900×400@2x |
| 16 | autocorrelation | Ch5 | PNG | 900×400@2x |
| 17 | distribution | Ch5 | PNG | 900×400@2x |
| 18 | coverage | Ch5 | PNG | 900×400@2x |
| 19 | correlation_bar | Ch6 | PNG | 900×400@2x (NEW) |
| 20 | radar | Ch7 | PNG | 600×600@2x |

**Chart style**: Use `plotly_white` template (matching existing codebase convention), consistent color palette across all analyzers. Theme config extracted to `charts/theme.py`.

## report_data.json Schema

The builder outputs this structure. Each top-level key corresponds to a report chapter. Keys set to `null` indicate data-gated sections not yet available.

```python
{
    "factor": {                          # Ch0: Identity card
        "id": "011",
        "name": "williams_r_variant",
        "expression": "Div(...)",
        "category": "candlestick",
        "batch": "alpha101_batch_4",
        "admitted_at": "2026-03-24",
        "data_level": "L0"              # L0/L1/L2/L3
    },
    "predictive_power": {                # Ch1
        "summary": {
            "is": {"rank_ic_mean": float, "rank_ic_std": float, "ic_mean": float, "ic_std": float,
                    "icir": float, "win_rate": float, "significant_rate": float,
                    "t_stat": float, "p_value": float},
            "oos": { ... same keys ... }
        },
        "annual": [{"year": int, "rank_ic": float, "icir": float, "regime": str}, ...],
        "monthly_heatmap_data": [[year, month, ic], ...],
        "charts": {"ic_timeseries": str, "ic_distribution": str, "rolling_ic": str,
                   "cumulative_ic": str, "monthly_heatmap": str}
    },
    "profitability": {                   # Ch2 (was "quintile")
        "stats": [{"group": "Q1".."Q5", "ann_return": float, "ann_vol": float,
                   "sharpe": float, "sortino": float, "calmar": float,
                   "max_dd": float, "max_dd_duration": int}, ...],
        "ls_stats": { ... same metrics for long-short ... },
        "monotonicity": float,
        "page_test_pvalue": float,
        "annual_group_returns": [[year, Q1_ret, Q2_ret, Q3_ret, Q4_ret, Q5_ret], ...],
        "long_contribution": float,      # % of L/S return from long side
        "short_contribution": float,
        "charts": {"quintile_bar": str, "cumulative_returns": str, "long_short": str,
                   "is_vs_oos_bar": str, "annual_group_returns": str}
    },
    "risk_attribution": null | {         # Ch3 (null at L0)
        "style_exposures": {"size": float, "momentum": float, ...},
        "industry_exposures": {"银行": float, ...},
        "purified_ic": float,
        "purified_icir": float,
        "charts": {"style_exposure": str, "purified_ic": str}
    },
    "conditional": {                     # Ch4
        "regime_ic": {"bull": {"ic": float, "icir": float},
                      "bear": {...}, "range": {...}},
        "vol_regime_ic": {"high": {"ic": float, "icir": float},
                          "low": {...}},
        "size_ic": null | {"large": float, "mid": float, "small": float},  # L1+
        "industry_ic": null | {"银行": float, ...},  # L1+
        "charts": {"conditional_ic": str, "annual_ic": str}
    },
    "decay_tradability": {               # Ch5 (was "decay" + "distribution")
        "ic_by_period": [{"days": int, "ic": float, "ratio": float}, ...],
        "half_life_days": int | null,
        "optimal_rebalance_days": int,
        "autocorrelation": [{"lag": int, "corr": float}, ...],
        "distribution": {
            "stats_is": {"mean": float, "std": float, "skew": float, "kurtosis": float,
                         "coverage": float, "nan_ratio": float},
            "stats_oos": { ... same ... }
        },
        "charts": {"ic_decay": str, "autocorrelation": str, "distribution": str, "coverage": str}
    },
    "uniqueness": {                      # Ch6
        "max_corr": float,
        "max_corr_factor": str,          # e.g. "F009 pv_corr_times_vol"
        "top5_correlated": [{"factor": str, "corr": float}, ...],
        "incremental_ic": float,
        "incremental_icir": float,
        "charts": {"correlation_bar": str}
    },
    "composite": {                       # Ch7
        "dimensions": [
            {"name": str, "score": float, "data_available": bool}, ...
        ],
        "composite_score": float,
        "composite_grade": str,          # S/A/B/C/D
        "library_rank": int,
        "library_total": int,
        "charts": {"radar": str}
    }
}
```

Chart values in `charts` dicts are PNG file paths (relative to vault/assets/FXXX/) when in vault mode, or inline Plotly HTML when in legacy mode.

## Architecture Changes

### File Structure (target)

```
src/report/
├── __init__.py
├── builder.py              # ReportDataBuilder (orchestrator) — rewrite
├── scorer.py               # CompositeScorer — rewrite
├── analytics/
│   ├── __init__.py
│   ├── ic.py               # ICAnalyzer — rewrite
│   ├── profit.py           # ProfitAnalyzer — rename + upgrade from groups.py
│   ├── risk.py             # RiskAttributor — NEW
│   ├── conditional.py      # ConditionalAnalyzer — NEW
│   ├── decay.py            # DecayAnalyzer — upgrade (absorb distribution.py)
│   └── uniqueness.py       # UniquenessAnalyzer — NEW
├── charts/
│   └── theme.py            # Shared Plotly theme config (extract from analyzers)
└── templates/              # Legacy HTML (deprecated, kept for reference)
    └── factor_report.html.j2
```

### Key Design Decisions

1. **Distribution analyzer merged into DecayAnalyzer** — distribution stats (coverage, skew, kurtosis) are part of "tradability" assessment, not a standalone concern
2. **Chart theme extracted** — all analyzers share one Plotly theme config instead of duplicating style code
3. **HTML pipeline deprecated** — template kept for reference but not maintained
4. **Builder orchestrates, analyzers compute** — builder handles data loading and chart export, analyzers are pure computation + figure generation

### Skill Update

The `factor-report` skill needs updating to match the new 7-chapter structure:
- New narrative config with per-chapter task/constraint (see Section 8 above)
- Updated frontmatter schema (add `data_level`, `composite_score`)
- New Obsidian callout patterns for data-missing sections
- Updated chart wikilink list (20 charts, 2 data-gated)
- Markdown template mapping (old → new):
  - "构造逻辑" → embedded in each chapter's verdict + Ch8 narrative
  - "经济解读" → Ch8 "经济学直觉" section
  - "A股市场背景" → Ch8 "A股市场适用性" section
  - "分析图表" → distributed into Ch1-Ch7 inline with analysis
  - "批判性审查" → Ch8 "批判性审查" section (preserved)

### Migration Notes

- Existing `FactorReportCard` in `mining/metrics.py` is kept for the mining evaluation pipeline (quick screening). The new report system's `CompositeScorer` is for in-depth analysis — different use cases, no conflict.
- Existing hardcoded `_REGIME_LOOKUP` in `ic.py` (lines 21-25) must be removed — replaced by `ConditionalAnalyzer`'s dynamic regime computation.
- Existing `distribution.py` analyzer is absorbed into `DecayAnalyzer` — file can be deleted after migration.

## Implementation Priorities

**Phase 1 (L0 data — immediate)**:
1. Rewrite ICAnalyzer (add Pearson, t-test, ICIR breakdown)
2. Upgrade ProfitAnalyzer (Sortino, Calmar, JT test, annual decomposition)
3. New ConditionalAnalyzer (market regime + volatility, OHLCV only)
4. New UniquenessAnalyzer (correlation matrix from DB)
5. Rewrite CompositeScorer (7 dimensions, S-curve, proper weights)
6. Update ReportDataBuilder (orchestrate new analyzers)
7. Extract chart theme
8. Update factor-report skill

**Phase 2 (L1 data — after data sync)**:
1. New RiskAttributor (Barra exposure, industry exposure)
2. Extend ConditionalAnalyzer (industry/size stratification)

**Phase 3 (L2+ data — future)**:
1. Turnover estimation in DecayAnalyzer
2. Transaction cost analysis
3. Market impact estimation

## Success Criteria

- A senior quant analyst reading the report can answer all 7 decision questions without looking elsewhere
- Every analysis chapter has a clear verdict backed by specific numbers
- Cross-factor comparison is possible through standardized scoring and structure
- Report generates successfully with L0 data, gracefully shows placeholders for missing dimensions
- LLM narrative is conclusion-first, data-driven, and avoids template-driven filler
