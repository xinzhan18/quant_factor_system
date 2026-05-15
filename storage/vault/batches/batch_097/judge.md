---
batch_id: batch_097
direction: conditional_operator_truncation
judged_at: 2026-05-15T23:55:00Z
candidates:
  - {candidate_id: C001, verdict: reserve}
  - {candidate_id: C002, verdict: reject}
  - {candidate_id: C003, verdict: reject}
  - {candidate_id: C004, verdict: reject}
  - {candidate_id: C005, verdict: reject}
  - {candidate_id: C006, verdict: reject}
batch_summary: {total: 6, admit: 0, reserve: 1, reject: 5}
admit_count: 0
reject_count: 5
reserve_count: 1
candidate_count: 6
mt_bucket: medium
---

# batch_097 Judge Summary

**Direction**: [[directions/conditional_operator_truncation]] (NEW)
**Batch goal**: Structural gap exploration — conditional operator family (Gt/Lt/If) under-utilized; 6 子族 truncation 路径 (T001-T006)
**Verdicts**: admit=0 · reserve=1 (C001) · reject=5 (C002, C003, C004, C005, C006)
**MT Counts (post-batch)**: cumulative 540 → 546 · direction 0 → 6 · validation_exposure 96 → 102

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ⏸ reserve | 🟢·🟡·🟡·🟡·🟢 | ic_oos=+0.0088 ls_t=+2.85 alpha_surv=**1.07** mc=0.41@F022 | 上影主导日占比 — 唯一 binarize 内容 ⊥ Barra basis 的几何, alpha_surv>1.0 但 ls_t<3.0 admit floor | [[batches/batch_097/candidates/C001]] |
| C002 | ❌ reject | 🟡·🔴·🔴·🟡·🟡 | ls_t=-0.61 alpha_surv=0.13 vol_20d=27.6 | 60d gap-up event rate 完全被 vol_20d basis 吸收 (binarized content 同构 basis) | [[batches/batch_097/candidates/C002]] |
| C003 | ❌ reject | 🟡·🟢·🔴·🟡·🟢 | ls_t=-3.59 alpha_surv=0.15 vol_20d=37.4 | mask × raw turnover (partial truncation) 保留 magnitude → 100% basis 吸收 | [[batches/batch_097/candidates/C003]] |
| C004 | ❌ reject | 🟢·🟡·🔴·🟡·🟢 | ls_t=-2.71 alpha_surv=**0.07** (本批最低) str_1m=5.45 | 上涨日占比 ≈ str_1m basis direct proxy (return-sign 同构 reversal style) | [[batches/batch_097/candidates/C004]] |
| C005 | ❌ reject | 🟡·🟢·🔴·🔴·🟢 | ic_oos=+0.057 (本批最强) alpha_surv=0.22 vol_20d=**46.8** (本批最高) max_corr=0.66 | 低振幅日占比 ≈ vol_20d basis 反向 proxy, max_corr 临 0.70 | [[batches/batch_097/candidates/C005]] |
| C006 | ❌ reject | 🟡·🟢·🔴·🟡·🟢 | ls_t=-3.57 style_r²=**0.71** (本批最高) str_1m=7.77 alpha_surv=0.83 | If × continuous momentum (conditional observation), gating 仅 filter 不破 absorption — P030 paradox 反例 | [[batches/batch_097/candidates/C006]] |

**档位编码**: 🟢 最优档 · 🟡 次档 · 🟠 边际 · 🔴 阻断档.

## 跨候选对比

**Style 聚合**: 5/6 候选 dominant=vol_20d (C001/C002/C003/C004/C005), C006 dom=str_1m. Vol_20d exposure 阶梯: C001 15.6 < C004 13.6 < C002 27.6 < C003 37.4 < C005 **46.8** (本批最高). **关键发现**: vol_20d exposure 强度与 alpha_survival 高度反向相关 (C005 vol_20d=46.8 → alpha_surv=0.22, C001 vol_20d=15.6 → alpha_surv=1.07) — 验证 conditional truncation 路径下 binarized content 是否 ⊥ Barra basis 是核心 admit 判断标准.

**相关度 cluster**: 6 候选 max_corr ∈ [0.35, 0.66], 全部 < 0.70 (无 near_duplicate). nearest 散布于 F017/F021/F022/F027 — 几何路径独立但 conditional truncation family 整体与现有 admit cluster 边缘.

**MT 预算推进**: cumulative 540 → 546; direction 0 → 6 (NEW direction 首批); bucket 仍 medium, search_adjusted 全候选在 0.32-0.59 之间.

**Binarize content 同构性分析 (本批最有价值发现)**:

