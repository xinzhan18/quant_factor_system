---
name: range_compression
status: exhausted
category: candlestick
source: baseline
parent_factor: factor_022
attempts: 2
best_ic: -0.030
last_batch: batch_019
priority: low
created: '2026-03-28'
---

Today's normalized range vs 60d average range ratio

## Rationale
IC=-0.042. Measures volatility regime relative to recent history.

## Related Factors
factor_022

## Probe Records
- 2026-03-29: range_volume_cross_20 (range×vol interaction) IC=-0.026 probe, -0.030 full

## Candidate History
- batch_019: range_volume_cross_20 REJECTED (IC=-0.030 but corr=0.811 with F022)
- **Conclusion**: Cross-dimension variant also too correlated. Direction exhausted.
