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

> [!abstract]+ 方向概要
> **状态**　🟡 saturated · priority=high · rounds=4 · admits=2
> **最近**　[[batches/batch_011/judge|batch_011]] · 2026-04-19 · admit=0 / reserve=0 / reject=8
> **成员**　[[../factors/F003|F003]] overnight_gap_normalized
> **一句话**　OHLCV 日内价格形成 DSL 空间穷尽；F003 隔夜跳空是局部最优，扩展窗口/EMA 变体全封闭。

---

## Hypothesis

前三个方向（amount_volatility_signal / turnover_structural_signal / value_liquidity_interaction）的 DSL 空间全部撞 `vol_20d` 天花板，且共用 `$amount / $volume / $turnover_rate` 字段空间——这些字段天然与 Barra 波动率因子耦合。

**新字段空间**：`$open / $high / $low / $close` 纯价格数据。OHLCV 日内价格形成关系编码了与成交量无关的信息：
1. **K线身体比**：(close - mid-range) / range — 日内多空力量对比，不依赖成交量
2. **收盘位置**：close 在日内 [low, high] 的相对位置 — 判断日内趋势强度
3. **波动率锚定**：价格变化 Std() / Mean() — 纯价格实现的波动率度量
4. **缺口信号**：open 与前一 close 的关系 — 非连续价格跳空信息

经济直觉：纯 OHLCV 信号与资金流（amount/volume）正交，因为它们只描述价格实现路径，不描述资金规模。

> [!info]+ 方向饱和说明
> **为何 saturated**：batch_010 admit F003（overnight_gap_normalized），batch_011 针对 F003 做扩展窗口（Ref2-5 × MeanHigh2-10）+ EMA 趋势变体 8 候选全 reject — C001/C002/C003/C004 `mono_sign_flip` 或 `ic_oos_too_low`；C005/C006 `near_duplicate F003`（corr=0.999）证明 F003 是该形状局部最优；C007/C008 EMA 趋势 `alpha_surv=0.085` 或 `mono_sign_flip`。日内 K线身体比/收盘位置/close-open 相关性系统性 `mono_sign_flip`，波动率锚定（Std/Mean）路径 sign_flip + oos_decay。
> **复活条件**：(1) Python Barra residual 路径（跳出 DSL 白名单）；(2) 新 hypothesis 如日内分钟级数据 / intraday seasonality / 隔夜-日内收益分解（见 [[overnight_intraday_split]]）；(3) OHLCV 与其他字段的非显然交互（当前交互已被 value_liquidity / amount_volatility 方向覆盖）。

---

## Threads

### T001: 价格形成基础指标 [✗ DISPROVEN batch_011]

> [!failure]+ Thread 结论
> **Question**: K线身体比、收盘位置等纯价格指标是否携带独立于流动性因子的 alpha？
> **Evidence trail**:
> - [[batches/batch_010/candidates/C004|batch_010 C004]]　ICIR=0.379 ls_t=8.36 mono=1.0 → **admit → [[../factors/F003|F003]] overnight_gap_normalized**
> - [[batches/batch_011/candidates/C001|batch_011 C001]]　ic_oos_too_low + mono_sign_flip → reject
> - [[batches/batch_011/candidates/C002|batch_011 C002]]　mono_sign_flip → reject
> - [[batches/batch_011/candidates/C003|batch_011 C003]]　mono_sign_flip → reject
> - [[batches/batch_011/candidates/C004|batch_011 C004]]　ic_oos_too_low + mono_sign_flip → reject
> - [[batches/batch_011/candidates/C005|batch_011 C005]]　near_duplicate F003（corr=0.999）→ reject
> - [[batches/batch_011/candidates/C006|batch_011 C006]]　near_duplicate F003（corr=0.999）→ reject
>
> **Conclusion**: F003 隔夜跳空有效，但扩展窗口（C001-C004）+ EMA 变体（C006）全部 reject 或 near_duplicate；C005/C006 与 F003 near_duplicate 证明 F003 是局部最优。

### T002: 波动率锚定价格信号 [◉ ACTIVE]

> [!note]+ Thread 进展
> **Question**: 价格变化的 Std/Mean 是否产生与 amount CV (F001) 正交的信号？
> **Evidence trail**:
> - [[batches/batch_010/candidates/C003|batch_010 C003]]　sign_flip + oos_decay → reject
> - [[batches/batch_010/candidates/C005|batch_010 C005]]　mono_sign_flip → reject
> - [[batches/batch_010/candidates/C006|batch_010 C006]]　mono_sign_flip → reject
> - [[batches/batch_011/candidates/C007|batch_011 C007]]　alpha_surv=0.085 + incr_ic=-0.022 (library reducer) → reject
> - [[batches/batch_011/candidates/C008|batch_011 C008]]　mono_sign_flip → reject
>
> **Next probes**: 方向 DSL 空间穷尽，需 Python Barra residual 或全新 hypothesis

