---
direction_tag: tsrank_diff_form
status: saturated
priority: medium
rounds: 2
admits: 0
last_batch: batch_102
last_admits: []
last_goal: "Round 102 NEW direction — library_gap finding 024 落地, 整库 9 admit CsRank-diff\n\
  (F015-F023) + 3 admit TsRank-single (F024/F025/F026) + 0 admit TsRank-diff. b096\
  \ 实测\nTsRank-diff vs CsRank-diff (F018) max_corr 0.14-0.19 几何独立 → 跨字段 TsRank-diff\n\
  是结构性未测 axis.\n\n**核心 hypothesis**: Sub(TsRank(X,N), TsRank(Y,N)) 跨字段 同窗 TsRank-diff\
  \ 应 escape\nT006 self-cancellation 律 (T006 仅约束同字段不同窗 b094/C001 dead), 测量\n\"哪个流量场更接近自身历史峰值\"\
  \ 的截面排序差异.\n\n**6 候选覆盖 (3 sub-thread, 6 sub-axis)**:\n- **T001 流量场跨字段 TsRank-diff\
  \ 同窗 (3 candidates)**:\n  C001 Sub(TsRank($amount,60), TsRank($num_trades,60)) —\
  \ 名义流量 vs 参与笔数\n  C002 Sub(TsRank($num_trades,60), TsRank($turnover_rate,60)) —\
  \ 笔数 vs 内生周转\n  C003 Sub(TsRank($amount,60), TsRank($turnover_rate,60)) — 名义流量 vs\
  \ 内生周转\n- **T002 几何字段 TsRank-diff (2 candidates)**:\n  C004 Sub(TsRank($close,60),\
  \ TsRank($volume,60)) — 价/量分位差\n  C005 Sub(TsRank(Sub($close,$open),60), TsRank(Sub($high,$low),60))\
  \ — body vs range\n- **T003 intraday vs overnight TsRank-diff (1 candidate)**:\n\
  \  C006 Sub(TsRank(Div(Sub($close,$open),Ref($close,1)),60), TsRank(Div(Sub($open,Ref($close,1)),Ref($close,1)),60))\n\
  \n**Self-check 5 hard rule**:\n- **T006 (cross-window cancellation)**: 全部 6 候选 LHS≠RHS\
  \ 字段, 同窗 (N=60 for both legs)\n  → escape T006 (T006 律仅约束同字段跨窗). 不重测 b094/b092 已\
  \ dead 子空间.\n- **P030 (alpha_surv>1.0 paradox)**: 全 6 multi-CP rationale, 不单 alpha_surv\
  \ 依赖\n- **P032 (Rank-Diff 第 8 cross-domain)**: 该律源自 CsRank-diff 实证 (b100/b094),\n\
  \  适用于 cross-section domain; **TsRank-diff 是时序 rank-diff, 不同 domain**,\n  本批显式标\
  \ \"P032 律待验证\" — 若 b102 全 dead, 则 P032 可扩展至 TsRank-diff;\n  若 b102 有 admit, 证明\
  \ P032 不适用于 time-series rank-diff.\n- **P033 (OOS sign-flip)**: 配置 sample_policy\
  \ train≤2021/val 2022-2023/holdout 2024+,\n  Phase 3 judge 必查 sign_consistency.\n\
  - **P004-deep (path-integral)**: TsRank 内嵌 60d 历史是 cumulative ordinal operation,\n\
  \  但跨字段 diff 不构成 path-integral 累积 (两 leg 各自 ordinal, 不叠加). 风险中等.\n\n**Anchor avoidance\
  \ (库内 12 rank-form factors)**:\n- F015-F023 (9 CsRank-diff): 全用 CsRank 不是 TsRank,\
  \ b096 实测 max_corr 0.14-0.19\n  cross-section vs time-series domain 不同\n- F024 (TsRank($num_trades/$volume,60)):\
  \ C001-C003 全部用 raw flow fields 非\n  ratio field, 几何 distinct; C004 用 $volume single-leg\
  \ 但与 F024 ratio 形式不同\n- F025 (TsRank(shadow_asymmetry,60)): 本批无 shadow geometry,\
  \ distinct\n- F026 (TsRank(close-position,60)): C004 用 $close raw 不是 close-position\
  \ ratio,\n  distinct\n\n**Baseline-first 守则 explicit skip**: 15 untouched TTM 字段\
  \ (财务比率) quarterly\n更新, TsRank 60d 内嵌历史 dim 不支持 quarterly granularity. 显式 skip baseline-first.\n\
  \n**avoid-this-batch**: NO same-field cross-window TsRank-diff (T006 dead 域),\n\
  NO CsRank-anywhere (与 F015-F023 同构), NO ratio-as-leg (与 F024 F026 同构),\nNO Mean/EMA\
  \ wrap (Phase 1 不需要 smoothing — 测试 raw form 的 ls_t 上限).\n\nTarget: ≥1 admit (ls_t\
  \ ≥ 3.0 + max_corr<0.40 + alpha_surv≥0.5 + incr_ic≥0.005)\nOR ≥2 candidates validated\
  \ borderline (alpha_surv≥0.5 + ls_t>2.0) 确认 TsRank-diff\ncross-field 是 productive\
  \ axis. 若 0 admit + 多数候选 ls_t<2.0 / vol_20d_exp>20,\n则 TsRank-diff form 全空间证伪, P032\
  \ 律扩展至 time-series rank-diff."
