---
name: valuation_pe_ps
status: active
category: valuation
source: genesis
parent_factor: F028
attempts: 1
best_ic: 0.020
last_batch: batch_023
priority: high
created: '2026-04-01'
logic_id: L009
---

Valuation factors based on PE and PS ratios — orthogonal to existing PB-based factors.
Logic: earnings yield (1/PE) and sales yield (1/PS) capture different dimensions of
cheapness than book value. PE reflects profitability, PS reflects revenue efficiency.

## Rationale
F028 (1/PB, IC=+0.028) and F034 (Rank(PB,60), IC=-0.038) confirmed valuation works.
Probe: 1/PE IC=+0.028 WinRate=59.5%; 1/PS IC=+0.022 WinRate=59.9%.
PE/PS are structurally independent from PB — different fundamental dimensions.

## Probe Records
2026-04-01 | Div(1, Add($pe_ratio, 0.001)) | IC=+0.028 ICIR=+0.267 WinRate=59.5% | pre-batch_023
2026-04-01 | Div(1, Add($ps_ratio, 0.001)) | IC=+0.022 ICIR=+0.233 WinRate=59.9% | pre-batch_023

## Candidate History
- batch_023 (2026-04-01): 3个候选, 1个录取
  - admitted: inverse_ps (F037) IC_OOS=0.020 mono_OOS=1.0 (稳定，OOS>IS)
  - rejected: inverse_pe — OOS单调性=-1.0（方向翻转），OOS衰减严重(0.45x)，ls_tstat=1.15不显著
  - rejected: pe_rank_60 — OOS_IC=-0.007接近零，OOS单调性=-0.10，OOS衰减严重(0.36x)
  - 结论: 1/PS有效; 1/PE OOS不稳定（PE含负值/极端值导致噪声大）; 下次尝试PS变体或其他窗口
