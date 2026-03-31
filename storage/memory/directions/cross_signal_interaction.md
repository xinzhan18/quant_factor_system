---
name: cross_signal_interaction
status: exhausted
category: composite
source: batch_020
parent_factor: factor_025
attempts: 1
best_ic: 0.027
last_batch: batch_020
priority: low
created: '2026-03-29'
---

Multiplicative combinations of independent signal dimensions (vol_reversal × WR, vol_reversal × Resi)

## Rationale
Hypothesis: multiplying two orthogonal signals produces a decorrelated composite.
Reality: products are dominated by the stronger component — corr with parent remains high.

## Probe Records
- 2026-03-29: vol_reversal_5 × WR → IC=+0.027, ICIR=0.338, WinRate=66.9%

## Candidate History
- batch_020: vol_reversal_x_wr_5 REJECTED (corr=0.972 with F025)
- batch_020: vol_reversal_x_wr_3 REJECTED (corr=0.734 with F025)
- batch_020: vol_reversal_x_wr_10 REJECTED (IC=0.025 < 0.03 threshold; corr=0.641 OK)
- batch_020: vol_reversal_x_resi REJECTED (IC=0.011, monotonicity=-0.1, garbage)
- batch_020: ranked_vol_reversal_x_wr REJECTED (corr=0.746 with F022)

## Lesson
Multiplying factor A × factor B produces signal highly correlated with whichever component is stronger (here F025). Only decorrelates when the weaker component dominates, but then IC drops below threshold. Cross-signal products are NOT a viable decorrelation strategy for OHLCV daily.
