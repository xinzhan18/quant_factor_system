---
direction_tag: microstructure_illiquidity
status: productive
priority: medium
rounds: 4
admits: 3
last_batch: batch_046
last_admits:
- F015
last_goal: '方向 saturated 后复活条件 (b) rank-diff symmetric interactions 探索 + sign-conditional
  Amihud 变体。绕开 batch_030/031 DSL residualize/horizon/Div cross-field 全败空间： (1) up-day
  vs down-day sign-conditional Amihud — 用 If gate 替代 Abs， 测 illiquidity 是否携带 signed
  directional information (batch_030 系列只测 symmetric magnitude)。 (2) Rank-diff symmetric
  interaction: CsRank(Amihud) - CsRank(F001_CV 里的 Std/Mean) 替代已败的 Div 结构（batch_031
  T004 disproven），scale-free 且几何上 真正对称。 (3) SignedPower(Amihud, 0.5) tail-compressed
  non-linear monotonic 变体，作为 rank-preserving 空对照延续（批 031 CsZscore 保序证据）。 (4) 探索新的
  Kyle-lambda 风格 signed illiquidity proxy (Δturnover / turnover²) — 非 |return| magnitude
  的替代信号源。 目标 ≥ 1 candidate 同时满足 max_corr@F012 < 0.50 + alpha_survival > 0.4。'
last_activity: '2026-04-24T19:22:38Z'
created_batch: batch_030
members:
- F012
- F015
retired_members: []
merged_into: null
---
# microstructure_illiquidity

> [!abstract]+ 方向概要
> - **状态**　🟢 `productive` · priority `medium` · rounds = 3 · admits = 2
> - **最近**　[[batches/batch_046/judge|batch_046]] · 2026-04-25 · admit=1 (C003) / reserve=1 (C006) / reject=4
> - **一句话**　方向 saturated 后被 batch_046 rank-diff symmetric interactions 复活：F013-to-be (Amihud rank − amount CV rank) 在 DSL 空间开辟 F012 之外的独立 alpha 子空间，兑现 direction 复活条件 (b)。

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

<!-- Current Focus: batch_046 后 direction 从 saturated 复活为 productive -->

> [!success]+ 复活说明（batch_046 后追加，2026-04-25）
> batch_046 C003 `Sub(CsRank(Amihud_20d), CsRank(amount_CV_10d))` admit 后方向从 `saturated → productive`。**复活条件 (b) rank-diff symmetric interactions 被证实有效**——这是在宣告 saturated 后 2 批即找到的有效子空间，说明 saturated 定性是对**当时探索范式的局部最优陈述**，不是永久结论。
>
> **兑现机制**: rank-diff 结构在 F012 空间之外开辟新维度，max_corr=0.655 接近 0.70 阈但 incremental_ic=0.031 证明库增值，alpha_surv=0.658 比 F012 高 48%。两端 scale-invariance 是必要条件（C004 Std 变体破坏范式）。
>
> **尚未兑现的复活条件**: (a) Python Barra residualized F012 → 归 [[directions/barra_residual_alpha]]；(c) minute-bar / tick-level 数据暂无；(d) F012 健在不需其家族复活。
>
> **下一轮方向**: T006 ANSWERED 后可开 T007 "rank-diff 扩展到其他 signal family"（vs F002 pb_ratio / F003 overnight gap / F007 open_position 等），测试范式在不同 signal 对上的泛化。

---

## Threads

### T006: rank-diff symmetric interactions [✓ ANSWERED batch_046]

> [!success]+ Thread 结论
> **Question**: 跨 signal family 的 CsRank 差结构（绕开 batch_031 T004 Div residualization disproven）是否能在 F012 之外开辟独立 alpha 子空间？
>
> **Answer**: 是。C003 `Sub(CsRank(Amihud_20d), CsRank(amount_CV_10d))` admit — IC_oos=0.054 mono_oos=1.0 ls_t=6.63 alpha_surv=0.658 incr_ic=0.031 max_corr=0.655@F012（strictly < 0.70 硬闸）9/9 年全正。**rank-diff 结构的 scale-free 属性让其真正脱离 F012 主子空间**，同时保留 F012 的 illiquidity 机制 + F001 的 amount dispersion 机制作为正交 rank reference。
>
> **Evidence trail**:
> - [[batches/batch_046/candidates/C003|batch_046 C003]]　`Sub(CsRank(Amihud_20d), CsRank(amount_CV_10d))` → **admit → F{id}@Phase4 amihud_cv_rank_diff_20**
> - [[batches/batch_046/candidates/C004|batch_046 C004]]　`Sub(CsRank(Std_amount), CsRank(Amihud_20d))` → max_corr=0.935 hard_gate reject（Std scale-dep 破坏 rank-diff 范式）
>
> **升格教训**: **rank-diff 符合率 range**：两端 signal family 都 scale-invariant（CV / ratio / correlation）时 rank-diff 结构 alpha 才独立；若一端 scale-dependent（Std / Mean / 绝对 level），rank-diff 退化为主因子近重复。C003/C004 对照是首个硬证据。推广到其他方向: 设计 CsRank 差结构时两端必须都 scale-free。

