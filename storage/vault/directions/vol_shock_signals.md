---
direction_tag: vol_shock_signals
status: dead
priority: low
rounds: 1
admits: 0
last_batch: batch_024
last_admits: []
last_goal: 首批 3 DSL 候选测 vol shock 信号——今日 range vs 20d baseline、5d vol vs 60d vol regime
  change、Abs 收益 vs 20d baseline。与 F001 (amount CV) 稳态波动正交；测突发性。
last_activity: '2026-04-20T22:11:14Z'
created_batch: batch_024
members: []
retired_members: []
merged_into: null
---
# vol_shock_signals

> [!abstract]+ 方向概要
> **状态**　🔴 dead · priority=low · rounds=1 · admits=0
> **最近**　[[batches/batch_024/judge|batch_024]] · 2026-04-21 · admit=0 / reserve=0 / reject=3
> **一句话**　Magnitude-based vol shock（range / vol-ratio / abs-return）在 A 股 cross-section 全部 collapse 到 vol_20d，不构成独立 alpha；已被跨方向 F001/F301 升格为系统级失败律。

---

## Hypothesis

> [!warning]+ ⚠️ Hypothesis 已证伪（batch_024 · 3/3 reject；F001/F301 升格为系统级）
> **原假设**：**突发** vol 变化（相对于近期基线）反映 information flow shocks；与 F001 (amount CV 稳定性) 正交——F001 测稳态波动幅度，本方向测**突发性**（today vs baseline）。
>
> **证伪证据**：3 个 DSL 候选全部 reject——C001 今日 range / 20d baseline（ls_t=-2.25 borderline + incr_ic=-0.027 库 reducer）；C002 5d/60d returns vol ratio（hard_gate mono_sign_flip，IS=+0.70 / OOS=-1.00 完全反转）；C003 Abs 收益 - 20d baseline（a_surv=0.117 catastrophic，vol_20d-derived）。无论 magnitude normalize 形式是 range / vol ratio / abs return，信号最终都塌缩到 vol_20d rank。
>
> **元教训（已升格为系统级 F001/F301，跨 8 方向 5+ 次独立确认）**：A 股 csi1000 universe 上**任何 magnitude / ratio / power-mean / Std / quantile 形态——无论作用于 return / range / amount / turnover / OHLC ratio 哪个字段——最终都坍缩为 vol_20d 的 monotone derivative**，alpha_survival 通常 < 0.30（典型死区 0.08–0.20）。"突发性 vs 基线"用幅度差或比值构造在本方向已被证伪。后续设计绝对避开 magnitude-only vol 信号；逃离路径仅四条：(a) Python Barra residual 工具链 orthogonalize（受 F010 coverage<0.80 限制）；(b) 非 daily-bar 数据（minute / tick）；(c) 非 magnitude 几何（sign 聚合 / rank-diff cross-family / 严格 mono_is≥0.6 + scale-free RHS 的 higher-moment 单层）；(d) overnight 段独立分解。

---

## Threads

### T001: Magnitude-based vol shock（range / abs return vs baseline） [✗ DISPROVEN batch_024]

> [!failure]+ Thread 结论
> **Question**: 今日 magnitude（range / abs return）相对于 20d baseline 的偏离是否携带 forward IC（"突发幅度"信号）？
> **Evidence trail**:
> - [[batches/batch_024/candidates/C001|batch_024 C001]]　今日 range / 20d mean range → ic=-0.029 ls_t=-2.25 incr_ic=-0.027 库 reducer → reject
> - [[batches/batch_024/candidates/C003|batch_024 C003]]　Abs 收益 - 20d baseline → ic=+0.008 ls_t=2.97 **a_surv=0.117 catastrophic**（vol_20d 衍生）→ reject
>
> **Conclusion**: Magnitude-based vol shock 无论 normalize 形式（range ratio / abs return deviation）都 collapse 到 vol_20d；幅度差 / 幅度比都无独立 alpha。（合并了原 T001 / T003——两者共享 magnitude-vs-baseline 失败根因）

### T002: 5d / 60d vol regime change [✗ DISPROVEN batch_024]

