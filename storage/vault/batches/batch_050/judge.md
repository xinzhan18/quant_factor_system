---
batch_id: batch_050
direction: ohlc_temporal_aggregation
judged_at: 2026-04-25T05:55:00Z
candidates:
  - {candidate_id: C001, verdict: reserve}
  - {candidate_id: C002, verdict: reject}
  - {candidate_id: C003, verdict: reject}
  - {candidate_id: C004, verdict: reject}
  - {candidate_id: C005, verdict: admit, factor_name: body_disp_pricevol_rank_diff_20}
  - {candidate_id: C006, verdict: reject}
batch_summary: {total: 6, admit: 1, reserve: 1, reject: 4}
admit_count: 1
reserve_count: 1
reject_count: 4
candidate_count: 6
mt_bucket: high
---

# batch_050 Judge Summary

> [!abstract]+ batch_050 · [[directions/ohlc_temporal_aggregation]] · 6 candidates
> ✅ **admit=1** (C005→F{next} `body_disp_pricevol_rank_diff_20`) · ⏸ **reserve=1** (C001 alpha_surv=0.33 + max_corr=0.50 边界) · ❌ **reject=4** (C002 max_corr=0.61 + vol_20d=53; C003 mono soft sign_flip; C004 incr_ic=0.003 不足; C006 hard_gate)
> **核心发现**：rank-diff 范式第 5 次跨家族兑现——OHLC 家族 saturated 状态被 higher-moment OHLC + price-vol RHS 突破。C005 LHS=Std(body_ratio,20) 是 direction.md hypothesis 复活条件 (a) "新 OHLC 原子维度" 的首次兑现，max_corr=0.270 整批整库最干净，与 4 个 admitted rank-diff (F015/F016/F017/F018) 全 <0.25。**T010 5 次 cross-family generalization tipping point 正式确认**——建议 Phase 5 consolidation 升格 lessons.md "rank-diff geometry" 通用规则。
> **MT Budget**: cumulative 258 → **264** · direction 22 → **28** · bucket `high` (search_adjusted → medium) · 本批 low=0 / med=0 / high=6

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ⏸ reserve | 🟢·🟢·🔴·🟡·🟢 | ic_oos=+0.044 ls_t=4.12 mono=1.0/1.0 alpha_surv=0.33 max_corr=0.50@F017 incr=0.013 | rank-order 真实 + 库空间 borderline；alpha_surv 单 dealbreaker；C005 admit 优先 | [[batches/batch_050/candidates/C001]] |
| C002 | ❌ reject | 🟢·🟢·🔴·🔴·🟢 | ic_oos=+0.068 ls_t=4.13 alpha_surv=0.27 max_corr=0.61@F018 vol_20d=53 | 三 flag 叠加：library cluster 共享 + 双 poor + extreme vol_20d | [[batches/batch_050/candidates/C002]] |
| C003 | ❌ reject | 🔴·🔴·false·🟡·🔴 | ic_oos=-0.013 ls_t=-0.36 mono+0.9→-0.3 cum_dd=-40.2 | intraday return 是 random walk + alpha_surv=2.32 false (raw IC≈0) | [[batches/batch_050/candidates/C003]] |
| C004 | ❌ reject | 🟡·🟡·🔴·🔴·🟢 | ic_oos=+0.040 ls_t=3.36 alpha_surv=0.26 max_corr=0.66@F017 incr=0.003 | LHS=gap 与 F010/F011/F017 共振; incr_ic dealbreaker | [[batches/batch_050/candidates/C004]] |
| C005 | ✅ **admit** | 🟢·🟡·🔴·🟢·🟢 | **ic_oos=+0.039 ls_t=2.90 mono=0.9/1.0 max_corr=0.270 incr=0.020 9/9yr+ cum_dd=-1.61** | rank-diff geometry 第 5 次 cross-family + Std(body_ratio) higher-moment hypothesis 复活条件 (a) 命中 + 整批 library-clean | [[batches/batch_050/candidates/C005]] · [[factors/F019]] |
| C006 | ❌ reject | hard_gate | sign_flip + ic_oos=0.004 + oos_decay=-0.30 | intraday body sign 是 random walk (b017 C003 教训复现) | [[batches/batch_050/candidates/C006]] |

