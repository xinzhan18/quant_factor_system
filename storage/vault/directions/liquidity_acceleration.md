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
> **状态**　🟡 saturated · priority=low · rounds=2 · admits=0
> **最近**　[[batches/batch_032/judge|batch_032]] · 2026-04-23 · admit=0 / reserve=6 / reject=0
> **一句话**　batch_023 + batch_032 累计 9 个候选证明 liquidity acceleration 是真实 rank-order 信号但被 F001 (amount CV) 完全吸收；rate-form 失败已升格为系统级 F300 教训。

---

## Hypothesis

> [!note]+ 🔵 exploring · 理论正交但实证重叠
> 流动性指标（amount, turnover_rate）的**加速度**（rate-of-change，非水平）携带超出 F001 (amount CV 离散度) 之外的信号。
> - amount/turnover 突变 → 关注度切换（事件驱动 vs 失去兴趣）
> - F001 测稳定性，本方向测**变化方向**——理论正交
> - 实证：batch_023 rank-order 强却 incr_ic 全负，与 F001 **同向冲突**

> [!warning]+ 饱和说明（batch_032 后追加）
> batch_032 把 T001 剩余 DSL 空间补齐：`$volume` base、10d/120d 长分母、长窗 normalized acceleration 三条路径全部落在 **"统计强 + incremental_ic 负"** 同一象限。在当前日频 DSL 空间里，liquidity acceleration 是**被 F001 吸收的 reserve family**，不再有 admit 可能。

> [!warning]+ ⚠️ 升格至系统律 (F300 / F004)
> 本方向是 **rate/delta/ratio 形式跨 csi1000 通用失效律** (F300, F004) 的 5+ 证伪源之一：
> - turnover/amount/volume 三条 base × 5d/60d × 10d/120d × normalized 全维度复现"rank-order 强 + signed incremental_ic 负" pattern
> - 与 fundamental_momentum (PE/PB/PS rate)、return_momentum_acceleration (5d-20d spread)、asymmetric_momentum (sign-conditional)、return_distribution (Q-range rate)、pv_covariance (Cov 形态) 同构失败
> - 对照律：F010 hhi_vol_20 **level** ls_t=7.50 整库记录 / F002 PB·amount **level** 可用 / F013 log 压缩 (非 rate) admit → 证明是 **rate 形式本身的 structural failure**
> - **设计准入**：未来本方向新候选默认 skip，除非 (a) Python residualization vs F001/F002 已检查 coverage <0.80，或 (b) F001 退役 / 更高频数据进入

---

## Threads

### T001: 长窗 ratio / normalized liquidity acceleration 能否逃离 F001 吸收 [✗ DISPROVEN batch_032]

> [!failure]+ Thread 结论
> **Question**: amount / turnover / volume 的长窗 ratio 与 normalized acceleration，是否能在 F001 之外独立贡献 forward IC？
> **Evidence trail**:
> - [[batches/batch_023/candidates/C001|batch_023 C001]]　5d/60d amount → ic=-0.043 ls_t=-2.92 mono=-1.00 incr_ic=-0.030 corr=0.299@F001 → **reserve**
> - [[batches/batch_023/candidates/C003|batch_023 C003]]　5d/60d turnover → ic=-0.042 ls_t=-3.27 mono=-1.00 incr_ic=-0.026 → **reserve**
> - [[batches/batch_032/candidates/C001|batch_032 C001]]　5d/60d volume → ic=-0.043 ls_t=-3.02 mono=-1.00 incr_ic=-0.026 corr=0.304@F001 → **reserve**
> - [[batches/batch_032/candidates/C002|batch_032 C002]]　10d/120d volume → ic=-0.042 ls_t=-2.69 mono=-0.90 incr_ic=-0.022 corr=0.303@F002 → **reserve**
> - [[batches/batch_032/candidates/C003|batch_032 C003]]　10d/120d amount → ic=-0.043 ls_t=-2.61 mono=-1.00 incr_ic=-0.024 corr=0.304@F002 → **reserve**
> - [[batches/batch_032/candidates/C004|batch_032 C004]]　10d/120d turnover → ic=-0.041 ls_t=-2.92 mono=-0.90 incr_ic=-0.019 corr=0.309@F001 → **reserve**
> - [[batches/batch_032/candidates/C005|batch_032 C005]]　normalized amount accel → ic=-0.037 ls_t=-2.74 mono=-1.00 incr_ic=-0.019 corr=0.310@F001 → **reserve**
> - [[batches/batch_032/candidates/C006|batch_032 C006]]　normalized volume accel → ic=-0.037 ls_t=-2.87 mono=-0.60 incr_ic=-0.017 corr=0.321@F001 → **reserve**
>
> **Answer**: 否。换 base、拉长窗、再做 normalized 全部产生负 signed incremental_ic。该 family 已被 F001/F002 吸收。
>
> **Revival conditions**: F001 退役、库结构重组、Python 真 residualization、或更高频数据进入。