### T005: sign-conditional / signed Amihud 变体 [◉ ACTIVE]

> [!failure]+ Thread 结论
> **Question**: (1) up-day vs down-day Amihud 是否有 sign asymmetry？(2) signed illiquidity proxy（Kyle-lambda 风格 Δturnover/turnover²）是否独立于 Abs(Amihud) 磁性空间？
>
> **Answer**:
> - (1) 日频 20d 窗口下 **sign asymmetry 不存在**：C001 (up-day) max_corr=0.942, C002 (down-day) max_corr=0.918，对偶差仅 0.024（噪声级）。day-level sign gate + 20d mean aggregation 的组合在 csi1000 上抹平 asymmetry。
> - (2) C006 Kyle-lambda signed turnover illiq: max_corr=0.16 库独立，9 年全负 sign_consistency=1.0 — **信号真实独立**，但 CP03 weak (ls_t=-1.84) + CP04 poor (alpha_surv=0.17) + signed incr_ic=-0.031 稀释库 → reserve 负参考。
>
> **Evidence trail**:
> - [[batches/batch_046/candidates/C001|batch_046 C001]]　up-day Amihud → max_corr=0.942@F012 → reject (hard_gate)
> - [[batches/batch_046/candidates/C002|batch_046 C002]]　down-day Amihud → max_corr=0.918@F012 → reject (hard_gate)
> - [[batches/batch_046/candidates/C005|batch_046 C005]]　SignedPower(F012, 0.5) → max_corr=**1.000** → reject (rank-preserving 保序二证)
> - [[batches/batch_046/candidates/C006|batch_046 C006]]　Mean(Δturnover/turnover², 20) → ic_oos=-0.042 ls_t=-1.84 alpha_surv=0.17 max_corr=0.16 signed_incr_ic=-0.031 → reserve
>
> **升格教训**:
> 1. **day-level sign gate + window mean aggregation 抹平 asymmetry** —— 复活条件: ≤ 5d 短窗（减少对称化）或 quantile-based asymmetry 测度（非 mean aggregation）
> 2. **DSL rank-preserving 变换族 ({Linear / SignedPower(p>0) / Sigmoid / Tanh / Exp / Softmax}) 对单已 admit 因子零信息增量** —— 建议 generator 层 hard-gate 预拦截（batch_031 C004 CsZscore + batch_046 C005 SignedPower 双证）
> 3. **Kyle-lambda signed illiquidity 方向库独立但 alpha 弱** —— 探索需走 CV 归一 / Barra residualize / 更强机制重构

### T001: Amihud 类 illiquidity 指标 [✓ ANSWERED batch_031]

> [!success]+ Thread 结论
> **Question**: Mean(|return|/$amount, n) 与 Mean(|return|/$turnover_rate, n) 是否能在横截面上提供独立于 F001(amount CV) / vol_20d(Barra) 的 illiquidity premium alpha？
>
> **Answer**: 是，且 F012 (Amihud 20d amount-denom) 是 DSL 空间局部+全局最优。horizon 扫描（10d/20d/60d/5d-return）与分母扫描（$amount/$turnover_rate）全部落入 near_duplicate 或 ls_t weak 象限——**F012 是 T001 DSL 空间的几何不变量**。
>
> **Evidence trail**:
> - [[batches/batch_030/candidates/C001|batch_030 C001]]　Amihud 20d amount-denom → IC_OOS=0.034 ls_t=4.48 mono=1.0 incr_ic=0.034 max_corr=0.754@F002 alpha_surv=0.443 → **admit → [[factors/F012|F012]] amihud_illiq_20d**
> - [[batches/batch_030/candidates/C002|batch_030 C002]]　Amihud 60d amount-denom → IC_OOS=0.027 ls_t=3.58 mono=1.0 incr_ic=0.025 max_corr=0.677@F002 alpha_surv=0.43 (CP04 poor) → **reserve**
> - [[batches/batch_030/candidates/C006|batch_030 C006]]　Amihud 20d turnover-denom → IC_OOS=0.032 ls_t=1.84 mono=1.0/0.7 incr_ic=0.022 max_corr=0.111@F010 alpha_surv=0.216 (CP04 poor) → **reserve**（库空间最独立但 ls_t<2）
> - [[batches/batch_031/candidates/C001|batch_031 C001]]　Amihud 10d amount-denom → max_corr=0.957@F012 → **reject (hard_gate near_dup)**
> - [[batches/batch_031/candidates/C005|batch_031 C005]]　Amihud 5d-return 20d → max_corr=0.959@F012 → **reject (hard_gate near_dup)**
>
> **升格教训**：Amihud 家族 horizon（分子 return 步长 / 聚合窗口）扫描不打开独立轴；20d amount-denom 是 A 股 csi1000 日频 DSL 空间的 microstructure illiquidity 局部最优。后续探索必须走 Python Barra residual 或非线性合成。

