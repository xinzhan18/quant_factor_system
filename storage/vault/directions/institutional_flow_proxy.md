---
direction_tag: institutional_flow_proxy
status: probing
priority: medium
rounds: 3
admits: 0
last_batch: batch_091
last_admits: []
last_goal: 'Reserve revival pool #1 (round 91 calibration/013 finding asset-driven):
  probe whether the 6 expression variants of b072/C006 TsRank($amount/$num_trades,60)
  — which passed alpha_surv 0.447 + max_corr 0.24 LOW + ls_t -7.54 top but was blocked
  by incr_ic=-0.018 micro-NEG — can recover incr_ic ≥ +0.005 via (a) window sweep
  30d/90d/120d, (b) rank-diff form (escape F012/F024 anchor cluster), (c) reducer
  reverse (sign-flip equivalence test), (d) volume-based ratio (P008 third atom).
  All candidates self-checked vs P030 (alpha_surv > 1.0 alone ≠ admit), P004-deep
  (no N-day path-integral, all are single-step TsRank wrappers — pass), P028 (no Cov-of-zero-mean-series
  — pass).'
last_activity: '2026-05-15T20:20:25Z'
created_batch: batch_072
members: []
retired_members: []
reserves:
- batch_072_C006
- batch_091_C004
merged_into: null
created_from: cockpit_round_72_new_field_$num_trades
---
# institutional_flow_proxy

> [!abstract]+ 方向概要
> - **状态**　🟡 `probing` (round 72 NEW direction，cockpit 提议) · priority `medium` · rounds = 0 · admits = 0
> - **一句话**　利用 2026-05-01 新增微观字段 `$num_trades`（单日成交笔数），构造 institutional flow proxy（avg_trade_size = $amount/$num_trades）+ retail attention proxy（$num_trades level）+ Order Flow Imbalance 类几何，规避 b068 C002 raw level 形式的 vol_20d 吸收陷阱。
> - **来源**　cockpit round 72 提议 — `$num_trades` 是 2026-05-01 新增字段，库内仅 b068 一次使用（C002/C006 直接 raw level 形式 reject），剩余几何空间（Std/rolling/rank-diff/interaction）完全未被探索；本批是 fundamental escape 最后一搏，若 dead → 下批必触 Phase 5 consolidation。

---

## Hypothesis

**经济学逻辑**：

1. **avg_trade_size flow volatility** — `$amount / $num_trades` 是单笔成交均额（机构倾向更大单子）；其 rolling Std 是"机构流动性"波动率，与单日 level（b068 C002 已 reject）几何不同 — 高波动机构流动 = 机构调仓密集 = forward 信息含量。
2. **$num_trades level = retail attention** — 单日成交笔数本身（不归一化）是散户关注度直接代理；高 num_trades 股票 = 散户高活跃度 = forward reversal 候选（A 股 retail 主导 reversal 律）。
3. **rank-diff vs amount** — `CsRank(avg_trade_size) − CsRank(Mean(amount,20))` 直接做 rank-diff，把"institutional concentration"从"general liquidity level"中分离 — 测试 P001 rank-diff 范式能否在 institutional flow 几何上突破。
4. **price-size correlation = OFI proxy** — `Corr(avg_trade_size, $close, 20)` 测试机构 buying-on-up 模式（institutional money tends to follow trend）— Order Flow Imbalance 的 cross-section 估计。
5. **institutional × short-momentum interaction** — `CsRank(avg_trade_size) × CsRank(5d return)` — 机构集中度 × 短期动量。如果机构买在涨势，rank product 应正向；机构买在跌势（contrarian），rank product 应负向。
6. **time-series rank of avg_trade_size** — `TsRank(avg_trade_size, 60)` — 测试机构流入"个股层 abnormal"是否携带 forward signal（vs cross-section level，时间维度的 anomaly）。

**与 b068 C002 raw level 的几何区分**：

- b068 C002 是 raw daily level — vol_20d_exp=9.75 + alpha_surv=0.13 catastrophic（单 cross-section level 隐式嵌入 vol，因为高 amount/低 num_trades 同时指向高 vol stocks）。
- **本批所有候选都引入额外几何维度**：(a) rolling Std/Corr/TsRank → 时间维度过滤；(b) CsRank → ordinal 形式剥离量纲；(c) rank-diff 或 interaction → 双 atom 复合脱单 vol 嵌入。

