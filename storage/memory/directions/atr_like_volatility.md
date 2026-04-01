---
name: atr_like_volatility
status: exhausted
category: volatility
source: baseline
parent_factor: factor_024
attempts: 1
best_ic: null
last_batch: null
priority: high
created: '2026-03-28'
---

Average True Range using nested If/Greater for max(H-L, |H-prevC|, |L-prevC|)

## Rationale
atr_like_14 IC=-0.044. Independent from Std(ret,20) at corr<0.7.

## Related Factors
factor_024

## Probe Records


## Candidate History
