---
batch_id: batch_013
direction: barra_residual_alpha
judged_at: 2026-04-19T15:10:00Z
candidates:
  - {candidate_id: C001, verdict: admit, factor_name: barra_residual_alpha_60d}
  - {candidate_id: C002, verdict: reserve}
  - {candidate_id: C003, verdict: reject}
  - {candidate_id: C004, verdict: reject}
  - {candidate_id: C005, verdict: reject}
batch_summary: {total: 5, admit: 1, reserve: 1, reject: 3}
---

# batch_013 Judge Summary

> [!abstract]+ batch_013 · [[directions/barra_residual_alpha]] · 5 candidates
> ✅ **admit=1** (C001→F{next}) · ⏸ **reserve=1** (C002) · ❌ **reject=3** (C003 C004 C005)
> **核心发现**: Barra residual alpha confirmed — full 7-style residual (C001) carries strong ICIR=0.293; vol_20d-only residual (C002) slightly weaker; turnover interaction (C003) flips sign; 10d styles (C004) redundant with 60d
> **MT Budget**: cumulative 72 → **77** · direction 5 → **6** · bucket `medium`（上界）· 本批 low=0 / med=2 / high=0

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ✅ admit | 🟢·🟢·🟡·🟢·🟡 | ICIR=0.293 ls_t=7.34 | Barra residual confirmed — vol_20d dominant style (coef=4.44) but residual IC=0.033 > raw IC=0.024 → genuine idiosyncratic alpha | [[batches/batch_013/candidates/C001]] · [[factors/F005]] |
| C002 | ⏸ reserve | 🟢·🟡·🟡·🟢·🟡 | ICIR=0.243 ls_t=7.28 | Keep vol_20d as signal slightly weaker; alpha_surv=1.62 (higher than C001); incremental_ic=0.030 + max_corr=0.12 — worth one more round observation | [[batches/batch_013/candidates/C002]] |
| C003 | ❌ reject | hard_gate | sign_flip+oos_decay=-1.65 | Turnover interaction breaks sign consistency; IS=-0.0066 vs OOS=+0.011 — IC reversal across train/val | [[batches/batch_013/candidates/C003]] |
| C004 | ❌ reject | hard_gate | redundant | Identical Barra residual to C001 (same metrics); 10d styles don't add value over 60d baseline | [[batches/batch_013/candidates/C004]] |
| C005 | ❌ reject | hard_gate | compute_error | Size-neutral quintile grouping crashed during compute — quintile assignment shape mismatch | [[batches/batch_013/candidates/C005]] |

## 跨候选对比

- **Style 聚合**: C001/C002 dominant style = vol_20d (exposure 4.44 / 9.71); both strip non-vol styles — vol_20d is the dominant absorption source in Barra residual alpha
- **相关度 cluster**: C001 vs C004 identical (max_corr implicit = 1.0); C002 more differentiated (max_corr=0.12 vs C001)
- **MT 预算**: direction_candidates 5 → 6; C001 and C002 push direction from 5→6 (both use vol_20d in style set); C003/C004/C005 rejected at gate — no new MT consumption
- **Survival ratio**: C002 (1.62) > C001 (1.35) — keeping vol_20d as signal shows better alpha survival after style stripping

## Thread 进展

**每个 T{n} 提及必须 wikilink** 到 `[[directions/barra_residual_alpha#T{n}]]`：

> [!success]+ T001 [[directions/barra_residual_alpha#T001]] — `[✓ ANSWERED batch_012]`
> Barra residual alpha exists — confirmed by C001/F004 in batch_012 and replicated in batch_013 with ICIR=0.293

> [!note]+ T002 [[directions/barra_residual_alpha#T002]] — `[◉ ACTIVE]`
> C001 admit → vol_20d dominant but residual IC > raw IC (0.033 > 0.024) = genuine idiosyncratic alpha. C002 reserve → vol-20d-only residual viable (ICIR=0.243, incremental_ic=0.030). Next: probe short-window (10d/20d) Barra residual vs pure vol_20d signal decay

> [!note]- T003 [[directions/barra_residual_alpha#T003]] — `[◉ ACTIVE]`（本批无推进）

## 方向级反思

本方向（`barra_residual_alpha`）两批验证：
- batch_012: admit F004 barra_residual_return (ICIR=0.293, ls_t=7.34)
- batch_013: admit C001 (replication with slightly different impl) + reserve C002

**关键发现**: vol_20d 是主要吞噬来源（exposure coef 4-9x 其他风格），但 Barra residual 本身仍携带显著 alpha。剥离非 vol 因子后保留 vol_20d 作为信号（C002）的 alpha_surv=1.62 高于全剥离（C001=1.35），说明 vol_20d 本身部分驱动 alpha。

下轮建议：
1. 纯 vol_20d 信号（不剥离任何 Barra 风格）vs Barra residual 哪个 IC 更高？
2. 20d 窗口的 Barra residual 是否比 60d 衰减更快？
3. C002 reserve 值得再观察一批 — incremental_ic=0.030 + max_corr=0.12 满足库空间独立条件

若下一批 reserve 候选仍无 admit，方向 status → saturated。
