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
> - **状态**　🔵 `saturated` · priority `low` · rounds = 8 · admits = 4 (F012 / F015 / F016)
> - **最近**　[[batches/batch_067/judge|batch_067]] · 2026-05-01 · admit=0 / reserve=0 / reject=6 (T009 全证伪)
> - **一句话**　Amihud-family + non-Amihud microstructure 4 atom 几何 daily-bar 全枯; rank-diff geometry 发源地 (F015/F016 兑现 6-family 范式), 但 anchor cluster lock 律 + P004 vol_20d 嵌入律 + P006 library-reducer 律三层 saturated 封口。

---

## Hypothesis

> [!note]+ Hypothesis · DSL-native · rank-diff geometry 发源方向
> Amihud (2002) "单位成交额引发的价格冲击" 是 DSL 空间剩余独立轴。本方向兑现路径已收敛为：
> 1. **Amihud level (F012)** — DSL 空间几何不变量, 后续 horizon / 分母 / residualize 扫描全 near_dup
> 2. **rank-diff geometry (F015/F016)** — `Sub(CsRank(scale-free LHS), CsRank(scale-free RHS))` 是 6-family 系统级范式发源地
>
> **结构性约束**
> - 市值代理红线 `|corr($market_cap)| > 0.3` reject; |return| 分子天然嵌入 vol_20d (P004); 双窗口 / 双分母扫描记录 `style_r²` + `alpha_survival`
> - **rank-diff 7 条硬约束** (lessons.md `Rank-Diff Geometry`, F002/F305 升格): (1) 两端 scale-invariant; (2) raw field 独立; (3) 同字段跨窗口禁止; (4) Sub 方向对偶 dedup; (5) 同批 LHS anchor rule; (6) RHS 共振饱和动态; (7) factor-anchored cluster (F012/F015/F016 已占据 rank-diff 端点)
>
> **⚠️ Saturated 封口证据 (3 层)**
> 1. **anchor cluster lock 律** (P005 第 N 次扩展): F012/F015/F016 + F017/F020/F022 anchor 跨 LHS/RHS/字段配对/Sub 两侧角色调换全部锁定 — atp atom (b061) + non-Amihud 4 atom (b067) max_corr 全部命中 anchor; F020 path-efficiency atom 跨 LHS/RHS 角色对换仍 anti-cluster -0.59 (b067 C006)
> 2. **P004 vol_20d structural absorption**: round 1 (rolling-regression) + round 2 (Skew/Kurt/autocorr/Rank-wrap) + round 3 (Roll-cov / path-efficiency / Kyle-signed / signed-close-mid) **三轮 12 候选独立证实** csi1000 daily-bar vol_20d-orthogonal subspace 已被 anchor cluster 完全占据
> 3. **P006 library-reducer 律 10 次复现**: incr_ic dual-gate (signed neg 或 < 0.015 borderline) 跨 family 系统性命中, b067 三种 typology 完整呈现 — "clean-but-empty" (C001 max_corr=0.07 但 incr_ic=-0.011) / "dead-zone-classic" (C004 ls_t=-3 强但 incr_ic=-0.010 + cum_mdd=-54.5) / "illusion-form" (C006 mono=1.0 + cum_mdd=-1.12 美感但 incr_ic=+0.0017<<0.015)
>
> **复活路径** (saturated → productive 重启): (a) minute-bar 数据接入 (intraday Roll-cov / path-efficiency / atp variance 不被 daily vol 吸收); (b) F012 / F017 / F020 anchor 退役后重测 path-efficiency × ps_ratio rank-diff (b067 C006 cum_mdd=-1.12 + 9/9 yr 全正 standalone value 真实, 仅 anchor 限制 admit); (c) Python OLS Barra residualize 于原始 atom 层 (DSL `Div(atom, vol_20d)` 已 DISPROVEN F304); (d) Kyle/Roll family 长 horizon evaluation policy 调整。

---

## Threads

### T007: rank-diff 范式跨 signal family 泛化 [◉ ACTIVE]

