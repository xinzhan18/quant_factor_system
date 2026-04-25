---
direction_tag: vwap_proxy_signals
status: saturated
priority: low
rounds: 3
admits: 1
last_batch: batch_057
last_admits: []
last_goal: 'T004 higher-moment LHS independence axis on VWAP-derived scale-free ratios
  × non-saturated rank-diff RHS — 6 candidates testing Std/Skew(synthesized_VWAP_gap,
  N≤20) wrapped in CsRank, paired with non-saturated RHS atoms (turnover_rate Mean
  10, range_to_close Med 20, log_circ_mktcap, amount/mktcap, log_amount Mean 20).
  Goal: open new VWAP-basis higher-moment alpha axis bypassing F005 OHLC mirror affine
  constraint via rank-diff decoupling (F019/F020 paradigm transfer to VWAP basis).
  Hard-checks: max_corr@F014<0.7, max_corr@anchor<0.30, alpha_surv>=0.30 (rank-diff
  threshold).'
last_activity: '2026-04-25T10:57:37Z'
created_batch: null
members:
- F014
merged_into: null
---
# vwap_proxy_signals

> [!abstract]+ 方向概要
> - **状态**　🟡 `saturated` · priority `low` · rounds = 3 · admits = 1 (F014)
> - **最近**　[[batches/batch_057/judge|batch_057]] · 2026-04-25 · 0/1/5（T004 higher-moment LHS × VWAP basis 几乎完全证伪：4/6 hard_gate fail；C005 Skew rank-order 极优但 vol_20d + F017 cluster 双重夹击）
> - **一句话**　Synthesized VWAP=`$amount/$volume` 在跨 session 维度 (vs prev_close) 解锁独立 alpha (F014)；其它形态 (daily-anchor / higher-moment / momentum) 全被 F005 OHLC mirror + F001 vol_20d + F017 cluster 三律夹击

---

## Hypothesis

`$vwap` 在当前数据源全零、precheck 禁用。但 `$amount/$volume` = 当日 RMB 总成交额 / 总成交股数 = **当日平均成交价/股 ≈ daily VWAP**。这是一个未被现有库利用的**合成 VWAP 通道**——paper QuantaAlpha 等论文都把 VWAP 作为基础字段（Alpha158/360 用 vwap），我们必须自合成。

经济直觉：
- **VWAP-close spread**：`($amount/$volume) - $close` = 当日平均成交价 vs 收盘价。正值说明日内多数交易在收盘以上完成（买方主导后期回落 / 高位放量套现）；负值反向。捕获日内 order-flow 不平衡的代理。
- **VWAP-open spread**：`($amount/$volume) - $open` = 平均成交价 vs 开盘价。正 = 日内整体上涨；负 = 下跌。可能与 body sign 同源但加权不同。
- **VWAP gap**：`($amount/$volume) - Ref($close, 1)` = 平均成交价 vs 昨收。包含隔夜信息 + 日内信息混合。
- **VWAP-close ratio aggregation**：5d/20d Mean of `($amount/$volume) / $close`，捕获持续偏离方向。

预期：与 F003 (gap), F009 (overnight-intraday spread), F006-F011 (shadow / overnight) 的信号源**有重叠但函数形式独立**——VWAP proxy 整合了 day-level 量价信息而 OHLC + overnight 系列分散在 4 个端点。

风险：
- 与 F009 overnight spread 共线（都包含日内/日间结构）
- 与 F002 pb_amount_ratio 都用 $amount，但 F002 未涉及 $volume
- 小盘股 $volume 低，$amount/$volume 方差大，可能 noise

> [!warning]+ ⚠️ 结构性约束（来自 distillation F005 · medium）
> **A 股 10% 涨跌幅 + OHLC algebraic mirror 双律**——daily-anchor VWAP 派生量（HLC 位置 / 范围中点 / VWAP-MeanVWAP 均值回归）在 cross-section 上与 F014 (VWAP-prev_close) 79–89% rank 共动。机制：H、L、prev_close 三个 reference point 都被 ±10% 涨跌幅夹紧，相互之间存在 affine-like 共变。
> **设计准则**：未来 VWAP 候选起手前必做：
> (a) 是否与 F014 在 H-L / prev_close / OHLC4 维度存在 affine 等价 → max_corr ≥ 0.85 必为 cluster；
> (b) 是否仿射常数等价（如 b042 C002 = C001 - 0.5 → metrics 六位小数恒等）；
> (c) 优先走 **跨 session VWAP** (F014 路径) 而非 daily-anchor，或 **orthogonalize by F014 / vol_20d** 残差路径。