**与 OHLCV admitted 因子几何独立性**：F001-F023 admitted 因子无 `$num_trades` 使用；avg_trade_size 几何与 amount level/CV (F002/F015/F043) 不同（分子分母都换 — 分子是 amount，分母是 num_trades 而非时间窗口聚合）。

**与 lessons 风险位的对照**：

- **L1 (vol_20d 结构性吸收)**：Phase 2 必须验证 vol_20d_exp。b068 C002 raw level=9.75 < 30%（不算极端但 alpha_surv=0.13 致命）。本批候选若 vol_20d_exp >25% **AND** alpha_surv<0.30 → 该方向也必死（与 fundamental_quality_carry 同构 dead）。
- **L2 (TTM × TTM Sub/Mul/Div 数据契约)**：本批不涉及 TTM × TTM；avg_trade_size 是 daily $amount/$num_trades，两端都 daily 字段无 NaN sparse。
- **L3 (signed cross-product regime drift)**：本批仅 C005 是 cross-product 形式（rank × rank），但两端都先 CsRank（无 absolute level 量纲）+ 短期 momentum vs avg_trade_size 不是 signed fundamental — 风险中等。
- **L4 (rank-diff geometry 7 律)**：C003 rank-diff 形式必须验证两端 scale-invariance（avg_trade_size 是 ratio 无量纲；Mean(amount,20) 有量纲 — 7-律 #1 触发警示，但 rank 化后 ordinal 已无量纲，等待 Phase 2 验证）。

**红线**：

- `|corr|>0.3` to `$market_cap` reject — $num_trades 与 size 强正相关（大票必然 num_trades 高）。所有候选必须先做 size-neutral 验证。
- `alpha_survival ≥ 0.40` (default), `max_corr<0.30` to library — 标准 admit 门槛。
- `vol_20d_exp > 25%` AND `alpha_survival < 0.30` 三立 → reject（标 vol_20d 吸收 + 该方向首批 dead → consolidation trigger）。

---

## Threads

### T001: avg_trade_size 时序几何 (rolling Std + TsRank) [◉ ACTIVE]

> [!warning]+ Thread 结论
> **Question**: avg_trade_size 的时序波动 / 时序 anomaly 是 institutional flow regime change proxy，与 raw daily level 几何不同，能脱 vol_20d 吸收？
>
> **Answer (round 91 update)**: **Std 形式 dead, TsRank 窗口轴全段封闭, reciprocal 等价, rank-diff form 是唯一 escape (但 statistical 不足)**.
>
> - **Std form** (b072/C001): vol_20d 三立 reject (vol_20d_exp=26.7)
> - **TsRank 窗口轴扫** (b091/C001-C003 全 reject): 30d max_corr=0.79, 60d=0.24(原), 90d=0.75, 120d=0.71 — **F024 (TsRank(num_trades/volume,60)) anchor 在 30-120d 窗口轴上是连续引力盆地**; 反直觉发现：alpha_surv 单调下降 (0.558→0.418→0.398) 即窗口越长 vol_20d 嵌入越深
> - **Reciprocal axis** (b091/C005 reject): TsRank($num_trades/$amount,60) 是 b072/C006 的 monotonic sign-flip duplicate (TsRank(1/x,N)=N+1-TsRank(x,N))
> - **P008 third ratio axis** (b091/C006 reject): TsRank($volume/$num_trades,60) hard_gate fail 0.957@F024 — sign-flip duplicate of F024
> - **Rank-diff form** (b091/C004 reserve): `Sub(TsRank60, TsRank20)` — **max_corr=0.18@F016 LOW + incr_ic=+0.008 PASS + alpha_surv=0.862 PASS + Barra residual IC sign flip (+0.014 vs raw -0.016)** — 真正脱 F024 anchor 邻域, 但 ls_t=-2.20 statistical 不足以 admit
>
> **Evidence trail**: [[batches/batch_072/candidates/C001|batch_072 C001]] Std → reject; [[batches/batch_072/candidates/C006|batch_072 C006]] TsRank 60d → reserve; [[batches/batch_091/candidates/C001|batch_091 C001]] / [[batches/batch_091/candidates/C002|C002]] / [[batches/batch_091/candidates/C003|C003]] 窗口扫 → 全 reject; [[batches/batch_091/candidates/C004|batch_091 C004]] rank-diff → reserve; [[batches/batch_091/candidates/C005|batch_091 C005]] reciprocal → reject; [[batches/batch_091/candidates/C006|batch_091 C006]] P008 third ratio → reject.
>
> **复活路径 (round 91 后)**: (a) C004 rank-diff form 配更短 RHS `Sub(TsRank60, TsRank10)` 增强信号; (b) 跨字段 rank-diff `Sub(TsRank($amount/$num_trades,60), TsRank($amount/$volume,60))`; (c) CsRank 二次包裹 `CsRank(Sub(TsRank60, TsRank20))`; (d) Python residualize on (F024+F012) + 重测 incr_ic/ls_t — 仅当 ls_t 改善 ≥ 2.5 才进 admit. **闭锁**: window axis 全段 + reciprocal + P008-third-ratio 三轴 disproven.