### T002: 短窗 normalized acceleration [✗ DISPROVEN batch_023]

> [!failure]+ 短窗 delta mono 弱
> **Question**: 5d-20d turnover normalized acceleration 是否可用？
> **Evidence trail**:
> - [[batches/batch_023/candidates/C002|batch_023 C002]]　5d-20d normalized accel → mono=-0.50 weak + 与 batch_004 C003 同源 → **reject**
>
> **结论**：短窗 normalized delta mono 不稳，需 60d+ 分母压噪声。

---

## Known Failures

| Candidate | Expression | Reject Reason |
|---|---|---|
| [[batches/batch_023/candidates/C002\|C002]] | 5d-20d turnover normalized acceleration | mono=-0.50 weak + batch_004 C003 同源 |

---

## Lessons (direction-level)

- **5d/60d ratio** 比 5d-20d delta 稳定——长分母压噪声
- **F001 吸收流动性 family**：corr ≈ 0.30 + incr_ic 全负 = 结构性约束，非 over-rejection
- 短窗 normalized acceleration (mono ≤ 0.5) 直接 skip，首选 60d+ 分母
- **换 field / 换分母 / 换 normalized 写法都不打开新轴**：amount / turnover / volume 三条 base × 多窗口 × normalized 全部负 signed incremental_ic
- **继续堆 reserve 没有知识增量**：稳定落"强统计 + 负增量"象限即转 saturated
- **rate vs level 律**（升格至 F300）：本方向是系统级 rate-form 失效的 5+ 同构证据之一，level 形式才稳定

---

## Related

- 🟢 [[amount_volatility_signal]] — F001 (amount CV) 所在方向；核心 reserve 原因
- 🔴 [[fundamental_momentum]] `dead` — 同 rate-form 失效 (F300 同源证据)
- 🔴 [[return_momentum_acceleration]] `dead` — 同 rate-form 失效
- 🔴 [[asymmetric_momentum]] `dead` — 同 rate-form 失效
- 🔴 [[return_distribution_signals]] `dead` — 同 rate-form 失效
- 🔴 [[pv_covariance]] `dead` — Cov 形态归簇 F001/F009/F012

---

## Narrative Log

> [!quote]+ 2026-04-23 · [[batches/batch_032/judge|batch_032]]
> **admit=0 / reserve=6 / reject=0**
> T001 剩余日频 DSL 空间补齐：volume base (C001/C002/C006) + 10d/120d 长分母 (C002/C003/C004) + normalized acceleration (C005/C006) 全部"统计强 + incremental_ic 负"reserve。C001 是最干净代表 (5d/60d volume 仍逃不开 F001 吸收)。
> **MT budget**　cumulative 152→**158** · direction 3→**9** · bucket `medium`
> **Operations**　`status: exploring → saturated` · `priority: medium → low`

> [!quote]+ 2026-04-21 · [[batches/batch_023/judge|batch_023]]
> **admit=0 / reserve=2 (C001+C003) / reject=1 (C002)**
> C001/C003 双 mono=-1.00 + ls_t -2.92/-3.27，但 corr≈0.30@F001 + incr_ic 全负 → reserve。C002 mono=-0.50 reject。
> **核心发现**：A 股流动性加速度 rank-order 极强但被 F001 吸收——结构性约束；F001 退役后 C001/C003 可复活。
