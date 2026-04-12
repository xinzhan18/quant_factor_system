---
direction_tag: fundamental_technical_cov
status: exploring
priority: high
rounds: 1
admits: 1
last_batch: batch_005
last_activity: '2026-04-12T17:39:44Z'
created_batch: batch_005
members:
- F006
merged_into: null
last_admits:
- F006
last_goal: 'First exploration of fundamental×technical covariance: Cov(turnover,PE/PB/PS),
  CsRank cross-products, EPS/revenue change×liquidity conditioning'
---
# Fundamental × Technical Covariance

## Hypothesis

基本面指标（PE/PB/PS）与技术面指标（价格/成交量/换手率）之间的协方差结构包含了市场对基本面信息消化速度的信号。当 fundamental 字段和 technical 字段的共振增强时，说明市场正在积极定价基本面变化——这种定价过程有惯性，创造了短期预测窗口。

核心经济逻辑：如果一只股票的 PE ratio 和 turnover_rate 同时在截面上排名上升，说明"估值在变贵的同时成交在放大"——可能是机构在积极买入。反之，PE 和 turnover 背离，可能是被动交易或噪声。这种协方差信号在 A 股尤其有效：散户主导的市场中，fundamental-technical 的共振强度反映了"聪明钱"的参与程度。

## Current Focus

首轮探索：建立 fundamental (PE/PB/PS) 与 technical (turnover/amount/close) 之间的滚动协方差/相关性信号。

## Threads

### T001: Cov(turnover, fundamental) 是否有独立 alpha [◉ ACTIVE]
**Question**: 换手率与 PE/PB/PS 的滚动协方差是否预测未来收益？
**Evidence trail**: (empty — first batch)
**Next probes**: Cov($turnover_rate, $pe_ratio, 20/60), Corr($turnover_rate, $pb_ratio, 20/60)

### T002: CsRank(fundamental) × CsRank(technical) 交互 [◉ ACTIVE]
**Question**: 截面排名的交互项（如 CsRank(PE) × CsRank(turnover)）是否比简单协方差更有效？
**Evidence trail**: (empty)
**Next probes**: Mul(CsRank($pe_ratio), CsRank($turnover_rate))

### T003: Fundamental change × technical regime [◉ ACTIVE]
**Question**: 基本面变化速度（Delta(PE, 60)）与技术面状态（Mean(turnover, 20)）的交互是否有信号？
**Evidence trail**: (empty)
**Next probes**: Mul(Delta($pe_ratio, 60), Mean($turnover_rate, 20))

## Known Failures
_(empty — first batch)_

## Related
- [[../lessons#Structural Constraints]] — A-share no short-side alpha
- [[../lessons#Prior Signal Space Knowledge]] — "Higher-order cross-field covariance" listed as promising

## Narrative Log
_(empty — first batch)_
