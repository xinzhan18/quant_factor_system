---
direction_tag: institutional_flow_proxy
status: probing
priority: medium
rounds: 5
admits: 0
last_batch: batch_100
last_admits: []
last_goal: 'Reserve revival pool #2 (round 91 closed window/reciprocal/P008-third
  axes — 5/6 axes disproven, only rank-diff Sub(TsRank60,TsRank20) b091/C004 partial-pass
  ls_t=-2.20 reserve). This batch pursues 4 explicit revival paths from direction.md
  T001 conclusion NOT touched by round 91: (a) shorter RHS rank-diff at multiple window
  pairs (60-10, 60-5, 120-60) for sharper regime-climax detection, (b) cross-field
  rank-diff with RHS swapped to non-num_trades ratio fields (escape F024 reciprocal
  envelope), (d) compound interactions. Skip path (c) CsRank-of-composite due to known
  qlib custom-op re-parse limitation. All candidates self-checked vs P030 (alpha_surv
  > 1.0 alone NOT admit, need incr_ic / max_corr / ls_t 2/3), P031 (P008 3-condition:
  TsRank>=60d + ratio + dim-less — pass), P032 (rank-diff geometry 7 laws — RHS scale-invariant
  ratio, no shared raw field, no same-field cross-window — checked per-candidate),
  P033 (sign-flip-via-reciprocal — closed in round 91, no candidates rely on it).
  All 6 are bona fide new geometry beyond round 91 6-axis closure.'
last_activity: '2026-05-16T07:07:25Z'
created_batch: batch_072
members: []
retired_members: []
reserves:
- batch_072_C006
- batch_091_C004
- batch_100_C001
- batch_100_C004
merged_into: null
created_from: cockpit_round_72_new_field_$num_trades
---
# institutional_flow_proxy

> [!abstract]+ 方向概要
> - **状态**　🟡 `probing` · priority `medium` · rounds = 4 · admits = 0 · reserves = 4 (b072/C006 + b091/C004 + b100/C001 + b100/C004)
> - **最近**　[[batches/batch_100/judge|batch_100]] · 2026-05-16 · 0/2/4
> - **一句话**　rank-diff shorter-RHS 几何 (60-10, 60-5) 真正脱 F024 anchor 邻域 + ls_t 单调升级 (-2.20→-2.60→-2.94) — 但 mt_bucket=high 'CP03 最高 borderline' 政策卡线，需 Python residualize 或方向 alternate 才能 admit。

---

## Hypothesis

**经济学逻辑** — `$amount/$num_trades` 是单笔成交均额，机构倾向更大单子；该 ratio 的时序 anomaly 携带 institutional flow regime change 信息。

**与 b068/C002 raw level 的几何区分**：raw daily level 隐式嵌入 vol_20d（高 amount/低 num_trades 同时指向高 vol stocks，vol_20d_exp=9.75 + alpha_surv=0.13 catastrophic）。本方向所有 alive 候选必须额外引入：(a) 时间维度过滤 (rolling Std/Corr/TsRank)，(b) ordinal 量纲剥离 (CsRank)，(c) 双 atom 复合 (rank-diff)。

**几何独立性**：F001-F023 admitted 无 `$num_trades`；avg_trade_size 与 amount level/CV (F002/F015/F043) 分子分母都换。但 round 91 实证 F024 `TsRank($num_trades/$volume,60)` 在 30-120d 窗口轴上是 width≥90d 的引力盆地，TsRank ratio 路径已被 F024 占位大半。

**红线**：
- `|corr|>0.3` to `$market_cap` reject（$num_trades 与 size 强正相关）
- `alpha_survival ≥ 0.40`, `max_corr<0.30` to library 标准 admit 门槛
- `vol_20d_exp > 25%` AND `alpha_survival < 0.30` 三立 → reject

