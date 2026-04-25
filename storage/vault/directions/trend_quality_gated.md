---
direction_tag: trend_quality_gated
status: dead
priority: low
rounds: 1
admits: 0
last_batch: batch_037
last_admits: []
last_goal: 'T001/T002/T003 baseline: probe whether momentum gated by abnormal amount
  (T001 linear/log), low return-vol (T002 Sharpe-like), or joint (T003 composite)
  survives csi1000 small-cap 2023 regime where raw momentum was disproven in return_momentum_acceleration/asymmetric_momentum
  dead directions. Paper Channel 3 CleanTrend/OrderlyTrend signals, applied via log-compression
  meta-pattern from F013.'
last_activity: '2026-04-23T18:33:46Z'
created_batch: null
members: []
merged_into: null
---
# trend_quality_gated

> [!abstract]+ 方向概要
> - **状态**　🔴 `dead` · priority `low` · rounds = 1 · admits = 0
> - **最近**　[[batches/batch_037/judge|batch_037]] · 2026-04-24 · 0/1/5（首批即 hypothesis 反向证伪）
> - **一句话**　paper Channel 3 CSI 300 大盘 trend-continuation 信号在 csi1000 **符号完全翻转为 reversal**；gate 不能救回 momentum

---

## Hypothesis

> [!warning] ⚠️ Hypothesis 完全证伪（batch_037）
> **原假设**：被 gate 过的 momentum (流动性 / 低残差噪声 / composite) 在 csi1000 复活成 trend continuation。
>
> **证伪**：6/6 候选 IC_OOS 在 -0.025 至 -0.033 区间，mono 全负，**signal 实质是 reversal 不是 trend**。Gate 不改方向，反而把 reversal 信号叠厚。
>
> **元教训**：(1) csi1000 5-10d momentum 是反转载体，gate 形态不能翻成 continuation；(2) `Std(daily_return, 20)` 作分母 = Barra vol_20d 设计共线，alpha 无法 orthogonalize；(3) paper Channel 3 CSI 300 大盘结果不可迁移到 csi1000 小盘，与 Channel 1 gap_acceptance 同样 8x+ 量级衰减且这里直接翻号。

Paper QuantaAlpha §5 Alpha Decay 观察：2023 年 A 股从大盘切到小盘，**raw momentum 全部 alpha_decay**（Alpha158/360 + AlphaAgent 的动量类因子都死），但 QuantaAlpha 发现的 `CleanTrend_Continuation_Score_RS10_WVMA5` (Rank IC 0.0590) 与 `OrderlyTrend_x_Absorption_10D_5D_20D` (Rank IC 0.0465) 依然存活。**共同结构**：短/中 horizon momentum × 低 residual volatility × 高流动性吸收（高 $amount / 低价格冲击）。

A 股本地化（csi1000 小盘）：
- 我们已有 `return_momentum_acceleration` / `asymmetric_momentum` 两条 dead 方向——证明**无条件 momentum** 在小盘上不存活
- 但这两条方向**都没有做质量 gate**（残差波动率、流动性吸收条件）
- 假设：**被 gate 过的 momentum** 在 csi1000 上可能复活——gate 剔除掉"小盘噪声驱动的反转型伪趋势"，只留下"机构持续买入/卖出的有序趋势"
- 参考 batch_036 log-compression meta-pattern：非线性门控（log / EMA / sigmoid-like 形状）在 csi1000 比线性门控更稳

与现有方向的关键区别：
- `return_momentum_acceleration` (dead)：单层 momentum 导数，无 gate
- `asymmetric_momentum` (dead)：上涨/下跌不对称，无 gate
- `intraday_price_formation` (saturated)：日内价格形状，不涉 momentum gate
- `liquidity_acceleration` (saturated)：流动性自身变化，不与 momentum 结合
- **本方向**：momentum **作为信号** + 流动性/残差波动率 **作为 gate** 的联合结构

