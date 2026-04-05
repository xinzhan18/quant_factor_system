---
name: pv_corr_window_variants
status: exhausted
category: volume
source: batch_019
parent_factor: factor_009
attempts: 1
best_ic: -0.039
last_batch: batch_019
priority: low
created: '2026-03-29'
---

Window variants of PV correlation × volatility (F009 = 10d window)

## Rationale
F009 uses Corr($close, $volume, 10) × Std(ret, 10). The 5d window version was admitted as F026 (IC=-0.039, corr=0.593 with F009). Shorter windows capture faster PV regime changes.

## Related Factors
factor_009, factor_026

## Probe Records
- 2026-03-29: pv_corr_times_vol_5 IC=-0.039, pv_corr_5d_only IC=-0.028

## Candidate History
- batch_019: pv_corr_times_vol_5 **ADMITTED** (F026) IC=-0.039, ICIR=-0.43, max_corr=0.593
- **Conclusion**: 5d variant admitted. Further window variants (3d, 7d) unlikely to add value given F009 (10d) and F026 (5d) already in library. Direction exhausted.
