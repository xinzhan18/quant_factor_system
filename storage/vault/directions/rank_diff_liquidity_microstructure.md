---
direction_tag: rank_diff_liquidity_microstructure
status: saturated
priority: high
rounds: 2
admits: 0
last_batch: batch_096
last_admits: []
last_goal: "Round 96 — rank-diff axis ls_t boost without Python residualize (daily_python\n\
  registry confirmed NO residualize template; degrading to DSL-only revival paths).\n\
  4 reserves (b091/C004 + b095/C001/C002/C006) cluster ls_t∈[-2.03,-2.60] < 3.0\n\
  admit floor — 6 DSL-only candidates explore 3 boost mechanisms:\n\nT005 EXTENSION\
  \ (4 candidates): Smoothing geometry sweep on b091/C004 base form.\nC001 10d Mean\
  \ wrap (extends b095/C006 5d Mean), C002 7d EMA wrap (decay-weighted\nsmoothing,\
  \ distinct from flat Mean), C005 Slope(rank-diff, 10) (trend-of-rank-diff\nacceleration\
  \ — geometric novelty: turns level→derivative signal), C006 60/40\nsub-axis (1.5:1\
  \ ratio, fills gap between disproven 3:1 long and tested 60/20).\n\nT006 NEW THREAD\
  \ (2 candidates): LHS field swap to scope-extend rank-diff axis.\nC003 Sub(TsRank($turnover_rate,60),TsRank($turnover_rate,20))\
  \ — dim-less rate\nfield (NOT raw size-coupled atom; T003 disproven only for size-coupled\
  \ raw\n$amount). C004 Sub(TsRank(amount/num_trades,120),TsRank(amount/num_trades,60))\n\
  — longer total window 2:1 ratio (untested sub-axis, distinct from 60/20 3:1\nand\
  \ 90/30 3:1).\n\nSelf-check 5 hard rules (round 73 + round 91 升格):\n- P030 alpha_surv>1.0\
  \ paradox: no single-form dependence; all candidates have\n  multi-CP rationale\
  \ targeting ls_t boost not alpha_surv inflation\n- P004-deep path-integral: Mean/EMA/Slope\
  \ are single-step wrappers on existing\n  rank-diff series (NOT cumsum/path-integral;\
  \ rank-diff input is already 60d\n  historical, smoothing/slope wraps don't add\
  \ memory layer)\n- P028 Cov-equiv: NO Cov atom; all rank-diff via TsRank\n- Reciprocal\
  \ duplicate: TsRank(1/x,N)=N+1-TsRank(x,N) — C003 turnover_rate\n  direction explicitly\
  \ NOT inverse-form of any admitted; C004 amount/num_trades\n  forward direction\
  \ (NOT 1/x)\n- Cross-section OLS sign-flip: N/A (no Python residualize in this batch\
  \ by\n  degradation; sign_consistency check is judge-time on raw output)\n- Reciprocal\
  \ duplicate of C006 b095 (Mean-then-Sub identity): C005 NOT linear\n  Mean-on-each-leg\
  \ (which would be identity); C005 is Slope wrap which is\n  non-linear in rank-diff\
  \ output — distinct geometry confirmed\n\nAnchor avoidance per b095:\n- F024 anchor\
  \ (TsRank($num_trades/$volume,60)): all candidates use LHS that's\n  NOT $num_trades/$volume\
  \ (C001-C002-C005-C006 use $amount/$num_trades; C003\n  uses $turnover_rate; C004\
  \ uses $amount/$num_trades) → no anchor collision\n- F012 anchor (Amihud=Mean(Abs(ret)/amount,20)):\
  \ all candidates avoid Amihud\n  structure; rank-diff axis is fundamentally different\
  \ geometry from Amihud\n  level\n- F015/F016 (CsRank-diff cluster): all candidates\
  \ use TsRank not CsRank → time\n  domain not cross-section domain\n\nBaseline-first\
  \ 守则 explicit skip: 15 TTM-untouched fields are fundamentally\nunrelated to microstructure\
  \ rank-diff geometry of this direction — TTM fields\nout of hypothesis scope. All\
  \ candidates use OHLCV/microstructure fields only.\n\nTarget: ≥1 admit (ls_t ≥ 3.0)\
  \ OR ≥1 boost-mechanism validated (alpha_surv ≥\n0.5 + ls_t > -2.0 marking T005/T006\
  \ productive). zero_admit_streak=8 context;\ncalibration_trigger already true from\
  \ b095 — this batch is final attempt before\norchestrator may dispatch calibration\
  \ flow."
