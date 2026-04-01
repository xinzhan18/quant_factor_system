---
name: signed_nonlinear_returns
status: dead
category: other
source: baseline
parent_factor: null
attempts: 1
best_ic: null
last_batch: null
priority: high
created: '2026-03-28'
---

SignedPower(ret, 0.5) compresses outliers while preserving sign

## Rationale
Baseline: IC=-0.057. Strong but may be correlated with raw returns.

## Probe Records
2026-04-01 | SignedPower(Sub(Div($close,Ref($close,5)),1), 0.5) | IC=-0.024 ICIR=-0.117 WinRate=42.6% | pre-batch_024

## Candidate History
- batch_024 (2026-04-01): 3个候选, 0个录取
  - signed_sqrt_ret5: corr=1.000 with F003 — 5d return signal == vol_regime_reversal signal
  - signed_cbrt_ret1: corr=1.000 with F023 — 不同幂次对相关性无影响
  - signed_sqrt_ret3: corr=0.742 with F014
  - 结论: 所有SignedPower(ret_N, p)变体均被F003/F023/F014覆盖。方向已死。
