---
direction_tag: fundamental_momentum
status: dead
priority: low
rounds: 1
admits: 0
last_batch: batch_022
last_admits: []
last_goal: 首批 4 DSL 候选探索 PE/PB/PS 变化率作为 cross-section signal。Edge 来自 earnings drift
  + valuation mean-reversion；与 value_liquidity_interaction 的 PE×turnover 交互不同——这里是纯单一指标的变化率。目标
  ≥1 admit。
last_activity: '2026-04-20T20:09:07Z'
created_batch: batch_022
members: []
retired_members: []
merged_into: null
---
# fundamental_momentum

> [!abstract]+ 方向概要
> **状态**　🔴 dead · priority=low · rounds=1 · admits=0
> **最近**　[[batches/batch_022/judge|batch_022]] · 2026-04-21 · admit=0 / reserve=0 / reject=4
> **一句话**　PE/PB/PS 纯变化率在 A 股 csi1000 不构成独立 alpha——一轮 4/4 全 reject，方向关闭；并入跨 5+ 方向 rate-form 结构性失败律（F004/F300）。

---

## Hypothesis

> [!warning]+ ⚠️ Hypothesis 已证伪（batch_022，4/4 reject；并入跨方向 rate-form 失败律 F004/F300）
> **原假设**　PE/PB/PS 变化率（rate of change）携带超出绝对水平的预测信息：earnings drift（散户对 EPS 修订反应慢，drift 5-20 天）+ valuation mean-reversion + cross-section rotation。本方向意在填补 [[value_liquidity_interaction]] 未测的"纯变化率"缺口。
>
> **证伪证据**　ls_t 范围 -1.22 ~ -1.81（全 <2）；incr_ic 全负（库 reducer）；C002 PB rate **r²=0.811 catastrophic**（几乎完全 vol_20d 衍生）；rank-based variant (C003) 改善 mono=-0.70 但 ls_t 仍弱；等权聚合 (C004) 不救弱信号。
>
> **元教训（升格至系统级，F004/F300 跨方向证据并入）**　
> 1. A 股 csi1000 上 fundamental ratio 的**纯变化率形式**不构成独立 alpha；F002（PB/amount **绝对水平**）证明 fundamental 信号本身可行，**不可行的是"变化率"形式**——下一次考察 fundamental 信号默认跳 level / level × interaction。
> 2. 警惕"变化率 ≈ 波动率"共线性陷阱（C002 r²=0.811 直证）。
> 3. **跨方向第 5+ 次重现**（fundamental_momentum / return_momentum_acceleration / asymmetric_momentum / return_distribution_signals / liquidity_acceleration / pv_covariance）：rate / delta / ratio / sign-conditional 拆分在 csi1000 cross-section **结构性失效**，对照 F010 hhi_vol_20 level ls_t=7.50 整库记录。建议升格 lessons.md `Structural Constraints` 段「rate/delta/ratio default-skip」。

---

## Threads

> [!failure]+ T001+T002+T003　PE / PB / PS 变化率（单指标 + rank-trend + 等权聚合）[✗ DISPROVEN batch_022]
> **Question**: PE/PB/PS 的 20d 变化率（含 rank-trend 和等权聚合形式）是否在 cross-section 上携带独立 forward IC？
>
> **Evidence trail**:
> - [[batches/batch_022/candidates/C001|C001]] · 20d PE rate → ic=-0.025 ls_t=-1.22 mono=-0.30 r²=0.512 incr=-0.024 → reject（库 reducer）
> - [[batches/batch_022/candidates/C002|C002]] · 20d PB rate → ic=-0.032 ls_t=-1.49 **r²=0.811 catastrophic**（vol_20d 衍生）→ reject
> - [[batches/batch_022/candidates/C003|C003]] · PE rank trend → ic=-0.022 ls_t=-1.81 mono=-0.70 r²=0.315 → reject（rank 救 mono 不救 ls_t）
> - [[batches/batch_022/candidates/C004|C004]] · PE+PB+PS 等权聚合 rate → ls_t=-1.27 → reject（聚合不救弱信号）
>
> **Conclusion**:
> 1. 单一指标 rate 全 weak（ls_t<2）。
> 2. PB rate 几乎完全被 vol_20d 解释（r²=0.811）——"变化率 ≈ 波动率"共线性陷阱。
> 3. Rank 化救 mono 救不了 ls_t；等权聚合三成分全 weak 则聚合依旧 weak。
> 4. 跨方向并轨（F004/F300）：rate/delta/ratio 形式系统级 default-skip。

---

## Related

- 🟡 [[value_liquidity_interaction]] `saturated` — 已测 PE/PB rate × turnover 交互（全 reject）；本方向填"纯变化率"缺口，结论一致证伪
- 🟡 [[barra_residual_alpha]] `saturated` — ep_ratio 为 Barra style 因子，本 hypothesis 天然受其约束
- 🔴 [[return_momentum_acceleration]] / [[asymmetric_momentum]] / [[return_distribution_signals]] / [[pv_covariance]] `dead` — 同属 F004/F300 rate-form 失败律共证方向
- 🟡 [[liquidity_acceleration]] `saturated` — turnover/amount/volume rate ratio 被 F001 吸收（同律不同机制）
- ✅ [[factors/F002|F002]] — 对照组：PB/amount **绝对水平**可用，证明 fundamental 信号本身可行，不可行的是"变化率"形式
- ✅ [[factors/F010|F010]] — 对照组：level 形式 ls_t=7.50 整库记录，rate vs level 对照决定性

---

## Narrative Log

> [!quote]+ 2026-04-21 · [[batches/batch_022/judge|batch_022]] · 方向关闭
> **admit=0 / reserve=0 / reject=4**
> - T001/T002/T003 全部 `[◉ ACTIVE] → [✗ DISPROVEN]`
> - 核心元教训：A 股 csi1000 fundamental ratio **变化率**不构成独立 alpha；F002 证明绝对 ratio 可用，变化率不行
> - MT budget：4 tests 全 reject，无 admit 占预算
> - Direction ops：`exploring → dead`（不可逆）；priority `medium → low`；不进入 retry pool

> [!quote]+ 2026-04-25 · Phase 5 consolidation · 并入跨方向失败律
> 收到 distillation findings F004（pattern_analyst, severity=high）+ F300（hypothesis_promoter, severity=high）：本方向作为「rate/delta/ratio 形式跨 5+ 方向结构性失效」核心证据之一被引用；hypothesis ⚠️ 段并入跨方向元教训，建议 lessons.md `Structural Constraints` 新增「rate/delta/ratio default-skip」条目。方向状态保持 dead，无新候选。