**档位编码**：🟢 最优档 · 🟡 次档 · 🟠 边际 · 🔴 阻断档 · `hard_gate` reject 不填色。

## 跨候选对比

**LHS 多元化结构 (本批 6 LHS 全唯一)**:
- C001: `Mean(body_ratio, 5)` — magnitude mean
- C002: `Mean($close/$high, 5)` — close ratio mean
- C003: `Mean(intraday_return, 5)` — return mean (random walk)
- C004: `Mean(gap_to_range, 5)` — overnight gap mean (与 F010/F011 共振)
- C005: `Std(body_ratio, 20)` — **higher moment (Std, 整批唯一)**
- C006: `Mean(Sign(body), 5)` — sign mean (与 F018 sign 几何 LHS=overnight 不同 — random walk)

**关键 admit 路径分析**: 6 LHS 中只有 C005 在两个维度上同时超越饱和：(1) **OHLC 家族** higher moment (Std vs 库内全 Mean-base)；(2) **rank-diff RHS 端** price-vol (vs F015/F016/F017/F018 的 amount/turnover/overnight 基准)。两个新维度叠加 → max_corr=0.270 整库唯一<0.30。

**reject 模式分类**:
- **library cluster 共振 reject (C002, C004)**：max_corr 0.61/0.66 + 与 5 库因子 ≥0.45 — `cross-family rank-diff 必须 LHS+RHS 都跳出已饱和 cluster`，半数失败 → reject
- **random walk LHS reject (C003, C006)**：纯 intraday return / intraday body sign 在 csi1000 5d 无 persistent drift；rank-diff 几何不能转 random walk 为 alpha
- **alpha_surv 单 dealbreaker reserve (C001)**：rank-order 真实但库空间 borderline 0.50 + alpha_surv 单 flag — calibration §Step 1 标志，pending

**与 b049 C006 admit 范式对照**: 
- b049 C006 (admit F018): LHS=Mean(Sign(overnight),20) — overnight 有 institutional accumulation drift
- 本批 C006 (reject): LHS=Mean(Sign(close-open),5) — intraday body 是 random walk
- **教训**: sign 聚合 paradigm 的 alpha 来源是 underlying field 的 persistent drift, 而非 Sign() 操作本身. 不能盲目跨字段泛化 sign aggregation.

**与 b049 C001/C005 (Mean|ret| vs L2 RealizedVol) 对照**:
- b049: L1 vs L2 vol family 同批冗余（IC -0.055/-0.055 几乎相同）
- 本批: Mean(body_ratio,5) (C001) vs Std(body_ratio,20) (C005) - 不同 moment, 不同 corr structure (C001 IC=0.044 / C005 IC=0.039 但 max_corr 0.50 vs 0.27 完全不同)
- **新教训**: **不同 moment of same atomic signal 不冗余** (Mean vs Std 是不同 family); 但 L1 vs L2 of same moment 冗余 (b049). **moment 选择是 rank-diff LHS 设计的独立轴**.

**Style 聚合**: 6 候选 dominant_style 全 vol_20d. C005 crowding=medium (整批唯一非 high), 其余 high. **OHLC 5d aggregation 天然 vol_20d 暴露** — direction structural constraint.

**MT 预算**: direction_candidates 22 → 28 接近 70 上限; 本方向 saturated → 重启 productive (C005 admit 突破), 但 MT 高位需注意下批暂停或换 direction.

## Thread 进展

