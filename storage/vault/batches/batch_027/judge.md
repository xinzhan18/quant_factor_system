---
batch_id: batch_027
direction: overnight_intraday_split
judged_at: 2026-04-21T06:45:00Z
candidates:
  - {candidate_id: C001, verdict: reject}
  - {candidate_id: C002, verdict: reject}
  - {candidate_id: C003, verdict: reject}
batch_summary: {total: 3, admit: 0, reserve: 0, reject: 3}
---

# batch_027 Judge Summary

> [!abstract]+ batch_027 · [[directions/overnight_intraday_split]] · 3 candidates
> ❌ **admit=0** · ❌ **reject=3**
> **核心发现**: pure intraday return 3/3 corr 0.65-0.89 @F009 + library reducer。**intraday 段不独立于 F009 spread**——F009 = overnight - intraday 所以 intraday ≈ overnight - F009，数学相关必然。Direction 进一步 saturated。
> **MT Budget**: cumulative 125 → **128** · direction 6 → **9** · bucket `medium`

## 候选一览

| ID | Verdict | Key | 反思 | Detail |
|---|---|---|---|---|
| C001 | ❌ reject | 5d intraday, corr=0.890@F009 | near_dup F009 pattern | [[batches/batch_027/candidates/C001]] |
| C002 | ❌ reject | 3d intraday, corr=0.651@F009 ls_t=-2.36 | ls_t weak + reducer | [[batches/batch_027/candidates/C002]] |
| C003 | ❌ reject | volume-weighted 5d, corr=0.885@F009 | volume weight 不解耦 | [[batches/batch_027/candidates/C003]] |

## 跨候选对比

- **F009 吸收 intraday 分量**：F009 = overnight - intraday，因此 admit F009 后 pure intraday = overnight - F009 → 被 F009 + F010/F011 完全覆盖。**spread 形式是正确的分解载体，pure 形式是冗余**。
- **volume weighting 不独立**：C003 corr=0.885 证明 log_volume 加权也无法让 intraday 跳出 F009 相关性

## 方向级反思

overnight_intraday_split 3 batches, 9 候选 → 3 admit / 1 reserve / 5 reject = admit 率 33%。intraday 镜像路径证伪 → 方向 **saturated** 的证据。

**Direction 操作**: status `productive → saturated`（与 ohlc_temporal_aggregation 相同路径）；priority `medium → low`。Library 中 overnight 家族 (F003/F009/F010/F011) 已 4 slot 达 bloat 上限。
