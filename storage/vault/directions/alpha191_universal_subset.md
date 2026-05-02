---
direction_tag: alpha191_universal_subset
status: exploring
priority: high
rounds: 0
admits: 0
last_batch: pending
last_admits: []
last_goal: null
last_activity: null
created_batch: batch_080
members: []
merged_into: null
---
# alpha191_universal_subset

> [!abstract]+ 方向概要
> - **状态**　🔵 `exploring` · priority `high` · rounds = 0 · admits = 0
> - **最近**　— · 来源 [[../papers/arxiv_2601_06499v1|arXiv 2601.06499v1 Cross-Market Alpha (Du-Walter-Ulrich 2026)]] · 待 batch_080 首批
> - **一句话**　从 GTJA Alpha191 库中筛取经过美股 DS-LASSO + 151 fundamental control 跨市场存活的 17 因子白名单，**优先实装库内尚未同形覆盖的 4-5 个 mechanism family**：multi-MA mean reversion (Alpha 046)、signed-volume accumulation/OBV (Alpha 084)、DMI directional pressure (Alpha 049)、跨日 true range/ATR (Alpha 161)、volume momentum/MACD (Alpha 155)。

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

### T001: Alpha 046 multi-window MA composite ratio 是否在 csi1000 上独立于现有 mean-reversion 家族提供新 alpha [◉ ACTIVE]

> [!note]+ Thread 当前
> **Question**: 4 个 MA 窗口 (3/6/12/24) 算术平均除以 spot price 的复合 mean-reversion 比率, 在 csi1000 daily 上是否携带与库内 F011 williams_r_variant / F022 close_position_amount_accel / F004 std_vol_20 (Grade B 73.1) 不冗余的信号? 多窗 vote 是否减少单窗 phase 噪声?
>
> **Evidence trail**:
> - (待 batch_080 C001 baseline) `Div(Add(Add(Add(Mean($close,3),Mean($close,6)),Mean($close,12)),Mean($close,24)),Mul($close,4))`
>
> **Next probes**: 若 baseline admit, round 2 探 4 窗替换为 (5/10/20/60) 长窗组合; 若 collapse 到单窗 mean-reversion, 改测 Alpha 071 (24d % dev from mean) 单窗对照, 验证多窗 vote 是否真的提供增量。

### T002: Alpha 084 OBV-style signed cumulative volume 是否在 csi1000 散户市携带与 F009 pv_corr 不冗余的方向 imbalance 信号 [◉ ACTIVE]

> [!note]+ Thread 当前
> **Question**: `Sum(sign(close - prev_close) × volume, 20)` 这种 sign-aggregation 是否独立于 F009 pv_corr_times_vol (Grade A 79.9) 的 covariance 几何? OBV 累积"买卖方向不平衡", F009 度量"价量同向一致性强度"——机制是否真不同?
>
> **Evidence trail**:
> - (待 batch_080 C002 baseline) `Sum(Mul(Sign(Sub($close,Ref($close,1))),$volume),20)`
> - (待 batch_080 C005 第二线) `Sub(Sub(EMA($volume,13),EMA($volume,27)),EMA(Sub(EMA($volume,13),EMA($volume,27)),10))` Volume MACD
>
> **Next probes**: 若 OBV admit, round 2 探短窗 (5d/10d) + 长窗 (60d/120d); 若 collapse @F009, 改测 OBV × turnover_rate composite; 若 sign-flip in csi1000 (散户主导短期 noise), 改测 abs(OBV) magnitude-only proxy。

### T003: Alpha 049 DMI directional pressure 在 csi1000 小盘震荡市是否需要 sign 翻转 [◉ ACTIVE]

> [!note]+ Thread 当前
> **Question**: Welles Wilder DMI 的 -DI/(+DI + -DI) 在大盘趋势市 (paper SPX 测) 显著为正, csi1000 小盘震荡为主, sign 是否翻转? IC sign 不稳时改测 abs(DMI) 是否仍 carry alpha (作为 momentum-magnitude proxy)。
>
> **Evidence trail**:
> - (待 batch_080 C003 baseline) Alpha 049 DMI Down ratio 直译
>
> **Next probes**: 若 sign-stable PASS, 验证机制独立于 range_structure / asymmetric_momentum; 若 sign-flip 但 |DMI| 显著, 改测 abs(directional_pressure_diff) 作 momentum-magnitude proxy; 若全 reject, 升格 "DMI 在 csi1000 散户市 alpha 不存在" 入 lessons。

### T004: Alpha 161 12d ATR 跨日 jump 维度是否独立于库内单日 range 信号 [◉ ACTIVE]

> [!note]+ Thread 当前
> **Question**: True Range = max(单日 H-L, |prev_close - H|, |prev_close - L|) 包含跨日 gap jump, 而库内 F021 upper_shadow_disp_range_compress / F022 close_position_amount_accel 都是单日 (H-L) 几何。ATR 的跨日 jump 维度是否提供新信号? 还是 collapse 到 std_returns_20 (F001 score=65.5)?
>
> **Evidence trail**:
> - (待 batch_080 C004 baseline) `Mean(Max(Max(Sub($high,$low),Abs(Sub(Ref($close,1),$high))),Abs(Sub(Ref($close,1),$low))),12)`
>
> **Next probes**: 若 admit + max_corr@F001 < 0.7, 验证跨日 jump 几何独立; 若 collapse @F001, 改测 ATR-of-overnight-only (剔除单日 H-L 项), 隔离跨日 jump 单独效应; 若全 collapse, 升格 "ATR ≡ vol_20d basis" 入 lessons (P018 律的 ATR 扩展)。

### T005: Paper-vetted but 库内邻接 / blocked 的 12 个因子何时复活 [◉ ACTIVE]

> [!note]+ Thread 当前
> **Question**: 5×5-only tail-sensitivity 子集 (Alpha 022/031/006/187/089/052/002/044/011/026/136/170) + vwap-blocked (Alpha 073/039) + benchmark-blocked (Alpha 181) + borderline-DSL (Alpha 190) 何时纳入测试? 触发条件是什么?
>
> **Evidence trail**:
> - (paper note 主结论) 仅 round 2+ 触发, round 1 不开
>
> **Next probes**: Round 2 触发条件 = (round 1 ≥2 admit + 至少 1 个 mechanism family alpha_surv 显著独立 from existing 库) → 开 5×5 tail-sensitivity 子集; vwap proxy (`$amount/$volume`) 触发条件 = round 1 至少 1 admit 证明 paper-vetted prior 在 csi1000 有效 → 试 Alpha 073 nested PV corr 的 vwap proxy 形式; benchmark proxy (universe-mean) 触发条件 = Phase 5 architecture 升级支持 cross-sectional benchmark filter。

---

## Known Failures

(空——本方向尚未提交任何候选)

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
- [[../lessons#Structural Constraints]]
- [[../papers/arxiv_2601_06499v1]] — 来源 paper note (含 17 因子完整白名单 + DSL 转写 + 隐藏假设)

---

## Narrative Log

(空——本方向尚未提交任何 batch)
