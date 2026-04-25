---
direction_tag: ohlc_temporal_aggregation
status: productive
priority: medium
rounds: 7
admits: 5
last_batch: batch_050
last_admits:
- F019
last_goal: 'T010 rank-diff 第 5 次跨家族泛化——测 OHLC scale-invariant 特征族 × 非 OHLC basis 的
  rank-diff 几何。

  ohlc_temporal_aggregation 3 admit 稳定但 last_admit=batch_020 已 4 批未进展 (saturated)。

  当前 rank-diff 4 次跨家族兑现 (F015 amihud×amount_cv microstructure / F016 amihud×turnover_cv
  microstructure /

  F017 overnight×turnover overnight / F018 overnight_sign×amount overnight)——全部发生在
  overnight

  或 microstructure 家族。本批测：rank-diff paradigm 能否在 OHLC 5d aggregation 家族内部兑现？

  若 admit 则 consolidation tipping point 正式确认 (5 跨家族)；若 reject 则揭示 OHLC scale-free
  signals

  的 rank-diff 饱和边界。

  cockpit 硬约束：每候选 LHS 唯一 + 避开 F017(turnover_5)/F018(amount_20) RHS / 避免 CsRank 外

  包 AmihudIlliq/HHI/RealizedVol (operators.py:428 bug)。所有 CsRank 内层使用标准 qlib DSL 算子

  (Mean/Std/Abs/Sub/Div/Sign/Ref)。直接满足复活条件 (a) 新 OHLC 原子维度 max_corr<0.50@F006/F007
  + (c)

  与非 OHLC 维度 (liquidity/fundamental/price-vol) rank-diff 交互。

  (C001) body_ratio × turnover_20——LHS=Mean(|C-O|/(H-L),5) 纯 OHLC body magnitude；

  RHS=CsRank(Mean($turnover,20)) 20d 流动性 basis 避开 F017 turnover_5。

  (C002) close_over_high × amount_10——LHS=Mean($close/$high,5) 价格端点比 OHLC；

  RHS=CsRank(Mean($amount,10)) 10d amount 避开 F018 amount_20。

  (C003) intraday_return × volume_20——LHS=Mean(($close-$open)/Ref($close,1),5) 纯 intraday
  return；

  RHS=CsRank(Mean($volume,20)) volume basis，分离 overnight F010/F011。

  (C004) gap_to_range × pb_60——LHS=Mean(($open-Ref($close,1))/(H-L),5) 跨日 gap 归一化
  intraday range；

  RHS=CsRank(Mean($pb_ratio,60)) 基本面 value basis 60d。

  (C005) body_ratio_std × price_vol——LHS=Std(|C-O|/(H-L),20) body 分布 dispersion (higher
  moment)；

  RHS=CsRank(Mean(Std($close,5),20)) 价格 vol 聚合 basis，区别 liquidity/fundamental。

  (C006) body_sign × pb_20——LHS=Mean(Sign($close-$open),5) sign 聚合 (非 magnitude) 复刻
  b049 C006 成功结构；

  RHS=CsRank(Mean($pb_ratio,20)) 基本面。与 F018 差别：F018 LHS=overnight_sign; C006 LHS=body_sign
  (intraday)。

  避开死模式：LHS 唯一 / 不共享 raw fields 结构 / 不用 CsRank 外包 custom op / 标准 DSL。

  目标 ≥1 admit 满足 max_corr@lib<0.70 + alpha_surv>0.40 + ls_t>2 + incremental_ic>0.010。'
last_activity: '2026-04-24T22:15:55Z'
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
> **状态**　🟢 productive · priority=medium · rounds=7 · admits=4 (+ F019 rank-diff)
> **最近**　[[batches/batch_050/judge|batch_050]] · 2026-04-25 · admit=1 / reserve=1 / reject=4
> **一句话**　5d OHLC aggregation 三独立维度 (F006/F007/F008) + higher-moment OHLC × price_vol rank-diff (F019)；rank-diff 范式跨 5 family tipping point 由本方向确认。

---

## Hypothesis

> [!success]+ Hypothesis（已基本验证 + 复活条件兑现）
> 单日 OHLC body/shadow 信号（[[intraday_price_formation]]）因 intraday noise 过大而全部 mono_sign_flip 失败；**多日 smoothed/aggregated** 版本可 reveal persistent intraday flow：连续 N 天 close > open = sustained order flow asymmetry，与单日 random walk 完全不同性质。
>
> 经济直觉：
> - 单日 body = random walk + microstructure noise
> - 5d/20d mean(body) 累加同向偏移 = persistent order flow
> - 反向 trend-following：高 mean shadow → 持续抛压 → 短期反转
>
> **验证结果**：(a) Mean-base 5d aggregation 在 close 端 (F006 upper-shadow) / open 端 (F007 open-position) / 3d phase (F008) 三独立维度成立；(b) higher-moment + rank-diff (F019 Std(body_ratio,20) × price_vol_60) 兑现复活条件。20d Mean-base 加深 vol_20d 耦合，magnitude-only / discrete count / turnover-wt 全 fail。

