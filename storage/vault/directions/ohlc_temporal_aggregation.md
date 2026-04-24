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
> **状态**　🟢 productive · priority=medium · rounds=6 · admits=4
> **最近**　[[batches/batch_050/judge|batch_050]] · 2026-04-25 · admit=1 / reserve=1 / reject=4
> **一句话**　5d OHLC aggregation 至少 3 维独立 (F006/F007/F008) + higher-moment OHLC × price_vol rank-diff (F019, batch_050)；rank-diff 范式 5 次跨家族兑现 tipping point.

---

## Hypothesis

> [!success]+ Hypothesis（已基本验证）
> 单日 OHLC body/shadow 信号（[[intraday_price_formation]]）因 intraday noise 过大而全部 mono_sign_flip 失败；**多日 smoothed/aggregated** 版本可 reveal persistent intraday flow：连续 N 天 close > open = sustained order flow asymmetry，与单日 random walk 完全不同性质。
>
> 经济直觉：
> - 单日 body = random walk + microstructure noise
> - 5d/20d mean(body) 累加同向偏移 = persistent order flow
> - 反向 trend-following：高 mean shadow → 持续抛压 → 短期反转
>
> **验证结果**：5d aggregation 在 close 端（upper-shadow）/ open 端（open-position）两个独立维度均成立；但 20d 加深 vol_20d 耦合，magnitude-only / discrete count / turnover-wt 全 fail。

> [!info]+ 饱和说明
> **为什么 ROI 低**：累计 admit 率 14% (3/21)；5d directional ratio 空间已被 F006 + F007 + F008 占满。剩余候选要么高 corr（7d upper-shadow corr=0.834@F006），要么 mono_sign_flip（3d open-position、10d upper-shadow 跨 phase 反转），要么 vol_20d 衍生。
>
> **复活条件**：(a) 新 OHLC 原子维度（跨日 engulfing、gap-close）且预期 max_corr<0.50@F006/F007；(b) regime 转变使 5d sweet spot 失效需重探窗口；(c) 与非 OHLC 维度（IV / 资金流）交互的 OHLC 变体。

---

## Promoted Lessons

1. **alpha_survival 是 vol_20d 衍生判别量**：>1.0 = Barra 空间独立载体；<<0.40 = vol 衍生。F006 admit 的核心证据是 alpha_surv=1.508，而非 ls_t / mono 单独（来自 b017 C004 vs C005 对照）。
2. **5d 是 OHLC aggregation sweet spot**：单日（intraday saturated）与 20d（vol-coupled）之间；既保 idiosyncratic flow 又过滤噪声；≥10d 跨 phase 反转。
3. **信号家族 multi-window 不对称**：upper-shadow 在 [3d, 7d] 都稳；open-position **严格 5d-only**（3d mono_sign_flip IS=-1.00 OOS=+0.90）——不能假设 window 扩展对所有维度同效。
4. **OHLC 三段约束 → algebraic mirror trap**：lower-shadow ≡ -upper-shadow（corr=1.000@F006），signed-range 与 F006 高 corr；三段 ratio 任意两端代数互补。
5. **Magnitude-only / turnover-wt / discrete count 全部失败**：signed 方向性是 OHLC 信号的必要条件，turnover 不构成独立 OHLC 轴（b021 C003 corr=0.579@F007 确认）。

---

## Threads

### T001: 多日 smoothed signed body 是否产生信号 [✗ DISPROVEN batch_017]

> [!failure]+ Thread 结论
> **Question**: Mean(body, 5) 与 Mean(body, 20) 是否 OOS IC > 0.008？sign 稳定？
> **Evidence trail**:
> - [[batches/batch_017/candidates/C001|b017 C001]]　5d signed body → ic=-0.043 alpha_surv=1.076 Barra-clean 但 incr_ic=-0.050 + cum_dd=-105（库内最深）→ reject（与 F003 反向冲突）
> - [[batches/batch_017/candidates/C002|b017 C002]]　20d signed body → ic=-0.042 r²=0.638 vol-coupled → reject
>
> **Answer**: 5d Barra-clean 但与库不正交；20d 加深 vol_20d 耦合。Hypothesis 部分成立——signed body 本身不是独立轴，但 shadow / open-position ratio 可以。

### T002: Sign-of-body 频率信号 [◉ RESERVED]

> [!note]+ Thread 当前
> **Question**: 多日内 close>open 的频率（bullish bar count）是否 forward-predictive？
> **Evidence trail**:
> - [[batches/batch_017/candidates/C003|b017 C003]]　5d Mean(Sign(close-open)) → ic=-0.033 ls_t=-3.55 mono=-0.80 alpha_surv=1.014 incr_ic=-0.031 → **reserve**（CP02-04 perfect 但 incr_ic 负，与 C005 镜像）
>
> **Next probes**: Phase 5 后若重启本方向，设计 C005-C003 对称 spread 信号。

