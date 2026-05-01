---
direction_tag: trend_residual_geometry
status: dead
priority: medium
rounds: 2
admits: 0
last_batch: batch_065
last_admits: []
last_goal: 'T001/T002/T003 baseline — operator-family 0-admit 空缺补位首批：Slope (C001/C006)
  / Resi (C002/C003) / Rsquare (C004/C005) 三 rolling-regression 算子在 csi1000 daily-bar
  cross-section 上是否携带独立于 23 admit Mean/Std-base 因子的 alpha。

  zero_admit_streak=5 saturation regime 下放弃 productive direction 的同 RHS family 重复
  (overnight/ohlc/microstructure 已 atp/close-position/sign atom 几何穷尽)，

  切换至 library_gap/002 (HIGH) + library_gap/005 (MEDIUM) 双 finding 推荐的 operator-family
  novelty axis。

  设计硬约束：(1) LHS atom 必 vol_20d 几何正交 — Slope/Ref / Resi / Rsquare 都是 first-order trend
  或 detrend 残差，不是 |return|/range/amount 的二阶聚合；

  (2) RHS 严避已知 dead endpoints (amount_20/turnover_5/overnight_5/body_ratio_20/price_vol_20/Amihud_20/H_L_60/circ_mktcap_60)
  与饱和 anchor cluster (F017 turnover-family / F021 H/L_60 / F002 amount-denominator)；

  (3) RHS 选 Mean(PE/PB/PS,60) raw fundamental level (区别于 fundamental_momentum dead
  的 rate/Delta) 或 standalone (raw Slope/Resi)；

  (4) 不嵌套 CsRank 内 custom ops (TsMin/TsMax/Tanh/HHI/RealizedVol/AmihudIlliq) — 使用
  qlib 内置 Slope/Resi/Rsquare 直接；

  (5) 6 候选每个对应不同 LHS atom (Slope-close / Resi-close / Rsquare-close / Slope-close-norm
  / Resi-turnover / Rsquare-amount), 不重叠.

  目标 ≥1 admit 兑现 max_corr@library<0.50 + alpha_surv≥0.30 + |ls_t|>2 + |incr_ic|≥0.015.'
last_activity: '2026-05-01T12:45:10Z'
created_batch: batch_065
members: []
retired_members: []
merged_into: null
---
# trend_residual_geometry

> [!abstract]+ 方向概要
> - **状态**　🔵 `exploring` · priority `medium` · rounds = 0 · admits = 0
> - **最近**　— · 新建于 [[batches/batch_065/judge|batch_065]]
> - **一句话**　Slope / Resi / Rsquare 三个 0-admit 时序回归算子家族首批探针——time-series detrending residual 与 cross-sectional Barra residual (F004/F005) 几何独立, 与 Mean/Std-base aggregation 不同。

---

## Hypothesis

> [!note]+ Hypothesis · operator-family 完全空缺补位
> 库内 23 admit 算子盘点：`Mean`(15 admit)/`Std`(4 admit)/`Sub`/`Mul`/`Div`/`Abs`/`Ref`/`Delta`/`Sign`/`CsRank` 主导。**`Slope` / `Resi` / `Rsquare` 三算子家族 0 admit**（[[_consolidation/findings/library_gap/002]] HIGH severity + [[_consolidation/findings/library_gap/005]] residual paradigm 单态空白）。
>
> **三条经济学线索**
> 1. **Time-series detrend residual ≠ cross-sectional Barra residual**：`Resi($close, 60)` 减去 60d 个股自身线性趋势, 残差 = 个股**短期 idiosyncratic deviation**（异于 F004/F005 减市场系统性风险）。捕捉个股相对自身趋势的偏离，而非相对市场。
> 2. **Trend slope as scale-free signal**：`Slope($close, N) / Ref($close, N)` = 日均收益率（% per day）规范化版本，是 cross-section 上 first-order 趋势强度信号。csi1000 trend = reversal（[[trend_quality_gated]] 已证 Mean(returns) gate 路径），但 Slope/Ref 未直接试过。
> 3. **R² as trend quality**：`Rsquare($close, 60)` ∈ [0,1] 测量 60d 趋势线性可预测度。orderly trend (high R²) vs ranging market (low R²) 是与库内 vol/range/Mean 信号正交的 axis。

