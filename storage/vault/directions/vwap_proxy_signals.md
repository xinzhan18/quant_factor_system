---
direction_tag: vwap_proxy_signals
status: productive
priority: medium
rounds: 2
admits: 1
last_batch: batch_042
last_admits: []
last_goal: T003 独立 VWAP 形态：F014 (VWAP-prev_close) 之外是否有其它 VWAP 形式携带独立 alpha？探五类锚点：HLC
  范围内 VWAP 位置 / VWAP 相对范围中点 / VWAP signed 持久性 / VWAP 相对 rolling mean 回归 / VWAP 与 body
  方向一致性。硬闸 max_corr@F014 < 0.7 防自我近重复，max_corr@F010 < 0.7 防 overnight 维度重复。
last_activity: '2026-04-24T01:47:37Z'
created_batch: null
members:
- F014
merged_into: null
---
# vwap_proxy_signals

> [!abstract]+ 方向概要
> - **状态**　🟢 `productive` · priority `medium` · rounds = 2 · admits = 1 (F014)
> - **最近**　[[batches/batch_042/judge|batch_042]] · 2026-04-24 · 0/3/3（T003 五子路径撞墙：HLC-位置类与 F014 79–89% 重合）
> - **一句话**　Synthesized VWAP=`$amount/$volume` 在跨 session 维度 (vs prev_close) 解锁独立 alpha；同 session / daily-anchor VWAP 形态被 A 股 10% 涨跌幅约束夹紧，rank-order 与 F014 高度共动

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

- T003 已挂起：剩余唯一路径是"orthogonalize by F014 / vol_20d 后的 VWAP 残差"，需 barra_residual_signal / orthogonalize 算子工具链
- 短期方向冷藏，等待 orthogonalize 工具或外部 paper 启发新形态

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

---

## Related

- 🟡 [[overnight_intraday_split]] `saturated` — F009 overnight-intraday spread；本方向 VWAP proxy 也含日内/日间结构
- 🟡 [[intraday_price_formation]] `saturated` — F003 gap magnitude；F005 双律共同作用方向
- 🟡 [[ohlc_temporal_aggregation]] `saturated` — F006-F008 shadow shape；OHLC algebraic mirror 出处
- 🟡 [[gap_acceptance_structure]] `productive` — F005 关联方向，10% 涨跌幅 cluster 共享
- 📖 [[lessons#Operator Registry]] — `$vwap` 全零，本方向用 `$amount/$volume` 合成

---

## Narrative Log

> [!quote]+ 2026-04-24 · [[batches/batch_042/judge|batch_042]]
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
