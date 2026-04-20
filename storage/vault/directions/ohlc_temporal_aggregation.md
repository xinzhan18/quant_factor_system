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

## Hypothesis

Single-day OHLC body/shadow signals (intraday_price_formation 方向) 全部 mono_sign_flip 失败——单日内 noise 太大，盖过任何稳定信号。但 **多日 smoothed/aggregated** 版本可能 reveal persistent intraday flow patterns：连续 N 天 close > open 反映 sustained buying pressure，与单日的 random walk 完全不同性质。

经济直觉：
- 单日 body 是 noisy 的（开盘到收盘是 random walk + microstructure noise）
- 5d/20d mean(body) 累加同向偏移 = persistent order flow asymmetry
- Trend-following 的反向：高 mean body → 持续买入 → 已 stretched → 短期反转

## Current Focus

**新方向首批 batch_017**：测试 5d/20d 聚合的 body / 强度 / 方向一致性 是否携带超出 single-day 的信号。

## Threads

### T001: 多日 smoothed body 是否产生信号 [✓ ANSWERED batch_017]
**Question**: Mean(body, 5) 和 Mean(body, 20) 是否 OOS IC > 0.008？sign 是否稳定？
**Evidence trail**:
- [[batches/batch_017/candidates/C001|batch_017 C001]]: 5d signed body → ic=-0.043 ls_t=-2.87 alpha_surv=1.076 (Barra-clean) 但 incr_ic=-0.050 (库 reducer) + cum_dd=-105 → reject
- [[batches/batch_017/candidates/C002|batch_017 C002]]: 20d signed body → ic=-0.042 ls_t=-2.62 r²=0.638 (vol-coupled) → reject
**Conclusion**: 5d signed body Barra-clean 但与库 F003 反向冲突；20d 加深 vol_20d 耦合。Hypothesis 部分成立——5d 保留 idiosyncratic 信号但与现库不正交。

### T002: Sign-of-body 频率信号 [◉ ACTIVE]
**Question**: 多日内 close>open 的频率（bullish bar count）是否 forward-predictive？
**Evidence trail**:
- [[batches/batch_017/candidates/C003|batch_017 C003]]: 5d Mean(Sign(close-open)) → ic=-0.033 ls_t=-3.55 mono=-0.80 alpha_surv=1.014 incr_ic=-0.031 → **reserve** (CP02-04 完美但 incr_ic 负)
**Next probes**: C003 与 C005 admit symmetric——下批做 C005-C003 对称信号或 spread

### T003: Close-vs-high 强度 + 多端点 OHLC aggregation [✓ ANSWERED batch_017+018]
**Question**: 5d mean(close/high) 测度 intraday close strength；持续 close 接近 high 是 sustained demand，是否 forward-predictive？扩展：open/range/body 各端点是否独立？
**Evidence trail**:
- [[batches/batch_017/candidates/C004|batch_017 C004]]: Mean(close/high, 5) → ic=+0.052 mono=+0.9 但 alpha_surv=0.003 catastrophic + ls_t=1.91<2 → reject (vol_20d 衍生)
- [[batches/batch_017/candidates/C005|batch_017 C005]]: Mean(upper-shadow, 5) → ic=+0.024 ls_t=3.20 mono=+0.90 alpha_surv=1.508 incr_ic=+0.031 cum_dd=-3.5 → **admit → upper_shadow_persistence_5d (F006)**
- [[batches/batch_018/candidates/C001|batch_018 C001]]: Mean(lower-shadow, 5) → near_dup F006 corr=1.000 (algebraic mirror) → reject
- [[batches/batch_018/candidates/C002|batch_018 C002]]: Mean(|body|/range, 5) → ic_oos_too_low (magnitude-only fails) → reject
- [[batches/batch_018/candidates/C003|batch_018 C003]]: Mean((open-low)/range, 5) → ic=+0.037 ls_t=3.22 mono=+0.90 alpha_surv=0.637 incr_ic=+0.023 cum_dd=-1.5 → **admit → open_position_persistence_5d (F007)**
- [[batches/batch_018/candidates/C004|batch_018 C004]]: Mean(signed_range, 5) → max_corr=0.544@F006 + incr_ic=-0.039 + cum_dd=-103 → reject
- [[batches/batch_018/candidates/C005|batch_018 C005]]: Mean(|gap|/range, 5) → alpha_surv=0.164 catastrophic → reject
- [[batches/batch_020/candidates/C001|batch_020 C001]]: Mean(upper-shadow, 3) → ic=+0.029 ls_t=2.91 mono=+0.90 alpha_surv=1.268 incr_ic=+0.022 max_corr=0.758@F006 → **admit → upper_shadow_persistence_3d (F008)** (high-corr admit 先例)
- [[batches/batch_020/candidates/C002|batch_020 C002]]: Mean(upper-shadow, 10) → mono_sign_flip IS=-0.60 OOS=+0.90 → reject (10d 跨 phase 反转，确认 5d sweet spot 上界)
- [[batches/batch_021/candidates/C001|batch_021 C001]]: Mean(open-position, 3) → mono_sign_flip IS=-1.00 OOS=+0.90 → reject (open-position 在 3d 完全反转 — F007 是 5d-only stable signal，与 upper-shadow multi-window 不对称)
- [[batches/batch_021/candidates/C002|batch_021 C002]]: Mean(upper-shadow, 7) → ic=+0.017 ls_t=2.33 mono=+0.90 alpha_surv=1.685 corr=0.834@F006 incr=+0.014 → **reserve** (rubric 形式允许 admit 但库 bloat 风险，7d 与 F006 5d + F008 3d 形成 3-window upper-shadow family 占库 30%)
- [[batches/batch_021/candidates/C003|batch_021 C003]]: turnover-weighted body sign 5d → corr=0.579@F007 + incr=-0.032 + mono=-0.30 → reject
**Conclusion**: OHLC aggregation 至少 3 个独立 admit——close 端 5d (F006) + open 端 5d (F007) + close 端 3d phase variant (F008)。Window range：upper-shadow 在 [3d, 7d] 都稳；open-position 仅 5d-only（**信号家族 multi-window 不对称**）；10d 反转。Magnitude-only / discrete count / turnover-weighting / Donchian 全部 fail。**方向 saturated** — admit 率从 25%→14%，剩余探索 ROI 低。

