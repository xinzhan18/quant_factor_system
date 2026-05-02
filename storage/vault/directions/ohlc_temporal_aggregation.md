---
direction_tag: ohlc_temporal_aggregation
status: saturated
priority: low
rounds: 10
admits: 5
last_batch: batch_081
last_admits: []
last_goal: 'Round 81 zero_admit_streak=4 (b063/b076/b079/b080), rounds_since_consolidation=8
  approaching 10 cap. ohlc_temporal_aggregation reactivation per cockpit guidance:
  long-window mean-reversion focus on OHLC ratio Mean/Std/Skew × {60d, 60d, 60d} combinations,
  with the explicit goal of escaping (a) vol_20d basis (P004) via symmetric normalizers
  (H+L), (b) OHLC algebraic mirror cluster (b063 lesson) via non-mirror atom geometry,
  (c) library reducer hard-block (P006) via TsRank window≥60d on ratio path (P008),
  (d) library OHLC family anchors F006/F007/F008 (Mean 5d) and F019/F020/F021 (Std/rank-diff
  20d) via 3× window separation + 3rd moment (Skew). 6 candidates: C001 standalone
  Mean(hl_norm_sym,60); C002 standalone Skew(body_ratio,60); C003 rank-diff hl_norm_sym
  × num_trades_60; C004 standalone Mean(co_norm_sym,60) signed long-drift; C005 rank-diff
  Skew(body_ratio,60) × amount_60; C006 TsRank(hl_norm_sym,60) P008-escape. ≥3 candidates
  touch baseline-first untouched atom × moment × window combinations: hl_norm_sym
  (H-L)/(H+L) is bounded scale-free, never admitted, and not a vol_20d direct proxy
  (unlike H-L/Ref(close,1)); co_norm_sym (C-O)/(C+O) similarly novel. Hard targets:
  ≥1 admit max_corr<0.40 (since b080 zero-admit-streak demands cleanest geometry)
  + alpha_surv≥0.30 + ls_t≥2 + incr_ic≥0.015 + 9/9 sign consistency. Fail → consolidation_trigger=true
  (rounds_since=8→9 next approaches 10 cap) + status productive→saturated transition
  recommend.'
last_activity: '2026-05-02T15:00:53Z'
created_batch: batch_017
members:
- F006
- F007
- F008
- F019
retired_members: []
merged_into: null
---
# ohlc_temporal_aggregation

> [!abstract]+ 方向概要
> **状态**　🟡 saturated · priority=low · rounds=10 · admits=5 (F006/F007/F008/F019 + Mean-base 三轴 + higher-moment rank-diff)
> **最近**　[[batches/batch_081/judge|batch_081]] · 2026-05-02 · admit=0 / reserve=1 (C006 P008 TsRank-escape 机制验证) / reject=5
> **一句话**　5d OHLC aggregation 三独立维度 (F006/F007/F008) + higher-moment rank-diff (F019) 兑现后，连续 5 批 zero_admit (b063/b076/b079/b080/b081) 实证方向饱和；60d-window OHLC ratio Mean/Skew × cross-section RHS 范式整体被 F018/F021/F012 absorbing prototype 锁死；唯一新机制——TsRank ratio-field≥60d (P008 escape) 单点首验 (b081 C006 alpha_survival=0.993)——分离至 T013 待跨方向复现，本方向冻结。

---

## Hypothesis

> [!success]+ Hypothesis（已基本验证 + 复活条件兑现 + 60d-window 续探整体饱和）
> 单日 OHLC body/shadow 信号（[[intraday_price_formation]]）因 intraday noise 过大而全部 mono_sign_flip 失败；**多日 smoothed/aggregated** 版本可 reveal persistent intraday flow：连续 N 天 close > open = sustained order flow asymmetry，与单日 random walk 完全不同性质。
>
> 经济直觉：
> - 单日 body = random walk + microstructure noise
> - 5d/20d Mean(body) 累加同向偏移 = persistent order flow
> - 反向 trend-following：高 mean shadow → 持续抛压 → 短期反转
>
> **验证结果**：(a) Mean-base 5d aggregation 在 close 端 (F006 upper-shadow) / open 端 (F007 open-position) / 3d phase (F008) 三独立维度成立；(b) higher-moment + rank-diff (F019 Std(body_ratio,20) × price_vol_60) 兑现复活条件；(c) **20d Mean-base 加深 vol_20d 耦合，60d-window standalone Mean / Skew / rank-diff 整体被库 anchor 吸收 (b063/b081 双轮实证)，magnitude-only / discrete count / turnover-wt 全 fail**。

