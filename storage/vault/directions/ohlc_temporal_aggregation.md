---
direction_tag: ohlc_temporal_aggregation
status: productive
priority: medium
rounds: 8
admits: 5
last_batch: batch_063
last_admits: []
last_goal: T012 higher-moment OHLC × non-vol-cluster RHS 第二轮——延伸 F019 (Std body_ratio,20
  × price_vol_60) 的复活路径，测 4 个 NEW OHLC 原子 (close_position / range_norm_prev_close
  / O-C / open_position) 的 higher-moment LHS × 4 个非 dead-endpoint RHS (turnover_60
  / pe_60 / pb_60 amount_60)。所有 LHS scale-free + 单层 moment + 窗口 ≤20d 满足 P003 atom-orthogonality
  三件套；严避 F006/F007/F019 anchor cluster；不嵌套 compound moment；不踩 dead RHS endpoints (overnight_5/turnover_5/amount_20/body_ratio_20/price_vol_20/circ_mktcap_60)。目标：≥1
  admit 兑现 max_corr<0.70 + alpha_surv≥0.30 + ls_t>2 + incr_ic≥0.015 (rank-diff borderline
  死区)。
last_activity: '2026-04-28T08:45:20Z'
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

1. **alpha_survival 是 vol_20d 衍生判别量**：>1.0 = Barra 空间独立载体；<<0.40 = vol 衍生（Mean-base）。**例外**：rank-diff geometry 因 CsRank Sub 必然部分映射到 cross-sectional dispersion，alpha_surv 0.30-0.40 区间是真实信号 + 必然 style coupling，不是 alpha 弱（F019 admit alpha_surv=0.21 仍 admit 即此机制；config 已 codify `alpha_surv_min.rank_diff=0.30`，见 [[_consolidation/findings/calibration/001]]）。
2. **5d 是 Mean-base OHLC aggregation sweet spot**：单日（intraday saturated）与 20d（vol-coupled）之间。但 **higher-moment 突破 sweet spot 约束**：Std(body_ratio,**20**d) 反而成为独立轴（窗口约束随 moment 阶数变化）。
3. **信号家族 multi-window 不对称**：upper-shadow [3d, 7d] 稳；open-position 严格 5d-only（3d mono_sign_flip IS=-1.00 OOS=+0.90）；≥10d Mean-base 跨 phase 反转。
4. **OHLC 三段约束 → algebraic mirror trap**：lower-shadow ≡ -upper-shadow（corr=1.000@F006），signed-range 与 F006 高 corr；三段 ratio 任意两端代数互补。
5. **Magnitude-only / turnover-wt / discrete count 全部失败**（Mean-base 维度）：signed 方向性是 OHLC Mean 信号必要条件，turnover 不构成独立 OHLC 轴。
6. **rank-diff × OHLC 兑现两条件**（F019 提取，[[_consolidation/findings/hypothesis_promoter/006]] 升格）：(a) higher-moment LHS（Std/Skew/Kurt vs 库内全 Mean-base, 完全独立轴）+ (b) RHS 跳出 turnover/amount/overnight cluster（price_vol 是新 basis）。两条件单独均不足，叠加才 max_corr<0.30。
7. **sign aggregation 不可盲目跨字段泛化**（T011 [✗]）：alpha 来自 underlying field 的 persistent drift，非 Sign() 操作几何性质。overnight 有 institutional accumulation drift（F018），intraday body 是 random walk（b017 C003 / b050 C006 双例 reject）。Phase 1 设计 sign 候选必须先核 underlying drift。
8. **rank-diff geometry 7 条硬约束（系统级，[[_consolidation/findings/pattern_analyst/002]]）**：(1) 两端 scale-invariance；(2) raw field 独立；(3) 同字段跨窗口禁止；(4) Sub 方向对偶 dedup；(5) 同批 LHS 共享 anchor rule；(6) RHS 共振饱和（dead endpoints 动态：overnight_5/turnover_5/amount_20/body_ratio_20/price_vol_20）；(7) factor-anchored cluster（saturated 方向 anchor 消化新候选）。本方向 b050 C001-C004 reject 全验证。
9. **incr_ic borderline 死区律（[[_consolidation/findings/calibration/004]]）**：max_corr ∈ [0.30, 0.70] 时 incr_ic 必须 ≥ 0.015 才 admit-eligible；本方向 b050 C001 (incr=0.013, max_corr=0.50) 即在死区。设计期 self-prune 0.008-0.013 incr_ic 候选。

---

## Threads

### T012: higher-moment OHLC 维度 [◉ ACTIVE]