## Known Failures
- C001 (batch_017): 5d signed body — incr_ic=-0.050 库 reducer + cum_dd=-105 整库最深
- C002 (batch_017): 20d signed body — style_r²=0.638 poor + incr_ic=-0.039
- C004 (batch_017): 5d close/high — alpha_surv=0.003 catastrophic (vol_20d derivative) + ls_t=1.91 weak
- C001 (batch_018): 5d lower-shadow — corr=1.000 with F006 (algebraic mirror trap)
- C002 (batch_018): 5d body magnitude — ic=0.0067<0.008 (magnitude-only no signal)
- C004 (batch_018): 5d signed range — corr=0.544@F006 + incr_ic=-0.039 + cum_dd=-103
- C005 (batch_018): 5d gap-magnitude/range — alpha_surv=0.164 catastrophic (third vol-derived pattern)
- C001 (batch_021): 3d open-position — mono_sign_flip IS=-1.00 OOS=+0.90 (open-position is 5d-only stable signal)
- C003 (batch_021): turnover-weighted body sign 5d — corr=0.579@F007 + incr=-0.032 + mono=-0.30 (turnover ≠ new axis)
- C001 (batch_019): 5d range expansion ratio — mono=-0.30 + ls_t=-0.89 (rank 噪声)
- C002 (batch_019): 5d range/amount — corr=0.746@F002 + r²=0.348 (amount-dominated cluster)
- C003 (batch_019): 5d volume-weighted body — corr=0.721@F007 (F007 mirror)
- C004 (batch_019): 5d count close-near-high — hard_gate sign_flip (discretization failure)