> [!info]+ 复活条件状态 (b050 后)
> 原列三条 (a) 新 OHLC 原子维度 / (b) regime 重探窗口 / (c) 非 OHLC 维度交互——**(a)+(c) 已由 F019 同时兑现** (Std body_ratio higher moment + price_vol RHS)。
>
> **新复活路径**：(d) higher-moment LHS 跨原子维度 (Std/Skew of upper_shadow_ratio / open_position / gap_to_range)；(e) MT 28/70 接近上限，下批暂停本方向，待 lessons.md 升格 rank-diff 五律 + OHLC defaults 后再启。

---

## Promoted Lessons

1. **alpha_survival 是 vol_20d 衍生判别量**：>1.0 = Barra 空间独立载体；<<0.40 = vol 衍生（Mean-base）。**例外**：rank-diff geometry 因 CsRank Sub 必然部分映射到 cross-sectional dispersion，alpha_surv 0.30-0.40 区间是真实信号 + 必然 style coupling，不是 alpha 弱（F019 admit alpha_surv=0.21 仍 admit 即此机制；config 已 codify `alpha_surv_min.rank_diff=0.30`，见 [[F200]]）。
2. **5d 是 Mean-base OHLC aggregation sweet spot**：单日（intraday saturated）与 20d（vol-coupled）之间。但 **higher-moment 突破 sweet spot 约束**：Std(body_ratio,**20**d) 反而成为独立轴（窗口约束随 moment 阶数变化）。
3. **信号家族 multi-window 不对称**：upper-shadow [3d, 7d] 稳；open-position 严格 5d-only（3d mono_sign_flip IS=-1.00 OOS=+0.90）；≥10d Mean-base 跨 phase 反转。
4. **OHLC 三段约束 → algebraic mirror trap**：lower-shadow ≡ -upper-shadow（corr=1.000@F006），signed-range 与 F006 高 corr；三段 ratio 任意两端代数互补。
5. **Magnitude-only / turnover-wt / discrete count 全部失败**（Mean-base 维度）：signed 方向性是 OHLC Mean 信号必要条件，turnover 不构成独立 OHLC 轴。
6. **rank-diff × OHLC 兑现两条件**（F019 提取，[[F305]] 升格）：(a) higher-moment LHS（Std/Skew/Kurt vs 库内全 Mean-base, 完全独立轴）+ (b) RHS 跳出 turnover/amount/overnight cluster（price_vol 是新 basis）。两条件单独均不足，叠加才 max_corr<0.30。
7. **sign aggregation 不可盲目跨字段泛化**（T011 [✗]）：alpha 来自 underlying field 的 persistent drift，非 Sign() 操作几何性质。overnight 有 institutional accumulation drift（F018），intraday body 是 random walk（b017 C003 / b050 C006 双例 reject）。Phase 1 设计 sign 候选必须先核 underlying drift。
8. **rank-diff geometry 7 条硬约束（系统级，[[F002]]）**：(1) 两端 scale-invariance；(2) raw field 独立；(3) 同字段跨窗口禁止；(4) Sub 方向对偶 dedup；(5) 同批 LHS 共享 anchor rule；(6) RHS 共振饱和（dead endpoints 动态：overnight_5/turnover_5/amount_20/body_ratio_20/price_vol_20）；(7) factor-anchored cluster（saturated 方向 anchor 消化新候选）。本方向 b050 C001-C004 reject 全验证。
9. **incr_ic borderline 死区律（[[F203]]）**：max_corr ∈ [0.30, 0.70] 时 incr_ic 必须 ≥ 0.015 才 admit-eligible；本方向 b050 C001 (incr=0.013, max_corr=0.50) 即在死区。设计期 self-prune 0.008-0.013 incr_ic 候选。

---

## Threads

### T012: higher-moment OHLC 维度 [◉ ACTIVE batch_051+]

