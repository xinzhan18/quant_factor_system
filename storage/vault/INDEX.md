---
generated_at: 2026-04-12T12:55:00Z
round: 1
total_active_directions: 1
total_factors_admitted: 2
last_batch: batch_001
last_consolidation_round: null
---

# Factor Research Index

> MOC (Map of Content)：所有研究方向和 admitted 因子的总览。
> 上半段由 LLM 维护；下半段由 Python 自动刷新。

## 活跃方向

### [[directions/candlestick_liquidity|K 线微观结构 × 流动性]] `productive` `high`
首轮探索产出 2 个因子。影线信号 IC 强劲（ICIR -0.42 到 -0.58），但 Barra vol 暴露是核心问题。下一步需要 CsRank 正交化或 ratio 表达式去 vol。3 个 thread 全部 active。

## 最近 Batch

| Batch | Direction | Admits | 关键发现 |
|---|---|---|---|
| [[batches/batch_001/judge\|batch_001]] | [[directions/candlestick_liquidity\|candlestick_liquidity]] | [[factors/F001\|F001]], [[factors/F002\|F002]] | 影线信号强但 vol 污染；shadow_product 最干净 |

## 因子库

| Factor | 名称 | ICIR | Style R² | 方向 |
|---|---|---|---|---|
| [[factors/F001\|F001]] | 下影线×换手率 | ==-0.576== | 0.36 | [[directions/candlestick_liquidity\|candlestick]] |
| [[factors/F002\|F002]] | 影线乘积 | -0.418 | ==0.21== | [[directions/candlestick_liquidity\|candlestick]] |

---

## Statistics (machine-generated)

<!-- BEGIN AUTO-SECTION -->

| Direction | Status | Priority | Rounds | Admits | Last batch |
|---|---|---|---|---|---|
| candlestick_liquidity | saturated | high | 4 | 5 | batch_004 |
| fundamental_technical_cov | exploring | medium | 3 | 2 | batch_007 |
| timing_signals | exploring | high | 1 | 3 | batch_008 |

| Metric | Value |
|---|---|
| Total factors admitted | 10 |
| Current round | 7 |
| Last consolidation | — |

<!-- END AUTO-SECTION -->
