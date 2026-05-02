---
direction_tag: reserve_revival_paths
status: active
priority: high
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
status_changed_at: '2026-05-02T06:00:00Z'
status_change_reason: NEW direction — direct flip-candidate revival (audit-driven,
  not frontier exploration)
---
# reserve_revival_paths

## Hypothesis

`research audit reserves` 报告 51 个 flip-candidate, 部分 reserve 因当时阈值或库内 saturated factor blocking 被卡, 但**结构上信号强 + 与现库可解耦**。本方向不在新 frontier 探索, 而是用"改表达式不改阈值"的复活路径直接重测最强 6 个 reserve, 验证 pipeline 是否产出真错杀。

## Threads

### T001 [✗ DISPROVEN batch_078] — TsRank-quantization family revival (C001 / C002 / C003)

**Question**: rhs_change (同 family 替分母) / mean_centering / window_sweep 能否破 TsRank-family reserve 的 saturated max_corr 阻断?

来源: b076/C005 (alpha_surv=1.43, incr_ic=+0.042 强 POS), b076/C001 (mono PERFECT, alpha_surv=1.18), b072/C006 (ls_t=-7.54 整库顶级, mono=-1.00)
共性: TsRank time-series 量纲化形式, 但因 max_corr 卡在 saturated F008 / incr_ic 不及阈卡死
路径: rhs_change (替分母去 trend), mean_centering (减 0.5 / 减 rolling mean), window_sweep (60→30)

**Answer (b078 DISPROVEN)**: C001 (rhs_change) max_corr 仅从 F008→F007 横向移动量级不变; C002 (mean_centering) 数学等价 no-op; C003 (window_sweep) max_corr 0.24→0.819 反向恶化. 三种 minor path 全部失败.

**Evidence trail**:
- [[batches/batch_078/candidates/C001|b078 C001]] rhs_change → reject (max_corr 0.469@F007)
- [[batches/batch_078/candidates/C002|b078 C002]] mean_centering → reject (TsRank 仿射不变, 数学等价)
- [[batches/batch_078/candidates/C003|b078 C003]] window_sweep → reject (max_corr 0.819@F024)

### T002 [✗ DISPROVEN batch_078] — rank_diff_geometry family revival (C004 / C005 / C006)

**Question**: retro_post_floor (floor codify 后规则改了 retest) / rhs_change (跨 atom 同 family) 能否复活 b053/b050/b058 的 rank_diff_geometry reserve?

来源: b053/C001 (mono PERFECT, ls_Sharpe=2.45, max_corr=-0.694@F020 反向耦合 = 互补不重复), b050/C001 (mono PERFECT, incr_ic=+0.013), b058/C001 (ic_oos=+0.055 batch high, ICIR=+0.40)
共性: rank_diff_geometry CsRank-Sub-CsRank 量纲化形式, alpha_surv 卡在 0.30 floor 边界 (post-floor codify 后部分应通过)
路径: retro_post_floor (b053 直接 retest), rhs_change (b050 离开 turnover, b058 离开 H/L_60 family)

**Answer (b078 DISPROVEN)**: C004 (retro_post_floor) ic_oos=+0.0025 hard-gate fail + mono FLIP — alpha decay confirmed; C005 (rhs_change turnover→num_trades) max_corr 0.628@F012 落回 amihud family; C006 (rhs_change H/L_60→num_trades) max_corr 0.790@F018 加深耦合.

**Evidence trail**:
- [[batches/batch_078/candidates/C004|b078 C004]] retro_post_floor → reject (alpha decay, hard-gate fail)
- [[batches/batch_078/candidates/C005|b078 C005]] rhs_change → reject (max_corr 0.628@F012)
- [[batches/batch_078/candidates/C006|b078 C006]] rhs_change → reject (max_corr 0.790@F018)

### T003 [✓ ANSWERED batch_078] — Library decoupling check

**Question**: 各 path_type 的 max_corr 与库内具体 blocking factor 关系如何? 是否可识别系统性 saturation pattern?

每候选必须报告 max_corr to F001-F025 库内全因子, 验证 path_type 是否实际破除 saturated family blocker。失败模式: max_corr 仍 >0.30 → path 选错, 应换更激进的 RHS (e.g. fundamental basis 而非 microstructure)。

**Answer (b078 ANSWERED)**: Library saturation 单调递增律 — 6 reserve 当时 max_corr 阻断在原 batch 时受 1-2 个因子卡, 25-30 batches 后受 3-5 个 factor 同时阻断. `Δ max_corr` 全为正或大幅恶化, 无一变松. P028 升格 candidate.

**Evidence trail**:
- 6 candidate 全部 max_corr ≥ 0.45, 5/6 在 admit 后 saturation 升级
- C003 max_corr 0.24→0.819 (Δ+0.58) F024 admit 后
- C006 max_corr 0.576→0.790 (Δ+0.21) F018 saturation 加深

## Known Failures

