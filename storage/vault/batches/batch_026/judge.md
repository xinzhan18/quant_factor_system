---
batch_id: batch_026
direction: overnight_intraday_split
judged_at: 2026-04-21T06:35:00Z
candidates:
  - {candidate_id: C001, verdict: admit, factor_name: overnight_return_persistence_3d}
  - {candidate_id: C002, verdict: reserve}
  - {candidate_id: C003, verdict: reject}
batch_summary: {total: 3, admit: 1, reserve: 1, reject: 1}
---

# batch_026 Judge Summary

> [!abstract]+ batch_026 · [[directions/overnight_intraday_split]] · 3 candidates
> ✅ **admit=1** (C001 → overnight_return_persistence_3d) · ⏸ **reserve=1** (C002 10d 库 bloat) · ❌ **reject=1** (C003 mono=+0.10)
> **核心发现**: F010 3d ablation 成功 (ls_t=7.98 整库第 2 强)；10d reserve 因库 bloat；product form 破坏 mono rank。
> **MT Budget**: cumulative 122 → **125** · direction 3 → **6** · bucket `low`

## 候选一览

| ID | Verdict | Key | 反思 | Detail |
|---|---|---|---|---|
| C001 | ✅ admit | 3d overnight, ls_t=7.98 mono=+1.00 corr=0.756@F010 incr=+0.020 | F010 3d ablation 成功 | [[batches/batch_026/candidates/C001]] · [[factors/F011]] |
| C002 | ⏸ reserve | 10d overnight, ls_t=6.59 mono=+1.00 corr=0.696@F010 incr=+0.018 | 库 bloat: 4th overnight slot | [[batches/batch_026/candidates/C002]] |
| C003 | ❌ reject | overnight × intraday product 5d, mono=+0.10 | product 破坏 rank | [[batches/batch_026/candidates/C003]] |

## 跨候选对比

- **window ablation pattern 确认**：F010 (5d) + F011 (3d) 双窗口 admit，与 F006/F008 upper-shadow 同 pattern。10d C002 被 reserve（库 bloat + 与 F010/F011 双重重叠）
- **product form 失败**：overnight × intraday 乘积 mono=+0.10 — product 破坏 rank，即便 ls_t 3.91 也不 admit

## Thread 进展

> [!success]+ T001 [[directions/overnight_intraday_split#T001]] — `[◉ ACTIVE]`
> F011 admit; 10d reserve 待库重组。

> [!failure]+ T002 [[directions/overnight_intraday_split#T002]] — `[✗ DISPROVEN batch_026]`
> product form 破坏 mono rank。

## 方向级反思

方向 2 batch 内 3 admit (F009/F010/F011) + 1 reserve + 2 reject = admit 率 50%。overnight 分解维度是本 session 最高产方向。10 factor library 中 overnight 家族已占 3 slot (F003/F010/F011) + F009 spread = 4 slot，达到库 bloat 上限。**方向基本饱和**——status `productive` 维持但 priority `high → medium`。
