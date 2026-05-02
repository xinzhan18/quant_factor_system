---
batch_id: batch_078
direction: reserve_revival_paths
judged_at: 2026-05-02T06:30:00Z
candidates:
  - {candidate_id: C001, verdict: reject, derives_from: batch_076/C005, revival_path_type: rhs_change}
  - {candidate_id: C002, verdict: reject, derives_from: batch_076/C001, revival_path_type: mean_centering}
  - {candidate_id: C003, verdict: reject, derives_from: batch_072/C006, revival_path_type: window_sweep}
  - {candidate_id: C004, verdict: reject, derives_from: batch_053/C001, revival_path_type: retro_post_floor}
  - {candidate_id: C005, verdict: reject, derives_from: batch_050/C001, revival_path_type: rhs_change}
  - {candidate_id: C006, verdict: reject, derives_from: batch_058/C001, revival_path_type: rhs_change}
batch_summary: {total: 6, admit: 0, reserve: 0, reject: 6}
admit_count: 0
reserve_count: 0
reject_count: 6
candidate_count: 6
mt_bucket: medium
---

# batch_078 Judge — reserve_revival_paths 全 reject 揭示 minor-path 复活律

> [!warning]+ batch_078 · [[directions/reserve_revival_paths]] · 6 candidates (round 78, NEW direction reserve pool retro audit driven, 0 admit)
> ❌ **admit=0** · ⏸ **reserve=0** · ❌ **reject=6**
> **核心发现**: 6 个 reserve 复活路径全 reject — **minor-path revival 假设系统性证伪**. 来自 b050/b053/b058/b072/b076 的 25-30 batch 之前的 reserve, 尽管原信号档位强 (mono PERFECT, ls_Sharpe=2.45, ic_oos=+0.055 batch high), 但经过库内同 family admit 累积 (F007/F008/F012/F017/F018/F024) 的几何饱和, 三种 minor 复活路径 (rhs_change 同 family / mean_centering / window_sweep / retro_post_floor) **全部不破 max_corr 阻断**.
> **MT Budget**: cumulative 426 → 432 · direction 0 → 6 · bucket `medium`
> **direction status**: `active` 维持 (NEW direction, 0 admits 但首批揭示系统性 finding); 但本批已**反向证伪 minor-path 复活假设**, 后续若复活只能升级到 python residualize 或跨 family rhs_change.

## 候选一览

