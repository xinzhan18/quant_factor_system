---
direction_tag: microstructure_illiquidity
status: saturated
priority: low
rounds: 8
admits: 4
last_batch: batch_067
last_admits: []
last_goal: 'T009 (NEW): Non-Amihud microstructure illiquidity proxies, vol_20d-orthogonal
  LHS atoms

  with non-turnover non-H-L-60 non-amount-derived RHS. Round 3/3 of orchestrator cycle
  —

  prior 2 rounds confirmed operator-family novelty != style novelty (rolling-regression

  Slope/Resi, Skew/Kurt/autocorr/Rank-wrap all vol_20d-locked on csi1000 daily).


  Atoms (LHS) targeted:

  T009.a Roll-style serial covariance: -Cov(Delta close, Ref Delta close, 20) — Roll
  (1984)

  effective spread is sqrt(-cov of return changes); structurally different from variance

  (covariance of CHANGES, not magnitude of changes). Hypothesis: Roll-cov captures
  bid-ask

  bounce / mean-reversion microstructure noise, NOT vol_20d magnitude.


  T009.b Path-efficiency ratio (H-L vs |close-open|): Mean(|close-open| / (high-low+eps),
  20)

  — Kaufman efficiency ratio analog at bar level. High value = directional move

  (informed-trader path); low value = noisy zigzag (uninformed liquidity-provider
  path).

  Scale-free, NOT magnitude-aggregation, NOT |return|-aggregation.


  T009.c Order-flow imbalance proxy via close-vs-midpoint: Mean((close - (high+low)/2)
  /

  (high-low+eps), 20) signed quantity in [-0.5, 0.5]. Signed version of F022 close-position

  (which is unsigned in [0,1]). Sign-content not magnitude-content; orthogonal to
  F022

  geometry.


  T009.d Kyle-lambda directional proxy: Mean(Sign(close-open) × |close-open| / amount,
  20)

  — directional version of Amihud. Differs from F012 (unsigned |ret|/amount): captures

  signed price impact per unit volume = Kyle''s price-impact coefficient analog. Note:
  NOT

  rank-diff geometry, level form.


  RHS basis (escape turnover-family + H-L_60 + amount aggregations):

  - $market_cap level (size factor, NOT in dead-endpoint list)

  - $pe_ratio level (value factor, fresh basis)

  - $ps_ratio level (sales-multiple, fresh)


  Pre-checks: 4-anchor pre-check at design — F002 (PB×amount) RHS not used; F012 (Amihud

  numerator) LHS atoms structurally distinct (Roll-cov, signed paths); F020 (gap-anti)
  no

  gap content; F022 (close-position cluster) signed not unsigned, also paired with
  non-amount

  RHS. P006 trap mitigation: no rank-diff anchor structure → max_corr expected <0.30.'
last_activity: '2026-05-01T14:15:47Z'
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

### T005: sign-conditional / signed Amihud 变体 [✗ DISPROVEN batch_061]

