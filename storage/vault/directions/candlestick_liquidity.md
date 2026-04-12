---
direction_tag: candlestick_liquidity
status: exploring
priority: high
rounds: 1
admits: 2
last_batch: batch_001
last_activity: '2026-04-12T11:39:53Z'
created_batch: batch_001
members:
- F020
- F021
merged_into: null
last_admits:
- F020
- F021
last_goal: First exploration of candlestick microstructure x liquidity interactions
  on csi1000 — test shadow ratios, body ratios, and range compression signals with
  and without turnover conditioner
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
**Evidence trail**: (empty — first batch)
**Next probes**: Mul(shadow_ratio, $turnover_rate), Mul(body_ratio, $turnover_rate)

### T002: Body ratio 的时间序列特征是否有预测力 [◉ ACTIVE]
**Question**: body ratio (|close-open|/(high-low)) 的滚动统计量（mean/std/trend）是否预测未来收益？
**Evidence trail**: (empty)
**Next probes**: Mean(body_ratio, 20), Std(body_ratio, 20), body_ratio 的 Cov with returns

### T003: OHLC range compression 信号 [◉ ACTIVE]
**Question**: 日内价格区间 (high-low)/close 的压缩/扩张是否预测波动率 regime change？
**Evidence trail**: (empty)
**Next probes**: Div(Sub($high,$low),$close) 的 rolling mean ratio (short/long)

## Known Failures
_(empty — first batch)_

## Related
- [[../lessons#Structural Constraints]] — A-share no short-side alpha
- [[../lessons#Prior Signal Space Knowledge]] — OHLCV near-exhausted but shadow/body ratios unexplored

## Narrative Log
_(empty — first batch)_
