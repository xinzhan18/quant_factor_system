---
direction_tag: microstructure_illiquidity
status: productive
priority: medium
rounds: 5
admits: 4
last_batch: batch_047
last_admits:
- F016
last_goal: 'T007 rank-diff 范式泛化 + T005 短窗 sign-conditional 重试。batch_046 admit F015
  (CsRank(Amihud_20) - CsRank(amount_CV_10))

  兑现 rank-diff 结构 alpha 源，升格教训：两端 signal family 必须都 scale-invariant (CV / ratio /
  correlation) 才独立。

  本批按此范式在其他 scale-free signal 对上泛化：(1) CsRank(Amihud_20) - CsRank(turnover_rate_CV_20)
  换分母 CV 字段

  测 amount vs turnover dispersion 对 Amihud 的正交性；(2) CsRank(pb_amount_ratio) - CsRank(Amihud)
  跨方向 value×liquidity

  rank-diff，两端都 scale-free；(3) CsRank(amount_CV_10) - CsRank(overnight_gap_20) amount×pct-signal，两端完全独立
  direction；

  (4) 反转对 CsRank(turnover_CV) - CsRank(Amihud) 测 rank-diff 方向对称性。(5)(6) T005 短窗 ≤5d
  sign-conditional 重试

  避开 batch_046 确认的 "20d mean aggregation 抹平 day-level sign gate" 失败律。目标 ≥ 1 candidate
  同时满足 max_corr@admitted < 0.50 + alpha_survival > 0.40 + ls_t > 2。'
last_activity: '2026-04-24T20:00:08Z'
created_batch: batch_030
members:
- F012
- F015
- F{id}@batch_047_C001
- F016
retired_members: []
merged_into: null
---
# microstructure_illiquidity

> [!abstract]+ 方向概要
> - **状态**　🟢 `productive` · priority `medium` · rounds = 5 · admits = 4
> - **最近**　[[batches/batch_047/judge|batch_047]] · 2026-04-25 · admit=1 (C001 → F016) / reserve=1 (C006) / reject=4
> - **一句话**　rank-diff geometry `Sub(CsRank(LHS_scale-free), CsRank(RHS_scale-free))` 在本方向连续两批 admit (F015, F016)，是当前 6-family 系统级范式的发源地；T005 sign-conditional 仅 quantile path 未测、T007 rank-diff 跨字段泛化保留 ACTIVE。

---

## Hypothesis

> [!note]+ Hypothesis · DSL-native · 已扩展为 rank-diff geometry 发源方向
> 现有库已覆盖 **amount dispersion**（F001 amount_cv_10）与 **valuation × liquidity level**（F002 pb_amount_ratio_20），但 **microstructure illiquidity** —— Amihud (2002) 定义的"单位成交额引发的价格冲击" —— 是 DSL 空间剩余独立轴。`AmihudIlliq` / `HHI` / `TsEntropy` 三原语零使用。
>
> **三条经济学线索**
> 1. **Illiquidity premium (Amihud 2002)**: `Mean(|return| / $amount, n)` 高的股票承担流动性风险 → 横截面 return premium 补偿。与 vol_20d 不同：测 *price-impact per dollar*。
> 2. **Trading concentration (HHI)**: `HHI($amount, n)` 测时序集中度——high HHI = 单日巨量主导（信息事件），low HHI = 均匀成交。与 F001 代数独立。
> 3. **Concentration asymmetry**: `TsEntropy($amount, n)` 与 HHI 数学孪生；同时有效 = 维度稳健，HHI 赢 Entropy 输 = 极端单日驱动。
>
> **结构性约束**
> - **市值代理红线**：Amihud 1/amount 可能与 1/market_cap 高相关——触 `|corr($market_cap)| > 0.3` 即 reject。
> - **vol_20d 耦合**：|return| 出现在分子，天然与 vol_20d 相关；分母 cross-section 归一化可剥离部分。记录 `style_r²` 与 `alpha_survival`。
> - 双窗口（20d/60d）测 horizon；双字段分母（$amount/$turnover_rate）测 normalization。
>
> **⚠️ 升格 (Phase 5 F002/F305 promotion)**：本方向是 **rank-diff geometry 设计范式的发源地**——`Sub(CsRank(LHS), CsRank(RHS))` 在 6 family 兑现 6 admit (F015–F020)，但范式不是万能钥匙。新候选必须严格 cite **rank-diff 7 条硬约束**（详见 lessons.md `Rank-Diff Geometry`）：(1) 两端 scale-invariant；(2) raw field 独立；(3) 同字段跨窗口禁止；(4) Sub 方向对偶 dedup；(5) 同批 LHS 共享 anchor rule；(6) RHS 共振饱和动态；(7) factor-anchored cluster (F012/F015/F016 已占据 rank-diff 端点)。

