---
direction_tag: return_momentum_acceleration
status: dead
priority: medium
rounds: 1
admits: 0
last_batch: batch_029
last_admits: []
last_goal: 3 候选测 return momentum delta / ratio 信号。与 fundamental_momentum (rate 形式失败)
  对照；这里是价格 return 非 fundamental ratios。
last_activity: '2026-04-21T16:40:05Z'
created_batch: batch_029
members: []
retired_members: []
merged_into: null
---
# return_momentum_acceleration

> [!abstract]+ 方向概要
> **状态**　🔴 dead · priority=medium · rounds=1 · admits=0
> **最近**　[[batches/batch_029/judge|batch_029]] · 2026-04-21 · admit=0 / reserve=0 / reject=3
> **一句话**　price return 的 rate/delta/ratio 形式在 csi1000 不携稳定 alpha；首批 3/3 全 weak 或 mono_sign_flip，方向封闭，已升格为系统级 lesson（rate-form structural failure 第 5 例）。

---

## Hypothesis

> [!warning]+ ⚠️ Hypothesis 已证伪（batch_029）→ 已升格 [[lessons|系统级 lesson]]（F300）
> **原假设**　Return momentum（mean return over window）变化率携带 alpha——加速（慢→快 momentum）vs 减速反映资金流变化。三条路径：5d-20d spread（近端加速）、5d/20d ratio（相对强度）、Delta(5d mean, 5)（二阶变化）。与 fundamental_momentum（PE/PB/PS rate 形式已全 reject）对照，验证 rate 失败是 fundamental-specific 还是更普适的 structural failure。
>
> **证伪结果**　3/3 DSL 候选全 reject：C001 spread ls_t=-0.81 + mono=-0.40 + incr_ic=-0.020 库 reducer；C002 ratio CP01 hard_gate **mono_sign_flip** IS=+0.70/OOS=-0.70 彻底不稳定；C003 Δ5d of 5d mean ls_t=-0.49 近随机 + mono=-0.30。与 fundamental_momentum 同源——**rate/delta 形式对信号稳定性不利**，level/mean 保留更多可用结构（F010 hhi_vol_20 level ls_t=7.50 对照）。
>
> **系统级元教训（F300 升格）**　第 5 次观察 **rate/delta/ratio form 失败**（fundamental_momentum / return_distribution_signals / liquidity_acceleration / asymmetric_momentum / 本方向）→ **一阶/二阶 rate-of-change 在 A 股 csi1000 cross-section 不携稳定 alpha**。Phase 1 设计含"变化率 / 加速度 / ratio / 拆分聚合"形式时**默认跳过**；若必须用，先做 Python residualization 检查 coverage 是否 ≥ 0.80。例外仅限：(a) rank-diff `Sub(CsRank, CsRank)` 对偶几何（不是 rate）；(b) `Div(Delta(X), X)` 仅作 rank-order sanity check 且预期 ls_t < 2。

---

## Threads

> [!failure]+ T001 · Return momentum 变化率 [✗ DISPROVEN batch_029]
> **Question**: 5d/20d return momentum 的 spread / ratio / delta 是否携带独立 forward IC？
> **Evidence trail**:
> - [[batches/batch_029/candidates/C001|batch_029 C001]]　`Sub(Mean(ret,5), Mean(ret,20))` → ic=-0.023 ls_t=-0.81 mono=-0.40 corr=0.499@F006 incr=-0.020 → reject（ls_t<1 + 库 reducer）
> - [[batches/batch_029/candidates/C002|batch_029 C002]]　`Div(Mean(ret,5), Abs(Mean(ret,20))+ε)` → **CP01 mono_sign_flip** IS=+0.70 / OOS=-0.70 → reject（方向性翻转）
> - [[batches/batch_029/candidates/C003|batch_029 C003]]　`Delta(Mean(ret,5), 5)` → ic=-0.020 ls_t=-0.49 mono=-0.30 incr=-0.018 → reject（ls_t 近随机）
>
> **Conclusion**: 三种变体（差 / 比 / delta）全 weak；F010 hhi_vol_20 level 形式 ls_t=7.50 对照印证 rate 形式本身是 structural failure，非窗口/字段选择问题。

---

## Known Failures

| Candidate | Expression | Reject Reason |
|---|---|---|
| [[batches/batch_029/candidates/C001\|C001]] | 5d-20d return spread | ls_t=-0.81 weak + mono=-0.40 + incr_ic=-0.020 库 reducer + corr=0.499@F006 |
| [[batches/batch_029/candidates/C002\|C002]] | 5d/20d return ratio | **CP01 hard_gate mono_sign_flip** IS=+0.70 / OOS=-0.70（方向不稳定） |
| [[batches/batch_029/candidates/C003\|C003]] | Δ5d of 5d return mean | ls_t=-0.49 catastrophic weak + mono=-0.30 + incr_ic=-0.018 |

---

## Related

- 🔴 [[fundamental_momentum]] `dead` — 同源失败：PE/PB/PS 纯变化率 ls_t -1.22 到 -1.81 全 weak；rate 形式通用失败
- 🔴 [[asymmetric_momentum]] `dead` — up-only / down-only return 分解全 reject，另一 return 结构变体证伪
- 🔴 [[return_distribution_signals]] `dead` — return 分布类 rate-form 同样全证伪
- 🔴 [[liquidity_acceleration]] `dead` — turnover ratio / 变化率全 reject，liquidity 侧 rate form 失败
- 🔴 [[pv_covariance]] `dead` — Cov 形态归簇 F001/F009/F012 反转载体，rate-form 第 6 例延伸
- 🟡 [[overnight_intraday_split]] `saturated` — overnight/intraday 时段分解，与本方向"时间尺度差"机制邻近

---

## Narrative Log

> [!quote]+ 2026-04-21 · [[batches/batch_029/judge|batch_029]]
> admit=0 / reserve=0 / reject=3 — 首批 3 候选全证伪并封闭方向：C001 spread ls_t=-0.81；C002 ratio CP01 mono_sign_flip；C003 Δ5d of 5d mean ls_t=-0.49。
> - T001: `[◉ ACTIVE] → [✗ DISPROVEN]`
> - 核心元教训：第 5 次 rate/delta form 失败（fundamental_momentum / return_distribution / liquidity_acceleration / asymmetric_momentum / 本 batch）→ 系统级 lesson（F300 已升格至 lessons.md `Structural Constraints`）。
> - Level vs rate 对比：F010 level ls_t=7.50 vs C001 rate ls_t=-0.81。
> - MT budget：消耗 3 tests（134 cum / 3 per-dir），全 reject 不占 admit 预算。
> - Direction ops：status `exploring → dead`（不可逆）；priority=medium 不下调；不进入 retry pool。