> [!warning]+ ⚠️ 已知陷阱与 prior 失败规避
> 1. **csi1000 momentum = reversal**（[[trend_quality_gated]] / [[asymmetric_momentum]] / [[return_momentum_acceleration]] dead 三方向）：本方向 Slope/Resi 候选 IC 可能负向；负 IC 仍可作 short-side 因子但 A 股约束强多头 → 设计上必须验证 Q1 spread 而非依赖 Q5 short。
> 2. **F300 rate/delta/ratio default-skip 跨 5+ 方向律**：`Slope(X)/Ref(X)` 是 first-order trend 而非 rate-of-change，但与 rate 几何邻近——必须 verify alpha_surv 与 incr_ic 双正。
> 3. **F002 anchor cluster (amount/turnover 分母)**：本方向 RHS 必须**完全脱离 amount/turnover 单字段时序聚合**——选 fundamental level (`Mean($pe_ratio,60)` / `Mean($pb_ratio,60)` / `Mean($ps_ratio,60)`) 或 OHLC ratio (`Mean(H/L,60)`) 作 RHS。
> 4. **Higher-moment raw fundamental 死区** ([F003/F201], 5 次 retro-confirm)：禁止 `Std($pe_ratio,N)` / `Std($pb_ratio,N)` 作 LHS——只用 raw level Mean。
> 5. **F022 close-position-in-range cluster**：Resi($close,N) 是时序 detrended close, 与 cross-sectional (C-L)/(H-L) 几何完全不同（一为时序自比, 一为日内 cross-section 范围位置）, 预期 corr<0.30。

---

## Current Focus

首批 baseline T001/T002/T003 — 三 thread 各占 ≥1 候选探针 operator-family 空缺：
- T001: `Slope/Ref` scale-free trend slope as standalone factor + rank-diff 包装
- T002: `Resi` time-series detrend residual atom × fundamental level RHS
- T003: `Rsquare` trend quality (R²) atom × non-dead RHS

不期待全 admit；目标 ≥1 admit 兑现 max_corr<0.50 + alpha_surv≥0.30 + |ls_t|>2 + |incr_ic|≥0.015。如全 reject, 至少建立 4-5 个 reserve 测 `Slope` vs `Resi` vs `Rsquare` 中哪个 atom 最有信号潜力, 缩窄 thread 2 阶段范围。

---

## Threads

### T001 · Slope / scale-free trend slope LHS [✗ DISPROVEN batch_065]

> [!failure]+ Thread 结论
> **Question**: `Slope($close, N) / Ref($close, N)` 作为 cross-section first-order 趋势信号在 csi1000 是否携带独立 alpha（含 reversal 方向）？raw standalone vs rank-diff 包装哪条形式更稳？短窗 vs 长窗 horizon 灵敏度？
>
> **Evidence trail**:
> - [[batches/batch_065/candidates/C001|batch_065 C001]] (短窗 standalone) ic_oos=-0.034 ls_t=-3.29 通过 hard gate, 但 CP04 catastrophic (style_r²=0.78, dom=str_1m beta=8.56, alpha_surv=0.24<0.40) + CP05 incremental_ic=-0.017 negative → **reject**
> - [[batches/batch_065/candidates/C006|batch_065 C006]] (长窗 rank-diff × PB60) sign_flip (train -0.006 vs val +0.008) + oos_decay=-1.297, 多年方向反转 (2015 -0.038 → 2023 +0.015) → **reject (hard_gate)**
>
> **结论**：Slope-on-close 双窗双结构皆失败。短窗信号本质 = str_1m 重表达，长窗信号 vol_20d 主导且 regime-sensitive。`Slope($close, N)` operator-family 在 csi1000 cross-section 无独立 alpha 空间。下批不再扩此 family。可考虑 Slope-on-other-fields（$turnover_rate, $amount）—— 但 RHS 必避 F002/F017 anchor。