> [!failure]+ Thread 结论 (4 路径全证伪 — quantile path 也是 library-reducer)
> **Question**: (1) sign asymmetry？(2) Kyle-lambda signed proxy？(3) 短窗 ≤5d？(4) max-min range non-mean aggregation？(5) **quantile-based asymmetry P90-P10 rolling**?
>
> **Answer**:
> - (1) 日频 20d **sign asymmetry 不存在**：up/down-day Amihud max_corr 0.942/0.918，对偶差 0.024。
> - (2) Kyle-lambda 库独立 (max_corr=0.16) 但 alpha_surv=0.17 + signed incr_ic=-0.031 → reserve 负参考。
> - (3) **batch_047 C005 短窗硬证伪**: 5d up-day Amihud max_corr 0.754，alpha_surv 反塌 **0.149**（F012 的 34%）→ trade-off 负面。
> - (4) **batch_047 C006 range 逃离失败**: range 与 F012 共变 86% (corr=0.862) → reserve。
> - (5) **batch_061 C005 quantile-Amihud P90-P10 P006 library-reducer 实证**: ls_t=3.21 + mono=1.0/1.0 + 9/9 yr 全正 + ls_sharpe=2.31 + lowest vol_20d=7.47 + style_r²=0.20 (整库罕见 risk-clean) BUT **incr_ic=-0.0023 NEG** → 看似最优 PnL 形状但加入 library 让组合信号变弱。**P006 第 6 次跨 family 复现**: mono≥0.85 + |ls_t|≥2.5 + incr_ic<0 + alpha_surv<0.40 全部命中。
>
> **Evidence trail**:
> - [[batches/batch_046/candidates/C001|b046 C001]] up-day 20d → 0.942@F012 reject
> - [[batches/batch_046/candidates/C002|b046 C002]] down-day 20d → 0.918@F012 reject
> - [[batches/batch_046/candidates/C005|b046 C005]] SignedPower(F012, 0.5) → max_corr=**1.000** reject (rank-preserving 二证)
> - [[batches/batch_046/candidates/C006|b046 C006]] Mean(Δturnover/turnover², 20) → reserve (signed neg)
> - [[batches/batch_047/candidates/C005|b047 C005]] up-day 5d → alpha_surv=**0.149** reject
> - [[batches/batch_047/candidates/C006|b047 C006]] TsMax-TsMin Amihud 5d → max_corr=**0.862** reserve
> - [[batches/batch_061/candidates/C005|b061 C005]] **quantile-Amihud P90-P10 rolling 20d × Mean(pe,60)** → ls_t=3.21 + mono=1.0/1.0 + 9/9 yr 全正 + ls_sharpe=2.31 但 **incr_ic=-0.0023 NEG** P006 library-reducer 第 6 次复现 → reject

### T009: non-Amihud microstructure proxies (Roll/Kyle/path-efficiency/signed-imbalance) [✗ DISPROVEN batch_067] (NEW thread, born-disproven)

> [!failure]+ Thread 结论
> **Question**: non-Amihud microstructure proxies (Roll covariance / Kaufman path-efficiency / Kyle signed-product / signed close-vs-midpoint imbalance) 是否在 csi1000 daily-bar cross-section 下携带独立于 Amihud (F012/F015/F016) family 的新 alpha?
>
> **Answer**: **non-Amihud microstructure 4 atoms 在 daily-bar 层全证伪**. 4 类 LHS 几何形式 (covariance / bounded-ratio / signed-product / signed-positional) 全部 vol_20d-嵌入 (P004) + 全部库 anchor cluster locked (P005, F009/F020/F022 anchor) + 三 PASS hard_gate 候选 P006 dual-gate 100% 命中 (incr_ic 全 ≤ 0.0017).
>
> **Evidence trail**:
> - [[batches/batch_067/candidates/C001|batch_067 C001]] Roll-cov level → ic_oos=-0.012 + max_corr=0.07 库内最 clean + incr_ic=-0.011 NEG + alpha_surv=0.23 → reject (P006 第 8 次复现, "clean-but-empty" 形式)
> - [[batches/batch_067/candidates/C002|batch_067 C002]] path-efficiency Mean → |IC_OOS|=0.0011 + decay 0.163 → reject (hard_gate, atom alpha density 不足 floor)
> - [[batches/batch_067/candidates/C003|batch_067 C003]] signed close-mid × $market_cap rank-diff → sign_flip + mono IS=-0.9→OOS=+0.9 catastrophic regime reversal → reject (hard_gate)
> - [[batches/batch_067/candidates/C004|batch_067 C004]] Kyle signed-product → ls_t=-3.0 + mono=-0.9/-0.9 强 + max_corr=0.37@F009 dead zone + incr_ic=-0.010 NEG + cum_mdd=-54.5 → reject (P006 第 9 次复现, "dead-zone-classic" 形式)
> - [[batches/batch_067/candidates/C005|batch_067 C005]] Roll-cov × pe rank-diff → |IC_OOS|=0.0009 + decay 0.131 → reject (hard_gate)
> - [[batches/batch_067/candidates/C006|batch_067 C006]] path-efficiency × ps rank-diff → ic_oos=+0.020 + mono=1.0/1.0 PERFECT + cum_mdd=-1.12 极浅 + max_corr=-0.59@F020 anti-cluster + incr_ic=+0.0017<<0.015 dual-gate → reject (P006 第 10 次复现, "illusion-form" 新形式)
>
> **升格 lessons 候选** (本 thread 贡献 3 条):
> 1. **non-Amihud microstructure atom 4 类几何全证伪 (csi1000 daily-bar)**: covariance / bounded-ratio / signed-product / signed-positional 4 类 LHS atom 形式跨 round 1-3 (rolling-regression / Skew-Kurt / Roll-Kyle-efficiency-imbalance) 全部 vol_20d-locked. minute-bar 数据接入前 microstructure direction daily-bar 探索路径关闭.
> 2. **P006 illusion-form 升格** (C006 新形态): mono=1.0 perfect + cum_mdd<-5 浅 + incr_ic<0.005 极低 + max_corr in [0.30, 0.70] = "PnL 美感掩盖 incremental 价值" trap. 应 codify 至 lessons.md P006 顶部反例段防止后续 LLM 被 PnL shape 美感诱导.
> 3. **F020 anchor cluster 跨 LHS/RHS 角色泛化**: F020 的 path-efficiency atom 作 RHS, 本批 C006 把同 atom 搬到 LHS, 仍 anti-cluster -0.59 — anchor 不仅占据 LHS+RHS 字段配对, 还占据 atom 在 Sub 两侧角色调换的 anti-mirror 位置 (P005 第 N 次扩展).
>
> **保留 OFF**: T009 thread closed. **复活路径**: (a) minute-bar 数据接入 (intraday Roll-cov / path-efficiency 在 5min bar 不被 daily vol 吸收); (b) F020 / F012 退役后重测 path-efficiency atom + ps_ratio rank-diff (C006 cum_mdd=-1.12 极浅 PnL 形状有 standalone value, 仅库 anchor 限制 admit); (c) Python OLS Barra residualize (DSL `Div(atom, vol_20d)` 不是真 orth, 已升格 lessons F304).