> [!warning]+ ⚠️ 60d-window 续探整体饱和 (b081 第三轮锁定)
> b063 (higher-moment 20d) + b081 (Mean/Skew 60d) 两轮 12 candidate 跨 ≥6 atom (close_position / range_norm_prev_close / signed_return_norm / open_position / upper_shadow / hl_norm_sym / co_norm_sym / body_ratio_skew / |gap|/range) admit=0 → **F019/F020 兑现路径六件套不可在 60d-window 跨原子泛化**。
>
> 锁死机理 (跨 finding 004/005/019 三律联动)：
> - **Geometric absorbing-factor 律** (finding 019)：F021 upper_shadow disp/range 在 OHLC body/range/shadow family 占据 absorbing prototype 位置 → b081 C001 hl_norm_sym 60d Mean max_corr=0.677@F021 数学同构 (Mean(H/L,60) 单调正相关 (H+L) 分母变体)
> - **Factor-anchored cluster** (finding 004 anchor 7)：F018 sustained directional drift 跨 family 锁死任何 long-window signed body Mean → b081 C004 co_norm_sym 60d Mean max_corr=0.385@F018 + incr_ic=-0.014 + str_1m=2.78 联合吞噬
> - **Library-reducer trap signature** (finding 005 5 元判别)：mono_oos≥0.9 + |ls_t|≥3 + incr_ic<0 + alpha_surv<0.30 → b081 C005 Skew(body_ratio,60)×amount_60 mono=+1.0/ls_t=+3.47/9/9 同号 alpha 表面强但 alpha_surv=0.07 critical + amount cluster halo
>
> **不再有"复活路径"留在本方向**——剩余探索全部分流到 T013 跨方向 P008 escape 复现。

---

## Promoted Lessons