| 候选 | binarize 内容 | 同构 Barra basis | alpha_surv | 结论 |
|---|---|---|---|---|
| C001 | 上影主导日 (candle geometry) | **无同构** ⊥ | **1.07** | 唯一 Barra-clean, distinct geometry |
| C002 | 强 gap-up | vol_20d (overnight gap = vol signal) | 0.13 | 100% absorption |
| C003 | mask × raw turnover (partial truncate) | vol_20d (raw turnover ≈ vol proxy) | 0.15 | 100% absorption |
| C004 | return-sign | str_1m (return-sign = short-term reversal) | 0.07 | 100% absorption |
| C005 | 低振幅日 (range threshold) | vol_20d (反向 vol indicator) | 0.22 | 100% absorption |
| C006 | If × continuous momentum | str_1m (momentum = str_1m basis) | 0.83 (paradox) | gating 不破 absorption |

**结论**: conditional truncation 路径的 admit 充分条件不是"形式独特" 而是 **"binarized content ⊥ Barra style basis"**. 满足该条件的候选 (C001) 是 Barra-clean residual alpha; 违反该条件的候选 (其它 5) 即使形式 distinct (Gt/Lt/If aggregate) 仍 100% basis 吸收.

## Thread 进展

> [!note]+ T001 [[directions/conditional_operator_truncation#T001]] — `[◉ ACTIVE]` (borderline)
> 本批 C001 (上影主导日 20d 占比). alpha_survival=**1.07** Barra-clean + ls_t=2.85 moderate + max_corr=0.41 → reserve.
> 唯一通过 P030 paradox guard 但 admit 充分条件 2/4 缺 max_corr/incr_ic. **唯一 productive thread, 下批 T001 几何扩展首要任务**.
>
> **Next probes**: (a) 下影主导日 (Lt of (C-L)/(H-L), 应是 C001 sign-flip 镜像非独立 — 需 check); (b) middle-body 主导日 (|close - (H+L)/2|/H-L < 0.3 rate, 完全不同 candle geometry); (c) range-position discrete bucket (close-position 离散化为 quintile rate); (d) C001 + Std/Skew wrap of event rate.

> [!failure]+ T002 [[directions/conditional_operator_truncation#T002]] — `[✗ DISPROVEN batch_097]`
> C002 60d gap-up rate alpha_surv=0.13 + vol_20d=27.6 catastrophic — gap-up rate 与 vol_20d basis 同构, binarize 不构成 escape.

> [!failure]+ T003 [[directions/conditional_operator_truncation#T003]] — `[✗ DISPROVEN batch_097]`
> C003 mask × raw turnover alpha_surv=0.15 + vol_20d=37.4 + style_r²=0.52 — partial truncation 保留 raw magnitude → 100% absorption. **核心机制揭示**: must full binarize, mask × raw 不构成 escape.

> [!failure]+ T004 [[directions/conditional_operator_truncation#T004]] — `[✗ DISPROVEN batch_097]`
> C004 上涨日占比 alpha_surv=**0.07** (本批最低) + str_1m=5.45 — return-sign 与 short-term reversal style 同构.

> [!failure]+ T005 [[directions/conditional_operator_truncation#T005]] — `[✗ DISPROVEN batch_097]`
> C005 低振幅日 60d ic_oos=+0.057 (本批最强 magnitude) 但 alpha_surv=0.22 + vol_20d=**46.8** (本批最高) + max_corr=0.66 — 低振幅日占比 ≈ vol_20d 反向 direct proxy.

> [!failure]+ T006 [[directions/conditional_operator_truncation#T006]] — `[✗ DISPROVEN batch_097]`
> C006 PV-corr gated momentum style_r²=**0.71** (本批最高) + str_1m=7.77 + alpha_surv=0.83 paradox — conditional observation × continuous signal 不破 momentum-basis 同构, P030 律反例.

## 跨候选反思 (4 层)

### Layer 1: 本批最强结论 — Binarized event-rate 路径**部分可行**但**严格依赖 binarized 内容与 Barra style basis 不同构**

- **C001 (alpha_surv=1.07)** 与 **C002/C004/C005 (alpha_surv∈[0.07, 0.22])** 都是 binarize + Mean aggregate 几何, 但 alpha_survival 天差地别.
- 区分: **C001 binarize 内容**(上影主导日 = candle geometry 衍生) 与 Barra 9-style basis (size/vol/momentum/value/quality/turnover/leverage/eps/str_1m) **不同构** → alpha_survival>1.0 真 distinct geometry
- **C002 内容**(强 gap-up) 与 vol_20d 同构, **C004 内容**(return sign) 与 str_1m 同构, **C005 内容**(低振幅日) 与 vol_20d 反向同构 → 100% basis 吸收
- **C006 conditional observation × continuous signal**: gating 不破 absorption — momentum 本身同构 str_1m, gate 只 filter 50% sample 但 cross-section ordering 保留

### Layer 2: 反 P004-deep 律 — Binarize 部分逃脱但**不绝对** (60d aggregate 仍部分共振)

- 本批 manifest 显式标注 P004-deep BORDERLINE: 离散事件率 aggregate 理论 path-memory β-shift 消失
- **实证三联**: C002 (60d gap rate) + C004 (20d return-sign rate) + C005 (60d low-amp rate) 全被 vol/str basis 吸收
- **机制升格**: P004-deep 律的本质不是"path-memory β-shift", 而是**"long-window aggregate 必然与 style basis 频谱共振 IF binarized content 同构 basis"**.
- C001 (20d 上影主导日 rate) 是 binarize aggregate 唯一逃脱案例, 但**不是因为 20d 窗口短** (C004 也是 20d 但被吸收), 而是因为 binarize content (candle geometry) 与 Barra style 不同构.

### Layer 3: T001 是真 productive thread, T002-T006 是 dead

- T001 (上影主导日): C001 borderline reserve, distinct geometry verified, **唯一 productive direction in this batch**
- T002 (gap event rate): dead — vol_20d 同构
- T003 (mask × raw): dead — partial truncation 不构成 escape, vol_20d_exp=37.4 catastrophic
- T004 (win rate): dead — str_1m 同构
- T005 (low-amp rate): dead — vol_20d 反向同构
- T006 (gated momentum): dead — conditional observation 不破 str_1m absorption

### Layer 4: Direction-level 洞察

- Conditional operator truncation 不是"一招通吃" — 结构性 gap 假设**部分验证**但前提条件严格
- **可行路径** (T001 + 类似几何): binarize content ⊥ Barra basis (candle geometry / non-money-flow regime indicator)
- **不可行路径** (T002-T006): binarize content // Barra basis (return-sign, gap, mom, amp, turnover-level)
- F028 anchor precheck 全候选通过 (max F028_corr=0.30 in C001, 其它 |corr|<0.5) — DSL conditional family 仍 0 admit, 不与 F028 cluster
- 下一批应聚焦 T001 几何扩展: (a) 下影主导日占比 (Lt of (C-L)/(H-L), 反向对偶, 与 C001 应是 sign-flip 镜像非独立); (b) middle-body 主导日占比 (Gt of (|close-(H+L)/2|)/H-L, 完全不同 candle geometry); (c) C001 + reversion gate 复合; (d) Python residualize C001 on vol_20d 看是否破 ls_t admit floor

## 错杀侦测扫描

无候选触发"错杀 4 件套" (max_corr<0.30 + incremental_ic>0.010 + mono_oos|x|≥0.80 + nearest_sign 相反). C001 max_corr=0.40 (不到 0.30), incremental_ic=0.0030 (不到 0.010) — 不构成错杀, reserve 决定基于 P030 paradox guard 三条件 2/4.

## §7.MT Budget

`mt_bucket: medium` for all 6 candidates; `search_adjusted` ranges low (C001=0.32) to medium (C003/C005=0.59). MT-adjusted 仅影响 borderline 候选档位描述, 不改变本批 verdict.

## Operations

- direction status: `exploring` (NEW direction, batch 0→1)
- rounds: 0 → 1; admits: 0; reserves: +1 (C001); rejects: +5
- zero_admit_streak: 8 → 9
- calibration_trigger 维持 true (from b095/b096), 但本批是结构性新方向探索 (NEW direction) **不加深 dead-spiral 因子**; orchestrator 下轮可以选择 (a) 继续 conditional family T001 几何扩展; (b) dispatch calibration 流程对 reserve 池整体重评估; (c) 开新方向.

## 下一步建议

1. **T001 几何扩展** (下批 candidates): C001 base form + binarize content 变体 (lower-shadow / middle-body / range-position 各种 candle geometry 离散化)
2. **lessons-promotion 三条**:
   - "Conditional truncation 路径 admit 充分条件: binarized content ⊥ Barra style basis (candle geometry / non-money-flow regime); 违反则 100% absorption"
   - "P004-deep 律本质升格: long-window aggregate 必然与 style basis 频谱共振 IF binarized content 同构 basis (path-memory β-shift 消失不够, 内容同构是真死因)"
   - "Conditional observation (If × continuous signal) 不破 absorption: gating 仅 filter sample, 不改变 cross-section ordering 与 style basis 同构关系"
3. **Python residualize 配套开发** 仍 missing (b096 blocker); 若开发, C001 + reserve pool 整体可走 Python residualize 路径
