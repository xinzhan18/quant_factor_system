---
direction_tag: rank_diff_liquidity_microstructure
status: exploring
priority: high
rounds: 1
admits: 0
last_batch: batch_095
last_admits: []
last_goal: 'Round 95 — fork from institutional_flow_proxy T001 rank-diff axis after
  b091/C004 first PASS

  (max_corr=0.18 + alpha_surv=0.862 + incr_ic=+0.008 全 PASS, ls_t=-2.20 weak). 6 candidates

  沿 5 sub-axis 推 rank-diff geometric space on amount/num_trades family:

  C001 (T001) RHS window 短端伸缩 Sub(TsRank60, TsRank10) — 测信号放大;

  C002 (T001) 长窗 3:1 ratio Sub(TsRank90, TsRank30) — 测尺度等比扩展稳态;

  C003 (T002) 跨字段 same window rank-diff Sub(TsRank(amount/num_trades,60), TsRank(amount/volume,60))
  — 测跨 RHS field 脱单 atom 自相关;

  C004 (T003) raw amount baseline rank-diff Sub(TsRank(amount,60), TsRank(amount,20))
  — 测 raw atom 是否仍 escape;

  C005 (T004) HP-2nd-order 3-term Sub(Add(TsRank60, TsRank10), Mul(2, TsRank20)) —
  测 acceleration form;

  C006 (T005) CsRank-wrap base form CsRank(Sub(TsRank60, TsRank20)) — 测 cross-section
  orthogonalization.

  Self-check 5 hard rule 全 PASS: P030 (无候选单边依赖 alpha_surv>1.0, 全候选 multi-CP rationale);

  P004-deep (C005 是 3 single TsRank 复合非 cumsum/path-integral, 每 term 都是 single-step
  TsRank wrapper);

  P028 Cov-equiv (无 Cov atom, 全候选基于 TsRank);

  reciprocal duplicate (PRE-FILTER: TsRank(1/x,N)=N+1-TsRank(x,N) → Sub(TsRank(1/x,60),
  TsRank(1/x,20))

  = -Sub(TsRank(x,60), TsRank(x,20)) monotonic sign-flip duplicate of b091/C004 →
  排除 num_trades/amount form

  + 排除 TsRank(volume/num_trades) 系列 = F024 sign-flip dup);

  rank-diff domain (amount/num_trades 是 b091 实证 PASS 域, 非 close-position self-cancel
  域 [b092 dead]

  非 overnight alpha-cancel 域 [b094 dead]).

  Baseline-first 守则 explicit skip: 15 TTM untouched fields 与本 direction (microstructure
  rank-diff geometry)

  完全不相关 — TTM/fundamental 字段不在本批 hypothesis scope 内. 本批 全 OHLCV/microstructure 字段

  ($amount/$num_trades/$volume).

  Precheck F012 (Amihud, $amount/$num_trades cluster anchor) + F024 (TsRank(num_trades/volume,60))
  +

  F015/F016 (CsRank-diff cluster) max_corr thresholds mandatory in Phase 2.

  Target: 至少 1 admit 或 ≥1 reserve 加 b091/C004 reserve pool. zero_admit_streak=7 上下文,

  本批是 streak 关键反击 (sub-axis 多样性 + b091 finding 直接 leverage).'
last_activity: '2026-05-15T22:55:26Z'
created_batch: batch_095
members: []
retired_members: []
reserves: []
merged_into: null
created_from: fork_from_institutional_flow_proxy_T001_rank_diff_escape_b091_C004_first_PASS
---
# rank_diff_liquidity_microstructure

> [!abstract]+ 方向概要
> - **状态**　🔵 `exploring` (round 95 NEW direction, fork from institutional_flow_proxy T001) · priority `high` · rounds = 0 · admits = 0
> - **一句话**　**Rank-diff axis** `Sub(TsRank(field, long_N), TsRank(field, short_N))` 在 liquidity microstructure (amount/num_trades) 域是 first PASS escape — b091/C004 max_corr=0.18 + alpha_surv=0.862 + incr_ic=+0.008 全 PASS but ls_t=-2.20 weak → 本方向沿 5 个 sub-axis 推 admission floor。
> - **来源**　institutional_flow_proxy T001 rank-diff 子轴在 b091/C004 实证真 escape 后, 该子轴升格独立方向以充分探索 RHS/LHS/window/wrapper/HP-2nd-order 几何空间。

---

## Hypothesis

