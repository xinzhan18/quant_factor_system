---
direction_tag: alpha191_universal_subset
status: saturated
priority: high
rounds: 2
admits: 2
last_batch: batch_086
last_admits: []
last_goal: 'Round 2 续探 paper-vetted Alpha191 universal subset 三条路径: (a) 5×5 tail-sensitivity
  子集 Alpha 022 (二阶 mean-reversion / change-in-BIAS) + Alpha 031 (BIAS-12 单窗 baseline)
  + Alpha 006 cross-section sign-of-delta; (b) Alpha 073 nested PV corr 用 $amount/$volume
  作 vwap proxy 的 P019-safe rank-spread 形式; (c) C005 Volume MACD ratio-form 复测 dim-less
  化. 避免 ATR (alpha161 vol_20d 吞噬) + OBV (csi1000 sign 翻转). T005 round 2 推进.'
last_activity: '2026-05-03T07:38:47Z'
created_batch: batch_080
members:
- F027
- F028
merged_into: null
---
# alpha191_universal_subset

> [!abstract]+ 方向概要
> - **状态**　🟢 `productive` · priority `high` · rounds = 2 · admits = 2 (round 2 reserve 1)
> - **最近**　[[batches/batch_086/judge|batch_086]] · 2026-05-03 · 0/1/5 (admit/reserve/reject) · 来源 [[papers/arxiv_2601_06499v1|arXiv 2601.06499v1 Cross-Market Alpha (Du-Walter-Ulrich 2026)]]
> - **一句话**　round 2 paper 5×5 tail-sensitivity 子集 (Alpha 022/031/006) + vwap proxy + Volume MACD ratio-form 三路径全证伪; alpha_surv > 1.0 三连但 incr_ic 全负 — 升格元教训"P008 形式层 ≠ library 充分条件" (T006 ACTIVE)。

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

**Round 3 计划 (post b086)**: T005 收窄到 **P008 escape 单变量优化** (基于 C006 reserve 形式 — `TsRank(BIAS_6 - lag3 BIAS_6, 60)` mono_oos=-0.70 + alpha_surv=1.21 + decay=1.21):

1. **字段族替换**: $turnover_rate / $amount / $num_trades 替代 $close 减少与 OHLC reversion family cluster (避免 b086 C001 与 F006-F027 整族 -0.44~-0.46 cluster 重演)
2. **TsRank 窗口**: 90 / 120 测试是否进一步 vol-normalize (b086 C006 60d alpha_surv=1.21, 长窗口可能提高至 ≥ 1.5)
3. **CsRank 包装**: 测 cross-section standardize 后 incr_ic 是否转正 (b086 C006 incr_ic=-0.0067 微负, CsRank 可能消除 cluster correlation)

**放弃**: paper 5×5 剩余 9 个 (Alpha 187/089/052/002/044/011/026/136/170) 全部基于 OHLC + price-only cross-section rank 几何, 与 b086 C001/C002/C003 失败模式同源. 移入 Known Failures.

**Round 3 退出条件**: 若 0 admit + 0 reserve → `status: productive → saturated` (round 1 admit 2 + round 2 reserve 1, edge 持续收窄). 若有 ≥1 admit, T006 形式层 ≠ library 充分条件 律得到 admit 反例, 升格 lessons.

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

### T002: Alpha 084 OBV-style signed cumulative volume 是否在 csi1000 散户市携带与 F009 pv_corr 不冗余的方向 imbalance 信号 [✗ DISPROVEN batch_086] (T002a OBV b085 + T002b Volume MACD b086 ratio-form 全证伪)

