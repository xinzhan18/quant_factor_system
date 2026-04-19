---
direction_tag: intraday_price_formation
status: saturated
priority: high
rounds: 4
admits: 2
last_batch: batch_011
last_admits: []
last_goal: 'Follow-up on F003 overnight_gap: test extended windows (Ref2-5 + MeanHigh2-10)
  and EMA trend signals; avoid body-ratio mono_sign_flip patterns from batch_010'
last_activity: '2026-04-19T13:59:11Z'
members:
- F003
merged_into: null
---
# intraday_price_formation

## Hypothesis

前三个方向（amount_volatility_signal / turnover_structural_signal / value_liquidity_interaction）的 DSL 空间全部撞 `vol_20d` 天花板，且共用 `$amount / $volume / $turnover_rate` 字段空间——这些字段天然与 Barra 波动率因子耦合。

**新字段空间**：`$open / $high / $low / $close` 纯价格数据。OHLCV 日内价格形成关系编码了与成交量无关的信息：
1. **K线身体比**：(close - mid-range) / range — 日内多空力量对比，不依赖成交量
2. **收盘位置**：close 在日内 [low, high] 的相对位置 — 判断日内趋势强度
3. **波动率锚定**：价格变化 Std() / Mean() — 纯价格实现的波动率度量
4. **缺口信号**：open 与前一 close 的关系 — 非连续价格跳空信息

经济直觉：纯 OHLCV 信号与资金流（amount/volume）正交，因为它们只描述价格实现路径，不描述资金规模。

## Current Focus

**新方向首批 batch**：测试 OHLCV-only DSL 候选是否能产生独立于 vol_20d 的 alpha。

## Threads

### T001: 价格形成基础指标 [✗ DISPROVEN batch_011]
**Question**: K线身体比、收盘位置等纯价格指标是否携带独立于流动性因子的 alpha？
**Answer**: F003 隔夜跳空有效，但扩展窗口（C001-C004）+ EMA 变体（C006）全部 reject 或 near_duplicate；C005/C006 与 F003 near_duplicate（corr=0.999）证明 F003 是局部最优。
**Evidence trail**:
- [[batches/batch_010/candidates/C004|batch_010 C004]]: ICIR=0.379 ls_t=8.36 mono=1.0 → **admit → F003 overnight_gap_normalized**
- [[batches/batch_011/candidates/C001|batch_011 C001]]: ic_oos_too_low + mono_sign_flip → reject
- [[batches/batch_011/candidates/C002|batch_011 C002]]: mono_sign_flip → reject
- [[batches/batch_011/candidates/C003|batch_011 C003]]: mono_sign_flip → reject
- [[batches/batch_011/candidates/C004|batch_011 C004]]: ic_oos_too_low + mono_sign_flip → reject
- [[batches/batch_011/candidates/C005|batch_011 C005]]: near_duplicate F003 → reject
- [[batches/batch_011/candidates/C006|batch_011 C006]]: near_duplicate F003 → reject

### T002: 波动率锚定价格信号 [◉ ACTIVE]
**Question**: 价格变化的 Std/Mean 是否产生与 amount CV (F001) 正交的信号？
**Evidence trail**:
- [[batches/batch_010/candidates/C003|batch_010 C003]]: sign_flip + oos_decay → reject
- [[batches/batch_010/candidates/C005|batch_010 C005]]: mono_sign_flip → reject
- [[batches/batch_010/candidates/C006|batch_010 C006]]: mono_sign_flip → reject
- [[batches/batch_011/candidates/C007|batch_011 C007]]: alpha_surv=0.085 + incr_ic=-0.022 (library reducer) → reject
- [[batches/batch_011/candidates/C008|batch_011 C008]]: mono_sign_flip → reject
**Next probes**: 方向 DSL 空间穷尽，需 Python Barra residual 或全新 hypothesis

## Known Failures
- C001 batch_010 `Div(Sub($close, Mean($high, 1)), Sub($high, $low))` — mono_sign_flip
- C002 batch_010 `Div(Sub($close, $low), Sub($high, $low))` — mono_sign_flip
- C003 batch_010 `Div(Sub($close, Ref($close, 1)), Sub($high, $low))` — sign_flip + oos_decay
- C005 batch_010 `Div(Std($close, 20), Mean($close, 20))` — mono_sign_flip
- C006 batch_010 `Div(Sub($close, EMA($close, 5)), EMA($close, 20))` — mono_sign_flip
- C007 batch_010 `Div(Sub($high, $close), Sub($high, $low))` — mono_sign_flip
- C008 batch_010 `Corr($close, $open, 20)` — ic_oos_too_low + mono_sign_flip
- C001 batch_011 `Div(Sub($open, Ref($close, 2)), Mean($high, 2))` — ic_oos_too_low + mono_sign_flip
- C002 batch_011 `Div(Sub($open, Ref($close, 3)), Mean($high, 3))` — mono_sign_flip
- C003 batch_011 `Div(Sub($open, Ref($close, 5)), Mean($high, 5))` — mono_sign_flip
- C004 batch_011 `Div(Sub($open, Ref($close, 2)), Mean($high, 10))` — ic_oos_too_low + mono_sign_flip
- C005 batch_011 `Div(Sub($open, Ref($close, 1)), Mean($high, 5))` — near_duplicate F003（corr=0.999）
- C006 batch_011 `Div(Sub($open, Ref($close, 1)), EMA($high, 5))` — near_duplicate F003（corr=0.999）
- C007 batch_011 `EMA($close, 5)` — CP04 alpha_surv=0.085 + incr_ic=-0.022（库 reducer）+ 负 IC 方向
- C008 batch_011 `Div(Sub($close, EMA($close, 10)), EMA($close, 10))` — mono_sign_flip

## Narrative Log
### 2026-04-19 [[batches/batch_010/judge|batch_010]]
8 候选 → admit=1 (F003 overnight_gap_normalized) / reserve=0 / reject=7。

**Thread 进展**：
- T001: admit C004，隔夜跳空信号有效（ls_t=8.36 + 完美单调 + 9年 IC 全正）；K线身体比/上影线比例/close/open相关性 4/4 mono_sign_flip 失效
- T002: reject C003/C005/C006，波动率锚定类（Std/Mean + EMA 偏差）全部 mono_sign_flip 或 sign_flip

**下一步**：深挖 C004 Ref($close,2-5) + Mean($high,2-10) 窗口变体；避开日内价格比率类

### 2026-04-19 [[batches/batch_011/judge|batch_011]]
8 候选 → admit=0 / reserve=0 / reject=8。方向 status → saturated。

**Thread 进展**：
- T001: **DISPROVEN** — F003 扩展窗口（C001-C004）全部 ic_oos_too_low 或 mono_sign_flip；C005/C006 near_duplicate F003（corr=0.999）
- T002: reject C007/C008 — EMA 趋势信号全部 fail（alpha_surv=0.085 或 mono_sign_flip）

**下一步**：intraday_price_formation DSL 空间穷尽；下一方向需 Python Barra residual 或全新 hypothesis

## Related
- [[lessons#Structural Constraints]]  （市值代理红线 / 向量化约束）
- [[amount_volatility_signal]]  （vol_20d 天花板教训）
