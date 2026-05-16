---
direction_tag: fundamental_ttm_cross_family
status: dead
priority: low
rounds: 2
admits: 0
last_batch: batch_103
last_admits: []
last_goal: 'Round 103 / fundamental_ttm_cross_family 首批. library_gap/020 finding +
  cockpit zero-admit streak 4 batches 提议刻意切换 geometry: 22 TTM 字段 15 untouched + 条件算子
  × fundamental 100% 未测. 6 候选三轴: (a) 2 atomic baseline CsRank ROE / 毛利率 (baseline-first
  律强制, 抢占 untouched 字段名额), (b) 3 F029 framework 字段维度扩展 — 把 close-position 换成 ROE /
  毛利率 / debt_to_asset 做 binarize+event-rate aggregation, (c) 1 PIT × $num_trades 非-amount-aggregate
  桥接 (绕 b068 vol_20d denominator 吸收路径). 刻意避开: TTM × TTM Sub/Mul/Div (b068 dead + 数据契约
  risk), Delta/Ref rate form (fundamental_momentum dead), Python residualize (python_ttm_residual_quality
  6/6 sign-flip dead), Mean(amount/turnover, N) denominator (b068 vol_20d_exp 23-31%
  吸收律). 4 律自检 P030/P033 全候选 inline; coverage hard_gate ≥0.80 + IS/OOS sign consistency
  严查 (基本面 PIT delay risk).'
last_activity: '2026-05-16T08:39:14Z'
created_batch: batch_103
members: []
retired_members: []
merged_into: null
created_from: library_gap/020 + cockpit_round_103_zero_admit_streak_geometry_switch
---
# fundamental_ttm_cross_family

> [!abstract]+ 方向概要
> - **状态**　🔴 `dead` · priority `low` · rounds = 1 · admits = 0 (first-batch 0 admit)
> - **最近**　[[batches/batch_103/judge|batch_103]] · 2026-05-16 · admit=0 / reserve=0 / reject=6
> - **一句话**　22 TTM 字段三 geometry (atomic baseline / F029 binarize / PIT × $num_trades) 平行独立证伪 — 第 8 条独立路径强化 lessons "csi1000 daily fundamental 真饱和" 顶层 macro lesson；首批 6/6 reject 即关方向。

---

## Hypothesis

> [!warning]+ ⚠️ Hypothesis 已证伪（batch_103，6/6 reject；first-batch dead）
> **原假设**　22 TTM 财务字段（15 个 baseline 完全 untouched + 条件算子 × fundamental 100% 未测）携带与 OHLCV 几何独立的 cross-section alpha；通过 atomic baseline + F029 framework + PIT × $num_trades 三 geometry 抢占独立 admit。
>
> **证伪证据**　三 thread × 三 geometry **平行独立失败模式各异**：
> - **T001 atomic baseline (C001/C002)**: regime sign-flip — fundamental level cross-section 在 train (2015-2021) / validation (2022-2023) 完全反号；hard_gate sign_flip + ic_oos < 0.008 + mono_flip ±1.0
> - **T002 F029-framework binarize (C003/C004/C005)**: cross-section degenerate quintiles — slow-moving TTM 字段在 20d windowed binarize 后取值集合极小, 5-quintile 分桶 Q1/Q5 大量 NaN, IC 计算无效
> - **T003 PIT × $num_trades bridge (C006)**: hard_gate 全过但 hypothesis 方向反 + 与 F012 amihud_illiq corr=-0.614 实质同源 + incr_ic=-0.003 库 reducer
>
> **元教训（待 Phase 5 升格）**
> 1. **F029 framework 字段维度律收紧** — `Mean(threshold-op($X, c), 20)` 仅适用于 daily-resolution 充分变动字段; TTM (季度更新) / quarterly delta 字段 default-skip 该 framework. Phase 1 generator 可加自检: 若 binarize 内层 atom ∈ TTM 字段集 → reject `f029_framework_field_resolution_mismatch`
> 2. **fundamental atomic CsRank baseline default-skip** — 第 2-3 类 atom 全 regime sign-flip (b022 PE/PB/PS rate + b068 quality/amount ratio + b103 atomic level), 升格 lessons "csi1000 daily fundamental 真饱和" 第 8 条独立证据
> 3. **$num_trades 不是 vol_20d 隐藏路径的安全替代品** — 与 amihud_illiq 同源, 与 F012 cluster 同源 (b072 institutional_flow_proxy 已局部证伪, 本批从 cross-family bridge 视角再次证伪)
> 4. **csi1000 daily fundamental 真饱和顶层 macro lesson 再次强化** — 本批构成第 8 条独立证据路径 (前 7: b068 ratio / b069-070 valuation rank / b071 Python residualize / b072 institutional flow / b075 cov microstructure × valuation 长窗 / b079 TsRank-Corr 双重包裹 / b086 alpha191 paper transfer)

---

## Threads

### T001: Quality TTM 字段 baseline cross-section alpha [✗ DISPROVEN batch_103]