**核心 hypothesis**: `Sub(TsRank(X, N_long), TsRank(X, N_short))` 是一种**双窗口 self-cancellation 时序几何**，其 cross-section 信号集中在 regime transition (中长期分位变化但短期未跟上 / 短期超前长期) — 不同于单 TsRank 的"个股相对历史水平"，rank-diff 是"长 vs 短时间尺度上 trend acceleration/deceleration"。

**为什么 b091/C004 真 escape**:
1. **max_corr=0.18** — 远低于 F024 anchor (TsRank(num_trades/volume,60)) 邻域；rank-diff 把单 TsRank 锁源拆开 → 几何独立
2. **alpha_surv=0.862** — Barra residual 后仍保留 86% 信号，alpha 真存在
3. **incr_ic=+0.008** PASS — 对库整体有 positive 增量
4. **Barra residual 后 IC sign flip** (+0.014 vs raw -0.016) — 表明信号方向被 Barra 风格"颠倒"，剥离后能看到真 alpha

**为什么 ls_t=-2.20 weak**:
- rank-diff form 是 "双窗口 self-cancellation" — 60d 慢趋势减 20d 快趋势 → 信号主要在 regime change 期才显著，平稳期信号微弱
- 这导致 long-short t-stat 摊薄；ICIR -0.193 也偏弱

**复活路径 (本方向 5 个 sub-axis)**:
- **T001 (本批主)**: RHS window 短端伸缩 — `Sub(TsRank60, TsRank10)`、`Sub(TsRank90, TsRank30)` — 假设：3:1 ratio 增信号
- **T002**: 跨字段 rank-diff — `Sub(TsRank($amount/$num_trades,60), TsRank($amount/$volume,60))` — 假设：同窗换 RHS field 脱 single-atom 自相关
- **T003**: Raw amount 单 atom — `Sub(TsRank($amount,60), TsRank($amount,20))` — 假设：rank-diff 在更基础的 size-coupled atom 上是否仍 escape
- **T004**: HP-style 2nd-order — `Sub(Add(TsRank60, TsRank10), Mul(2, TsRank20))` — 假设：3-term 2 阶差 acceleration 更陡 (注意 P004-deep guard：3 个 single TsRank 复合，非 N-day path-integral)
- **T005**: CsRank-wrap — `CsRank(Sub(TsRank60, TsRank20))` — 假设：外层 cross-section rank 化抹平极端分布，可能改善 ls_t 但 max_corr 也可能上升

**为什么是新 direction 而非 institutional_flow_proxy 延续**:
- institutional_flow_proxy T001 4/5 sub-axis 已 disproven (window sweep / reciprocal / P008-third-ratio)；该 direction 是"avg_trade_size 时序几何"，scope 太窄
- 本方向 axis 是 rank-diff form 本身 — 可适用任何 liquidity microstructure 字段；scope 跨字段（amount/num_trades/volume/turnover）
- 升格条件已满足：b091/C004 实证 rank-diff axis 真存在；rank-diff axis 在不同 LHS 字段上的几何空间未被探索

**与 lessons 风险位的对照**:
- **rank-diff salvage 限定** (lessons "rank-diff salvage 限定")：本方向所有候选 RHS 都不是 F024/F012/turnover_60d 死锚 — 全是同字段双窗口或 same family 跨字段
- **P004-deep 路径积分**: T004 是 3-term 但每 term 都是 single TsRank（非 cumsum/path-integral），通过 guard
- **reciprocal duplicate 律 (b091 升格)**: TsRank(1/x,N)=N+1-TsRank(x,N) → `Sub(TsRank(1/x,60), TsRank(1/x,20)) = -Sub(TsRank(x,60), TsRank(x,20))` monotonic sign-flip duplicate → 本方向**不设此候选**
- **F024 anchor**: 跨字段 RHS 切到 `$amount/$volume` (T002) 已规避 F024 = `TsRank($num_trades/$volume,60)` 共线；T003 raw amount 完全脱 ratio
- **P008 frontier (TsRank-ratio)**: rank-diff form 在 TsRank-ratio frontier 之上加一层 — 是 frontier 的 derivative axis

**红线**:
- `|corr|>0.3` 至 `$market_cap` reject (T003 raw amount 需重点验证 size 共线性)
- `alpha_survival ≥ 0.40` + `max_corr<0.30` to library
- `vol_20d_exp > 25%` AND `alpha_survival < 0.30` 三立 → reject

---

## Current Focus

