---
direction_tag: alpha191_universal_subset
status: productive
priority: high
rounds: 1
admits: 2
last_batch: batch_085
last_admits:
- F027
- F028
last_goal: 首批实装 paper-vetted Alpha191 子集 (Du-Walter-Ulrich 2026 17 因子白名单中 5 个 + alpha071
  BIAS 长窗 mean-reversion 第 6) 作为 csi1000 daily DSL baseline，验证 cross-market universal
  alpha 在散户主导小盘 universe 是否仍有 carry，目标 ≥1 admit + ≥2 reserve，机制层覆盖 multi-MA mean reversion
  / signed cumulative volume (OBV) / DMI directional pressure / ATR cross-day true
  range / Volume MACD / BIAS long-window % deviation 共 6 个互补 mechanism family
last_activity: '2026-05-02T17:52:48Z'
created_batch: batch_080
members:
- F027
- F028
merged_into: null
---
# alpha191_universal_subset

> [!abstract]+ 方向概要
> - **状态**　🟢 `productive`（首次 admit by Phase 4） · priority `high` · rounds = 1 · admits = 2
> - **最近**　[[batches/batch_085/judge|batch_085]] · 2026-05-02 · 2/1/3 (admit/reserve/reject) · 来源 [[papers/arxiv_2601_06499v1|arXiv 2601.06499v1 Cross-Market Alpha (Du-Walter-Ulrich 2026)]]
> - **一句话**　paper-vetted 17-因子白名单首批兑现 multi-MA reversion + DMI 双 admit, alpha_survival>1.0 第二/三例顶级实证 csi1000 反向迁移成立。

---

## Hypothesis

**外部独立先验**: Du-Walter-Ulrich (arXiv 2601.06499v1, 2026) 把 Alpha191 库整库 (剔除 23 个数值不稳 → 168 测试) 跑到 S&P 500 (2002-2022 monthly aggregated)，用 double-selection LASSO 同时控住 Jensen-Kelly-Pedersen (2023) 444-character US factor zoo 浓缩的 151 fundamental controls。**17 个 Alpha191 因子在 3×2 portfolio 上 t > 2.0 存活**，5×5 portfolio 扩到 29 个，PCA / Elastic Net 横向交叉验证发现核心 6-8 个签名因子三种估计器同时显著。

**A 股本地化主张**: A 股本土因子能在大盘机构化美股穿过 151-control DS-LASSO 等价于这些因子捕捉的是**纯行为/微观结构机制**而非"特定市场 anomaly"。Paper 自己承认 "explanatory power would be even more pronounced in U.S. small-cap or emerging markets where retail participation is higher"——把这条逻辑反向应用：对 csi1000 (中小盘 + 散户主导) 反向迁移这 17 个的预期 alpha 应该是 SPX 的**上界**而非下界。

**库覆盖盘点 (本方向 Phase 1 设计的关键归因)**:

| Alpha # | Mechanism family | 库内同形 F-id | 决策 |
|---|---|---|---|
| 046 | Multi-window MA composite mean reversion | **无** | 主候选 (T001) |
| 084 | Signed cumulative volume accumulation (OBV) | **无** | 主候选 (T002) |
| 049 | Directional pressure asymmetry (DMI) | **无** | 主候选 (T003) |
| 161 | Cross-day true range volatility (ATR) | **无** (单日 range 已饱和但跨日 jump 未覆盖) | 主候选 (T004) |
| 155 | Volume momentum / MACD-on-volume | **无** | 第二线 (T002 衍生) |
| 015 | Overnight gap return | F010/F011 已覆盖 | skip |
| 001 | Vol-growth × return neg corr | F018 邻接 (sign-aggregation 同生态位) | skip |
| 184 | 200d delayed price-gap correlation | gap_acceptance saturated 但 200d 未试 | thread T005 留给 round 2 |
| 071 | 24d % deviation from mean | mean-reversion 家族部分覆盖 | baseline 对照 |
| 063 | 6d RSI | F011 williams_r_variant 邻接 | baseline 对照 |
| 086 | 10d price acceleration vs directional change | asymmetric_momentum dead 但条件 momentum 未试 | thread T005 留给 round 2 |
| 054 | Intraday vol + corr (3 项加权和) | F006/F007/F008 高重叠风险 | 反面教材 不主推 |
| 123 | PV vs low-V correlation rank | F009 pv_corr (Grade A 79.9) 邻接 | 高重叠 |
| 073 | Nested decayed PV correlations | **vwap blocked** | 留给 vwap proxy 探索 |
| 039 | Decay-adjusted momentum-VWAP divergence | **vwap blocked** | 留给 vwap proxy 探索 |
| 181 | Benchmark-relative excess return skewness | **benchmark blocked** | 留给 universe-mean proxy 探索 |
| 190 | Log gain-to-loss variability ratio | borderline DSL | 留给 round 2 |