> [!success]+ Thread 结论 (PARTIAL ANSWERED batch_047)
> **Q**: rank-diff 范式 (CsRank(X) − CsRank(Y), 两端 scale-free) 跨 signal family 是否有效?
> **A**: 部分泛化成立。可行空间收窄为"同 direction 内部 scale-free × scale-free 字段对换"; 跨 direction 泛化两个硬约束 (raw field 独立 + 两端均未被库因子主导吸收)。
>
> **Evidence trail**:
> - [[batches/batch_047/candidates/C001|b047 C001]] `Sub(CsRank(Amihud_20), CsRank(turnover_CV_20))` → **admit → F016** · ic_oos=0.050 ls_t=6.76 incr_ic=0.023 max_corr=0.734@F015
> - [[batches/batch_047/candidates/C002|b047 C002]] `Sub(CsRank(pb_amount_ratio_20), CsRank(Amihud_20))` → ic_oos=|0.0074|<0.008 ($amount 共分母 Sub 抵消)
> - [[batches/batch_047/candidates/C003|b047 C003]] `Sub(CsRank(amount_CV_10), CsRank(overnight_gap_20))` → max_corr=0.692@F001 incr_ic=−0.0038 (F001 吸收主导端)
> - [[batches/batch_047/candidates/C004|b047 C004]] C001 Sub 翻转 → 数学反号 (同批 anchor rule)
>
> **保留 ACTIVE**: 下轮可测 (1) Amihud × correlation-based (`Corr($close, $amount, 20)`); (2) 库内其他 scale-free 对 (F007 × F010); (3) "field-level 独立 + scale-free" 双条件跨 direction。

### T005: sign-conditional / signed Amihud 变体 [✗ DISPROVEN batch_061]

> [!failure]+ Thread 结论 (5 路径全证伪)
> **Q**: (1) sign asymmetry / (2) Kyle-lambda signed / (3) 短窗 ≤5d / (4) max-min range / (5) quantile-based asymmetry P90-P10 rolling?
> **A**: 全否。
> - (1) 日频 20d up/down-day Amihud max_corr 0.942/0.918 — 均值抹平 sign asymmetry
> - (2) Kyle-lambda 库独立 (max_corr=0.16) 但 alpha_surv=0.17 + signed incr_ic=−0.031
> - (3) 5d up-day Amihud alpha_surv=0.149 (F012 的 34%) trade-off 负面
> - (4) max-min range 与 F012 共变 86% (corr=0.862) range-based 无法逃离 level
> - (5) **quantile-Amihud P90-P10 P006 library-reducer 实证** (b061 C005): ls_t=3.21 + mono=1.0/1.0 + 9/9 yr 全正 + ls_sharpe=2.31 + lowest vol_20d=7.47 (整库罕见 risk-clean) BUT **incr_ic=−0.0023 NEG** — quantile spread 几何线性独立但 F012/F015/F016 联合已捕获分布形状 sufficient statistic, P006 第 6 次跨 family 复现
>
> **Evidence**: b046 C001/C002 (sign), b046 C005 SignedPower=1.000 (rank-preserving 二证), b046 C006 signed turnover, b047 C005/C006, b061 C005 quantile.

### T009: non-Amihud microstructure proxies (Roll/Kyle/path-efficiency/signed-imbalance) [✗ DISPROVEN batch_067, born-disproven]

> [!failure]+ Thread 结论
> **Q**: non-Amihud 4 atom (Roll covariance / Kaufman path-efficiency / Kyle signed-product / signed close-vs-midpoint) 在 csi1000 daily-bar 是否携带独立 alpha?
> **A**: **4 类几何全证伪**。LHS 形式跨 covariance / bounded-ratio / signed-product / signed-positional 全 vol_20d-嵌入 (P004) + 全库 anchor cluster locked (P005, F009/F020/F022) + 三 PASS hard_gate 候选 P006 dual-gate 100% 命中。
>
> **Evidence trail** (b067):
> - C001 Roll-cov level → max_corr=0.07 库内最 clean BUT incr_ic=−0.011 NEG + alpha_surv=0.23 (P006 "clean-but-empty")
> - C002 path-efficiency Mean → |IC_OOS|=0.0011 + decay 0.163 (atom alpha density 不足 floor)
> - C003 signed close-mid × $market_cap rank-diff → sign_flip + mono IS=−0.9→OOS=+0.9 catastrophic regime reversal
> - C004 Kyle signed-product → ls_t=−3.0 强 + max_corr=0.37@F009 dead zone + incr_ic=−0.010 NEG + cum_mdd=−54.5 (P006 "dead-zone-classic")
> - C005 Roll-cov × pe rank-diff → |IC_OOS|=0.0009 + decay 0.131 (T007 atom 复合需 ≥0.015 floor)
> - C006 path-efficiency × ps rank-diff → mono=1.0/1.0 PERFECT + cum_mdd=−1.12 极浅 + max_corr=−0.59@F020 anti-cluster + incr_ic=+0.0017<<0.015 (P006 "illusion-form" 新形态)
>
> **保留 OFF**。复活路径见 Hypothesis 块。