T001 RHS window 伸缩 + T002 跨字段 RHS 是本批主推；T003 raw atom 作 control，T004 HP-2nd-order 作 stress test，T005 CsRank-wrap 作 stat boost 实验。目标：至少 1 个候选把 ls_t 从 b091/C004 的 -2.20 推到 ≥ 3.0 同时维持 max_corr<0.30 + incr_ic POS。

---

## Threads

### T001: RHS window 短端伸缩 (signal amplification) [◉ ACTIVE]

> [!note]+ Thread 当前
> **Question**: b091/C004 base form `Sub(TsRank($amount/$num_trades,60), TsRank($amount/$num_trades,20))` ls_t=-2.20 weak，将 RHS 短窗从 20d 缩到 10d 是否放大"双窗口 trend acceleration"信号？或拉到 30d 配 LHS=90d 维持 3:1 ratio 是否更稳？
>
> **Evidence trail**:
> - [[batches/batch_091/candidates/C004|batch_091 C004]]　base form 60/20　max_corr=0.18 + alpha_surv=0.862 + incr_ic=+0.008 PASS, ls_t=-2.20 weak → **reserve**
> - [[batches/batch_095/candidates/C001|batch_095 C001]]　60/10 RHS-short　ic_oos=-0.0165 ls_t=-2.60 alpha_surv=0.77 max_corr=0.18 incr_ic=+0.0107 → **reserve** (错杀 4 件套全满足)
> - [[batches/batch_095/candidates/C002|batch_095 C002]]　90/30 长窗 3:1　ic_oos=-0.0143 ls_t=-2.03 alpha_surv=0.68 max_corr=0.18 incr_ic=+0.0050 → **reserve** (长窗等比扩展不放大信号)
>
> **Next probes**: 短端方向 (10d≤RHS≤30d) 已饱和; 转向 (a) Python OLS residualize on (F012+F024+vol_20d), 看是否破 ls_t 3.0 阈; (b) reserve 池合成 (rank-diff family 线性组合 boost ls_t).

### T002: 跨字段 rank-diff (RHS field swap) [✗ DISPROVEN batch_095]

> [!failure]+ Thread 结论
> **Question**: 同窗 60d 下 LHS=$amount/$num_trades RHS=$amount/$volume — 两个 amount-normalized ratio 跨字段 rank-diff 是否 escape 单 atom 自相关同时仍维持 max_corr<0.30？
>
> **Answer**: **disproven (RHS=$amount/$volume 形式)**. RHS=$amount/$volume 撞 F024 anchor (TsRank($num_trades/$volume,60) 同 60d TsRank, $volume 分母同源) → max_corr=-0.74@F024, hard_gate fail (sign_flip + oos_decay). 跨字段 rank-diff 必须避开 RHS 与 admitted anchor 同字段族; F024/F012 anchor 在 amount/num_trades/volume domain 高度密集, 跨字段 RHS 空间被夹.
>
> **Evidence trail**:
> - [[batches/batch_095/candidates/C003|batch_095 C003]]　Sub(TsRank(amount/num_trades,60), TsRank(amount/volume,60))　max_corr=0.74@F024, sign_flip + oos_decay double fail → **reject (hard_gate)**
>
> **复活路径**: 仅 RHS 跨字段族 (microstructure → fundamental basis) 或换 numerator 字段族 (e.g., $turnover_rate based ratio LHS) 才可能突破.

### T003: Raw amount 单 atom rank-diff [✗ DISPROVEN batch_095]

> [!failure]+ Thread 结论
> **Question**: rank-diff form 在不经 ratio 化的 raw $amount 上是否仍 escape F012/F024 anchor？raw amount 自带 size 共线性，rank-diff 把 trend-direction 隔离能否打开？
>
> **Answer**: **disproven**. raw $amount baseline rank-diff 无法 escape size×vol 联合 basis — vol_20d_exp=38.4 库内最高之一; ls_t=-0.63 weak; alpha_surv=1.03 P030 paradox guard 触发 (Barra residual IC sign flip vs raw). P008 frontier 必要条件 "ratio 字段" 违反 — rank-diff axis 限定 dim-less ratio LHS, raw atom 不进入复活路径.
>
> **Evidence trail**:
> - [[batches/batch_095/candidates/C004|batch_095 C004]]　Sub(TsRank($amount,60), TsRank($amount,20))　ls_t=-0.63 weak, vol_20d_exp=38.4 catastrophic, alpha_surv=1.03 (P030 paradox) → **reject**
>
> **Lessons-promotion candidate**: "rank-diff axis 必须配 dim-less ratio LHS (P008 三必要条件之一); raw size-coupled atom (raw $amount/$volume/$turnover_rate level) rank-diff 默认 reject" — 升格至 P008 frontier 完整条件.

