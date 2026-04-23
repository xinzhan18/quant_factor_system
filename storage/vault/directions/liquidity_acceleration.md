---
direction_tag: liquidity_acceleration
status: saturated
priority: low
rounds: 2
admits: 0
last_batch: batch_032
last_admits: []
last_goal: 推进 liquidity_acceleration T001：测试更长分母 10d/120d 与 volume base 的流动性加速度，确认是否能在
  F001 amount CV 吸收之外产生正 incremental_ic；同时用长窗 normalized acceleration 对照短窗 delta 失败是否只是噪声问题。
last_activity: '2026-04-23T14:52:59Z'
created_batch: batch_023
members: []
retired_members: []
merged_into: null
---
# liquidity_acceleration

> [!abstract]+ 方向概要
> **状态**　🟡 saturated · priority=low · rounds=1 · admits=0
> **最近**　[[batches/batch_032/judge|batch_032]] · 2026-04-23 · admit=0 / reserve=6 / reject=0
> **一句话**　batch_023 与 batch_032 累计 9 个候选都证明 liquidity acceleration 是真实信号，但在当前日频 DSL 空间里只会复现 F001 吸收后的 reserve pattern。

---

## Hypothesis

> [!note]+ 🔵 exploring · 理论正交但实证重叠
> 流动性指标（amount, turnover_rate）的**加速度**（rate-of-change，非水平）携带超出 F001 (amount CV 离散度) 之外的信号。
> - amount/turnover 突变 → 关注度切换（事件驱动 vs 失去兴趣）
> - F001 测稳定性，本方向测**变化方向**——理论正交
> - 实证：batch_023 rank-order 强却 incr_ic 全负，与 F001 **同向冲突**

> [!warning]+ 饱和说明（batch_032 后追加）
> batch_032 把 T001 的剩余 DSL 空间基本补齐：`$volume` base、10d/120d 长分母、以及长窗 normalized acceleration 三条路径全部落在 **“统计强 + incremental_ic 负”** 的同一象限。
>
> **结论**：在当前日频 DSL 空间里，liquidity acceleration 不是待 admit 的新家族，而是**被 F001 吸收后的 reserve family**。继续新增同类 reserve 不再提升知识密度，因此方向转 saturated。

---

## Threads

### T001: 长窗 ratio / normalized liquidity acceleration 能否逃离 F001 吸收 [✗ DISPROVEN batch_032]

> [!failure]+ Thread 结论
> **Question**: amount / turnover / volume 的长窗 ratio 与 normalized acceleration，是否能在 F001 之外独立贡献 forward IC？
> **Evidence trail**:
> - [[batches/batch_023/candidates/C001|batch_023 C001]]　5d/60d amount → ic=-0.043 ls_t=-2.92 mono=-1.00 incr_ic=-0.030 corr=0.299@F001 → **reserve**
> - [[batches/batch_023/candidates/C003|batch_023 C003]]　5d/60d turnover → ic=-0.042 ls_t=-3.27 mono=-1.00 incr_ic=-0.026 → **reserve**（60d 分母比 5/20 更稳）
> - [[batches/batch_032/candidates/C001|batch_032 C001]]　5d/60d volume → ic=-0.043 ls_t=-3.02 mono=-1.00 incr_ic=-0.026 corr=0.304@F001 → **reserve**
> - [[batches/batch_032/candidates/C002|batch_032 C002]]　10d/120d volume → ic=-0.042 ls_t=-2.69 mono=-0.90 incr_ic=-0.022 corr=0.303@F002 → **reserve**
> - [[batches/batch_032/candidates/C003|batch_032 C003]]　10d/120d amount → ic=-0.043 ls_t=-2.61 mono=-1.00 incr_ic=-0.024 corr=0.304@F002 → **reserve**
> - [[batches/batch_032/candidates/C004|batch_032 C004]]　10d/120d turnover → ic=-0.041 ls_t=-2.92 mono=-0.90 incr_ic=-0.019 corr=0.309@F001 → **reserve**
> - [[batches/batch_032/candidates/C005|batch_032 C005]]　normalized amount accel → ic=-0.037 ls_t=-2.74 mono=-1.00 incr_ic=-0.019 corr=0.310@F001 → **reserve**
> - [[batches/batch_032/candidates/C006|batch_032 C006]]　normalized volume accel → ic=-0.037 ls_t=-2.87 mono=-0.60 incr_ic=-0.017 corr=0.321@F001 → **reserve**
>
> **Answer**: 否。无论换 `$volume` base、拉长到 10d/120d，还是把 short-minus-mid delta 再做长窗归一，**全部候选仍是负 signed incremental_ic**。这说明问题不在短窗噪声，也不在 field 选择，而在于该 family 在当前库空间已经被 F001/F002 吸收。
>
> **Revival conditions**: F001 退役、库结构重组、Python 真 residualization、或更高频数据进入后再开。

