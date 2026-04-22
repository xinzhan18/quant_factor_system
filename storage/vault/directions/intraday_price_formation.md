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
> **一句话**　OHLCV 纯价格 DSL 空间穷尽；F003 隔夜跳空是唯一局部最优，日内身体比 / 收盘位置 / 波动率锚定 / EMA 变体系统性 `mono_sign_flip`。

---

## Hypothesis

> [!warning]+ Hypothesis · ⚠️ 部分证伪
> **原假设**：`$open/$high/$low/$close` 纯价格信号与资金流（amount/volume）正交，可避开前三个方向撞到的 `vol_20d` 天花板。四条路径：(1) K线身体比；(2) 收盘位置；(3) 波动率锚定 Std/Mean；(4) 缺口信号。
>
> **证伪信号（≥3）**：
> 1. 日内价格比率类（身体比 / 收盘位置 / 上影线比 / close-open Corr）系统性 `mono_sign_flip` — 日内多空在中长期持有中对称抵消
> 2. 波动率锚定 Std/Mean 路径 `sign_flip + oos_decay` — 与 amount CV 同源，未逃脱 vol_20d 耦合
> 3. EMA 趋势（close 相对 EMA 偏差 / EMA 本身）`alpha_surv=0.085 + incr_ic=-0.022` — 单均线已被库内因子覆盖
>
> **存活部分**：隔夜缺口（open 对前 close 的跳空）——F003 入库后扩展窗口（Ref2-5 × MeanHigh2-10）全 reject，`corr=0.999` near_duplicate 证明 F003 是该形状**唯一局部最优**。

---

## Threads

### T001: 价格形成基础指标 [✗ DISPROVEN]

> [!failure]+ Thread 结论
> **Question**: K线身体比 / 收盘位置 / 日内价格比率是否携带独立于流动性的 alpha？
> **Evidence trail**:
> - [[batches/batch_010/candidates/C004|b010 C004]]　ICIR=0.379 · ls_t=8.36 · mono=1.0 → **admit [[../factors/F003|F003]]**
> - b010 C001/C002/C007/C008（身体比 / 收盘位置 / 上影线 / close-open Corr）→ 4/4 `mono_sign_flip`
> - [[batches/batch_011/candidates/C001|b011 C001-C004]]　F003 扩展窗口（Ref2-5 × MeanHigh2-10）→ `ic_oos_too_low / mono_sign_flip`
> - [[batches/batch_011/candidates/C005|b011 C005]] / [[batches/batch_011/candidates/C006|C006]]　`near_duplicate F003`（corr=0.999）
>
> **Conclusion**: 除隔夜缺口外全线失效；F003 是该形状局部最优，扩展空间关闭。

### T002: 波动率锚定 + EMA 趋势 [✗ DISPROVEN]

> [!failure]+ Thread 结论
> **Question**: 价格 Std/Mean 或 EMA 趋势是否与 amount CV (F001) 正交？
> **Evidence trail**:
> - [[batches/batch_010/candidates/C003|b010 C003]]　`sign_flip + oos_decay`
> - [[batches/batch_010/candidates/C005|b010 C005]] / [[batches/batch_010/candidates/C006|C006]]　Std/Mean + EMA 偏差 `mono_sign_flip`
> - [[batches/batch_011/candidates/C007|b011 C007]]　`alpha_surv=0.085 + incr_ic=-0.022`（库 reducer）
> - [[batches/batch_011/candidates/C008|b011 C008]]　`mono_sign_flip`
>
> **Conclusion**: 价格实现波动率与资金波动率同源，非正交维度；单 EMA 偏差已被库内信号覆盖。

---

## Lessons Upgraded

- **日内对称抵消默认律**：K线身体比 / 收盘位置 / close-open Corr 等日内价格比率类，`mono_sign_flip` 是默认失效模式——日内多空力量在中长期持有中对称抵消。
- **corr=0.999 near_duplicate 信号**：扩展窗口候选与已入库因子近乎完全相关，即证该形状唯一最优，关闭同形状变体搜索空间。
- **Std/Mean 与 amount CV 同源**：价格实现波动率不构成与资金流正交的新字段空间。

---

## Known Failures