last_activity: '2026-05-15T23:25:50Z'
created_batch: batch_095
members: []
retired_members: []
reserves: []
merged_into: null
created_from: fork_from_institutional_flow_proxy_T001_rank_diff_escape_b091_C004_first_PASS
---
# rank_diff_liquidity_microstructure

> [!abstract]+ 方向概要
> - **状态**　🟠 `saturated` (round 96 后定格) · priority `high` · rounds = 2 · admits = 0 · reserves 累计 7
> - **一句话**　**Rank-diff axis** `Sub(TsRank(field, long_N), TsRank(field, short_N))` 在 amount/num_trades 域几何 escape 真实 (max_corr≤0.19 + alpha_surv≥0.50) 但 **DSL-only 路径下 ls_t 自然上限 ≈ 2.6** 远低于 3.0 admit floor —— **唯一剩余复活路径 = Python OLS cross-section residualize**（daily_templates 当前无该模板）。
> - **来源**　institutional_flow_proxy T001 rank-diff sub-axis fork (b091/C004 first PASS) → 本方向 6 sub-axis (T001–T006) 全部探索完成。

---

## Hypothesis

**核心 hypothesis**: `Sub(TsRank(X, N_long), TsRank(X, N_short))` 是 **双窗口 self-cancellation 时序几何** —— cross-section 信号集中在 regime transition（长 vs 短时间尺度 trend acceleration/deceleration），区别于单 TsRank 的"个股相对历史水平"。

**axis 律（b091+b095+b096 三批联立精炼）**:
- ✅ **PASS 域**: dim-less ratio LHS（amount/num_trades）+ 双窗口 self-cancellation + 短窗 RHS（10–30d）+ 任意 smoothing wrapper
- ❌ **FAIL 域**: close-position（b092） + overnight（b094） + raw size-coupled atom（T003） + 跨字段撞 anchor（T002） + 多阶差（T004） + 单一 rate/level LHS（T006） + Slope 类 derivative wrap（T005 C005）

**ls_t 上限律 ⚠️ (b096 升格)**:
> rank-diff axis 在 DSL-only 路径下 ls_t 自然上限 ≈ 2.6 < 3.0 admit floor。窗口比 sweep 6:1→3:1→2:1→1.5:1 全部 ls_t∈[-2.03, -2.60]；smoothing operator type/depth（flat Mean → exp-weighted EMA → 5d→10d）仅影响 risk cleanness（alpha_surv 0.36→0.51），**不影响 ls_t**。证明 ls_t 瓶颈在 **cross-section dispersion 域** 而非 time-series noise 域；trade-off 律：smoothing 调 alpha_surv 不动 ls_t；窗口窄化降 style+corr 同时降 ls_t magnitude。两路径正交但都不可达 admit floor。

**DSL 不可达 ⚠️ (b096 升格)**:
> 本方向 reserve 池 7 候选（b091/C004 + b095/C001/C002/C006 + b096/C001/C002/C006）全部 max_corr ≤ 0.19、alpha_surv≥0.50、错杀 3–4/4 件套 —— **库空间独立的 alpha 真实存在**，但 DSL 表达层无法 boost ls_t 跨越 admit floor。

**Python residualize 唯一路径 ⚠️ (b095/b096 next_hint, 仍待开发)**:
> b095 next_hint 提出唯一未走的复活路径 = **Python OLS cross-section residualize on (F012 + F024 + vol_20d)** —— 通过显式 strip 三大 size×liquidity basis exposure 后重测 ls_t，看 alpha "净化" 是否破 3.0。b096 因 `src/research/daily_templates/registry.py` 无 residualize template **被迫降级**走 DSL-only smoothing/window sweep，结果实证 DSL 路径全数耗尽。**该 Python template 不开发 → 本方向终结。**

**红线**（仍生效，但本方向 saturated 后不再下新批）:
- `|corr|>0.3` 至 `$market_cap` reject
- `alpha_survival ≥ 0.40` + `max_corr<0.30` to library
- `vol_20d_exp > 25%` AND `alpha_survival < 0.30` 三立 → reject

---

## Current Focus

**已 saturated**。所有 6 sub-axis（T001–T006）DSL 探索完成；T001/T005 active 但接近耗尽，T002/T003/T004/T006 disproven。**进入 stand-by 状态等待**：
1. Python OLS cross-section residualize template 开发（解 b095 next_hint）
2. calibration 流程对 reserve pool 整体重评估（C002 EMA alpha_surv=0.49 + C006 60/40 style_r²=0.06 优先 admit 候选）

不出新批次。

---

## Threads

### T001: RHS window 比 sweep [✓ EXHAUSTED]