### T002: $num_trades raw level retail attention [✗ DISPROVEN batch_072]

> [!failure]+ Thread 结论
> **Question**: $num_trades 单日 level cross-section rank 携带 retail attention premium（高 attention → forward reversal）？
>
> **Answer**: **born-disproven**. C002 CsRank($num_trades) max_corr=**0.75@F012** NEAR_DUPLICATE + vol_20d_exp=30.9 + incr=-0.038. **关键 insight**: $num_trades raw cross-section level 是 **size × Amihud 联合代理** — F012 (-|return|/$amount) 通过 size 共线性同样捕捉 retail attention 几何空间. 新字段不等于新几何空间.
>
> **Evidence trail**: [[batches/batch_072/candidates/C002|batch_072 C002]] → reject (NEAR_DUPLICATE).
>
> **lessons 升格候选**: "raw $num_trades CsRank default-skip — F012 anchor through size co-linearity + vol_20d 吸收双重锁".

### T003: rank-diff institutional vs general liquidity 分离 [✗ DISPROVEN batch_072]

> [!failure]+ Thread 结论
> **Question**: `CsRank(avg_trade_size) - CsRank(Mean(amount,20))` 通过 P001 rank-diff 把 institutional concentration 从 general liquidity 中分离？
>
> **Answer**: **born-disproven, hard_gate 三立**. C003 sign_flip + oos_decay -1.888 + mono_sign_flip 0.70/-1.00. P001 rank-diff 7 律 #6 RHS Mean(amount,20) 死亡 endpoints — anchor cluster 跨字段族 (institutional concentration LHS) 也无法脱 amount_20 anchor.
>
> **Evidence trail**: [[batches/batch_072/candidates/C003|batch_072 C003]] → hg_fail 三立 reject.
>
> **复活路径**: 换 RHS endpoints 脱 amount/turnover/H-L_60 死亡 family.

### T004: price-flow correlation OFI proxy [✗ DISPROVEN batch_072]

> [!failure]+ Thread 结论
> **Question**: Corr(avg_trade_size, $close, 20) 携带机构买涨/买跌的 forward signal？
>
> **Answer**: **born-disproven, alpha_surv 杀**. C004 alpha_surv=0.25 三立 + dominant_style=vol_20d (style_r²=0.09 低但 dom 仍 vol_20d). Daily rolling correlation 不脱 vol_20d basis.
>
> **Evidence trail**: [[batches/batch_072/candidates/C004|batch_072 C004]] → reject.
>
> **复活路径**: minute-bar OFI (需 minute 数据接入，daily 不可行).

### T005: institutional × short-momentum cross-product [✗ DISPROVEN batch_072]

> [!failure]+ Thread 结论
> **Question**: CsRank(avg_trade_size) × CsRank(5d momentum) 揭示机构择时方向（trend-following vs contrarian）？
>
> **Answer**: **born-disproven, library reducer signature**. C005 ls_t=-7.32 + alpha_surv=0.526 PASS + max_corr=**0.46@F009** borderline + incr_ic=**-0.027** 强 NEG. cross-product 形式 (机构集中度 × 价格运动方向) 在 csi1000 cross-section 几何空间已被 F009 (overnight pv_corr_5) 占位。P008 软判定默认 reject (设计无独立新几何).
>
> **Evidence trail**: [[batches/batch_072/candidates/C005|batch_072 C005]] → reject.

## Known Failures