---

> [!success]+ Current Focus（batch_046+047 后）
> 方向从 `saturated → productive`：连续两批 rank-diff admit (F015 amount_CV / F016 turnover_CV)。**复活条件 (b) rank-diff symmetric interactions** 兑现。
>
> **泛化范围收窄硬证据 (batch_047)**: T007 跨 direction 失败两端：(a) C002 $amount 共分母 → noise；(b) C003 amount_CV 被 F001 主导吸收 → signed neg。
>
> **未兑现复活路径**: (a) Python Barra residualized F012 → 归 [[directions/barra_residual_alpha]]；(c) minute-bar/tick 数据暂无；(d) F012 健在不需家族复活。
>
> **下一轮**: T007 ACTIVE，focus shift 至 Amihud × correlation-based (`Corr($close, $amount, 20)`) 或库内其他 scale-free 对的 rank-diff（F007 upper_shadow_pct × F010 overnight）；T005 仅 **quantile-based asymmetry (P90-P10 rolling Amihud)** 未测。**新设计必须先做 7 条 gate 检查清单 (F002 升格)**。

---

## Threads

### T007: rank-diff 范式跨 signal family 泛化 [◉ ACTIVE]

> [!success]+ Thread 结论 (PARTIAL ANSWERED batch_047)
> **Question**: rank-diff 范式（CsRank(X) - CsRank(Y), 两端 scale-free）在其他 signal family 对上是否也有效？
>
> **Answer**: 部分泛化成立。**可行空间收窄为"同 direction 内部 scale-free × scale-free 字段对换"**；跨 direction 泛化两个硬约束。
>
> **Evidence trail**:
> - [[batches/batch_047/candidates/C001|batch_047 C001]]　`Sub(CsRank(Amihud_20), CsRank(turnover_CV_20))` → **admit → F016 amihud_turnover_cv_rank_diff_20** · ic_oos=0.050 mono_oos=1.0 ls_t=6.76 alpha_surv=0.579 max_corr=0.734@F015 incr_ic=0.023 · 9/9 年全正
> - [[batches/batch_047/candidates/C002|batch_047 C002]]　`Sub(CsRank(pb_amount_ratio_20), CsRank(Amihud_20))` → ic_oos=|-0.0074|<0.008 → hard_gate fail（$amount 共分母 Sub 抵消）
> - [[batches/batch_047/candidates/C003|batch_047 C003]]　`Sub(CsRank(amount_CV_10), CsRank(overnight_gap_20))` → max_corr=0.692@F001 incr_ic=**-0.0038** → reject（F001 吸收主导端）
> - [[batches/batch_047/candidates/C004|batch_047 C004]]　C001 Sub 翻转 → 完美数学反号 → reject（同批 anchor rule）
>
> **升格教训** (已并入 lessons.md `Rank-Diff Geometry` 7 条硬约束 via F002/F305):
> 1. 两端 raw field-level 独立（不共享 raw field）
> 2. 一端未被库因子主导吸收（否则 Sub 抵消主效应 → signed incr_ic 为负）
> 3. **rank-diff Sub 方向对偶律**：`Sub(A,B)` 与 `Sub(B,A)` 数学完全反号 → generator 应 pre-dedup
> 4. 同 direction 内部 scale-free 字段对换比跨 direction 泛化更可靠
>
> **保留 ACTIVE**: 下轮可测 (1) Amihud × correlation-based (`Corr($close, $amount, 20)`)；(2) 库内其他 scale-free 对（F007 × F010 等）；(3) "field-level 独立 + scale-free" 双条件跨 direction 候选。

### T005: sign-conditional / signed Amihud 变体 [◉ ACTIVE — 仅 quantile path 未测]