### T004: Amihud residualization + cross-field 交互 [✗ DISPROVEN batch_031]

> [!failure]+ Thread 结论
> **Question**: (1) Amihud 除以 realized_vol / mean_turnover / cross-section z-score 是否能把 CP04 style_r² 从 0.47 降到 <0.25？(2) PB / Amihud（价值/流动性非对称 Div，避开 Mul 量纲陷阱）是否能打开 illiquidity × value 第三维？
>
> **Answer**: 全否。DSL 层 residualization 不是真 orthogonalization：CsZscore 保序零贡献、vol-residualize 放大 vol_20d 暴露、turnover-residualize 搬家（style_r² 改善但 alpha_survival 塌 69%）；Div-based cross-field 与 Mul 同样撞量纲陷阱。
>
> **Evidence trail**:
> - [[batches/batch_031/candidates/C002|batch_031 C002]]　Div(Amihud, Std(ret,20)) → max_corr=0.919@F012 vol_20d exposure 5.9→32.6 → **reject (hard_gate)**
> - [[batches/batch_031/candidates/C003|batch_031 C003]]　Div(Amihud, Mean(turnover,20)) → ic_oos=0.0598 ls_t=5.12 alpha_surv=**0.137**（塌 69%）max_corr=0.707@F012 incr_ic=0.042 → **reserve**（唯一略出 near_dup 线但 CP04 塌陷）
> - [[batches/batch_031/candidates/C004|batch_031 C004]]　CsZscore(Amihud) → max_corr=**1.000**@F012 → **reject (hard_gate)**（rank-preserving 变换保序）
> - [[batches/batch_031/candidates/C006|batch_031 C006]]　Div($pb_ratio, Amihud) → ic_oos=-0.050 ls_t=-4.76 alpha_surv=**0.025** max_corr=0.788@F012 **incr_ic=-0.044** → **reject**（CP05 high + signed negative incr_ic）
>
> **升格教训**：
> 1. **Rank-preserving 变换（CsZscore/Scale/Sigmoid/Tanh/Softmax）在 cross-section 空间对 IC 零贡献** —— 下轮任何 direction 首轮应 skip 这类候选
> 2. **DSL 层 `Div(factor, proxy)` residualization 不是真 orthogonalization** —— 要么保序、要么只是 style exposure 搬家；真 residualize 必走 Python OLS
> 3. **Div-based cross-field 与 Mul 同样撞量纲吞噬** —— illiquidity × value 交互需走 rank-diff symmetric 结构或 Python ensemble

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
| [[batches/batch_030/candidates/C005\|batch_030 C005]] | `TsEntropy($amount, 20)` | CP03 weak (ls_t=1.54 < 2) + signed incremental_ic=-0.001 近零（无库增值）+ mono=0.7 |
| [[batches/batch_031/candidates/C001\|batch_031 C001]] | 10d Amihud | hard_gate near_dup 0.957@F012（horizon 保序）|
| [[batches/batch_031/candidates/C002\|batch_031 C002]] | `Div(Amihud, Std(ret,20))` | hard_gate near_dup 0.919@F012；vol-residualize 放大 vol_20d exposure 5.9→32.6 |
| [[batches/batch_031/candidates/C004\|batch_031 C004]] | `CsZscore(Amihud)` | hard_gate near_dup **1.000**@F012（rank-preserving 保序空对照）|
| [[batches/batch_031/candidates/C005\|batch_031 C005]] | 5d-return Amihud | hard_gate near_dup 0.959@F012（分子 horizon 代数等价）|
| [[batches/batch_031/candidates/C006\|batch_031 C006]] | `Div($pb_ratio, Amihud)` | CP05 high + signed incr_ic=-0.044；Div 让 F012 主导，PB 被自身 style 吞噬 |

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