> [!success]- Thread 结论
> **Question**: 窗口比变化（6:1 / 3:1 / 2:1 / 1.5:1）能否突破 ls_t 瓶颈？
>
> **Answer**: **exhausted, all ls_t < 3.0**. 窗口比 sweep 结果:
>
> | 比例 | LHS/RHS | ls_t | 状态 |
> |---|---|---|---|
> | 6:1 | 60/10 | -2.60 | reserve (b095/C001) |
> | 3:1 | 60/20 | -2.20 | reserve (b091/C004 base) |
> | 3:1 | 90/30 | -2.03 | reserve (b095/C002) |
> | 2:1 | 120/60 | hard_gate fail | reject (b096/C004) |
> | 1.5:1 | 60/40 | -2.13 | reserve (b096/C006, style_r²=0.06 最干净) |
>
> 长窗等比扩展（90/30）不放大信号；2:1 长窗 train_ic≈0 cross-section spread 失效；1.5:1 窄窗 risk 最干净但 ls_t magnitude 同步降。**ls_t 与 window ratio 在 DSL 域无单调改善路径**。

### T002: 跨字段 rank-diff RHS swap [✗ DISPROVEN]

> [!failure]- Thread 结论
> **b095/C003** `Sub(TsRank(amount/num_trades,60), TsRank(amount/volume,60))` → max_corr=-0.74@F024（$volume 分母同源）+ sign_flip + oos_decay double fail。F024/F012 anchor 在 amount/num_trades/volume domain 高度密集 → 跨字段 RHS 空间被夹。

### T003: Raw size-coupled atom rank-diff [✗ DISPROVEN]

> [!failure]- Thread 结论
> **b095/C004** `Sub(TsRank($amount,60), TsRank($amount,20))` → vol_20d_exp=38.4 catastrophic + alpha_surv=1.03 P030 paradox + ls_t=-0.63 weak。**升格 lessons**: rank-diff axis 必须配 dim-less ratio LHS（P008 frontier 三必要条件之一）；raw size-coupled atom 默认 reject。

### T004: HP-2nd-order rank-diff (acceleration) [✗ DISPROVEN]

> [!failure]- Thread 结论
> **b095/C005** `Sub(Add(TsRank60,TsRank10), Mul(TsRank20,2))` → triple hard_gate fail, alpha_surv=7.80 paradox 极致。**升格 lessons**: rank-form (TsRank/CsRank) 不可做 N>1 阶差扩展 —— rank space ordinal 破坏 Taylor-series 几何, HP-Hodrick-Prescott smoothing 多阶 rank-diff 默认 pre-Phase2 reject。

### T005: outer smoothing wrap [✓ EXHAUSTED]

> [!success]- Thread 结论
> **Question**: smoothing wrapper 能否打 ls_t admit floor？
>
> **Answer**: **smoothing operator 只动 alpha_surv 不动 ls_t**。
>
> | candidate | wrap | alpha_surv | ls_t | 状态 |
> |---|---|---|---|---|
> | b095/C006 | Mean 5d | 0.50 | -2.50 | reserve |
> | b096/C001 | Mean 10d | 0.36 | -2.46 | reserve |
> | b096/C002 | EMA 7d | **0.49** (+36%) | -2.52 | reserve |
> | b096/C005 | Slope 10d | — | hard_gate triple fail | reject |
>
> Slope 类 derivative wrap rank space 不支持稳定 derivative 提取（train +0.0021 vs val -0.0051 sign_flip + ic_oos<0.008 + oos_decay=-2.4）。**关键发现**: ls_t 瓶颈在 cross-section dispersion 不在 time-series noise → smoothing 路径正交于 ls_t 维度。

### T006: rank-diff axis LHS field swap [✗ DISPROVEN]

> [!failure]- Thread 结论
> **b096/C003** `Sub(TsRank($turnover_rate,60),TsRank($turnover_rate,20))` → ls_t=-0.75 + Q1-Q5 中段非线性（Q3=-0.000316 最低, Q5=-0.000072 反弹）+ alpha_surv=0.94 临 P030 + vol_20d=34.01 catastrophic + 2015 sign-flip。
>
> **结论 (T002+T003+T006 联立)**: **rank-diff axis LHS 非 amount/num_trades family path 基本封闭**。
>
> **升格 lessons-candidate**: rank-diff axis 限定 ratio LHS = numerator/denominator where both are 微观 flow fields ($amount, $num_trades, $volume) —— 单一 rate/level field LHS 不构成有效 cross-section spread。

---

## Known Failures