> [!failure]+ Thread 结论 (T002a OBV-20d + T002b Volume MACD ratio-form)
> **Question**: `Sum(sign(close - prev_close) × volume, 20)` 这种 sign-aggregation 是否独立于 F009 pv_corr_times_vol 的 covariance 几何? T002b: Volume MACD histogram dim-less 化是否修正 mono_oos 弱单调?
>
> **Answer T002a**: ✗ DISPROVEN. OBV-20d 在 csi1000 散户市 (a) sign 翻转; (b) Barra 完全吞噬 (alpha_survival=0.17); (c) Q5-only 一桨 mono_oos=-0.3; (d) incr_ic=-0.005 library reducer.
>
> **Answer T002b**: ✗ DISPROVEN (batch_086). Volume MACD ratio-form 复测**反向恶化**: dim-less 化使 mono_oos 从 -0.30 (b085) 退化到 -0.10 (b086) 几乎无 rank-order, alpha_surv=1.585 顶级 Barra 真独立但 incr_ic=-0.023 本批最强负 library-reducer. ratio-norm 引入 cap-denominator 隐藏 vol_20d 嵌入 (P016 风险扩展到 volume_mean denominator), Mean(volume,27) cross-section 注入 size 横截面差异消除 raw rank-order. T002 整 thread DISPROVEN, 关闭.
>
> **Evidence trail**:
> - [[batches/batch_085/candidates/C002|batch_085 C002]] `Sum(Mul(Sign(Sub($close,Ref($close,1))),$volume),20)` IC_oos=-0.027 alpha_surv=0.17 mono_oos=-0.3 → **reject (T002a OBV DISPROVEN)**
> - [[batches/batch_085/candidates/C005|batch_085 C005]] Volume MACD raw alpha_surv=1.39 mono_oos=-0.3 incr_ic=-0.015 → **reserve (P008 软判定区火种)**
> - [[batches/batch_086/candidates/C005|batch_086 C005]] `Div(... MACD ratio-form ...)` alpha_surv=1.585 mono_oos=-0.10 incr_ic=-0.023 → **reject (T002b DISPROVEN, ratio-norm 反向恶化)**
>
> **Lesson upgraded**: 升格候选 lessons "P008 形式层独立 ≠ library 充分条件" + "Volume-mean denominator 等价于 cap-denominator 隐藏 vol_20d 风险扩展".

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

### T005: Paper-vetted but 库内邻接 / blocked 的 12 个因子何时复活 [◉ ACTIVE] (round 2 部分推进 batch_086)

> [!note]+ Thread 当前
> **Question**: 5×5-only tail-sensitivity 子集 (Alpha 022/031/006/187/089/052/002/044/011/026/136/170) + vwap-blocked (Alpha 073/039) + benchmark-blocked (Alpha 181) + borderline-DSL (Alpha 190) 何时纳入测试? 触发条件是什么?
>
> **Round 2 (batch_086) 推进结果**: 三条续探路径全检验 — 4 reject + 1 reserve, 0 admit:
> - **path (a) 5×5 tail-sensitivity 子集 (Alpha 022/031/006)**: 全部 reject. C001/C006 是 Alpha 022 两形式 (EMA-12 vs TsRank-60), C002 Alpha 031 BIAS-12 单窗与 F027 等价, C003 Alpha 006 weighted-price Δ4 sign rank csi1000 daily 信号过弱. **5×5 子集 paper 在 daily 不兑现** (与 3×2 子集 b085 50% 兑现 sharp contrast).
> - **path (b) vwap proxy via $amount/$volume**: C004 reject (sign_flip + ic≈0 + decay=-1.05). Alpha 073 nested decayed Corr 在 daily DSL 不可达, **vwap-blocked permanently** (移入 Known Failures + 路径关闭).
> - **path (c) Volume MACD ratio-form**: T002b DISPROVEN (见 T002).
> - 仅 path (a) C006 P008 escape 形式获得 reserve (alpha_surv=1.21 + mono_oos=-0.70 + decay=1.21 OOS 强于 IS, 但 incr_ic=-0.007 仍微负).
>
> **Evidence trail**:
> - [[batches/batch_085/candidates/C001|batch_085 C001]] Alpha 046 multi-MA → **admit F027** (3×2 round 1)
> - [[batches/batch_085/candidates/C003|batch_085 C003]] Alpha 049 DMI Down → **admit F028** (3×2 round 1)
> - [[batches/batch_086/candidates/C001|batch_086 C001]] Alpha 022 EMA-12 形式 alpha_surv=1.59 incr_ic=-0.016 → **reject (cluster 整族)**
> - [[batches/batch_086/candidates/C002|batch_086 C002]] Alpha 031 BIAS-12 单窗 corr=0.954@F027 → **reject (hard_gate)**
> - [[batches/batch_086/candidates/C003|batch_086 C003]] Alpha 006 sign-rank ic_oos=0.0053<0.008 → **reject (hard_gate, 信号过弱)**
> - [[batches/batch_086/candidates/C004|batch_086 C004]] vwap-proxy rank-spread sign_flip → **reject (hard_gate, vwap-blocked permanently)**
> - [[batches/batch_086/candidates/C006|batch_086 C006]] Alpha 022 TsRank-60 P008 escape mono_oos=-0.70 alpha_surv=1.21 incr_ic=-0.007 → **reserve (P008 软判定区火种)**
>
> **Next probes**: T005 收窄到**P008 escape 单变量优化** (基于 C006 reserve 形式):
> - (a) 字段族替换: $turnover_rate / $amount / $num_trades 替代 $close 减少与 OHLC reversion family cluster (与 b073/b074 学到的 cap-denominator 警告对照, 但 microstructure-only ratio 是 P008 真生效路径)
> - (b) TsRank 窗口 90/120 测试是否进一步 vol-normalize
> - (c) CsRank 包装测 incr_ic 是否转正
> - **放弃 paper 5×5 剩余 9 个** (Alpha 187/089/052/002/044/011/026/136/170): 全部基于 OHLC + price-only cross-section rank 几何, 与本批 C001/C002/C003 失败模式同源 — 移入 Known Failures.