---

## Current Focus

- 方向已 saturated（batch_057 转化）。剩余所有探索路径短期阻塞或低 ROI:
  - T003 残差路径阻塞于 orthogonalize 工具链
  - T004 higher-moment paradigm transfer 几乎完全证伪（VWAP-prev gap 嵌入 vol_20d 信息 → higher-moment 不是独立 axis）
- **复活条件**: F017 退役 → C005 重测; vol_20d Python residual 工具链 + coverage 修复; minute-bar 数据基础设施

---

## Threads

### T001: VWAP-Close / VWAP-Open / VWAP-prevclose spread [✓ ANSWERED batch_040]

> [!success]+ Thread 结论
> **Question**: VWAP spread 形态是否携带独立 alpha？
> **Answer**: 是，**但仅在跨 session 维度（VWAP - prev_close）**。same-day spread (C001 raw, C005 VWAP-open 5d) 都 fail——C001 weak mono 0.10、C005 是 F012 reducer。C004 (VWAP - prev_close) 引入 overnight 维度后 mono 跳到 0.60、ls_t=3.79。
>
> **Evidence trail**:
> - [[batches/batch_040/candidates/C001|batch_040 C001]]　(VWAP-close)/close raw, IC=+0.027 mono=0.10 → **reject** (一桨驱动)
> - [[batches/batch_040/candidates/C004|batch_040 C004]]　(VWAP-prevclose)/prevclose, IC=+0.011 **mono=+0.60** ls_t=3.79 incr=+0.012 → **admit → [[factors/F014]]**
> - [[batches/batch_040/candidates/C005|batch_040 C005]]　VWAP-open 5d, IC=-0.017 mono=-0.90 incr=-0.013 → **reject** (F012 reducer，clean reversal 但 admit 减库)

### T002: VWAP normalized to price 5d/20d aggregation [✗ DISPROVEN batch_040]

> [!failure]+ Thread 结论
> **Question**: ($amount/$volume) / $close 比值的 5d/20d 聚合是否独立？
> **Answer**: 否。C002/C003/C006 全部 mono=0.10。日内 VWAP/close 偏离没有 cross-section 可聚合持续性。
>
> **Evidence trail**:
> - [[batches/batch_040/candidates/C002|batch_040 C002]]　5d agg of C001, IC=+0.021 → **reject**
> - [[batches/batch_040/candidates/C003|batch_040 C003]]　20d agg of C001, IC=+0.018 alpha_surv=0.32 → **reject**
> - [[batches/batch_040/candidates/C006|batch_040 C006]]　VWAP/close ratio 20d, IC=+0.018 → **reject** (与 C003 加法常数等价)

### T003: 独立 VWAP 形态（HLC 位置 / 范围中点 / signed 持久性 / 均值回归 / 方向一致性）[⏸ SUSPENDED batch_042]

> [!note]+ Thread 当前
> **Question**: F014 (VWAP-prev_close) 之外，是否存在其它 VWAP 形式携带独立 alpha？
> **Status**: 挂起。5 子路径中 4 类已部分证伪（HLC 位置 stat-space 重合 / signed-Sign agg 稀疏 / VWAP 均值回归 rank 崩 / sign×sign 失效）。剩 1 条"orthogonalize by F014 / vol_20d 后的 VWAP 残差"路径阻塞于工具链。
>
> **Evidence trail**:
> - [[batches/batch_042/candidates/C001|batch_042 C001]]　(VWAP-L)/(H-L) — IC=0.032 ls_t=2.72 但 **max_corr@F014=0.887**，stat-space 重合 → **reserve**
> - [[batches/batch_042/candidates/C002|batch_042 C002]]　(VWAP-midHL)/(H-L) — **与 C001 仿射等价**（C002=C001-0.5）metrics 恒等 → **reserve**
> - [[batches/batch_042/candidates/C003|batch_042 C003]]　Mean(Sign(VWAP-prev_close), 5) — Sign 使 85.7% 压零，ls_t=-0.67 → **reserve**
> - [[batches/batch_042/candidates/C004|batch_042 C004]]　(VWAP-MeanVWAP20)/MeanVWAP20 — mono 0.9→-0.3 翻号 style_r²=0.68 吞噬 → **reject**
> - [[batches/batch_042/candidates/C005|batch_042 C005]]　Mean(Sign(body)×Sign(VWAP-prev_close), 5) — sign×sign 丢 magnitude, cum_mdd=-70 → **reject**
> - [[batches/batch_042/candidates/C006|batch_042 C006]]　C001 的 5d agg — alpha_surv=0.29 + max_corr=0.894@F014 → **reject**
>
> **关键发现**: A 股 10% 涨跌幅约束使 HLC range 与 prev_close 尺度共动——"daily-anchor VWAP" 在 cross-section 上无法实证独立于 "cross-session VWAP" (F014)。已沉淀为 distillation F005。
>
> **Next probes**: orthogonalize by F014 / vol_20d 残差路径（需工具链）。