1. **alpha_survival 是 vol_20d 衍生判别量**：>1.0 = Barra 空间独立载体（C006 alpha_surv=0.993 是本方向首例）；<<0.40 = vol 衍生（Mean-base）。**例外**：rank-diff geometry 因 CsRank Sub 必然部分映射到 cross-sectional dispersion，alpha_surv 0.30-0.40 区间是真实信号 + 必然 style coupling，不是 alpha 弱（F019 admit alpha_surv=0.21 仍 admit；config 已 codify `alpha_surv_min.rank_diff=0.30`，见 [[_consolidation/findings/calibration/001]]）。
2. **5d 是 Mean-base OHLC aggregation sweet spot**：单日（intraday saturated）与 20d（vol-coupled）之间。**higher-moment 突破 sweet spot 约束**：Std(body_ratio,**20**d) 反而成为独立轴（窗口约束随 moment 阶数变化）。**60d Mean / Skew 路径整体不通**：60d Mean → 数学同构于库 anchor RHS (F021/F018)；60d Skew → 3 阶矩有效样本不足显著性 (b081 C002 ic_oos=-0.0041 hard_gate)。
3. **信号家族 multi-window 不对称**：upper-shadow [3d, 7d] 稳；open-position 严格 5d-only（3d mono_sign_flip IS=-1.00 OOS=+0.90）；≥10d Mean-base 跨 phase 反转。
4. **OHLC 三段约束 → algebraic mirror trap**：lower-shadow ≡ -upper-shadow（corr=1.000@F006），signed-range 与 F006 高 corr；三段 ratio 任意两端代数互补。**higher-moment 形态扩展** (b063 C001)：Std/Var/Skew/Kurt of mirror-pair ratios cluster=0.79@F021。**60d 同窗口分母变体扩展** (b081 C001)：(H+L) vs (H/L) 单调正相关 → cross-section rank 高度同构 (max_corr=0.68@F021)。
5. **Magnitude-only / turnover-wt / discrete count / num_trades RHS 全部失败**（Mean-base 维度）：signed 方向性是 OHLC Mean 信号必要条件，turnover/num_trades/amount 不构成独立 OHLC 轴 (b081 C003 num_trades_60 max_corr=0.612@F012 + alpha_surv=0.078 critical 实证)。
6. **rank-diff × OHLC 兑现两条件**（F019 提取，[[_consolidation/findings/hypothesis_promoter/006]] 升格）：(a) higher-moment LHS（Std/Skew/Kurt vs 库内全 Mean-base, 完全独立轴）+ (b) RHS 跳出 turnover/amount/overnight cluster（price_vol 是新 basis）。两条件单独均不足，叠加才 max_corr<0.30。**60d 窗口扩展不可行** (b081 C005 验证：rank-diff Skew(body_ratio,60)×amount_60 即使 mono=+1.0/ls_t=+3.47/9/9 同号仍 alpha_surv=0.07 critical)。
7. **sign aggregation 不可盲目跨字段泛化**（T011 [✗]）：alpha 来自 underlying field 的 persistent drift，非 Sign() 操作几何性质。overnight 有 institutional accumulation drift（F018），intraday body 是 random walk（b017 C003 / b050 C006 双例 reject）。Phase 1 设计 sign 候选必须先核 underlying drift。
8. **rank-diff geometry 7 条硬约束（系统级，[[_consolidation/findings/pattern_analyst/004]]）**：(1) 两端 scale-invariance；(2) raw field 独立；(3) 同字段跨窗口禁止；(4) Sub 方向对偶 dedup；(5) 同批 LHS 共享 anchor rule；(6) RHS 共振饱和（dead endpoints 动态：overnight_5/turnover_5/amount_20/body_ratio_20/price_vol_20/circ_mktcap_60/H_L_60_geo/**num_trades_60 (b081 升格)**）；(7) factor-anchored cluster（saturated 方向 anchor 消化新候选）。
9. **incr_ic borderline 死区律（[[_consolidation/findings/calibration/004]]）**：max_corr ∈ [0.30, 0.70] 时 incr_ic 必须 ≥ 0.015 才 admit-eligible；本方向 b050 C001 (incr=0.013, max_corr=0.50) / b063 C004 (incr=0.006, max_corr=0.69) / b081 C005 (incr=0.005, max_corr borderline) 三例死区。设计期 self-prune 0.008-0.013 incr_ic 候选。
10. **🆕 Geometric absorbing-factor 律（[[_consolidation/findings/pattern_analyst/019]]，本方向 b081 C001 升格首例）**：admit factor 在其几何 family 内自动成为 absorbing prototype——同 family 后续 frontier 续探在 cross-section 上 max_corr ≥0.55@该 factor。**判别要件**：family 内 admit ≥1 后，同 family 续探 max_corr ≥0.55@admit factor → 默认 reject 不再消耗 CP3-CP6 计算预算。**逃离路径**：cross-family RHS / 高阶 composition (ratio-of-derived-quantity, F025 案例) / Python residualize on prototype factor。本方向 F021 upper_shadow disp/range 已被实证为 OHLC body/range/shadow family absorbing prototype。
11. **🆕 P008 TsRank ratio-field≥60d escape 机制层验证（b081 C006，单例首证）**：bounded scale-free OHLC ratio 上 TsRank window≥60d 与 CsRank/Mean 几何完全不同——own-history mean-reversion 轴。C006 alpha_survival=**0.993** ≈ 1.0（Barra 空间独立载体首例）+ vol_20d=12.56（同批 standalone 平均 25+ 一半以下）+ max_corr=0.268@F022 库内最干净。**机制层兑现，库增值未达**（incr_ic=-0.035 与库内多个低 corr 因子形成"低 corr 同向减项"集体效应）→ **跨方向复现待办，本方向冻结**。

---

## Threads

### T013: TsRank ratio-field own-history mean-reversion (P008 escape 路径) [◉ ACTIVE · 跨方向待复现]

> [!note]+ Thread 当前
> **Question**: TsRank window≥60d on bounded scale-free OHLC/microstructure ratios (hl_norm_sym, body_ratio, range/prev_close, turnover_rate, etc.) 是否构成可复现的 vol_20d-escape 路径并产生 admittable alpha？
>
> **Evidence trail (单例首证)**:
> - [[batches/batch_081/candidates/C006|b081 C006]]　TsRank(hl_norm_sym,60)　alpha_survival=**0.993** ≈ 1.0 (Barra 空间独立载体首例) + max_corr=0.268@F022 库内最干净 + style_r²=0.133 + vol_20d=12.56 (vs 同批 standalone 平均 25+) + ls_t=-3.64 + 9/9 yr 同号 → **reserve (P008 机制验证 ✓ 但 incr_ic=-0.035 整批最严重负 + mono_oos=-0.40 弱单调 + cum_ic_mdd=-108 极深 → 不达 admit)**
>
> **Answer (单例)**: P008 TsRank ratio-field≥60d **机制层面验证有效**——TsRank 几何与 CsRank/Mean 完全不同的 own-history mean-reversion 轴；alpha_survival=0.993 比 ohlc_temporal_aggregation 方向其他长窗候选（vol_20d 暴露 17-48）高出整整一个量级。但**库增值不达**——本候选与库内多个低 corr 因子（F001/F022 等）形成"低 corr 同向减项"集体效应，incr_ic=-0.035。
>
> **Next probes (跨方向，本方向冻结)**: 优先在 anchor_proximity_momentum / range_structure / microstructure_illiquidity 这类 productive 方向尝试，避免本方向 MT cap. 候选 atom: TsRank(body_ratio, 60), TsRank(close_position, 60), TsRank(gap_ret/range, 60), TsRank(turnover_rate, 60), TsRank(num_trades/volume, 60) (注：F024 同 atom 已 admit，需变体). 与 finding/010 + finding/019 配对：高阶 composition (ratio-of-derived-quantity) + TsRank≥60d 是 dim-less ratio frontier 真红利第一+第二阶组合。
>
> **禁忌 (起始)**: (a) TsRank ratio-field <60d window 不在 P008 范畴内（cockpit 强调 window≥60d）；(b) TsRank on raw price/volume 未验证（P008 限定 ratio fields）；(c) 多 TsRank 嵌套 (TsRank of TsRank) 未验证；(d) 同 family 内 atom 重复（F024 num_trades/volume 已 admit → 同 family TsRank 续探被 absorbing prototype 锁死，必须 cross-family）。

### T012: higher-moment OHLC 维度 [✓ ANSWERED batch_081 — 60d-window 整体饱和]

> [!success]+ Thread 结论
> **Question**: Std/Skew/Kurt of OHLC ratios 是否构成与 Mean-based 库因子独立的轴？哪些 atomic OHLC × moment × window 组合产生 alpha？
>
> **Answer (三轮终结)**:
> - **20d Std × non-vol-cluster RHS** [✓ b050 F019 admit]：Std(body_ratio,20) × price_vol_60，rank-diff cluster 兑现（六件套：atom multi-regime stable + atom 与 vol_20d 几何正交 + normalizer 无 regime drift + sign 保留 + price normalizer 优于 range + 避 mirror pair Std cluster）
> - **20d Std × vol-cluster RHS** [✗ b063 6/6 reject]：vol_20d_exp 76.53 整库新纪录 (signed return Std) / 53.04 (range Std) — atom 自身即 realized vol direct proxy → P003 vol_20d 边界律持续 escalate；OHLC algebraic mirror higher-moment 形态首次实证
> - **60d Mean × cross-section RHS** [✗ b081 5/6 reject]：F021/F018 absorbing prototype 锁死 (Geometric absorbing-factor 律首证)；hl_norm_sym (H+L 分母变体) 与 F021 RHS Mean(H/L,60) 数学同构；co_norm_sym 60d Mean 与 F018 sustained directional drift 同源
> - **60d Skew × any RHS** [✗ b081 实证不可行]：3 阶矩 60d 窗口有效样本不足 (~120 < 显著性所需) → ic_oos hard_gate fail
>
> 当前唯二兑现 atom 仍是 F019 body_ratio (20d Std) + F020 gap_ret (20d Std)。本 thread 结论：higher-moment OHLC 维度在 ohlc_temporal_aggregation 方向**仅 20d 窗口 × 非饱和 RHS cluster 一支兑现**，60d 续探路径整体不通，已穷尽。

### T002: Sign-of-body 频率信号 [✗ DISPROVEN batch_050]

> [!failure]+ Thread 结论
> **Question**: 多日内 close>open 的频率（bullish bar count）是否 forward-predictive？standalone (b017 C003 reserve) 与 rank-diff 包装 (b050 C006) 是否复活？
>
> **Answer**: intraday body sign 是 random walk，无 underlying persistent drift，rank-diff 包装也救不了。与 [[overnight_intraday_split]] F018 (overnight_sign 有 institutional accumulation drift) 形成对照律 → 已升格至 Lesson 7。

---

## Closed Threads (compressed)

- **T001 多日 smoothed signed body** [✗ DISPROVEN batch_017]：5d (b017 C001) Barra-clean 但 incr_ic=-0.050 cum_dd=-105；20d (b017 C002) r²=0.638 vol-coupled。signed body 本身非独立轴。
- **T003 多端点 OHLC aggregation** [✓ ANSWERED batch_017-021]：5d aggregation ≥3 独立 admit (F006 upper-shadow + F007 open-position + F008 3d phase)。Window 规律：upper-shadow [3d,7d] 稳但 ≥7d corr 逼近 F006；open-position 严格 5d-only；≥10d 跨 phase 反转。Magnitude-only / discrete / turnover-wt / Donchian 全 fail。Mean-base 维度饱和，admit 率 25%→14%。
- **T010 rank-diff × OHLC family** [✓ ANSWERED batch_050]：兑现需 (a) higher-moment LHS + (b) RHS 跳出已饱和 cluster。F019 双新维度叠加 → max_corr=0.270 整库最干净 + 与 4 admitted rank-diff 全 <0.25。**rank-diff 范式第 5 次跨家族 tipping point 正式确认**（已升格 Lesson 6 + [[_consolidation/findings/hypothesis_promoter/006]]）。
- **T011 sign aggregation 跨字段泛化** [✗ DISPROVEN batch_050]：alpha 来自 underlying drift 非 Sign() 几何（已升格 Lesson 7）。
- **T012 higher-moment OHLC** [✓ ANSWERED batch_081 — 见 above]：20d Std × non-vol RHS 兑现 (F019)；60d Mean/Skew × any RHS 整体被 F021/F018 absorbing prototype + 3 阶矩样本不足锁死。

---

## Known Failures（典型对照样本，60d-window 饱和锁死证据完整）

| Candidate | Expression | Reject Reason |
|---|---|---|
| [[batches/batch_017/candidates/C001\|b017 C001]] | 5d signed body | incr_ic=-0.050 + cum_dd=-105 |
| [[batches/batch_017/candidates/C004\|b017 C004]] | 5d close/high Mean | alpha_surv=0.003（vol_20d derivative 判别量起源）|
| [[batches/batch_018/candidates/C001\|b018 C001]] | 5d lower-shadow Mean | corr=1.000@F006（algebraic mirror trap 起源）|
| [[batches/batch_020/candidates/C002\|b020 C002]] | 10d upper-shadow Mean | mono_sign_flip（5d sweet spot 上界）|
| [[batches/batch_021/candidates/C001\|b021 C001]] | 3d open-position Mean | mono_sign_flip（F007 5d-only）|
| [[batches/batch_050/candidates/C006\|b050 C006]] | body_sign × pb_20 rank-diff | hard_gate；intraday body sign random walk |
| [[batches/batch_063/candidates/C001\|b063 C001]] | Std(close_position,20) × turnover_60 | max_corr=0.79@F021（OHLC mirror higher-moment trap 首证）|
| [[batches/batch_063/candidates/C003\|b063 C003]] | Std((C-O)/prev_close,20) × pb_60 | vol_20d=76.53 整库新纪录（atom 即 realized vol proxy）|
| [[batches/batch_063/candidates/C004\|b063 C004]] | Std(open_position,20) × amount_60 | max_corr=0.69@F012 + incr_ic 死区（strongest stat ls_t=4.89 仍阻断）|
| [[batches/batch_081/candidates/C001\|b081 C001]] | Mean(hl_norm_sym,60) standalone | max_corr=0.677@F021 数学同构 (Geometric absorbing-factor 律首证) + vol_20d=47.81 + alpha_surv=0.274 |
| [[batches/batch_081/candidates/C002\|b081 C002]] | Skew(body_ratio,60) standalone | ic_oos=-0.0041 hard_gate（3 阶矩 60d 窗口样本不足）|
| [[batches/batch_081/candidates/C003\|b081 C003]] | rank-diff hl_norm_sym × num_trades_60 | num_trades RHS 与 F012 流动性 cluster 共线 + alpha_surv=0.078 critical |
| [[batches/batch_081/candidates/C004\|b081 C004]] | Mean(co_norm_sym,60) standalone | max_corr=0.385@F018 同源 (functional P006) + incr_ic=-0.014 |
| [[batches/batch_081/candidates/C005\|b081 C005]] | rank-diff Skew(body_ratio,60) × amount_60 | mono=+1.0/ls_t=+3.47/9/9 同号但 alpha_surv=0.07 critical + amount cluster + incr_ic=0.005 死区（finding 005 5 元判别 5/5 全立）|

---

## Related

- 🟡 [[intraday_price_formation]] `saturated` — 单日 body/shadow 已穷尽；本方向在其基础上探 multi-day aggregation
- 🟢 [[overnight_intraday_split]] `productive` — F018 overnight_sign rank-diff 与 b050 C006 intraday_sign 形成 sign aggregation 对照律；F018 是本方向 b081 C004 absorbing anchor
- 🟢 [[gap_acceptance_structure]] `productive` — F020 = Std(gap_ret) × body_ratio rank-diff，higher-moment LHS 跨 family 复现
- 🟢 [[microstructure_illiquidity]] `productive` — F015/F016 rank-diff 起源 family；F012 是本方向 b081 C003 absorbing anchor
- 🟢 [[range_structure]] `productive` — T013 P008 escape 跨方向复现优先靶
- 🟢 [[anchor_proximity_momentum]] `productive` — T013 P008 escape 跨方向复现优先靶
- 🔴 [[return_distribution_signals]] `dead` — 同样 vol_20d 主导；alpha_surv 判别量教训源于此
- 🟢 [[lessons#Rank-Diff Geometry]] — 7 条硬约束 + 5 律升格源
- 🟢 [[lessons#OHLC Family Defaults]] — algebraic mirror / multi-day aggregation / sign × persistent drift
- 🟢 [[_consolidation/findings/pattern_analyst/019]] — Geometric absorbing-factor 律（本方向 F021 b081 C001 实证条目之一）
- 🟢 [[_consolidation/findings/pattern_analyst/021]] — In-batch denominator family 等价性自检（本方向 OHLC 等价分母 全 family 适用）

---

## Narrative Log

> [!quote]+ 2026-05-02 · [[batches/batch_081/judge|batch_081]] · admit=0 / reserve=1 / reject=5 · **status: productive → saturated**
> T012 第三轮 + T013 起始 — **60d 长窗 OHLC ratio Mean/Skew × cross-section RHS 范式整体饱和实证 + P008 TsRank escape 路径单点首验**.
> 6 candidate 跨 4 atom (hl_norm_sym, co_norm_sym, body_ratio_skew, num_trades_amount RHS) admit=0；5/6 候选触发 P006 library-reducer hard-block 同律. 关键 finding:
> 1. **hl_norm_sym=(H-L)/(H+L) 与 F021 RHS Mean(H/L,60) 数学同构** (C001 max_corr=0.677@F021) — atom-orthogonality 第七件: 同窗口分母变体 (H+L vs H/L 单调正相关) cross-section rank 高度同构. **Geometric absorbing-factor 律 (finding 019) 本方向首证**.
> 2. **co_norm_sym=(C-O)/(C+O) 60d Mean 与 F018 sustained directional drift 同源** (C004 max_corr=0.385@F018) — long-window signed body Mean 实证不脱 institutional accumulation drift basis.
> 3. **3 阶矩 Skew(body_ratio, 60) 统计显著性不足** (C002 ic_oos=-0.0041 hard_gate fail) — T012 next probes Skew/Kurt 路径**实证不可行**.
> 4. **num_trades_60 RHS 与 turnover/F012 流动性 cluster 共线** — 升格 dead RHS endpoints 候选清单.
> 5. **🆕 C006 P008 TsRank ratio-field≥60d escape 路径首例机制验证** — alpha_survival=0.993 ≈ 1.0 = Barra 空间独立载体 + max_corr=0.268 库内最干净 + style_r²=0.133 + vol_20d=12.56 (vs 同批 standalone 平均 25+) + ls_t=-3.64 + 9/9 yr 同号. 但 incr_ic=-0.035 整批最严重负 + mono_oos=-0.40 弱单调 + cum_ic_mdd=-108 极深 → **reserve, 等待跨方向复现**. **新 thread T013 单独追踪 P008 escape 路径**, 切其他方向（anchor_proximity_momentum / range_structure 等）测复现性.
>
> **MT budget**: cumulative 444→**450** · direction 34→**40** = 57% cap. **zero_admit_streak 4→5** (b063/b076/b079/b080/b081 五批连续).
>
> **Operations**　`status: productive → saturated` (5 批 zero admit 充分实证方向饱和) · priority `medium → low` · T012 [✓ ANSWERED] · T013 [◉ ACTIVE 跨方向待复现] · 本方向 60d-window probes 终结.

> [!quote]- 2026-04-28 · [[batches/batch_063/judge|batch_063]] · admit=0 / reserve=0 / reject=6
> T012 第二轮 — higher-moment OHLC × non-vol-cluster RHS 全 6 candidate reject + atom-orthogonality 三件套精细化为六件 (a) atom multi-regime stable + (b) atom 与 vol_20d 几何正交 + (c) normalizer 无 regime drift + (d) sign 保留 + (e) price normalizer 优于 range normalizer + (f) 避 OHLC mirror pair atom Std cluster. vol_20d 整库新纪录 (C003 76.53 / C002 53.04). zero_admit_streak 3→4. Operations: priority medium → low.

> [!quote]- 2026-04-25 · [[batches/batch_050/judge|batch_050]] · admit=1 / reserve=1 / reject=4 · **关键转折点 / direction 复活**
> direction `saturated → productive` (4 batch 0-admit 后突破)。**C005 admit F019 `body_disp_pricevol_rank_diff_20`**：LHS=Std(body_ratio,20) higher moment + RHS=Mean(Std($close,5),20) price_vol——hypothesis 复活条件 (a)+(c) 兑现 + max_corr=0.270 整批整库最干净 + incr_ic=0.020。**rank-diff 范式第 5 次跨家族 tipping point 正式确认** (跨 microstructure/overnight/OHLC 4 family 5 admit)，触发 Phase 5 consolidation。C001 reserve (alpha_surv=0.33 + max_corr=0.50 + incr_ic=0.013 borderline 死区)。4 reject 验证 7 硬约束。

> [!quote]- 2026-04-21 · [[batches/batch_021/judge|batch_021]] · admit=0 / reserve=1 / reject=2
> direction `productive → saturated`。3d open-position mono_sign_flip（F007 5d-only）；7d upper-shadow alpha_surv=1.685 但 corr=0.834@F006 → reserve 避 bloat；turnover-wt body sign corr=0.579@F007 → turnover 非新轴。Mean-base 累计 admit 率 14% (3/21)。

> [!quote]- 2026-04-21 · [[batches/batch_020/judge|batch_020]] · admit=1 / reject=1 · **关键转折点 / F008 admit**
> F008 upper_shadow_persistence_3d admit（alpha_surv=1.268 max_corr=0.758@F006，high-corr admit 先例）；10d upper-shadow mono_sign_flip → 确认 5d sweet spot 上界在 10d。

> [!quote]- 2026-04-21 · [[batches/batch_018/judge|batch_018]] · admit=1 / reject=4 · **关键转折点 / F007 admit**
> F007 open_position_persistence_5d admit（ic=+0.037 max_corr=0.276@F006 完全机制正交）。4 reject 暴露三 trap：algebraic mirror / magnitude-only / vol_20d mirror。

> [!quote]- 2026-04-21 · [[batches/batch_017/judge|batch_017]] · admit=1 / reserve=1 / reject=3 · **关键转折点 / 首 admit (F006) + 系统级元发现**
> status `exploring → productive`。F006 upper_shadow_persistence_5d admit：alpha_surv=1.508 + incr_ic=+0.031 + 9 年 IC 全正。**系统级元发现**：(1) alpha_survival 判别量；(2) 5d sweet spot；(3) upper-shadow 与 overnight-gap 机制正交。