**与 lessons 风险位的对照**:

- **`gap_acceptance_structure` saturated**: Alpha 015 同形, 已 skip。本方向不重复 gap-acceptance 几何。
- **`asymmetric_momentum` / `return_momentum_acceleration` dead** (pure momentum 已证伪): Alpha 046 反向 — 是 mean reversion 多窗复合, 不是 momentum。Alpha 049 DMI 是 directional pressure ratio, 不是简单 momentum。
- **`vol_shock_signals` dead** (magnitude vol 普遍 collapse 到 vol_20d): Alpha 161 ATR 包含跨日 jump 项, 不是单日 range/std 同形。需在 Phase 3 看 max_corr@F001 (std_returns_20)。
- **`range_structure` saturated**: 单日 range 已饱和; Alpha 161 ATR 是其未覆盖的跨日维度。
- **`pv_covariance` active**: Alpha 084 OBV 是 PV 关系的方向化版本但机制独立 (sign accumulation vs covariance)。
- **`liquidity_acceleration` active**: Alpha 155 Volume MACD 与 volume 短长 spread 邻接, 需在 Phase 3 看 max_corr@F033 mean_turnover_5。

**多重检验风险 (paper-side)**: 17/168 = 10.1%, naive 5% threshold 期望 8.4 false positives。Paper 没做 Bonferroni / BH FDR 校正。**对策**: 优先实装在 3×2 + 5×5 + Elastic Net + PCA **三种估计器同时显著** 的核心 6-8 个 (046 / 084 / 073 / 123 / 049 / 071 / 184 / 155)；本方向首批只实装其中 4 个无 vwap / 无 benchmark / 库内未覆盖的子集。

---

## Current Focus

**Round 80 (首批)**: 主线测 **4 个 paper-vetted 库内未覆盖的 mechanism family** + 第二线 1 个 volume momentum, 全部 DSL 直译 (替换 SMA → EMA 并改写条件为 If/Sign):

1. Alpha 046 Multi-MA Mean Reversion Ratio
2. Alpha 084 OBV-20d (signed cumulative volume)
3. Alpha 049 DMI Down (directional pressure ratio)
4. Alpha 161 12-Day ATR (true range)
5. Alpha 155 Volume MACD Histogram (EMA-substituted)

预期: ≥1 admit (优先序 ATR > OBV > DMI > Multi-MA > VolMACD), ≥2 reserve。失败模式归因: ATR collapse @F001 std_returns_20, OBV collapse @F009 pv_corr, DMI sign-flip in csi1000 small-cap regime, Multi-MA collapse to 单窗 mean-reversion 已饱和, VolMACD collapse to F033 mean_turnover_5。

**Round 80 之后**: 若 ≥2 admit, 开 Round 2 探 5×5-only tail-sensitivity 子集 (Alpha 022/031/006/187/089 等); 若 0 admit 但有 reserve 火种, 改测 vwap proxy 路径 (Alpha 073/039 用 `$amount/$volume` 替代 vwap); 若全 reject, 升格 lessons "paper-vetted ≠ csi1000 universal" + 方向 saturated。

---

## Threads

### T001: Alpha 046 multi-window MA composite ratio 是否在 csi1000 上独立于现有 mean-reversion 家族提供新 alpha [✓ ANSWERED batch_085]

