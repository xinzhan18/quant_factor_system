---
direction_tag: microstructure_illiquidity
status: productive
priority: high
rounds: 1
admits: 1
last_batch: batch_030
last_admits:
- F012
last_goal: 测试 microstructure 层 illiquidity 维度——Amihud 20d/60d、HHI(amount/turnover)
  时序集中度、TsEntropy(amount)——是否能在 F001(amount CV) / F002(pb×amount) / vol_20d Barra
  basis 外提供独立 alpha。三个自定义 DSL 算子在 29 批历史从未使用。
last_activity: '2026-04-23T11:39:14Z'
created_batch: batch_030
members:
- F012
retired_members: []
merged_into: null
---
# microstructure_illiquidity

> [!abstract]+ 方向概要
> - **状态**　🔵 `exploring` · priority `high` · rounds = 0 · admits = 0
> - **最近**　[[batches/batch_030/judge|batch_030]] · 2026-04-23 · admit=1 / reserve=4 / reject=1
> - **一句话**　首批 admit Amihud illiquidity 20d（C001 → `amihud_illiq_20d`）；HHI 孪生双候选库空间冗余 reserve；Entropy 证伪。

---

## Hypothesis

> [!note]+ Hypothesis · 新开 · DSL-native
> 现有库已覆盖 **amount dispersion**（F001 amount_cv_10，测资金稳定性）与 **valuation × liquidity level**（F002 pb_amount_ratio_20，测估值×流动性水平），但 **microstructure illiquidity** —— Amihud (2002) 定义的"单位成交额引发的价格冲击" —— 从未探过。29 批历史中 `AmihudIlliq` / `HHI` / `TsEntropy` 三个 registered 自定义算子零使用，是 DSL 空间明确剩余的独立轴。
>
> **三条经济学线索**
> 1. **Illiquidity premium (Amihud 2002)**: `Mean(|return| / $amount, n)` 高的股票承担更高流动性风险 → 横截面上需要 return premium 补偿。与 vol_20d（magnitude）不同：Amihud 测的是 *price-impact per dollar*, 不是 *price range*。
> 2. **Trading concentration (HHI)**: `HHI($amount, n)` = Σ(p_i²) where p_i = amount_i / Σamount。测的是成交额**时序集中度** —— 高 HHI = 某几天巨量主导（信息事件驱动），低 HHI = 均匀成交。与 F001（Std/Mean 测波动幅度）**代数独立**：HHI 对单日极值敏感而 Std/Mean 对均值偏离平方根敏感。
> 3. **Concentration asymmetry**: `TsEntropy($amount, n)` 与 HHI 是数学孪生（一个测集中，一个测分散），但在尾部行为上差异显著。HHI 对 single-dominant-day 极度敏感，Entropy 对 uniform-vs-bimodal 更敏感。两者若同时有效说明该维度稳健；若 HHI 赢 Entropy 输说明"极端单日事件"驱动。
>
> **结构性约束**
> - **市值代理红线风险**：Amihud 1/amount 可能与 1/market_cap 高相关（illiquidity ≈ 1/size）—— 若触 `|corr($market_cap)| > 0.3` 红线则 reject。这是硬假设检验，不绕开。
> - **vol_20d 耦合风险**：|return| 出现在 Amihud 分子，天然与 vol_20d 相关。但分母 $amount 的 cross-section 归一化可能剥离部分。记录 `style_r²` 与 `alpha_survival`，以判别 Amihud 是否独立于现有 Barra basis。
> - 双窗口扫描（20d / 60d）测 horizon 稳定性；双字段分母（$amount / $turnover_rate）测 normalization 选择。

---

## Current Focus

首批 admit C001 (`amihud_illiq_20d`) 打破 29 批历史"DSL 层无空间"断言，证实 Amihud illiquidity 是 DSL-native 剩余轴。但 admit 条件严苛：max_corr=0.754@F002（CP05 high）靠 incremental_ic=0.034 硬救；CP04 borderline（turnover_20d + vol_20d 双吞噬）。下轮焦点：**residualize Amihud by turnover_20d / vol_20d** 做纯化变体，目标 alpha_survival 从 0.44 → >0.70；若仍被 Barra 主导则方向 edge = "纯路径" 局部最优 F002-family 而非真独立维度。

---

## Threads

### T001: Amihud 类 illiquidity 指标 [◉ ACTIVE]