### T008: atp = $amount/$volume avg-trade-price atom [✗ DISPROVEN batch_061, born-disproven]

> [!failure]+ Thread 结论
> **Q**: avg-trade-price (atp = $amount/$volume) 是否构成与 Amihud family 几何独立的新 microstructure atom?
> **A**: **atp atom 真实是 NEW dimension** (与 F012/F015/F016 corr 全 |<0.13|, 与 OHLC family corr ≤|0.31|) **BUT 几何独立 ≠ admit-eligible** — 4 代 atp 几何变体 × 4 fresh RHS 6 候选全 reject。**atp + amount-derived RHS 落入 F017 anchor cluster** (4/6 候选 max_corr 0.51-0.60@F017)。
>
> **Evidence trail** (b061): C001 (atp-close-dev × Std turnover_60 max_corr=0.531@F017) / C002 (Std atp-close-dev × pe alpha_surv=0.17 + cum_mdd=−55.89 P003 边界) / C003-C004 (atp_range_pos 弱 ls_t<1.5) / C006 (60d 跨窗口同构 0.529@F017)。
>
> **保留 OFF**。

### T006: rank-diff symmetric interactions [✓ ANSWERED batch_046]

> [!success]- Thread 结论
> **Q**: 跨 signal family 的 CsRank 差结构是否能在 F012 之外开辟独立 alpha 子空间?
> **A**: 是。C003 `Sub(CsRank(Amihud_20d), CsRank(amount_CV_10d))` admit → **F015** — IC_oos=0.054 ls_t=6.63 incr_ic=0.031 max_corr=0.655@F012。
> **升格教训**: 两端必须都 scale-invariant; scale-dependent (Std/Mean/level) 退化为主因子近重复 (C004 Std 变体 max_corr=0.935 对照硬证)。

### T001: Amihud 类 illiquidity 指标 [✓ ANSWERED batch_031]

> [!success]- Thread 结论
> **Q**: Mean(|return|/$amount, n) / Mean(|return|/$turnover_rate, n) 是否提供独立 illiquidity premium?
> **A**: 是。**F012 (Amihud 20d amount-denom)** 是 DSL 空间几何不变量。horizon × 分母扫描全 near_duplicate 或 ls_t weak。
> **关键 admit**: [[batches/batch_030/candidates/C001|b030 C001]] → **F012 amihud_illiq_20d** · IC_OOS=0.034 ls_t=4.48 incr_ic=0.034 max_corr=0.754@F002 alpha_surv=0.443。

### T004: Amihud residualization + cross-field 交互 [✗ DISPROVEN batch_031]

> [!failure]- Thread 结论
> **A**: 全否。CsZscore 保序、vol-residualize 放大 vol_20d、turnover-residualize 搬家、Div cross-field 撞量纲。3 条升格教训 (rank-preserving IC 零贡献 / DSL `Div` ≠ 真 orth / Div cross-field 撞量纲) 已升格 lessons.md `Path Selection` (F304)。

### T002 / T003: HHI vs TsEntropy [✓ ANSWERED batch_030]

