---
direction_tag: return_momentum_acceleration
status: dead
priority: medium
rounds: 1
admits: 0
last_batch: batch_029
last_admits: []
last_goal: 3 候选测 return momentum delta / ratio 信号。与 fundamental_momentum (rate 形式失败)
  对照；这里是价格 return 非 fundamental ratios。
last_activity: '2026-04-21T16:40:05Z'
created_batch: batch_029
members: []
retired_members: []
merged_into: null
---
# return_momentum_acceleration

> [!abstract]+ 方向概要
> **状态**　🔴 dead · priority=medium · rounds=1 · admits=0
> **最近**　[[batches/batch_029/judge|batch_029]] · 2026-04-21 · admit=0 / reserve=0 / reject=3
> **一句话**　price return 的 rate/delta 形式在 A 股 csi1000 不携稳定 alpha，3/3 候选全 weak 或 mono_sign_flip。

---

## Hypothesis

Return momentum (mean return over window) 变化率可能携带信息——加速（从慢 momentum 到快）vs 减速 反映资金流变化。假设路径：(1) 5d mean return 减 20d mean return 捕捉"近端加速"；(2) 5d/20d ratio 捕捉"相对加速强度"；(3) Delta(5d mean, 5) 捕捉"二阶变化"。

与 fundamental_momentum（PE/PB/PS 纯变化率已全 reject）对照：本方向用**价格 return**而非 fundamental ratios，验证 rate 形式失败是 fundamental-specific 还是更普适的 structural failure。

> [!warning] ⚠️ Hypothesis 已证伪（batch_029）
> 3 个 DSL 候选全 reject：C001 (5d-20d spread) ls_t=-0.81 弱 + mono=-0.40 + incr_ic=-0.020 库 reducer；C002 (5d/20d ratio) CP01 hard_gate mono_sign_flip IS=+0.70/OOS=-0.70 彻底不稳定；C003 (Δ5d of 5d mean) ls_t=-0.49 几乎随机 + mono=-0.30。与 fundamental_momentum 失败原理同源——**rate/delta 形式对信号稳定性不利**，level/mean 形式保留更多可用结构（对比：F010 hhi_vol_20 level 形式 ls_t=7.50）。
> **元教训**　第 5 次观察 **rate/delta form 失败** 模式（前有 fundamental_momentum / return_distribution / liquidity_acceleration ratio / asymmetric_momentum ratio / 本 batch）。**一阶/二阶 rate-of-change 在 A 股 csi1000 cross-section 不携稳定 alpha**——下一次设计含 "变化率 / 加速度 / ratio" 形式候选时默认跳过，改走 level-based 或 level × interaction 路径。

---

## Threads

### T001: Return momentum 变化率 [✗ DISPROVEN batch_029]

> [!failure]+ Thread 结论
> **Question**: 5d/20d return momentum 的 spread / ratio / delta 是否携带独立 forward IC？
> **Evidence trail**:
> - [[batches/batch_029/candidates/C001|batch_029 C001]]　5d-20d return spread `Sub(Mean(ret,5), Mean(ret,20))` → ic=-0.023 ls_t=-0.81 mono=-0.40 r²=0.085 a_surv=1.515 corr=0.499@F006 incr=-0.020 → reject (ls_t<1 weak + 库 reducer)
> - [[batches/batch_029/candidates/C002|batch_029 C002]]　5d/20d return ratio `Div(Mean(ret,5), Abs(Mean(ret,20))+ε)` → CP01 hard_gate **mono_sign_flip** IS=+0.70 / OOS=-0.70 → reject (方向性翻转)
> - [[batches/batch_029/candidates/C003|batch_029 C003]]　Δ5d of 5d return mean `Delta(Mean(ret,5), 5)` → ic=-0.020 ls_t=-0.49 mono=-0.30 r²=0.065 a_surv=1.354 corr=0.423@F006 incr=-0.018 → reject (ls_t 几乎随机)
>
> **Conclusion**: 三种变体（差/比/delta）全 weak；对比 F010 hhi_vol_20 level 形式 ls_t=7.50，证明 rate 形式本身是 structural failure，不是窗口/字段选择问题。

---

## Known Failures

| Candidate | Expression | Reject Reason |
|---|---|---|
| [[batches/batch_029/candidates/C001\|C001]] | 5d-20d return spread | ls_t=-0.81 weak + mono=-0.40 + incr_ic=-0.020 库 reducer + corr=0.499@F006 |
| [[batches/batch_029/candidates/C002\|C002]] | 5d/20d return ratio | **CP01 hard_gate mono_sign_flip** IS=+0.70 / OOS=-0.70 (方向不稳定) |
| [[batches/batch_029/candidates/C003\|C003]] | Δ5d of 5d return mean | ls_t=-0.49 catastrophic weak + mono=-0.30 + incr_ic=-0.018 |

---

## Related

- 🔴 [[fundamental_momentum]] `dead` — 同源失败：PE/PB/PS 纯变化率 ls_t -1.22 到 -1.81 全 weak；本方向用 price return 代替 fundamental ratios，结论相同 → rate 形式通用失败
- 🔴 [[asymmetric_momentum]] `dead` — up-only / down-only return 分解全 reject，另一种 return 结构变体证伪
- 🔴 [[return_distribution_signals]] `dead` — return 分布类 rate-form 信号同样全证伪
- 🔴 [[liquidity_acceleration]] `dead` — turnover ratio / 变化率 全 reject，liquidity 侧 rate form 失败
- 🟡 [[overnight_intraday_split]] `saturated` — overnight/intraday 时段分解方向，与本方向"时间尺度差"机制邻近

---

## Narrative Log

> [!quote]+ 2026-04-21 · [[batches/batch_029/judge|batch_029]]
> **admit=0 / reserve=0 / reject=3** — return momentum rate/delta 形式首批 3 候选全证伪：C001 5d-20d spread ls_t=-0.81 weak；C002 5d/20d ratio CP01 hard_gate mono_sign_flip；C003 Δ5d of 5d mean ls_t=-0.49 近随机。
> - T001 return momentum 变化率：`[◉ ACTIVE] → [✗ DISPROVEN batch_029]`
> - **核心元教训**：第 5 次观察 rate/delta form 失败（fundamental_momentum / return_distribution / liquidity_acceleration ratio / asymmetric_momentum ratio / 本 batch）→ **一阶/二阶 rate-of-change 在 A 股 csi1000 cross-section 不携稳定 alpha**，已 promote 为系统级 lesson。
> - **Level vs rate 对比**：F010 hhi_vol_20 level 形式 ls_t=7.50 vs C001 rate 形式 ls_t=-0.81 — 印证 level/mean 保留更多 structure。
> - **MT budget**: 本 batch 消耗 3 tests（134 cumulative / 3 per-direction），全 reject，无 admit 占预算。
> - **Direction operations**: status `exploring → dead`（不可逆）；priority=medium 不下调（首批即封闭，无需再 retry）；不进入 retry pool。
