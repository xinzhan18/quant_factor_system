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
> - **最近**　[[batches/batch_028/judge|batch_028]] · 2026-04-21 · 0 admit / 0 reserve / 3 reject
> - **一句话**　up/down return 分解 3/3 hard_gate 失败——IS/OOS `sign/mono` 反转证伪 loss aversion cross-section edge

---

## Hypothesis

分解 5d return 为 up-days 和 down-days 两段，测各自对 forward return 的预测力。

**文献依据**：up-down 不对称反映 loss aversion / disposition effect——散户倾向 sit on losses（不卖跌）→ down-day returns 更 informative。

> [!warning] ⚠️ Hypothesis 已证伪（batch_028）
> 3 角度（down-only / up-only / ratio）全挂 `hard_gate sign_flip` 或 `mono_sign_flip`——**IS 有效的方向在 OOS 完全反转**。
>
> **元教训**　条件拆分（`If` + sign 过滤）在 daily 频率天然放大 regime 敏感度；无条件聚合（例：F010 `overnight_return_persistence_5d`，ls_t = ==7.50== 整库最强）反而更稳。后续 direction 设计应避开 **sign-conditional** daily return 拆分。

---

## Threads

### T001: Down-only / asymmetry ratio momentum [✗ DISPROVEN batch_028]

> [!failure]+ Thread 结论
> **Question**: 5d mean down-only return（以及 abs(down)/up 不对称比值）是否携带 forward IC 且 IS/OOS 方向一致？
>
> **Evidence trail**:
> - [[batches/batch_028/candidates/C001|batch_028 C001]]　5d down-only mean → `hard_gate sign_flip` (train ==-0.004== / val ==+0.017==) → **reject**
> - [[batches/batch_028/candidates/C003|batch_028 C003]]　abs(down)/up ratio 5d → `hard_gate mono_sign_flip` IS ==-0.70== / OOS ==+0.60== → **reject**

### T002: Up-only momentum [✗ DISPROVEN batch_028]

> [!failure]+ Thread 结论
> **Question**: 5d mean up-only return 是否独立于全段 return 提供 cross-section alpha？
>
> **Evidence trail**:
> - [[batches/batch_028/candidates/C002|batch_028 C002]]　5d up-only mean → `hard_gate mono_sign_flip` IS ==+0.70== / OOS ==-0.60== → **reject**

---

## Known Failures

| Candidate | Expression | Reject Reason |
|---|---|---|
| [[batches/batch_028/candidates/C001\|C001]] | 5d down-only mean | `sign_flip` train -0.004 / val +0.017 |
| [[batches/batch_028/candidates/C002\|C002]] | 5d up-only mean | `mono_sign_flip` IS +0.70 / OOS -0.60 |
| [[batches/batch_028/candidates/C003\|C003]] | abs(down) / up ratio | `mono_sign_flip` IS -0.70 / OOS +0.60 |

---

## Related

- 🟡 [[overnight_intraday_split]] `saturated` — overnight 段**无条件聚合**成功（F010 ls_t = 7.50）
- 🟡 [[ohlc_temporal_aggregation]] `saturated`
- 🔴 [[return_momentum_acceleration]] `dead` — return rate 变化率亦失败

---

## Narrative Log

> [!quote]+ 2026-04-21 · [[batches/batch_028/judge|batch_028]]
> **首批即 dead** · admit = 0 / reserve = 0 / reject = 3
>
> - C001 / C002 / C003 全 hard_gate 挂：3 角度一次性暴露 IS/OOS `sign` 或 `mono` 反转。
> - 三角度同时失败的**结构意义**大于单独失败：问题在 conditional aggregation 本身，而非算子实现。
> - MT budget　cumulative 128 → **131** · direction 0 → **3** · bucket `low`
>
> **Operations**　`status: exploring → dead` · `priority: medium`（保留供 meta 教训引用）
