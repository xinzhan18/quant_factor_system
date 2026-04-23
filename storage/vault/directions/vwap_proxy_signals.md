---
direction_tag: vwap_proxy_signals
status: productive
priority: medium
rounds: 1
admits: 1
last_batch: batch_040
last_admits:
- F014
last_goal: 'T001+T002 first pass on synthesized VWAP = $amount/$volume. Probe VWAP-close
  / VWAP-open / VWAP-prevclose spreads, raw and price-normalized; 5d/20d aggregations.
  Critical: max_corr@F003 < 0.7 and @F009 < 0.7 to avoid near_duplicate with existing
  overnight/gap family.'
last_activity: '2026-04-23T19:54:09Z'
created_batch: null
members:
- F014
merged_into: null
---
# vwap_proxy_signals

> [!abstract]+ 方向概要
> - **状态**　🟢 `productive` · priority `medium` · rounds = 1 · admits = 1 (F014)
> - **最近**　[[batches/batch_040/judge|batch_040]] · 2026-04-24 · 1/0/5（首批即 admit C004 → F014 vwap_overnight_spread）
> - **一句话**　Synthesized VWAP=`$amount/$volume` 在跨 session 维度 (vs prev close) 解锁独立 alpha；同 session VWAP-close 偏离没有 rank-order

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

---

## Current Focus

- 首批 6 候选覆盖 4 个 spread 形态 + 2 个聚合
- T001 测 raw spread；T002 测 normalized spread；T003 测 aggregated
- 关键审计：max_corr@F003 / @F009 < 0.7 防 near_dup

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

---

## Known Failures

| Candidate | Expression | Reject Reason |
|---|---|---|
| [[batches/batch_040/candidates/C001\|C001]] | `(VWAP - close)/close` raw | weak mono 0.10 + ls_t<2 (Q1 一桨驱动) |
| [[batches/batch_040/candidates/C002\|C002]] | C001 5d agg | IC↓ ls_t↓ alpha_surv↓ |
| [[batches/batch_040/candidates/C003\|C003]] | C001 20d agg | weak mono + alpha_surv=0.32 poor |
| [[batches/batch_040/candidates/C005\|C005]] | (VWAP - open) 5d | mono=-0.90 但 incr=-0.013 (F012 reducer) |
| [[batches/batch_040/candidates/C006\|C006]] | (VWAP/close) 20d | 与 C003 加法常数等价 |

---

## Related

- 🟡 [[overnight_intraday_split]] `saturated` — F009 overnight-intraday spread；本方向 VWAP proxy 也含日内/日间结构，max_corr 重点测试
- 🟡 [[intraday_price_formation]] `saturated` — F003 gap magnitude；VWAP gap 是本方向 candidate 之一
- 🟡 [[ohlc_temporal_aggregation]] `saturated` — F006-F008 shadow shape；VWAP 是 OHLC 的另一种聚合
- 📖 [[lessons#Operator Registry]] — `$vwap` 全零，本方向用 `$amount/$volume` 合成