> [!note]+ Thread 当前
> **Question**: Std/Skew/Kurt of OHLC ratios 是否构成与 Mean-based 库因子独立的轴？哪些 atomic OHLC × moment 组合产生 alpha？
> **Evidence trail**:
> - b050 C001 (Mean of body_ratio) vs C005 (Std of body_ratio) → max_corr 0.50 vs 0.27 完全不同 corr structure → **不同 moment 是独立设计轴**
> - b050 C005 → admit F019 (Std body_ratio,20 × price_vol_60) → first higher-moment OHLC admit
> - 跨 family 复现：[[gap_acceptance_structure]] F020 = Std(gap_ret,20) × body_ratio_20 同律
> - **b063 C001-C006 6/6 reject** → atom-orthogonality 三件套精细化为**六件**：(a) atom multi-regime stable + (b) **atom 与 vol_20d 几何正交** (排除 range/prev_close, signed return/prev_close 等 vol-direct-proxy 原子) + (c) normalizer 无 regime drift + (d) sign 信息保留 (F020 sign-preserved 兑现 vs b063 C006 sign-stripped 失败) + (e) **price normalizer 优于 range normalizer** (Ref(close,1) 跨 regime 稳 vs H-L drift) + (f) **避 OHLC algebraic mirror pair atom Std cluster** (b063 C001 close_position Std 与 F021 upper_shadow Std cluster=0.79)
> - **b063 vol_20d 整库新纪录连刷**: C003 style_r²=0.6991 vol_20d=76.53 (signed return Std), C002 vol_20d=53.04 (range Std) — atom 自身即 realized vol direct proxy
> - **b063 OHLC algebraic mirror higher-moment 形态首次实证**: lower_shadow ≡ -upper_shadow → Std-pair cross-section rank cluster
>
> **Answer (部分)**: F019/F020 兑现路径**不能简单泛化至任意 OHLC ratio Std**. 兑现条件六件全部满足才能进入 admit-eligible 候选空间. 当前唯二兑现 atom: F019 body_ratio (intraday H-L 短期稳 + sign-stripped 但 ratio scale-free) + F020 gap_ret (跨 session + Ref(close,1) normalizer + sign-preserved).
>
> **Next probes (剩余探索路径稀薄)**: (1) **F019/F020 atom 的 Skew/Kurt 形态** (从 2nd moment 升至 3rd moment, atom 仍 body_ratio 或 gap_ret); (2) F008 upper_shadow 3d phase 在 Skew 维度但需先核 F006/F021 cluster — 估总剩余 candidate ≤2-3. **direction MT 34/70 approaching exhaustion** (从 28/70 → 34/70, +6 本批), **下批应切方向**.
>
> **禁忌 (本批新增)**：(a) range/prev_close, (C-O)/prev_close, |gap|/range, ratio-of-magnitudes 等 atom 是 vol_20d direct proxy 全部禁; (b) close_position, lower_shadow Std 与 upper_shadow Std OHLC mirror cluster, 不再设计同 mirror pair higher-moment 候选; (c) compound moment LHS (smooth-then-std b052 C006 教训) 持续禁; (d) 仍 dead RHS endpoints (overnight_5/turnover_5/amount_20/body_ratio_20/price_vol_20).

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
- **T010 rank-diff × OHLC family** [✓ ANSWERED batch_050]：兑现需 (a) higher-moment LHS + (b) RHS 跳出已饱和 cluster。F019 双新维度叠加 → max_corr=0.270 整库最干净 + 与 4 admitted rank-diff 全 <0.25。**rank-diff 范式第 5 次跨家族 tipping point 正式确认**（已升格 Lesson 6 + [[_consolidation/findings/hypothesis_promoter/006]]）。
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
| [[batches/batch_050/candidates/C004\|b050 C004]] | gap_to_range × pb_60 rank-diff | incr_ic=0.003 < 0.015 borderline 死区（[[_consolidation/findings/calibration/004]]）|
| [[batches/batch_050/candidates/C006\|b050 C006]] | body_sign × pb_20 rank-diff | hard_gate；intraday body sign random walk（b017 C003 教训复现）|
| [[batches/batch_063/candidates/C001\|b063 C001]] | Std(close_position,20) × turnover_60 | max_corr=0.79@F021 + incr_ic=-0.009 NEG（OHLC algebraic mirror higher-moment trap 首次实证）|
| [[batches/batch_063/candidates/C002\|b063 C002]] | Std(range/prev_close,20) × pe_60 | vol_20d=53.04 极端 + alpha_surv=0.39 + incr_ic=-0.009 NEG（atom 自身即 realized vol proxy）|
| [[batches/batch_063/candidates/C003\|b063 C003]] | Std((C-O)/prev_close,20) × pb_60 | vol_20d=76.53 整库新纪录 + ls_t=-1.14 weak（signed return / prev_close 直接 vol proxy）|
| [[batches/batch_063/candidates/C004\|b063 C004]] | Std(open_position,20) × amount_60 | max_corr=0.69@F012 + incr_ic=0.006<0.015 死区律（本批 strongest stat ls_t=4.89 仍阻断）|
| [[batches/batch_063/candidates/C005\|b063 C005]] | Std(upper_shadow,20) × pe_20 | hard_gate mono_sign_flip -0.90→+1.00（OHLC mirror trap 跨样本 reversal）|
| [[batches/batch_063/candidates/C006\|b063 C006]] | Std(\|gap\|/range,20) × amount_60 | alpha_surv=0.09 critical + range normalizer drift（双 normalizer regime drift）|

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

