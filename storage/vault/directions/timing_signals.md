---
direction_tag: timing_signals
status: exploring
priority: high
rounds: 1
admits: 3
last_batch: batch_008
last_activity: '2026-04-15T16:07:49Z'
created_batch: batch_008
members:
- F008
- F009
- F010
merged_into: null
last_admits:
- F008
- F009
- F010
last_goal: 'First round timing signals: raw IdxMax/IdxMin (close/volume/turnover),
  timing×momentum interactions, multi-window timing differential'
---
# Timing Signals (IdxMax / IdxMin)

## Hypothesis

IdxMax 和 IdxMin 算子返回"过去 N 天内极值发生在哪一天"——这是纯时序位置信息，与 level（价格/成交量级别）正交。极值发生的时机包含了市场微观结构的节奏信息：如果最高价出现在窗口的最开始（IdxMax 接近 N），说明价格在下行通道；如果出现在最近（IdxMax 接近 0），说明处于上行突破中。

这个方向的独特之处在于：（1）IdxMax/IdxMin 是离散整数值，天然正交于连续的 Barra style 因子；（2）F005（IdxMax(上影线,20)×(-5日ret)）已经证明 timing 信号与现有因子库极低冗余（max_corr=0.233）——本方向是 F005 成功经验的系统化拓展。

核心经济逻辑：A 股散户在极值时刻的行为具有系统性偏差——追高杀跌。IdxMax/IdxMin 的时序位置捕捉了"极端情绪发生在多久之前"，这与情绪衰减速度有关。如果极值很久以前发生（idx 大），情绪已经消化，价格回归基本面；如果刚刚发生（idx 小），情绪还在，趋势可能延续。

## Current Focus

系统化探索不同字段的 IdxMax/IdxMin + 条件因子组合。F005 证明了 shadow × timing × momentum 的方向可行。

## Threads

### T001: IdxMax/IdxMin 不同字段的信号强度 [◉ ACTIVE]
**Question**: $close, $volume, $turnover_rate, $amount 的 IdxMax/IdxMin 哪个有最强独立信号？
**Evidence trail**: 
- F005(batch_004): IdxMax(上影线/close,20)×(-5日ret) ICIR=+0.386, style_r2=0.052, corr=0.233 → 验证了 timing 方向可行
**Next probes**: IdxMax($close,20), IdxMin($close,20), IdxMax($volume,20), IdxMax($turnover_rate,20)

### T002: Timing × momentum/reversal 交互 [◉ ACTIVE]
**Question**: IdxMax/IdxMin 与近期收益（5d/10d/20d ret）的交互是否比 raw timing 更强？
**Evidence trail**: (F005 是 shadow timing × momentum，本轮测试 price/volume timing × momentum)
**Next probes**: Mul(IdxMax($close,20), Div($close,Ref($close,5)))

### T003: 多窗口 timing 差异 [◉ ACTIVE]
**Question**: 短窗口(5d)和长窗口(60d)的 IdxMax 差值是否捕捉 regime 转换？
**Evidence trail**: (empty)
**Next probes**: Sub(IdxMax($close,5), IdxMax($close,60))

## Known Failures
_(empty — first batch)_

## Related
- [[factors/F005]] — IdxMax(上影线,20)×(-5日ret) 已证明 timing 方向可行
- [[../lessons#Prior Signal Space Knowledge]] — "Timing signals (IdxMax/IdxMin based)" listed as promising

## Narrative Log
_(empty — first batch)_