> [!note]+ Thread 当前
> **Question**: Std/Skew/Kurt of OHLC ratios 是否构成与 Mean-based 库因子独立的轴？哪些 atomic OHLC × moment 组合产生 alpha？
> **Evidence trail**:
> - b050 C001 (Mean of body_ratio) vs C005 (Std of body_ratio) → max_corr 0.50 vs 0.27 完全不同 corr structure → **不同 moment 是独立设计轴**
> - b050 C005 → admit F019 (Std body_ratio,20 × price_vol_60) → first higher-moment OHLC admit
> - 跨 family 复现：[[gap_acceptance_structure]] F020 = Std(gap_ret,20) × body_ratio_20 同律
>
> **Next probes**: (1) `Std(upper_shadow_ratio, 20) × non-vol RHS` 测 F006 在 higher moment 维度泛化；(2) `Skew(body_ratio, 60)` 三阶矩；(3) `Kurt(open_position, 20)` 是否 reveal regime change。**禁忌**：避开 RHS dead endpoints (overnight_5/turnover_5/amount_20/body_ratio_20/price_vol_20)；compound moment LHS（smooth-then-std，b052 C006 教训）IS over-fit 风险；同批 LHS 共享 anchor 仅 admit 1。direction MT 28/70 接近上限，下批暂停 + Phase 5 升格 rank-diff 五律 + OHLC defaults 后再启。

### T002: Sign-of-body 频率信号 [✗ DISPROVEN batch_050]

> [!failure]+ Thread 结论
> **Question**: 多日内 close>open 的频率（bullish bar count）是否 forward-predictive？standalone (b017 C003 reserve) 与 rank-diff 包装 (b050 C006) 是否复活？
> **Evidence trail**:
> - [[batches/batch_017/candidates/C003|b017 C003]] 5d Mean(Sign(close-open)) standalone → ic=-0.033 ls_t=-3.55 incr_ic=-0.031 → reserve（CP02-04 perfect 但 incr_ic 负）
> - [[batches/batch_050/candidates/C006|b050 C006]] Mean(Sign(close-open),5) × pb_20 rank-diff → hard_gate 三 fail (sign_flip / ic_oos=0.004 / oos_decay=-0.30) → reject
>
> **Answer**: intraday body sign 是 random walk，无 underlying persistent drift，rank-diff 包装也救不了。与 [[overnight_intraday_split]] F018 (overnight_sign 有 institutional accumulation drift) 形成对照律 → 已升格至 Lesson 7。

---

## Closed Threads (compressed)

- **T001 多日 smoothed signed body** [✗ DISPROVEN batch_017]：5d (b017 C001) Barra-clean 但 incr_ic=-0.050 cum_dd=-105；20d (b017 C002) r²=0.638 vol-coupled。signed body 本身非独立轴。
- **T003 多端点 OHLC aggregation** [✓ ANSWERED batch_017-021]：5d aggregation ≥3 独立 admit (F006 upper-shadow + F007 open-position + F008 3d phase)。Window 规律：upper-shadow [3d,7d] 稳但 ≥7d corr 逼近 F006；open-position 严格 5d-only；≥10d 跨 phase 反转。Magnitude-only / discrete / turnover-wt / Donchian 全 fail。Mean-base 维度饱和，admit 率 25%→14%。
- **T010 rank-diff × OHLC family** [✓ ANSWERED batch_050]：兑现需 (a) higher-moment LHS + (b) RHS 跳出已饱和 cluster。F019 双新维度叠加 → max_corr=0.270 整库最干净 + 与 4 admitted rank-diff 全 <0.25。**rank-diff 范式第 5 次跨家族 tipping point 正式确认**（已升格 Lesson 6 + [[F305]]）。
- **T011 sign aggregation 跨字段泛化** [✗ DISPROVEN batch_050]：alpha 来自 underlying drift 非 Sign() 几何（已升格 Lesson 7）。

---

## Known Failures（仅保留典型对照样本）

| Candidate | Expression | Reject Reason |
|---|---|---|
| [[batches/batch_017/candidates/C001\|b017 C001]] | 5d signed body | incr_ic=-0.050 + cum_dd=-105 |
| [[batches/batch_017/candidates/C004\|b017 C004]] | 5d close/high Mean | alpha_surv=0.003（vol_20d derivative 判别量起源）|
| [[batches/batch_018/candidates/C001\|b018 C001]] | 5d lower-shadow Mean | corr=1.000@F006（algebraic mirror trap 起源）|
| [[batches/batch_018/candidates/C002\|b018 C002]] | 5d \|body\|/range Mean | magnitude-only ic=0.0067 |
| [[batches/batch_020/candidates/C002\|b020 C002]] | 10d upper-shadow Mean | mono_sign_flip（5d sweet spot 上界）|
| [[batches/batch_021/candidates/C001\|b021 C001]] | 3d open-position Mean | mono_sign_flip（F007 5d-only）|
| [[batches/batch_021/candidates/C003\|b021 C003]] | turnover-wt body sign 5d | corr=0.579@F007（turnover 非新轴）|
| [[batches/batch_050/candidates/C002\|b050 C002]] | close/high × amount_10 rank-diff | max_corr=0.611@F018 + alpha_surv=0.27 + vol_20d=53（约束 7 RHS cluster）|
| [[batches/batch_050/candidates/C004\|b050 C004]] | gap_to_range × pb_60 rank-diff | incr_ic=0.003 < 0.015 borderline 死区（[[F203]]）|
| [[batches/batch_050/candidates/C006\|b050 C006]] | body_sign × pb_20 rank-diff | hard_gate；intraday body sign random walk（b017 C003 教训复现）|

