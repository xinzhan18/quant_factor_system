---
batch_id: batch_101
direction: binarize_geometry_barra_orthogonal
judged_at: 2026-05-16T07:30:00Z
candidates:
  - {candidate_id: C001, verdict: reject}
  - {candidate_id: C002, verdict: reject}
  - {candidate_id: C003, verdict: reject}
  - {candidate_id: C004, verdict: reject}
  - {candidate_id: C005, verdict: reject}
  - {candidate_id: C006, verdict: reject}
batch_summary: {total: 6, admit: 0, reserve: 0, reject: 6}
admit_count: 0
reject_count: 6
reserve_count: 0
candidate_count: 6
mt_bucket: medium
---
# batch_101 Judge Summary

> [!abstract]+ batch_101 · [[directions/binarize_geometry_barra_orthogonal]] · 6 candidates
> ✅ **admit=0** · ⏸ **reserve=0** · ❌ **reject=6**
> **核心发现**: F029 之外 single-day candle binarize 几何空间 6 axes 系统化 sweep 全 reject — 验证 finding 023 的核心担忧"family-space 非孤立"在第一轮即被挑战: middle-body (CP01 sign 翻号) / 上影微小 mirror (CP01 sign 翻号 + OOS 归零) / 弱 open (alpha_surv=0.07 str_1m 直接吸收) / inside-bar (alpha_surv=0.125 vol_20d 反向 proxy 吸收) / weak-close × low-turnover (max_corr=0.726@F029 high + 库 reducer) / 大实体 0.7 (vol_exp=28.80 史诗 + incr_ic 负). **3 条 lesson 升格 candidate**.
> **MT Budget**: cumulative 564 → **570** · direction 0 → **6** · bucket `medium`（新方向首批 direction-level exposure 低拉 mt_bucket 至 medium not high）· 本批 low=0 / med=6 / high=0

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | hard_gate | sign_flip + oos_decay -3.65 + mono_sign_flip | middle-body proximity 几何 IS/OOS sign 双翻号 + 单调 sign 翻号, regime-dependent, 不是稳定 alpha 几何 | [[batches/batch_101/candidates/C001]] |
| C002 | ❌ reject | hard_gate | sign_flip + ic_oos 0.001 + oos_decay -0.138 | 弱上影日 mirror, OOS 信号归零; F029 阈值 sign-dependent 律字段切换即失效 | [[batches/batch_101/candidates/C002]] |
| C003 | ❌ reject | mixed·borderline·**poor**·medium·mixed | alpha_surv=**==0.07==** str_1m=3.36 + vol_20d=15.06 | open 弱开日 ≡ str_1m basis 直接 proxy, 字段切换 close→open 共振 1-month reversal | [[batches/batch_101/candidates/C003]] |
| C004 | ❌ reject | mixed·borderline·**poor**·low·mixed | alpha_surv=**==0.125==** vol_20d=7.19 max_corr=**==0.208==**(!) | inside-bar rate ≡ low vol regime 反向 proxy; max_corr 低但 incr_ic≈0 是"static vs dynamic ⊥"悖论 | [[batches/batch_101/candidates/C004]] |
| C005 | ❌ reject | mixed·borderline·borderline·**high**·stable | max_corr=**==0.726==**@F029 + incr_ic=-0.0005 | F029 子集; turnover self-baseline 复合 condition 反引入 str_1m=3.51 + alpha_surv 从 F029 的 1.10 退化到 0.33 | [[batches/batch_101/candidates/C005]] |
| C006 | ❌ reject | hard_gate | ic_oos=0.0054<0.008 + vol_20d=**==28.80==** + incr_ic=-0.009 | 大实体 trend-day rate ≡ vol_20d basis 史诗共振; body 几何 binarize Gt 强端 0.7 + Lt 弱端 0.3 双向 dead | [[batches/batch_101/candidates/C006]] |

**档位编码**：🟢 最优档 · 🟡 次档 · 🔴 阻断档 · `hard_gate` reject 不填色.

## 跨候选对比