> [!failure]+ Thread 结论
> **Question**: 单 atom `CsRank($return_on_equity_ttm)` / `CsRank($gross_profit_margin_ttm)` 在 csi1000 cross-section 是否携带 forward IC，且不被 vol_20d basis 吸收？
>
> **Answer**: **regime sign-flip 证伪**。fundamental level cross-section rank 在 train (2015-2021) 与 validation (2022-2023) **符号完全相反**, IC 量级在 noise floor (0.006-0.008) 附近;  baseline 形式直接证伪 → cross-section fundamental quality LEVEL 在 csi1000 daily 上不携带 regime-stable alpha。
>
> **Evidence trail**:
> - [[batches/batch_103/candidates/C001|batch_103 C001]] `CsRank($return_on_equity_ttm)` → train_ic +0.0065, val_ic -0.0063, mono_is +1.00 → mono_oos -1.00, ic_oos -0.0063 below noise → **reject (hard_gate sign_flip + ic_oos_too_low + oos_decay + mono_flip 四重)**
> - [[batches/batch_103/candidates/C002|batch_103 C002]] `CsRank($gross_profit_margin_ttm)` → train_ic +0.0034, val_ic -0.0079, ic_is 几乎平坦, decay -2.355 catastrophic → **reject (hard_gate sign_flip + ic_oos_too_low + oos_decay)**
>
> **机制**: TTM quality level 在 2022-2023 利率上行 + 中小盘价值回归 regime 反转 — 高 ROE / 高毛利公司因估值贵在该段反向 underperform.

### T002: Conditional truncation × fundamental field event-rate [✗ DISPROVEN batch_103]

> [!failure]+ Thread 结论
> **Question**: F029 framework (`Mean(threshold-op($field, threshold), 20)`) 在 fundamental TTM 字段 (ROE / 毛利率 / 资产负债率) 上是否复制 F029 admit 模式，还是 fundamental binarize 像 gap-rate 那样 ≡ vol_20d basis？
>
> **Answer**: **第三种 failure mode** — 既不是 admit, 也不是 vol_20d 吸收, 而是 **cross-section degenerate quintiles** (新失败律!). slow-moving TTM 字段在 20d windowed binarize 后取值集合极小, 5-quintile 切桶产生大量 ties → Q1/Q5 NaN, IC 计算无效.
>
> **Evidence trail**:
> - [[batches/batch_103/candidates/C003|batch_103 C003]] `Mean(Gt($return_on_equity_ttm, 0.10), 20)` → ic_is/ic_oos = NaN, quintile_is 仅 Q3 有值, hard_gate vacuously pass 但实质 NaN → **reject**
> - [[batches/batch_103/candidates/C004|batch_103 C004]] `Mean(Lt($debt_to_asset_ratio_ttm, 0.45), 20)` → train_ic +0.0257, val_ic NaN, quintile_is 3 桶 (Q1/Q5 NaN), mono_is +0.50 forced from 3 桶 → **reject (hard_gate sign_flip val_NaN)**
> - [[batches/batch_103/candidates/C005|batch_103 C005]] `Mean(Gt($gross_profit_margin_ttm, 0.30), 20)` → ic_is -0.022, ic_oos NaN, incr_ic = **-0.0478** 严重 library reducer, quintile Q2/Q3/Q4 only → **reject (实质失败 + library reducer)**
>
> **机制 + 升格元教训**: F029 7-D 律字段维度新约束**升格** — `Mean(threshold-op($X, c), 20)` 仅适用于 daily-resolution 充分变动字段, TTM (季度更新) 字段在 20d windowed binarize 后产生 cross-section degeneracy. F029 7-D 律字段维度边界**严格收紧至 price-derived only**.

### T003: PIT × non-vol microstructure 桥接 [✗ DISPROVEN batch_103]

> [!failure]+ Thread 结论
> **Question**: `Mul(CsRank(TTM_quality), CsRank($num_trades))` 用 $num_trades 替代 Mean($amount/turnover, N) 是否绕开 vol_20d 吸收路径？$num_trades 是 corr-safe + non-amount-aggregate 字段，理论上不嵌入 daily vol basis。
>
> **Answer**: **hypothesis 方向反 + 实质 amihud_illiq 同源**。C006 通过 hard_gate (mono perfect -1.00/-1.00, ls_t=-3.94, sign_consistency=1.0 9 年同号) 但: (a) 信号方向与 hypothesis 相反 (expected positive carry, empirical strong negative mean-reversion), (b) max_lib_corr = 0.614 @ F012 (amihud_illiq), 机制实质同源 — high num_trades = high activity = low Amihud illiq, (c) incremental_ic = **-0.003** 库 reducer, (d) CP04 poor (style_r² 0.546, vol_20d 9.46, dom=vol_20d, crowding=high).
>
> **Evidence trail**:
> - [[batches/batch_103/candidates/C006|batch_103 C006]] `Mul(CsRank($return_on_equity_ttm), CsRank($num_trades))` → ic_oos=-0.031, ls_t_oos=-3.94, mono_oos=-1.00, alpha_surv=0.45, **max_corr=0.614@F012, incr_ic=-0.003**, style_r²=0.55 → **reject (CP05 high + library reducer + CP04 poor + hypothesis 方向反)**
>
> **机制 + 升格元教训**: $num_trades 在 cross-section composite 中扮演 amihud-illiq 同源信号, 不构成与 OHLCV/Amihud 几何独立的 microstructure axis. **TTM × non-amount-aggregate microstructure bridge 失效** — $num_trades 不是 vol_20d 隐藏路径的安全替代品.

