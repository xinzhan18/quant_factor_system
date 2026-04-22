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
> 🟡 **saturated** — 3 rounds, 3 admits (F009 overnight_intraday_spread_5d / F010 overnight_return_persistence_5d / F011)。overnight 家族 4 slot 达 bloat 上限；intraday 镜像被 F009 数学结构吸收，无独立信息。

---

## Hypothesis

分解 daily return 为 overnight ((open-prev_close)/prev_close) 和 intraday ((close-open)/open) 两段，两段受不同参与者驱动：overnight = 隔夜消息 + 机构 pre-market 决策；intraday = 日内散户 + 算法交易。**两段的 cross-sectional rotation 可能正交**——持续 overnight 强但 intraday 弱 vs 反之，预测不同 forward return 结构。

F003 已覆盖 overnight gap magnitude；F007 open-position 部分关联；但**两段 return 的 spread / ratio / correlation 未测**。

> [!info]+ 方向饱和说明
> **ROI 低的原因**：overnight 段 aggregation（spread + 5d persistence）已在 batch_025 一次 DOUBLE ADMIT 吸收主信号；batch_027 intraday 镜像 3/3 reject，corr 0.65-0.89 @F009——**F009 = overnight - intraday 的数学结构已隐式吸收 intraday 分量**，pure intraday 是 overnight - F009 的线性组合，无独立信息。overnight 家族 4 slot（含 F003/F007/F009/F010）达 bloat 上限。
> **复活条件**：
> - 新字段：引入 minute-bar 内的 session-level 分解（open auction / midday / close auction）突破 daily overnight/intraday 二分
> - 更长 horizon：测 20d+ overnight persistence 是否仍独立于 5d 版本
> - 正交 aggregation：overnight sign frequency（方向而非 magnitude）、overnight × intraday 交互项的非线性形式

---

## Threads

### T001: overnight - intraday spread + aggregation [✓ ANSWERED batch_025]

> [!success]+ 机制确认：overnight 段独立 alpha 已吸收
> **Question**: overnight return 与 intraday return 的 spread（或各自 aggregation）是否在 cross-section 携带独立于现有 OHLCV 信号的 persistent alpha？
> **Answer**: 是。overnight 段在 cross-section 上独立于 intraday 信号；spread 与 pure overnight 两种 aggregation 均有效，ls_t=7.50 (C002) 打破整库记录。
> **Evidence trail**:
> - [[batches/batch_025/candidates/C001|batch_025 C001]]: overnight-intraday spread 5d → ic=+0.047 ls_t=5.18 mono=+1.00 incr=+0.044 corr=0.708@F007 → **admit → overnight_intraday_spread_5d (F009)**
> - [[batches/batch_025/candidates/C002|batch_025 C002]]: 5d overnight return persistence → ic=+0.024 ls_t=7.50 mono=+1.00 incr=+0.019 corr=0.424@F003 → **admit → overnight_return_persistence_5d (F010)**

---

### T002: overnight / intraday ratio [◉ ACTIVE]

> [!note]+ 未测机制：ratio 形式未验证
> **Question**: overnight/intraday ratio（非 spread 非 correlation 的第三种函数形式）是否携带独立信号？
> **Evidence trail**:
> - 未测，留给 batch_026（方向已 saturated，本 thread 实际搁置）

---

### T003: overnight-intraday correlation [✗ DISPROVEN batch_025]

> [!failure]+ 机制封闭：correlation 形式不稳定
> **Question**: 20d Corr(overnight, intraday) 是否在 cross-section 上提供稳健的预测力？
> **Evidence trail**:
> - [[batches/batch_025/candidates/C003|batch_025 C003]]: 20d Corr(overnight, intraday) → hard_gate sign_flip train +0.005 / val -0.006 → **reject**

---

### T004: intraday 镜像 aggregation [✗ DISPROVEN batch_027]

> [!failure]+ 机制封闭：F009 已吸收 intraday 分量
> **Question**: intraday return 5d/3d mean（镜像 F010/F011 的 overnight aggregation）是否携带独立于 F009 spread 的 alpha？
> **Answer**: 否。F009 = overnight - intraday 的数学结构已吸收 intraday 分量，pure intraday 是 overnight - F009 的线性组合。
> **Evidence trail**:
> - [[batches/batch_027/candidates/C001|batch_027 C001]]: 5d intraday mean → corr 0.65-0.89 @F009 + incr_ic 负 → **reject**
> - [[batches/batch_027/candidates/C002|batch_027 C002]]: 3d intraday mean → corr 0.65-0.89 @F009 + incr_ic 负 → **reject**
> - [[batches/batch_027/candidates/C003|batch_027 C003]]: volume-weighted intraday → corr 0.65-0.89 @F009 + incr_ic 负 → **reject**

---

## Known Failures

| Batch | Candidate | Pattern | 原因 |
|---|---|---|---|
| batch_025 | C003 | 20d Corr(overnight, intraday) | hard_gate sign_flip train +0.005 / val -0.006 |
| batch_027 | C001 | 5d intraday mean | corr 0.65-0.89 @F009 + incr_ic 负（intraday 非独立于 F009 spread）|
| batch_027 | C002 | 3d intraday mean | corr 0.65-0.89 @F009 + incr_ic 负（intraday 非独立于 F009 spread）|
| batch_027 | C003 | volume-weighted intraday | corr 0.65-0.89 @F009 + incr_ic 负（intraday 非独立于 F009 spread）|

---

## Related

- 🟢 [[intraday_price_formation]] (productive) — F003 overnight gap admit，本方向 overnight 段的上游字段依赖
- 🟡 [[ohlc_temporal_aggregation]] (saturated) — F007 open-position admit，与 F009 spread 相关性 0.708

---

## Narrative Log

> [!quote]- 2026-04-21 [[batches/batch_025/judge|batch_025]]
> **admit=2 (C001 + C002) / reserve=0 / reject=1 — direction status: exploring → productive (DOUBLE ADMIT 首批!)**
>
> - **C001 admit → overnight_intraday_spread_5d (F009)**: ic=+0.047 ls_t=5.18 mono=+1.00 incr=+0.044 — 机构 vs 散户 spread
> - **C002 admit → overnight_return_persistence_5d (F010)**: ic=+0.024 **ls_t=7.50 整库最强** mono=+1.00 incr=+0.019
> - **C003 reject**: 20d overnight-intraday correlation sign_flip — correlation 形式不稳定
>
> **核心发现**：overnight 段携带独立于 intraday 的 persistent signal；aggregation 形式有效，correlation 形式不稳。ls_t=7.50 (C002) 打破整库记录。
>
> **下一步 batch_026**：3d/10d overnight aggregation window ablation + overnight × intraday 乘积 + overnight 符号频率。

> [!quote]+ 2026-04-21 [[batches/batch_027/judge|batch_027]]
> **admit=0 / reserve=0 / reject=3 — direction status: productive → saturated**
>
> - Intraday 镜像 3/3 reject: 5d/3d intraday corr 0.65-0.89 @F009 + volume-weighted 同样冗余
> - **F009 = overnight - intraday 数学结构已吸收 intraday 分量**——pure intraday 是 overnight - F009 的线性组合，无独立信息
> - Direction status `productive → saturated`，overnight 家族 4 slot 达 bloat 上限