### T008: atp = $amount/$volume avg-trade-price atom [✗ DISPROVEN batch_061] (NEW thread, born-disproven)

> [!failure]+ Thread 结论
> **Question**: avg-trade-price (atp = $amount/$volume) 是否构成与 Amihud family (F012/F015/F016) 几何独立的新 microstructure atom？atp/close deviation (intraday-VWAP-vs-close) 与 atp_range_position (atp 在日内 range 中位置) 两 facet 是否各自独立？
>
> **Answer**: **atp atom 真实是 NEW dimension** (与 F012/F015/F016 corr 全 |<0.13|, 与 F019/F020/F021 OHLC family corr ≤|0.31|) **BUT 与 admit-eligible 因子 几何独立 ≠ admit-eligible** — 4 代 atp 几何变体 × 4 个 fresh RHS basis 6 候选全 reject。**atp + amount-derived RHS 几何位置落入 F017 anchor cluster** (overnight × turnover-family RHS 通用 cluster 槽), F017 anchor 范围扩大至 turnover-family RHS 任意聚合 (turnover_5 / Std turnover_60 / Med turnover_20 同 cluster)。
>
> **Evidence trail**:
> - [[batches/batch_061/candidates/C001|b061 C001]] Mean(atp-close-dev,20) × Std(turnover,60) → max_corr=0.531@F017 incr_ic=0.0098 borderline ls_t=1.60 → reject
> - [[batches/batch_061/candidates/C002|b061 C002]] **Std(atp-close-dev,20)** × Mean(pe,60) → alpha_surv=0.17 (vol_20d=51.79) + 9/9 yr 同号负 mono=-1.0 ls_t=-2.74 + cum_mdd=-55.89 → reject (P003 higher-moment regime sign-flip 边界 — atp-close-dev 单日与 |return| 同构, Std 二阶聚合直接落入 vol_20d 吸收)
> - [[batches/batch_061/candidates/C003|b061 C003]] Mean(atp_range_pos,20) × Mean(ps,60) → ls_t=0.94 weak + alpha_surv=0.32 max_corr=0.305@F021 → reject
> - [[batches/batch_061/candidates/C004|b061 C004]] Mean(atp_range_pos,5) × Med(turnover,20) → ls_t=1.48 weak + max_corr=0.603@F017 incr_ic=0.0117 borderline → reject
> - [[batches/batch_061/candidates/C006|b061 C006]] Mean(atp-close-dev,60) × Std(turnover,60) → 与 C001 同 RHS 同 LHS 跨窗口同构 max_corr=0.529@F017 incr_ic=0.0089 borderline → reject
>
> **升格 lessons 候选** (本 thread 贡献 3 条):
> 1. **F017 anchor cluster 占位律泛化** — admitted rank-diff factor 几何 anchor 跨 RHS family 任意聚合形式锁定 (而非局限原 RHS 字段窗口)
> 2. **higher-moment LHS axis 迁移条件收窄** — atom 必须与单日 |daily_return| / range 几何正交, 否则 Std/Var 二阶聚合直接落入 vol_20d 吸收 (P003 边界扩展)
> 3. **NEW atom 几何独立 ≠ admit-eligible** — 新 atom 与库内全部因子 corr<0.30 是必要非充分条件, 还需 atom + RHS 组合不落入已 admitted factor 的 cross-section anchor cluster
>
> **保留 OFF**: 当前 daily-bar + F017 健在条件下 atp atom 路径关闭。**复活路径**: (a) atp × non-amount/non-OHLC RHS (cross-day momentum / lag-shifted reference) 是否能脱 F017 cluster — 待测; (b) F017 退役后重测; (c) minute-bar 数据接入后 intraday atp variance / kurtosis 路径。
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
| [[batches/batch_067/candidates/C001\|b067 C001]] | `-Cov(Δp, Ref(Δp,1), 20)` Roll-cov level | CP05 incr_ic=-0.011 NEG + alpha_surv=0.23 + ls_t=-2.12 weak (P006 第 8 次复现, "clean-but-empty" 形式) |
| [[batches/batch_067/candidates/C002\|b067 C002]] | `Mean(\|body\|/(H-L), 20)` path-efficiency | CP01 hard_gate \|IC_OOS\|=0.0011<0.008 + decay 0.163 (atom alpha density 不足) |
| [[batches/batch_067/candidates/C003\|b067 C003]] | `Sub(CsRank(signed_close_mid),CsRank($market_cap))` | CP01 hard_gate sign_flip + mono IS=-0.9→OOS=+0.9 (P003 regime reversal) |
| [[batches/batch_067/candidates/C004\|b067 C004]] | `Mean(sign(close-open)·\|body\|/$amount, 20)` Kyle signed | CP05 incr_ic=-0.010 NEG + max_corr=0.37@F009 dead zone + alpha_surv=0.19 + cum_mdd=-54.5 (P006 第 9 次复现, "dead-zone-classic") |
| [[batches/batch_067/candidates/C005\|b067 C005]] | `Sub(CsRank(-Cov(Δp,Δp_{t-1},20)),CsRank($pe_ratio))` | CP01 hard_gate \|IC_OOS\|=0.0009<0.008 + decay 0.131 (T007 atom 复合需 ≥0.015 floor) |
| [[batches/batch_067/candidates/C006\|b067 C006]] | `Sub(CsRank(Mean(\|body\|/(H-L),20)),CsRank($ps_ratio))` | CP05 max_corr=-0.59@F020 anti-cluster + incr_ic=+0.0017<<0.015 dual-gate floor (P006 第 10 次复现, "illusion-form": mono=1.0 + cum_mdd=-1.12 美感掩盖 incremental 不足) |

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