---

## Known Failures

| Candidate | Expression | Reject Reason |
|---|---|---|
| [[batches/batch_103/candidates/C001\|C001]] | `CsRank($return_on_equity_ttm)` | hard_gate: sign_flip ±0.006 + ic_oos_too_low + mono_flip ±1.00 |
| [[batches/batch_103/candidates/C002\|C002]] | `CsRank($gross_profit_margin_ttm)` | hard_gate: sign_flip +0.003 → -0.008 + ic_oos_too_low + oos_decay -2.355 |
| [[batches/batch_103/candidates/C003\|C003]] | `Mean(Gt($return_on_equity_ttm, 0.10), 20)` | F029-on-TTM degeneracy: ic_is/ic_oos NaN, Q1/Q5 NaN |
| [[batches/batch_103/candidates/C004\|C004]] | `Mean(Lt($debt_to_asset_ratio_ttm, 0.45), 20)` | hard_gate sign_flip val NaN; F029-on-TTM degeneracy (2nd) |
| [[batches/batch_103/candidates/C005\|C005]] | `Mean(Gt($gross_profit_margin_ttm, 0.30), 20)` | F029-on-TTM degeneracy (3rd) + incr_ic = -0.048 severe library reducer |
| [[batches/batch_103/candidates/C006\|C006]] | `Mul(CsRank($return_on_equity_ttm), CsRank($num_trades))` | CP05 high (max_corr=0.614@F012) + incr_ic = -0.003 library reducer + CP04 poor (vol_20d 9.46) + hypothesis sign 反 |

---

## Related

- ⚫ [[fundamental_quality_carry]] `archived` — TTM-quality / daily-aggregate-liquidity ratio dead, 元教训已升格 lessons
- 🔴 [[fundamental_momentum]] `dead` — PE/PB/PS rate form dead
- 🔴 [[python_ttm_residual_quality]] `dead` — Python OLS residualize 6/6 OOS sign-flip
- 🟡 [[pit_valuation_pure]] `saturated` — PB/dividend yield rank composite saturated
- 🟡 [[conditional_operator_truncation]] `saturated` — F029 7-D framework, **本方向闭合其字段维度 = price-derived only**
- 🟡 [[value_liquidity_interaction]] `saturated` — F002 admit 路径
- 🟡 [[institutional_flow_proxy]] `probing` — $num_trades 信号探索, **本方向交叉证实 $num_trades ≡ amihud_illiq 同源**
- [[lessons#Forbidden Patterns]] TTM-quality default-skip 律 + rate-form default-skip
- [[lessons#Path Selection]] csi1000 daily fundamental 真饱和顶层 macro lesson (**本批是第 8 条独立证据路径**)

---

## Narrative Log

> [!quote]+ 2026-05-16 · [[batches/batch_103/judge|batch_103]]
> **First-batch dead — 三 geometry 平行独立证伪** · admit=0 / reserve=0 / reject=6
>
> - T001 (C001/C002): atomic CsRank baseline regime sign-flip
> - T002 (C003/C004/C005): F029-framework × TTM 字段 → cross-section degenerate quintiles (新失败律, 三次独立复现)
> - T003 (C006): PIT × $num_trades bridge 通过 hard_gate 但 hypothesis 方向反 + 与 F012 amihud_illiq 同源 + library reducer (incr_ic=-0.003)
> - MT budget　cumulative 576 → **582** · direction 0 → **6** · bucket `medium`
>
> **Calibration trigger 自检**: 0/4 触发 (无 over-rejection flag — C006 max_corr=0.614 + incr_ic 负 → 非错杀, 是真 library-redundant; 无 reserve 候选满足库空间独立; 无悖论复现)
>
> **下批建议**:
> - 不再追加本方向 batch — 三 thread 全 DISPROVEN 闭合
> - 元教训等待 Phase 5 consolidate 升格 lessons
> - 与 fundamental_quality_carry / fundamental_momentum / python_ttm_residual_quality 三方向同型 first-batch 0-admit dead → "fundamental TTM csi1000 daily cross-section 真饱和" macro lesson 第 8 条独立证据
>
> **Operations**　`status: exploring → dead` (LLM 翻 status — 三 thread DISPROVEN, first-batch zero admit, hypothesis 元教训 4 条已写入 warning callout)