### T006: P008 escape 形式层独立 (alpha_surv > 1.0) 是否结构性脱离 library 充分条件 (incr_ic > 0)? 🆕 [◉ ACTIVE]

> [!note]+ Thread 当前
> **Question**: 本批 alpha_surv > 1.0 三连出现 (C001=1.59 / C005=1.585 / C006=1.21) 但 incr_ic 全负 (-0.016 / -0.023 / -0.007) — 形式层 Barra 真独立 ≠ library 增值. csi1000 daily 库内 sign-flipped reversion family + TsRank-60 family 是否结构性饱和? P008 escape 是否需要 admit 阈值 incr_ic > 0.005 + max_lib_corr < 0.30 双条件?
>
> **Evidence trail**:
> - [[batches/batch_086/candidates/C001|batch_086 C001]] alpha_surv=1.59 max_corr=0.456@F006 incr_ic=-0.016 cluster F006/F007/F008/F009/F027 → reject
> - [[batches/batch_086/candidates/C005|batch_086 C005]] alpha_surv=1.585 max_corr=0.338@F027 incr_ic=-0.023 → reject
> - [[batches/batch_086/candidates/C006|batch_086 C006]] alpha_surv=1.21 max_corr=0.444@F008 incr_ic=-0.007 → reserve (incr_ic 微负但救场弱)
> - 对照 b082 F026 admit (incr_ic 正 + alpha_surv > 1.0 + max_corr 0.481)
> - 对照 b085 F027 admit (alpha_surv=1.13 + max_corr=0.544 高 但 incr_ic 正)
>
> **Next probes**: T006 是 cross-direction 教训候选, 涉及 lessons.md "P008 软判定区 reject vs reserve 边界" 的边界细化. 可能升格到 lessons.md "P008 形式层 ≠ library 充分条件" 律. 待 Phase 5 consolidation 评估.

---

## Known Failures

| Candidate | Expression | Reject Reason |
|---|---|---|
| [[batches/batch_085/candidates/C002\|b085 C002]] | `Sum(Mul(Sign(Sub($close,Ref($close,1))),$volume),20)` | OBV-20d csi1000 sign 翻转 + alpha_surv=0.17 Barra 吞噬 + mono_oos=-0.3 Q5-only 一桨 + incr_ic=-0.005 library reducer |
| [[batches/batch_085/candidates/C004\|b085 C004]] | `Mean(Greater(...,12)` ATR | ATR-12d ≡ vol_20d (exposure=31.4 顶级) + alpha_surv=0.064 + max_corr=0.66@F019 + incr_ic=-0.018: P006 trio 齐 |
| [[batches/batch_085/candidates/C006\|b085 C006]] | `TsRank(Div(Sub($close,Mean($close,24)),Mean($close,24)),60)` | BIAS-24 + TsRank60 单窗 P008 frontier escape 失败 (max_corr=0.42@F009) + incr_ic=-0.019 |
| [[batches/batch_086/candidates/C001\|b086 C001]] | `EMA(Sub(Div(Sub($close,Mean($close,6)),Mean($close,6)),Ref(...,3)),12)` | Alpha 022 EMA-12 二阶 BIAS-6 diff: alpha_surv=1.59 但 incr_ic=-0.016 + cluster F006/F007/F008/F009/F027 整族 -0.44~-0.46 |
| [[batches/batch_086/candidates/C002\|b086 C002]] | `Mul(Sub(Div($close,Mean($close,12)),1),100)` | Alpha 031 BIAS-12 单窗 hard_gate near_duplicate corr=0.954@F027 (与 multi-MA 几何等价) |
| [[batches/batch_086/candidates/C003\|b086 C003]] | `Mul(CsRank(Sign(Sub(Add(Mul($open,0.85),Mul($high,0.15)),Ref(...,4)))),-1)` | Alpha 006 weighted-price Δ4 sign rank: ic_oos=0.0053<0.008 hard_gate (csi1000 daily 信号过弱 + sign-mono mismatch) |
| [[batches/batch_086/candidates/C004\|b086 C004]] | `Sub(TsRank(Div($amount,$volume),60),TsRank(Mean($volume,30),60))` | Alpha 073 vwap-proxy rank-spread: sign_flip + ic≈0 + decay=-1.05 三连 hard_gate. **Alpha 073 nested decayed Corr DSL 不可达 → vwap-blocked permanently** |
| [[batches/batch_086/candidates/C005\|b086 C005]] | `Div(... MACD histogram ..., Mean($volume,27))` | Volume MACD ratio-form (T002b): dim-less 化反向恶化 mono_oos=-0.30→-0.10; alpha_surv=1.585 但 incr_ic=-0.023 本批最强负 |

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