| Batch | Candidate | Expression | Reject reason |
|---|---|---|---|
| [[batches/batch_072/candidates/C001\|batch_072 C001]] | C001 | `Std(Div($amount, $num_trades), 20)` | P004 vol_20d 三立: alpha_surv=0.17 + sty_r²=0.25 + vol_20d_exp=26.7 + dom=vol_20d. Std rolling 嵌入 vol_20d basis (Std of ratio 直接捕捉日内交易量波动) |
| [[batches/batch_072/candidates/C002\|batch_072 C002]] | C002 | `CsRank($num_trades)` | CP05 NEAR_DUPLICATE max_corr=0.75@F012 + style_r²=0.59 + vol_20d_exp=30.9 + incr=-0.038. $num_trades raw level = size × Amihud 联合代理 |
| [[batches/batch_072/candidates/C003\|batch_072 C003]] | C003 | `Sub(CsRank(Div($amount, $num_trades)), CsRank(Mean($amount, 20)))` | hard_gate 三立: sign_flip (train +0.0091/val -0.0171) + oos_decay=-1.888 + mono_sign_flip (IS=0.70 OOS=-1.00). P001 rank-diff 7 律 #6 RHS amount_20 死亡 endpoints |
| [[batches/batch_072/candidates/C004\|batch_072 C004]] | C004 | `Corr(Div($amount, $num_trades), $close, 20)` | alpha_surv=0.25 三立 + dom=vol_20d (sty_r²=0.09 低但 dom 仍 vol_20d). 20d rolling correlation 不脱 vol_20d basis |
| [[batches/batch_072/candidates/C005\|batch_072 C005]] | C005 | `Mul(CsRank(Div($amount, $num_trades)), CsRank(Sub($close, Ref($close, 5))))` | P008 软判定: ls_t=-7.32 + alpha_surv=0.526 PASS + max_corr=0.46@F009 borderline + incr=-0.027 强 NEG. cross-product 形式与 F009 pv_corr 几何同源吸收 |
| [[batches/batch_091/candidates/C001\|batch_091 C001]] | C001 | `TsRank(Div($amount, $num_trades), 30)` | P030 三立: incr_ic=-0.012 NEG + max_corr=0.79@F024 HIGH. 缩窗反而提升 max_corr (F024 几何邻域在更短窗口更密集) |
| [[batches/batch_091/candidates/C002\|batch_091 C002]] | C002 | `TsRank(Div($amount, $num_trades), 90)` | P030 三立: incr_ic=-0.007 NEG + max_corr=0.75@F024 HIGH. 90d 窗口在 60d-120d 之间仍在 F024 引力盆地 |
| [[batches/batch_091/candidates/C003\|batch_091 C003]] | C003 | `TsRank(Div($amount, $num_trades), 120)` | P030 三立: incr_ic=-0.006 NEG + max_corr=0.71@F024 HIGH + alpha_surv=0.398 < threshold 0.40 边界破. 反直觉: 120d 比 60d/90d alpha_surv 更低 |
| [[batches/batch_091/candidates/C005\|batch_091 C005]] | C005 | `TsRank(Div($num_trades, $amount), 60)` | Reciprocal monotonic sign-flip duplicate of b072/C006 (TsRank(1/x,N)=N+1-TsRank(x,N)) — IC=+0.054 与 b072/C006 -0.054 完美镜像. max_corr=0.84@F024 |
| [[batches/batch_091/candidates/C006\|batch_091 C006]] | C006 | `TsRank(Div($volume, $num_trades), 60)` | hard_gate near_duplicate fail: max_corr=0.957@F024. TsRank(volume/num_trades,60) 是 F024 (TsRank(num_trades/volume,60)) 的字段对 reciprocal sign-flip duplicate |

---

## Narrative Log

- **2026-05-02 (round 72)**: NEW direction created from cockpit hint — `$num_trades` 2026-05-01 新增字段库内仅 b068 一次使用（直接 raw level 形式 reject），rolling/rank-diff/interaction 几何完全未探索。本批是 fundamental escape 最后一搏，若 dead → 下批触 Phase 5 consolidation.

- **2026-05-02 round 73 Phase 5 consolidation · 方向维持 probing（C006 reserve 火种保留）**: hypothesis_promoter/008 + pattern_analyst/010 + pattern_analyst/013 + pattern_analyst/015 + library_gap/009 + calibration/005 升格 4 条元教训至 lessons.md：(a) `Path Selection` "TsRank window≥60d on ratio fields 是新 vol_20d-escape 路径"（C006 实证 vol_20d_exp 降 65% + style_r² 降 75%，库内首例 partial-progress） + raw $num_trades 不构成新几何衍生律（C002 max_corr=0.75@F012 NEAR_DUPLICATE）；(b) 顶层 macro lesson "csi1000 daily fundamental + institutional flow 真饱和" 路径 e（institutional flow microstructure 几何独立但 forward reversal + incr_ic NEG）；(c) Hot Topics P006 段 "P008 软判定补丁"（alpha_surv > 0.30 + incr_ic < 0 + max_corr ∈ [0.40, 0.50] borderline → reject 默认 vs max_corr < 0.30 LOW + 独立新几何 → reserve 火种）。**calibration/005 verdict**：C006 reserve 维持 NOT admit，trigger #1-#4 全部不立，**不放宽 incr_ic floor**；C006 等 incr_ic 改善路径：(a) 配 RHS rank-diff 测 incr_ic 改善；(b) 30d/120d 窗口扫；(c) Python residualize on F009 后再 CsRank。**direction 维持 probing**（C006 火种活跃 + library_gap/009 提议同方向 5 候选 follow-up batch `tsrank_timeseries_ratio` 优先级 medium）；priority 不变；T001 partial-progress（C006 reserve），T002/T003/T004/T005 born-disproven。