### T002 · Resi time-series detrend residual atom [✗ DISPROVEN batch_065]

> [!failure]+ Thread 结论
> **Question**: `Resi($close, N)` time-series 60d 线性回归残差是否构成与 F004/F005 (cross-sectional Barra residual) 几何独立的 axis？fundamental level RHS（PE/PB level）能否避开 F002 anchor cluster？
>
> **Evidence trail**:
> - [[batches/batch_065/candidates/C002|batch_065 C002]] (Resi(60)+PB60 rank-diff) sign_flip (train -0.0227 vs val +0.0010) + ic_oos<0.008 + decay=-0.045 → **reject (hard_gate)**
> - [[batches/batch_065/candidates/C003|batch_065 C003]] (Resi(20)+PE60 rank-diff) 通过 hard gate 但 weak (ls_t=-1.05, ic_oos=-0.0086) + CP05 incremental_ic=-0.018 negative + ic_by_year 逐年衰减 (2015 -0.022 → 2023 -0.0044) → **reject**
>
> **结论**：Resi-on-close 双窗双 RHS 配置全失败。time-series Resi atom 在 csi1000 cross-section 与库内 OHLC range 几何因子（F006, F008, F009）信号空间共同覆盖，独立性为虚 (max_lib_corr 低但 incremental_ic 负)。`Resi($close, N)` × fundamental level RHS 路径在当前 23 admit 库覆盖度下无 admit 空间。lessons 候选升格："time-series Resi-on-close 在 csi1000 cross-section 死区，atom 几何独立但库空间增量为负"。

### T003 · Rsquare trend quality (R²) atom [✗ DISPROVEN batch_065]（部分 ANSWERED）

> [!note]+ Thread 当前
> **Question**: `Rsquare($close, 60)` orderly-trend vs ranging-market 区分度是否与库内 vol/range/Mean 信号正交？是否捕捉小盘股 "机构吸筹有序 trend" vs "散户随机震荡" 的微观结构差异？standalone vs rank-diff 包装哪个稳？
>
> **Evidence trail**:
> - [[batches/batch_065/candidates/C004|batch_065 C004]] (standalone Rsquare 60d) sign_flip (train +0.003 vs val -0.001) + ic_oos<0.008 + mono=1.0/0.8 完美但 spread≈0 → **reject (hard_gate)**
> - [[batches/batch_065/candidates/C005|batch_065 C005]] (Rsquare(60)/PS60 rank-diff) 通过 hard gate, ic_oos=+0.0155 mono_oos=0.9 ls_t=1.13 + alpha_surv=0.19 + incr_ic=+0.002 + ic_by_year 2017+ 信号增强 (2017 +0.024, 2022 +0.021) → **reserve**
>
> **结论（部分）**：Rsquare standalone 信号几乎为 0（rank-order 完美但 cardinal spread 可忽略），但 rank-diff 包装 (C005) 把信号放大到 OOS IC=+0.0155 边缘 admit 区。**T003 部分 ANSWERED**：standalone DISPROVEN, rank-diff × PS level 路径仍 ACTIVE 但 ls_t weak (1.13).
>
> **Next probes**: 下批以 C005 为 anchor 测 Rsquare(60d) × {PE60d, PB60d, raw norm} 三 RHS 中哪条最稳；同时窗口扫描 Rsquare(120d) 看长窗是否更平滑。若仍全 reject 且 ls_t < 1.5 → T003 整体 DISPROVEN，方向 status: exploring → dead。

### T004 · Rsquare-rank-diff RHS 选型 [✗ DISPROVEN batch_065] 🆕

