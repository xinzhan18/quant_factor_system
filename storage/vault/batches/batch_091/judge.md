---
batch_id: batch_091
direction: institutional_flow_proxy
judged_at: 2026-05-15T20:30:00Z
candidates:
  - {candidate_id: C001, verdict: reject}
  - {candidate_id: C002, verdict: reject}
  - {candidate_id: C003, verdict: reject}
  - {candidate_id: C004, verdict: reserve}
  - {candidate_id: C005, verdict: reject}
  - {candidate_id: C006, verdict: reject}
batch_summary: {total: 6, admit: 0, reserve: 1, reject: 5}
admit_count: 0
reject_count: 5
reserve_count: 1
candidate_count: 6
mt_bucket: high
---

# batch_091 Judge Summary

> [!abstract]+ batch_091 · [[directions/institutional_flow_proxy]] · 6 candidates
> ✅ **admit=0** · ⏸ **reserve=1** (C004 rank-diff form) · ❌ **reject=5** (3× window sweep + reciprocal duplicate + hard_gate fail)
> **核心发现**: Reserve revival pool #1 (b072/C006 复活路径) — 窗口轴 (30/90/120d) 全部被 F024 anchor 锁死 (max_corr 0.71-0.79)；reciprocal 倒数变换 (C005) 通过 monotonic 等价撞 b072/C006 本身；P008 third ratio (volume/num_trades, C006) 直接撞 F024 硬闸。**唯一突破**：rank-diff form (C004 Sub(TsRank60, TsRank20)) max_corr=0.18 LOW + incr_ic=+0.008 PASS + alpha_surv=0.86 PASS — 库空间独立但 ls_t=-2.20 statistical 不足 → reserve。
> **MT Budget**: cumulative 504 + 6 = **510** · direction 6 → **12** · bucket `high` (上界)

## 候选一览

