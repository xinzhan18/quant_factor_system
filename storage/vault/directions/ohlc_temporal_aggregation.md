---
direction_tag: ohlc_temporal_aggregation
status: saturated
priority: medium
rounds: 5
admits: 3
last_batch: batch_021
last_admits: []
last_goal: Round 5：F007 3d ablation (open-position 短期 phase variant)、7d upper-shadow
  (5d 与 10d 之间的 sweet spot 边界)、turnover-weighted body sign (与 F006/F007 不同的加权机制)。3
  候选探完剩余维度，目标 admit 1+ 或确认饱和。
last_activity: '2026-04-20T19:49:02Z'
created_batch: batch_017
members:
- F006
- F007
- F008
retired_members: []
merged_into: null
---
# ohlc_temporal_aggregation

> [!abstract]+ 方向概要
> **状态**　🟡 saturated · priority=medium · rounds=5 · admits=3
> **最近**　[[batches/batch_021/judge|batch_021]] · 2026-04-21 · admit=0 / reserve=1 / reject=2
> **一句话**　5d OHLC aggregation 至少 3 维独立（close 端 F006 / open 端 F007 / 3d phase F008），剩余维度 ROI 低，方向饱和。

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

---

## Related

- 🟡 [[intraday_price_formation]] `saturated` — 单日 body/shadow 已穷尽；本方向在其基础上探 multi-day aggregation
- 🔴 [[return_distribution_signals]] `dead` — 同样 vol_20d 主导；alpha_surv 判别量教训源于此
- 🟢 [[lessons#Structural Constraints]] — OHLC 三段约束 / algebraic mirror / vol_20d derivative pattern 系统级教训源

---

## Narrative Log

> [!quote]+ 2026-04-21 · [[batches/batch_021/judge|batch_021]] · admit=0 / reserve=1 / reject=2
> direction `productive → saturated`。3d open-position mono_sign_flip（F007 5d-only）；7d upper-shadow alpha_surv=1.685 但 corr=0.834@F006 → reserve 避 bloat；turnover-wt body sign corr=0.579@F007 → turnover 非新轴。累计 admit 率 14% (3/21)。下批触发 Phase 5 consolidation。

> [!quote]- 2026-04-21 · [[batches/batch_020/judge|batch_020]] · admit=1 / reject=1
> F008 upper_shadow_persistence_3d admit（alpha_surv=1.268 max_corr=0.758@F006，high-corr admit 先例）；10d upper-shadow mono_sign_flip（IS=-0.60 OOS=+0.90）→ 确认 5d sweet spot 上界在 10d。

> [!quote]- 2026-04-21 · [[batches/batch_019/judge|batch_019]] · admit=0 / reject=4
> 4/4 reject：rank 噪声 / F002 amount cluster / F007 mirror / discrete sign_flip。5d directional ratio 空间被 F006/F007 饱和信号首现；status 仍 productive，待 b020 验证。

> [!quote]- 2026-04-21 · [[batches/batch_018/judge|batch_018]] · admit=1 / reject=4
> F007 open_position_persistence_5d admit（ic=+0.037 max_corr=0.276@F006 完全机制正交）。4 reject 暴露三 trap：algebraic mirror（lower-shadow ≡ -upper-shadow）、magnitude-only（无符号失方向）、vol_20d mirror（\|gap\|/range alpha_surv=0.164 第 3 个 vol 衍生）。

> [!quote]- 2026-04-21 · [[batches/batch_017/judge|batch_017]] · admit=1 / reserve=1 / reject=3
> status `exploring → productive`（首 admit，4 轮 0-admit 后关键突破）。F006 upper_shadow_persistence_5d admit：alpha_surv=1.508 + incr_ic=+0.031 + cum_dd=-3.5（库内最浅）+ 9 年 IC 全正。**系统级元发现**：(1) alpha_survival 是 vol_20d 衍生判别量（C004 vs C005 对照）；(2) 5d 是 OHLC sweet spot；(3) upper-shadow 与 overnight-gap 机制正交（max_corr=0.069@F003）。