> [!danger] 🛑 升格教训（来自 distillation findings F004 / F006 / F302）
> 本方向已被三条独立 finding 标注为 "升格元教训" 来源，未来同类 paper-driven gate hypothesis 起手前必读：
>
> - **F004** rate/delta/ratio + Meta-pattern 机械迁移风险：log-compression 在 sign×body (F013) 工作 ≠ 在 momentum gate 工作（本方向 6/6 IC_OOS 负）≠ 在 value × liquidity 工作（log_value_liquidity 6/6 负）。**结构相同 ≠ 语义相同**——csi1000 小盘反转簇会把所有"量×方向复合"形态吸收为同一载体。
> - **F006** Paper CSI 300 → csi1000 transfer 普遍失败 + sign aggregation drift 依赖：本方向是该律的第二次独立验证（首次为 gap_acceptance 8x 衰减）；csi1000 小盘 momentum/continuation 是反转载体，gate 形式不能翻号。
> - **F302** Paper transfer default 律：复刻 paper alpha 必须先在 csi1000 重测原始 raw signal 是否同号；翻号或单调性破坏 → 方向直接 dead，不要再用 gate / 加权抢救。建议本方向 `dead → archived`。

---

## Current Focus

- 方向已 dead，无 active focus
- 元教训已通过 F004 / F006 / F302 三条 finding 流向 lessons.md（待下次 consolidation 升格 `## Paper Transferability` 子段）
- future "paper Channel 4/5" 类 intake 起手前必读 F006 + F302

---

## Threads

### T001: Trend × 流动性吸收 gate [✗ DISPROVEN batch_037]

> [!failure]+ Thread 结论
> **Question**: 10d momentum × abnormal $amount（吸收 gate）是否携带独立于 F001/F002/F013 的 alpha？
>
> **Answer**: 否。线性 amount (C001) / log amount (C002) / turnover (C006) 加权全部 IC_OOS 反向（-0.033 至 -0.033），mono 全负，与 F009 反转簇 corr 0.30-0.44。流动性 gate 不能翻 momentum 符号，反而强化 reversal。
>
> **Evidence trail**:
> - [[batches/batch_037/candidates/C001|batch_037 C001]]　linear amount gate, IC_OOS=-0.033 mono=-0.4 incr=-0.020 → **reject**
> - [[batches/batch_037/candidates/C002|batch_037 C002]]　log amount gate, IC_OOS=-0.033 mono=-0.7 9 年同号 → **reserve**（统计强但方向反向，等 sister direction）
> - [[batches/batch_037/candidates/C006|batch_037 C006]]　turnover gate, IC_OOS=-0.033 → **reject**

### T002: Trend × 低残差噪声 gate [✗ DISPROVEN batch_037]

> [!failure]+ Thread 结论
> **Question**: 10d momentum × 1/Std(daily_return, 20)（低噪声 gate）是否比纯 momentum 存活？
>
> **Answer**: 否。Std(daily_return, 20) 作分母 = Barra vol_20d 设计共线，style_r²=0.35-0.52，alpha 已被 Barra basis 吸收。signal 仍反向。
>
> **Evidence trail**:
> - [[batches/batch_037/candidates/C003|batch_037 C003]]　10d/20d Sharpe-like, IC_OOS=-0.027 style_r²=0.519 → **reject**
> - [[batches/batch_037/candidates/C005|batch_037 C005]]　5d/20d Sharpe-like, IC_OOS=-0.026 → **reject**

### T003: Composite Trend × (Liquidity × Residual Noise) [✗ DISPROVEN batch_037]

> [!failure]+ Thread 结论
> **Question**: 同时 gate 两个维度是否比单 gate 更强？
>
> **Answer**: 否。叠 gate 不解决方向问题。C004 IC_OOS=-0.025，alpha_surv=0.44 勉强过，仍反向。
>
> **Evidence trail**:
> - [[batches/batch_037/candidates/C004|batch_037 C004]]　composite gate, IC_OOS=-0.025 → **reject**

---

## Known Failures