**reserve revival 焦点（核心未决）**：b072/C006 reserve 的 incr_ic 改善路径已经在 round 91 6-axis sweep 中证伪 5/6 — window 全段闭锁、reciprocal 等价、P008-third-ratio sign-flip duplicate；仅 rank-diff `Sub(TsRank60, TsRank20)` (b091/C004) 真正脱 F024 anchor 邻域，但 ls_t 不足。下一波复活只能尝试：(a) 更短 RHS rank-diff、(b) 跨字段 rank-diff、(c) CsRank 二次包裹、(d) Python residualize on F024+F012 重测 incr_ic/ls_t。

---

## Threads

### T001: avg_trade_size 时序几何 (rolling Std + TsRank + rank-diff) [◉ ACTIVE]

> [!note]+ Thread 当前
> **Question**: avg_trade_size 时序波动 / anomaly / rank-diff 是 institutional flow regime change proxy，能脱 vol_20d 吸收 + F024 anchor 邻域？
>
> **Answer (round 100 update)**: **Path (a) shorter-RHS rank-diff 真正脱 F024 anchor — 双 reserve (b100/C001 60-10, b100/C004 60-5) 升级 ls_t -2.60/-2.94 但仍 mt-capped borderline；Path (b) cross-field rank-diff 3/3 hard-gate sign_flip 系统失败；Path (a) longer-LHS (60→120) degenerate — rank-diff direction-asymmetric 律确立**。
>
> **Evidence trail**:
> - [[batches/batch_072/candidates/C001|batch_072 C001]] Std form vol_20d 三立 reject (vol_20d_exp=26.7)
> - [[batches/batch_091/candidates/C001|batch_091 C001-C003]] TsRank window 轴扫: 30/90/120d 全 high@F024 引力盆地，alpha_surv 单调下降
> - [[batches/batch_091/candidates/C005|batch_091 C005]] Reciprocal axis monotonic sign-flip dup
> - [[batches/batch_091/candidates/C006|batch_091 C006]] P008-third-ratio max_corr=0.957@F024 字段对 reciprocal dup
> - [[batches/batch_091/candidates/C004|batch_091 C004]] **rank-diff 60-20 reserve** max_corr=0.18@F016 + incr_ic=+0.008 + alpha_surv=0.862 + ls_t=-2.20
> - [[batches/batch_100/candidates/C001|batch_100 C001]] **rank-diff 60-10 reserve** max_corr=0.18@F028 + incr_ic=+0.010 + alpha_surv=0.77 + ls_t=-2.60 (超 b091/C004)
> - [[batches/batch_100/candidates/C004|batch_100 C004]] **rank-diff 60-5 reserve** max_corr=0.22@F028 + incr_ic=+0.009 + alpha_surv=0.39 + ls_t=-2.94 (最强)
> - [[batches/batch_100/candidates/C002|batch_100 C002]] cross-field rank-diff RHS=$amount/$volume → sign_flip reject (P032 law #2 binding)
> - [[batches/batch_100/candidates/C003|batch_100 C003]] cross-field RHS=$turnover_rate → sign_flip reject
> - [[batches/batch_100/candidates/C005|batch_100 C005]] longer-LHS 60-120 → IS ic≈0 sign undefined reject (direction-asymmetric)
> - [[batches/batch_100/candidates/C006|batch_100 C006]] cross-field RHS=raw $volume → sign_flip reject (P031 RHS 必须 ratio)
>
> **b072/C006 reserve 火种 (维持)**: ls_t=-7.54 整库顶级 + alpha_surv=0.447 + max_corr=0.24@F009 LOW + vol_20d_exp=10.87
>
> **Next probes**:
> - (i) Python residualize on (F024+F012+F015+F016) 重测 b100/C001 incr_ic — 若残差 ls_t ≥ 3.0 + alpha_surv ≥ 0.50 → admit-track
> - (ii) Engineering 工程修复 qlib `_build_cs_cache` class-name→registered-name map → 解锁 path (c) CsRank-second-wrap
> - (iii) reserve pool 已 4 个 (b072/C006 + b091/C004 + b100/C001 + b100/C004)，跨批 calibration retro triage 可考虑复活路径
>
> **闭锁** (round 100 扩展): window axis 全段 + reciprocal + P008-third-ratio (round 91) + **cross-field rank-diff (path b 全失败)** + **longer-LHS direction degenerate (path a 反向)**。**唯一仍 open**: path (c) CsRank-second-wrap (工程阻塞) + Python residualize (需 escape hatch)。

### T002: $num_trades raw level retail attention [✗ DISPROVEN batch_072]

> [!failure]+ Thread 结论
> C002 `CsRank($num_trades)` max_corr=0.75@F012 NEAR_DUPLICATE + vol_20d_exp=30.9 + incr=-0.038。**关键 insight**: raw $num_trades CsRank = size × Amihud 联合代理，被 F012 (`-|return|/$amount`) 通过 size 共线性 anchor。**新字段 ≠ 新几何空间**。已升格 lessons "raw $num_trades CsRank default-skip"。

### T003: rank-diff vs general liquidity 分离 [✗ DISPROVEN batch_072]

> [!failure]+ Thread 结论
> C003 `Sub(CsRank(avg_trade_size), CsRank(Mean($amount,20)))` hg 三立: sign_flip + oos_decay=-1.888 + mono_sign_flip 0.70/-1.00。P001 rank-diff 7 律 #6 — RHS `Mean(amount,20)` 死亡 endpoints anchor 跨字段族不可解锁。**复活路径**: 换 RHS 脱 amount/turnover/H-L_60 死亡 family。

### T004: price-flow Corr OFI proxy [✗ DISPROVEN batch_072]

> [!failure]+ Thread 结论
> C004 `Corr(avg_trade_size, $close, 20)` alpha_surv=0.25 三立 + dom=vol_20d。Daily rolling correlation 不脱 vol_20d basis。**复活路径**: 需 minute-bar OFI（daily 不可行）。

### T005: institutional × short-momentum cross-product [✗ DISPROVEN batch_072]

> [!failure]+ Thread 结论
> C005 `Mul(CsRank(avg_trade_size), CsRank(Sub($close, Ref($close,5))))` ls_t=-7.32 PASS + alpha_surv=0.526 PASS + max_corr=0.46@F009 borderline + incr_ic=-0.027 强 NEG。cross-product 形式与 F009 (overnight pv_corr_5) 几何同源吸收。P008 软判定 reject。

---

## Known Failures

| Batch | Candidate | Expression | Reject reason |
|---|---|---|---|
| [[batches/batch_072/candidates/C001\|batch_072 C001]] | C001 | `Std(Div($amount, $num_trades), 20)` | P004 vol_20d 三立: alpha_surv=0.17 + sty_r²=0.25 + vol_20d_exp=26.7 + dom=vol_20d |
| [[batches/batch_072/candidates/C002\|batch_072 C002]] | C002 | `CsRank($num_trades)` | CP05 NEAR_DUPLICATE max_corr=0.75@F012 + style_r²=0.59 + vol_20d_exp=30.9 + incr=-0.038 |
| [[batches/batch_072/candidates/C003\|batch_072 C003]] | C003 | `Sub(CsRank(Div($amount, $num_trades)), CsRank(Mean($amount, 20)))` | hg 三立: sign_flip + oos_decay=-1.888 + mono_sign_flip 0.70/-1.00 |
| [[batches/batch_072/candidates/C004\|batch_072 C004]] | C004 | `Corr(Div($amount, $num_trades), $close, 20)` | alpha_surv=0.25 三立 + dom=vol_20d (sty_r²=0.09) |
| [[batches/batch_072/candidates/C005\|batch_072 C005]] | C005 | `Mul(CsRank(Div($amount, $num_trades)), CsRank(Sub($close, Ref($close, 5))))` | P008 软判: ls_t=-7.32 + max_corr=0.46@F009 + incr=-0.027 NEG |
| [[batches/batch_091/candidates/C001\|batch_091 C001]] | C001 | `TsRank(Div($amount, $num_trades), 30)` | P030 三立: incr_ic=-0.012 NEG + max_corr=0.79@F024 HIGH |
| [[batches/batch_091/candidates/C002\|batch_091 C002]] | C002 | `TsRank(Div($amount, $num_trades), 90)` | P030 三立: incr_ic=-0.007 NEG + max_corr=0.75@F024 HIGH |
| [[batches/batch_091/candidates/C003\|batch_091 C003]] | C003 | `TsRank(Div($amount, $num_trades), 120)` | P030 三立: incr_ic=-0.006 NEG + max_corr=0.71@F024 + alpha_surv=0.398 边界破 |
| [[batches/batch_091/candidates/C005\|batch_091 C005]] | C005 | `TsRank(Div($num_trades, $amount), 60)` | Reciprocal sign-flip duplicate of b072/C006, max_corr=0.84@F024 |
| [[batches/batch_091/candidates/C006\|batch_091 C006]] | C006 | `TsRank(Div($volume, $num_trades), 60)` | hg near_duplicate: max_corr=0.957@F024 字段对 reciprocal duplicate |
| [[batches/batch_100/candidates/C002\|batch_100 C002]] | C002 | `Sub(TsRank(Div($amount,$num_trades),60), TsRank(Div($amount,$volume),60))` | hg sign_flip: train +0.0057 / val -0.0127 (P032 law #2 binding — LHS/RHS 共享 $amount numerator) |
| [[batches/batch_100/candidates/C003\|batch_100 C003]] | C003 | `Sub(TsRank(Div($amount,$num_trades),60), TsRank($turnover_rate,60))` | hg sign_flip: train +0.0297 / val -0.0031 + ic_oos_min fail (RHS $turnover_rate 不满足 P031 完整三条件) |
| [[batches/batch_100/candidates/C005\|batch_100 C005]] | C005 | `Sub(TsRank(Div($amount,$num_trades),120), TsRank(Div($amount,$num_trades),60))` | hg train ic≈0 (4e-5) sign undefined — longer-LHS direction-asymmetric degeneracy |
| [[batches/batch_100/candidates/C006\|batch_100 C006]] | C006 | `Sub(TsRank(Div($amount,$num_trades),60), TsRank($volume,60))` | hg sign_flip: train +0.0321 / val -0.0027 + ic_oos_min fail (RHS raw $volume 不脱 size embedding) |

---

## Narrative Log

- **2026-05-02 (round 72 created)**: NEW direction from cockpit hint — `$num_trades` 2026-05-01 新增字段，库内仅 b068 一次使用 (raw level reject)，rolling/rank-diff/interaction 几何完全未探索。

- **2026-05-02 (batch_072 judged)**: admit=0 reserve=1 (C006) reject=5. 5/5 PASS-hg mono_oos=-1.00 PERFECT + sign_consistency=1.0 — `$num_trades` 几何在 csi1000 daily 是 reversal 方向。**C006 `TsRank(avg_trade_size,60)` 最强发现**: ls_t=-7.54 整库顶级 + alpha_surv=0.447 + style_r²=0.15 + max_corr=0.24@F009 LOW + vol_20d_exp=10.87 (vs C001 Std 26.7, 降 60%)；唯一阻断 incr_ic=-0.018 micro-NEG → reserve。**P009 发现**: TsRank 时序量纲化在 ratio 字段上大幅降 vol_20d_exp (65%↓) + style_r² (75%↓)，是新 vol_20d-escape 路径。**P010 发现**: alpha_surv>0.30 + incr_ic<0 软判 reject vs reserve 边界 = 设计层是否含独立新几何。

- **2026-05-02 (round 73 Phase 5 consolidation)**: 4 元教训升 lessons.md — (a) Path Selection "TsRank window≥60d on ratio fields is new vol_20d-escape" + raw $num_trades 不构成新几何；(b) macro lesson "csi1000 daily fundamental+institutional flow 真饱和" 路径 e；(c) Hot Topics P006 "P008 软判定补丁"。**calibration/005 verdict**: C006 reserve 维持 NOT admit，trigger #1-#4 不立，不放宽 incr_ic floor。direction 维持 probing，火种活跃 + library_gap/009 提议 5-candidate follow-up batch `tsrank_timeseries_ratio`。

- **2026-05-16 (batch_100 judged, reserve revival pool #2)** · [[batches/batch_100/judge|batch_100]]: admit=0 reserve=2 (C001 60-10, C004 60-5) reject=4 (C002/C003/C006 cross-field hard-gate, C005 longer-LHS degenerate). **Path (a) shorter-RHS 真正脱 F024 anchor**: C001 ls_t=-2.60 + alpha_surv=0.77 + max_corr=0.18@F028 + incr_ic=+0.010 + sign_consistency=1.0 + monotonicity_oos=-1.0 + cum_ic_mdd=-15 极浅，超越 b091/C004 reserve（ls_t -2.20→-2.60，max_corr 0.18@F016→0.18@F028 — anchor 都换了）。C004 (60-5) ls_t=-2.94 最强但 alpha_surv=0.39 微低 threshold 0.40。**Path (b) cross-field rank-diff 系统失败**: 3/3 hard-gate sign_flip — P032 law #2 'raw field 独立' 在 ratio-vs-ratio (C002 共享 $amount) 和 ratio-vs-raw (C006 RHS raw $volume) 都 binding；C003 RHS=$turnover_rate 不满足 P031 完整三条件，IS overfit / OOS noise。**Path (a) longer-LHS direction degenerate** (C005 60-120): IS ic≈4e-5 sign undefined → rank-diff 'direction-asymmetric' 律确立 (LHS 基础窗 + RHS 更短才有效，反方向 cancellation)。**MT bucket=high 满载** (cumulative 552→558, direction 6→12, exposure 1.0) → 'CP03 最高 borderline' 政策硬卡 reserve 不至 admit。**Engineering blocker**: path (c) CsRank-of-composite 因 qlib `_build_cs_cache` 用 `str(self.feature)` 序列化时返回类名 'TsRankOp' 而非注册名 'TsRank'，re-parse fail；C004/C005 原设计被迫降级。修复 1-line（_CUSTOM_OPS 反向 map），可解锁 path (c) 整个轴。direction 维持 probing；reserve pool 升级至 4 个；下批可切方向或工程修复后回访。

- **2026-05-16 (batch_091 judged, reserve revival pool #1)**: admit=0 reserve=1 (C004 rank-diff) reject=5 (3 窗口扫 + 2 reciprocal duplicates). 复活 b072/C006 的 6 axes (window 30/90/120d + rank-diff + reciprocal + P008-third-ratio) **5/6 axes 闭锁，仅 rank-diff 突破** (C004 max_corr=0.18@F016 LOW + incr_ic=+0.008 PASS + alpha_surv=0.862 + Barra residual IC sign flip — 真正脱 F024 anchor 邻域)。但 ls_t=-2.20 + mt_bucket=high → reserve only。**反直觉 P032 候选**: window 30→60→90→120d alpha_surv 单调下降 0.558→0.447→0.418→0.398 — TsRank 长窗口在 ratio 字段反而加重 vol_20d 嵌入（与 P031 "TsRank ≥ 60d" escape 三条件微张力，提示窗口"过长"也有上界）。**F024 anchor 邻域确认**: width≥90d 引力盆地，非 60d 点锚。**Reciprocal canonical 漏检升格候选**: generator 应在 freeze 时识别 `TsRank(Div(a,b),N)` ≡ `TsRank(Div(b,a),N)` 的 reciprocal 等价。T001 深化（window/reciprocal/P008-third-ratio 三轴 disproven, rank-diff 轴 partial-progress）。direction 维持 probing（双 reserve 火种）；下批若再 0-admit → 考虑转 saturated。
