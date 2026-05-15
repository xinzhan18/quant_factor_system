---
batch_id: batch_095
direction: rank_diff_liquidity_microstructure
judged_at: 2026-05-16T06:50:00Z
candidates:
  - {candidate_id: C001, verdict: reserve}
  - {candidate_id: C002, verdict: reserve}
  - {candidate_id: C003, verdict: reject}
  - {candidate_id: C004, verdict: reject}
  - {candidate_id: C005, verdict: reject}
  - {candidate_id: C006, verdict: reserve}
batch_summary: {total: 6, admit: 0, reserve: 3, reject: 3}
admit_count: 0
reject_count: 3
reserve_count: 3
candidate_count: 6
mt_bucket: medium
---

# batch_095 Judge Summary

> [!abstract]+ batch_095 · [[directions/rank_diff_liquidity_microstructure]] · 6 candidates
> ✅ **admit=0** · ⏸ **reserve=3** (C001/C002/C006 rank-diff axis 同字段双窗口 family) · ❌ **reject=3** (C003 跨字段 RHS 撞 F024, C004 raw atom vol_20d 吞噬, C005 HP-2nd-order rank space 失效)
> **核心发现**: rank-diff axis 在 amount/num_trades 域 **second batch 实证 escape geometry**: 4/6 候选通过 hard_gate, 3/6 进 reserve 形成 axis cluster (b091/C004 + 本批 C001/C002/C006). 但**统计强度瓶颈未破**: 3 reserve 的 ls_t ∈ [-2.03, -2.60] 全部 < 3.0 admit floor. 关键 negative finding: HP-style 2nd-order 3-term rank-diff (C005) 失败 — rank space ordinal 不支持 Taylor-series 多阶展开, 升格 lessons forbidden pattern.
> **MT Budget**: cumulative 528 → **534** · direction 0 → **6** · bucket `medium` (新方向 direction_candidates 从 0 起步) · 本批 low=0 / med=6 / high=0

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ⏸ reserve | 🟢·🟡·🟡·🟢·🟢 | ic_oos=-0.0165 ls_t=-2.60 alpha_surv=0.77 max_corr=0.18 incr_ic=+0.0107 | RHS-short (60/10) 略改善 b091/C004 base, 错杀 4 件套全满足 | [[batches/batch_095/candidates/C001]] |
| C002 | ⏸ reserve | 🟢·🟡·🟡·🟢·🟢 | ic_oos=-0.0143 ls_t=-2.03 alpha_surv=0.68 max_corr=0.18 incr_ic=+0.0050 | 长窗 3:1 (90/30) 信号衰减, 验证"长窗等比扩展不放大"反 hypothesis | [[batches/batch_095/candidates/C002]] |
| C003 | ❌ reject | hard_gate (sign_flip+oos_decay) | max_corr=0.74@F024 | 跨字段 RHS=$amount/$volume 撞 F024 anchor (同 60d TsRank, volume 分母同源) | [[batches/batch_095/candidates/C003]] |
| C004 | ❌ reject | 🟡·**🔴**·**🟠**·🟡·🟡 | ls_t=-0.63 weak, vol_20d_exp=38.4, alpha_surv=1.03 (P030 paradox) | raw $amount 无法 escape size×vol 联合 basis, P008 frontier "ratio 字段"必要条件违反 | [[batches/batch_095/candidates/C004]] |
| C005 | ❌ reject | hard_gate (triple fail) | ic_oos=-0.0012 几乎为零, alpha_surv=7.80 paradox 极致 | HP-2nd-order rank space 失败 — ordinal 不支持 Taylor-series 多阶差 (lessons-promotion candidate) | [[batches/batch_095/candidates/C005]] |
| C006 | ⏸ reserve | 🟢·🟡·🟡·🟢·🟢 | ic_oos=-0.0190 ls_t=-2.50 alpha_surv=0.50 max_corr=0.19 incr_ic=+0.0064 | 5d Mean smoothing 拉到本批最强 IC magnitude, 但 ls_t 不变 - smoothing 不是 admission 关键 | [[batches/batch_095/candidates/C006]] |