- **2026-05-02 (batch_072 judged)**: admit=0 reserve=1 (C006) reject=5. **核心发现**: 5/5 PASS-hg 候选 mono_oos=-1.00 PERFECT + sign_consistency=1.0 — `$num_trades` 几何空间在 csi1000 daily 上是 reversal 方向 (机构集中 = 散户高活跃 = forward reversal). **C006 TsRank(avg_trade_size, 60) 是本批最强发现**: ls_t=-7.54 整库顶级 + alpha_surv=0.447 PASS + style_r²=0.15 极清洁 + max_corr=0.24@F009 LOW 几何独立 + vol_20d_exp=10.87 (vs C001 Std 形式 26.7, 降 60%). **唯一阻断 incr_ic=-0.018 微 NEG** → reserve 而非 admit. **关键发现 P009**: TsRank 时序量纲化在 ratio 字段上比 cross-section level 大幅降低 vol_20d_exp (实证 65%↓) + style_r² (75%↓) — 时序 rank 是新逃 vol_20d 路径候选 (库内极少先例). **关键发现 P010**: alpha_surv>0.30 + incr_ic<0 软判定 reject vs reserve 边界 = 设计层是否含独立新几何 (max_corr<0.30 + 未被探索 atom). T002 (raw level retail attention) + T003 (rank-diff) + T004 (Corr OFI) + T005 (cross-product) 4 thread born-disproven; T001 通过 C006 partial-progress. **下批建议**: 鉴于 zero_admit_streak=13 + 三 fundamental 方向 dead/archived + 本批仅 reserve — 强烈建议 orchestrator 启动 Phase 5 consolidation, 不再续探本方向. 详见 [[batches/batch_072/judge|batch_072 judge]].

- **2026-05-16 (batch_091 judged, round 91 reserve revival pool #1)**: admit=0 reserve=1 (C004 rank-diff form) reject=5 (3 窗口扫 + 2 reciprocal duplicates). **核心发现**: 复活 b072/C006 的 5 candidate axes (window sweep 30/90/120d + rank-diff + reciprocal + P008 third ratio) **4/5 axes 闭锁**, 仅 **rank-diff axis 突破** (C004 max_corr=0.18@F016 LOW + incr_ic=+0.008 PASS + alpha_surv=0.862 PASS + Barra residual IC sign flip — 真正脱 F024 anchor 邻域). 但 C004 ls_t=-2.20 仅 moderate, mt_bucket=high 进一步降档 → statistical 不足 admit, reserve. **关键反直觉发现 P032 候选**: window 轴扫 30→60→90→120d alpha_surv **单调下降** 0.558→0.447→0.418→0.398 — 即 TsRank 长窗口在 ratio 字段上反而加重 vol_20d 嵌入 (与 P031 P008 escape 三条件 "TsRank ≥ 60d" 形成微张力，提示窗口"过长"也有上界). **F024 anchor 几何邻域确认**: 30-120d 窗口轴上 max_corr 0.71-0.79 连续高位 → F024 不是 60d 点锚, 是 width≥90d 的引力盆地. **Reciprocal canonical 漏检升格候选**: C005/C006 通过 Phase 1 freeze 但 Phase 2 IC 后立即被 sign-flip equivalence 拦截 — generator 应在 freeze 时识别 `TsRank(Div(a,b),N)` 与 `TsRank(Div(b,a),N)` 的 reciprocal 等价. **T001 thread 深化** (window/reciprocal/P008-third-ratio 三轴 disproven, rank-diff 轴 partial-progress). **direction status 维持 probing** (C004 火种 + b072/C006 火种 双 reserve); 下批若再 0-admit → 考虑转 saturated. 详见 [[batches/batch_091/judge|batch_091 judge]].