### T004: HP-style 2nd-order rank-diff (acceleration form) [✗ DISPROVEN batch_095]

> [!failure]+ Thread 结论
> **Question**: 3-term `Sub(Add(TsRank60, TsRank10), Mul(2, TsRank20))` 形式（Hodrick-Prescott-style 2 阶差代理）能否捕捉到 rank-diff 一阶差捕捉不到的二阶趋势加速度？
>
> **Answer**: **disproven**. rank space (ordinal [0,1] 百分位) 不支持 Taylor-series 多阶展开 — rank 是序数变换, 二阶差不构成 acceleration 几何; 3-term 复合自我抵消导致 ic_oos=-0.0012 几乎为零; alpha_surv=7.80 paradox 极致触发 (Barra residual sign flip 8× magnitude vs raw IC). 信号已 sign_flip + ic_oos_min + oos_decay 三 hard_gate fail.
>
> **Evidence trail**:
> - [[batches/batch_095/candidates/C005|batch_095 C005]]　Sub(Add(R60,R10), Mul(R20,2))　triple hard_gate fail, alpha_surv=7.80 paradox → **reject**
>
> **Lessons-promotion candidate**: "rank-form (TsRank/CsRank) 不可做 N>1 阶差扩展 — rank space ordinal 破坏 Taylor-series 几何, HP-Hodrick-Prescott smoothing 多阶 rank-diff 默认 reject pre-Phase2" — 升格至 lessons.md Forbidden Patterns 段.

### T005: outer smoothing wrap (noise reduction) [◉ ACTIVE]

> [!note]+ Thread 当前
> **Question**: 在 b091/C004 base form 外面套一层 noise-reduction wrapper 是否能改善 ls_t (平滑高频时序噪音保留 regime transition 中段信号)？
>
> 原 design 是 CsRank-wrap，但 Qlib 在 CsRank 的 cross-section cache build 中通过 `str(self.feature)` 重新解析 expression，碰到自定义 TsRank op 时引擎以类名 `TsRankOp` 查 `Operators._ops` 失败 (系统级 limitation)。改用 Mean 5d 实现同 noise-reduction 目标，且 Mean 是 Qlib built-in 不触发 string reparse。
>
> **Evidence trail**:
> - [[batches/batch_095/candidates/C006|batch_095 C006]]　Mean(Sub(TsRank60, TsRank20), 5)　ic_oos=-0.0190 (本批最强 IC magnitude), ls_t=-2.50, alpha_surv=0.50 临界 → **reserve**
>
> **Next probes**: (a) 7d/10d Mean window 上调测 smoothing 深度对 ls_t 的影响; (b) 绕过 Qlib CsRank reparse bug 走 Python 实现真 CsRank-wrap (custom op string repr fix 或 Python factor 直接计算).

---

## Known Failures

| Candidate | Expression | Reject Reason |
|---|---|---|
| [[batches/batch_095/candidates/C003\|C003]] | `Sub(TsRank(amount/num_trades,60), TsRank(amount/volume,60))` | hard_gate: sign_flip + oos_decay; max_corr=0.74@F024 (RHS volume 分母同源 anchor) |
| [[batches/batch_095/candidates/C004\|C004]] | `Sub(TsRank($amount,60), TsRank($amount,20))` | CP03 weak (ls_t=-0.63), CP04 vol_20d_exp=38.4 catastrophic, P030 paradox; raw atom 无 escape size×vol basis |
| [[batches/batch_095/candidates/C005\|C005]] | `Sub(Add(TsRank60,TsRank10), Mul(TsRank20,2))` | hard_gate triple fail (sign_flip + ic_oos_min + oos_decay); HP-2nd-order rank space failure, alpha_surv=7.80 paradox |

---

## Related

