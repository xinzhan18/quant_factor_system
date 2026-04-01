---
name: size_value_crossover
status: active
category: other
source: crossover
parent_factor: F037,F038
attempts: 1
best_ic: 0.031
last_batch: batch_024
priority: high
created: '2026-04-01'
logic_id: L010
---

Crossover of size factor (F038 inverse_circ_mktcap) and valuation factors (F028/F037).
Multiplicative combination amplifies stocks that are BOTH small AND cheap.

## Rationale
Probe: 1/circ_mktcap × 1/PB IC=+0.037 ICIR=0.458 WinRate=68.6% — exceptional.
Both components independently admitted. Product creates non-linear synergy:
small cheap stocks get double-amplified signal vs either factor alone.

## Probe Records
2026-04-01 | Mul(Div(1, Add($circ_market_cap,1)), Div(1, Add($pb_ratio,0.001))) | IC=+0.037 ICIR=+0.458 WinRate=68.6% | pre-batch_024

## Candidate History
- batch_024 (2026-04-01): 3个候选, 2个录取(1新增+1替换)
  - admitted: size_x_ps (F039) IC=0.021 mono_IS=mono_OOS=1.0 ls_t=4.65 (近乎完美)
  - replaced F038: inverse_circ_mktcap(IC=0.012) → size_x_pb(IC=0.031, 2.58x提升)
  - rejected: size_x_low_pb_rank — mono=0.0(IS), ls_tstat=0.039，完全不显著
  - 结论: size×valuation crossover是高质量信号；下次尝试size×pe_clean, size×turnover