| Candidate | Expression | Reject Reason |
|---|---|---|
| [[batches/batch_037/candidates/C001\|C001]] | `Mean(Mul(10d_ret, $amount/Mean($amount,20)), 5)` | misaligned + library reducer (incr=-0.020) |
| [[batches/batch_037/candidates/C003\|C003]] | `Mean((10d_ret) / Std(daily_ret, 20), 5)` | misaligned + Barra vol_20d 设计共线 (style_r²=0.519) |
| [[batches/batch_037/candidates/C004\|C004]] | composite trend × log-amount / vol | misaligned + composite 不解决方向问题 |
| [[batches/batch_037/candidates/C005\|C005]] | 5d momentum / 20d daily_ret std | misaligned + ls_t<2 weak |
| [[batches/batch_037/candidates/C006\|C006]] | `Mean(Mul(10d_ret, $turnover/Mean($turnover,20)), 5)` | misaligned + library reducer (incr=-0.020) |

---

## Related

- 🔴 [[return_momentum_acceleration]] `dead` — 无 gate 动量在 csi1000 失效，本方向通过 gate 试图绕开（同被 F004 援引）
- 🔴 [[asymmetric_momentum]] `dead` — 方向性动量拆分失效，本方向不做方向拆分（同被 F004 援引）
- 🔴 [[log_value_liquidity]] `dead` — F013 log-compression meta-pattern 同样机械迁移失败（F004 三方向并列证据）
- 🔴 [[pv_covariance]] `dead` — 第三个 meta-pattern 迁移失败方向（F004 三方向并列证据）
- 🟡 [[gap_acceptance_structure]] `productive` — F006 援引：paper CSI 300 → csi1000 transfer 律的第一次独立验证（8x 衰减）；本方向是第二次（翻号）
- 🟡 [[intraday_price_formation]] `saturated` — 日内价格形状，与本方向的跨日 trend 正交
- 🟡 [[liquidity_acceleration]] `saturated` — 流动性自身变化，本方向用作 gate
- 📖 [[papers/arxiv_2602_07085v2]] — paper intake 种子（Channel 3: CleanTrend_Continuation + OrderlyTrend_x_Absorption）
- 📖 [[lessons#Structural Constraints]]（F004 / F006 / F302 升格目标段落，待下次 consolidation）

---

## Narrative Log

> [!quote]+ 2026-04-24 · [[batches/batch_037/judge|batch_037]]
> **首批即 hypothesis 反向证伪 → status: exploring → dead** · admit=0 / reserve=1 (C002) / reject=5
>
> - 6/6 候选 IC_OOS 全负（-0.025 至 -0.033），mono 全负，9 年 IC 全负——signal 是 reversal 不是 trend
> - 与 dead 方向 return_momentum_acceleration / asymmetric_momentum 已证伪结论一致
> - C002 log gate 统计稳健但方向反向，reserve 等待 sister direction `gated_reversal` 是否值得开
> - MT budget cumulative 180 → **186** · direction 0 → **6** · bucket `medium`
>
> **Operations**　`status: exploring → dead` · `priority: medium → low` · 元教训进 lessons.md（下次 consolidation）

> [!quote]- 2026-04-24 · paper intake extension
> **方向由 QuantaAlpha paper Channel 3（CleanTrend / OrderlyTrend）推断得出** · rounds = 0 / admits = 0
>
> - 核心洞察：无条件 momentum 在 csi1000 已证伪（return_momentum_acceleration / asymmetric_momentum 两条 dead 方向），但 paper Channel 3 证明**被 gate 过的 momentum** 在 2023 regime 下存活
> - 假设：gate 剔除小盘"噪声驱动反转型伪趋势"，只留"机构持续买卖的有序趋势"
> - 首批目标：T001（流动性 gate）+ T002（低残差噪声 gate）对照，T003 composite baseline
>
> **Operations**　新建 `status: exploring` · `priority: medium`（paper Channel 3 是 secondary evidence，主 gap_acceptance 已 harvested；本方向是 hedge bet）