> [!note]+ Thread 当前
> **Question**: 承接 T003 reserve C005 — Rsquare(60d) rank-diff 包装下，PE/PB/PS 三种 fundamental level RHS（60d Mean）哪个最稳？rank-diff 包装是否可推广到 Rsquare on $turnover_rate / $volume 跨字段？
>
> **Evidence trail**:
> - 待下批兑现
>
> **Next probes**: 下批 6 候选可设计 (a) Rsquare(60)/PE60 rank-diff (b) Rsquare(60)/PB60 rank-diff (c) Rsquare(120)/PS60 长窗 (d) Rsquare on $turnover_rate × PS60 (e) Rsquare-rank no-RHS standalone-rank (f) Rsquare(60) × Slope(60) 自交。目标 ≥1 admit，否则 thread DISPROVEN + 方向 dead。

---

## Known Failures

- C001 `Div(Slope($close, 20), Ref($close, 20))` — 通过 hard gate 但 CP04 catastrophic (str_1m beta=8.56, alpha_surv=0.24<0.40) + CP05 incremental_ic=-0.017 negative
- C002 `Sub(CsRank(Resi($close, 60)), CsRank(Mean($pb_ratio, 60)))` — hard_gate sign_flip (train -0.0227 → val +0.0010) + ic_oos<0.008 + decay=-0.045
- C003 `Sub(CsRank(Resi($close, 20)), CsRank(Mean($pe_ratio, 60)))` — weak stat (ls_t=-1.05) + incremental_ic=-0.018 negative + 逐年衰减
- C004 `Rsquare($close, 60)` — hard_gate sign_flip (train +0.003 → val -0.001) + ic_oos<0.008，rank-order 完美但 cardinal spread 几乎为 0
- C006 `Sub(CsRank(Div(Slope($close, 60), Ref($close, 60))), CsRank(Mean($pb_ratio, 60)))` — hard_gate sign_flip + decay=-1.297，多年方向反转 (2015 -0.038 → 2023 +0.015 regime drift)

---

## Related

- 🔴 [[trend_quality_gated]] `dead` — 测过 Mean(returns,N) × amount/vol gate, 全 reject; 本方向用 Slope/Resi/Rsquare 算子 (0 admit family) 区别于 Mean(returns) gate
- 🔴 [[return_momentum_acceleration]] `dead` — 单层 momentum 导数 (Delta) 不存活, 本方向用 Slope (rolling regression slope) 替代 raw Delta
- 🔴 [[asymmetric_momentum]] `dead` — 上涨/下跌不对称无 gate; 本方向用 R² 测 trend quality 不分方向
- 🟢 [[microstructure_illiquidity]] `productive` — F015/F016 Amihud rank-diff anchor; 本方向 RHS 避开 Amihud 字段
- 🟢 [[overnight_intraday_split]] `productive` — F017 anchor cluster (turnover-family RHS) 必避; 本方向 RHS 用 fundamental level
- 🟡 [[value_liquidity_interaction]] `saturated` — F002 anchor cluster (amount/turnover 分母); 本方向 RHS 用 raw fundamental level (Mean(PE,N) / Mean(PB,N) / Mean(PS,N)) 不带 amount/turnover 分母
- 🟡 [[barra_residual_alpha]] `saturated` — F004/F005 cross-sectional Barra residual; 本方向 Resi 是 time-series 自身回归残差, 几何不同
- 📖 [[_consolidation/findings/library_gap/002]] HIGH — Skew/Kurt/Slope/Resi operator family 0 admit
- 📖 [[_consolidation/findings/library_gap/005]] MEDIUM — residual paradigm 单态空白 (cross-sectional Barra only)

---

## Narrative Log

### 2026-05-01 [[batches/batch_065/judge|batch_065]]

admit=0 / reserve=1 (C005) / reject=5。本方向首批落地，Slope/Resi/Rsquare 三 0-admit operator-family 整体困境揭晓：**LHS atom 与 vol_20d 几何正交期望全面破产**——5/6 候选 dom=vol_20d (beta 8-15.84)，1/6 dom=str_1m (C001 beta=8.56)。Operator-family novelty 不等价 style novelty: Slope/Resi/Rsquare 在 close 字段上的信号载体仍是标准 Barra 风险因子。