> [!failure]+ Thread 结论
> **Question**: 短窗口 5d vol 相对于长窗口 60d vol 的比值是否 capture regime change 并携带 cross-sectional forward IC？
> **Evidence trail**:
> - [[batches/batch_024/candidates/C002|batch_024 C002]]　5d/60d returns vol ratio → hard_gate mono_sign_flip IS=+0.70 / OOS=-1.00（完全反转）→ reject
>
> **Conclusion**: 短/长窗口 vol ratio 跨期行为不稳——IS/OOS mono 完全反转暴露其本质是 vol regime 的 random walk noise，不是可交易的结构信号。

---

## Known Failures

| Candidate | Expression | Reject Reason |
|---|---|---|
| [[batches/batch_024/candidates/C001\|C001]] | 今日 range / 20d mean range | ls_t=-2.25 borderline + incr_ic=-0.027 库 reducer |
| [[batches/batch_024/candidates/C002\|C002]] | 5d/60d returns vol ratio | hard_gate mono_sign_flip（IS=+0.70 / OOS=-1.00 完全反转）|
| [[batches/batch_024/candidates/C003\|C003]] | Abs 收益 - 20d baseline | **alpha_surv=0.117 catastrophic**（vol_20d-derived 第 4 次独立出现）|

---

## Related

- 🔴 [[amount_volatility_signal]] `dead/saturated` — 测稳态 CV；19/19 候选 dominant_style=vol_20d，是 F301 律的源头数据点
- 🔴 [[return_distribution_signals]] `dead` — 高阶矩 (skew/kurt/qrange) 同样 collapse 到 vol_20d，与本方向共享"magnitude 变换 → vol rank"失败根因
- 🔴 [[quantile_shape_signals]] `dead` — Quantile robust ≠ Barra orthogonal，第 4 次跨方向独立确认 F301
- 🟡 [[stochastic_position]] `saturated` — %K / TsRank 6/6 dominant_style=vol_20d (exposure 8.7–16.5)，同源
- 🟡 [[range_structure]] `exploring` — T002 magnitude/ratio 全败已收窄至 Kurt-only
- 🟡 [[barra_residual_alpha]] `saturated` — vol_20d 为 Barra style 之一，本方向失败本质是 style coupling

---

## Narrative Log

> [!quote]+ 2026-04-25 · Phase 5 consolidation · F001/F301 升格
> Distillation specialists (pattern_analyst F001 + hypothesis_promoter F301) 跨 8 方向 5+ 次独立确认本方向元教训为系统级 vol_20d 吸收律：daily-bar magnitude / ratio / power-mean / quantile / Std 任何变换在 csi1000 cross-section 全部 monotone-equivalent 到 vol_20d rank。Hypothesis ⚠️ 文本已纳入逃离路径四条 (Barra residual / minute-bar / 非 magnitude 几何 / overnight)。本方向维持 dead，未来若再起须先读 F001（lessons.md Structural Constraints "vol_20d 吸收律"），且必须嵌入逃离路径之一；不可在 daily-bar single-series magnitude 空间内 retry。

> [!quote]+ 2026-04-21 · [[batches/batch_024/judge|batch_024]] · 方向封档
> **admit=0 / reserve=0 / reject=3** — 3 候选全 reject：库 reducer / hard_gate mono_sign_flip / vol_20d 衍生 catastrophic alpha_surv。
> - T001+T003 合并为 Magnitude-based vol shock：`[◉ ACTIVE] → [✗ DISPROVEN]`
> - T002 5d/60d vol regime：`[◉ ACTIVE] → [✗ DISPROVEN]`
> - **核心元教训**：magnitude-based vol shock 信号在 A 股 cross-section 全部 collapse 到 vol_20d（第 4 次独立观察，跨 amount_volatility_signal / return_distribution_signals / barra_residual_alpha 多方向确认）。突破须换坐标系（signed return / intraday microstructure / portfolio regime）。
> - **MT budget**: 3 tests，全 reject，无 admit 占预算。
> - **Direction ops**: status `exploring → dead`（不可逆）；priority `low`；不进入 retry pool。