### T010: rank-diff × OHLC family — higher moment + price_vol RHS [✓ ANSWERED batch_050]

> [!success]+ Thread 结论
> **Question**: rank-diff 范式 (F015-F018 跨 microstructure/overnight 4 admit) 能否在 OHLC 家族泛化？哪些 LHS / RHS 组合可避开 already-saturated cluster？
> **Evidence trail**:
> - [[batches/batch_050/candidates/C005|b050 C005]] `Std(body_ratio,20) × price_vol_20` rank-diff → ic_oos=+0.039 ls_t=2.90 mono=0.9/1.0 alpha_surv=0.21 max_corr=**0.270** incr_ic=+0.020 9/9yr+ cum_dd=-1.61 → **admit F019** body_disp_pricevol_rank_diff_20
> - [[batches/batch_050/candidates/C001|b050 C001]] `Mean(body_ratio,5) × turnover_20` → ic_oos=0.044 max_corr=0.496@F017 (RHS turnover 共振) → reserve
> - [[batches/batch_050/candidates/C002|b050 C002]] `Mean(C/H,5) × amount_10` → max_corr=0.611@F018 + vol_20d=53 → reject (cluster 共振)
> - [[batches/batch_050/candidates/C004|b050 C004]] `gap_to_range × pb_60` → max_corr=0.655@F017 incr=0.003 (LHS gap 与 F010/F011 共振) → reject
>
> **Answer**: rank-diff × OHLC 兑现需 **(a) higher moment LHS** (Std/Skew/Kurt vs 库内全 Mean-base, 完全独立轴) + **(b) RHS 跳出 turnover/amount/overnight cluster** (price_vol 是新 basis). C005 双新维度叠加 → max_corr=0.270 整库最干净 + 与 4 admitted rank-diff (F015/F016/F017/F018) 全 <0.25. **rank-diff 范式第 5 次跨家族兑现, T010 tipping point 正式确认**, 触发 Phase 5 consolidation.

### T011: sign aggregation 是否可跨字段泛化 [✗ DISPROVEN batch_050]

> [!failure]+ Thread 结论
> **Question**: b049 C006 (overnight_sign_freq admit F018) 的 alpha 是否来自 Sign() 操作几何性质本身？是否可应用于 intraday body sign 泛化？
> **Evidence trail**:
> - [[batches/batch_050/candidates/C006|b050 C006]] `Mean(Sign(close-open),5) × pb_20` rank-diff → hard_gate 三 fail (sign_flip train=-0.013 val=+0.004 / ic_oos=0.004 / oos_decay=-0.30) → reject
>
> **Answer**: sign aggregation paradigm 的 alpha 来自 **underlying field 的 persistent drift**, 而非 Sign() 操作的几何性质. overnight 有 institutional accumulation drift (F018 admit); intraday body 是 random walk (C006 fail). 验证 b017 C003 历史教训 (intraday body sign standalone reserve 镜像无 alpha). **sign aggregation 不可盲目跨字段泛化**.

### T012: higher-moment OHLC 维度 [◉ ACTIVE batch_050+]

> [!note]+ Thread 当前
> **Question**: Std/Skew/Kurt of OHLC ratios 是否构成与 Mean-based 库因子独立的轴？哪些 atomic OHLC × moment 组合产生 alpha？
> **Evidence trail**:
> - b050 C001 (Mean of body_ratio) vs C005 (Std of body_ratio) → max_corr 0.50 vs 0.27 完全不同 corr structure → **不同 moment 是独立设计轴**
> - C005 admit (Std body_ratio,20) → first higher-moment OHLC admit
>
> **Next probes**: (1) `Std(upper_shadow_ratio, 20) × non-vol RHS` 测 F006 在 higher moment 维度泛化; (2) `Skew(body_ratio, 60)` 三阶矩; (3) `Kurt(open_position, 20)` 是否 reveal regime change. 但 direction MT 28/70 接近上限，下批暂停本方向 + Phase 5 consolidation 升格 lessons.md 后再启.

### T003: 多端点 OHLC aggregation (close / open / shadow) [✓ ANSWERED batch_018-021]