**Thread 进展**：
- T001 Slope/Ref → ✗ DISPROVEN：短窗 (C001) str_1m 重表达 + incremental_ic 负 / 长窗 (C006) regime drift sign_flip
- T002 Resi → ✗ DISPROVEN：双窗双 RHS (C002 long/PB hard_gate, C003 short/PE weak+负 incr_ic) 全失败，与库内 F006/F008/F009 信号空间共同覆盖
- T003 Rsquare → 部分 ANSWERED：standalone (C004) 信号近 0 + rank-order 完美但 spread≈0 → DISPROVEN; rank-diff (C005) 通过 hard gate, ic_oos=+0.0155 + mono_oos=0.9 + ic_by_year 2017+ 增强 → RESERVE
- T004 🆕 Rsquare-rank-diff RHS 选型：承接 C005 anchor，下批扫 PE/PB/PS 三 RHS + Rsquare(120) 长窗

**hot_topic 复现**：P004 (vol_20d 结构性吸收) 显著强化——本批 6 候选 LHS 与 vol_20d 几何正交全部失败。P006 (library_reducer trap) 部分缓解——rubric 的 incremental_ic 双重 gate (max_corr<0.30 + incr_ic>0.010) 在 C001 上正确避免错杀风险（max_corr=0.24 但 incr_ic=-0.017 不达 incr_ic 必要条件）。

**下一步**：保留方向 exploring 一批，下批以 C005 (Rsquare/PS rank-diff) 作 anchor 测 Rsquare(60) × {PE60, PB60, raw norm} + Rsquare(120) 长窗 + Rsquare-on-other-fields ($turnover_rate, $volume)。若仍全 reject → 方向 status: exploring → dead，T003/T004 thread DISPROVEN，升格 lessons "time-series Slope/Resi/Rsquare on $close 在 csi1000 cross-section 死区"。

**Operations**　`status: exploring` 保持 (rounds 0→1，admits 0；T001/T002 DISPROVEN 缩窄到 T003/T004 单路径) · `priority: medium` 保持

> [!quote]+ 2026-04-28 · 方向新建
> **方向开题** · 来自 [[_consolidation/findings/library_gap/002]] (HIGH) + [[_consolidation/findings/library_gap/005]] (MEDIUM) 双 finding 推荐, 切入 zero_admit_streak=5 saturation regime 下唯一未试 operator-family 空缺。
>
> - 库内 23 admit factor expressions 盘点 confirm: `Slope` / `Resi` / `Rsquare` 三算子 0 出现 (manual scan F001-F023)
> - 历史 batch 仅 batch_001/003/033 测过 Slope on `$amount` family, **Slope on $close / $high / $low / $turnover_rate / $pe_ratio 全部未试**; **Resi 与 Rsquare 在 manifest history 0 出现**
> - 方向区别于 [[trend_quality_gated]] (dead) 的关键: trend_quality 用 `Mean(returns,N)` (一阶聚合) gate by amount; 本方向用 `Slope/Resi/Rsquare` (rolling regression family) — operator-family 几何不同, 不是 Mean(ret) 的 alias
> - 6 候选设计三条 thread: T001 Slope (C001/C006), T002 Resi (C002/C003), T003 Rsquare (C004/C005)
> - RHS 严避: ❌ amount/turnover 单字段聚合 (F002 anchor) ❌ overnight_5/turnover_5/body_ratio_20/price_vol_20/Amihud_20/H/L_60 dead endpoints ❌ circ_mktcap (Barra direct) ❌ F017 turnover-family cluster
> - RHS 安全选: ✅ Mean(PE,60) / Mean(PB,60) / Mean(PS,60) raw fundamental level (level form 区别于 fundamental_momentum dead 的 Delta/rate) ✅ standalone (无 RHS, raw factor) ✅ 自身 standalone (R² 单 atom)
>
> **Operations**　`status: exploring` (新建) · `priority: medium` (operator-family novelty 强 + library_gap HIGH severity 双背书, 但 csi1000 reversal 风险已知) · rounds 0→1 (待 b065 落地后)
