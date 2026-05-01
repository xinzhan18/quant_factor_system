---
direction_tag: institutional_flow_proxy
status: probing
priority: medium
rounds: 2
admits: 0
last_batch: batch_072
last_admits: []
last_goal: '首批 6 候选探索 $num_trades 字段族（2026-05-01 新增微观字段，库内仅 b068 二次直接 raw level 使用
  reject）。

  所有候选引入额外几何维度 (rolling Std / TsRank / rank-diff / Corr / cross-product) 规避 b068 C002

  raw level vol_20d 吸收陷阱。avg_trade_size = $amount/$num_trades 是 institutional flow
  proxy，

  $num_trades level 是 retail attention proxy。本批是 fundamental escape 最后一搏，若 dead →
  下批

  触 Phase 5 consolidation. 目标 ≥1 admit 验证假设。'
last_activity: '2026-05-02T04:30:00Z'
created_batch: batch_072
members: []
retired_members: []
reserves:
- batch_072_C006
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
> **Answer**: **Std 形式 dead, TsRank 形式 reserve**. C001 Std(avg_trade_size,20) vol_20d_exp=26.7 + alpha_surv=0.17 标准 vol_20d 三立 reject — 20d rolling Std 仍嵌入 vol_20d. **C006 TsRank 60d 是 partial-progress**: vol_20d_exp=10.87 (vs C001 26.7, 降 60%) + style_r²=0.15 (vs C001 0.25, 降 40%) + alpha_surv=0.447 PASS + max_corr=0.24@F009 LOW 几何独立 + ls_t=-7.54 整库顶级 + mono PERFECT — **首次在 csi1000 上看到 ratio 字段时序量纲化 (TsRank window≥60d) 显著降低 vol_20d 嵌入**. 但 incr_ic=-0.018 微 NEG → reserve 不 admit.
>
> **Evidence trail**: [[batches/batch_072/candidates/C001|batch_072 C001]] Std → reject; [[batches/batch_072/candidates/C006|batch_072 C006]] TsRank 60d → reserve.
>
> **复活路径**: (a) C006 配 RHS rank-diff 测试 incr_ic 改善; (b) 30d/120d 窗口扫; (c) Python residualize on F009 后再 CsRank; (d) 跨字段 TsRank composite.

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

---

## Narrative Log

- **2026-05-02 (round 72)**: NEW direction created from cockpit hint — `$num_trades` 2026-05-01 新增字段库内仅 b068 一次使用（直接 raw level 形式 reject），rolling/rank-diff/interaction 几何完全未探索。本批是 fundamental escape 最后一搏，若 dead → 下批触 Phase 5 consolidation.

- **2026-05-02 round 73 Phase 5 consolidation · 方向维持 probing（C006 reserve 火种保留）**: hypothesis_promoter/008 + pattern_analyst/010 + pattern_analyst/013 + pattern_analyst/015 + library_gap/009 + calibration/005 升格 4 条元教训至 lessons.md：(a) `Path Selection` "TsRank window≥60d on ratio fields 是新 vol_20d-escape 路径"（C006 实证 vol_20d_exp 降 65% + style_r² 降 75%，库内首例 partial-progress） + raw $num_trades 不构成新几何衍生律（C002 max_corr=0.75@F012 NEAR_DUPLICATE）；(b) 顶层 macro lesson "csi1000 daily fundamental + institutional flow 真饱和" 路径 e（institutional flow microstructure 几何独立但 forward reversal + incr_ic NEG）；(c) Hot Topics P006 段 "P008 软判定补丁"（alpha_surv > 0.30 + incr_ic < 0 + max_corr ∈ [0.40, 0.50] borderline → reject 默认 vs max_corr < 0.30 LOW + 独立新几何 → reserve 火种）。**calibration/005 verdict**：C006 reserve 维持 NOT admit，trigger #1-#4 全部不立，**不放宽 incr_ic floor**；C006 等 incr_ic 改善路径：(a) 配 RHS rank-diff 测 incr_ic 改善；(b) 30d/120d 窗口扫；(c) Python residualize on F009 后再 CsRank。**direction 维持 probing**（C006 火种活跃 + library_gap/009 提议同方向 5 候选 follow-up batch `tsrank_timeseries_ratio` 优先级 medium）；priority 不变；T001 partial-progress（C006 reserve），T002/T003/T004/T005 born-disproven。

- **2026-05-02 (batch_072 judged)**: admit=0 reserve=1 (C006) reject=5. **核心发现**: 5/5 PASS-hg 候选 mono_oos=-1.00 PERFECT + sign_consistency=1.0 — `$num_trades` 几何空间在 csi1000 daily 上是 reversal 方向 (机构集中 = 散户高活跃 = forward reversal). **C006 TsRank(avg_trade_size, 60) 是本批最强发现**: ls_t=-7.54 整库顶级 + alpha_surv=0.447 PASS + style_r²=0.15 极清洁 + max_corr=0.24@F009 LOW 几何独立 + vol_20d_exp=10.87 (vs C001 Std 形式 26.7, 降 60%). **唯一阻断 incr_ic=-0.018 微 NEG** → reserve 而非 admit. **关键发现 P009**: TsRank 时序量纲化在 ratio 字段上比 cross-section level 大幅降低 vol_20d_exp (实证 65%↓) + style_r² (75%↓) — 时序 rank 是新逃 vol_20d 路径候选 (库内极少先例). **关键发现 P010**: alpha_surv>0.30 + incr_ic<0 软判定 reject vs reserve 边界 = 设计层是否含独立新几何 (max_corr<0.30 + 未被探索 atom). T002 (raw level retail attention) + T003 (rank-diff) + T004 (Corr OFI) + T005 (cross-product) 4 thread born-disproven; T001 通过 C006 partial-progress. **下批建议**: 鉴于 zero_admit_streak=13 + 三 fundamental 方向 dead/archived + 本批仅 reserve — 强烈建议 orchestrator 启动 Phase 5 consolidation, 不再续探本方向. 详见 [[batches/batch_072/judge|batch_072 judge]].