> [!note]+ Thread 当前
> **Question**: Mean(|return|/$amount, n) 与 Mean(|return|/$turnover_rate, n) 是否能在横截面上提供独立于 F001(amount CV) / vol_20d(Barra) 的 illiquidity premium alpha？
>
> **Evidence trail**:
> - [[batches/batch_030/candidates/C001|batch_030 C001]]　Amihud 20d amount-denom → IC_OOS=0.034 ls_t=4.48 mono=1.0 incr_ic=0.034（6.7× 阈值）max_corr=0.754@F002 alpha_surv=0.443 → **admit → amihud_illiq_20d**
> - [[batches/batch_030/candidates/C002|batch_030 C002]]　Amihud 60d amount-denom → IC_OOS=0.027 ls_t=3.58 mono=1.0 incr_ic=0.025 max_corr=0.677@F002 alpha_surv=0.43 (CP04 poor) → **reserve**（同 thread anchor，不可与 C001 双 admit）
> - [[batches/batch_030/candidates/C006|batch_030 C006]]　Amihud 20d turnover-denom → IC_OOS=0.032 ls_t=1.84 mono=1.0/0.7 incr_ic=0.022 max_corr=0.111@F010 alpha_surv=0.216 (CP04 poor) → **reserve**（库空间最独立但 ls_t<2）
>
> **Partial Answer**: 20d horizon + $amount 分母 = T001 局部最优。30 批首触 microstructure DSL 原语，证实 illiquidity premium 作为独立 alpha 轴存在。horizon 扫描（20d vs 60d）与 分母扫描（$amount vs $turnover_rate）均落入较弱象限，说明"短窗 + dollar-scaled Amihud" 是当前 DSL 空间最强组合。
>
> **Next probes**: (1) `AmihudIlliq` 自定义算子直接调用（vs 手构 `Mean(Div(Abs(Div(Delta($close,1), Ref($close,1))), $amount), 20)`）看是否产出 bit-for-bit 相同结果（若不同则算子内部可能做了 normalize/winsorize，是新候选）; (2) residualize C001 by turnover_20d 或 vol_20d（DSL 层可尝试 `Div(Amihud, Std($close, 20))` 作价格-规模双归一）; (3) Amihud × F002 交互（illiquidity × 价值）。

### T002: 成交额时序集中度（HHI）[✓ ANSWERED batch_030]

> [!success]+ Thread 结论
> **Question**: HHI($amount, 20) 与 HHI($turnover_rate, 20) 测的"成交额时序集中度"是否独立于 F001(Std/Mean 测绝对波动)？即 high-concentration（一天独大）是否与 high-CV（长期波动高）经济意义不同？
>
> **Evidence trail**:
> - [[batches/batch_030/candidates/C003|batch_030 C003]]　HHI($amount, 20) → IC=-0.0385 ls_t=-4.02 mono=-1.0 alpha_surv=0.58 max_corr=0.594@F001 **signed incr_ic=-0.013** 9 年全负 → **reserve**（库稀释）
> - [[batches/batch_030/candidates/C004|batch_030 C004]]　HHI($turnover_rate, 20) → IC=-0.0352 ls_t=-4.08 mono=-1.0 alpha_surv=0.64 max_corr=0.597@F001 **signed incr_ic=-0.010** 9 年全负 → **reserve**（库稀释）
>
> **Answer**: **机制真实存在但库已吸收**。HHI 与 F001 相关 0.59-0.60 + signed incremental_ic 均为负——F001 (amount CV 10d) 已把"amount 变异信号"的主要载体占领，HHI 作为高阶矩孪生在当前库空间冗余。两候选互为 anchor，即使增量转正也只能择一 admit。
>
> **复活条件**：(1) F001 retire 后 HHI 可作为 amount-family 代表复活；(2) residualize HHI by F001 / vol_20d 的残差版若能产出 signed positive incr_ic 可重开 T002.

### T003: 集中度 vs 分散度的代数孪生对比 [✗ DISPROVEN batch_030]