> [!quote]+ 2026-05-01 · [[batches/batch_067/judge|batch_067]] · T009 NEW BORN-DISPROVEN · **productive → saturated** (admits 4 保持 / priority low 保持)
> admit=0 / reserve=0 / reject=6. 本批 zero admit, T009 (NEW non-Amihud microstructure 4 atoms) 全证伪. /factor-mine cycle Round 3/3.
> - **T009 NEW thread born-disproven**: 4 类 LHS atom 几何形式 (Roll covariance / Kaufman path-efficiency / Kyle signed-product / signed close-vs-midpoint imbalance) 跨 6 候选全 reject. PASS hard_gate 三候选 (C001/C004/C006) **P006 dual-gate 100% 命中** (incr_ic 全 ≤ 0.0017, 三种 typology 形态完整呈现): C001 "clean-but-empty" (max_corr=0.07 库内最 clean + incr_ic=-0.011 NEG) / C004 "dead-zone-classic" (max_corr=0.37 + incr_ic=-0.010 NEG + ls_t=-3.0 强 PnL 但 cum_mdd=-54.5 灾难) / C006 "illusion-form" (mono=1.0 PERFECT + cum_mdd=-1.12 极浅 PnL 美感 + max_corr=-0.59@F020 anti-cluster + incr_ic=+0.0017<<0.015 dual-gate). FAIL hard_gate 三候选: C002 (atom alpha density 不足 floor) / C003 (signed positional × size factor regime catastrophic 翻盘 P003) / C005 (Roll-cov × pe rank-diff atom 信号被 PE RHS 稀释).
> - **P004 vol_20d structural absorption 跨第 4 类 atom 复现**: round 1 (rolling-regression) + round 2 (Skew/Kurt/autocorr/Rank-wrap) + **本批 round 3 (Roll-cov/path-efficiency/Kyle-signed/signed-close-mid)** 三轮跨 12 候选独立证实 csi1000 daily-bar cross-section 上 vol_20d-orthogonal subspace 已被 F002/F012/F018/F020/F022/F023 anchor cluster 完全占据. C006 vol_20d exposure=17.63 整库顶级极值 (efficiency ratio 看似 bounded [0,1] vol-orthogonal 但深度嵌入). C004 vol_20d=9.32 + str_1m=4.00 双 absorber. C001 vol_20d=7.26 (Roll covariance 本应 vol-orthogonal 但 cross-section 仍部分嵌入).
> - **F020 anchor cluster 跨 LHS/RHS 角色泛化**: F020 的 path-efficiency atom 在原表达式作 RHS (`Sub(CsRank(Std(gap_ret,20)), CsRank(Mean(|body|/(H-L),20)))`); 本批 C006 把同 atom 搬到 **LHS**, 仍 anti-cluster -0.59 — anchor 不仅占据字段配对 (P005), 还占据 atom 在 Sub 两侧角色调换的 anti-mirror 位置. P005 第 N 次扩展.
> - **direction status 转换**: 信号设计层证据 ≥4 路径 cluster ✓ (Amihud-family + non-Amihud 4 atoms 全 closed) + 数据契约层 minute-bar 不可达 ✓ + Python OLS Barra residual 已 DISPROVEN (T004 b031). **双层 saturated 证据律满足** → status `productive → saturated`. T005/T008/T009 三 thread 全 DISPROVEN; T007 ACTIVE 但本批未推进; T001/T006 ANSWERED (admits 4 保持). priority 保持 low.
> - **MT budget**: cumulative 360→**366** · direction 30→**36** · bucket `high` (search_adjusted `medium-low`)
> - **zero_admit_streak**: 系统级 7→8 · **rounds_since_consolidation**: 7→8 (距 10 阈值 2 批, 临近 consolidation 触发)
>
> **Operations**: status `productive → saturated` (T009 NEW + 双层证据律) · priority `low` 保持 · rounds 6→7 · admits 4 保持 · members [F012, F015, F016] 保持
>
> **复活路径** (saturated → productive 重启条件): (a) minute-bar 数据接入 (intraday Roll-cov / path-efficiency 在 5min bar 不被 daily vol 吸收); (b) F020 / F012 anchor 退役后重测 C006 path-efficiency × ps_ratio rank-diff (cum_mdd=-1.12 极浅 + mono=1.0 perfect + 9/9 年全正 magnitude 稳定 — standalone value 真实, 仅库 anchor 限制 admit); (c) Python OLS Barra residualize 于原始 atom 层 (DSL `Div(atom, vol_20d)` 已 DISPROVEN F304); (d) Kyle/Roll family 长 horizon evaluation policy 调整 (10d-20d C006 IC 上升 0.034-0.051 显示长 horizon 信号增强).
>
> **升格 lessons 候选 (3 条)**: (1) non-Amihud microstructure atom 4 类几何全证伪; (2) P006 illusion-form 新形态 codify; (3) F020 anchor cluster 跨 LHS/RHS 角色泛化.