### T004: Higher-moment LHS on VWAP-derived scale-free ratios × non-saturated rank-diff RHS [◉ ACTIVE]

> [!note]+ Thread 当前
> **Question**: VWAP basis 上的 higher-moment LHS（Std/Skew of synthesized VWAP gap, N≤20d, scale-free, single-layer）能否通过 rank-diff 与非饱和 RHS 配对，跨 family 解耦后兑现独立 alpha——即把 F019 (Std body_ratio,20) / F020 (Std gap_ret,20) 跨 family 律迁移到 VWAP 基底？
>
> **Status**: batch_057 启动。设计契约：
> (a) LHS 必须是 scale-free VWAP-derived ratio（VWAP-prev/prev / VWAP-open/open / VWAP-vs-VWAP_5d/VWAP_5d）
> (b) higher-moment 算子必须单层、N≤20d（避 P003 regime sign-flip）
> (c) RHS atom 必须避开饱和 endpoints（overnight_5/turnover_5/amount_20/body_ratio_20/price_vol_20）
> (d) max_corr@F014<0.7 + max_corr@anchor<0.30
> (e) 不嵌套 TsKurt/TsSkew inside CsRank（操作 bug）
>
> **Evidence trail**:
> - [[batches/batch_057/candidates/C001|batch_057 C001]]　Std(VWAP-prev gap, 20) ⊕ turnover_rate Mean 10 → **reject (hard_gate ic_oos=-0.007 < 0.008)**
> - [[batches/batch_057/candidates/C002|batch_057 C002]]　Std(VWAP-prev gap, 10) ⊕ Med((H-L)/close, 20) → **reject (hard_gate sign_flip)**
> - [[batches/batch_057/candidates/C003|batch_057 C003]]　Std(VWAP-open gap, 20) ⊕ Log(circ_market_cap) → **reject** (ls_t=-0.14, mono_oos=0, vol_20d exposure=**48.04** 整库罕见极值, incr_ic=-0.007 库减值)
> - [[batches/batch_057/candidates/C004|batch_057 C004]]　Std(VWAP-prev gap, 20) ⊕ Mean(amount/circ_market_cap, 20) → **reject (hard_gate mono_sign_flip IS=0.7/OOS=-0.6)**
> - [[batches/batch_057/candidates/C005|batch_057 C005]]　Skew(VWAP-prev gap, 20) ⊕ turnover_rate Mean 10 → **reserve** (mono_oos=0.9, cum_ic_mdd=-2.18 整库罕见, ic_by_year 9 年单调强化; alpha_surv=0.157<<0.30 + max_corr=0.51@F017 + incr_ic=0.005 触 F203 cluster co-resonance)
> - [[batches/batch_057/candidates/C006|batch_057 C006]]　Std(VWAP momentum 5d, 20) ⊕ Mean(Log(amount), 20) → **reject (hard_gate ic_oos=0.0035 < 0.008)**
>
> **结论 (batch_057)**: T004 几乎完全证伪。二阶矩 (Std) 路径 3 候选全 hard_gate fail；三阶矩 (Skew) C005 唯一 reserve 但被 vol_20d + F017 cluster 双重夹击；within-VWAP momentum noise dominated；VWAP-open anchor 同 session = vol_20d 极端载体 (exp=48.04 整库新高)。
>
> **Next probes**: 仅有 (a) Kurt 四阶矩 + (b) Skew × 不同 RHS 残余路径；但方向 rounds=3 + reject>80% 已触 saturated 转化。复活路径：F017 退役 / vol_20d Python residual 工具链 / minute-bar 数据。

---

## Known Failures

