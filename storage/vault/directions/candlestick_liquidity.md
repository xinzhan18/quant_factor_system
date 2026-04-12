---
direction_tag: candlestick_liquidity
status: productive
priority: high
rounds: 1
admits: 2
last_batch: batch_001
last_activity: '2026-04-12T12:51:41Z'
created_batch: batch_001
members:
- F001
- F002
merged_into: null
last_goal: First exploration of candlestick microstructure x liquidity interactions
  on csi1000 — test shadow ratios, body ratios, and range compression signals with
  and without turnover conditioner
last_admits:
- F001
- F002
---
# Candlestick Microstructure x Liquidity

## Hypothesis

A-share 日内 K 线形态（影线比例、实体大小）包含订单流信息。大单在盘中的试探行为会在上下影线中留下统计痕迹。当流动性充足（换手率高或成交额大）时，这种信息更容易被市场消化，但消化存在滞后——创造了 1-5 天的短期预测窗口。

核心经济逻辑：长上影线意味着日内有卖方力量将价格推高后未能维持（抛压信号）；长下影线意味着买方力量在低位承接（支撑信号）。这些 intraday 信号在 close price 中被部分掩盖，但可以通过 OHLC 的组合表达式重新提取。当 turnover/amount 同时高企时，信号的信噪比更高。

该方向的优势在于：（1）OHLC 字段在 Qlib 数据中完备且零缺失；（2）与现有 OHLCV 相关因子（legacy library 中的 pv_corr、vol_cv 等）正交性较好——因为那些因子主要基于 close-volume 关系，而本方向关注 OHLC 四价的微观结构。

## Current Focus

首轮探索：建立 candlestick 基本特征（body ratio、shadow ratios）与 turnover 的交互信号，验证在 csi1000 universe 上是否有统计显著的 IC。

## Threads

### T001: Shadow × turnover 交互是否有独立 alpha [◉ ACTIVE]
**Question**: 上影线/下影线比例与换手率的乘积，在控制 Barra 风格后是否保留 alpha？
**Evidence trail**:
- batch_001: C001 upper_shadow×turnover IC=-0.051 ICIR=-0.444 但 style_r2=0.35 → reserve (vol contaminated)
- batch_001: C002 lower_shadow×turnover IC=-0.064 **ICIR=-0.576** alpha_surv=0.61 → **F020 admitted** (override CP04: alpha_surv > 0.60)
**Next probes**: 尝试 CsRank 归一化减少 vol 暴露; 换用 $amount 替代 $turnover_rate

### T002: Body ratio 的时间序列特征是否有预测力 [◉ ACTIVE]
**Question**: body ratio (|close-open|/(high-low)) 的滚动统计量（mean/std/trend）是否预测未来收益？
**Evidence trail**:
- batch_001: C005 Mean(body_ratio,20) IC=0.001 → noise, reject
- batch_001: C006 Std(body_ratio,20) IC=0.006 ICIR=0.155 → too weak, reserve
**Next probes**: 尝试 Cov(body_ratio, returns) 或 body_ratio 的 delta/trend 变化

### T003: OHLC range compression 信号 [◉ ACTIVE]
**Question**: 日内价格区间 (high-low)/close 的压缩/扩张是否预测波动率 regime change？
**Evidence trail**:
- batch_001: C007 range_compression(5/60) IC=-0.038 ICIR=-0.339 alpha_surv=0.67 → reserve (borderline CP04)
- batch_001: C008 range×turnover IC=-0.072 但 style_r2=0.61 → reject (vol proxy)
**Next probes**: 纯 range compression 不加 turnover; 尝试更长 lookback (10/120)

## Known Failures
- C003 `Mul(squared_range, $turnover_rate)` — style_r2=0.46, pure vol proxy. Squaring range amplifies vol contamination.
- C005 `Mean(body_ratio, 20)` — IC=0.001, no signal. Average body ratio is not predictive.
- C008 `Mul(range, Mean($turnover_rate, 5))` — style_r2=0.61, worst risk profile. Range×turnover is fundamentally a vol×liquidity interaction fully captured by Barra.

## Related
- [[../lessons#Structural Constraints]] — A-share no short-side alpha
- [[../lessons#Prior Signal Space Knowledge]] — OHLCV near-exhausted but shadow/body ratios unexplored

## Narrative Log

### 2026-04-12 batch_001
First exploration. 8 candidates, 2 admits ([[../factors/F020|F020]] lower_shadow×turnover, [[../factors/F021|F021]] shadow_product), 3 reserves, 3 rejects.

**Key finding**: Candlestick shadow signals are strong (ICIR -0.42 to -0.58) but heavily contaminated by Barra vol_20d exposure (style_r2 0.21-0.61). The turnover conditioner amplifies both signal and vol contamination. Shadow product (F021) without turnover has the cleanest risk profile (style_r2=0.21).

**Critical lesson**: All shadow/range signals correlate with realized volatility. Future candidates must either (1) use CsRank to orthogonalize against vol, or (2) focus on ratio-based expressions that cancel out the vol scaling.

Status: exploring → **productive** (first admits). Direction remains high priority — strong raw IC but needs risk-cleaner variants.
