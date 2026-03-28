---
name: intraday_range_patterns
status: exhausted
category: candlestick
source: baseline
parent_factor: null
attempts: 1
best_ic: 0.044
last_batch: batch_019
priority: medium
created: '2026-03-28'
---

Mean((H-L)/C, N) and close position Div(C-L, H-L) have strong IC

## Rationale
Baseline: avg_range_5d IC=-0.064, close_position IC=-0.053, upper_shadow IC=0.053. Williams %R variant IC=0.067.

## Probe Records
- 2026-03-29: Smoothed Williams %R — 3d IC=+0.037, 5d IC=+0.036, 10d IC=+0.034
- 2026-03-29: Body range ratio IC=+0.021, signed body sum 5d IC=-0.012

## Candidate History
- batch_019: smoothed_williams_r_3 REJECTED (IC=0.044 but corr=0.804 with F011)
- batch_019: smoothed_williams_r_5 REJECTED (IC=0.042 but corr=0.770 with F001)
- batch_019: smoothed_williams_r_10 REJECTED (IC=0.041 but corr=0.831 with F001)
- **Conclusion**: All smoothed variants too correlated with existing factors. Direction exhausted at corr<0.7.
