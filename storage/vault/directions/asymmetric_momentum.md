---
direction_tag: asymmetric_momentum
status: exploring
priority: medium
rounds: 1
admits: 0
last_batch: batch_028
last_admits: []
last_goal: '首批 3 候选测 up/down return 分解: 5d mean down-only, 5d mean up-only, 两者比值。测是否携独立
  alpha。'
last_activity: '2026-04-20T22:55:53Z'
created_batch: batch_028
members: []
retired_members: []
merged_into: null
---
# asymmetric_momentum

## Hypothesis

分解 5d return 为 up-days 和 down-days 两段，测各自对 forward return 的预测力。文献：up-down 不对称反映 loss aversion / disposition effect——散户倾向 sit on losses（不卖跌）→ down-day returns 更 informative。

## Threads

### T001: Down-only momentum [◉ ACTIVE]
### T002: Up-only momentum [◉ ACTIVE]

## Known Failures
- (空)

## Related
- [[overnight_intraday_split]] (saturated - overnight 维度)
- [[ohlc_temporal_aggregation]] (saturated)

## Narrative Log
### 2026-04-21 batch_028 (planned)