> [!success]- Thread 结论
> T002 HHI($amount/$turnover, 20) vs F001: corr=0.59-0.60 + signed incr_ic 均负 → reserve (F001 已吸收 amount 时序集中度)。
> T003 HHI vs Entropy: HHI 赢 (ls_t=−4.02), Entropy 输 (ls_t=1.54) — amount 集中度信号是**单日极值驱动**, 不是分布均匀度驱动。代数孪生在真实数据上不等价。

---

## Known Failures

| Candidate | Expression | Reject Reason |
|---|---|---|
| [[batches/batch_030/candidates/C005\|b030 C005]] | `TsEntropy($amount, 20)` | CP03 weak ls_t=1.54 + signed incr_ic≈0 |
| [[batches/batch_031/candidates/C001\|b031 C001]] | 10d Amihud | hard_gate 0.957@F012 |
| [[batches/batch_031/candidates/C002\|b031 C002]] | `Div(Amihud, Std(ret,20))` | hard_gate 0.919; vol-residualize 放大 vol_20d |
| [[batches/batch_031/candidates/C004\|b031 C004]] | `CsZscore(Amihud)` | hard_gate **1.000**@F012 (rank-preserving) |
| [[batches/batch_031/candidates/C005\|b031 C005]] | 5d-return Amihud | hard_gate 0.959@F012 |
| [[batches/batch_031/candidates/C006\|b031 C006]] | `Div($pb_ratio, Amihud)` | CP05 + signed incr_ic=−0.044 |
| [[batches/batch_046/candidates/C001\|b046 C001]] / C002 | up/down-day Amihud 20d | hard_gate 0.942 / 0.918@F012 |
| [[batches/batch_046/candidates/C004\|b046 C004]] | `Sub(CsRank(Std_amount), CsRank(Amihud_20d))` | hard_gate 0.935 (Std scale-dep 破坏 rank-diff) |
| [[batches/batch_046/candidates/C005\|b046 C005]] | `SignedPower(F012, 0.5)` | hard_gate **1.000** (rank-preserving 二证) |
| [[batches/batch_047/candidates/C002-C005\|b047 C002-C005]] | rank-diff variants | $amount 共分母 / F001 吸收 / Sub 反号 / alpha_surv=0.149 |
| [[batches/batch_061/candidates/C001-C006\|b061 C001-C006]] | atp atom × 4 RHS | T008 borndisproven; F017 anchor cluster (4/6 max_corr 0.51-0.60) + C002 cum_mdd=−55.89 + C005 quantile P006 第 6 次 (incr_ic=−0.0023) |
| [[batches/batch_067/candidates/C001\|b067 C001]] | Roll-cov level | incr_ic=−0.011 NEG + alpha_surv=0.23 (P006 "clean-but-empty") |
| [[batches/batch_067/candidates/C002\|b067 C002]] | `Mean(\|body\|/(H-L),20)` | hard_gate \|IC_OOS\|=0.0011 |
| [[batches/batch_067/candidates/C003\|b067 C003]] | signed close-mid × $market_cap | hard_gate sign_flip mono IS=−0.9→OOS=+0.9 |
| [[batches/batch_067/candidates/C004\|b067 C004]] | Kyle signed-product | incr_ic=−0.010 + max_corr=0.37@F009 + cum_mdd=−54.5 (P006 "dead-zone-classic") |
| [[batches/batch_067/candidates/C005\|b067 C005]] | Roll-cov × pe rank-diff | hard_gate \|IC_OOS\|=0.0009 |
| [[batches/batch_067/candidates/C006\|b067 C006]] | path-efficiency × ps rank-diff | max_corr=−0.59@F020 anti-cluster + incr_ic=+0.0017<<0.015 (P006 "illusion-form") |

---

## Related

