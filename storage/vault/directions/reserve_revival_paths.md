---
direction_tag: reserve_revival_paths
status: disproven
priority: low
rounds: 2
admits: 0
last_batch: batch_078
last_admits: []
last_goal: "Round 78 NEW direction — reserve_pool retro audit driven (51 flip-candidates).\n\
  6 candidates 直接处理最强 reserve 复活路径, \"改表达式不改阈值\":\n  C001 rhs_change   — TsRank(midprice/Mean(C,5),\
  \ 60)  ← b076/C005\n  C002 mean_centering — TsRank(close_position - 0.5, 60) ← b076/C001\n\
  \  C003 window_sweep — TsRank(amount/num_trades, 30)  ← b072/C006\n  C004 retro_post_floor\
  \ — Sub(CsRank(Std(body/range,20)), CsRank(Mean(amihud_proxy,60))) ← b053/C001\n\
  \  C005 rhs_change   — Sub(CsRank(Mean(body/range,5)), CsRank(Mean(num_trades,20)))\
  \ ← b050/C001\n  C006 rhs_change   — Sub(CsRank(Mean(Sign(open-Ref(close,1)),60)),\
  \ CsRank(Mean(num_trades,20))) ← b058/C001\n红线: alpha_surv>=0.40 (TsRank fam) /\
  \ >=0.30 (rank_diff_geometry fam); max_corr<0.30; |corr market_cap|<0.3"
last_activity: '2026-05-02T06:20:11Z'
created_batch: batch_078
members: []
retired_members: []
reserves: []
merged_into: null
created_from: cockpit_round_78_reserve_pool_retro_audit_51_flip_candidates
status_changed_at: '2026-05-02T06:20:11Z'
status_change_reason: DISPROVEN — b078 dedicated revival experiment 6/6 reject;
  minor-path revival (rhs_change 同 family / mean_centering / window_sweep / retro_post_floor)
  系统性证伪; 仅 Python residualize / 跨 family / 跨 direction 三路径生还
---
# reserve_revival_paths

> **STATUS: DISPROVEN (b078).** Minor-path revival hypothesis 全面证伪。本方向作为 audit
> 工具留档，**不再批新候选**。后续 reserve 复活只走以下生还路径，且应在新 direction
> (e.g. `library_residualize_python`) 内执行：
> 1. **Python residualize** — cross-section OLS residual against blocking admit factor (DSL 表达不出)
> 2. **跨 family rhs_change** — microstructure → fundamental basis 或 temporal basis (同 family RHS 切换无效，P027)
> 3. **跨 direction 机制复现** — 把 reserve 的机制 (e.g. P008 escape) 在不同 direction 测 generalizability
>
> 已 DISPROVEN minor paths (default-skip in generator pre-check)：rank-form 仿射变换 (no-op, P025) /
> 同 family rhs_change (P027) / window_sweep (saturation 加深, P028) / retro_post_floor for aged reserves
> (alpha decay, P026)。

## Hypothesis (DISPROVEN)

**原假设**: `research audit reserves` 报告 51 个 flip-candidate, 部分 reserve 因当时阈值或库内 saturated
factor blocking 被卡, 但结构上信号强 + 与现库可解耦; 用"改表达式不改阈值"的 minor 复活路径 (rhs_change /
mean_centering / window_sweep / retro_post_floor) 应可重测出真错杀。

**b078 证伪**: 6 候选 / 5 minor 路径 / 0 admit 0 reserve 6 reject。`Δ max_corr` 全为正或大幅恶化 (C003
+0.58, C006 +0.21), 无一变松。**Library saturation 单调累积律 (P028)** — reserve 在原 batch 时 max_corr
阻断由 1-2 个 admit 因子卡, 25-30 batches 后由 3-5 个 admit 因子同时阻断 + admit family 内 absorbing
prototype 形成 (F024 trade-density / F025 OHLC shape / F018 sign-freq liquidity)。**不存在"等阈值变松了
再复活"的免费午餐**。

## Threads (all closed)

### T001 [✗ DISPROVEN b078] — TsRank-quantization family revival (C001 / C002 / C003)

rhs_change / mean_centering / window_sweep 不破 TsRank-family reserve saturated max_corr 阻断。
- C001 rhs_change b076/C005: max_corr F008→F007 横移量级不变 (0.45→0.469), 信号衰减 35%
- C002 mean_centering b076/C001: TsRank 仿射不变 → 与原表达式**数学等价 no-op** (P025)
- C003 window_sweep b072/C006: 60→30d 缩窗 max_corr **0.24→0.819@F024** 反向恶化 (F024 admit 后 saturation upgrade)

### T002 [✗ DISPROVEN b078] — rank_diff_geometry family revival (C004 / C005 / C006)

retro_post_floor / rhs_change (跨 atom 同 family) 不复活 rank_diff_geometry reserve。
- C004 retro_post_floor b053/C001: ic_oos=+0.0025 hard-gate fail + mono FLIP — **alpha decay confirmed**
  (b053 ls_Sharpe=2.45 → b078 25 batches 间隔信号消失, P026)
- C005 rhs_change b050/C001: turnover→num_trades 落回 amihud family, max_corr 0.628@F012 (P027)
- C006 rhs_change b058/C001: H/L_60→num_trades 反而**加深** F018 共线 (0.576→0.790, P028)