> [!failure]+ Thread 结论 (3 路径全证伪 / 1 路径未测)
> **Question**: (1) sign asymmetry？(2) Kyle-lambda signed proxy？(3) 短窗 ≤5d？(4) max-min range non-mean aggregation？
>
> **Answer**:
> - (1) 日频 20d **sign asymmetry 不存在**：up/down-day Amihud max_corr 0.942/0.918，对偶差 0.024。
> - (2) Kyle-lambda 库独立 (max_corr=0.16) 但 alpha_surv=0.17 + signed incr_ic=-0.031 → reserve 负参考。
> - (3) **batch_047 C005 短窗硬证伪**: 5d up-day Amihud max_corr 0.754，alpha_surv 反塌 **0.149**（F012 的 34%）→ trade-off 负面。
> - (4) **batch_047 C006 range 逃离失败**: range 与 F012 共变 86% (corr=0.862) → reserve。
>
> **Evidence trail**:
> - [[batches/batch_046/candidates/C001|b046 C001]] up-day 20d → 0.942@F012 reject
> - [[batches/batch_046/candidates/C002|b046 C002]] down-day 20d → 0.918@F012 reject
> - [[batches/batch_046/candidates/C005|b046 C005]] SignedPower(F012, 0.5) → max_corr=**1.000** reject (rank-preserving 二证)
> - [[batches/batch_046/candidates/C006|b046 C006]] Mean(Δturnover/turnover², 20) → reserve (signed neg)
> - [[batches/batch_047/candidates/C005|b047 C005]] up-day 5d → alpha_surv=**0.149** reject
> - [[batches/batch_047/candidates/C006|b047 C006]] TsMax-TsMin Amihud 5d → max_corr=**0.862** reserve
>
> **升格教训**:
> 1. day-level sign gate + window mean aggregation 抹平 asymmetry（20d/5d 双证伪）
> 2. max-min range 与 level 共变 86% → range-based 无法逃离 level 引力
> 3. **rank-preserving 变换族零信息增量**（已升格 lessons.md via F007）
> 4. Kyle-lambda 方向库独立但 alpha 弱
>
> **剩余复活路径**: 仅 **quantile-based asymmetry (P90-P10 rolling Amihud)** 未测——非 mean / 非 max-min 的 quantile-range 可能提取 tail asymmetry 不与 level 同构。Thread 保留 ACTIVE 等 quantile DSL 表达或 minute-bar 数据接入。

### T006: rank-diff symmetric interactions [✓ ANSWERED batch_046]

> [!success]- Thread 结论
> **Q**: 跨 signal family 的 CsRank 差结构是否能在 F012 之外开辟独立 alpha 子空间？
> **A**: 是。C003 `Sub(CsRank(Amihud_20d), CsRank(amount_CV_10d))` admit → **F015** — IC_oos=0.054 mono_oos=1.0 ls_t=6.63 alpha_surv=0.658 incr_ic=0.031 max_corr=0.655@F012。**rank-diff scale-free 属性脱离 F012 主子空间**。
> **升格教训**: 两端必须都 scale-invariant（CV/ratio/correlation）；scale-dependent (Std/Mean/level) 退化为主因子近重复。C003/C004 对照（C004 Std 变体 max_corr=0.935）首个硬证据。

### T001: Amihud 类 illiquidity 指标 [✓ ANSWERED batch_031]

> [!success]- Thread 结论
> **Q**: Mean(|return|/$amount, n) 与 Mean(|return|/$turnover_rate, n) 是否提供独立 illiquidity premium？
> **A**: 是。F012 (Amihud 20d amount-denom) 是 DSL 空间几何不变量。horizon 扫描（10d/20d/60d/5d）与分母扫描全部落入 near_duplicate 或 ls_t weak。
> **关键 admit**: [[batches/batch_030/candidates/C001|b030 C001]] → **F012 amihud_illiq_20d** · IC_OOS=0.034 ls_t=4.48 incr_ic=0.034 max_corr=0.754@F002 alpha_surv=0.443
> **升格教训**: 后续探索必须走 Python Barra residual 或非线性合成。

### T004: Amihud residualization + cross-field 交互 [✗ DISPROVEN batch_031]