| Candidate | Expression | Reject Reason |
|---|---|---|
| [[batches/batch_010/candidates/C001\|b010 C001]] | `Div(Sub($close, Mean($high,1)), Sub($high,$low))` | mono_sign_flip |
| [[batches/batch_010/candidates/C002\|b010 C002]] | `Div(Sub($close,$low), Sub($high,$low))` | mono_sign_flip |
| [[batches/batch_010/candidates/C003\|b010 C003]] | `Div(Sub($close,Ref($close,1)), Sub($high,$low))` | sign_flip + oos_decay |
| [[batches/batch_010/candidates/C005\|b010 C005]] | `Div(Std($close,20), Mean($close,20))` | mono_sign_flip |
| [[batches/batch_010/candidates/C006\|b010 C006]] | `Div(Sub($close,EMA($close,5)), EMA($close,20))` | mono_sign_flip |
| [[batches/batch_010/candidates/C007\|b010 C007]] | `Div(Sub($high,$close), Sub($high,$low))` | mono_sign_flip |
| [[batches/batch_010/candidates/C008\|b010 C008]] | `Corr($close,$open,20)` | ic_oos_too_low + mono_sign_flip |
| [[batches/batch_011/candidates/C001\|b011 C001]] | `Div(Sub($open,Ref($close,2)), Mean($high,2))` | ic_oos_too_low + mono_sign_flip |
| [[batches/batch_011/candidates/C002\|b011 C002]] | `Div(Sub($open,Ref($close,3)), Mean($high,3))` | mono_sign_flip |
| [[batches/batch_011/candidates/C003\|b011 C003]] | `Div(Sub($open,Ref($close,5)), Mean($high,5))` | mono_sign_flip |
| [[batches/batch_011/candidates/C004\|b011 C004]] | `Div(Sub($open,Ref($close,2)), Mean($high,10))` | ic_oos_too_low + mono_sign_flip |
| [[batches/batch_011/candidates/C005\|b011 C005]] | `Div(Sub($open,Ref($close,1)), Mean($high,5))` | near_duplicate F003 (corr=0.999) |
| [[batches/batch_011/candidates/C006\|b011 C006]] | `Div(Sub($open,Ref($close,1)), EMA($high,5))` | near_duplicate F003 (corr=0.999) |
| [[batches/batch_011/candidates/C007\|b011 C007]] | `EMA($close,5)` | alpha_surv=0.085 + incr_ic=-0.022 |
| [[batches/batch_011/candidates/C008\|b011 C008]] | `Div(Sub($close,EMA($close,10)), EMA($close,10))` | mono_sign_flip |

---

## Revival Conditions

1. **Python Barra residual 路径**（跳出 DSL 白名单，剥离市值/波动率暴露后再测价格形状）
2. **隔夜-日内收益分解**（见 [[overnight_intraday_split]]）——F003 生态位横向延伸
3. **日内分钟 / tick 数据**引入（当前日频 OHLCV 已穷尽）
4. OHLCV 与其他字段的**非显然交互**（需避开 value_liquidity / amount_volatility 已覆盖区）

---

## Related

- 📖 [[lessons#Structural Constraints]] — 市值代理红线 / 向量化约束
- 🟡 [[amount_volatility_signal]] `saturated` — vol_20d 天花板教训，本方向在 OHLCV 字段重演
- 🔵 [[overnight_intraday_split]] — F003 隔夜缺口的横向延伸生态位

---

## Narrative Log

> [!quote]+ 2026-04-19 · [[batches/batch_010/judge|batch_010]] · admit=1 reject=7
> F003 overnight_gap_normalized 入库（ls_t=8.36 · 完美单调 · 9 年 IC 全正）。T001 身体比 / 收盘位置 / close-open Corr 4/4 `mono_sign_flip`；T002 Std/Mean + EMA 偏差全部 `sign_flip`。

> [!quote]+ 2026-04-19 · [[batches/batch_011/judge|batch_011]] · admit=0 reject=8 → saturated
> T001 F003 扩展窗口全 reject；C005/C006 `corr=0.999` 证 F003 局部最优。T002 EMA 趋势 `alpha_surv=0.085` 或 `mono_sign_flip`。**方向 DSL 空间穷尽**，待 Python Barra residual 或隔夜-日内分解新 hypothesis 复活。