- 🟢 [[institutional_flow_proxy]] `probing` — 母方向，T001 rank-diff sub-axis fork 出本方向
- 🟡 [[tsrank_timeseries_ratio]] `saturated` — F024 anchor 所在方向，rank-diff form 是 TsRank-ratio frontier 的 derivative axis
- 🥈 [[factors/F024|F024]] — `TsRank($num_trades/$volume,60)` 主要 anchor，precheck 必看 max_corr threshold
- 🥈 [[factors/F012|F012]] — `Amihud_20d` ($amount/$num_trades 同源 cluster anchor)
- 🥇 [[factors/F015|F015]] / 🥇 [[factors/F016|F016]] — `amihud_cv_rank_diff_20` / `amihud_turnover_cv_rank_diff_20` 是 CsRank-diff cluster，与 TsRank-diff 几何上是 cross-section vs time-series 对偶
- [[lessons#Path Selection]] (P008 frontier + reserve revival paths)
- [[lessons#Structural Constraints]]

---

## Narrative Log

> [!quote]+ 2026-05-16 · [[batches/batch_095/judge|batch_095]] judge
> **rank-diff axis 第 2 批实证 escape geometry, 但统计强度瓶颈未破** · admit=0 / reserve=3 / reject=3
>
> - T001 RHS-window 伸缩: C001 (60/10) + C002 (90/30) 双 reserve, 短端方向有效但 ls_t < 3.0 admit floor 不破; 长端 (90d) 衰减验证"等比扩展不放大信号"反 hypothesis (与 b091 window-sweep alpha_surv 单调下降一致)
> - T002 跨字段 RHS: C003 (amount/num_trades vs amount/volume) **disproven** — RHS=$amount/$volume 撞 F024 anchor (volume 分母同源, max_corr=0.74)
> - T003 raw atom: C004 (raw $amount) **disproven** — vol_20d_exp=38.4 catastrophic, P008 frontier "ratio 字段"必要条件违反
> - T004 HP-2nd-order: C005 **disproven (升格 candidate)** — rank space ordinal 不支持 Taylor-series 多阶展开, alpha_surv=7.80 paradox 极致案例
> - T005 outer smoothing wrap: C006 (Mean 5d) **reserve**, 本批最强 IC magnitude (-0.019), 验证 noise-reduction 改善 IC 但 ls_t 不变 — admission 瓶颈在 cross-section dispersion 不在 IC magnitude
>
> **axis 律精炼 (b091+本批联立)**:
> - ✅ rank-diff axis PASS 域: dim-less ratio LHS (amount/num_trades) + 双窗口 self-cancellation + 短窗 RHS (10-30d) + 任意 smoothing wrapper
> - ❌ rank-diff axis FAIL 域: close-position (b092) + overnight (b094) + raw atom (C004) + 跨字段撞 anchor (C003) + 多阶差 (C005)
>
> **MT budget**: cumulative 528 → **534** · direction 0 → **6** · bucket `medium` (上界, search_adjusted 0.479-0.576)
>
> **Calibration trigger 触发**: zero_admit_streak 7→8 + 最近 3 批累计 admit=0 + reserve 池 ≥1 满足"库空间独立" (C001 错杀 4 件套全满足) → orchestrator 下轮考虑校准诊断流程
>
> **Operations**　`status: exploring` 维持 · rounds 0→1 · admits 0 · reserves +3 (C001/C002/C006)
> **下一步**: 不再重复同字段双窗口 1 阶 rank-diff; 转向 (a) Python OLS residualize on (F012+F024+vol_20d) 看是否破 ls_t 3.0; (b) T005 7d/10d Mean wrap; (c) reserve 池 4 候选合成 (rank-diff family 线性组合 boost ls_t)

> [!quote]- 2026-05-16 · batch_095 design
> **新方向创建** — fork from institutional_flow_proxy T001 rank-diff sub-axis. b091/C004 first PASS on rank-diff axis (max_corr=0.18 + alpha_surv=0.862 + incr_ic=+0.008) 触发独立方向化。本批 6 候选沿 5 个 sub-axis (T001-T005) 推 rank-diff geometric space:
>
> - T001 (RHS window 伸缩, 2 候选): C001 60/10 短端 + C002 90/30 长端 3:1 等比
> - T002 (跨字段 RHS, 1 候选): C003 amount/num_trades vs amount/volume same window
> - T003 (raw atom rank-diff, 1 候选): C004 raw $amount 60/20
> - T004 (HP-2nd-order, 1 候选): C005 acceleration form on amount/num_trades
> - T005 (CsRank-wrap, 1 候选): C006 outer CsRank on base form
>
> Self-check 5 hard rule 全 PASS: P030 (无候选单边依赖 alpha_surv>1.0), P004-deep (T004 是 3 single TsRank 复合非 path-integral), Cov-equiv (无 Cov atom), reciprocal duplicate (排除 num_trades/amount 形式 = sign-flip dup of b091/C004), rank-diff domain (amount/num_trades 是 b091 实证 PASS 域非 close-position 也非 overnight self-cancel 域).
>
> **Operations**　`status: exploring (NEW)` · priority `high`