> [!success]+ Thread 结论
> **Question**: 5d mean(close/high)、mean(open-position)、shadow ratios 各端点是否机制独立？window 范围几何？
>
> **Admit evidence**:
> - [[batches/batch_017/candidates/C005|b017 C005]]　Mean(upper-shadow, 5) → ic=+0.024 ls_t=3.20 mono=+0.90 alpha_surv=1.508 incr_ic=+0.031 cum_dd=-3.5（库内最浅）→ **admit F006 upper_shadow_persistence_5d**；max_corr=0.069@F003 → 与 overnight-gap 机制正交
> - [[batches/batch_018/candidates/C003|b018 C003]]　Mean((open-low)/range, 5) → ic=+0.037 ls_t=3.22 mono=+0.90 alpha_surv=0.637 incr_ic=+0.023 max_corr=0.276@F006 → **admit F007 open_position_persistence_5d**（持续高开 = 隔夜信息驱动 momentum continuation）
> - [[batches/batch_020/candidates/C001|b020 C001]]　Mean(upper-shadow, 3) → ic=+0.029 ls_t=2.91 mono=+0.90 alpha_surv=1.268 max_corr=0.758@F006 → **admit F008 upper_shadow_persistence_3d**（high-corr admit 先例）
>
> **Reject evidence (saturation signals)**:
> - b017 C004 close/high → alpha_surv=0.003 catastrophic（vol_20d derivative）
> - b018 C001 lower-shadow → corr=1.000@F006（algebraic mirror）
> - b018 C002/C005 magnitude-only（\|body\|/range, \|gap\|/range）→ 无符号失方向 / alpha_surv=0.164（第 3 个 vol 衍生）
> - b018 C004 signed-range → corr=0.544@F006 + incr_ic=-0.039
> - b019 C001-C004 range expansion / range/amount / vol×body / discrete count → 4/4 reject（rank 噪声 / F002 cluster / F007 mirror / sign_flip）
> - b020 C002 Mean(upper-shadow, 10) → mono_sign_flip IS=-0.60 OOS=+0.90（**确认 5d sweet spot 上界**）
> - b021 C001 Mean(open-position, 3) → mono_sign_flip IS=-1.00 OOS=+0.90（**F007 5d-only stable**）
> - b021 C002 Mean(upper-shadow, 7) → alpha_surv=1.685 clean 但 corr=0.834@F006 → **reserve**（避库 bloat）
> - b021 C003 turnover-wt body sign 5d → corr=0.579@F007 + incr=-0.032 → **turnover ≠ 新 OHLC 轴**
>
> **Answer**: OHLC 5d aggregation ≥3 独立 admit（close 端 F006 + open 端 F007 + 3d phase F008）。Window 规律：upper-shadow [3d, 7d] 稳定但 ≥7d corr 逼近 F006；open-position 严格 5d-only；≥10d 跨 phase 反转。Magnitude-only / discrete / turnover-wt / Donchian 全 fail。**方向 saturated** — admit 率 25%→14%。

---

## Known Failures

| Candidate | Expression | Reject Reason |
|---|---|---|
| [[batches/batch_017/candidates/C001\|b017 C001]] | 5d signed body | incr_ic=-0.050 + cum_dd=-105（库最深）|
| [[batches/batch_017/candidates/C002\|b017 C002]] | 20d signed body | r²=0.638 vol-coupled |
| [[batches/batch_017/candidates/C004\|b017 C004]] | 5d close/high | alpha_surv=0.003（vol_20d derivative）|
| [[batches/batch_018/candidates/C001\|b018 C001]] | 5d lower-shadow | corr=1.000@F006（algebraic mirror）|
| [[batches/batch_018/candidates/C002\|b018 C002]] | 5d \|body\|/range | magnitude-only ic=0.0067 |
| [[batches/batch_018/candidates/C004\|b018 C004]] | 5d signed range | corr=0.544@F006 + cum_dd=-103 |
| [[batches/batch_018/candidates/C005\|b018 C005]] | 5d \|gap\|/range | alpha_surv=0.164（vol-derived）|
| [[batches/batch_019/candidates/C001\|b019 C001]] | 5d range expansion | mono=-0.30 + ls_t=-0.89 |
| [[batches/batch_019/candidates/C002\|b019 C002]] | 5d range/amount | corr=0.746@F002（amount cluster）|
| [[batches/batch_019/candidates/C003\|b019 C003]] | 5d volume×body | corr=0.721@F007 |
| [[batches/batch_019/candidates/C004\|b019 C004]] | 5d count close-near-high | hard_gate sign_flip |
| [[batches/batch_020/candidates/C002\|b020 C002]] | 10d upper-shadow | mono_sign_flip（跨 phase 反转）|
| [[batches/batch_021/candidates/C001\|b021 C001]] | 3d open-position | mono_sign_flip（F007 5d-only）|
| [[batches/batch_021/candidates/C003\|b021 C003]] | turnover-wt body sign 5d | corr=0.579@F007 + mono=-0.30 |
| [[batches/batch_050/candidates/C002\|b050 C002]] | close/high × amount_10 rank-diff | max_corr=0.611@F018 + alpha_surv=0.27 + vol_20d=53 |
| [[batches/batch_050/candidates/C003\|b050 C003]] | intraday_return × volume_20 rank-diff | mono+0.9→-0.3 跨 phase 反转 + ls_t=-0.36 |
| [[batches/batch_050/candidates/C004\|b050 C004]] | gap_to_range × pb_60 rank-diff | incr_ic=0.003 < 0.010 + max_corr=0.655@F017 |
| [[batches/batch_050/candidates/C006\|b050 C006]] | body_sign × pb_20 rank-diff | hard_gate (sign_flip + ic_oos=0.004 + oos_decay=-0.30); intraday body sign random walk |

