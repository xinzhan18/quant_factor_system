---
factor_id: "072"
name: pt_corr_20
category: volume
grade: B-est
score: TBD
logic_id: L003
admitted: 2026-04-03
tags: [factor, volume, price-turnover-correlation, grade-pending]
---

# F072 pt_corr_20

## Overview

| Metric | Value |
|--------|-------|
| Expression | `Corr($close, $turnover_rate, 20)` |
| Category | Volume / Microstructure |
| Logic | L003 (Volume-Price Divergence) |
| Grade | **Pending** (report builder Qlib Corr bug) |
| Rebalance | 20d |

**Rationale**: 20-day rolling correlation between close price and turnover rate. Low correlation = less herding behavior = healthier price formation. When price moves are not accompanied by proportional turnover changes, the stock has more diverse opinion and less momentum-chasing.

**Key Distinction from F009**: F009 uses `Corr($close, $volume)` — raw volume correlates with market cap. F072 uses `$turnover_rate` (volume/float) which is inherently cap-neutral. MaxCorr vs F009 = only 0.492.

## Predictive Power (from Evaluation)

| Metric | IS (2020-2023) | OOS (2024) |
|--------|----------------|------------|
| IC | -0.027 | -0.019 |
| ICIR | -0.317 | -0.163 |
| ls_tstat | | **-5.23** |
| ls_return | | -0.109%/day |

## Profitability (from Evaluation)

| Metric | IS | OOS |
|--------|-----|-----|
| Q1 (long) | 0.097%/day | **0.206%/day** |
| Q2 | 0.065%/day | 0.190%/day |
| Q3 | 0.055%/day | 0.168%/day |
| Q4 | 0.041%/day | 0.174%/day |
| Q5 (short) | -0.012%/day | 0.133%/day |
| **Monotonicity** | **-1.0** | **-0.9** |

> [!success] Exceptional OOS Monotonicity
> Mono_OOS = -0.9 is the best OOS monotonicity seen in the last 5 mining rounds (038-042). The signal maintains near-perfect quintile ordering out-of-sample, confirming regime robustness.

> [!tip] Long-Side Alpha Confirmed
> Q1_OOS (0.206%/day) clearly outperforms Q5_OOS (0.133%/day). The long side drives alpha, making this suitable for A-share long-only portfolios.

## Uniqueness

| Metric | Value |
|--------|-------|
| Max Corr | **0.492** (vs F009 pv_corr_times_vol) |

Highly independent. The key differentiation is using `$turnover_rate` (cap-neutral) instead of `$volume` (cap-correlated). The standalone Corr without vol multiplier also contributes to independence.

## Design Notes

- **Simplicity advantage**: The standalone `Corr()` without `× Std()` multiplier proved more regime-robust than the complex product version (Mono_OOS -0.9 vs -0.3).
- **Cap-neutral by construction**: `$turnover_rate = volume / float_shares`, already size-normalized.
- **Report generation blocked**: Qlib's Corr operator has a shape mismatch bug on full-range evaluation. Metrics above are from the batch evaluation pipeline which handles this correctly.