last_activity: '2026-05-16T08:08:20Z'
created_batch: batch_102
members: []
retired_members: []
reserves:
- b102_C003
- b102_C006
merged_into: null
created_from: library_gap_finding_024_cross_field_TsRank_diff_unexplored
---
# tsrank_diff_form

> [!abstract]+ 方向概要
> - **状态**　🟠 `saturated` (b102 后定格) · priority `medium` · rounds = 1 · admits = 0 · reserves 累计 2
> - **一句话**　`Sub(TsRank(X,N), TsRank(Y,N))` **跨字段 TsRank-diff** 经 b102 实测: 3/6 max_corr ≥ 0.45 with library family-anchors (F003/F024/F026), incr_ic 倾向 negative, **TsRank-diff 不构成新几何空间, 是 raw alpha 的 ordinal rotation 或 cross-section dispersion-ceiling-limited 信号**. C006 (intraday/overnight) CP03 strong 全 3/3 + 9 年 robust 但 max_corr=-0.694 with F003 + incr_ic=-0.006 → reserve; C003 (amount/turnover) mono perfect + 库独立但 ls_t=-1.67 < admit floor → reserve.
> - **来源**　library_gap finding 024 (medium severity, suggested_new_direction).

---

## Hypothesis

**核心 hypothesis**: `Sub(TsRank(X, N), TsRank(Y, N))` 跨字段 TsRank-diff 应 escape T006 self-cancellation 律 (T006 仅约束同字段不同窗), 测量 "哪个流量场更接近自身历史峰值" 的截面排序差异.

**axis 律 (b102 升格)**:

> **跨字段 TsRank-diff family-anchor collapse 律**: `Sub(TsRank(X,N), TsRank(Y,N))` 在 X/Y 来自 same library family (e.g. both flow fields, both return components) 时, cross-section corr ≥ 0.45 with library nearest, incr_ic 倾向 negative. **TsRank-diff 不构成新几何空间, 仅 ordinal rotation**. 例外: X/Y dim-mismatch (size-coupled vs scale-free, 如 C003 $amount vs $turnover_rate) 可达 max_corr<0.30 库独立, 但 cross-section dispersion 上限同 [[rank_diff_liquidity_microstructure#ls_t-上限律 ⚠️ (b096-升格)|rank_diff_liquidity_microstructure]] (ls_t ∈ [-1.67, -2.60]).

**axis 律 (b102 升格 — sign-instability)**:

> **a 股 9 年 TsRank-diff cross-period drift 律 (P033 sub-case)**: 跨字段 raw flow field TsRank-diff (C001/C002 实证) 在 a 股 2015-2023 sample 上 ic_by_year monotonic drift (e.g. C002 -0.038 → +0.020, sign flip 在 2018-2019). train≤2021 / val≥2022 split 把 "机制翻转点" 包在 train 内 → 强制 sign_flip hard_gate fail. 不可挽救 (不是 noise 而是 structural regime change).

**axis 律 (b102 升格 — vol_20d 共振)**:

> **几何字段 TsRank-diff vol_20d 共振律 (T002 disproven)**: $close/$volume/body/range raw field TsRank-diff (C004/C005 实证) dominant_style=vol_20d exposure ≥ 12, residual_ic sign 倾向反向 (P030 paradox 雏形). 几何字段在 TsRank 后 ordinal-normalize 信息密度过低, cross-section spread 由 vol_20d basis 主导.

**红线**:
- `|corr|>0.7` 至 library admit → near_dup reject
- `alpha_survival ≥ 0.40` + `max_corr<0.30` to library 为 admit floor
- `vol_20d_exp > 25%` AND `alpha_survival < 0.30` 三立 → reject

---

## Current Focus

**已 saturated** after b102. 不出新批次. 进入 stand-by 等待:
1. Python OLS cross-section residualize on F003 (复活 C006 路径); 或
2. /consolidate-calibration 流程对 reserve pool (C003 + C006 + 累计 7 from rank_diff_liquidity) 重评估
3. 若 (1)(2) 都不复活, 本方向终结, P032 律正式扩展至 TsRank-diff form

---

## Threads

### T001: 流量场跨字段 TsRank-diff 同窗 [✗ DISPROVEN batch_102]

> [!failure]+ Thread 结论
> **Question**: 跨字段 raw flow field TsRank-diff (X=$amount, $num_trades, $turnover_rate) 同窗 60d 是否构成独立 cross-section alpha?
>
> **Answer**: **2/3 hard_gate sign_flip dead** (C001 amount/num_trades + C002 num_trades/turnover — a 股 9 年 structural drift); **1/3 borderline reserve** (C003 amount/turnover — size-coupled vs scale-free dim mismatch 救下 mono perfect + 库独立 但 ls_t < admit floor).
>
> **Evidence trail**:
> - [[batches/batch_102/candidates/C001|batch_102 C001]] `Sub(TsRank($amount,60),TsRank($num_trades,60))` → train_ic=+0.002 vs val_ic=-0.030 sign_flip + oos_decay=-16.6 → **reject (hard_gate)**
> - [[batches/batch_102/candidates/C002|batch_102 C002]] `Sub(TsRank($num_trades,60),TsRank($turnover_rate,60))` → 9 年 ic_by_year monotonic drift -0.038 → +0.020 → **reject (hard_gate)**
> - [[batches/batch_102/candidates/C003|batch_102 C003]] `Sub(TsRank($amount,60),TsRank($turnover_rate,60))` → ic_oos=-0.015 mono_oos=-1.0 max_corr=0.26@F028 ls_t=-1.67 → **reserve (错杀件 4/4)**
>
> **Next probes**: C003 待 Python residualize 或 calibration 复活; T001 主体 disproven for same-family flow pair.

### T002: 几何字段 TsRank-diff [✗ DISPROVEN batch_102]

> [!failure]+ Thread 结论
> **Question**: 几何字段 ($close/$volume 价量; body/range candle geometry) raw TsRank-diff 同窗是否构成 cross-section spread?
>
> **Answer**: **完全 disproven**. C004 (close/volume) + C005 (body/range) 双 reject. P030 paradox + mono OOS collapse + dom_style=vol_20d 严重共振. TsRank ordinal-normalize 过 close/volume/body/range 后, 信息密度过低, cross-section spread 由 vol_20d basis 主导, 不形成独立 alpha.
>
> **Evidence trail**:
> - [[batches/batch_102/candidates/C004|batch_102 C004]] `Sub(TsRank($close,60),TsRank($volume,60))` → ls_t=-0.15 noise + alpha_surv=4.29 P030 paradox + mono OOS 1.0→-0.10 collapse → **reject**
> - [[batches/batch_102/candidates/C005|batch_102 C005]] `Sub(TsRank(close-open,60),TsRank(high-low,60))` → ls_t=0.10 noise + mono OOS 50% collapse + vol_20d exposure 15.71 + residual sign flip → **reject**
>
> **Next probes**: 不再测 几何 raw TsRank-diff; T002 关闭.

### T003: intraday vs overnight TsRank-diff [◉ ACTIVE]

> [!note]+ Thread 当前
> **Question**: return decomposition component (intraday body vs overnight gap) 60d TsRank-diff 是否构成新的 alpha 空间?
>
> **Evidence trail**:
> - [[batches/batch_102/candidates/C006|batch_102 C006]] `Sub(TsRank(close-open,60),TsRank(open-ref(close,1),60))` → ic_oos=-0.027 ls_t=-3.69 mono=-0.9 alpha_surv=1.27 max_corr=**-0.694**@F003 incr_ic=**-0.006** → **reserve**
>
> **Finding**: CP03 strong 全 3/3 + 9 年 sign-consistent — **真实 alpha 存在**, 但 cross-section corr=-0.694 与 F003 (overnight_gap_normalized) → C006 ≈ raw F003 的 ordinal rotation, incr_ic 负 = 库已含该 alpha 空间. **TsRank-diff 没有创造新空间, 仅 form rotation**.
>
> **Next probes**:
> - Python OLS residualize C006 on F003 — 看 residual ls_t 是否仍 > 2.0
> - 或 F003 retire 后用 C006 替代 (TsRank-diff form 可能比 raw overnight gap 更稳定 + 更 clean style_r²=0.042)

---

## Known Failures

| Candidate | Expression | Reject Reason |
|---|---|---|
| [[batches/batch_102/candidates/C001\|b102/C001]] | `Sub(TsRank($amount,60),TsRank($num_trades,60))` | hard_gate: sign_flip train +0.002 vs val -0.030 + oos_decay=-16.6 (a 股 9 年 cross-period drift) |
| [[batches/batch_102/candidates/C002\|b102/C002]] | `Sub(TsRank($num_trades,60),TsRank($turnover_rate,60))` | hard_gate: sign_flip train -0.009 vs val +0.022 + oos_decay=-2.34 + ic_by_year 9 年 monotonic drift |
| [[batches/batch_102/candidates/C004\|b102/C004]] | `Sub(TsRank($close,60),TsRank($volume,60))` | CP03 weak (ls_t=-0.15) + CP04 P030 paradox (alpha_surv=4.29) + mono OOS 1.0→-0.10 collapse + vol_20d exposure 12.26 |
| [[batches/batch_102/candidates/C005\|b102/C005]] | `Sub(TsRank(close-open,60),TsRank(high-low,60))` | CP03 weak (ls_t=0.10 noise) + mono OOS 50% collapse + Q5 reversal + vol_20d exposure 15.71 (本批最高) + residual sign flip |

## Reserve Pool (2 候选)

| Candidate | Expression | ls_t | alpha_surv | max_corr | incr_ic | 错杀件 |
|---|---|---|---|---|---|---|
| [[batches/batch_102/candidates/C003\|b102/C003]] | `Sub(TsRank($amount,60),TsRank($turnover_rate,60))` | -1.67 | 0.80 | 0.26@F028 | 0.004 | **4/4** |
| [[batches/batch_102/candidates/C006\|b102/C006]] | `Sub(TsRank(close-open,60),TsRank(open-ref(close,1),60))` | **-3.69** | 1.27 | -0.694@F003 | **-0.006** | 2/4 (max_corr/incr_ic 失败) |

**reserve pool 最强 admit 候选**: C006 (CP03 strong 全 3/3, 9 年 robust, style_r²=0.042 最 clean) 但 incr_ic 负是决定性 blocker; C003 (库独立 + mono perfect) 但 ls_t magnitude 不足.

---

## Related

- 🟠 [[rank_diff_liquidity_microstructure]] `saturated` —— TsRank-diff (同字段跨窗) 已 dead; 本方向 (跨字段同窗) 经 b102 也 saturated, 共构 rank-diff form 全空间 exhausted
- 🥈 [[factors/F003|F003]] —— `overnight_gap_normalized`, C006 的 ordinal rotation source (corr=-0.694)
- 🥈 [[factors/F024|F024]] —— `TsRank($num_trades/$volume,60)`, C001/C002/C004 共享 num_trades/volume RHS leg (corr 0.32-0.69)
- 🥈 [[factors/F026|F026]] —— `TsRank(close-position,60)`, C005 共享 body/range geometry (corr=0.45)
- 🥇 [[factors/F018|F018]] —— `CsRank-diff overnight × amount`, b096 实证 TsRank-diff vs CsRank-diff 几何独立 — **本批 (b102) 部分挑战该结论**: 跨字段 raw atom TsRank-diff 反而与 raw alpha family 高同源
- 🥈 [[factors/F028|F028]] —— `DMI down-ratio 12d`, C003 nearest (corr=0.26 低)
- [[_consolidation/findings/library_gap/024|library_gap/024]] source finding
- [[lessons#Path Selection]] (T006 cross-window cancellation + P032 cross-domain rank-diff)
- [[lessons#Threshold Calibration]] (4-piece 错杀检测; C003 全中)

---

## Narrative Log

### 2026-05-16 [[batches/batch_102/judge|batch_102]]
**跨字段 TsRank-diff form 一批后 saturated** — admit=0 / reserve=2 (C003/C006) / reject=4

- **T001 (流量场跨字段)**: 2/3 hard_gate sign_flip dead (C001 amount/num_trades + C002 num_trades/turnover, **a 股 9 年 cross-period structural drift** 律); 1/3 reserve (C003 size-coupled vs scale-free pair 救下).
- **T002 (几何字段)**: 完全 disproven (C004 close/volume + C005 body/range — TsRank ordinal-normalize 后信息密度过低, vol_20d 主导).
- **T003 (intraday/overnight)**: 1 reserve (C006 — CP03 strong 全 3/3 + 9 年 robust, 但 max_corr=-0.694@F003 + incr_ic=-0.006 = 库已含信号; ordinal rotation 非新空间).

**核心方向级 finding**: **跨字段 TsRank-diff 不构成新几何空间**, 倾向坍缩到现有 raw alpha 的 ordinal rotation (T003 case) 或 cross-section dispersion-ceiling-limited 信号 (T001/T002 case). b096 "TsRank-diff vs CsRank-diff 几何独立" 结论 **仅适用于 CsRank-diff cluster 不延伸到 raw price/volume/overnight family**.

**P032 律升格 candidate**: `Sub(TsRank(X,N),TsRank(Y,N)) 在 X/Y 来自 same library family (both flow / both return component) 时, cross-section corr ≥ 0.45 with library nearest, incr_ic 倾向 negative — 整族 default reject`. 例外 `dim-mismatch pair (size-coupled vs scale-free)` 救下 库独立但 ls_t < admit floor.

**MT Budget**: cumulative 570 → **576** · direction 0 → **6** · bucket `medium` (search_adjusted 0.22-0.59).

**Calibration trigger 加强**: zero_admit_streak 3 → 4; C003 错杀件 4/4 全中; 累计 reserve 池 9 候选 (b102/C003 + b102/C006 + rank_diff_liquidity 7) 待 calibration triage.

**Operations**　`status: probing → saturated` (一批耗尽 form-space) · rounds 0→1 · reserves +2
**下一步**: (a) 不再下同形式新批; (b) **强烈建议 orchestrator dispatch /consolidate-calibration** 处理 reserve pool 整体复活; (c) Python OLS residualize template 开发 — 复活 C006 (on F003) + C003 (on F012+F024+vol_20d).