> [!failure]- Thread 结论
> **Q**: DSL 层 Div-residualize 或 PB/Amihud cross-field 是否打开 illiquidity × value 第三维？
> **A**: 全否。CsZscore 保序、vol-residualize 放大 vol_20d、turnover-residualize 搬家 (alpha_surv 塌 69%)；Div cross-field 撞量纲。
> **升格教训** (已并入 lessons.md via F304):
> 1. Rank-preserving 变换 IC 零贡献
> 2. DSL `Div(factor, proxy)` 不是真 orthogonalization
> 3. Div-based cross-field 撞量纲吞噬 → 真 orth 必走 Python OLS

### T002: 成交额时序集中度（HHI）[✓ ANSWERED batch_030]

> [!success]- Thread 结论
> **Q**: HHI($amount/$turnover, 20) 是否独立于 F001(Std/Mean)？
> **A**: 机制真实存在但库已吸收。HHI 与 F001 corr=0.59-0.60 + signed incr_ic 均负 (-0.013/-0.010) → reserve。
> **复活条件**: F001 retire 后 HHI 可作 amount-family 代表复活；residualize 版若 signed positive incr_ic 可重开。

### T003: 集中度 vs 分散度的代数孪生对比 [✗ DISPROVEN batch_030]

> [!failure]- Thread 结论
> **Q**: HHI vs TsEntropy 哪个赢？
> **A**: **HHI 赢 (ls_t=-4.02)、Entropy 输 (ls_t=1.54)**。amount 时序集中度的经济信号是**单日极端事件驱动**，不是分布均匀度驱动。
> **升格教训**: 代数孪生在真实市场数据上经常不等价——同维度的不同矩统计量对不同尾部结构敏感，应同时测才能定位真实数据结构。

---

## Known Failures

| Candidate | Expression | Reject Reason |
|---|---|---|
| [[batches/batch_030/candidates/C005\|b030 C005]] | `TsEntropy($amount, 20)` | CP03 weak (ls_t=1.54) + signed incr_ic≈0 + mono=0.7 |
| [[batches/batch_031/candidates/C001\|b031 C001]] | 10d Amihud | hard_gate near_dup 0.957@F012 |
| [[batches/batch_031/candidates/C002\|b031 C002]] | `Div(Amihud, Std(ret,20))` | hard_gate 0.919@F012；vol-residualize 放大 vol_20d 5.9→32.6 |
| [[batches/batch_031/candidates/C004\|b031 C004]] | `CsZscore(Amihud)` | hard_gate **1.000**@F012 (rank-preserving 保序) |
| [[batches/batch_031/candidates/C005\|b031 C005]] | 5d-return Amihud | hard_gate 0.959@F012 |
| [[batches/batch_031/candidates/C006\|b031 C006]] | `Div($pb_ratio, Amihud)` | CP05 high + signed incr_ic=-0.044 |
| [[batches/batch_046/candidates/C001\|b046 C001]] | up-day Amihud 20d | hard_gate 0.942@F012 |
| [[batches/batch_046/candidates/C002\|b046 C002]] | down-day Amihud 20d | hard_gate 0.918@F012 |
| [[batches/batch_046/candidates/C004\|b046 C004]] | `Sub(CsRank(Std_amount), CsRank(Amihud_20d))` | hard_gate 0.935 (Std scale-dep 破坏 rank-diff 范式) |
| [[batches/batch_046/candidates/C005\|b046 C005]] | `SignedPower(F012, 0.5)` | hard_gate **1.000** (rank-preserving 二证) |
| [[batches/batch_047/candidates/C002\|b047 C002]] | `Sub(CsRank(pb_amount_ratio_20), CsRank(Amihud_20))` | CP01 hard_gate ic_oos=\|-0.0074\|<0.008；$amount 共分母 Sub 抵消 |
| [[batches/batch_047/candidates/C003\|b047 C003]] | `Sub(CsRank(amount_CV_10), CsRank(overnight_gap_20))` | CP05 max_corr=0.692@F001 + signed incr_ic=-0.0038 |
| [[batches/batch_047/candidates/C004\|b047 C004]] | `Sub(CsRank(turnover_CV_20), CsRank(Amihud_20))` | C001 Sub 翻转数学反号；同批 anchor rule |
| [[batches/batch_047/candidates/C005\|b047 C005]] | `Mean(If(ret>0,ret/amount,0), 5)` | CP04 alpha_surv=0.149 + max_corr=0.754@F012 |

---

## Related