本节登记所有 reject candidate, 防止后续 batch 重蹈表达式 (P008 anti-recap rule).

- **batch_078/C001** (rhs_change b076/C005): `TsRank(Div(Mul(Add($high,$low),0.5), Add(Mean($close,5),1e-9)), 60)` — 5d Mean trend-removal 不破 upper-shadow family, max_corr=0.469@F007, incr_ic=-0.030. Failure: rhs_change 同 family 内分母替换无效.
- **batch_078/C002** (mean_centering b076/C001): `TsRank(Sub(Div(Sub($close,$low),Add(Sub($high,$low),1e-9)),0.5), 60)` — TsRank rank-invariant under affine transform, 与 b076/C001 数学等价. Failure: mean_centering 是 no-op (P025 升格).
- **batch_078/C003** (window_sweep b072/C006): `TsRank(Div($amount, Add($num_trades,1e-9)), 30)` — 30d 与 60d TsRank 80%+ 共线, max_corr=0.819@F024 saturation 升级. Failure: window_sweep 在 admit 后 saturation 不破共线.
- **batch_078/C004** (retro_post_floor b053/C001): `Sub(CsRank(Std(Div(Sub($close,$open),Add(Sub($high,$low),1e-9)),20)),CsRank(Mean(Div(Abs(Sub($close,Ref($close,1))),Add($amount,1e-9)),60)))` — 信号已 alpha decay, ic_oos=+0.0025 hard-gate fail + mono FLIP. Failure: retro_post_floor 假设原信号守恒被证伪 (P026 升格).
- **batch_078/C005** (rhs_change b050/C001): `Sub(CsRank(Mean(Div(Abs(Sub($close,$open)),Add(Sub($high,$low),1e-9)),5)),CsRank(Mean($num_trades,20)))` — turnover→num_trades 落回 amihud family, max_corr=0.628@F012, sty_r²=0.331 poor. Failure: rhs_change 在同 microstructure liquidity family 内换 RHS 不破共线 (P027 升格).
- **batch_078/C006** (rhs_change b058/C001): `Sub(CsRank(Mean(Sign(Sub($open,Ref($close,1))),60)),CsRank(Mean($num_trades,20)))` — F018 admit 后 sign-freq × liquidity 几何已塌缩, RHS 切换反而加深 (max_corr 0.576→0.790@F018), sty_r²=0.359 poor. Failure: rhs_change 跨 atom 同 family 在 admit 后 saturation 失败 (P028 升格).

## Narrative Log

### batch_078 (round 78, NEW direction debut)

**Verdict summary**: 0 admit / 0 reserve / 6 reject — minor-path revival 假设全面证伪.

**核心发现**: 6 个 reserve (来自 b050/b053/b058/b072/b076, 间隔 25-30 batches) 在 5 种 minor 复活路径 (rhs_change 同 family / mean_centering / window_sweep / retro_post_floor / rhs_change 跨 atom 同 family) 下**全部不破 max_corr 阻断**. 路径系统性失败模式:

- **C001 rhs_change b076/C005**: 5d Mean trend-removal → max_corr 0.469@F007 (从 F008 横移, 量级未变), 信号衰减 35%
- **C002 mean_centering b076/C001**: 减 0.5 是 TsRank 仿射 no-op, 与原表达式数学等价 (P025 设计 checklist 升格)
- **C003 window_sweep b072/C006**: 60→30d 缩窗 max_corr **0.24→0.819@F024** 反向恶化 (F024 admit 后 saturation upgrade)
- **C004 retro_post_floor b053/C001**: ic_oos=+0.0025 hard-gate fail + mono FLIP — alpha decay confirmed (b053 → b078 间隔 25 batches, 信号已消失, P026 升格)
- **C005 rhs_change b050/C001**: turnover→num_trades 落回 amihud family, max_corr 0.628@F012 (P027 跨 family rhs_change 升格)
- **C006 rhs_change b058/C001**: H/L_60→num_trades 反而**加深** F018 共线 (0.576→0.790, P028 library saturation 单调律升格)

**Library evolution insight**: reserve 在当时 reserve 时 max_corr 阻断由 1-2 因子卡, 25-30 batches 后由 3-5 因子同时阻断. `Δ max_corr` 全为正或大幅恶化, 无一变松. **不存在"等阈值变松了再复活"的免费午餐 — saturation pressure 单调递增**.

**P-level lesson 升格 candidate**: P025 (rank-form 仿射 no-op), P026 (reserve alpha decay), P027 (rhs_change 必须跨 family), P028 (library saturation 单调累积).

**Next batch 策略**: 方向内深化必须升级到 (a) python residualize 跳出 DSL, 或 (b) 跨 family rhs_change (microstructure → fundamental basis), 或 (c) structural transform (Mean→Std/Skew 量纲层升级). Minor-path 已 fully ruled out.

**rounds_since_consolidation=5**, 加本批 4 个 P-level lesson candidate, **建议 next round 提前触发 consolidation 把 finding 升格 lessons.md**.