- **Style 聚合 (catastrophic)**: 6 候选 vol_20d_exposure 分布 = [18.97, 6.58, 15.06, 7.19, 8.00, **28.80**]. 中位数 11.5, 最大 28.80 (C006 大实体率). **6/6 都被 vol_20d 主导**, 即使设计 anti-vol-isomorphic 也未逃脱 — 表明 conditional binarize 在 csi1000 daily geometry 上**默认结局是 vol_20d 共振**, F029 是稀有例外.
- **str_1m 共振**: C002/C003/C005 三个 str_1m_exp [2.91, 3.36, 3.51] 中等-高水平 — open-tail (C003) 直接共振; close-high mirror (C002) 中度共振; weak-close × low-turnover 复合 (C005) 触发 str_1m 共振. F029 close-low 弱端 str_1m_exp=0.91 (实测) 是**唯一逃 str_1m 的几何**.
- **max_corr 分布**: [0.595, 0.422, 0.363, 0.208, **0.726**, 0.475]. C004 inside-bar 给出 max_corr=0.208 (low!) 但 alpha_surv=0.125 表明 library-independent 仅在线性 corr 意义上, 非真正几何 distinct.
- **alpha_surv 分布**: [0.45, 0.76, **0.07**, **0.125**, 0.33, 2.15]. C003/C004 双 poor; C006 alpha_surv=2.15 paradox guard 标准案例 (alpha_surv > 1.0 但 0/3 配套指标全 fail).
- **MT 预算推进**: cumulative 564 → 570; direction_candidates 0 → 6 (新方向直接 6 + 0); bucket `medium` (direction 仍 sparse).

## Thread 进展