> [!quote]+ 2026-04-28 · [[batches/batch_063/judge|batch_063]] · admit=0 / reserve=0 / reject=6
> T012 第二轮 — **higher-moment OHLC × non-vol-cluster RHS 全 6 candidate reject + atom-orthogonality 三件套精细化为六件**. 6 candidate 跨四类 OHLC 三段 ratio 原子 (close_position / range_norm_prev_close / (C-O)/prev_close / open_position / upper_shadow / |gap|/range) 揭示 F019/F020 兑现路径**不能简单泛化**. 关键 finding:
> 1. **vol_20d structural absorption 整库新纪录连刷** (C003 style_r²=0.6991 vol_20d=76.53 / C002 vol_20d=53.04) — atom 自身即 realized vol direct proxy 时 Std 二阶聚合放大该 proxy → P003 vol_20d 边界律持续 escalate. ohlc_temporal_aggregation 方向首次直接命中 vol_20d 极端吸收 (跨 family 9-direction-confirmed → 第 10).
> 2. **OHLC algebraic mirror trap higher-moment 形态首次实证** (C001 close_position Std × turnover_60 与 F021 upper_shadow Std × range_60 cluster=0.79) — lessons.md OHLC Family Defaults 段 algebraic 检查升格新增第四件: Std/Var/Skew/Kurt of mirror-pair ratios cluster.
> 3. **rank-diff borderline 死区律第三次实证 (C004)** — max_corr=0.6873@F012 + incr_ic=0.0062<0.015 双重 gate 不达, 阻断本批 strongest stat profile (ls_t=4.89 + ls_sharpe=3.52 + 9/9 yr 全正). **alpha quality ≠ tradable independence 律重申**: 单维度 cleanness 强不充分 (与 b062 C005 同律).
> 4. **higher-moment LHS atom-orthogonality 三件套精细化为六件** — (a) atom multi-regime stable; (b) **atom 与 vol_20d 几何正交** (排除 vol-direct-proxy atom); (c) normalizer 无 regime drift; (d) **sign 保留** (F020 ✓ vs b063 C006 sign-stripped ✗); (e) **price normalizer 优于 range normalizer** (Ref(close,1) 跨 regime 稳 vs H-L drift); (f) **避 OHLC mirror pair atom Std cluster**.
>
> **MT budget**: cumulative 336→**342** · direction 28→**34** approaching exhaustion · bucket high (search_adjusted ≈ 0.49 medium). **zero_admit_streak 3→4** (b060/b061/b062/b063 四批连续). **calibration_trigger=false** (4 批 zero admit 满足 ≥3 但累计 reserve=1 仍 < 稳健 ≥2 阈值). 升格量已累 11 条 (本批 4 + b062 4 + b061 3) → consolidation 升格紧迫性高于 rounds 阈值.
>
> **Operations**　`status: productive (维持 T012 仍 ACTIVE 但范围窄)` · priority `medium → low` (剩余 candidate 空间稀薄 ≤2-3, 让位给其他 direction).

> [!quote]- 2026-04-25 · [[batches/batch_050/judge|batch_050]] · admit=1 / reserve=1 / reject=4
> (折叠) direction `saturated → productive` (4 batch 0-admit 后突破)。C005 admit F019 `body_disp_pricevol_rank_diff_20`：LHS=Std(body_ratio,20) higher moment + RHS=Mean(Std($close,5),20) price_vol——hypothesis 复活条件 (a)+(c) 兑现 + max_corr=0.270 整批整库最干净 + incr_ic=0.020。**rank-diff 范式第 5 次跨家族 tipping point 正式确认** (跨 microstructure/overnight/OHLC 4 family 5 admit)，触发 Phase 5 consolidation。C001 reserve (alpha_surv=0.33 + max_corr=0.50 + incr_ic=0.013 borderline 死区)。4 reject 验证 7 硬约束：C002 RHS cluster + vol_20d=53；C003 intraday return random walk；C004 incr_ic 死区；C006 intraday body sign random walk (b017 C003 教训复现)。

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