| Candidate | Expression | Reject Reason |
|---|---|---|
| [[batches/batch_095/candidates/C003\|b095/C003]] | `Sub(TsRank(amount/num_trades,60), TsRank(amount/volume,60))` | hard_gate: sign_flip + oos_decay; max_corr=0.74@F024 (RHS volume 同源) |
| [[batches/batch_095/candidates/C004\|b095/C004]] | `Sub(TsRank($amount,60), TsRank($amount,20))` | CP03 weak (ls_t=-0.63), CP04 vol_20d_exp=38.4, P030 paradox |
| [[batches/batch_095/candidates/C005\|b095/C005]] | `Sub(Add(TsRank60,TsRank10), Mul(TsRank20,2))` | hard_gate triple fail; HP-2nd-order rank space 不支持, alpha_surv=7.80 paradox |
| [[batches/batch_096/candidates/C003\|b096/C003]] | `Sub(TsRank($turnover_rate,60),TsRank($turnover_rate,20))` | CP03 weak (ls_t=-0.75), CP04 vol_20d_exp=34 + alpha_surv=0.94, CP06 2015 sign-flip |
| [[batches/batch_096/candidates/C004\|b096/C004]] | `Sub(TsRank($amount/$num_trades,120),TsRank($amount/$num_trades,60))` | hard_gate: train_ic≈0 sign undefined + oos_decay=-278; 120d 稀释 train period |
| [[batches/batch_096/candidates/C005\|b096/C005]] | `Slope(Sub(TsRank60,TsRank20),10)` | hard_gate triple: sign_flip + ic_oos<0.008 + oos_decay=-2.4; rank space 无稳定 derivative |

## Reserve Pool (7 候选, 库空间独立, ls_t∈[-2.03, -2.60])

| Candidate | Expression | ls_t | alpha_surv | max_corr | 错杀件 |
|---|---|---|---|---|---|
| [[batches/batch_091/candidates/C004\|b091/C004]] | rank-diff 60/20 base | -2.20 | 0.86 | 0.18 | 4/4 |
| [[batches/batch_095/candidates/C001\|b095/C001]] | rank-diff 60/10 | -2.60 | 0.77 | 0.18 | 4/4 |
| [[batches/batch_095/candidates/C002\|b095/C002]] | rank-diff 90/30 | -2.03 | 0.68 | 0.18 | 4/4 |
| [[batches/batch_095/candidates/C006\|b095/C006]] | Mean(rank-diff, 5) | -2.50 | 0.50 | 0.19 | 4/4 |
| [[batches/batch_096/candidates/C001\|b096/C001]] | Mean(rank-diff, 10) | -2.46 | 0.36 | 0.19 | 3/4 |
| [[batches/batch_096/candidates/C002\|b096/C002]] | EMA(rank-diff, 7) | -2.52 | **0.49** | 0.19 | 3.5/4 |
| [[batches/batch_096/candidates/C006\|b096/C006]] | rank-diff 60/40 | -2.13 | **0.51** | **0.14** | 3/4 |

**reserve pool 最强 admit 候选**: C002 EMA wrap（alpha_surv +36%）+ C006 60/40（style_r²=0.06, max_corr=0.14 最干净）。两者待 Python residualize 或 calibration 流程复活。

---

## Related

