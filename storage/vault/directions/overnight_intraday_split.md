---
direction_tag: overnight_intraday_split
status: saturated
priority: high
rounds: 3
admits: 3
last_batch: batch_027
last_admits: []
last_goal: 'Round 3: intraday return 5d/3d mean mirror of F010/F011 overnight。测 intraday
  段是否与 overnight 段正交、产独立 alpha；若 admit，overnight+intraday 两段同时入库形成完整分解。'
last_activity: '2026-04-21T16:40:05Z'
created_batch: batch_025
members:
- F009
- F010
- F011
retired_members: []
merged_into: null
---
# overnight_intraday_split

> [!abstract]+ 方向概要
> 🟡 **saturated** · 3 rounds · 3 admits — overnight 家族 4 slot（F003 / F007 / F009 / F010）达 bloat 上限；intraday 镜像被 F009 数学结构吸收（corr 0.65-0.89@F009），无独立信息可挖。
> **Members**: [[F009]] overnight_intraday_spread_5d · [[F010]] overnight_return_persistence_5d · [[F011]] overnight_return_persistence_3d

---

## Hypothesis

> [!success]+ 已验证（partial）
> 分解 daily return 为 **overnight** ((open-prev_close)/prev_close) 与 **intraday** ((close-open)/open) 两段，驱动因子不同：overnight = 隔夜消息 + 机构 pre-market；intraday = 日内散户 + 算法。**Aggregation 形式（spread / persistence）在 cross-section 上携带独立 alpha**——batch_025 DOUBLE ADMIT 打破整库 ls_t 记录（F010 ls_t=7.50）。
>
> **已封闭**：correlation 形式不稳（sign_flip）；pure intraday 镜像冗余（F009 = overnight - intraday 已隐式吸收 intraday 分量）。
>
> **复活条件**：
> - **新字段**：minute-bar session 分解（open auction / midday / close auction）突破 daily 二分
> - **更长 horizon**：20d+ overnight persistence 是否仍独立于 5d 版本
> - **正交 aggregation**：overnight sign frequency（方向而非 magnitude）、overnight × intraday 非线性交互

---

## Threads

### T001 · overnight aggregation (spread + persistence) [✓ ANSWERED batch_025]

> [!success]+ 机制确认：overnight 段独立 alpha 已吸收
> **Question**: overnight return 与 intraday return 的 spread / 各自 aggregation 是否携带独立于现有 OHLCV 的 persistent alpha？
> **Answer**: 是。overnight 段在 cross-section 上独立于 intraday；spread 与 pure overnight persistence 两种 aggregation 均有效。
> **Evidence trail**:
> - [[batches/batch_025/candidates/C001|batch_025 C001]]: spread 5d → ic=+0.047 ls_t=5.18 mono=+1.00 incr=+0.044 corr=0.708@F007 → **admit → [[F009]]**
> - [[batches/batch_025/candidates/C002|batch_025 C002]]: 5d overnight persistence → ic=+0.024 **ls_t=7.50（整库记录）** mono=+1.00 incr=+0.019 corr=0.424@F003 → **admit → [[F010]]**

---

### T002 · overnight-intraday correlation [✗ DISPROVEN batch_025]

> [!failure]+ 机制封闭：correlation 形式不稳定
> **Question**: 20d Corr(overnight, intraday) 是否在 cross-section 上提供稳健预测力？
> **Answer**: 否。correlation 形式 sign_flip，无 cross-section 稳定性。
> **Evidence trail**:
> - [[batches/batch_025/candidates/C003|batch_025 C003]]: 20d Corr → hard_gate sign_flip train +0.005 / val -0.006 → **reject**

---

### T003 · intraday 镜像 aggregation [✗ DISPROVEN batch_027]

> [!failure]+ 机制封闭：F009 已吸收 intraday 分量
> **Question**: intraday return 5d/3d mean（镜像 F010/F011 的 overnight aggregation）是否携带独立于 F009 spread 的 alpha？
> **Answer**: 否。F009 = overnight - intraday 的数学结构已吸收 intraday 分量——pure intraday 是 (overnight - F009) 的线性组合，无独立信息。3/3 reject。
> **Evidence trail**:
> - [[batches/batch_027/candidates/C001|batch_027 C001]]: 5d intraday mean → corr 0.65-0.89@F009 + incr_ic 负 → **reject**
> - [[batches/batch_027/candidates/C002|batch_027 C002]]: 3d intraday mean → corr 0.65-0.89@F009 + incr_ic 负 → **reject**
> - [[batches/batch_027/candidates/C003|batch_027 C003]]: volume-weighted intraday → corr 0.65-0.89@F009 + incr_ic 负 → **reject**

---

### T004 · overnight / intraday ratio [◉ SUSPENDED]

> [!note]+ 未测，方向 saturated 搁置
> **Question**: overnight/intraday ratio（非 spread 非 correlation 的第三种函数形式）是否携带独立信号？
> **Evidence trail**: 未测。复活需配合新字段或更长 horizon，单独此 thread 不足以改 saturated 状态。

---

## Known Failures

| Batch | Candidate | Pattern | 原因 |
|---|---|---|---|
| batch_025 | C003 | 20d Corr(overnight, intraday) | hard_gate sign_flip train +0.005 / val -0.006 |
| batch_027 | C001 | 5d intraday mean | corr 0.65-0.89@F009 + incr_ic 负（F009 已吸收 intraday 分量）|
| batch_027 | C002 | 3d intraday mean | 同上 |
| batch_027 | C003 | volume-weighted intraday | 同上 |

---

## Lessons (升格)

- **数学结构吸收律**：当 F_parent = A - B 被 admit 后，pure A / pure B 的镜像 aggregation 会是 parent 的线性组合，corr 必然高 → **先跑代数展开检查，再决定是否生成镜像候选**。
- **aggregation > correlation**：cross-section 稳健性上，aggregation（spread / persistence / mean）优于 Corr(.,.,N)；本方向 correlation 1/1 sign_flip，相关形式需审慎上排。
- **家族 bloat 上限**：overnight 家族 4 slot（F003 / F007 / F009 / F010）已覆盖主信号；同 horizon 继续挖掘 ROI 极低。

---

## Related

- 🟢 [[intraday_price_formation]] (productive) — F003 overnight gap admit，本方向 overnight 段的上游字段依赖
- 🟡 [[ohlc_temporal_aggregation]] (saturated) — F007 open-position admit，与 F009 spread corr=0.708

---

## Narrative Log

> [!quote]- 2026-04-21 [[batches/batch_025/judge|batch_025]] · exploring → productive (DOUBLE ADMIT 首批)
> admit=2 / reject=1。C001 admit → [[F009]] overnight_intraday_spread_5d (ic=+0.047, ls_t=5.18, incr=+0.044)；C002 admit → [[F010]] overnight_return_persistence_5d (ic=+0.024, **ls_t=7.50 整库最强**)；C003 reject — 20d 相关性 sign_flip。核心发现：overnight 段携带独立于 intraday 的 persistent signal；aggregation 有效，correlation 不稳。

> [!quote]+ 2026-04-21 [[batches/batch_027/judge|batch_027]] · productive → saturated
> admit=0 / reject=3。Intraday 镜像 3/3 reject（5d/3d/volume-weighted），全部 corr 0.65-0.89@F009 + incr_ic 负。**定论**：F009 = overnight - intraday 的数学结构已吸收 intraday 分量，pure intraday 是 (overnight - F009) 的线性组合。overnight 家族 4 slot 达 bloat 上限，方向 saturated。