> [!success]+ Thread 结论
> **Question**: 4 个 MA 窗口 (3/6/12/24) 算术平均除以 spot price 的复合 mean-reversion 比率, 在 csi1000 daily 上是否携带与库内 F011 williams_r_variant / F022 close_position_amount_accel / F004 std_vol_20 (Grade B 73.1) 不冗余的信号? 多窗 vote 是否减少单窗 phase 噪声?
>
> **Answer**: ✓ admit. Alpha 046 multi-MA composite mean-reversion ratio 在 csi1000 daily 上**独立于现有 mean-reversion family** 提供新 alpha. ICIR=0.31, ls_t=4.36, alpha_survival=1.13 (Barra 空间真独立), incr_ic=0.034 (库增值 7 倍标准). 多窗 vote 通过 phase 噪声平均 + 跨 horizon 趋势-反转混合编码, 与现有库 OHLC daily intraday geometry 几何独立. C006 BIAS-24 长窗 mean-reversion 单窗对照 reject (max_corr 0.42@F009 越过 P008 frontier 阈值) — 说明多窗 vote 形式比单窗 % deviation form 更真实独立.
>
> **Evidence trail**:
> - [[batches/batch_085/candidates/C001|batch_085 C001]] `Div(Add(Add(Add(Mean($close,3),Mean($close,6)),Mean($close,12)),Mean($close,24)),Mul($close,4))` IC_oos=0.049 ICIR=0.31 alpha_surv=1.13 → **admit → [[factors/F027]]**
> - [[batches/batch_085/candidates/C006|batch_085 C006]] `TsRank(Div(Sub($close,Mean($close,24)),Mean($close,24)),60)` BIAS-24 + TsRank60 max_corr=0.42@F009 → **reject (P008 frontier 失败)**
>
> **Next probes**: round 2 可探 (5/10/20/60) 长窗组合 vs (3/6/12/24) 短窗组合对比, 验证 multi-MA composite 是否在更长 horizon 上仍独立; T001 已封闭。

### T002: Alpha 084 OBV-style signed cumulative volume 是否在 csi1000 散户市携带与 F009 pv_corr 不冗余的方向 imbalance 信号 [✗ DISPROVEN batch_085] (OBV) + Volume MACD reserved

> [!failure]+ Thread 结论 (OBV-20d)
> **Question**: `Sum(sign(close - prev_close) × volume, 20)` 这种 sign-aggregation 是否独立于 F009 pv_corr_times_vol 的 covariance 几何?
>
> **Answer**: ✗ DISPROVEN. OBV-20d 在 csi1000 散户市 (a) sign 翻转 (paper 正预测 vs IC=-0.027 全负 9 年); (b) Barra 完全吞噬 (alpha_survival=0.17 < 0.40 threshold, 残差仅 17%); (c) Q5-only 一桨 mono_oos=-0.3 弱单调; (d) incr_ic=-0.005 library reducer. F018 (overnight_sign_freq_amount_rank_diff_20) 已占据 sign-aggregation rank-diff 几何 prototype. paper-vetted ≠ csi1000 universal 实证。
>
> **Evidence trail**:
> - [[batches/batch_085/candidates/C002|batch_085 C002]] `Sum(Mul(Sign(Sub($close,Ref($close,1))),$volume),20)` IC_oos=-0.027 alpha_surv=0.17 mono_oos=-0.3 → **reject**
> - [[batches/batch_085/candidates/C005|batch_085 C005]] `Sub(Sub(EMA($volume,13),EMA($volume,27)),EMA(Sub(EMA($volume,13),EMA($volume,27)),10))` Volume MACD alpha_surv=1.39 (Barra 真独立) 但 mono_oos=-0.3 + incr_ic=-0.015 → **reserve (P008 软判定区火种)**
>
> **Next probes**: T002 split 为两条 — T002a OBV DISPROVEN; **T002b Volume MACD ratio-form 复测 ACTIVE** (优先路径: `MACD_hist / Mean(volume,27)` dim-less 化, round 2 测试)。

### T003: Alpha 049 DMI directional pressure 在 csi1000 小盘震荡市是否需要 sign 翻转 [✓ ANSWERED batch_085]

> [!success]+ Thread 结论
> **Question**: Welles Wilder DMI 的 -DI/(+DI + -DI) 在大盘趋势市 (paper SPX 测) 显著为正, csi1000 小盘震荡为主, sign 是否翻转?
>
> **Answer**: ✓ admit. **csi1000 sign 未翻转**, paper 同向 (train +0.040, val +0.033, 9 年同号正). DMI directional pressure asymmetry 在散户震荡市仍保持 paper sign, 不需 abs(DMI) magnitude proxy 替代. ICIR=0.23 borderline 但 ls_t=3.03 + 9 年同号 + cum_ic_mdd 仅 -1.23 时序极稳. 库内首次直接的 directional sign-aggregated magnitude ratio mechanism family.
>
> **Evidence trail**:
> - [[batches/batch_085/candidates/C003|batch_085 C003]] DMI Down ratio 12d IC_oos=0.033 ls_t=3.03 alpha_surv=0.66 → **admit → [[factors/F028]]**
>
> **Next probes**: T003 已封闭; round 2 可探 DMI Up (Sum(up DM,12)/(up+down)) 对偶形式 / DMI window 替换 (8/24) / DMI × turnover composite。