### T002: 短窗 normalized acceleration [✗ DISPROVEN batch_023]

> [!failure]+ 短窗 delta mono 弱
> **Question**: 5d-20d turnover normalized acceleration 是否可用？
> **Evidence trail**:
> - [[batches/batch_023/candidates/C002|batch_023 C002]]　5d-20d normalized accel → mono=-0.50 weak + 与 batch_004 C003 同源 → **reject**
>
> **结论**：短窗 normalized delta 形式 mono 不稳，需长分母（60d+）才能压住噪声。

---

## Known Failures

| Candidate | Expression | Reject Reason |
|---|---|---|
| [[batches/batch_023/candidates/C002\|C002]] | 5d-20d turnover normalized acceleration | mono=-0.50 weak + batch_004 C003 同源 |

---

## Lessons (direction-level)

- **5d/60d ratio** 比 5d-20d delta 稳定得多——长分母压住噪声
- **F001 吸收流动性 family**：corr ≈ 0.30 + incr_ic 全负 = 结构性约束，不是 over-rejection
- 短窗 normalized acceleration (mono ≤ 0.5) 直接 skip，首选 60d+ 分母
- **换 field / 换分母 / 换 normalized 写法都不打开新轴**：`$amount` / `$turnover_rate` / `$volume` 三条 base 在 5d/60d、10d/120d、以及 normalized delta 下全部给出负 signed incremental_ic
- **继续堆 reserve 没有知识增量**：当一个方向的所有候选都稳定落在“强统计 + 负增量”象限时，应转 saturated，而不是无限期保留更多同型 reserve

---

## Related

- 🟢 [[amount_volatility_signal]] — F001 (amount CV) 所在方向；核心 reserve 原因
- 🔴 [[fundamental_momentum]] `dead` — 同为"变化率" family，但 rank-order 弱；本方向 rank-order 强证明有结构性 edge

---

## Narrative Log

> [!quote]+ 2026-04-23 · [[batches/batch_032/judge|batch_032]]
> **admit=0 / reserve=6 / reject=0**
> batch_032 把 T001 的剩余日频 DSL 空间基本补齐：volume base（C001/C002/C006）、10d/120d 长分母（C002/C003/C004）、以及 normalized acceleration（C005/C006）全部成功复现“**统计强 + incremental_ic 负**”的 reserve pattern。
>
> - C001 是本批最干净的代表性 reserve：5d/60d volume 证明“换到 `$volume`”也逃不开 F001 吸收
> - C002/C003/C004 证明 10d/120d 长分母只是在更稳定地复现同一风格载体，不能打开新轴
> - C005/C006 证明 normalized acceleration 的问题不只是短窗太噪，长窗版本仍无正边际
> - **MT budget**　cumulative 152 → **158** · direction 3 → **9** · bucket `medium`
>
> **Operations**　`status: exploring → saturated` · `priority: medium → low`

> [!quote]+ 2026-04-21 · [[batches/batch_023/judge|batch_023]]
> **admit=0 / reserve=2 (C001+C003) / reject=1 (C002)**
> C001/C003 双 mono=-1.00 + ls_t -2.92/-3.27，但 corr≈0.30@F001 + incr_ic 全负 → reserve。C002 mono=-0.50 reject。
> **核心发现**：A 股流动性加速度 rank-order 极强但被 F001 吸收——结构性约束；F001 退役后 C001/C003 可复活。
