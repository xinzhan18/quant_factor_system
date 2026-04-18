---
direction_tag: fundamental_technical_cov
status: exploring
priority: medium
rounds: 3
admits: 2
last_batch: batch_007
last_activity: '2026-04-15T14:04:40Z'
created_batch: batch_005
members:
- F006
- F007
merged_into: null
last_admits: []
last_goal: 'Third round: Cov变体(amt×PE/tur×PS/tur×PB短窗口), PE rank delta+conditioning,
  Corr(tur,PB/amt,PS,60d), Cov(ret,PE,20d)'
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

### 2026-04-12 [[batches/batch_005/judge|batch_005]]
首轮。8 候选，1 admit（[[factors/F006|F006]] 营收增长×CsRank(-PB), ICIR=0.331, max_corr=0.167），2 reserve，5 reject。Cov 类信号 style 干净但偏弱。CsRank 交互被 vol 污染。Corr(tur,PE,20) NaN error。F006 开启纯 fundamental 信号维度。

### 2026-04-12 [[batches/batch_006/judge|batch_006]]
第二轮。1 admit（[[factors/F007|F007]] Cov(换手率,PE,20天), ICIR=-0.316, style_r2=0.099），3 reserve，4 reject。T001 的 20 天 Cov 是最佳 Cov 表达。T004(rank delta) 干净正交但太弱(ICIR 0.16)。PS/PB 的 Cov 被 value style 污染。exploring → **productive**。

### 2026-04-15 [[batches/batch_007/judge|batch_007]]
第三轮。==0 admit==，3 reserve，5 reject。Cov(amt,PE,20) corr=0.855 vs F007 → 冗余。PS/PB Cov 全部 style_r2>0.3。Corr 信号在 fundamental 字段上==完全不可行==（估值变化太慢→标准差趋零→NaN）。T004 rank delta 仍然太弱。

**方向状态评估**：
- T001(Cov): F007 是最佳表达，PE 20天。PS/PB 版本 style 污染。==T001 saturated==。
- T002(CsRank 交互): batch_005 全部 style_r2>0.3。==T002 saturated==。
- T003(fundamental change): F006 是最佳表达。EPS/Revenue 变体与 F006 冗余>0.6。==T003 接近 saturated==。
- T004(rank delta): 极干净极正交但 ICIR 0.15-0.20——信号强度不够 admit。Reserve 观察。

**priority**: high → **medium**。方向产出率下降，但 T004 有少量残余空间。