### T004: Alpha 161 12d ATR 跨日 jump 维度是否独立于库内单日 range 信号 [✗ DISPROVEN batch_085]

> [!failure]+ Thread 结论
> **Question**: True Range = max(单日 H-L, |prev_close - H|, |prev_close - L|) 包含跨日 gap jump, 跨日 jump 维度是否提供新信号? 还是 collapse 到 vol_20d?
>
> **Answer**: ✗ DISPROVEN. ATR-12d **完全 collapse 到 vol_20d** — vol_20d_exposure=31.4 整库顶级 (alpha killer 教科书级), alpha_survival=0.064 残差仅 6.4%. max_corr=0.66@F019 (high), incr_ic=-0.018 (强负). P006 library-reducer trio 齐全. 跨日 jump 项 (|prev_close-H|, |prev_close-L|) 在 cross-section 上与 single-day vol monotone-equivalent — 因为 vol_20d basis 计算就含 close-to-close return std. ATR ≡ vol_20d 升格 lessons "P018 律 ATR 扩展" 候选教训.
>
> **Evidence trail**:
> - [[batches/batch_085/candidates/C004|batch_085 C004]] ATR-12d IC_oos=-0.058 alpha_surv=0.064 max_corr=0.66@F019 vol_20d_exp=31.4 → **reject (P006 trio)**
>
> **Next probes**: T004 已封闭; ATR-of-overnight-only (剔除单日 H-L 项) 单独测试也大概率失败因 overnight gap 与 close-to-close return 同源 — **不建议复活**。

### T005: Paper-vetted but 库内邻接 / blocked 的 12 个因子何时复活 [◉ ACTIVE]

> [!note]+ Thread 当前
> **Question**: 5×5-only tail-sensitivity 子集 (Alpha 022/031/006/187/089/052/002/044/011/026/136/170) + vwap-blocked (Alpha 073/039) + benchmark-blocked (Alpha 181) + borderline-DSL (Alpha 190) 何时纳入测试? 触发条件是什么?
>
> **Evidence trail**:
> - (round 1 trigger 条件已满足 batch_085: ≥2 admit ✓ C001+C003 + ≥1 mechanism family alpha_surv 显著独立 ✓ C001 alpha_surv=1.13 + C005 alpha_surv=1.39)
>
> **Next probes**: Round 2 触发条件**全部满足** → 下批可推进:
> - 5×5 tail-sensitivity 子集首测 (Alpha 022/031/006 优先, 其 5×5 t > 3.0 + 库内未覆盖 mechanism)
> - vwap proxy `$amount/$volume`: Alpha 073 nested PV corr 的 vwap proxy 路径
> - C005 Volume MACD ratio-form 复测 (`MACD_hist / Mean(volume,27)` dim-less 化)
> - 后续 thread T006 待新候选设计后定。

---

## Known Failures

| Candidate | Expression | Reject Reason |
|---|---|---|
| [[batches/batch_085/candidates/C002\|C002]] | `Sum(Mul(Sign(Sub($close,Ref($close,1))),$volume),20)` | OBV-20d csi1000 sign 翻转 + alpha_surv=0.17 Barra 吞噬 + mono_oos=-0.3 Q5-only 一桨 + incr_ic=-0.005 library reducer |
| [[batches/batch_085/candidates/C004\|C004]] | `Mean(Greater(Greater(Sub($high,$low),Abs(Sub(Ref($close,1),$high))),Abs(Sub(Ref($close,1),$low))),12)` | ATR-12d ≡ vol_20d (exposure=31.4 顶级) + alpha_surv=0.064 + max_corr=0.66@F019 + incr_ic=-0.018: P006 trio 齐 |
| [[batches/batch_085/candidates/C006\|C006]] | `TsRank(Div(Sub($close,Mean($close,24)),Mean($close,24)),60)` | BIAS-24 + TsRank60 P008 frontier escape 失败 (max_corr=0.42@F009 越过 0.40 阈值) + incr_ic=-0.019 软判定区 reject |

---

## Related

