---
name: amount_volatility
status: exhausted
category: volume
source: state_hint
parent_factor: null
attempts: 1
best_ic: -0.041
last_batch: batch_022
priority: low
created: '2026-03-31'
logic_id: L003
---

$amount-based volatility and correlation factors. $amount confirmed to have data.
Similar in spirit to volume volatility (F004) but $amount = price×volume, capturing
combined price-volume activity.

## Rationale
Probe: Std($amount, 20) IC=-0.035. Consistent with low-vol anomaly.
$amount differs from $volume because it incorporates price level — high $amount vol
means high price×volume activity, not just high volume count.

## Probe Records
2026-03-31 | Std($amount, 20) | IC=-0.035 ICIR=-0.272 WinRate=38.4% | batch_022

## Candidate History
- batch_022 (2026-03-31): 3个候选, 0个录取
  - rejected: amount_vol_10 IC=-0.041 corr=0.731 with F004, amount_vol_20 IC=-0.037 corr=0.785 with F004, amount_pv_corr_10 IC=-0.032 corr=0.858 with F009
  - 全部因与已有因子高度相关被Stage2淘汰; $amount方向与$volume信号空间高度重叠
