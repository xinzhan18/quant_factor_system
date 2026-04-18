---
direction_tag: candlestick_liquidity
status: saturated
priority: high
rounds: 4
admits: 5
last_batch: batch_004
last_activity: '2026-04-12T17:11:19Z'
created_batch: batch_001
members:
- F001
- F002
- F003
- F004
- F005
merged_into: null
last_goal: 'Fourth round: T004 shadow×momentum深化 — 不同momentum窗口(5/10/20), 上下影线对称测试,
  CsRank双rank化, shadow×volume regime, shadow timing(IdxMax), shadow asymmetry'
last_admits:
- F005
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
- [[batches/batch_001/judge#C001|batch_001 C001]]: upper_shadow×turnover IC=-0.051 ICIR=-0.444 但 style_r2=0.35 → reserve (vol contaminated)
- [[batches/batch_001/judge#C002|batch_001 C002]]: lower_shadow×turnover IC=-0.064 **ICIR=-0.576** alpha_surv=0.61 → **[[factors/F001|F001]] admitted** (override CP04: alpha_surv > 0.60)
**Next probes**: 尝试 CsRank 归一化减少 vol 暴露; 换用 $amount 替代 $turnover_rate

### T002: Body ratio 的时间序列特征是否有预测力 [◉ ACTIVE]
**Question**: body ratio (|close-open|/(high-low)) 的滚动统计量（mean/std/trend）是否预测未来收益？
**Evidence trail**:
- [[batches/batch_001/judge#C005|batch_001 C005]]: Mean(body_ratio,20) IC=0.001 → noise, reject
- [[batches/batch_001/judge#C006|batch_001 C006]]: Std(body_ratio,20) IC=0.006 ICIR=0.155 → too weak, reserve
**Next probes**: 尝试 Cov(body_ratio, returns) 或 body_ratio 的 delta/trend 变化

### T003: OHLC range compression 信号 [◉ ACTIVE]
**Question**: 日内价格区间 (high-low)/close 的压缩/扩张是否预测波动率 regime change？
**Evidence trail**:
- [[batches/batch_001/judge#C007|batch_001 C007]]: range_compression(5/60) IC=-0.038 ICIR=-0.339 alpha_surv=0.67 → reserve (borderline CP04)
- [[batches/batch_001/judge#C008|batch_001 C008]]: range×turnover IC=-0.072 但 style_r2=0.61 → reject (vol proxy)
**Next probes**: 纯 range compression 不加 turnover; 尝试更长 lookback (10/120)

## Known Failures
- C003 `Mul(squared_range, $turnover_rate)` — style_r2=0.46, pure vol proxy. Squaring range amplifies vol contamination.
- C005 `Mean(body_ratio, 20)` — IC=0.001, no signal. Average body ratio is not predictive.
- C008 `Mul(range, Mean($turnover_rate, 5))` — style_r2=0.61, worst risk profile. Range×turnover is fundamentally a vol×liquidity interaction fully captured by Barra.

## Related
- [[../lessons#Structural Constraints]] — A-share no short-side alpha
- [[../lessons#Prior Signal Space Knowledge]] — OHLCV near-exhausted but shadow/body ratios unexplored

## Narrative Log

### 2026-04-12 [[batches/batch_001/judge|batch_001]]
首轮探索。8 候选，2 admit（[[factors/F001|F001]] 下影线×换手率、[[factors/F002|F002]] 影线乘积），3 reserve，3 reject。

**核心发现**：影线信号 IC 强劲（ICIR -0.42 到 -0.58），但 Barra vol_20d 暴露严重（style_r2 0.21-0.61）。换手率条件因子同时放大了信号和 vol 污染。影线乘积（F002）不含换手率，风险最干净（style_r2=0.21）。

**关键教训**：所有 shadow/range 信号与实现波动率正相关。后续候选必须：(1) 用 CsRank 正交化去 vol，或 (2) 用 ratio 表达式抵消 vol 的 scale 效应。

状态：exploring → **productive**（首批 admit）。方向保持高优先级——原始 IC 强但需要更干净的变体。

### 2026-04-13 [[batches/batch_002/judge|batch_002]]
第二轮：CsRank 正交化实验。8 候选，1 admit（[[factors/F003|F003]] 下影线ratio×CsRank(amount)），1 reserve，6 reject。

**核心发现**：
1. CsRank 正交化成功降 vol（style_r2 从 0.2-0.6 降到 0.02-0.03），但 IC 也大幅下降。==信号和 vol 暴露高度纠缠==。
2. CsRank(shadow_product) 与 F002 corr=1.0 → 同一因子的 rank 变换不改变排序，T001 重要发现。
3. ==F003 ICIR=-0.607 是目前全系统最强信号==。用 CsRank($amount) 替代 raw $turnover_rate，保留了 F001 的核心机制但换了 liquidity 度量。
4. Range compression 所有变体（5/60, 10/60, 20/120）全部是 vol proxy (style_r2 > 0.3)，T003 接近 saturated。
5. 上影线的 CsRank 化后 IC 消失 → 上影线预测力主要来自绝对 scale（vol 本身），不是截面排序。

**Thread 更新**：
- T001：CsRank 去 vol 实验完成，结论：rank 化降 vol 但也降信号。换 liquidity 度量（$amount vs $turnover_rate）更有效。
- T002：Cov(body_ratio, return) 是 vol proxy (alpha_surv=0.07)；Delta(body_ratio) 干净但太弱。T002 接近 exhausted。
- T003：三种 range compression 都是 vol proxy。==T003 标记为 near-exhausted==。

**下一步**：探索 shadow 信号与 fundamental 字段的交互（如 shadow × PE rank）；或尝试 TsRank 时序排名替代 CsRank 截面排名。

### 2026-04-13 [[batches/batch_003/judge|batch_003]]
第三轮：shadow × fundamental + TsRank + momentum 交互。8 候选，1 admit（[[factors/F004|F004]] 上影线/close × 负5日收益），0 reserve，7 reject。

**核心发现**：
1. ==冗余是本轮主要瓶颈==。TsRank(shadow_product) style_r2=0.024 极干净、ICIR=-0.499，但 max_corr=0.743 vs F002 超标。下影线×相对换手 也同理（corr=0.744）。随着因子库增长，候选空间被挤压。
2. Fundamental conditioning（×CsRank(-PB) / ×CsRank(-PE)）对 shadow 信号==无效==（C001 IC=0.010, C006 style_r2=0.682）。Shadow 是短期微观结构信号，fundamental 是长期价值信号，两者的时间尺度不匹配。
3. ==F004 是全新的信号方向==：上影线 × 负动量。正方向 IC（高因子值→高收益），机制是"跌后出现的抛压=反弹失败确认"。与 F001-F003 的负方向信号正交。corr=0.607。
4. 影线乘积×CsRank(-PE) corr=0.946 vs F002 → CsRank conditioning 不够改变排序。

**Thread 更新**：
- T001：fundamental conditioning 失败（时间尺度不匹配）。TsRank 有效去 vol 但冗余超标。T001 ==接近 saturated==。
- T002：body_ratio × PB = vol proxy。==T002 标记 exhausted==。
- T003：已 near-exhausted（batch_002 结论）。
- ==新增 T004==：shadow × momentum reversal（F004 开启新方向）。上影线/close × (-5日ret) ICIR=0.418, style_r2=0.127。正方向信号。

**下一步**：深化 T004（momentum reversal × candlestick 变体）。candlestick_liquidity 方向在纯 shadow 信号上接近饱和，但 T004 开启了 shadow × momentum 的新维度。