> [!failure]+ Thread 结论
> **Question**: HHI($amount, 20)（Σp_i²）与 TsEntropy($amount, 20)（-Σp_i log p_i）是同一维度的互补度量，二者在横截面 IC 上差异如何？HHI 赢 = 单日极值驱动；Entropy 赢 = uniform-vs-bimodal 差异驱动；同时有效 = 维度稳健。
>
> **Evidence trail**:
> - [[batches/batch_030/candidates/C005|batch_030 C005]]　TsEntropy($amount, 20) → IC=+0.011 ls_t=**1.54**（weak，< 2 阈值）mono=0.7 alpha_surv=1.43 max_corr=0.343@F001（符号反向）**signed incr_ic=-0.0008**（近零）→ **reject**
> - （比较：C003 HHI amount 20d → IC=-0.0385 ls_t=**-4.02** mono=-1.0）
>
> **Answer**: **HHI 赢、Entropy 输。** ls_t 量级相差 2.6×（4.02 vs 1.54），方向相反——"amount 时序集中度" 的经济信号是**单日极端事件驱动**，不是**分布均匀度驱动**。TsEntropy 对"有几天高、几天低"的 uniform-vs-bimodal 分布差异敏感但对"一天独大"不敏感；而 amount 真正携带预测力的维度是后者。**Thread 结题**，后续 microstructure 探索不再追加 entropy 变体。
>
> **升格教训**：代数孪生（HHI vs Entropy）在真实市场数据上**经常不等价**——同一维度的不同矩统计量对不同尾部结构敏感，应同时测才能定位信号的真实数据结构。

---

## Known Failures

| Candidate | Expression | Reject Reason |
|---|---|---|
| [[batches/batch_030/candidates/C005\|C005]] | `TsEntropy($amount, 20)` | CP03 weak (ls_t=1.54 < 2) + signed incremental_ic=-0.001 近零（无库增值）+ mono=0.7 + IS ls_sharpe=0.06 跳 OOS 1.11 (OOS 碰巧) |

---

## Related

- 🟢 [[amount_volatility_signal]] `productive` — F001 所在方向；F001 吸收 20d 时序集中度维度是 T002 reserve 的核心原因
- 🟢 [[value_liquidity_interaction]] `productive` — F002 所在方向；C001 admit 后与 F002 max_corr=0.754，Amihud 与 pb/amount 共享 1/amount 结构
- 🟡 [[turnover_structural_signal]] `saturated` — turnover CV/AutoCorr 测过；HHI(turnover) 已在本方向补测 → reserve
- 🟡 [[barra_residual_alpha]] `saturated` — 全库 Barra 背景；C001 admit 的 CP04 borderline 证实 turnover_20d + vol_20d 双吞噬仍是方向主要 style 约束
- 🔵 [[liquidity_acceleration]] `exploring` — 同样 incremental_ic 为负 reserve 先例（batch_023 C001/C003）支持本批 C003/C004 reserve 决定
- [[lessons#Structural Constraints]] — 市值代理红线 / 向量化约束

---

## Narrative Log

> [!quote]+ 2026-04-23 · [[batches/batch_030/judge|batch_030]] · 方向首批打破 3 批零 admit 僵局
> admit=1 / reserve=4 / reject=1。
> - **T001 Amihud 家族（C001/C002/C006）**：首批 admit C001 (`amihud_illiq_20d`, 20d amount-denom, IC=0.034 ls_t=4.48 incr_ic=0.034 max_corr=0.754@F002)。C002 (60d) / C006 (turnover-denom) 作为 horizon × 字段对照 reserve，thread 保持 ACTIVE。
> - **T002 HHI 家族（C003/C004）**：两候选单体 strong（ls_t=±4.02/-4.08, mono=-1.0, 9 年全负）但 signed incremental_ic 均负（-0.013/-0.010）——F001 已吸收 amount 时序集中度维度。Thread ANSWERED。
> - **T003 HHI vs Entropy（C005）**：C005 TsEntropy ls_t=1.54 weak + mono=0.7，vs C003 HHI ls_t=-4.02 mono=-1.0——**单日极值驱动假设胜**，Entropy 变体 disproven。Thread DISPROVEN。
> - **系统级发现**：29 批 "DSL 层无空间" 断言被部分证伪——`AmihudIlliq` / `HHI` / `TsEntropy` 三原语真有 DSL-native 差异信号，但 admit 门槛严苛（必须高 incremental_ic 硬救）。
> - **MT budget**　cumulative 140 → **146** · direction 0 → **6** · bucket `medium`（search_adjusted 0.9→0.66 仍 medium）
>
> **Operations**　`status: exploring → productive (Phase 4 Python auto-flip on first admit)` · priority `high` 保留