> [!failure]+ T001 [[directions/binarize_geometry_barra_orthogonal#T001]] — `[✗ DISPROVEN batch_101]`
> reject C001. middle-body proximity 几何 IS/OOS 双 sign 翻号 + 单调反号, regime-dependent. 中点附近事件 IS 期 = 信号缺失日 positive 选股, OOS 期反 — 不构成稳定 alpha 几何. 几何 confirmed disprove.

> [!failure]+ T002 [[directions/binarize_geometry_barra_orthogonal#T002]] — `[✗ DISPROVEN batch_101]`
> reject C002. 弱上影 mirror (反 F029 close-low → close-high) sign 翻号 + OOS 归零. F029 律 (Lt 弱端 thick-tail ⊥ basis) 在字段切换 (close-tail → upper-shadow-tail) 即破坏. **lesson candidate**: 阈值 sign-dependent 律字段绑定.

> [!failure]+ T003 [[directions/binarize_geometry_barra_orthogonal#T003]] — `[✗ DISPROVEN batch_101]`
> reject C003. 弱 open 低位日 (reciprocal of b099/C004) alpha_surv=**0.07** str_1m_exp=3.36, open 字段切换 (close→open) 即 触发 str_1m basis 共振. b099/C004 同构 dead 验证 conditional_operator_truncation hypothesis 第 4 条 (字段 — open vs close 切换即跨入 str_1m basis 吸收区) **不论 tail 方向都成立**.

> [!failure]+ T004 [[directions/binarize_geometry_barra_orthogonal#T004]] — `[✗ DISPROVEN batch_101]`
> reject C004. inside-bar 跨日 range pattern alpha_surv=**0.125** vol_20d=7.19. max_corr=0.208 (low!) + mono_oos=-0.90 真实, 但 incr_ic≈0 显示 **"static vs dynamic ⊥ Barra 悖论"**: 几何独立 ≠ alpha 独立 — inside-bar 直接 ≡ low vol regime proxy. 跨日 range pattern 路径 dead.

> [!failure]+ T005 [[directions/binarize_geometry_barra_orthogonal#T005]] — `[✗ DISPROVEN batch_101]`
> reject C005. weak-close × low-turnover cross-field compound max_corr=**0.726@F029** + incr_ic=-0.0005 库 reducer. **关键发现**: turnover self-baseline 复合 condition 没有保护 ⊥ Barra basis — 在 F029 已 ⊥ basis 的 close-tail 上叠加 turnover-low 条件, str_1m_exp 从 0.91 涨到 3.51, alpha_surv 从 1.10 跌到 0.33. **复合 condition 引入 selectivity 反而吸引 basis 共振**. lesson candidate.

> [!failure]+ T006 [[directions/binarize_geometry_barra_orthogonal#T006]] — `[✗ DISPROVEN batch_101]`
> reject C006. 大实体率 Gt 强端 0.7: ic_oos=0.0054<0.008 + vol_20d_exp=**28.80** 史诗 + incr_ic=-0.009. body 几何 binarize 跨阈值方向双向 dead (Lt 0.3 small-body 已 b098/C002 dead, 本批 Gt 0.7 大实体 dead). **阈值 sign-dependent 律仅适用 close-position 字段** (close × Lt × 0.2 × 20d 是唯一 admissible point).

## 方向级反思

batch_101 首轮 0 admit 0 reserve 6 reject 全军覆没. 6 axes 系统化 sweep 揭示:

1. **F029 是 quasi-isolated singularity 的 hyper-isolated 版本** — 不仅在 conditional_operator_truncation 方向的 close-pos × Lt × 0.2 × 20d 7 维约束邻域是 quasi-isolated point, 在更广 single-day candle binarize 6-axis 邻域 (middle-body / 上影 mirror / open mirror / inside-bar / compound / body Gt) 也是 isolated — **每个 axis 都被 vol_20d / str_1m basis 共振吃干, F029 是 csi1000 daily geometry 上唯一 conditional binarize ⊥ Barra basis 的 admissible 点**.

2. **finding 023 部分挑战**: finding 023 假设"family-space 非孤立, single-day candle binarize 子族还有大量未开发 ⊥ basis 几何". batch_101 实证显示**预期清单中的 6 子族全部 ≡ basis**:
   - middle-body (T001): regime-dependent sign
   - 弱上影 mirror (T002): 字段切换破 F029 律
   - 弱 open mirror (T003): open 字段 ≡ str_1m
   - inside-bar (T004): ≡ low vol regime
   - cross-field compound (T005): 复合反吸引 basis
   - body Gt 强端 (T006): ≡ vol_20d 史诗共振

3. **3 条 lesson promotion candidate**:
   - **(a) 阈值 sign-dependent 律字段绑定**: F029 Lt 弱端 thick-tail ⊥ basis 律仅在 close-position 字段成立, 字段切换 (close→open / close→upper-shadow / close→body) 即失效 — 字段而非"close-tail" 几何抽象本身是 anchor.
   - **(b) 复合 condition 反吸引 basis 律**: 在 ⊥ basis 母信号 (F029) 上叠加 selectivity condition (turnover-low) 反而引入新 basis exposure (str_1m), alpha_surv 退化 — selectivity 与 ⊥ basis 不兼容.
   - **(c) body 几何 binarize family 跨阈值方向双向 dead**: b098/C002 Lt 0.3 small + b101/C006 Gt 0.7 large 双 dead, body 维度无 ⊥ basis admissible point.

4. **direction operations**: 0/6 全 reject 首批, 但 6 axes 一次性 exhaust 主要 axis-wise hypothesis, 直接 status: exploring → dead (而非 saturated) — hypothesis 已被实证整体证伪 (finding 023 的"family-space 非孤立"假设至少在线性 binarize 路径上不成立). 不预期沿此方向再开 batch.

**下一步**: 
- 本方向 status: `exploring → dead` (1 batch 完成 sweep 即证伪 hypothesis, 见 lessons "P004-deep 律本质升格" 同构 ".)
- 3 条 lesson promote 待 consolidation 提取
- finding 023 的"family-space 非孤立"假设可缩窄: F029 + b097/C001 reserve 是 single-day candle binarize ⊥ basis 在 csi1000 daily 上**仅有的两个 admissible point**, 完整空间 sweep 7+ batches 30+ candidates 后无新 admit → conditional binarize 路径 csi1000 daily 真饱和
- 后续优先级: 转 F028 邻域 axis-wise 扩展 (DMI conditional ratio, 几何与 candle binarize 完全不同) / 跳出 conditional 路径