> [!quote]- 2026-04-28 · [[batches/batch_061/judge|batch_061]] · T005 DISPROVEN · T008 NEW BORN-DISPROVEN · productive (admits 4 保持 / priority medium → low)
> admit=0 / reserve=0 / reject=6。本批 zero admit, T005 quantile path + T008 atp atom 双 thread 关闭。
> - **T005 quantile-Amihud P90-P10 path P006 library-reducer 实证**: C005 ls_t=3.21 + mono=1.0/1.0 + 9/9 yr 全正 + ls_sharpe=2.31 + lowest vol_20d=7.47 + style_r²=0.20 (整批最干净 risk profile) BUT **incr_ic=-0.0023 NEG** P006 第 6 次跨 family 复现。**T005 thread DISPROVEN**: quantile spread (P90-P10) of magnitude-distribution 几何线性独立但 Barra + library 组合层冗余, 三 Amihud factor (F012 Mean / F015 CV / F016 turnover-CV) 联合已捕获分布形状 sufficient statistic。
> - **T008 (NEW) atp = $amount/$volume avg-trade-price atom 4 代变体全 reject**: atp atom 真实是 NEW dimension (与 F012/F015/F016 Amihud family corr 全 |<0.13|, 与 F019/F020/F021 OHLC family corr ≤|0.31|) BUT atp + amount-derived RHS 几何位置落入 F017 anchor cluster (4/6 候选 max_corr 0.51-0.60@F017)。**升格教训 (3 条 lessons 候选)**: (1) F017 anchor cluster 占位律泛化 (跨 RHS family 任意聚合形式锁定, 而非局限原字段窗口); (2) higher-moment LHS axis 迁移条件收窄 (atom 必须与单日 |daily_return| / range 几何正交否则 Std 二阶聚合直接落入 vol_20d 吸收); (3) NEW atom 几何独立 ≠ admit-eligible (atom + RHS 组合不落入已 admitted factor 的 cross-section anchor cluster 才充分)。
> - **C002 P003 higher-moment regime sign-flip atp family 实证**: Std(atp-close-dev,20) × Mean(pe,60) — alpha_surv=0.17 critical + vol_20d=51.79 极端 + cum_ic_mdd=-55.89 catastrophic + 9/9 yr 同号负 (sign consistency 1.0 但 IS-OOS 同号深亏)。F019/F020 OHLC + gap higher-moment LHS axis **不能迁移到 atp-close family** (atp-close-dev 单日嵌入 vol_20d 几何位置)。
> - **方向 ACTIVE thread 状态**: T005 (sign-conditional Amihud) DISPROVEN · T007 (rank-diff 跨 direction 泛化) ACTIVE 但本批未推进 · T008 (atp atom NEW) DISPROVEN at 创建批。剩余 ACTIVE thread 仅 T007, 但 microstructure 方向 daily-bar 几何剩余探索路径稀薄。
> - MT budget cumulative 318→**324** · direction 24→**30** · bucket `high` (search_adjusted 0.51 → medium)
>
> **Operations**: status `productive` 保留 (4 admits + F015/F016 A级仍优秀) · `priority: medium → low` (T005/T008 双 disproven, T007 未推进, 探索路径稀薄, 等论文/数据接入或 F017 退役后重启) · rounds 5→6 · admits 4 保持 · zero_admit_streak 1→2 (全系统连续 2 批 zero admit)

> [!quote]- 2026-04-25 · [[batches/batch_047/judge|batch_047]] · T007 PARTIAL-ANSWERED · T005 FURTHER-DISPROVEN · productive (admits 2→3, 后续 +F016 至 4)
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