> [!quote]+ 2026-04-25 · [[batches/batch_046/judge|batch_046]] · T006 ANSWERED · T005 PARTIAL-DISPROVEN · 方向从 saturated 复活为 productive
> admit=1 (C003) / reserve=1 (C006) / reject=4。
> - **C003 rank-diff breakthrough**: `Sub(CsRank(Amihud_20d), CsRank(amount_CV_10d))` 兑现 saturated 复活条件 (b) rank-diff symmetric interactions — IC_oos=0.054 mono_oos=1.0 ls_t=6.63 alpha_surv=0.658（比 F012 的 0.443 高 48%）incr_ic=0.031 max_corr=0.655@F012（< 0.70 阈）9/9 年全正 cum_ic_mdd=-1.61 批内最强。
> - **C001/C002 sign-conditional 对偶结题**: up-day vs down-day Amihud max_corr 0.942/0.918 near_dup F012 → 日度 20d 窗口下 sign asymmetry 近乎完美被窗口均值抹平，散户恐慌抛售假说在此时间尺度不成立。
> - **C004 rank-diff 设计范式硬证据**: 同 C003 结构但分母端 Std (scale-dep) 替 CV → max_corr 0.935 退化为 F012 近重复。**升格教训**: rank-diff 结构 alpha 源依赖两端 signal family 都 scale-invariant（CV / ratio / correlation）；若一端 scale-dependent，rank-diff 退化。
> - **C005 rank-preserving 保序二证**: SignedPower(F012, 0.5) max_corr=**1.000** — 延续 batch_031 C004 CsZscore 1.000 教训，证实 DSL 层 {Linear / SignedPower(p>0) / Sigmoid / Tanh / Exp / Softmax} 对单已 admit 因子零信息增量。
> - **C006 signed illiq proxy 独立但弱**: Kyle-lambda 风格 Δturnover/turnover² max_corr=0.16（库独立）+ 9 年全负（sign_consistency=1.0），但 alpha_surv=0.17 + signed incr_ic=-0.031 稀释库 → reserve 负参考。
> - **MT budget**　cumulative 152 → **240** · direction 12 → **18** · bucket `high`（search_adjusted 0.54 medium, C003 strong 档保留）

> **Operations**　`status: saturated → productive` · `priority: low → medium` · rounds 2→3 · admits 1→2 · T006 ANSWERED, T005 保留 ACTIVE, 新开 T007（rank-diff 扩展到其他 signal family）。

> [!quote]- 2026-04-23 · [[batches/batch_031/judge|batch_031]] · T001 ANSWERED + T004 DISPROVEN · 方向 saturated
> admit=0 / reserve=1 (C003) / reject=5。
> - **F012 几何不变量**（5/6 候选）：10d/5d-return/CsZscore/vol-residualize/PB-cross 全部与 F012 相关 0.707-1.000
> - **T004 四子路径全败**：residualization 不是真 orth（rank-preserving 保序 / Div 搬家 / Div cross-field 量纲陷阱）
> - **C003 唯一略出 near_dup 线**但 CP04 alpha_surv 从 0.443 塌至 0.137（vol_20d exposure 3× 激活）——reserve 归档负证据
> - **3 条升格系统级教训**：(1) rank-preserving 变换 IC 零贡献；(2) DSL Div residualization ≠ 真 orth；(3) Div-based cross-field 与 Mul 撞同样量纲吞噬
> - **MT budget**　cumulative 146 → **152** · direction 6 → **12** · bucket `medium`
>
> **Operations**　`status: productive → saturated` · `priority: high → low` · 下轮换方向。

> [!quote]- 2026-04-23 · [[batches/batch_030/judge|batch_030]] · 方向首批打破 3 批零 admit 僵局
> admit=1 / reserve=4 / reject=1。
> - **T001 Amihud 家族（C001/C002/C006）**：首批 admit C001 (`amihud_illiq_20d`, 20d amount-denom, IC=0.034 ls_t=4.48 incr_ic=0.034 max_corr=0.754@F002)。C002 (60d) / C006 (turnover-denom) 作为 horizon × 字段对照 reserve，thread 保持 ACTIVE。
> - **T002 HHI 家族（C003/C004）**：两候选单体 strong（ls_t=±4.02/-4.08, mono=-1.0, 9 年全负）但 signed incremental_ic 均负（-0.013/-0.010）——F001 已吸收 amount 时序集中度维度。Thread ANSWERED。
> - **T003 HHI vs Entropy（C005）**：C005 TsEntropy ls_t=1.54 weak + mono=0.7，vs C003 HHI ls_t=-4.02 mono=-1.0——**单日极值驱动假设胜**，Entropy 变体 disproven。Thread DISPROVEN。
> - **系统级发现**：29 批 "DSL 层无空间" 断言被部分证伪——`AmihudIlliq` / `HHI` / `TsEntropy` 三原语真有 DSL-native 差异信号，但 admit 门槛严苛（必须高 incremental_ic 硬救）。
> - **MT budget**　cumulative 140 → **146** · direction 0 → **6** · bucket `medium`（search_adjusted 0.9→0.66 仍 medium）
>
> **Operations**　`status: exploring → productive (Phase 4 Python auto-flip on first admit)` · priority `high` 保留
