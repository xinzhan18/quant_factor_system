---
name: value_x_reversal
status: active
category: valuation
source: crossover
parent_factor: F028
attempts: 1
best_ic: 0.0331
last_batch: batch_022
priority: high
created: '2026-03-31'
logic_id: L009
---

Cross-dimensional signal: valuation (1/PB) × price reversal.
Logic: cheap stocks (low PB) with recent decline = deep value buying opportunity.
Crossover of L009 (价值估值效应) and L001 (中期动量反转).

## Rationale
Probe: Mul(1/PB, neg_ret20) IC=+0.022 WinRate=57.9%.
F028 (inverse_pb alone) IC=+0.028. Cross-signal should improve timing by filtering
to cheap stocks that have shown weakness (price decline after being cheap = potential
value realization trigger). Consistent with L009 hypothesis.

## Probe Records
2026-03-31 | Mul(Div(1,Add($pb_ratio,0.001)), neg_ret20) | IC=+0.022 ICIR=+0.120 WinRate=57.9% | batch_022

## Candidate History
- batch_022 (2026-03-31): 3个候选, 1个录取
  - admitted: pb_x_reversal_10 (F035) IC=0.0331 ICIR=0.2435 OOS_decay=0.97
  - rejected: pb_x_reversal_20 IC=0.0295 — 与F035结构重叠，窗口更长但IC更低
  - rejected: pb_rank_x_reversal_20 IC=-0.0264 — 方向翻转(IS monotonicity=0.0), win_rate=39.3%
  - 结论: 1/PB × 短期反转(10d)有效; 20d窗口没有增量价值; ts_rank(PB)变换无效
  - 下次: 尝试PE/PS × 反转, 或加市值中性化
