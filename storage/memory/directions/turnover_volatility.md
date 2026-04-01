---
name: turnover_volatility
status: active
category: liquidity
source: batch_021
parent_factor: null
attempts: 1
best_ic: 0.047
last_batch: batch_021
priority: high
created: '2026-03-29'
---

Volatility of turnover rate at various windows — captures trading behavior instability

## Rationale
High turnover volatility = speculative/erratic trading = underperformance. New signal dimension unlocked by $turnover_rate field.

## Probe Records
- 2026-03-29: Std($turnover_rate, 20) → IC=-0.036, ICIR=-0.334 — STRONG

## Candidate History
- batch_021: turnover_vol_10 ADMITTED as F027 (IC=-0.047, ICIR=-0.533, max_corr=0.655)
- batch_021: turnover_vol_20 ADMITTED as F031 (IC=-0.044, ICIR=-0.492, max_corr=0.697)
- batch_021: turnover_vol_60 ADMITTED as F032 (IC=-0.035, ICIR=-0.412, max_corr=0.556)
