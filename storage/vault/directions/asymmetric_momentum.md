---
direction_tag: asymmetric_momentum
status: dead
priority: medium
rounds: 1
admits: 0
last_batch: batch_028
last_admits: []
last_goal: '首批 3 候选测 up/down return 分解: 5d mean down-only, 5d mean up-only, 两者比值。测是否携独立
  alpha。'
last_activity: '2026-04-21T16:40:05Z'
created_batch: batch_028
members: []
retired_members: []
merged_into: null
---

# asymmetric_momentum

> [!abstract]+ 方向概要
> - **状态**　🔴 `dead` · priority `medium` · rounds = 1 · admits = 0
> - **最近**　[[batches/batch_028/judge|batch_028]] · 2026-04-21 · 0 admit / 0 reject = 3
> - **一句话**　up/down return 分解 3/3 hard_gate 全挂——sign-conditional daily 拆分在 OOS 完全反转，证伪 loss-aversion cross-section edge

---

## Hypothesis

> [!warning]+ Hypothesis 已证伪（batch_028）
> **原假设**　分解 5d return 为 up-days 与 down-days 两段，down-only 侧因 loss aversion / disposition effect（散户 sit on losses）更 informative。
>
> **证伪证据**　3 角度（down-only / up-only / abs(down)÷up）3/3 `hard_gate` 挂 `sign_flip` 或 `mono_sign_flip`——**IS 显著的方向在 OOS 完全反转**，与 regime noise 无法区分。
>
> **升格经验**　**sign-conditional daily return 拆分** 在 daily 频率天然放大 regime 敏感度；无条件聚合（对照：F010 `overnight_return_persistence_5d` ls_t = ==7.50== 整库最强）才稳定。后续 direction 设计应避开任何基于 daily return 正负号的条件拆分。

---

## Threads

### T001: Sign-conditional return decomposition [✗ DISPROVEN batch_028]

> [!failure]+ Thread 结论
> **Question**: 5d up-only / down-only / abs(down)÷up 三种 sign-conditional 聚合，是否携独立 forward IC 且 IS/OOS 方向一致？
>
> **Evidence trail**:
> - [[batches/batch_028/candidates/C001|C001]]　5d down-only mean → `sign_flip` train ==−0.004== / val ==+0.017== → reject
> - [[batches/batch_028/candidates/C002|C002]]　5d up-only mean → `mono_sign_flip` IS ==+0.70== / OOS ==−0.60== → reject
> - [[batches/batch_028/candidates/C003|C003]]　abs(down)/up ratio 5d → `mono_sign_flip` IS ==−0.70== / OOS ==+0.60== → reject
> - **结构结论**　3 角度同时挂 ≠ 单点失败：问题在 conditional aggregation 本身，而非算子实现

---

## Known Failures

| Candidate | Expression | Reject Reason |
|---|---|---|
| [[batches/batch_028/candidates/C001\|C001]] | 5d down-only mean | `sign_flip` train −0.004 / val +0.017 |
| [[batches/batch_028/candidates/C002\|C002]] | 5d up-only mean | `mono_sign_flip` IS +0.70 / OOS −0.60 |
| [[batches/batch_028/candidates/C003\|C003]] | abs(down) / up ratio | `mono_sign_flip` IS −0.70 / OOS +0.60 |

---

## Related

- 🟡 [[overnight_intraday_split]] `saturated` — 无条件聚合路径成功（F010 ls_t = 7.50），反例对照
- 🟡 [[ohlc_temporal_aggregation]] `saturated`
- 🔴 [[return_momentum_acceleration]] `dead` — return 变化率亦失败，同族教训

---

## Narrative Log

> [!quote]+ 2026-04-21 · [[batches/batch_028/judge|batch_028]] — 首批即 dead
> - admit 0 / reject 3；C001/C002/C003 全 `hard_gate`（sign / mono 反转）
> - MT budget　cumulative 128 → **131** · direction 0 → **3** · bucket `low`
> - `status: exploring → dead` · priority `medium`（保留供 meta 教训引用）
