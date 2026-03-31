---
name: turnover_level
status: active
category: liquidity
source: batch_021
parent_factor: null
attempts: 1
best_ic: 0.046
last_batch: batch_021
priority: high
created: '2026-03-29'
---

Average turnover rate level and changes — captures liquidity/speculation regime

## Rationale
High turnover = speculative activity = negative alpha. Classic A-share liquidity factor.

## Probe Records
- 2026-03-29: Mean($turnover_rate, 20) → IC=-0.032, ICIR=-0.279 — STRONG
- 2026-03-29: Delta(Mean($turnover_rate, 5), 5) → IC=-0.020, ICIR=-0.184 — GOOD

## Candidate History
- batch_021: mean_turnover_20 ADMITTED as F029 (IC=-0.038, ICIR=-0.397, max_corr=0.668)
- batch_021: mean_turnover_5 ADMITTED as F033 (IC=-0.046, ICIR=-0.477, max_corr=0.645)
- batch_021: turnover_change_5 ADMITTED as F030 (IC=-0.022, ICIR=-0.287, max_corr=0.454)