> [!success]+ T010 [[directions/ohlc_temporal_aggregation#T010]] 🆕 — `[✓ ANSWERED batch_050]`
> rank-diff 范式第 5 次跨家族兑现且首次在 OHLC 家族——LHS=Std(body_ratio,20) higher moment OHLC + RHS=price_vol 双新维度。max_corr=0.270 整库唯一<0.30 + incr_ic=0.020 健康. **T010 5th cross-family tipping point 正式确认**: F015/F016 (microstructure) + F017 (overnight×turnover) + F018 (overnight_sign×amount) + 本批 C005 (OHLC×price_vol) 跨 4 family 5 admit. → 触发 Phase 5 升格 lessons.md 通用 rank-diff geometry 规则.

> [!failure]+ T011 [[directions/ohlc_temporal_aggregation#T011]] 🆕 — `[✗ DISPROVEN batch_050]`
> sign aggregation paradigm 不能盲目跨字段泛化——LHS 的 underlying field 必须有 persistent drift (overnight ✓ / intraday body ✗). C006 hard_gate 三 fail 验证 b017 C003 教训, 同时反向证 b049 C006 admit 的 alpha 来源是 overnight field 的 institutional accumulation drift, 而非 Sign() 操作几何.

> [!info]+ T012 [[directions/ohlc_temporal_aggregation#T012]] 🆕 — `[◉ ACTIVE]`
> **不同 moment of same atomic signal 不冗余**: Mean(body_ratio) vs Std(body_ratio) 是 rank-diff LHS 设计的独立轴 (C001 vs C005 max_corr 0.50 vs 0.27 显示 moment 改变 corr structure 完全). 下批可探: Skew/Kurt of body_ratio, Std/Mean of upper_shadow / open_position 等 higher-moment OHLC 变体.

> [!note]- T003 [[directions/ohlc_temporal_aggregation#T003]] — `[✓ ANSWERED batch_017-021 + batch_050]`
> direction 从 saturated 重启 productive: 本批 C005 admit 突破 b020 之后 4 batch 0-admit. ohlc_temporal_aggregation 因子库 3→4 (F006/F007/F008 + F019).

## 方向级反思

**direction 状态变化**: `saturated → productive` (5 round 0-admit 后突破). admit 率从 14% (3/21) 调整为 4/27=15%, 但本次突破依赖 rank-diff geometry 而非传统 OHLC 设计. 

**已确认饱和的 OHLC 子空间**:
- standalone OHLC ratio (b017-021 全 reject 除 F006/F007/F008 admit)
- 5d Mean of body_ratio / close_position / upper_shadow magnitude (Mean-based 已饱和)
- intraday return / intraday body sign (random walk 不可救)

**仍开放的 OHLC 子空间**:
- **higher moment OHLC** (Std/Skew/Kurt of body_ratio, upper_shadow, open_position) — C005 首探
- **OHLC × price_vol cross-family rank-diff** (本批 C005 RHS) vs **OHLC × turnover/amount** (C001/C002/C004 共振)
- **OHLC 标量化与 fundamental basis** (C004 失败 + C002 边界——pb 与 OHLC LHS 共振 size)
- **3d/7d rolling Std body_ratio** (本批 only 20d，window sweep 待探)

**Library 健康度**: ohlc_temporal_aggregation 4/(18+1)=21%, 仍可控. F019 (C005) 独立性 max_corr=0.27 优于 F018 (0.62), 库结构性更健康.

**5 次 rank-diff cross-family tipping point 触发 Phase 5 consolidation**:
- **建议升格 lessons.md 新 section "rank-diff geometry"**: 内容包括 (1) RHS 端共振饱和律 (b049 lesson); (2) higher-moment LHS 是独立轴 (本批 lesson); (3) sign aggregation 需 underlying drift (本批 lesson); (4) cross-family generalization 需 LHS+RHS 都跳出 cluster.
- **跨 5 direction**: microstructure (F015/F016) + overnight (F017/F018) + ohlc_temporal_aggregation (F019) — rank-diff 已成系统级 paradigm.

## 阈值校准诊断

本批 admit=1 + reserve=1, 不触发 calibration:
- ✗ 连续零 admit: F019 admit 重置计数
- ✗ Reserve 积压: cumulative reserve/judged 比例正常
- ✗ 库规模停滞: F018→F019 持续增长
- ✗ 悖论复现: alpha_survival<0.40 但库空间独立 admit (C005) 是 calibration 已建立的合理 pattern (F015/F016/F018 先例)

C001 reserve 标记为 `pending_calibration`——若连续 3 批 0 admit + C001 仍是 max_corr<0.30 + incr_ic>0.010 等错杀诊断标志, 触发追溯流程.
