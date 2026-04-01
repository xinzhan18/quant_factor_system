---
name: alpha101_composites
status: active
category: composite
source: baseline
parent_factor: factor_013
attempts: 7
best_ic: 0.0363
last_batch: batch_019
priority: high
created: '2026-03-28'
---

Multi-signal interaction formulas from WorldQuant Alpha101 paper

## Rationale
21.7% yield rate. Best: alpha024 IC=+0.049. Cross-sectional rank→Rank(x,60).

## Related Factors
factor_013, factor_014, factor_016, factor_017, factor_018, factor_021, factor_025

## Probe Records
- 2026-03-29: Alpha012 variants (sign(ΔVol)×(-ΔClose)) — 3d IC=+0.034, 5d IC=+0.036, 10d IC=+0.039

## Candidate History
- batch_019: vol_confirmed_reversal_5 **ADMITTED** (F025) IC=+0.036, ICIR=0.50, max_corr=0.433
- batch_019: vol_confirmed_reversal_10 REJECTED (inter-candidate corr >> 0.7 with F025)
- batch_019: vol_confirmed_reversal_3 REJECTED (OOS IC=0.028 < threshold; inter-candidate corr)