| ID | Verdict | 档位 (CP02·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | aligned · strong→borderline · acceptable · **high** · stable | ic_oos=-0.048, ls_t=-7.64, **max_corr=0.79@F024**, incr_ic=-0.012 | 30d 窗口缩短反而提升 max_corr (vs 60d=0.24) — F024 几何邻域在更短窗口更密集 | [[batches/batch_091/candidates/C001]] |
| C002 | ❌ reject | aligned · strong→borderline · acceptable · **high** · stable | ic_oos=-0.056, ls_t=-7.46, **max_corr=0.75@F024**, incr_ic=-0.007 | 90d 窗口位于 60d-120d 之间 - 仍在 F024 anchor 引力盆地 | [[batches/batch_091/candidates/C002]] |
| C003 | ❌ reject | aligned · strong→borderline · **borderline** · **high** · stable | ic_oos=-0.058, ls_t=-7.50, **max_corr=0.71@F024**, alpha_surv=**0.398** poor, incr_ic=-0.006 | 季度窗口反直觉：窗口越长 vol_20d 嵌入越深 (alpha_surv 0.558→0.418→0.398 单调下降) | [[batches/batch_091/candidates/C003]] |
| C004 | ⏸ **reserve** | aligned · **weak** · acceptable · **low** · stable | ic_oos=-0.016, **ls_t=-2.20** weak, **max_corr=0.18@F016**, **incr_ic=+0.008** PASS, alpha_surv=**0.862** | 唯一脱 F024 几何邻域 — rank-diff form 真正 escape！但统计强度不足 admit | [[batches/batch_091/candidates/C004]] |
| C005 | ❌ reject | **mixed** · strong→borderline · acceptable · **high** · stable | ic_oos=+0.054, ls_t=+7.57, **max_corr=0.84@F024**, incr_ic=+0.009 | 倒数变换 monotonic sign-flip duplicate of b072/C006 (mathematically equivalent) | [[batches/batch_091/candidates/C005]] |
| C006 | ❌ reject | hard_gate | **max_corr=0.957 @F024** (>0.9 硬闸) | F024 的 reciprocal monotonic duplicate (TsRank(volume/num_trades) ≡ TsRank(num_trades/volume) sign-flip) | [[batches/batch_091/candidates/C006]] |

## 跨候选对比

本批 6 候选沿 5 个独立 axes 探索 T001 复活路径：

| Axis | Candidates | 结论 |
|---|---|---|
| Window sweep | C001 (30d), C002 (90d), C003 (120d) | **全段 disproven** — F024 anchor 在 30-120d 是连续引力盆地 (max_corr 0.71-0.79)。反直觉发现：alpha_surv 单调下降 0.558→0.418→0.398，长窗口反加重 vol_20d 嵌入 |
| Rank-diff | C004 Sub(TsRank60, TsRank20) | **partial escape** — max_corr=0.18 LOW + incr_ic=+0.008 PASS + alpha_surv=0.862 PASS。唯一脱 F024 几何，但 ls_t=-2.20 weak → reserve |
| Reciprocal | C005 TsRank(num_trades/amount, 60) | **sign-flip duplicate** — TsRank(1/x,N)=N+1-TsRank(x,N) 让本候选与 b072/C006 monotonic 等价 (IC 完美镜像 ±0.054) |
| P008 third ratio | C006 TsRank(volume/num_trades, 60) | **sign-flip duplicate of F024** — hard_gate fail 0.957@F024，TsRank(volume/num_trades) 是 F024 (TsRank(num_trades/volume)) 字段对 reciprocal sign-flip 等价 |

**跨候选相关性总结**：C001/C002/C003/C005/C006 在 F024 anchor 引力盆地内互相高相关（共享同一 trade-density geometry）；C004 是唯一几何 outlier (max_corr=0.18 vs 其它 0.71-0.96)，但代价是信号量级下降一个数量级 (ls_t -2.2 vs -7.5)。

## Thread 进展

### T001 — avg_trade_size 时序几何

**状态**: 维持 `[◉ ACTIVE]` — 但本批将 T001 探索深化，4/5 子轴 disproven，rank-diff form (C004) 作为新 partial-progress 候选 reserve 接力 b072/C006。

| Sub-axis (复活路径) | 候选 | Round 73 状态 | Round 91 状态 |
|---|---|---|---|
| (a) RHS rank-diff | C004 | proposed | **partial-progress** (reserve) |
| (b) window sweep | C001/C002/C003 | proposed | **全段 disproven** |
| (c) Python residualize on F009 | — | proposed | 未实验 (留至 round 92+) |
| (d) 跨字段 TsRank composite | — | proposed | 未实验 (留至 round 92+) |
| (e) Reciprocal axis (round 91 新增) | C005 | — | **sign-flip duplicate disproven** |
| (f) P008 third ratio (round 91 新增) | C006 | — | **sign-flip duplicate disproven** |

T002 (raw level retail attention) / T003 (rank-diff vs amount) / T004 (Corr OFI) / T005 (cross-product) 维持 round 72 disproven 状态。

## 候选反思（4 层）

### Layer 1 — 候选间结构对比

**3 window sweep (C001/C002/C003)** 形成完美的 axis 扫描：
- max_corr 单调下降 (window 增长方向)：0.79 → 0.75 → 0.71
- incr_ic NEG 维持改善但全段负：-0.012 → -0.007 → -0.006
- **反直觉**：alpha_surv 单调下降 0.558 → 0.418 → 0.398 (窗口越长 vol_20d 嵌入越深)
- ls_t magnitude 平稳：-7.64, -7.46, -7.50 (信号强度不依赖窗口)
- **结论**：窗口轴在 F024 的 60d 邻域内 (30d-120d 范围) 是连续几何邻域，**整段不存在 escape 点**

**Reciprocal axis (C005/C006)**：
- C005 (TsRank($num_trades/$amount, 60)) 是 b072/C006 的 sign-flip duplicate (倒数 + TsRank monotonic 不变)
- C006 (TsRank($volume/$num_trades, 60)) 是 F024 的 sign-flip duplicate (字段对 reciprocal + TsRank monotonic 不变)
- **两个都是 monotonic-equivalent duplicates** — TsRank 包裹下倒数变换是中性的，不构成新几何

**Rank-diff axis (C004) 是唯一 escape**：
- max_corr 从 window-sweep 段 (0.71-0.79) 跳到 0.18 — 几何上彻底脱离 F024
- 但代价：信号量级下降 (ls_t 从 -7.50 降至 -2.20)
- 机制层面：rank-diff 是"双窗口 self-cancellation" — 60d 慢趋势减去 20d 快趋势 → 信号主要在过渡期 (regime change) 才显著，平稳期信号微弱

### Layer 2 — MT 预算

- batch-level cumulative_candidates 504→510，bucket `high` 维持
- direction-level 6→12（本批 6 候选都 judged）
- 所有候选 mt_bucket=high → CP03 即使 strong 也降至 borderline
- search_adjusted: C001 0.531/medium，C004 0.808/high — C004 的 high 是因为本候选触及 untested 几何轴 (rank-diff form 是 P031 lessons #1 提及的"rank-diff salvage"路径首次实证)

### Layer 3 — Thread 进展

**T001 [◉ ACTIVE]** (avg_trade_size 时序几何) — 本批 6 候选全部沿 T001 推进：
- 窗口轴 (b)：30d/90d/120d → **全部 disproven** (F024 anchor 锁死 60d 邻域)
- Rank-diff 轴 (a)：C004 → **partial-progress**：库空间独立 (max_corr=0.18 + incr_ic=+0.008) PASS，但统计强度不足 admit → reserve
- Reciprocal 轴 (c)：C005 → **disproven** (sign-flip 等价于 b072/C006，monotonic-invariant duplicate)
- P008 third ratio 轴 (d)：C006 → **disproven** (TsRank(volume/num_trades) 是 F024 sign-flip duplicate)

T001 状态变化：partial-progress → **deeper partial-progress** (C004 rank-diff form 是新候选保留火种，原 b072/C006 reserve 仍维持)

### Layer 4 — 方向级反思

**direction 状态评估**：
- rounds 2→3, admits 仍 0
- reserve pool: b072/C006 + b091/C004 (2 个 reserve)
- 4 个 thread 状态：T001 partial-progress (深化)，T002/T003/T004/T005 已 disproven (batch_072)
- zero_admit_streak: 5→6

**核心元教训 (升格 lessons 候选)**：

1. **Reciprocal monotonic-invariant duplicates** — TsRank/CsRank 包裹下 Div(a,b) 与 Div(b,a) 是 sign-flip 等价 (TsRank(1/x,N)=N+1-TsRank(x,N))。Phase 1 generator canonical 检查应升格识别 reciprocal pair (当前漏检 C005/C006)
2. **Window axis 在 F024 anchor 邻域内连续封闭** — 30d/60d/90d/120d 都在 F024 (60d) 引力盆地内 (max_corr 0.71-0.79)，不存在窗口 escape 点
3. **Rank-diff form 是 escape 唯一路径** — C004 max_corr=0.18 跳脱证实 round 91 lessons P008 escape 律的 rank-diff salvage 子律。但代价是 ls_t magnitude 大幅下降 (信号在过渡期才显著)
4. **Window 越长 vol_20d 嵌入越深 (反直觉)** — alpha_surv 30d=0.558, 90d=0.418, 120d=0.398 — 长窗口反而恶化 Barra 残差。可能机制：120d 包含跨季度 vol regime 完整 cycle，时序 rank 携带的 cross-section vol info 增加

**下批建议**：
- **强烈不建议**继续 window sweep / reciprocal / P008-stack 路径
- **建议 reserve C004 进入 Python residualize 路线** — 若 incr_ic 在 (F024+F012) residualization 后 ≥ 0.010 + ls_t 改善至 ≥ 2.5 → admit；否则维持 reserve
- direction 整体接近 **saturated** 状态 — T001 4 个子轴 (window/rank-diff/reciprocal/P008-stack) 全部探索，仅 rank-diff form 部分突破但 statistical 不足
- Phase 5 consolidation 触发条件：rounds_since_consolidation=0 (刚 91), zero_admit_streak=6 → 不立即触发，但下一批若再 0-admit 应触发

**Direction status 翻牌建议**：维持 `probing` (C004 火种活跃)；T001 partial-progress 深化（多了 rank-diff 维度）；考虑下批后转 `saturated`。

## Calibration Triggers (Phase 3.5)

| Trigger | 状态 | 详情 |
|---|---|---|
| 错杀 flag (over-rejection) | ✅ Not triggered | 5 reject 全部有结构性原因 (F024 anchor cluster / sign-flip duplicate / hard_gate) — 无错杀 |
| 连续零 admit 警戒 | ⚠️ Watching | zero_admit_streak=6 (b086-b091)。**但** C004 reserve 满足"库空间独立"条件 (max_corr=0.18, incr_ic=+0.008) — 已是 calibration/013 反 P030 验证候选，正常 reserve 流程，不触发放宽 |
| Reserve 积压 | Not triggered | 累计 reserve 比例未达 40% |
| 悖论复现 | ✅ **Triggered weakly** | "alpha_surv 单调下降 vs 窗口延长" 与 P004-deep (path-integral 失败) 同类律 — TsRank 长窗口虽非 path-integral，但有类似 vol_20d 残余涌现机制。建议下次 consolidation 关注 |

**Calibration verdict**：不触发阈值放宽。维持 P030 hard rule。C004 reserve 正常进入 round 92+ 复活路径队列。