| Candidate | Expression | Reject Reason |
|---|---|---|
| [[batches/batch_040/candidates/C001\|b040 C001]] | `(VWAP - close)/close` raw | weak mono 0.10 + ls_t<2 (Q1 一桨驱动) |
| [[batches/batch_040/candidates/C002\|b040 C002]] | C001 5d agg | IC↓ ls_t↓ alpha_surv↓ |
| [[batches/batch_040/candidates/C003\|b040 C003]] | C001 20d agg | weak mono + alpha_surv=0.32 poor |
| [[batches/batch_040/candidates/C005\|b040 C005]] | (VWAP - open) 5d | mono=-0.90 但 incr=-0.013 (F012 reducer) |
| [[batches/batch_040/candidates/C006\|b040 C006]] | (VWAP/close) 20d | 与 C003 加法常数等价 |
| [[batches/batch_042/candidates/C004\|b042 C004]] | `(VWAP - MeanVWAP20)/MeanVWAP20` | mono_flip IS→OOS, style_r²=0.68 vol_20d 吞噬, cum_mdd=-73 |
| [[batches/batch_042/candidates/C005\|b042 C005]] | `Mean(Sign(body)×Sign(VWAP-prev_close), 5)` | sign×sign 丢 magnitude, cum_ic_mdd=-70, edge 近 3 年衰减 |
| [[batches/batch_042/candidates/C006\|b042 C006]] | `Mean((VWAP-L)/(H-L), 5)` | alpha_surv=0.29 poor + max_corr=0.894@F014 high |
| [[batches/batch_057/candidates/C001\|b057 C001]] | `Sub(CsRank(Std(VWAP-prev gap, 20)), CsRank(Mean(turnover_rate, 10)))` | hard_gate ic_oos=-0.007<0.008 noise |
| [[batches/batch_057/candidates/C002\|b057 C002]] | `Sub(CsRank(Std(VWAP-prev gap, 10)), CsRank(Med((H-L)/close, 20)))` | hard_gate sign_flip + 双 IC<0.005 |
| [[batches/batch_057/candidates/C003\|b057 C003]] | `Sub(CsRank(Std(VWAP-open gap, 20)), CsRank(Log(circ_mktcap)))` | ls_t=-0.14, mono_oos=0, vol_20d exp=**48.04** 整库新高, incr_ic=-0.007 |
| [[batches/batch_057/candidates/C004\|b057 C004]] | `Sub(CsRank(Std(VWAP-prev gap, 20)), CsRank(Mean(amount/circ_mktcap, 20)))` | hard_gate mono_sign_flip IS=0.7/OOS=-0.6 |
| [[batches/batch_057/candidates/C006\|b057 C006]] | `Sub(CsRank(Std((VWAP-VWAP_5d)/VWAP_5d, 20)), CsRank(Mean(Log(amount), 20)))` | hard_gate ic_oos=0.0035<0.008 within-VWAP noise |

---

## Related