- 🟢 [[amount_volatility_signal]] `productive` — F001 所在方向；F001 吸收 20d 时序集中度是 T002 reserve 的核心原因
- 🟢 [[value_liquidity_interaction]] `saturated` — F002 所在方向；F305 升格证伪：rank-diff 在 saturated 方向被 F002 anchor cluster 锁死
- 🟢 [[overnight_intraday_split]] `productive` — 同期 rank-diff 兑现方向（F017/F018），F305 律 (3)/(5) 升格源
- 🟢 [[ohlc_temporal_aggregation]] `productive` — F019 admit；F305 higher-moment LHS axis 跨 family 复现源
- 🟢 [[gap_acceptance_structure]] `productive` — F020 admit；higher-moment LHS axis 跨 family 复现
- 🟡 [[turnover_structural_signal]] `saturated` — HHI(turnover) 已在本方向补测 → reserve
- 🟡 [[barra_residual_alpha]] `saturated` — F304 升格：Python residual coverage<0.80 系统性边界
- 🔵 [[intraday_price_formation]] `saturated` — F305 边界证伪源（F020 anti-anchor cluster 锁死）
- 🔵 [[liquidity_acceleration]] `exploring` — incremental_ic 为负 reserve 先例
- [[lessons#Rank-Diff Geometry]] — 7 条硬约束 (F002/F305 升格)
- [[lessons#Path Selection]] — DSL Div / rank-preserving ≠ 真 orthogonalization (F304 升格)
- [[lessons#CP05 Redundancy]] — `incr_ic_min_when_corr_borderline = 0.015` (F203 升格)
- [[lessons#Threshold Calibration]] — `alpha_surv_min.rank_diff = 0.30` direction-aware 阈值 (F200 升格)
- [[lessons#Operator Registry]] — rank-preserving family AST hard_gate 规则 (F007 升格)

---

## Phase 5 Findings 升格摘要

> [!info]+ 本方向被 6 个 distillation findings 引用（截至 batch_054）
>
> **F002 (high · pattern_analyst)**: rank-diff geometry 范式律——本方向是 6-family 兑现的发源地 (F015/F016)，7 条硬约束已升格 lessons.md `Rank-Diff Geometry`。新候选起手必须做 7 条 gate 清单。
>
> **F007 (medium · pattern_analyst)**: Rank-preserving 变换零增量律 + "Barra-clean ≠ library-clean" 律。本方向 b031 C004 (CsZscore=1.000) + b046 C005 (SignedPower=1.000) 是双独立证据。已升格 lessons.md `Operator Registry`。
>
> **F200 (high · calibration)**: 引入 `alpha_surv_min.rank_diff = 0.30` direction-aware 阈值——rank-diff 结构 vol_20d exposure 是几何宿命，0.30-0.40 区间是真实信号，不应单 dealbreaker reject。F015/F016 兑现。
>
> **F203 (medium · calibration)**: codify `incr_ic_min_when_corr_borderline = 0.015`。本方向 b047 C001 (incr=0.023) 是该准则的 admit precedent。
>
> **F304 (medium · hypothesis_promoter)**: DSL `Div / rank-preserving` 不替代真 orthogonalization——T004 三条升格教训 (CsZscore 保序 / Div 搬家 / Div cross-field 撞量纲) 升格 lessons.md `Path Selection`。
>
> **F305 (medium · hypothesis_promoter)**: rank-diff geometry 五律 + 泛化边界——本方向 T006/T007 升格教训 (1)/(2)/(4) 是 5 律的源；saturated 方向 (value-liq, intraday) 失败定义边界。

---

## Narrative Log

> [!quote]+ 2026-04-25 · [[batches/batch_047/judge|batch_047]] · T007 PARTIAL-ANSWERED · T005 FURTHER-DISPROVEN · productive (admits 2→3, 后续 +F016 至 4)
> admit=1 (C001 → F016) / reserve=1 (C006) / reject=4。
> - **C001 T007 rank-diff 泛化首锤**: `Sub(CsRank(Amihud_20), CsRank(turnover_CV_20))` admit — ic_oos=0.050 mono_oos=1.0 ls_t=6.76 alpha_surv=0.579 incr_ic=0.023 max_corr=0.734@F015 9/9 年全正。证实 rank-diff 范式泛化到分母字段替换仍产出独立 alpha。
> - **C002/C003 T007 范式边界硬证据**: C002 $amount 共分母让 Sub 抵消 → noise；C003 amount_CV 端被 F001 吸收 → signed neg incr_ic=-0.0038 reject。**T007 范式 2 约束升格**: (a) 两端 raw field 独立；(b) 两端未被库因子主导。
> - **C004 Sub 方向对偶硬证据**: C001 vs C004 数学完美反号 (|corr|=1) → 同批 anchor rule reject。**generator 层应 pre-dedup**。
> - **C005 T005 (a) 短窗硬证伪**: 5d up-day Amihud max_corr 0.754 但 alpha_surv **0.149** (F012 的 34%) → trade-off 负面。
> - **C006 T005 range 逃离失败**: 5d max-min range 与 F012 共变 86% → reserve。
> - **MT budget**: cumulative 240→**246** · direction 18→**24** · bucket `high`
>
> **Operations**: `status: productive` 保留 · `priority: medium` 保留 · rounds 3→4 · admits 2→3 · T007 ACTIVE (partial answered) · T005 (a) disproven 但 thread 保留 ACTIVE 等 quantile path

> [!quote]- 2026-04-25 · [[batches/batch_046/judge|batch_046]] · T006 ANSWERED · T005 PARTIAL-DISPROVEN · saturated → productive
> admit=1 (C003 → F015) / reserve=1 (C006) / reject=4。
> - **C003 rank-diff breakthrough**: `Sub(CsRank(Amihud_20d), CsRank(amount_CV_10d))` 兑现复活条件 (b) — IC_oos=0.054 mono_oos=1.0 ls_t=6.63 alpha_surv=0.658 incr_ic=0.031 max_corr=0.655@F012 9/9 年全正。
> - **C001/C002 sign-conditional 对偶结题**: up/down-day Amihud max_corr 0.942/0.918 → 日度 20d 窗口 sign asymmetry 被均值抹平。
> - **C004 rank-diff 设计范式硬证据**: 同 C003 结构但分母 Std (scale-dep) → max_corr 0.935 退化。**升格教训**: rank-diff 两端必须都 scale-invariant。
> - **C005 rank-preserving 保序二证**: SignedPower(F012, 0.5) max_corr=**1.000**。
> - **C006 signed illiq proxy 独立但弱**: max_corr=0.16 但 alpha_surv=0.17 + signed neg → reserve。
> - **MT budget**: cumulative 152→**240** · direction 12→**18** · bucket `high`
>
> **Operations**: `status: saturated → productive` · `priority: low → medium` · rounds 2→3 · admits 1→2 · T006 ANSWERED, T005 ACTIVE, 新开 T007.

> [!quote]- 2026-04-23 · [[batches/batch_031/judge|batch_031]] · T001 ANSWERED + T004 DISPROVEN · 方向 saturated
> admit=0 / reserve=1 (C003) / reject=5。
> - **F012 几何不变量**（5/6 候选）：10d/5d-return/CsZscore/vol-residualize/PB-cross 全部与 F012 相关 0.707-1.000
> - **T004 四子路径全败**：residualization 不是真 orth
> - **3 条升格系统级教训**：(1) rank-preserving 变换 IC 零贡献；(2) DSL Div ≠ 真 orth；(3) Div-based cross-field 撞量纲吞噬
> - **MT budget**: cumulative 146→**152** · direction 6→**12** · bucket `medium`
>
> **Operations**: `status: productive → saturated` · `priority: high → low`.

> [!quote]- 2026-04-23 · [[batches/batch_030/judge|batch_030]] · 方向首批打破僵局
> admit=1 (C001 → F012) / reserve=4 / reject=1。
> - **T001 Amihud 家族**: F012 (`amihud_illiq_20d`, IC=0.034 ls_t=4.48 incr_ic=0.034 max_corr=0.754@F002) admit
> - **T002 HHI 家族**: 单体 strong 但 signed incremental_ic 均负 → F001 已吸收 amount 时序集中度
> - **T003 HHI vs Entropy**: HHI 赢 Entropy 输 → 单日极值驱动假设胜
> - **MT budget**: cumulative 140→**146** · direction 0→**6** · bucket `medium`
>
> **Operations**: `status: exploring → productive` · priority `high` 保留.
