---
direction_tag: log_value_liquidity
status: dead
priority: low
rounds: 1
admits: 0
last_batch: batch_038
last_admits: []
last_goal: 'T001+T002 baseline: probe log-compressed value × liquidity composites
  — pb/ps/pe rank multiplied by log(abnormal amount/turnover/volume). Direct application
  of batch_036 F013 meta-pattern to value_liquidity_interaction''s previously-disproven
  linear DSL space. F002 corr is the gating audit; max_corr<0.7 to admit, 0.7-0.85
  reserve, ≥0.85 reject as near_dup.'
last_activity: '2026-04-23T19:00:41Z'
created_batch: null
members: []
merged_into: null
---
# log_value_liquidity

> [!abstract]+ 方向概要
> - **状态**　🔴 `dead` · priority `low` · rounds = 1 · admits = 0
> - **最近**　[[batches/batch_038/judge|batch_038]] · 2026-04-24 · 0/0/6（首批即 hypothesis 反向证伪）
> - **一句话**　Meta-pattern 跨方向迁移失败：log-compression 在 value × liquidity 维度变成 overnight-intraday 反转簇载体，6/6 reject

> [!warning] ⚠️ Hypothesis 完全证伪（batch_038, 1 批 6/6）
> 原假设：log-compression 元教训从 [[gap_acceptance_structure]] (F013) 迁移到 value × liquidity 解锁新 alpha。
> 实测：6/6 候选 IC_OOS 全负 (-0.023 ~ -0.034)，mono ≈ 0 或负，incr_ic 全负 (-0.016 ~ -0.029)，max_corr@F009 0.22-0.26 → 真实承载体是 overnight-intraday 反转簇的 value-weighted 包装，而非 value × liquidity。
> **元教训 (升格自 F303)**：(1) Meta-pattern 跨方向迁移**不能机械复用**——log 在 sign × body 工作是因 sign 已是规整二值（噪声集中在 magnitude 尾部），log 救不了 value × liquidity 是因 value 通道在 csi1000 小盘已独立失效；(2) csi1000 PB/PS/PE rank 不载独立 value alpha，与 [[value_liquidity_interaction]] T001/T003 同结论；(3) 设计 hedge bet（"复用上批成功 trick"）必须先独立验证底层信号 alive，否则 meta-pattern 任何包装都救不回。
> **关联系统级反模式 (F004)**：本方向与 [[trend_quality_gated]] (b037) + [[pv_covariance]] (b039) 共同构成 "meta-pattern 机械迁移连续 3 批全败" 证据链——跨方向结构相同 ≠ 跨方向语义相同。

---

## Hypothesis

`value_liquidity_interaction` 的 T001 已证伪线性 value × liquidity 在 csi1000 的两条 DSL 路径（乘法 / 除法），仅 F002 `Div($pb_ratio, Mean($amount, 20))` 一条线性除法存活。**Batch_036 决定性证据**：log-compression 在 `gap_acceptance_structure` 把 mono_OOS 从 0.30 翻倍到 0.60，证明非线性压缩在 csi1000 小盘可抑制噪声放大。

应用到 value × liquidity：
- **F002 (linear pb/amount-mean ratio) → log-compressed 变体**：`Mul(CsRank($pb_ratio), Log(Div($amount, Mean($amount, 20))))` 等。预期：log 压缩 abnormal liquidity 尾部，与 F002 不构成 near_duplicate（不同函数形式）但承袭 value × liquidity 信号本质。
- **横扩到 ps/pe**：log-compressed value × liquidity 不限于 PB——`ps × log(abnormal turnover)`、`pe × log(abnormal amount)` 是同结构变体。

与现有方向区别：
- `value_liquidity_interaction` (saturated)：所有候选都是线性 Mul/Div/CsRank diff 形态，没有 log 形态
- `gap_acceptance_structure` (saturated)：log 形态只用在 sign×sign 上，没碰 value
- 本方向：value × log(abnormal liquidity) 联合形态，**直接复用 batch_036 元教训**

> Hypothesis 保留（仅 1 批证伪，未达 ≥3 批阈值）但已被 batch_038 正面反驳；结论与教训详见上方 ⚠️ callout。

---

## Threads

### T001: PB × log abnormal liquidity [✗ DISPROVEN batch_038]

> [!failure]+ Thread 结论
> **Question**: pb_ratio × log(abnormal $amount or $turnover_rate) 是否产生独立于 F002 的 alpha？
>
> **Answer**: 否。4 个 pb 变体 (C001/C002/C005/C006) 全部 IC_OOS 负，与 F009 反转簇 -0.22 ~ -0.26 共振，库 reducer。
>
> **Evidence trail**:
> - [[batches/batch_038/candidates/C001|C001]] pb × log(amt/mean) IC_OOS=-0.029, incr=-0.029 → reject
> - [[batches/batch_038/candidates/C002|C002]] pb × log(turnover/mean) IC_OOS=-0.028 → reject
> - [[batches/batch_038/candidates/C005|C005]] pb × log(vol/mean) IC_OOS=-0.028 → reject
> - [[batches/batch_038/candidates/C006|C006]] pb × log(amt/mean) + 5d smooth IC_OOS=-0.023 → reject