- 🟡 [[overnight_intraday_split]] `saturated` — F009 overnight-intraday spread；本方向 VWAP proxy 也含日内/日间结构
- 🟡 [[intraday_price_formation]] `saturated` — F003 gap magnitude；F005 双律共同作用方向
- 🟡 [[ohlc_temporal_aggregation]] `saturated` — F006-F008 shadow shape；OHLC algebraic mirror 出处
- 🟡 [[gap_acceptance_structure]] `productive` — F005 关联方向，10% 涨跌幅 cluster 共享
- 📖 [[lessons#Operator Registry]] — `$vwap` 全零，本方向用 `$amount/$volume` 合成

---

## Narrative Log

> [!quote]+ 2026-04-25 · [[batches/batch_057/judge|batch_057]]
> **T004 几乎完全证伪 → status: productive → saturated** · admit=0 / reserve=1 (C005) / reject=5
>
> - 6 候选探"higher-moment LHS × VWAP basis × non-saturated rank-diff RHS"路径，**4/6 hard_gate 失败** (ic_oos_too_low ×2 / sign_flip ×1 / mono_flip ×1) — 二阶矩 (Std) 路径在 turnover_rate Mean 10 / Med((H-L)/close,20) / amount/circ_mktcap Mean 20 三个非饱和 RHS 上全 fail
> - C003 (Std VWAP-open gap × Log circ_mktcap) reject — vol_20d exposure=**48.04** 整库历史新高 (超 b008 C005=32.0)，证实 VWAP-open 同 session 锚点是 vol_20d 极端载体；ic_by_year 2015 后 9 年单边翻号
> - C005 (Skew VWAP-prev gap × turnover_rate Mean 10) reserve — 唯一进入软 CP 的高张力候选: rank-order **极优** (mono_oos=0.9, sign_consist=1.0, cum_ic_mdd=**-2.18 整库罕见**, ic_by_year 9 年单调强化 +0.016→+0.030) **vs** 严重 vol_20d 吸收 (alpha_surv=**0.157**<<0.30 rank-diff floor) + F017 cluster 共振 (max_corr=0.51, incr_ic=0.005 触 **F203 cluster co-resonance reject pattern**)
> - **结构发现**: F019/F020 paradigm transfer to VWAP basis 失败。差异: F019/F020 (Std body_ratio / Std gap_ret) 的 atom 与 vol_20d 正交；而 VWAP-prev gap 自身嵌入波动率信息 → higher-moment 不是独立 axis 而是 vol_20d 极端载体。**lessons.md "Promising Unexplored" 第 1 条需附 caveat: family-agnostic higher-moment 律仅在 atom 自身与 vol_20d 正交时成立**
> - MT budget cumulative 300 → **306** (首次破 300) · direction 12 → **18** · bucket `high`（封顶 search_adjusted 推回 `medium`）
>
> **Operations**　`status: productive → saturated`（rounds=3 + 连续 2 batch reject>80% 满足触发）· `priority: medium → low`（剩余路径仅 Kurt 四阶矩 / Skew × 不同 RHS / Python residualize / minute-bar，全部短期阻塞或低 ROI）
>
> **复活条件**: F017 退役 → C005 重测；vol_20d Python residualization 工具链 + coverage 修复 → T003/T004 残差路径重启；非 daily-bar 数据 → 根本性逃离

> [!quote]- 2026-04-24 · [[batches/batch_042/judge|batch_042]]
> **T003 五子路径撞墙 · 0 admit / 3 reserve / 3 reject**
>
> - C001 (VWAP-L)/(H-L) HLC 位置 IC_OOS=0.032 ls_t=2.72 cum_mdd=-2.04 看似最强候选，但 **max_corr@F014=0.887**，stat-space 与 F014 79% 重合 → reserve
> - C002 = C001 - 0.5（仿射等价），metrics 六位小数恒等 → reserve。**设计 regret**：未识别仿射等价，freeze 应做 canonical 去重
> - C003 Sign+5d agg 使 85.7% 压零 → reserve（沉淀但不值得因子化）
> - C004 VWAP 20d 均值回归 mono_flip + style_r²=0.68 vol_20d 吞噬 → reject
> - C005 sign×sign 丢 magnitude + cum_ic_mdd=-70 edge 近 3 年衰减 → reject
> - C006 C001 5d agg alpha_surv=0.29 poor → reject
> - **结构发现**：A 股 10% 涨跌幅约束使 HLC range 与 prev_close 尺度共动，"daily-anchor VWAP" 无法实证独立于"cross-session VWAP"——T003 的 4/5 子路径在这个约束下一并失败（已沉淀至 distillation F005）
> - MT budget cumulative 204 → **210** · direction 6 → **12** · bucket `high`（封顶 search_adjusted 推回 `medium`）
>
> **Operations**　`priority: medium → low`（T003 剩余路径阻塞于 orthogonalize 工具链；方向短期挂起）· `status: productive` 保持（2 rounds 不足判 saturated）

> [!quote]- 2026-04-24 · [[batches/batch_040/judge|batch_040]]
> **首批 1 admit + T001 ANSWERED + T002 DISPROVEN** · admit=1 (C004 → F014) / reserve=0 / reject=5
>
> - Synthesized VWAP `$amount/$volume` 通道兑现：跨 session 维度 (vs prev_close) 解锁信号
> - C004 IC_OOS=+0.011 mono=+0.60 ls_t=+3.79 alpha_surv=0.68 incr=+0.012 max_corr=0.17@F002 → F014 vwap_overnight_spread
> - C001-C003/C006 同 session VWAP-close 偏离 mono=0.10 全 reject——T002 DISPROVEN
> - C005 (VWAP-open) clean reversal mono=-0.90 但 incr=-0.013 是 F012 reducer，符合 csi1000 reversal cluster lesson
> - $vwap forbidden 通道补完，13 个 admits 中 max_corr 全部 ≤0.18 独立性最强
> - MT budget cumulative 198 → **204** · direction 0 → **6** · bucket `medium`
>
> **Operations**　`status: exploring → productive`（首次 admit）· `priority: medium` 保持
