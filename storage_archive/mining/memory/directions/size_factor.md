---
name: size_factor
status: active
category: other
source: genesis
parent_factor: null
attempts: 1
best_ic: 0.012
last_batch: batch_023
priority: high
created: '2026-04-01'
logic_id: L010
---

Market capitalization size factors. A-shares are known for a small-cap premium driven
by retail investor attention, lower institutional coverage, and liquidity constraints.
$circ_market_cap and $market_cap are available but completely untested as of batch_023.

## Rationale
L010 (规模效应) has gen=0, adm=0 — no factors ever generated for this logic.
Probe: 1/(circ_market_cap+1) IC=+0.016 WinRate=55.8%. Borderline signal but
completely new dimension with expected low correlation to OHLCV and turnover factors.

## Probe Records
2026-04-01 | Div(1, Add($circ_market_cap, 1)) | IC=+0.016 ICIR=+0.155 WinRate=55.8% | pre-batch_023

## Candidate History
- batch_023 (2026-04-01): 3个候选, 1个录取
  - admitted: inverse_circ_mktcap (F038) IC=0.012 IC_OOS=0.012 mono_IS=mono_OOS=1.0 ls_t=2.92
  - rejected: smallcap_x_reversal_10 — corr=0.755 with F035（超阈值）
  - rejected: circ_mktcap_rank_60 — ic_max_drawdown=-43（极不稳定），与F036 corr=0.675接近边界，与F038信号重叠
  - 结论: 小市值直接因子有效(inverse形式)；rank形式不稳定；×reversal交叉信号因corr被挡；下次尝试市值中性化或与其他维度交叉