- 🟢 [[institutional_flow_proxy]] `probing` —— 母方向，T001 rank-diff sub-axis fork 出本方向
- 🟡 [[tsrank_timeseries_ratio]] `saturated` —— F024 anchor 所在方向；rank-diff form 是 TsRank-ratio frontier 的 derivative axis
- 🥈 [[factors/F024|F024]] —— `TsRank($num_trades/$volume,60)` 主 anchor
- 🥈 [[factors/F012|F012]] —— `Amihud_20d` 同源 cluster anchor
- 🥇 [[factors/F015|F015]] / 🥇 [[factors/F016|F016]] —— `CsRank-diff` cluster, 与 TsRank-diff 是 cross-section vs time-series 对偶
- [[lessons#Path Selection]] (P008 frontier + reserve revival paths)
- [[lessons#Structural Constraints]]

---

## Narrative Log

> [!quote]+ 2026-05-16 · [[batches/batch_096/judge|batch_096]] judge
> **DSL-only revival path 实证 ls_t boost 不可达；rank-diff axis cross-section dispersion 自然上限 < 3.0** · admit=0 / reserve=3 (C001/C002/C006) / reject=3 (C003/C004/C005)
>
> - **Python residualize 降级**: b095 next_hint 唯一未走路径 (Python OLS cross-section residualize) 因 `src/research/daily_templates/registry.py` 无 residualize 模板而降级；该路径需先开发模板。
> - **T001 RHS window sweep exhausted**: C004 120/60 (2:1) hard_gate fail; C006 60/40 (1.5:1) reserve (ls_t=-2.13 最弱 + style_r²=0.06 最干净)；窗口比 sweep 6:1→3:1→2:1→1.5:1 全 ls_t < 3.0。
> - **T005 smoothing wraps explored**: C001 (10d Mean) alpha_surv 不变；C002 (7d EMA) alpha_surv 0.36→**0.49** (+36%) 但 ls_t 不动；C005 (Slope) hard_gate triple fail。**关键发现**: smoothing operator type/depth 仅影响 risk cleanness, 不影响 ls_t —— 证 ls_t 瓶颈在 cross-section dispersion 而非 time-series noise.
> - **T006 NEW + DISPROVEN**: C003 ($turnover_rate LHS swap) ls_t=-0.75 + Q1-Q5 中段非线性 + alpha_surv=0.94 临 P030 + 2015 sign-flip; rank-diff axis LHS 非 amount/num_trades family path 基本封闭.
> - **trade-off 律**: smoothing 域可调 alpha_surv 但不动 ls_t；window 比窄化降 style+corr 但同时降 ls_t magnitude。两路径都不可达 ls_t ≥ 3.0.
> - **Reserve 池累计 7 候选** (max_corr ≤ 0.19, 错杀 3-3.5/4 件套, ls_t∈[-2.03,-2.60]); **EMA wrap (C002 alpha_surv=0.49)** + **60/40 (C006 style_r²=0.06)** 为 reserve pool 最强候选.
>
> **MT Budget**: cumulative 534 → **540** · direction 6 → **12** · bucket `medium` (search_adjusted 0.44-0.51)
>
> **Calibration trigger 加强**: zero_admit_streak 8→9; orchestrator 强烈建议 dispatch calibration 流程.
>
> **Operations**　`status: saturated`（exploring → saturated） · rounds 1→2 · reserves +3
> **下一步**: (a) Python residualize 模板开发 → 解 b095 next_hint; (b) calibration 流程对 reserve pool 重评估; (c) 若 (a)(b) 都不复活, 本方向终结.

> [!quote]- 2026-05-16 · [[batches/batch_095/judge|batch_095]] judge
> **rank-diff axis 第 2 批实证 escape geometry, 但统计强度瓶颈未破** · admit=0 / reserve=3 / reject=3
>
> - T001 RHS-window 伸缩: C001 (60/10) + C002 (90/30) 双 reserve, 短端方向有效但 ls_t < 3.0 admit floor 不破; 长端 (90d) 衰减验证"等比扩展不放大信号"反 hypothesis.
> - T002 跨字段 RHS: C003 (amount/num_trades vs amount/volume) **disproven** — RHS=$amount/$volume 撞 F024 anchor.
> - T003 raw atom: C004 (raw $amount) **disproven** — vol_20d_exp=38.4 catastrophic, P008 frontier "ratio 字段"必要条件违反.
> - T004 HP-2nd-order: C005 **disproven (升格 candidate)** — rank space ordinal 不支持 Taylor-series 多阶展开, alpha_surv=7.80 paradox 极致.
> - T005 outer smoothing wrap: C006 (Mean 5d) **reserve**, 本批最强 IC magnitude (-0.019); admission 瓶颈在 cross-section dispersion 不在 IC magnitude.
>
> **axis 律精炼 (b091+本批联立)**:
> - ✅ PASS 域: dim-less ratio LHS (amount/num_trades) + 双窗口 self-cancellation + 短窗 RHS (10-30d) + 任意 smoothing wrapper
> - ❌ FAIL 域: close-position + overnight + raw atom + 跨字段撞 anchor + 多阶差
>
> **MT budget**: cumulative 528 → **534** · direction 0 → **6** · bucket `medium`
>
> **Operations**　`status: exploring` 维持 · rounds 0→1 · reserves +3
> **下一步**: 不再重复同字段双窗口 1 阶 rank-diff; 转向 (a) Python OLS residualize on (F012+F024+vol_20d) 看是否破 ls_t 3.0; (b) T005 7d/10d Mean wrap; (c) reserve 池 4 候选合成.

> [!quote]- 2026-05-16 · batch_095 design
> **新方向创建** — fork from institutional_flow_proxy T001 rank-diff sub-axis. b091/C004 first PASS on rank-diff axis (max_corr=0.18 + alpha_surv=0.862 + incr_ic=+0.008) 触发独立方向化。本批 6 候选沿 5 个 sub-axis (T001-T005) 推 rank-diff geometric space.
>
> **Operations**　`status: exploring (NEW)` · priority `high`
