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

## Hypothesis

分解 daily return 为 overnight ((open-prev_close)/prev_close) 和 intraday ((close-open)/open) 两段，两段受不同参与者驱动：overnight = 隔夜消息 + 机构 pre-market 决策；intraday = 日内散户 + 算法交易。**两段的 cross-sectional rotation 可能正交**——持续 overnight 强但 intraday 弱 vs 反之，预测不同 forward return 结构。

F003 已覆盖 overnight gap magnitude；F007 open-position 部分关联；但**两段 return 的 spread / ratio / correlation 未测**。

## Current Focus

3 候选测 overnight/intraday spread + ratio + corr。

## Threads

### T001: overnight - intraday spread + aggregation [✓ ANSWERED batch_025]
**Evidence**:
- [[batches/batch_025/candidates/C001|batch_025 C001]]: overnight-intraday spread 5d → ic=+0.047 ls_t=5.18 mono=+1.00 incr=+0.044 corr=0.708@F007 → **admit → overnight_intraday_spread_5d**
- [[batches/batch_025/candidates/C002|batch_025 C002]]: 5d overnight return persistence → ic=+0.024 ls_t=7.50 mono=+1.00 incr=+0.019 corr=0.424@F003 → **admit → overnight_return_persistence_5d**
**Conclusion**: overnight 段在 cross-section 上独立于 intraday 信号；spread 与 pure overnight 两种 aggregation 均有效。

### T002: overnight / intraday ratio [◉ ACTIVE]
未测，留给 batch_026。

### T003: overnight-intraday correlation [✗ DISPROVEN batch_025]
**Evidence**: C003 hard_gate sign_flip train +0.005 / val -0.006

## Known Failures
- C003 (batch_025): 20d Corr(overnight, intraday) — hard_gate sign_flip

## Related
- [[intraday_price_formation]] (F003 overnight gap admit)
- [[ohlc_temporal_aggregation]] (F007 open-position admit)

## Narrative Log
### 2026-04-21 [[batches/batch_025/judge|batch_025]]
**admit=2 (C001 + C002) / reserve=0 / reject=1 — direction status: exploring → productive (DOUBLE ADMIT 首批!)**

- **C001 admit → overnight_intraday_spread_5d (F009)**: ic=+0.047 ls_t=5.18 mono=+1.00 incr=+0.044 — 机构 vs 散户 spread
- **C002 admit → overnight_return_persistence_5d (F010)**: ic=+0.024 **ls_t=7.50 整库最强** mono=+1.00 incr=+0.019
- **C003 reject**: 20d overnight-intraday correlation sign_flip — correlation 形式不稳定

**核心发现**：overnight 段携带独立于 intraday 的 persistent signal；aggregation 形式有效，correlation 形式不稳。ls_t=7.50 (C002) 打破整库记录。

**下一步 batch_026**：3d/10d overnight aggregation window ablation + overnight × intraday 乘积 + overnight 符号频率。

### 2026-04-21 [[batches/batch_027/judge|batch_027]]
**admit=0 / reserve=0 / reject=3 — direction status: productive → saturated**

- Intraday 镜像 3/3 reject: 5d/3d intraday corr 0.65-0.89 @F009 + volume-weighted 同样冗余
- **F009 = overnight - intraday 数学结构已吸收 intraday 分量**——pure intraday 是 overnight - F009 的线性组合，无独立信息
- Direction status `productive → saturated`，overnight 家族 4 slot 达 bloat 上限

**Known Failures 追加**:
- C001/C002/C003 (batch_027): 5d/3d/volume-weighted intraday — corr 0.65-0.89 @F009 + incr_ic 全负 (intraday 非独立于 F009 spread)