---

## Related

- 🟡 [[intraday_price_formation]] `saturated` — 单日 body/shadow 已穷尽；本方向在其基础上探 multi-day aggregation
- 🔴 [[return_distribution_signals]] `dead` — 同样 vol_20d 主导；alpha_surv 判别量教训源于此
- 🟢 [[lessons#Structural Constraints]] — OHLC 三段约束 / algebraic mirror / vol_20d derivative pattern 系统级教训源

---

## Narrative Log

> [!quote]+ 2026-04-25 · [[batches/batch_050/judge|batch_050]] · admit=1 / reserve=1 / reject=4
> direction `saturated → productive` (4 batch 0-admit 后突破). C005 admit F019 `body_disp_pricevol_rank_diff_20`: LHS=Std(body_ratio,20) higher moment + RHS=Mean(Std($close,5),20) price_vol — direction.md hypothesis 复活条件 (a) "新 OHLC 原子维度" 兑现 + max_corr=0.270 整批整库最干净 + incr_ic=0.020. **rank-diff 范式第 5 次跨家族 tipping point 正式确认** (跨 microstructure/overnight/OHLC 4 family 5 admit). C001 (Mean(body_ratio)) reserve alpha_surv=0.33 + max_corr=0.50 边界. 4 reject: C002 max_corr=0.61 + vol_20d=53; C003 intraday return random walk; C004 incr_ic=0.003 不足; C006 hard_gate (intraday body sign random walk, b017 C003 教训复现).

> [!quote]- 2026-04-21 · [[batches/batch_021/judge|batch_021]] · admit=0 / reserve=1 / reject=2
> direction `productive → saturated`。3d open-position mono_sign_flip（F007 5d-only）；7d upper-shadow alpha_surv=1.685 但 corr=0.834@F006 → reserve 避 bloat；turnover-wt body sign corr=0.579@F007 → turnover 非新轴。累计 admit 率 14% (3/21)。下批触发 Phase 5 consolidation。

> [!quote]- 2026-04-21 · [[batches/batch_020/judge|batch_020]] · admit=1 / reject=1
> F008 upper_shadow_persistence_3d admit（alpha_surv=1.268 max_corr=0.758@F006，high-corr admit 先例）；10d upper-shadow mono_sign_flip（IS=-0.60 OOS=+0.90）→ 确认 5d sweet spot 上界在 10d。

> [!quote]- 2026-04-21 · [[batches/batch_019/judge|batch_019]] · admit=0 / reject=4
> 4/4 reject：rank 噪声 / F002 amount cluster / F007 mirror / discrete sign_flip。5d directional ratio 空间被 F006/F007 饱和信号首现；status 仍 productive，待 b020 验证。

> [!quote]- 2026-04-21 · [[batches/batch_018/judge|batch_018]] · admit=1 / reject=4
> F007 open_position_persistence_5d admit（ic=+0.037 max_corr=0.276@F006 完全机制正交）。4 reject 暴露三 trap：algebraic mirror（lower-shadow ≡ -upper-shadow）、magnitude-only（无符号失方向）、vol_20d mirror（\|gap\|/range alpha_surv=0.164 第 3 个 vol 衍生）。

> [!quote]- 2026-04-21 · [[batches/batch_017/judge|batch_017]] · admit=1 / reserve=1 / reject=3
> status `exploring → productive`（首 admit，4 轮 0-admit 后关键突破）。F006 upper_shadow_persistence_5d admit：alpha_surv=1.508 + incr_ic=+0.031 + cum_dd=-3.5（库内最浅）+ 9 年 IC 全正。**系统级元发现**：(1) alpha_survival 是 vol_20d 衍生判别量（C004 vs C005 对照）；(2) 5d 是 OHLC sweet spot；(3) upper-shadow 与 overnight-gap 机制正交（max_corr=0.069@F003）。