### T002: PS / PE × log abnormal liquidity [✗ DISPROVEN batch_038]

> [!failure]+ Thread 结论
> **Question**: 横扩到 ps/pe 维度，log-compressed value × liquidity 是否成立？
>
> **Answer**: 否。ps × log(amt) (C003) 与 pe × log(turnover) (C004) 同病，IC_OOS=-0.032 / -0.034，机制承载与 pb 变体一致。
>
> **Evidence trail**:
> - [[batches/batch_038/candidates/C003|C003]] ps × log(amt/mean) IC_OOS=-0.032 → reject
> - [[batches/batch_038/candidates/C004|C004]] pe × log(turnover/mean) IC_OOS=-0.034 → reject

---

## Known Failures

| Candidate | Expression | Reject Reason |
|---|---|---|
| [[batches/batch_038/candidates/C001\|C001]] | `Mul(CsRank($pb_ratio), Log(Div($amount, Mean($amount, 20))))` | misaligned + library reducer (incr=-0.029) |
| [[batches/batch_038/candidates/C002\|C002]] | `Mul(CsRank($pb_ratio), Log(Div($turnover_rate, Mean($turnover_rate, 20))))` | misaligned + reducer (incr=-0.027) |
| [[batches/batch_038/candidates/C003\|C003]] | `Mul(CsRank($ps_ratio), Log(Div($amount, Mean($amount, 20))))` | misaligned + reducer (incr=-0.029) |
| [[batches/batch_038/candidates/C004\|C004]] | `Mul(CsRank($pe_ratio), Log(Div($turnover_rate, Mean($turnover_rate, 20))))` | misaligned + reducer (incr=-0.028) |
| [[batches/batch_038/candidates/C005\|C005]] | `Mul(CsRank($pb_ratio), Log(Div($volume, Mean($volume, 20))))` | misaligned + reducer (incr=-0.028) |
| [[batches/batch_038/candidates/C006\|C006]] | `Mean(C001, 5)` smoothed | misaligned + reducer (incr=-0.016) |

---

## Related

- 🟡 [[value_liquidity_interaction]] `saturated` — F002 线性除法是 value × liquidity 唯一存活；本方向探 log 非线性失败 → 第 2 个 admit 通道关闭
- 🟡 [[gap_acceptance_structure]] `saturated` — F013 log-compression meta-pattern 提供方；同款变换在本方向反向证伪
- 🔴 [[trend_quality_gated]] `dead` — meta-pattern 机械迁移连续失败案例（b037, paper → csi1000 + gated）
- 🔴 [[pv_covariance]] `dead` — meta-pattern 机械迁移连续失败案例（b039, Cov 形态归 F001/F009/F012 反转簇）
- 🟡 [[amount_volatility_signal]] `saturated` — F001 amount_cv_10；本方向避免与 amount-vol 组合直接重叠
- 📖 [[lessons#Meta-pattern Transfer]] · [[lessons#Structural Constraints]]

---

## Narrative Log

> [!quote]+ 2026-04-24 · [[batches/batch_038/judge|batch_038]]
> **首批即 hypothesis 反向证伪 → status: exploring → dead** · admit=0 / reserve=0 / reject=6
>
> - 6/6 IC_OOS 全负 (-0.023 ~ -0.034)，mono ≈ 0 或负，incr_ic 全负 → 库 reducer
> - 真实承载体：overnight-intraday 反转簇（max_corr@F009 0.22-0.26）的 value-weighted 包装
> - 元教训：meta-pattern 跨方向迁移**不能机械复用**——log-compression 在 sign × body 工作 ≠ 在 value × liquidity 工作
> - csi1000 PB/PS/PE rank 不载独立 value alpha（与 value_liquidity_interaction T001/T003 同结论）
> - MT budget cumulative 186 → **192** · direction 0 → **6** · bucket `medium`
>
> **Operations**　`status: exploring → dead` · `priority: medium → low` · 元教训 (F303) 进 lessons.md「Meta-pattern Transfer」新段

> [!quote]- 2026-04-24 · meta-pattern transfer (origin)
> **方向由 batch_036 F013 admit + log-compression meta-pattern 推断得出** · rounds = 0
>
> - 核心洞察：log-compression 修好了 csi1000 sign × body acceptance 的 mono barbell 问题（0.30 → 0.60）
> - 假设迁移：同样的非线性压缩应用到 value × liquidity 可能解锁 F002 之外的新 admit
> - 首批目标：T001 pb 类 log 变体 + T002 ps/pe 横扩
>
> **Operations**　新建 `status: exploring` · `priority: medium`（meta-pattern 二度试验，hedge bet）