---

## Known Failures

| Candidate | Expression | Reject Reason |
|---|---|---|
| [[batches/batch_010/candidates/C001\|batch_010 C001]] | `Div(Sub($close, Mean($high, 1)), Sub($high, $low))` | mono_sign_flip |
| [[batches/batch_010/candidates/C002\|batch_010 C002]] | `Div(Sub($close, $low), Sub($high, $low))` | mono_sign_flip |
| [[batches/batch_010/candidates/C003\|batch_010 C003]] | `Div(Sub($close, Ref($close, 1)), Sub($high, $low))` | sign_flip + oos_decay |
| [[batches/batch_010/candidates/C005\|batch_010 C005]] | `Div(Std($close, 20), Mean($close, 20))` | mono_sign_flip |
| [[batches/batch_010/candidates/C006\|batch_010 C006]] | `Div(Sub($close, EMA($close, 5)), EMA($close, 20))` | mono_sign_flip |
| [[batches/batch_010/candidates/C007\|batch_010 C007]] | `Div(Sub($high, $close), Sub($high, $low))` | mono_sign_flip |
| [[batches/batch_010/candidates/C008\|batch_010 C008]] | `Corr($close, $open, 20)` | ic_oos_too_low + mono_sign_flip |
| [[batches/batch_011/candidates/C001\|batch_011 C001]] | `Div(Sub($open, Ref($close, 2)), Mean($high, 2))` | ic_oos_too_low + mono_sign_flip |
| [[batches/batch_011/candidates/C002\|batch_011 C002]] | `Div(Sub($open, Ref($close, 3)), Mean($high, 3))` | mono_sign_flip |
| [[batches/batch_011/candidates/C003\|batch_011 C003]] | `Div(Sub($open, Ref($close, 5)), Mean($high, 5))` | mono_sign_flip |
| [[batches/batch_011/candidates/C004\|batch_011 C004]] | `Div(Sub($open, Ref($close, 2)), Mean($high, 10))` | ic_oos_too_low + mono_sign_flip |
| [[batches/batch_011/candidates/C005\|batch_011 C005]] | `Div(Sub($open, Ref($close, 1)), Mean($high, 5))` | near_duplicate F003（corr=0.999）|
| [[batches/batch_011/candidates/C006\|batch_011 C006]] | `Div(Sub($open, Ref($close, 1)), EMA($high, 5))` | near_duplicate F003（corr=0.999）|
| [[batches/batch_011/candidates/C007\|batch_011 C007]] | `EMA($close, 5)` | CP04 alpha_surv=0.085 + incr_ic=-0.022（库 reducer）+ 负 IC 方向 |
| [[batches/batch_011/candidates/C008\|batch_011 C008]] | `Div(Sub($close, EMA($close, 10)), EMA($close, 10))` | mono_sign_flip |

---

## Related

- 📖 [[lessons#Structural Constraints]] — 市值代理红线 / 向量化约束
- 🟡 [[amount_volatility_signal]] `saturated` — vol_20d 天花板教训（本方向在 OHLCV 字段空间重演同类饱和）
- 🔵 [[overnight_intraday_split]] — 隔夜-日内分解维度，F003 所在生态位的横向延伸

---

## Narrative Log

> [!quote]+ 2026-04-19 · [[batches/batch_010/judge|batch_010]]
> **admit=1 / reserve=0 / reject=7** — F003 overnight_gap_normalized 入库（ls_t=8.36 + 完美单调 + 9年 IC 全正）。
> - T001 价格形成基础指标：admit C004 隔夜跳空信号有效；K线身体比 / 上影线比例 / close-open 相关性 4/4 `mono_sign_flip` 失效
> - T002 波动率锚定价格信号：reject C003/C005/C006，Std/Mean + EMA 偏差类全部 `mono_sign_flip` 或 `sign_flip`
> - **下一步**：深挖 C004 Ref($close,2-5) + Mean($high,2-10) 窗口变体；避开日内价格比率类

> [!quote]+ 2026-04-19 · [[batches/batch_011/judge|batch_011]]
> **admit=0 / reserve=0 / reject=8** — 方向 status → saturated。
> - T001 价格形成基础指标：**DISPROVEN** — F003 扩展窗口（C001-C004）全部 `ic_oos_too_low` 或 `mono_sign_flip`；C005/C006 `near_duplicate F003`（corr=0.999）
> - T002 波动率锚定价格信号：reject C007/C008 — EMA 趋势信号全部 fail（`alpha_surv=0.085` 或 `mono_sign_flip`）
> - **下一步**：intraday_price_formation DSL 空间穷尽；下一方向需 Python Barra residual 或全新 hypothesis