## 跨候选对比

本批 6 候选沿 5 个独立 axes (T001-T005) 探索 rank-diff form 在 amount/num_trades 域的几何空间:

| Axis | Candidates | 结论 |
|---|---|---|
| **T001 RHS-window 伸缩** | C001 (60/10) + C002 (90/30) | **partial success** — C001 略改善 base (-0.017 vs -0.0165), C002 衰减 (-0.014); 短端方向 (10d ≤ RHS ≤ 30d) 有效, 长端 (≥90d) 衰减; 同字段双窗口几何 self-cancellation 有效但 ls_t < 3.0 不足 admit |
| **T002 跨字段 same window** | C003 (amount/num_trades vs amount/volume, 60d) | **disproven** — RHS=$amount/$volume 撞 F024 anchor (同 60d TsRank, volume 分母同源, max_corr=-0.74), 跨字段 rank-diff 必须避开 F024 引力盆地 |
| **T003 raw atom baseline** | C004 (raw $amount, 60/20) | **disproven** — raw $amount 无法 escape size×vol 联合 basis (vol_20d_exp=38.4 库内最高之一), P008 frontier "ratio 字段"必要条件违反; rank-diff axis 限定 dim-less ratio LHS |
| **T004 HP-2nd-order 3-term** | C005 (R60+R10-2*R20) | **disproven (升格 candidate)** — rank space ordinal 不支持 Taylor-series 多阶展开, 3-term 复合自我抵消 (IC ≈ 0), alpha_surv=7.80 paradox 极致触发 |
| **T005 outer smoothing wrap** | C006 (Mean 5d) | **partial success** — IC magnitude 最强 (-0.019), 但 ls_t 持平 base; smoothing 不破 admission floor — admission 瓶颈在 cross-section dispersion 不在 IC magnitude |

**跨候选相关性**:
- 3 reserve (C001/C002/C006) 同字段双窗口 family — 互相 corr 估计 > 0.5 (待 Phase 2 cross-corr 验证) → reserve 池增 3 但实质独立信号源 1 个
- C003 与 F024 max_corr=-0.74 (近 duplicate)
- C004 与 CsRank-diff cluster (F022/F016/F018) max_corr ~0.25 — 不独立
- C005 库独立 (max_corr 0.16) 但信号几乎为零

**MT 预算推进**: 新方向 direction_candidates 从 0 起步 → 6; cumulative 528 → 534; bucket medium (新方向 medium 上界), 全候选 mt_bucket=medium 但 search_adjusted ∈ [0.479, 0.576] 仍维持 borderline 档位.

## Thread 进展

每个 thread 在 [[directions/rank_diff_liquidity_microstructure]] 同步更新:

> [!note]+ T001 [[directions/rank_diff_liquidity_microstructure#T001]] — `[◉ ACTIVE]`
> reserve C001 (60/10) + reserve C002 (90/30). RHS-window 伸缩部分验证: 短端 (10d) 改善 IC magnitude 但 ls_t 不破; 长端 (90d) 衰减. 短端方向 (10d ≤ RHS ≤ 30d) 是有效复活路径, 但单 axis 不能突破 admit 阈.

> [!failure]+ T002 [[directions/rank_diff_liquidity_microstructure#T002]] — `[✗ DISPROVEN batch_095]`
> reject C003. 跨字段 RHS=$amount/$volume same-window rank-diff 撞 F024 (max_corr=0.74). T002 path 在 RHS=$amount/$volume 形式 disproven; 跨字段 rank-diff 可能仍有效 RHS 空间被 F024/F012 anchor 包围.

> [!failure]+ T003 [[directions/rank_diff_liquidity_microstructure#T003]] — `[✗ DISPROVEN batch_095]`
> reject C004. raw atom rank-diff 无 escape (vol_20d_exp=38.4); rank-diff axis 限定 dim-less ratio LHS (P008 frontier 三必要条件之一) — raw $amount/$volume/$turnover_rate 均不进入复活路径.

> [!failure]+ T004 [[directions/rank_diff_liquidity_microstructure#T004]] — `[✗ DISPROVEN batch_095]`
> reject C005. HP-style 2nd-order 3-term rank-diff 失败 (lessons-promotion candidate: rank space ordinal 不支持 Taylor-series 多阶差); T004 axis 全 form 路径封闭.

> [!note]+ T005 [[directions/rank_diff_liquidity_microstructure#T005]] — `[◉ ACTIVE]`
> reserve C006 (Mean 5d wrap, IC magnitude 最强 -0.019). T005 5d smoothing 验证了"IC magnitude 改善"但 ls_t 不变 — smoothing 不是 admission 关键, 瓶颈在 cross-section dispersion. 下一步: 7d/10d Mean window 上调, 或绕过 Qlib CsRank reparse bug 实现真 CsRank-wrap.

## 方向级反思

**hypothesis 部分验证**: rank-diff axis 在 amount/num_trades 域是 escape geometry — 第 2 批连续 4/6 候选通过 hard_gate, 3/6 进 reserve, 库独立性 (max_corr 0.18-0.27) + alpha_survival (0.50-0.77) + sign_consistency 1.0 + mono_oos -0.90 强单调 — 结构性 filter 全过.

**核心瓶颈未破**: 4 reserve (b091/C004 + 本批 C001/C002/C006) 的 ls_t ∈ [-2.03, -2.60] 全部 < 3.0 admit floor. 1 阶 rank-diff form 几何上 escape F024 anchor, 但**信号 magnitude 上限被 cross-section dispersion 限制** — rank-diff 的输出 cross-section 分布 (∈ [-1,1] 范围) 内在限制 ls_tstat 上限.

**axis 律精炼 (b091 + 本批联立)**:
- ✅ **rank-diff axis PASS 域**: dim-less ratio LHS (amount/num_trades) + 双窗口 self-cancellation + 短窗 RHS (10d-30d) + 任意 wrapper (Mean 5d 验证)
- ❌ **rank-diff axis FAIL 域**: close-position (b092) + overnight (b094) + raw atom (本批 C004) + 跨字段撞 anchor (本批 C003) + 多阶差 (本批 C005)
- 待验证: Python OLS vol_20d-residualize on numerator (复活路径 (a)) — 是否能 push ls_t ≥ 3.0

**Direction 决策**:
- status: `exploring` 维持 (rounds=0→1, admits=0)
- 不转 `dead` (4 candidates PASS structural filter, axis 有效)
- 不转 `saturated` (探索仍在第 1 轮, T005 axis 仍有 7d/10d wrap 空间)
- 下批策略: 不再重复同字段双窗口 1 阶 rank-diff (4 个 reserve 已饱和该几何), 转向 (a) **Python residualize on (F012 + F024 + vol_20d)** 看是否破 ls_t 阈; (b) **T005 outer wrap** 7d/10d Mean 测 smoothing window 上调效果; (c) reserve 池 4 候选合成 (rank-diff family 组合 alpha 通过线性合成 boost ls_t).

**Consolidation trigger 检查**:
- zero_admit_streak: 7→8 (本批 admit=0)
- rounds_since_consolidation: 4→5 (未达 10 trigger)
- **未触发 consolidation**

**Calibration trigger 检查**:
- 错杀 flag: C001 错杀 4 件套全满足 + C006 错杀 4/5 件套 (incr_ic 未达 0.010 严格) → 共 1-2 个 reserve 满足 "库空间独立" (max_lib_corr<0.30 + incremental_ic>0.010)
- 连续零 admit 警戒: 本批 admit=0 + 最近 3 批 (b093/b094/b095) 累计 admit=0 + 累计 reserve ≥1 满足 "库空间独立" → **calibration trigger 满足**
- **calibration_trigger=true** — orchestrator 下轮决定是否走校准诊断流程