> [!quote]+ 2026-05-03 · [[batches/batch_086/judge|batch_086]]
> **paper-vetted Alpha191 universal-subset round 2 兑现率急剧下滑 0/6 admit + 1/6 reserve · 16% 信号留存** (vs round 1 50%) · admit = 0 / reserve = 1 / reject = 5
>
> - **paper 5×5 tail-sensitivity 子集在 csi1000 daily 系统失效**: 3 候选 (Alpha 022/031/006) 全部 reject (1 reject + 2 hard_gate fail). 与 3×2 子集 batch_085 50% 兑现 sharp contrast. paper 警告"monthly aggregation 抹平 high-frequency dynamics" 在 5×5 子集表现尤强 — 5×5 增加 sort granularity 但保留 monthly aggregation, 在 daily 频率被噪声主导.
> - **alpha_surv > 1.0 三连出现 (n=3 in single batch)**: C001=1.59, C005=1.585, C006=1.21 — 三个 pass 候选**全部** Barra 真独立 (residual_IC > raw_IC). P008 escape 形式层证据本批集中爆发. **但 incr_ic 全部负** (-0.016 / -0.023 / -0.007) — **形式层独立 ≠ library 增值**, 升格元教训候选 (T006 ACTIVE 待 Phase 5).
> - **Volume MACD T002b ratio-form 假设证伪**: dim-less 化反向恶化 mono (-0.30 → -0.10). 原因: Mean(volume,27) 分母 cross-section 注入 size 横截面差异 (P016 cap-denominator 风险扩展到 volume_mean denominator). T002 整 thread DISPROVEN 关闭.
> - **vwap-proxy rank-spread 路径完全失效**: C004 三连 hard_gate (sign_flip + ic≈0 + decay=-1.05). Alpha 073 nested decayed Corr DSL 不可达, **vwap-blocked permanently** 升格.
> - **C006 reserve 火种**: Alpha 022 TsRank-60 + 二阶 BIAS-6 diff 形式. vol_20d_exp=8.80 显著低 (vs C001 19.06 / C005 16.65), 8 年同号负 + decay=1.21 OOS 强于 IS + mono_oos=-0.70 强单调. P008 escape **真正** vol-normalized 但 incr_ic 仅微负 -0.0067 (比 C001 -0.016 / C005 -0.023 显著好), 处 P008 软判定区 reserve.
> - **MT budget**: cumulative 474 → 480 · direction 6 → 12 (翻倍) · validation_exposure 85 → 91 · bucket `high` (search_adjusted=medium)
>
> **Operations**: `status: productive` 保持 (round 1 admit 2 + round 2 reserve 1, ROI 下降但 edge 未死) · priority `high` 保持 · T002 整 thread DISPROVEN (T002a OBV b085 + T002b Volume MACD ratio-form b086) · T005 round 2 部分推进 (5×5 子集证伪 + vwap proxy 证伪 + Volume MACD ratio 证伪 + P008 escape reserve) · **T006 新建** (alpha_surv > 1.0 三连 + incr_ic 全负 → 形式层 ≠ library 充分条件 律, 升格 lessons 候选)
>
> **下一步**: T005 收窄到 P008 escape 单变量优化 (基于 C006 reserve 形式) — (1) 字段族替换 $turnover_rate / $amount / $num_trades 替代 $close 减少 OHLC reversion family cluster; (2) TsRank 窗口 90/120 测试; (3) CsRank 包装测 incr_ic 是否转正. **放弃** paper 5×5 剩余 9 个 (Alpha 187/089/052/002/044/011/026/136/170, 同源失败模式). 若 round 3 仍 0 admit + 0 reserve, 升格 `status: productive → saturated`.

> [!quote]- 2026-05-02 · [[batches/batch_085/judge|batch_085]]
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