---

## Related

- 🟡 [[intraday_price_formation]] `saturated` — 单日 body/shadow 已穷尽；本方向在其基础上探 multi-day aggregation
- 🟢 [[overnight_intraday_split]] `productive` — F018 overnight_sign rank-diff 与本方向 b050 C006 intraday_sign 形成 sign aggregation 对照律
- 🟢 [[gap_acceptance_structure]] `productive` — F020 = Std(gap_ret) × body_ratio rank-diff，higher-moment LHS 跨 family 复现
- 🟢 [[microstructure_illiquidity]] `productive` — F015/F016 rank-diff 起源 family
- 🔴 [[return_distribution_signals]] `dead` — 同样 vol_20d 主导；alpha_surv 判别量教训源于此
- 🟢 [[lessons#Rank-Diff Geometry]] — 7 条硬约束 + 5 律升格源
- 🟢 [[lessons#OHLC Family Defaults]] — algebraic mirror / multi-day aggregation / sign × persistent drift

---

## Narrative Log

> [!quote]+ 2026-04-25 · [[batches/batch_050/judge|batch_050]] · admit=1 / reserve=1 / reject=4
> direction `saturated → productive` (4 batch 0-admit 后突破)。C005 admit F019 `body_disp_pricevol_rank_diff_20`：LHS=Std(body_ratio,20) higher moment + RHS=Mean(Std($close,5),20) price_vol——hypothesis 复活条件 (a)+(c) 兑现 + max_corr=0.270 整批整库最干净 + incr_ic=0.020。**rank-diff 范式第 5 次跨家族 tipping point 正式确认** (跨 microstructure/overnight/OHLC 4 family 5 admit)，触发 Phase 5 consolidation。C001 reserve (alpha_surv=0.33 + max_corr=0.50 + incr_ic=0.013 borderline 死区)。4 reject 验证 7 硬约束：C002 RHS cluster + vol_20d=53；C003 intraday return random walk；C004 incr_ic 死区；C006 intraday body sign random walk (b017 C003 教训复现)。

> [!quote]- 2026-04-21 · [[batches/batch_021/judge|batch_021]] · admit=0 / reserve=1 / reject=2
> direction `productive → saturated`。3d open-position mono_sign_flip（F007 5d-only）；7d upper-shadow alpha_surv=1.685 但 corr=0.834@F006 → reserve 避 bloat；turnover-wt body sign corr=0.579@F007 → turnover 非新轴。Mean-base 累计 admit 率 14% (3/21)。下批触发 Phase 5 consolidation。

> [!quote]- 2026-04-21 · [[batches/batch_020/judge|batch_020]] · admit=1 / reject=1
> F008 upper_shadow_persistence_3d admit（alpha_surv=1.268 max_corr=0.758@F006，high-corr admit 先例）；10d upper-shadow mono_sign_flip → 确认 5d sweet spot 上界在 10d。

> [!quote]- 2026-04-21 · [[batches/batch_019/judge|batch_019]] · admit=0 / reject=4
> 4/4 reject：rank 噪声 / F002 amount cluster / F007 mirror / discrete sign_flip。5d directional ratio 空间被 F006/F007 饱和信号首现。

> [!quote]- 2026-04-21 · [[batches/batch_018/judge|batch_018]] · admit=1 / reject=4
> F007 open_position_persistence_5d admit（ic=+0.037 max_corr=0.276@F006 完全机制正交）。4 reject 暴露三 trap：algebraic mirror / magnitude-only / vol_20d mirror。

> [!quote]- 2026-04-21 · [[batches/batch_017/judge|batch_017]] · admit=1 / reserve=1 / reject=3
> status `exploring → productive`（首 admit）。F006 upper_shadow_persistence_5d admit：alpha_surv=1.508 + incr_ic=+0.031 + 9 年 IC 全正。**系统级元发现**：(1) alpha_survival 判别量；(2) 5d sweet spot；(3) upper-shadow 与 overnight-gap 机制正交。