| ID | Verdict | derives_from | path_type | 档位 (CP1·2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|---|---|
| C001 | ❌ reject | b076/C005 | rhs_change | ✓·aligned·weak·borderline·**high(F007)**·stable | ic_oos=-0.025 ls_t=-1.80 mono=-0.4 alpha_surv=1.14 sty_r²=0.128 max_corr=**0.469@F007** incr=-0.030 | 5d Mean trend-removal 不破 upper-shadow family (F007/F008 共线), 信号衰减 35% | [[batches/batch_078/candidates/C001]] |
| C002 | ❌ reject | b076/C001 | mean_centering | ✓·aligned·strong·good·**high(F008)**·stable | ic_oos=-0.047 ls_t=-6.36 mono=-1.0 alpha_surv=1.18 sty_r²=0.062 max_corr=**0.471@F008** incr=-0.040 | **设计错误 — TsRank rank-invariant under affine transform**, 减 0.5 是 no-op, 与 b076/C001 数学等价. P025 升格 | [[batches/batch_078/candidates/C002]] |
| C003 | ❌ reject | b072/C006 | window_sweep | ✓·aligned·strong·borderline·**severe(F024)**·stable | ic_oos=-0.048 ls_t=-7.72 mono=-0.9 alpha_surv=0.604 sty_r²=0.110 max_corr=**0.819@F024** incr=-0.028 | 60→30d 缩窗几何上 80%+ 共线 F024 (trade_density), window_sweep 不破 admit 后 saturation | [[batches/batch_078/candidates/C003]] |
| C004 | ❌ reject | b053/C001 | retro_post_floor | **❌**·misaligned·weak·borderline·high(F002)·**unstable** | **ic_oos=+0.0025 < 0.008 HARD-GATE FAIL**, mono FLIP +0.30/-0.80, ls_t=-0.20, alpha_surv=2.74 (noise放大) | 信号已 collapse — alpha decay confirmed (b053 → b078 间隔 25 batches). retro_post_floor 假设原信号守恒被证伪. P026 升格 | [[batches/batch_078/candidates/C004]] |
| C005 | ❌ reject | b050/C001 | rhs_change | ✓·aligned·strong·**poor(0.331)**·high(F012)·stable | ic_oos=+0.029 ls_t=+4.11 mono=**+1.0/+1.0 PERFECT** alpha_surv=0.478 sty_r²=**0.331** max_corr=**0.628@F012** incr=+0.011 | turnover→num_trades RHS 落回 amihud family, microstructure liquidity 几何同源, 整体 family 已被 F012/F017/F018 占满. P027 升格 | [[batches/batch_078/candidates/C005]] |
| C006 | ❌ reject | b058/C001 | rhs_change | ✓·aligned·strong·**poor(0.359)**·**severe(F018)**·stable | ic_oos=+0.0385 (batch high) ls_t=+4.21 mono=**+1.0/+1.0 PERFECT** alpha_surv=0.413 sty_r²=**0.359** max_corr=**0.790@F018** incr=+0.008 | F018 admit 后, sign-freq × liquidity rank-diff 几何已塌缩. RHS 切换反而**加深** F018 共线 (0.576 → 0.790). P028 升格 | [[batches/batch_078/candidates/C006]] |

**档位编码**：🟢 最优档（aligned/strong/good/low/stable）· 🟡 次档（mixed/borderline/acceptable/medium）· 🟠 边际 · 🔴 阻断档（misaligned/weak/poor/high/unstable）.

## 跨候选对比 — minor-path revival 系统性失败

**5 种复活路径 vs library saturation 对照**:

| 路径 | 候选 | 来源 reserve | 当时 max_corr | 本批 max_corr | Δ max_corr | 失败模式 |
|---|---|---|---|---|---|---|
| rhs_change (同 family) | C001 | b076/C005 (0.45@F008) | 0.45 | 0.469@F007 | +0.02 | 5d Mean ≈ raw close, 同 upper-shadow family |
| mean_centering | C002 | b076/C001 (0.47@F008) | 0.47 | 0.471@F008 | +0.00 | TsRank 仿射不变, 数学 no-op |
| window_sweep | C003 | b072/C006 (0.24) | 0.24 | **0.819@F024** | **+0.58** | 60→30 共线; **F024 admit 后 saturation 升级** |
| retro_post_floor | C004 | b053/C001 (alpha_surv=0.37 卡 0.40) | -0.69 | 0.526@F002 | — | **alpha decay** — 25 batches 后信号消失 |
| rhs_change (跨 atom 同 family) | C005 | b050/C001 (0.50@F017) | 0.50 | 0.628@F012 | +0.13 | turnover→num_trades 仍在 liquidity family |
| rhs_change (跨 atom 同 family) | C006 | b058/C001 (0.576@F018) | 0.58 | **0.790@F018** | **+0.21** | RHS 切换反而**加深** F018 共线 |

**关键洞察**:

1. **Library saturation accumulates monotonically (P028 升格 candidate)**: reserve 在当时 reserve 时未通过的 max_corr 阻断, 经过 25-30 batches admit 演进**只会更糟**. 库内 admit 的同 family 因子越多, 复活越难. 不存在"等阈值变松了再复活"的免费午餐 — saturation pressure 单调递增.

2. **Minor-path revival fails on saturated families (P027 升格 candidate)**: rhs_change 同 family 内换 RHS / mean_centering 仿射变换 / window_sweep 时间窗微调 — 这三种 "改表达式不改阈值" 的最小路径**不足以破 admit factor 几何饱和**. 真要复活必须升级:
   - **python residualize** (cross-section OLS residual against blocking factor) — DSL 表达不出
   - **跨 family rhs_change** (e.g. liquidity proxy → fundamental basis 或 temporal basis)
   - **structural transform** (Mean → Std/Skew 量纲层升级, Sub → Div 形式升级)

3. **Mean-centering by constant on rank-form is no-op (P025 升格 candidate)**: TsRank/CsRank 是 rank-invariant under monotonic transform. C002 减 0.5 与 b076/C001 数学等价 — Phase 1 设计 checklist 应直接 reject 此类 trivial path. **Phase 1 自检规则**: rank-form 内部仿射变换 (a*x + b, a>0) 直接判等价.

4. **Reserve alpha decay (P026 升格 candidate)**: b053/C001 在 25 batches 之前 ls_Sharpe=2.45 mono PERFECT, 现 ic_oos=+0.0025 mono FLIP. **chronologically aged reserve (≥1 year) 信号衰减不可避免**, retro_post_floor path 必须独立验证当前信号强度. 不存在"原信号永恒"假设.

5. **Strong intrinsic signal ≠ admit-eligible (signal vs 库 fit 的本质矛盾)**: C005 / C006 的 mono PERFECT 1.0/1.0 在历史 batch 上是 admit-grade 表现 (b076 F025 admit 时 mono=+0.9 较低), 但在当前 saturated 库内仍 reject. 因为 admit 决策是 **incremental utility (max_corr + incr_ic)** 而非 **intrinsic strength** — 强信号若被库内已有因子完全 explain 则零增量价值.

6. **direction-level 反思 (本 NEW direction 价值评估)**: reserve_revival_paths 作为 direction 价值不在 admit 数量, 而在揭示 **library evolution → reserve obsolescence law** — 6 reject 全部是 systematic finding, 直接产出 4 个 P-level lesson 升格 candidate (P025-P028). 这是 Phase 5 consolidation 应该升格的 cross-batch pattern.

## Thread 进展

> [!failure]+ T001 [[directions/reserve_revival_paths#T001]] — `[× DISPROVEN batch_078]` (TsRank-quantization minor revival)
> **Question**: rhs_change (同 family 替分母) / mean_centering / window_sweep 能否破 TsRank-family reserve 的 saturated max_corr 阻断?
>
> **Answer**: **DISPROVEN**. C001 (rhs_change) max_corr 仅从 F008→F007 横向移动量级不变; C002 (mean_centering) 数学等价 no-op; C003 (window_sweep) max_corr 0.24→0.819 反向恶化 (F024 admit 后 saturation upgrade). **三种 minor path 全部失败**.
>
> **Evidence trail**:
> - [[batches/batch_078/candidates/C001|b078 C001]] rhs_change 5d Mean trend-removal → reject (max_corr 0.469@F007)
> - [[batches/batch_078/candidates/C002|b078 C002]] mean_centering 减 0.5 → reject (TsRank 仿射不变, 与原表达式数学等价)
> - [[batches/batch_078/candidates/C003|b078 C003]] window_sweep 60→30 → reject (max_corr 0.819@F024 saturation upgrade)

> [!failure]+ T002 [[directions/reserve_revival_paths#T002]] — `[× DISPROVEN batch_078]` (rank_diff_geometry minor revival)
> **Question**: retro_post_floor (floor codify 后规则改了 retest) / rhs_change (跨 atom 同 family) 能否复活 b053/b050/b058 的 rank_diff_geometry reserve?
>
> **Answer**: **DISPROVEN**. C004 (retro_post_floor) ic_oos=+0.0025 hard-gate fail + mono FLIP — alpha decay confirmed; C005 (rhs_change turnover→num_trades) max_corr 0.628@F012 落回 amihud family; C006 (rhs_change H/L_60→num_trades) max_corr **0.790@F018 加深** F018 共线. **整个 microstructure liquidity rank-diff 几何空间已被 F012/F017/F018 占满**.
>
> **Evidence trail**:
> - [[batches/batch_078/candidates/C004|b078 C004]] retro_post_floor b053/C001 → reject (alpha decay, hard-gate fail)
> - [[batches/batch_078/candidates/C005|b078 C005]] rhs_change b050/C001 → reject (max_corr 0.628@F012 amihud collapse)
> - [[batches/batch_078/candidates/C006|b078 C006]] rhs_change b058/C001 → reject (max_corr 0.790@F018 加深耦合)

> [!success]+ T003 [[directions/reserve_revival_paths#T003]] — `[✓ DISCOVERED batch_078]` (library decoupling check yields meta-finding)
> **Question**: 各 path_type 的 max_corr 与库内具体 blocking factor 关系如何?
>
> **Answer**: **REVEALED**. Library saturation 单调递增律 — 6 reserve 当时 max_corr 阻断在原 batch 时受 1-2 个因子卡, 25-30 batches 后受 3-5 个 factor 同时阻断. `Δ max_corr` 全为正或大幅恶化 (C003 +0.58, C006 +0.21), 无一变松. 这是 NEW finding, 升格为 P028 lesson candidate.

## P-level lesson 升格 candidate (本批新增)

| Code | Lesson | Source |
|---|---|---|
| P025 | rank-form 内部仿射变换 (a*x + b, a>0) 是 TsRank/CsRank 的 no-op, Phase 1 设计 checklist 应直接 reject | C002 setup error |
| P026 | reserve alpha decay — chronologically aged reserve (≥1 year, ≥20 batches) 在 retest 时信号可能完全消失, retro_post_floor 不假设守恒 | C004 b053/C001 alpha decay |
| P027 | rhs_change 必须跨 family — 同 family 内换 RHS (turnover→num_trades, amount→num_trades) 不破共线性, microstructure liquidity 是同 hypersurface 的不同投影 | C005/C006 |
| P028 | Library saturation accumulates monotonically — reserve 推迟复活无收益, 反而越来越难; minor-path revival (rhs_change/mean_centering/window_sweep) 不破已 saturated family | 整体 |

## 本 NEW direction 后续策略

**direction status**: `active` 维持 (NEW direction 首批 0 admit 但产出 4 个 P-level finding), 不立即 dead.

**Next batch 选项** (orchestrator 决策):
1. **方向内深化 — Python residualize 路径**: 把 b076/C005 (alpha_surv=1.43) 信号 cross-section regress F007/F008 取 residual, 用 python_factor 入库. 跳出 DSL 表达限制.
2. **方向内深化 — 跨 family rhs_change**: 把 b050/C001 / b058/C001 的 RHS 从 microstructure liquidity 换成 fundamental ($pe_ratio_60d_mean / $debt_to_asset_ratio_ttm) 测真正解耦.
3. **direction 切换**: 若 reserve revival 路径已 fully explored, 切换到其他 frontier (e.g. 对未在 reserve audit 报告中出现的 NEW signal hypothesis).
4. **Phase 5 consolidation 触发**: rounds_since_consolidation=5 + 4 个 P-level finding — 距 10 round 阈值还有 5, 但 finding 密度高, 可考虑提前触发 calibration phase 把 P025-P028 fold 进 lessons.md.

**红线信号**: rounds_since_consolidation 已到 5 (距 10 阈值过半), 加本批 4 个 P-level lesson candidate, **建议 next round consolidation eligible**.