### T003 [✓ ANSWERED b078] — Library decoupling check

Library saturation 单调递增律：6 reserve 当时 max_corr 阻断 1-2 因子卡, 25-30 batches 后受 3-5 个
factor 同时阻断。`Δ max_corr` 全为正或大幅恶化, 无一变松 → P028 升格 candidate。

## Known Failures

防止后续 batch 重蹈表达式 (P008 anti-recap rule)。

- **b078/C001** (rhs_change b076/C005): `TsRank(Div(Mul(Add($high,$low),0.5), Add(Mean($close,5),1e-9)), 60)` — 5d Mean trend-removal 不破 upper-shadow family, max_corr=0.469@F007, incr_ic=-0.030.
- **b078/C002** (mean_centering b076/C001): `TsRank(Sub(Div(Sub($close,$low),Add(Sub($high,$low),1e-9)),0.5), 60)` — TsRank affine-invariant, 与 b076/C001 数学等价 (P025 升格).
- **b078/C003** (window_sweep b072/C006): `TsRank(Div($amount, Add($num_trades,1e-9)), 30)` — 30d 与 60d TsRank 80%+ 共线, max_corr=0.819@F024 saturation 升级 (P028).
- **b078/C004** (retro_post_floor b053/C001): `Sub(CsRank(Std(Div(Sub($close,$open),Add(Sub($high,$low),1e-9)),20)),CsRank(Mean(Div(Abs(Sub($close,Ref($close,1))),Add($amount,1e-9)),60)))` — alpha decay, ic_oos=+0.0025 hard-gate fail + mono FLIP (P026 升格).
- **b078/C005** (rhs_change b050/C001): `Sub(CsRank(Mean(Div(Abs(Sub($close,$open)),Add(Sub($high,$low),1e-9)),5)),CsRank(Mean($num_trades,20)))` — turnover→num_trades 落回 amihud family, max_corr=0.628@F012 (P027 升格).
- **b078/C006** (rhs_change b058/C001): `Sub(CsRank(Mean(Sign(Sub($open,Ref($close,1))),60)),CsRank(Mean($num_trades,20)))` — sign-freq × liquidity 几何已塌缩, RHS 切换 max_corr 0.576→0.790@F018 反而加深 (P028 升格).

## Narrative Log

### batch_078 (DISPROVEN — minor-path revival 假设全面证伪)

**Verdict**: 0 admit / 0 reserve / 6 reject。

**核心发现**: 6 个 reserve (b050/b053/b058/b072/b076, 间隔 25-30 batches) × 5 种 minor 路径
(rhs_change 同 family / mean_centering / window_sweep / retro_post_floor / rhs_change 跨 atom
同 family) → **全部不破 max_corr 阻断**。

**P-level 升格** (4 律, 跨 specialist 共识 — pattern_analyst/016 + calibration/008 +
hypothesis_promoter/013):
- **P025** rank-form 仿射 no-op: TsRank/CsRank rank-invariant under affine `(a*x+b, a>0)`. C002 减
  0.5 是数学 no-op, Phase 1 设计 checklist 必须 reject。
- **P026** reserve alpha decay: aged reserve (≥1 year, ≥20 batches) retest 时信号可完全消失
  (b053 ls_Sharpe=2.45 mono PERFECT → b078 ic_oos=+0.0025 mono FLIP)。retro_post_floor 路径**不
  假设原信号守恒**。
- **P027** rhs_change 必须跨 family: 同 microstructure liquidity family 内换 RHS
  (turnover→num_trades, amount→num_trades, H/L_60→num_trades) 不破共线 — microstructure liquidity
  是同 hypersurface 的不同投影。复活必须升级到 (a) python residualize 跳出 DSL; (b) 跨 family rhs_change
  (microstructure → fundamental); (c) structural transform (Mean→Std/Skew)。
- **P028** library saturation 单调累积: reserve 推迟复活无收益, 反而越来越难。`Δ max_corr` 全为
  正或恶化, 无一变松。

**Library evolution insight**: 当时 reserve max_corr 由 1-2 因子卡, 25-30 batches 后由 3-5 个 admit
同时阻断 + family-internal absorbing prototype 形成 (F024 / F025 / F018)。

**Cross-finding consensus** (pattern_analyst/016 + calibration/008 共同结论):
- minor-path revival **DISPROVEN**, default-skip in generator pre-check
- 仅生还路径: Python residualize / 跨 family rhs_change / structural transform / 跨 direction 机制复现
- 5 个高价值候选 (b072/C006, b076/C005, b080/C006, b081/C006, barra_residual_alpha pool b012-014) 仅
  via 升级路径复活, 推荐迁移到新 direction `library_residualize_python` (library_gap/013)
- still-reserve pool 28 个 alpha_surv direction-floor fail — **真饱和**, 无 revival path 可推荐

**Direction 终态**: status → DISPROVEN。本方向不再批新候选；reserve 复活全部走 (a) `library_residualize_python`
(Python wrapper track), (b) 跨 family / 跨 direction 新方向, 或 (c) current-evaluator re-judge with
ic_by_year sign-stability check。
