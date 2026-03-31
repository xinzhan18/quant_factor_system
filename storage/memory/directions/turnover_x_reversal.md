---
name: turnover_x_reversal
status: active
category: liquidity
source: crossover
parent_factor: F027
attempts: 1
best_ic: 0.0392
last_batch: batch_022
priority: high
created: '2026-03-31'
logic_id: L004
---

Cross-dimensional signal: turnover (level or volatility) × price reversal.
Logic: high-activity stocks that declined recently face mean reversion.
Crossover of L004 (换手率流动性) and L001 (动量反转).

## Rationale
Probe: Mul(Std($turnover_rate,10), neg_ret5) IC=+0.024 WinRate=59.9%.
High win rate suggests a stable pattern. Turnover volatility selects stocks with
erratic investor participation; recent decline selects potential reversal candidates.
Active traders step in → short-term bounce.

## Probe Records
2026-03-31 | Mul(Std($turnover_rate,10), neg_ret5) | IC=+0.024 ICIR=+0.140 WinRate=59.9% | batch_022

## Candidate History
- batch_022 (2026-03-31): 2个候选, 1个录取
  - admitted: turnover_level_x_reversal_20 (F036) IC=0.0286 ICIR=0.2073
  - rejected: turnover_vol_x_reversal_5 IC=0.0391 corr=0.926 with F003 (换手率波动率方向已饱和，level比vol更有独特性)
  - 结论: 换手rate水平 × 反转方向有效; 下次尝试其他窗口或与市值交叉
