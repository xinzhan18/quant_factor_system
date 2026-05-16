---
batch_id: batch_099
direction: conditional_operator_truncation
judged_at: 2026-05-16T01:00:00Z
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
mt_bucket: high
---

# batch_099 Judge Summary

> [!abstract]+ batch_099 · [[directions/conditional_operator_truncation]] · 6 candidates
> ❌ **reject=6** (C001-C006 全 reject) · admit=0 · reserve=0
> **核心发现**: F029 family **三轴扩展全部失败** — window 长 (60d → OOS 归零), threshold 微调 (0.15 → near_dup F029 corr=0.82 + incr_ic 负), Std-aggregate wrap (与 Mean 数学等价), open-position mirror (alpha_surv=0.15 // str_1m), Gt 0.8 short-window (window-invariant fail 验证 b098 律), compound vol-filter (引入 vol_20d=45.2 史诗共振). F029 在 family-space 是**孤立 admissible point** (close-position + Lt + 0.2 阈值 + 20d 同时锁定).
> **MT Budget**: cumulative 552 → **558** · direction 12 → **18** · bucket `high`（全 6 候选都到达 high 上界, search_adjusted 多数降至 medium/low）· 本批 low=0 / med=1(C004 adj) / high=5

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | hard_gate | sign_flip + ic_oos=-0.0007 | 60d 长窗使 weak-close event rate OOS 信号完全消失 — F029 family window 上限 < 60d | [[batches/batch_099/candidates/C001]] |
| C002 | ❌ reject | 🟢·🟡·🟡·🔴·🟡 | ic_oos=0.0080 max_corr=0.82@F029 incr_ic=-0.0003 | 阈值 0.2→0.15 微调 = F029 真子集, near_dup + 负库增值; F029 在 threshold 维度是 quasi-isolated point | [[batches/batch_099/candidates/C002]] |
| C003 | ❌ reject | hard_gate | sign_flip + max_corr=0.6163 (与 C001 完全同号同量级) | Std-of-binarize 60d 与 Mean-of-binarize 60d **数学几乎等价** (Var(Bernoulli)=p(1-p)) — aggregate wrap 轴 dead | [[batches/batch_099/candidates/C003]] |
| C004 | ❌ reject | 🟢·🟢·🔴·🟡·🟢 | ic_oos=0.022 strong, alpha_surv=0.15 catastrophic, incr_ic=-0.0023 | open-position mirror // str_1m basis (字段从 close 切到 open 即跨入 momentum 吸收区) — 与 T004 上涨日 mirror confirmation | [[batches/batch_099/candidates/C004]] |
| C005 | ❌ reject | hard_gate | ic_oos=-0.0040 (<0.008) | 短窗 10d 验证 b098 律 window-invariant — Gt 0.8 强端 binarize fail 与 window 无关 (10d & 20d 都 fail) | [[batches/batch_099/candidates/C005]] |
| C006 | ❌ reject | hard_gate | sign_flip + vol_20d_exp=45.18 史诗 + alpha_surv=0.615 | 复合 filter 引入 vol_20d 共振 — Gt(amplitude) ≡ vol_20d proxy, AND 复合时 vol_20d-isomorphic condition 主导, F029 ⊥ basis 优势被覆盖 | [[batches/batch_099/candidates/C006]] |

**档位编码**: 🟢 最优档 · 🟡 次档 · 🟠 边际 · 🔴 阻断档 · `hard_gate` reject 不填色.

## 跨候选对比

- **Style 聚合**: 6 候选中 5 个 dominant_style = vol_20d (C001/C002/C003/C004/C006), C005 也 vol_20d. F029 family 整体偏 vol_20d basis (与 F029 本身 dominant=str_1m 不同 — F029 dominant=str_1m=1.93 / vol_20d=7.0 平衡, 本批扩展候选都偏 vol_20d ≥ 7).
- **相关度 cluster**: C001 ≡ C003 (max_corr 与 F029 都 0.6163-0.6164 同号同 4 位小数, **二者 cross-section 信号 99% 同构**, 印证 Std-of-binarize 60d ≈ Mean-of-binarize 60d 律). C002/C006 都与 F029 corr ≥ 0.81 (threshold 微调与 compound filter 都未脱离 F029 base 几何).
- **vol_20d_exposure 阶梯**:
  - C006 复合 filter: **45.18** ⚠️ 史诗 catastrophic (本批最高, 全库 admit 历史 top-3)
  - C002 narrower threshold: 23.15 (high)
  - C001 alt-window 60d: 13.31 (本批最低)
  - C003 Std 60d: 13.36 (与 C001 几乎同步)
  - C004 open mirror: 10.23
  - C005 strong-close short: 7.41
  → 阶梯一致: 越加 vol-related condition (amplitude / shorter window strong-close), vol_20d 越深, F029 ⊥ basis 优势越被侵蚀.
- **MT 预算推进**: cumulative 552 → 558; direction_candidates 12 → 18 (本方向已扫近 1/3 family-space). Family score=0.987 接近饱和; direction score=0.585; exposure=1.0. **整批 mt_bucket=high** (但 search_adjusted 1 个 medium, 多数 low).
- **零 admit + 零 reserve** = 单批 family-axis 6 维度同时探活全部 fail. 这是 conditional_operator_truncation 方向**第一次** zero-reserve 批次 (b097 有 1 reserve, b098 admit 1).

## Thread 进展

> [!failure]+ T008 [[directions/conditional_operator_truncation#T008]] — 状态保持 `[✓ ANSWERED batch_098]` + 三轴升格补充
> 6 候选中 5 个属 T008 family 扩展 (C001 60d, C002 0.15, C003 Std-60d, C005 Gt-0.8-short, C006 compound). 全部 reject 但**律升格密集**:
> 1. **window 上限**: 60d 长窗 OOS 信号完全消失 (C001 + C003), F029 family 20d 是 sweet spot
> 2. **threshold sensitivity 窄**: 0.2 → 0.15 微调 = near_dup F029 + incr_ic 负 (C002); F029 在 threshold 维度是 quasi-isolated point
> 3. **aggregate wrap dead**: Std-of-binarize 与 Mean-of-binarize 60d 数学几乎等价 (Var(Bernoulli)=p(1-p) 在 low-rate 区与 p 共线) (C003)
> 4. **compound vol-filter 反弹**: Gt(amplitude) ≡ vol_20d proxy, AND 复合时 vol_20d 主导, F029 ⊥ basis 优势被覆盖 (C006)
> 5. **window-invariant of Gt-0.8 fail**: 短窗 10d 同 hard_gate fail, 印证 b098 律 (C005)
> **综合 conclusion**: F029 family axis-space 全方位探活完成, F029 是 close-position × Lt × 0.2 × 20d 的**孤立 admissible point**, 周围邻域全 dead.

> [!failure]+ T001 [[directions/conditional_operator_truncation#T001]] — 状态保持 `[◉ ACTIVE]` (b097/C001 reserve hold), 补充 disprove 一个 mirror
> C004 (open-position Lt 0.2 mirror) reject — open vs close 字段切换即跨入 str_1m + vol_20d basis 吸收区. b097/C001 上影主导日 reserve hold 维持, 但**字段维度 mirror 不可推广** (T001 reciprocal mirror 不可推广已 b098 验证, 本批进一步证明字段维度 mirror 也不可推广).

## 方向级反思

**conditional_operator_truncation 方向的 edge 已 systematically mapped**:
- **Active alpha**: F028 (DMI conditional, b085 admit) + F029 (close-position weak Lt 0.2 20d, b098 admit) — 2 admits in 99 rounds.
- **Family-space 拓扑**: F029 邻域内 (window / threshold / aggregate-wrap / field-mirror / compound-filter) 6 方向探活全 dead. F029 不是 family-cluster 的中心点而是**孤立 admissible point**.
- **`status: productive → saturated` 触发条件**: 本批 6 reject + zero reserve, 同方向 last 3 batches (b097/b098/b099) 累积 6 admit / 18 candidates = 5.5% admit rate. 已显著低于 productive 阈值 (一般 >15%).
- **下一轮建议** (若 orchestrator 继续选此方向):
  1. **跳出 F029 family-space**: 探索其它 conditional content 维度 (例如 turnover-binarize, fundamental-binarize, momentum-binarize 而非 candle-geometry-binarize)
  2. **F028 邻域**: 库 28 admit 中 F028 是另一 conditional anchor (DMI down ratio), 尚未在 family-space 内做 axis-wise 扩展
  3. **Python residualize on vol_20d**: b097/C001 reserve (上影主导日 alpha_surv=1.07 reserve) 仍 hold 等 daily_python 模板, 是仍可激活的 reserve
- **建议 status change**: `productive → saturated` (LLM 在 frontmatter 翻翻牌)

**MT Budget 信号**: cumulative 552, direction 18. cumulative 接近 600 历史阈值 (历史 admit cumulative 在 ~540-560 区间). search_adjusted 全 low/medium 说明同方向重复搜索回报递减.

**零 admit + 零 reserve, calibration trigger 状态**: zero_admit_streak 0 → **1**; rounds_since_consolidation 8 → **9**. **错杀侦测扫描**: 所有 6 候选无满足 4 件套 (C002/C004 都 incr_ic 负值, 不满足 incremental_ic > 0.010 条件). 无错杀风险.

**律升格 candidate (round 99 → lessons.md)** — 这是本批的真正产出, 即使 0 admit 也是有效 lesson:
1. **F029 family axis-wise 行为律 (b099 综合)**: F029 是 close-position × Lt × 0.2 阈值 × 20d × Mean × 单 condition 的**6 维约束孤立 admissible point**; 任一维度扰动 (window / threshold / aggregate / field / direction / compound) 即跨出 ⊥ basis 区. — 应升格.
2. **Std-of-binarize ≡ Mean-of-binarize 60d 律 (C003 实证)**: Var(Bernoulli)=p(1-p), p 低值区与 p 单调相关; 长窗下 second moment 不构成正交几何. — 应升格 (跨 family 普适).
3. **Compound vol-isomorphic condition 反弹律 (C006 实证)**: AND 复合两 condition 时 vol_20d-isomorphic condition 会主导 Barra basis 同构性, 即使另一 condition ⊥ basis 也被覆盖. — 应升格 (跨 family 普适).
4. **binarize content (字段+方向+阈值) 三要素决定 ⊥ basis 律 (b098 round 10 律 → b099 精化)**: 仅同 (range-position) geometry framework 不足够, 字段切换 (close → open) 即跨入 str_1m basis 吸收区. — 应升格 (round 10 律的进一步精化).