- 🟢 [[amount_volatility_signal]] `productive` — F001 吸收 20d 时序集中度 (T002 reserve 核心因)
- 🟢 [[value_liquidity_interaction]] `saturated` — F002 anchor; F305 边界证伪源
- 🟢 [[overnight_intraday_split]] `productive` — F017/F018 同期 rank-diff; F305 律 (3)/(5) 升格源
- 🟢 [[ohlc_temporal_aggregation]] `productive` — F019 admit; higher-moment 跨 family 复现
- 🟢 [[gap_acceptance_structure]] `productive` — F020 admit; b067 C006 anti-cluster source
- 🟡 [[turnover_structural_signal]] `saturated` — HHI(turnover) 已补测
- 🟡 [[barra_residual_alpha]] `saturated` — F304 Python residual coverage<0.80 边界
- 🔵 [[intraday_price_formation]] `saturated` — F305 边界 (F020 anti-anchor lock)
- 🔵 [[liquidity_acceleration]] `exploring` — incremental_ic 负 reserve 先例
- [[lessons#Rank-Diff Geometry]] — 7 条硬约束 (F002/F305)
- [[lessons#Path Selection]] — DSL Div / rank-preserving ≠ 真 orth (F304)
- [[lessons#CP05 Redundancy]] — `incr_ic_min_when_corr_borderline = 0.015` (F203)
- [[lessons#Threshold Calibration]] — `alpha_surv_min.rank_diff = 0.30` (F200)
- [[lessons#Operator Registry]] — rank-preserving family AST hard_gate (F007)

---

## Phase 5 Findings 升格摘要

> [!info]+ 本方向被 6 个 distillation findings 引用 (截至 batch_054)
> - **F002 (high · pattern_analyst)**: rank-diff geometry 范式律发源地 (F015/F016), 7 条硬约束已升格
> - **F007 (medium · pattern_analyst)**: rank-preserving 零增量律 + "Barra-clean ≠ library-clean" (b031 C004 + b046 C005 双独立证据)
> - **F200 (high · calibration)**: `alpha_surv_min.rank_diff = 0.30` direction-aware 阈值 (F015/F016 兑现)
> - **F203 (medium · calibration)**: `incr_ic_min_when_corr_borderline = 0.015` (b047 C001 incr=0.023 admit precedent)
> - **F304 (medium · hypothesis_promoter)**: DSL `Div / rank-preserving` 非真 orth (T004 三条升格)
> - **F305 (medium · hypothesis_promoter)**: rank-diff geometry 五律 + 泛化边界 (T006/T007 升格源)

---

## Narrative Log

> [!quote]+ 2026-05-01 · [[batches/batch_067/judge|batch_067]] · T009 NEW BORN-DISPROVEN · **productive → saturated**
> admit=0 / reserve=0 / reject=6. T009 (non-Amihud 4 atoms) 全证伪, /factor-mine cycle Round 3/3。
> - **T009 born-disproven**: 4 类 LHS atom 几何 (Roll-cov / path-efficiency / Kyle-signed / signed close-mid) 跨 6 候选全 reject. 三 PASS hard_gate 候选 **P006 dual-gate 100% 命中** 三种 typology 完整呈现 — C001 "clean-but-empty" / C004 "dead-zone-classic" / C006 "illusion-form" (新形态: mono=1.0 + cum_mdd=−1.12 美感掩盖 incremental 不足)。
> - **P004 vol_20d structural absorption 第 3 轮 (Roll/path-eff/Kyle/signed-mid) 复现**: 三轮 12 候选独立证实 csi1000 daily-bar vol_20d-orthogonal subspace 已被 F002/F012/F018/F020/F022/F023 anchor cluster 完全占据 (C006 vol_20d=17.63 整库顶级)。
> - **F020 anchor cluster 跨 LHS/RHS 角色泛化**: F020 path-efficiency atom 原作 RHS, b067 C006 搬到 LHS 仍 anti-cluster −0.59 — anchor 占据 atom 在 Sub 两侧角色调换的 anti-mirror 位置 (P005 第 N 次扩展)。
> - **双层 saturated 证据律满足**: 信号设计层 ≥4 路径 closed (Amihud + non-Amihud 4 atom) + 数据契约层 minute-bar 不可达 + Python OLS Barra residual DISPROVEN (T004 b031) → status `productive → saturated`, T005/T008/T009 全 DISPROVEN, T007 ACTIVE 但本批未推进。
> - MT budget 360→**366** · direction 30→**36** · zero_admit_streak 7→8 · rounds_since_consolidation 7→8。
>
> **Operations**: status `productive → saturated` · priority `low` 保持 · rounds 7 · admits 4 保持 · members [F012, F015, F016] 保持。**升格 lessons 候选 (3)**: non-Amihud 4 类几何全证伪 / P006 illusion-form 新形态 / F020 anchor LHS-RHS 角色对换泛化。

> [!quote]- 2026-04-28 · [[batches/batch_061/judge|batch_061]] · T005 DISPROVEN · T008 NEW BORN-DISPROVEN · priority medium → low
> admit=0 / reserve=0 / reject=6. T005 quantile path + T008 atp atom 双 thread 关闭。
> - **T005 quantile-Amihud P90-P10 P006 实证**: C005 ls_t=3.21 + mono=1.0/1.0 + 9/9 yr 全正 + ls_sharpe=2.31 + lowest vol_20d=7.47 BUT **incr_ic=−0.0023 NEG** P006 第 6 次跨 family 复现 → T005 DISPROVEN。
> - **T008 atp atom**: NEW dimension 真实 (corr<|0.13| with Amihud family) BUT atp + amount-derived RHS 落入 F017 anchor cluster (4/6 max_corr 0.51-0.60)。3 条升格教训: F017 cluster 占位律泛化 / higher-moment LHS 迁移条件收窄 / 几何独立 ≠ admit-eligible。
> - **C002 P003 atp 实证**: Std(atp-close-dev,20) × Mean(pe,60) alpha_surv=0.17 + vol_20d=51.79 + cum_mdd=−55.89 + 9/9 yr 同号负 — atp-close-dev 单日嵌入 vol_20d, OHLC higher-moment LHS 不能迁移 atp family。
> - MT budget 318→**324** · direction 24→**30** · zero_admit_streak 1→2。

> [!quote]- 2026-04-25 · [[batches/batch_047/judge|batch_047]] · T007 PARTIAL-ANSWERED · admit=1 → F016
> admit=1 (C001 → F016) / reserve=1 / reject=4。C001 `Sub(CsRank(Amihud_20), CsRank(turnover_CV_20))` admit (ic_oos=0.050 ls_t=6.76 incr_ic=0.023 max_corr=0.734@F015 9/9 全正)。**T007 范式 2 约束升格**: (a) raw field 独立; (b) 两端未被库主导。**Sub 方向对偶律** (C001/C004 数学反号) generator 应 pre-dedup。MT 240→**246** · direction 18→**24**。

> [!quote]- 2026-04-25 · [[batches/batch_046/judge|batch_046]] · T006 ANSWERED · saturated → productive · admit=1 → F015
> C003 `Sub(CsRank(Amihud_20d), CsRank(amount_CV_10d))` rank-diff breakthrough (IC_oos=0.054 ls_t=6.63 incr_ic=0.031 max_corr=0.655@F012 9/9 全正) — 兑现复活条件 (b)。C001/C002 sign-conditional 对偶结题 (max_corr 0.942/0.918)。C004 Std 变体退化 max_corr=0.935 → **rank-diff 两端必须 scale-invariant**。C005 SignedPower(F012,0.5) max_corr=**1.000** (rank-preserving 二证)。MT 152→**240**。

> [!quote]- 2026-04-23 · [[batches/batch_031/judge|batch_031]] · T001 ANSWERED + T004 DISPROVEN · 方向 saturated
> admit=0 / reserve=1 / reject=5. F012 几何不变量 (5/6 候选 corr 0.707-1.000)。T004 四子路径全败: residualization 不是真 orth。3 条升格教训: rank-preserving IC 零贡献 / DSL Div ≠ 真 orth / Div cross-field 撞量纲吞噬 (升格 lessons.md F304)。`status: productive → saturated` · `priority: high → low`。

> [!quote]- 2026-04-23 · [[batches/batch_030/judge|batch_030]] · 方向首批打破僵局 · admit=1 → F012
> T001 Amihud admit: F012 amihud_illiq_20d (IC=0.034 ls_t=4.48 incr_ic=0.034 max_corr=0.754@F002)。T002 HHI 单体 strong 但 signed incremental_ic 均负 → F001 已吸收。T003 HHI 赢 Entropy 输 (单日极值驱动)。`status: exploring → productive`。
