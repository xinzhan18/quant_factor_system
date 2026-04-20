---
direction_tag: vol_shock_signals
status: dead
priority: low
rounds: 1
admits: 0
last_batch: batch_024
last_admits: []
last_goal: 首批 3 DSL 候选测 vol shock 信号——今日 range vs 20d baseline、5d vol vs 60d vol regime
  change、Abs 收益 vs 20d baseline。与 F001 (amount CV) 稳态波动正交；测突发性。
last_activity: '2026-04-20T22:11:14Z'
created_batch: batch_024
members: []
retired_members: []
merged_into: null
---
# vol_shock_signals

## Hypothesis

**突发** vol 变化（相对于近期基线）反映 information flow shocks；与 F001 (amount CV 稳定性) 正交——F001 测稳态波动幅度，本方向测**突发性**（today vs baseline）。

## Current Focus

3 候选测 vol shock 在不同 horizon 的表现。

## Threads

### T001: 日内 range vs 20d baseline [✗ DISPROVEN batch_024]
**Evidence**: C001 ic=-0.029 ls_t=-2.25 incr_ic=-0.027 库 reducer → reject；C003 ic=+0.008 ls_t=2.97 **a_surv=0.117 catastrophic** (vol 衍生)
**Conclusion**: magnitude-based vol shock 无论 normalize 形式都 collapse to vol_20d。

### T002: 5d vol vs 60d vol (regime change) [✗ DISPROVEN batch_024]
**Evidence**: C002 hard_gate mono_sign_flip IS=+0.70 / OOS=-1.00 → reject
**Conclusion**: 短/长窗口 vol ratio 跨期行为不稳。

## Known Failures
- C001 (batch_024): today range / 20d mean range — ls_t=-2.25 borderline + incr_ic=-0.027 库 reducer
- C002 (batch_024): 5d/60d returns vol ratio — hard_gate mono_sign_flip (vol regime IS/OOS 完全反转)
- C003 (batch_024): Abs return shock - 20d baseline — **alpha_surv=0.117 catastrophic** (vol_20d-derived 第 4 次出现)

## Related
- [[amount_volatility_signal]]  (测稳态 CV)
- [[return_distribution_signals]]  (dead — 高阶矩 collapse to vol_20d)

## Narrative Log
### 2026-04-21 [[batches/batch_024/judge|batch_024]]
**admit=0 / reserve=0 / reject=3 — direction status: exploring → dead**

3 候选全 reject：库 reducer / hard_gate / vol_20d 衍生 catastrophic alpha_surv。**元教训**：magnitude-based vol shock 信号在 A 股 cross-section 全部 collapse to vol_20d (第 4 次独立观察)。后续 direction 设计应绝对避开 magnitude-only vol 信号。