## Related
- [[lessons#Structural Constraints]]
- [[intraday_price_formation]]  （saturated；单日 body/shadow 已穷尽）
- [[return_distribution_signals]]  （dead；同样 vol_20d 主导）

## Narrative Log
### 2026-04-21 [[batches/batch_017/judge|batch_017]]
**admit=1 / reserve=1 / reject=3 — direction status: exploring → productive (首 admit)**

**4 轮 0-admit 之后的关键突破**：
- **C005 admit → upper_shadow_persistence_5d**：5d mean upper-shadow ratio (high-close)/(high-low)。alpha_surv=1.508 (residual stronger than raw)、incr_ic=+0.031 库 adder、cum_dd=-3.5（库内最浅）、9 年 IC 全正。机制：持续 close 远低 day-high = 持续抛压 → 反转上涨。
- **C003 reserve**：5d sign-of-body frequency。CP02-04 perfect (alpha_surv=1.014, mono=-0.80)，但 incr_ic=-0.031 库 reducer。与 C005 镜像。
- **C001/C002 reject**：signed body 5d/20d，longer window 加深 vol_20d 耦合（r² 0.234→0.638）；5d Barra-clean 但 incr_ic 负。
- **C004 reject**：close/high 5d，alpha_surv=0.003 catastrophic 暴露其本质 ≡ vol_20d monotone derivative。

**核心元发现（系统层级）**：
1. **alpha_survival 是新关键判别量**：4 轮以来 18 个 reject 中部分被错过的"vol_20d 衍生" pattern 在本批通过 C004 vs C005 对照得到清晰区分——alpha_surv > 1.0 = "Barra 空间独立载体"，<< 0.40 = "vol 衍生"。**C005 admit 的核心证据是 alpha_survival=1.508，不是 ls_t/mono 单独**。
2. **5d aggregation 是 sweet spot**：单日 (intraday_price_formation 全 saturated) 与 20d (vol-coupled) 之间的 5d 窗口是 OHLC 信号的 sweet spot——既保留 idiosyncratic flow 又过滤噪声。
3. **upper-shadow 机制独立性**：C005 max_corr=0.069 with F003 (overnight gap)——OHLC 空间内 intraday-shadow 与 overnight-gap 完全机制正交。

**Direction operations**：
- status `exploring → productive`（首 admit）
- priority `medium → high`（productive 方向应提升优先级）

**下一步（batch_018）**：
1. 同方向 deepen — 5d 窗口的 OHLC pattern 变体：lower-shadow、body-position-in-range、signed body × range、跨日 body 一致性
2. C005 + C003 symmetric pair design — 5d frequency-asymmetry 信号
3. **观察**: 该方向是否能持续产 admit （alpha_surv > 1 + incr_ic > 0 是关键指标）

### 2026-04-21 [[batches/batch_018/judge|batch_018]]
**admit=1 / reserve=0 / reject=4 — 方向连续两批 admit (F006+F007)**

- **C003 admit → open_position_persistence_5d (F007)**: ic=+0.037 ls_t=3.22 mono=+0.90 alpha_surv=0.637 incr_ic=+0.023 cum_dd=-1.5。机制：5d mean(open-low)/(high-low) 测度持续开盘位置；持续高开 = 隔夜信息驱动 momentum continuation。与 F006 max_corr=0.276 完全机制正交。
- **C001 reject (algebraic mirror)**: lower-shadow corr=1.000 with F006 — OHLC 三段约束 trap。
- **C002 reject (magnitude-only)**: |body|/range ic=0.0067<0.008 — 无符号失去方向性。
- **C004 reject (interaction trap)**: signed-range corr=0.544@F006 + incr_ic=-0.039 — sign×magnitude 不构新维度。
- **C005 reject (vol-derived again)**: |gap|/range alpha_surv=0.164 — 第 3 个被识别的 vol_20d 镜像。

**方向核心结论**：OHLC 5d aggregation 至少 2 个独立维度（close-strength F006 + open-position F007），max_corr=0.276 远低 0.30 阈值。**预期还有 1-2 个独立维度可探**：body-position（close vs midpoint）、3d/10d 窗口 ablation。

**下一步（batch_019）**：
1. 第三轮 ohlc_temporal_aggregation：探索剩余维度 (close-vs-midpoint, body asymmetry, 3d/10d ablation)
2. 若 0 admit → 方向接近 saturated；若再 1 admit → 5d OHLC 至少 3 维独立

### 2026-04-21 [[batches/batch_019/judge|batch_019]]
**admit=0 / reserve=0 / reject=4 — 方向第 3 轮 0 admit 接近 saturated**

- C001 (range expansion): mono=-0.30 + ls_t=-0.89 → rank 失败
- C002 (range/amount): max_corr=0.746@F002 + r²=0.348 → 落入 F002 cluster
- C003 (volume × body): max_corr=0.721@F007 → F007 mirror
- C004 (discrete count): hard_gate sign_flip → 离散化丢失 magnitude

**饱和判断**：方向 admit 率 22% (2/9 candidates)，但本批 4/4 reject + 库 corr 与新 admits 重叠 → **5d directional ratio 空间被 F006/F007 饱和**。

**Known Failures 追加**:
- C001 (batch_019): 5d range expansion — mono=-0.30 + ls_t=-0.89 (range 演化噪声)
- C002 (batch_019): 5d range/amount — corr=0.746@F002 (落入 amount-dominated cluster)
- C003 (batch_019): 5d volume-weighted body — corr=0.721@F007 (F007 mirror)
- C004 (batch_019): 5d count of close-near-high — hard_gate sign_flip (离散化失败)

**下一步（batch_020）**：
1. 跨日 pattern：3d 内 high 上升 + 5d body sign 一致性 (engulfing-like)
2. window ablation：3d/10d upper-shadow 验证 5d 是 sweet spot
3. 若 batch_020 仍 0 admit → status `productive → saturated`

### 2026-04-21 [[batches/batch_021/judge|batch_021]]
**admit=0 / reserve=1 / reject=2 — direction status: productive → saturated**

- C001 reject: 3d open-position F007 ablation hard_gate mono_sign_flip IS=-1.00 OOS=+0.90。F007 是 5d-only stable signal。
- C002 reserve: 7d upper-shadow alpha_surv=1.685 极 clean 但 corr=0.834@F006 high → 库 bloat。
- C003 reject: turnover-weighted body sign 5d → corr=0.579@F007 + incr_ic=-0.032 + mono=-0.30。turnover ≠ 新 axis。

Direction status `productive → saturated`。累计 admit 率 14% (3/21)。下批触发 Phase 5 consolidation，再开新方向。