- 🟡 [[gap_acceptance_structure]] `saturated` — Alpha 015 (overnight gap) 同生态位, 本方向不重复 gap-acceptance 几何; T007 cross-ratio Barra 吸收律已封该家族
- 🟢 [[intraday_price_formation]] `productive` — Alpha 054 (反面教材) 与 F006/F007/F008 body / corr 重叠风险, 本方向避开
- 🔴 [[asymmetric_momentum]] `dead` — pure momentum 已证伪; Alpha 046 反向 (mean-reversion 多窗复合)
- 🔴 [[return_momentum_acceleration]] `dead` — 同上, 与 Alpha 049 DMI 区别在 directional pressure ratio 而非 raw acceleration
- 🟡 [[range_structure]] `saturated` — 单日 range 饱和; Alpha 161 ATR 是其未覆盖的跨日 jump 维度
- 🔴 [[vol_shock_signals]] `dead` — magnitude vol 普遍 collapse 到 vol_20d; Alpha 161 需 Phase 3 看 max_corr@F001
- 🟢 [[pv_covariance]] `productive` — F009 pv_corr_times_vol Grade A; Alpha 084 OBV 是 PV 方向化, 机制独立但需 max_corr@F009 验证
- 🟢 [[liquidity_acceleration]] `productive` — Alpha 155 Volume MACD 邻接, 需 Phase 3 看 max_corr@F033 mean_turnover_5
- 🟢 [[microstructure_illiquidity]] `productive` — F012 amihud 系列邻接, 本方向无 illiq 同形候选
- 🔵 [[fundamental_quality_carry]] `exploring` — 完全独立 (本方向无 TTM 字段)
- [[lessons#Structural Constraints]]
- [[papers/arxiv_2601_06499v1]] — 来源 paper note (含 17 因子完整白名单 + DSL 转写 + 隐藏假设)

---

## Narrative Log

> [!quote]+ 2026-05-02 · [[batches/batch_085/judge|batch_085]]
> **paper-vetted Alpha191 universal-subset 首批兑现 2/6 admit + 1/6 reserve · 50% 信号留存** · admit = 2 / reserve = 1 / reject = 3
>
> - **paper 反向迁移假设部分成立**: 5 paper 主线候选 (C001-C005) 中 2 admit + 1 reserve, 与 paper 17/168 = 10.1% 期望兑现率比较, csi1000 反向迁移 (50%) 显著强于 paper SPX. 主要失败模式是 **csi1000 散户市 sign 翻转** (C002 OBV) + **vol_20d 结构性吸收** (C004 ATR), 与 paper 警告 "universe asymmetry" 一致.
> - **alpha_survival > 1.0 频次升级**: C001=1.13 + C005=1.39 一次性产出两例 daily-resolution Barra 真独立载体, 超过 lessons.md "P008 escape 机制层验证" 历史仅 b081 C006 一例 ≈1.0. 升格证据: P008 escape 不是 b081 一次性巧合.
> - **F009 anchor 显化**: 6 候选中 4 个 nearest=F009 (overnight_intraday_spread_5d), max_corr 0.21-0.54. F009 之前未被 lessons/INDEX 识别为 anchor, 本批显示 F009 是 daily close-anchor cluster prototype, 与 F025/F026 daily intraday position anchor 共同形成 csi1000 daily 三大 anchor. 提议 INDEX HOT-TOPICS-LLM 升格.
> - **新 admitted 因子**: F{next} multi_ma_reversion_4w (paper Alpha 046, ICIR=0.31 ls_t=4.36 alpha_surv=1.13) + F{next+1} dmi_down_ratio_12 (paper Alpha 049, ls_t=3.03 alpha_surv=0.66 9 年同号).
> - **MT budget**: cumulative 468 → 474 · direction 0 → 6 · bucket `medium`
>
> **Operations**　`status: exploring → productive` (Phase 4 auto on first admit) · priority `high` 保持 · T001+T003 ANSWERED · T002 split (T002a OBV DISPROVEN + T002b Volume MACD ACTIVE reserve) · T004 DISPROVEN · T005 round 2 trigger 满足
>
> **下一步**: round 2 推进 — (1) 5×5 tail-sensitivity 子集首测 (Alpha 022/031/006); (2) vwap proxy ($amount/$volume) for Alpha 073 nested PV corr; (3) C005 Volume MACD ratio-form 复测 (`MACD_hist / Mean(volume,27)`).
