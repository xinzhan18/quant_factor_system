---
batch_id: batch_098
direction: conditional_operator_truncation
judged_at: 2026-05-16T00:20:00Z
candidates:
  - {candidate_id: C001, verdict: reject}
  - {candidate_id: C002, verdict: reject}
  - {candidate_id: C003, verdict: reject}
  - {candidate_id: C004, verdict: admit, factor_name: weak_close_day_rate_20}
  - {candidate_id: C005, verdict: reject}
  - {candidate_id: C006, verdict: reject}
batch_summary: {total: 6, admit: 1, reserve: 0, reject: 5}
admit_count: 1
reject_count: 5
reserve_count: 0
candidate_count: 6
mt_bucket: high
---

# batch_098 Judge Summary

> [!abstract]+ batch_098 · [[directions/conditional_operator_truncation]] · 6 candidates
> ✅ **admit=1** (C004→F{next} `weak_close_day_rate_20`) · ⏸ **reserve=0** · ❌ **reject=5**
> **核心发现**: T008 弱端 close-position binarize (Lt(.,0.2)) 路径 alpha_survival=1.10 Barra-clean admit, ls_t=3.28 上探到 admit floor — 验证 round 9 升格律 "binarize content ⊥ Barra basis" 必要性 + 揭示 close-position 弱端/上半段在 Barra basis 同构性 sign-dependent (Lt 弱端 ⊥, Gt 上半段 //).
> **MT Budget**: cumulative 546 → **552** · direction 6 → **12** · bucket 全 high (search_adjusted 部分降至 medium/low) · 本批 low=2 (C001/C004 search_adjusted=low) / med=1 (C005) / high=3 (基础 bucket)

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | 🟡·🟡·🟡·🟡·🟡 | ic_oos=-0.012 ls_t=-2.85 alpha_surv=**0.50** vol_20d=16.2 max_corr=0.49@F022 incr_ic=-0.006 | close 上半段主导日 (Gt(.,0.5)) — alpha_surv 临界仅过 0.10 buffer, expected_sign 反向, mirror of b097/C001 但 Barra basis 同构性显著不同 | [[batches/batch_098/candidates/C001]] |
| C002 | ❌ reject | hard_gate | ic_oos_too_low: 0.0021 < 0.008 | small-body 主导日占比信号在 csi1000 daily 几乎平坦, candle geometry 内 body 维度 binarize 无效 | [[batches/batch_098/candidates/C002]] |
| C003 | ❌ reject | hard_gate ×3 | sign_flip + ic_oos_too_low + oos_decay_neg | 高阈 (0.8) 强收盘日 regime instability, 80% 阈值 binarize 在 vol_20d basis 共振更深, 不如 50% 阈值 robust | [[batches/batch_098/candidates/C003]] |
| C004 | ✅ admit | 🟢·🟡·🟡·🟡·🟡 | **ic_oos=+0.0095 ls_t=+3.28 alpha_surv=1.10** max_corr=0.32@F006 incr_ic=-0.002 | 20d 弱收盘日 (Lt(.,0.2)) — Barra-clean residual alpha + candle geometry distinct geometry; close-position 弱端 binarize ⊥ vol_20d basis 验证 | [[batches/batch_098/candidates/C004]] · [[factors/F029]] |
| C005 | ❌ reject | 🔴·🟡·🔴·🟡·🟢 | ic_oos=-0.041 alpha_surv=**0.030** vol_20d=**35.4** ic_by_year 单调强化 | T002 gap event rate 高阈 1.5% **比 b097/C002 (0.5%) 更恶化** alpha_survival (0.13→0.03), gap rate 路径在 conditional family 中**结构性 dead** | [[batches/batch_098/candidates/C005]] |
| C006 | ❌ reject | hard_gate ×2 | sign_flip + oos_decay_neg | 跨日 candle-pattern (反向 body sign) regime-dependent, 不构成 stable cross-section signal | [[batches/batch_098/candidates/C006]] |

**档位编码**: 🟢 最优档 · 🟡 次档 · 🟠 边际 · 🔴 阻断档.

## 跨候选对比

**Style 聚合**: 4/4 hard_gate pass 候选 dominant=vol_20d (C001/C004/C005/C006 即使 hard_gate fail 也 dom=vol_20d 隐含). vol_20d exposure 阶梯: **C004 23.90 (alpha_surv=1.10!) < C001 16.22 (alpha_surv=0.50) < C005 35.40 (alpha_surv=0.03)** — 关键发现: **alpha_survival 与 vol_20d_exp 不是单调反相关**, C004 vol_20d=23.9 比 C001 vol_20d=16.2 更高但 alpha_survival 反而高 (1.10 vs 0.50) → **vol_20d 共线 magnitude 不是 alpha_survival 的决定因素, binarize content 与 vol_20d basis 的 non-linear 频谱重叠才是**.

**相关度 cluster**: 4 hard_gate pass 候选 max_corr ∈ [0.32, 0.49], 全部 < 0.70 (无 near_duplicate). nearest 分布: F006 (上影 5d mean), F020 (gap-vol rank-diff), F022 (close-position dispersion). conditional truncation family 整体与现有 admit cluster 边缘 distinct.

**MT 预算推进**: cumulative 546 → 552; direction 6 → 12; bucket 全部 high (NEW direction 第二批, family 累积频次推高); search_adjusted 大部分降至 low/medium (本批 conditional truncation 几何在 family 内已被探索一轮, 累积 6 个 → 12 个候选).

**Binarize content ⊥ Barra basis 验证 (本批核心发现, 接续 b097)**:

| 候选 | binarize 内容 | 同构 Barra basis | alpha_surv | 结论 |
|---|---|---|---|---|
| **C004** | 弱收盘日 ((C-L)/(H-L) < 0.2) candle geometry | **无同构** ⊥ | **1.10** | **admit** Barra-clean distinct geometry |
| C001 | close 上半段 ((C-L)/(H-L) > 0.5) candle geometry | vol_20d 部分同构 | 0.50 | borderline reject, mirror of b097/C001 但 alpha_surv 显著低 |
| C002 | small-body 主导日 candle geometry | (信号过弱无法判断) | — | hard_gate fail |
| C003 | 强收盘日高阈 (0.8) candle geometry | vol_20d 同构 (高阈引入 vol regime sensitivity) | — | hard_gate sign_flip ×3 |
| C005 | gap-up 高阈 (1.5%) | **vol_20d 强同构** | **0.030** | reject (P004-deep T002 路径结构性 dead) |
| C006 | 跨日 candle-pattern (反向 body sign) | regime-dependent | — | hard_gate fail |

**结论升格 (round 9 → 升级)**: conditional truncation 路径下 binarize 内容与 Barra basis 同构性是 **sign-dependent + threshold-dependent**:
- **同 (C-L)/(H-L) 信号底层**, 弱端 binarize (Lt(.,0.2)) ⊥ vol_20d, 上半段 (Gt(.,0.5)) // vol_20d 部分, 高阈 (Gt(.,0.8)) // vol_20d 更深
- gap-event 路径无论阈值 (0.5% / 1.5%) 都 // vol_20d (T002 family dead)
- 跨日 candle-pattern 是 regime-dependent (T009 dead)
- single-day candle geometry (shadow / close-position 弱端) 才是真 ⊥ Barra basis 路径

## Thread 进展

> [!success]+ T008 [[directions/conditional_operator_truncation#T008]] — `[✓ VALIDATED batch_098]` (admit + dead high阈)
> 本批 C004 (弱收盘日 20d 占比, (C-L)/(H-L) < 0.2 rate) **admit**: alpha_survival=1.10 Barra-clean + ls_t=3.28 + max_corr=0.32. 同 thread C003 (强收盘日 80% 阈值) hard_gate fail 三 gate. T008 内**弱端 binarize 路径 productive**, 高阈强收盘 dead. 与 b097/C001 (上影主导日 reserve, 50% 阈值) 互补构成 "close-position 弱端 candle geometry" 子族.
>
> **Next probes**: (a) C004 + Std/Skew 包装 (volatility of rate); (b) 弱收盘日 + reversion gate 复合; (c) 60d 弱收盘日占比 (windowscan); (d) 其它 binarize 阈值 (Lt(.,0.3) / Lt(.,0.1)) 验证阈值敏感性.

> [!failure]+ T001 [[directions/conditional_operator_truncation#T001]] — `[mixed result batch_098]` (mirror reject)
> 本批 C001 (close 上半段主导日 50% 阈值) 是 b097/C001 (上影主导日 50% 阈值, reserve) 的 reciprocal mirror. C001 OOS sign 反 (-0.012) + alpha_survival=0.50 borderline + incremental_ic 负 → reject. **T001 reciprocal mirror 路径 dead**, 上影主导日原 reserve (b097/C001) 不构成 admit (ls_t=2.85 < 3.0 floor + alpha_survival 1.07 但 mirror not portable). **关键洞察**: T001 候选 (b097/C001 上影主导, b098/C001 close-上半段) 形式上是同信号 (C-L)/(H-L) 的不同二分, Barra basis 同构性显著不同, 不严格对偶.

> [!failure]+ T007 [[directions/conditional_operator_truncation#T007]] — `[✗ DISPROVEN batch_098]`
> 本批 C002 (small-body 主导日 |body|/range<0.3 rate) hard_gate ic_oos_too_low (0.0021 < 0.008). small-body candle geometry 在 csi1000 daily cross-section 信号几乎平坦, body 维度 binarize **结构性失败** — body 与 vol_20d 高度共线 (大 body=高 vol), binarize 后信号被吸收近零.

> [!failure]+ T002 [[directions/conditional_operator_truncation#T002]] — `[✗ DEFINITIVELY DISPROVEN batch_098]` (高阈版本)
> 本批 C005 (gap-up 高阈 1.5% 60d rate) alpha_survival=0.030 + vol_20d_exp=35.4 比 b097/C002 (0.5% 阈值, alpha_surv=0.13) **更恶化**. **T002 family 整体结构性 dead**, 任何 gap-threshold binarize + Mean aggregate 都 // vol_20d basis (overnight gap 自身是 daily vol marker).

> [!failure]+ T008 high阈 sub-thread — `[✗ DISPROVEN batch_098]`
> 本批 C003 (强收盘日 80% 阈值) hard_gate sign_flip ×3. **高阈 (0.8) close-position binarize regime instability** — 80% 阈值在涨停日 (close==high) 被强制拉满, 引入 trend/vol regime sensitivity. 50% 阈值 (b097/C001 上影主导日) 是 robust binarize 切分, 高阈不可推广.

> [!failure]+ T009 [[directions/conditional_operator_truncation#T009]] — `[✗ DISPROVEN batch_098]`
> 本批 C006 (跨日反向 body pattern 60d rate) hard_gate sign_flip + oos_decay. **跨日 candle-pattern 是 regime-dependent, 不构成 stable cross-section signal**. candle-pattern binarize 路径有效性**仅限单日内 geometry** (shadow, close-position), 跨日 pattern dead.

## 跨候选反思 (4 层)

### Layer 1: 本批最强结论 — T008 弱端 close-position binarize 路径 admit (库内第 2 个 conditional truncation rate alpha)

- **C004 admit** 是 conditional_operator_truncation direction 首个 admit (b097 0 admit, b098 1 admit), 累积 12 候选 1 admit (8% admit rate, 优于 dead-spiral 前期方向)
- alpha_survival=1.10 Barra-clean (与 b097/C001 reserve 上影主导日 1.07 同档级)
- ls_tstat=3.28 上探到 admit floor 3.0 (b097/C001 ls_t=2.85 未达 floor 是 reserve 原因 — 本候选解决)
- candle geometry **弱端 close-position binarize** 是 Barra-clean 子族被验证
- **结论**: T001 (上影主导日) + T008 (弱收盘日) 构成 "close-position 弱端 candle geometry" admit 子族, 几何路径 distinct from 27 个 linear-arithmetic admit + 1 个 conditional truncation (F028 DMI down-ratio).

### Layer 2: 升格律 — Binarize content 与 Barra basis 同构性 sign-dependent + threshold-dependent

- 本批 C001 (close 上半段 50%) vs C004 (close 弱端 20%) 同 (C-L)/(H-L) 信号底层, **alpha_survival 1:2 差距** (0.50 vs 1.10) — binarize **方向 (上半 vs 弱端)** 决定 Barra basis 同构性, 不是 magnitude
- 本批 C003 (强收盘 80%) vs C001 (上半段 50%) vs C004 (弱端 20%) **同信号不同阈值**: 高阈 80% sign_flip × 3, 50% borderline alpha_surv=0.50, 弱端 20% Barra-clean 1.10 — **阈值越偏 tail, 与 vol_20d basis 同构性差异越显著**, 弱端 tail (Lt(.,0.2)) 是真 ⊥, 强端 tail (Gt(.,0.8)) 是更深 //
- **机理**: A 股 csi1000 daily close-position 分布 skew negative (left-tail thick: 弱收盘比强收盘频率高, 与 vol_20d basis 频谱重叠程度也不对称) → Lt(low_threshold) 选 left-tail event 是 thick-tail 稳定子族, Gt(high_threshold) 选 right-tail event 与 vol regime sensitivity 共振

### Layer 3: T002 family 结构性 dead 升格 (跨阈值 dead)

- b097/C002 (gap-up 0.5% 阈值, 60d) alpha_surv=0.13 + vol_20d=27.6 reject
- 本批 C005 (gap-up 1.5% 阈值, 60d) alpha_surv=**0.030** + vol_20d=**35.4** reject (更恶化)
- 提高阈值反而恶化 alpha_survival — **gap-event 内容自身 ≡ vol_20d basis 信号 source**, 不通过 threshold tuning 解决
- **T002 family 整体结构性 dead**: 任何 `Mean(Gt(gap, threshold), N)` 形式 candidate 都 // vol_20d basis
- 跨 thread 同义: T002 (gap event rate) ≡ vol_20d basis 频谱内, **conditional truncation 路径需绕开 overnight gap 信号**

### Layer 4: Direction-level 洞察 (round 9 状态汇总)

- conditional_operator_truncation direction 累积 12 候选: 1 admit (C004 弱收盘日, 本批) + 1 reserve (b097/C001 上影主导日) + 10 reject
- **active threads 升级**: T008 active-validated (admit + extension paths), T001 mixed (b097 reserve hold, b098 mirror dead)
- **dead threads**: T002 (gap event rate, 跨阈值 dead), T003 (mask × raw), T004 (return-sign rate), T005 (低振幅日 rate), T006 (If × continuous momentum), T007 (small-body 主导日 rate), T009 (跨日 candle pattern)
- **edge 状态**: candle geometry single-day binarize 路径**部分 productive** (shadow + close-position 弱端), 多数子族 dead — direction 不至于 dead-spiral, 但 future batches 应聚焦 T008 extension (C004 + Std/Skew wrap, 不同窗口, 不同弱端阈值)
- **下一轮建议**: (a) C004 base + extension wraps (Std/Skew of rate, 60d 窗口); (b) 弱收盘日 + reversion gate 复合; (c) 其它 binarize 阈值 (Lt(.,0.15) / Lt(.,0.25)) 验证阈值敏感性; (d) lower-shadow 主导日 (Lt of (H-C)/(H-L)) 镜像于 b097/C001 上影主导
- 9-batch zero_admit_streak **打破** (9 → 0 reset) — calibration_trigger 可能解除压力 (从 dead-spiral 进入 productive territory)

## 错杀侦测扫描

无候选触发"错杀 4 件套":
- C001 max_corr=0.49 > 0.30 失败
- C004 max_corr=0.32 > 0.30 失败 — 已 admit, 非错杀路径
- C005 max_corr=0.38 + alpha_surv=0.03 catastrophic, 是真 vol_20d basis 吸收
- hard_gate fail 三候选 (C002/C003/C006) 不进 CP04+ 评估

无 reserve 候选触发, 无错杀诊断必要.

## §7.MT Budget

`mt_bucket` 全 6 候选 base bucket `high` (NEW direction 第二批累积 12 候选, family 频次 saturating); `search_adjusted` 部分降级: C001 low (0.3602), C004 low (0.3101), C005 medium (0.5283), 其它 high. MT-adjusted 仅影响 borderline 候选档位描述, 不改变本批 verdict (C004 admit 基于 ls_t=3.28 strong + alpha_surv=1.10 + distinct geometry 综合, MT-adjusted low 不阻 admit).

## Operations

- direction status: `exploring` (NEW direction, batch 1→2)
- rounds: 1 → 2; admits: 0 → **1** (C004); reserves: 0 (b097/C001 保留 reserve pool 但本批不新增); rejects: +5
- zero_admit_streak: 9 → **0** (break! 9 batches 累积零 admit 进入 productive territory)
- calibration_trigger: 维持但**压力解除** — 本批 admit 验证 lessons round 91 升格律 (binarize content ⊥ Barra basis), 表明系统 calibration 是正确的 (没有错杀, 真 alpha 在严格 floor 下也能识别)
- rounds_since_consolidation: 7 → 8 (距离 10 还有 2 轮, 本轮不触发)

## 下一步建议

1. **T008 extension (下批 candidates)**: C004 base form + extension wraps (Std/Skew of weak_close_day rate); 不同窗口 (60d 弱收盘日占比, robust test); 不同弱端阈值 (Lt(.,0.15) / Lt(.,0.25)) 验证阈值敏感性; lower-shadow 主导日 (Lt of (H-C)/(H-L)) 镜像于 b097/C001
2. **lessons-promotion 候选 (积累, 等 Phase 5)**:
   - "Binarize content 与 Barra basis 同构性是 sign-dependent + threshold-dependent: 同信号底层 (C-L)/(H-L), 弱端 binarize (Lt(.,0.2)) ⊥ vol_20d, 上半段 (Gt(.,0.5)) 部分 //, 高阈 (Gt(.,0.8)) 更深 // — sign 选 left-tail thick 是 robust escape"
   - "T002 gap-event rate family 跨阈值结构性 dead: gap content // vol_20d basis 是 source-level 同构, threshold tuning 不解决"
   - "T009 跨日 candle-pattern family dead: 复合 candle-pattern 是 regime-dependent 不是 alpha-stable, candle geometry binarize 路径有效性仅限单日内 geometry"
3. **F028 anchor cluster**: conditional family 第 2 个 admit (F028 DMI down-ratio + C004→F{next} weak_close_day_rate_20) 形成 cluster — F028 用 Lt×Greater 双 condition 比值, C004 用 Lt 单 condition rate; cluster 内 distinct geometry, 库内 conditional truncation rate 形式仍只有 1 个 admit
