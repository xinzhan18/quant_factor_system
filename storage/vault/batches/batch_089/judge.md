---
batch_id: batch_089
direction: idiosyncratic_momentum_residual
judged_at: 2026-05-04T16:45:00Z
candidates:
  - {candidate_id: C001, verdict: reject, thread_id: T001}
  - {candidate_id: C002, verdict: reject, thread_id: T001}
  - {candidate_id: C003, verdict: reject, thread_id: T001}
  - {candidate_id: C004, verdict: reject, thread_id: T002}
  - {candidate_id: C005, verdict: reject, thread_id: T003}
  - {candidate_id: C006, verdict: reject, thread_id: T004}
batch_summary: {total: 6, admit: 0, reserve: 0, reject: 6}
admit_count: 0
reject_count: 6
reserve_count: 0
candidate_count: 6
mt_bucket: medium
---

# batch_089 Judge Summary

> [!abstract]+ batch_089 · [[directions/idiosyncratic_momentum_residual]] · 6 candidates
> ✅ **admit=0** · ⏸ **reserve=0** · ❌ **reject=6** (all 6 reject — 方向首批反向证伪)
> **核心发现**: 海通-37 IMom path-integral 假设在 csi1000 daily 上**整体反向 + Barra basis 越累越深 + library reducer 全 NEG** 三立证伪. 6/6 reject 中 4 个 hard_gate PASS (C001/C002/C003/C004) + 2 个 hard_gate 边缘 (C005 ls_t=-0.28 / C006 ls_t=-1.58 弱信号), **incremental_ic 全负** (-0.018/-0.015/-0.011/-0.014/-0.010/-0.009). T001 (path-integral raw cumulative 60/120/250d 三窗) 全 reject + T002 (vol-normalized 120d Sharpe-like) reject + T003 (rank-diff path-integral vs raw return 突破 T014 4 律 attempt) reject + T004 (low-IVOL gated salvage 路径) reject — **方向四个子假设 4/4 全证伪, 直接归 dead**. 关键升格律 (P004 边界扩展 + paper transfer 律新例 + alpha_surv > 1.0 单边不足律): **(i) Barra residualization 单日 vol_20d 线性剥离不阻断 N-day path memory 重累积 — cumulative sum 形式即使在 60d/120d/250d 窗口下 dom_style 全部恢复 = vol_20d, exposure 19.6-23.2 (整批最高), 律边界从"second-moment magnitude / 累积形式" 扩展到 "Barra-residualized return 也无法逃离, path memory 是结构性律不是线性算子可剥离"**; (ii) **海通-37 paper monthly IMom → csi1000 daily 双失败**: 方向反号 (paper momentum → csi1000 mean-reversion) + horizon mismatch (paper 12月 horizon 在日频 250d 等价 form 上 alpha_surv 单调衰减至最低 0.356); (iii) **rank-diff × residual paradigm path-integral LHS 扩展失败 (C005)**: alpha_surv=1.054 form-independent + max_corr=0.15 LOW 整批最低, 但 ls_t=-0.28 信号几乎不存在 + mono_oos=-0.20 quintile collapse — alpha_survival > 1.0 单边不足律第 4 次实证 (b072/b086/b087/b088 + 本批 = 5 次).
> **MT Budget**: cumulative 492 → **498** · direction 0 → **6** (新方向首批) · bucket `medium` (search_adjusted=medium, family≈0.97 saturated cluster, direction=0.0 新方向余量, exposure=1.0)

## 候选一览

| ID | Verdict | 档位 (CP1·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | pass·strong·**borderline-acc**·**borderline-high**·perfect | ic_oos=-0.054 ls_t=-6.19 mono=-1.0/-0.9 alpha_surv=0.421 max_corr=0.35@F027 incr_ic=-0.0178 9/9_neg | T001 60d short window. **方向反号** (paper momentum → mean-reversion) + **dom=vol_20d exp=23.2 巨大** + library reducer (F027 multi_ma_reversion 同质) + incr_ic strongly NEG. P004 边界扩展强证据: cumulative path-integral 重累积 vol_20d 比 single-day 残差更深 → Barra residualization 不破 path memory. | [[batches/batch_089/candidates/C001]] |
| C002 | ❌ reject | pass·strong·**poor**·medium·perfect | ic_oos=-0.049 ls_t=-4.76 mono=-1.0/-1.0 alpha_surv=**0.373** max_corr=0.28@F002 incr_ic=-0.0147 9/9_neg | T001 120d medium. **alpha_surv=0.373 < 0.40 floor (CP04 FAIL)**. 窗口越长 alpha_surv 越低 (0.42→0.37→0.36 单调衰减) — Barra basis 吸收随 path memory 加深. | [[batches/batch_089/candidates/C002]] |
| C003 | ❌ reject | pass·strong-borderline·**poor**·medium·acceptable | ic_oos=-0.041 ls_t=-3.41 alpha_surv=**0.356** max_corr=0.28@F002 incr_ic=-0.0111 dom=vol_20d | T001 250d long (paper Haitong-37 12m equivalent). **alpha_surv=0.356 整批最低**. paper 12m horizon 在 csi1000 daily 完全失效 — 月频 → 日频 path memory 不同律. T001 thread DISPROVEN 三窗全 reject. | [[batches/batch_089/candidates/C003]] |
| C004 | ❌ reject | pass·strong·**poor**·medium·acceptable | ic_oos=-0.053 ls_t=-5.01 alpha_surv=**0.332** max_corr=0.29@F017 incr_ic=-0.0145 dom=vol_20d | T002 120d vol-normalized Sum/Std (paper strict definition). **vol-normalize 不仅没救 alpha_surv 反而 0.332 整批最低 + 比 raw C002 (0.373) 更差**. 分母 Std(ε,120) 共线于 vol_20d basis, 除以噪声放大 Barra 项. paper IR=2.04 配方在 csi1000 daily 完全失效. T002 DISPROVEN. | [[batches/batch_089/candidates/C004]] |
| C005 | ❌ reject | pass·**weak**·acceptable·LOW·mixed | ic_oos=-0.013 **ls_t=-0.28** mono_oos=-0.20 alpha_surv=1.054 max_corr=**0.15@F002 LOW** incr_ic=-0.0096 | T003 rank-diff path-integral vs raw return 120d. alpha_surv=1.054 form-independent + max_corr 0.15 LOW (整批最低), 但 **ls_t=-0.28 信号几乎不存在 + mono_oos=-0.20 quintile collapse**. **alpha_surv > 1.0 单边不足律第 5 次实证** (跨 b072/b086/b087/b088/本批). T003 DISPROVEN: rank-diff salvage 在 path-integral LHS 同样失败. 不达 reserve 门槛 (ls_t 太弱). | [[batches/batch_089/candidates/C005]] |
| C006 | ❌ reject | pass·**weak**·borderline·medium·acceptable | ic_oos=-0.037 **ls_t=-1.58** alpha_surv=0.395 max_corr=0.30@F021 incr_ic=-0.0093 style_r²=0.0_artifact | T004 low-IVOL gated 60d. style_r²=0.0 是 metric 退化 artifact (gating 0/1 mask 让 Barra exposure metric 计算无意义), 不是真 clean. ls_t 从 C001 -6.19 衰减到 -1.58, 信号 strength 不足. T004 DISPROVEN: IVOL gating 不破 library overlap (incr_ic 仍 NEG) 且削弱 signal — vol_20d path memory 是结构性律不可通过 LHS 0/1 mask 切除. | [[batches/batch_089/candidates/C006]] |

## 跨候选对比

- **本批整体律 — Barra residualization + path integral 不破 vol_20d 吸收**: 4 个 hard_gate PASS 候选 (C001-C004) **dominant_style 全部 = vol_20d**, exposure 19.6-23.2 (整批最高 cluster, 比单日 F004 残差更深). C005 / C006 因 form 退化 (rank-diff / gating) 让 dom_style 失真但 incr_ic 仍 NEG. 对照 F004 单日 Barra-residual: F004 alpha_surv=1.41 + admit OK, **本批 N-day 累积形式 alpha_surv 0.33-0.42 全衰减至 floor 附近**. 直接证据: **Barra cross-sectional residualization 是 single-step 线性算子, 对单日 ε 有效, 但 path integral Sum(ε_t-N+1..ε_t) = Σ(原始 ε_i + Σ_j β_ij(t-i) X_j(t-i)), 内层 β 在 t 时不是常数, path-memory β shift 让累积形式 vol_20d 暴露重新涌现**. 这是 P004 律的结构性扩展 — 比 P008 TsRank 时序 form / P016 cap-denominator 嵌入 更深的层次, 适用于"任何对 residual 做 N-day 累积/时序聚合的算子".

- **C001 vs C002 vs C003 三窗 ablation 结论 (T001 完整测绘)**: alpha_surv 单调衰减 0.42→0.37→0.36 (60d→120d→250d), ic_oos 平稳 -0.054→-0.049→-0.041, ls_t 衰减 -6.19→-4.76→-3.41. **窗口越长 path memory vol_20d 累积越深 → alpha 衰减**. 与 b074 T007 F024 atom × window plateau (0.91-0.97 corr 高度自相关) 对照 — 本方向是另一种 window-ablation 失败模式: 不是 plateau 而是 monotonic decay. **结论**: csi1000 daily IMom-equivalent 不存在 sweet spot 窗口, 任何 N>20 都被 path-memory vol_20d 吸收.

- **C002 vs C004 head-to-head (raw Sum vs vol-normalized Sum/Std at 120d)**: alpha_surv 0.373 vs 0.332 — vol-normalize 反而恶化 0.04. 机制: 分母 Std(ε,120) 是 residual 的时序 std, 与 cross-section vol_20d basis 强相关, 除以高 vol_20d-loaded 噪声放大 Barra 项相对 weight. paper Haitong-37 IR=2.04 的高 Sharpe 在月频 stable estimate 下成立, 日频 120d Std 仍在 vol_20d basis 强吸收范围 — sampling frequency 不变换 paper IR 失效. **paper transferability 第 N 例**: 日频降阶不仅 magnitude 衰减 + 方向反号, 还有 statistical estimator 失效 (vol-normalize 在 weekly/monthly 是 risk adjustment, 在 daily 是 Barra basis 放大器).

- **C005 是本批"形式独立性最强但 alpha 实质最弱"特例**: alpha_surv=1.054 + max_corr=0.15 LOW (整批最低) — 看似完美 hot fire 候选, 但 ls_t=-0.28 信号 ~zero + mono_oos=-0.20 collapse + ic_oos=-0.013 接近零. **不达 reserve fire 门槛**: lessons.md 已升格 reserve fire 4 要件 (max_corr<0.30 + alpha_surv≥0.40 + sign_consistency=1.0 + ls_t/ic 至少 borderline-strong). C005 满足前 3 (max_corr 0.15 / alpha_surv 1.05 / sign_consistent), **第 4 个 ls_t=-0.28 太弱**. **alpha_survival > 1.0 单边不足律第 5 次实证** (b072 C005 / b086 C001 / b087 C001 / b088 C001+C005 / 本批 C005). 该律累计跨方向证据 ≥5 次, 应 Phase 5 consolidation 升格 lessons "Rank-Order ≠ Tradable Alpha" 段子律: **"alpha_survival > 1.0 + max_corr < 0.30 LOW + sign_consistency=1.0 三立完美 form 独立性时, 仍必须 ls_t ≥ 1.5 或 incr_ic > 0 至少一项才可 reserve, 单纯 form 独立 ≠ alpha 实质."**

- **海通-37 paper 整体证伪深度归因**: 论文 csi500 monthly IMom = N月 FF3 残差 Sum/Std → RankIC 3.98% IR=2.04. 本批 csi1000 daily 6/6 reject 揭示 4 层独立失效:
  1. **方向反号** (paper momentum → csi1000 mean-reversion): cumulative residual 在 csi1000 daily 上 high → 后续 NEG, 与 paper 反向. paper 的 momentum effect 在 A 股 csi1000 通过日频测试**完全反号**.
  2. **Frequency mismatch** (monthly → daily path memory 律): paper monthly bar 的 Barra residualization 是 cross-month residual sequence 累加, csi1000 daily 是 cross-day, sampling frequency 不变换 path-memory β shift 律.
  3. **Universe weakness** (paper csi500 → csi1000): paper 自报"中证 800 以外" IC 仅 1.67% (vs 沪深 300 4.56%) — csi1000 是 paper 已知最弱 universe, 加上 frequency mismatch 双重折扣.
  4. **Library overlap** (csi1000 admitted F027 multi_ma_reversion 已捕获 mean-reversion 几何): incr_ic NEG 律 — Barra-residual basis 之外的库内 non-Barra 因子已捕获 cross-section mean-reversion 同质 alpha.
  
  **paper transferability 律第 4 个独立证据** (与海通-37 同律的 Chaikin/AD/PVT/PE-PB papers 已升格 lessons round 73): **"paper monthly/weekly large-cap → csi1000 daily 默认双失败 (方向反号 + 量级衰减), 即使 form 独立性强 (alpha_surv ≥1.0) 仍被 csi1000 admitted library 内非-Barra 几何 capture"**.

- **跨方向 zero-admit streak 升至 4 (b086-b088 + b089)**: rounds_since_last_consolidation=0 (round 73 刚做 consolidation). 但 active_directions=22 ≥ 20 (consolidation 触发条件 #2 已立) + 跨方向 zero-admit streak=4 + 多方向 dead/saturated 累积 (overnight_intraday_split saturated / range_structure dead / signed_money_flow_oscillator dead / **本批后 idiosyncratic_momentum_residual dead**). consolidation_trigger 信号充分.

- **MT 预算推进**: direction_candidates 0 → 6 (本方向首批, dead 后不再投入); cumulative 492 → 498. bucket `medium` (search_adjusted=medium, family≈0.97 接近 saturated cluster ceiling, direction=0.0 新方向余量, exposure=1.0).

## Thread 进展

> [!failure]+ T001 raw cumulative residual return 60/120/250d ablation [[directions/idiosyncratic_momentum_residual#T001]] — `[✗ DISPROVEN batch_089]`
> reject 3 (C001 60d / C002 120d / C003 250d). T001 thread 关键问题完整回答:
> - **N 日累积残差是否 incremental over F004 单日切片**: 否. 三窗 incr_ic 全 NEG (-0.018/-0.015/-0.011), max_corr 反向归簇到库内 mean-reversion 几何 (F027 multi_ma_reversion / F002 pb_amount_ratio) 而非 F004 自身 (corr<0.02@F004 几何独立但 alpha 不独立).
> - **最优窗口在哪一档**: 不存在 sweet spot. alpha_surv 60d→120d→250d 单调衰减 0.42→0.37→0.36, 任何 N>20 path-memory vol_20d 吸收主导.
> - **方向是 momentum 还是 mean-reversion**: csi1000 daily 上**反向有效** mean-reversion. paper Haitong-37 momentum 假设方向反号.
> 
> Thread 状态: **DISPROVEN**. **机制结论**: T001 path-integral raw form 在 csi1000 daily 上 (a) 反向, (b) Barra basis 累积吸收, (c) 库内 non-Barra mean-reversion 几何 capture. 三立失败.

> [!failure]+ T002 vol-normalized Sum/Std 120d (paper strict) [[directions/idiosyncratic_momentum_residual#T002]] — `[✗ DISPROVEN batch_089]`
> reject 1 (C004). T002 关键问题回答:
> - **vol-normalization 是否是 paper IR=2.04 的结构性配方**: 否. C004 alpha_surv=0.332 vs C002 raw=0.373, vol-normalize 反而恶化. 分母 Std(ε,120) 共线于 vol_20d basis, 除以噪声放大 Barra 项. paper monthly bar 下 Std 是 stable estimate, daily 120d Std 仍在 vol_20d basis 吸收范围.
> 
> Thread 状态: **DISPROVEN**. **机制结论**: paper IR 配方在 csi1000 daily 不仅不救 alpha 反而恶化. sampling frequency 决定 estimator alpha 性质.

> [!failure]+ T003 rank-diff path-integral vs raw cumulative return [[directions/idiosyncratic_momentum_residual#T003]] — `[✗ DISPROVEN batch_089]`
> reject 1 (C005). T003 关键问题回答:
> - **rank-diff × residual paradigm 能否突破 T014 disprove 4 律 (with path-integral LHS)**: 否. C005 alpha_surv=1.054 form-independent + max_corr=0.15 LOW 完美 form 独立, 但 **ls_t=-0.28 + mono_oos=-0.20 + ic_oos=-0.013 信号实质几乎不存在**. T014 4 律对 path-integral LHS 同样 holds.
> - **path-integral LHS 与 point-statistic LHS 是否同律**: 是. cumulative residual rank ≈ cumulative raw rank (csi1000 daily styles 解释力弱), rank-diff 接近零噪音.
> 
> Thread 状态: **DISPROVEN**. **机制结论**: rank-diff salvage 在 csi1000 daily 上对任何 LHS 同律失败 (T014 + T003 双实证). **alpha_survival > 1.0 单边不足律第 5 次实证**.

> [!failure]+ T004 low-IVOL gated cumulative residual [[directions/idiosyncratic_momentum_residual#T004]] — `[✗ DISPROVEN batch_089]`
> reject 1 (C006). T004 关键问题回答:
> - **vol_20d 是否真已被 barra residualization 剥离干净**: 否. cumulative sum form 重累积 path-memory vol exposure (C001-C004 dom=vol_20d 直证), gating 0/1 mask 让 metric 退化但 incr_ic 仍 NEG (库 overlap 不破).
> - **IVOL gating 是否提供独立 alpha**: 否. ls_t 从 C001 -6.19 衰减到 C006 -1.58 (信号 strength 不足), max_corr=0.30@F021 仍 borderline.
> 
> Thread 状态: **DISPROVEN**. **机制结论**: vol_20d path memory 是 cross-section 结构性律, 不可通过 LHS 0/1 mask 简单切除. **重要 lesson**: F004 单日残差 admit + 本批 6/6 path-integral reject 对照 → **Barra residualization 单步线性算子有效, N-day 累积/path-integral 形式无效**, 律边界比 P004 vol_20d 律已知"non-linear absorption" 更深一层 (path memory β-shift).

## 方向级反思

本方向 round 1 (b089, 首批) 兑现率 0/6 admit + 0/6 reserve, 与 b084-b088 形成**跨方向连续 4 batch zero-admit** 模式. 主要发现:

1. **P004 律深度扩展实证 (升格证据强, 律边界从 single-step 算子扩展到 path-integral)**: F004 单日 Barra-residual admit (alpha_surv=1.41, dom_style 已剥) ↔ 本批 N-day cumulative residual 6/6 reject (alpha_surv 0.33-0.42 全衰减, dom=vol_20d 全恢复 exposure 19.6-23.2). **直接证据**: Barra cross-sectional residualization 是 single-step 线性算子, path-memory β shift 让 cumulative form 重累积 vol_20d basis 暴露. 应 Phase 5 consolidation 升格 lessons.md "P004 vol_20d 结构性吸收律" 段子律: **"Barra residualization 是 single-step 线性算子, 对 single-day ε admit-able (F004 已 admit), 但 N-day path-integral form (Sum/Mean/Sum-over-Std/rank-diff/IVOL-gated 任何累积) 在 csi1000 daily 上 dom_style 全部恢复 = vol_20d, alpha_surv 衰减至 floor — path-memory β-shift 是 P004 律的更深层次, 比已知 'non-linear vol_20d absorption' (Linear OLS Polynomial 不破律) 更结构性. 实操律: cumulative residual form 默认 reject; 若需 isolate residual alpha, 应 stay at single-step (F004 模式) + 用 multi-day evaluation horizon 替代 multi-day LHS aggregation."**

2. **海通-37 paper transferability 4 层独立失效律 (paper transfer 律新例)**: csi500 monthly RankIC 3.98% IR=2.04 → csi1000 daily 6/6 reject. 4 层独立机制: (a) **方向反号** (momentum → mean-reversion, csi1000 daily 全反相); (b) **frequency mismatch** (monthly → daily path memory 律不对称); (c) **universe weakness** (paper 已自承 csi500 大盘到 csi1000 小盘 IC 衰减 2.4x); (d) **library overlap** (csi1000 admitted non-Barra mean-reversion 几何 F027 已 capture). 应 Phase 5 升格 lessons.md "Paper Transferability" 段第 N 条 (与 b088 Chaikin / b069-b072 PIT/TTM paper 同律): **"paper monthly/weekly cumulative residual / IMom / signed-money-flow / TTM-PIT class signal → csi1000 daily 默认 4 层独立失效, 即使 form 独立性极强 (alpha_surv ≥ 1.0 / max_corr ≤ 0.20 LOW) 仍被 csi1000 admitted library 内非-Barra 几何 capture. paper transferability 4 律失败模式: 方向反号 + 频率失效 + universe 衰减 + library overlap 任意 1 条立则 paper 信号默认 reject."**

3. **alpha_survival > 1.0 单边不足律第 5 次实证 (跨 5 batch 升格证据已 sufficient)**: C005 alpha_surv=1.054 + max_corr=0.15 LOW + sign_consistency=1.0 三立完美 form 独立, 但 ls_t=-0.28 信号 ~zero. 累计 b072 C006 / b086 C001 / b087 C001 / b088 C001+C005 / 本批 C005 = **5 次跨方向独立证据**. 应 Phase 5 升格 lessons.md "Rank-Order ≠ Tradable Alpha" 段子律: **"alpha_survival > 1.0 + max_corr < 0.30 LOW + sign_consistency=1.0 三立 form 独立性时, 仍须 ls_t ≥ 1.5 或 incr_ic > 0 至少一项才可 reserve, 否则默认 reject. 机理: form 独立 (vs Barra basis / vs admitted library) 是 necessary 不是 sufficient — 信号 strength (ls_t / ic_oos) 是 admit/reserve 的 second necessary gate."**

4. **方向状态翻 dead 强建议**: idiosyncratic_momentum_residual round 1 (首批) 0/6 admit + 0/6 reserve + 4/4 测试子假设 (T001 三窗 + T002 vol-normalize + T003 rank-diff + T004 IVOL gating) 全部 DISPROVEN. **建议方向状态从 `exploring` 直接翻 `dead`**: 理由 (a) 所有可能的 form 维度 (raw 累积 / vol-normalize / rank-diff / gating 4 大变体) 全 reject, 无未测子路径; (b) Barra residualization 限制是 P004 律深层 (单步 vs path-integral), 非工艺问题; (c) paper transferability 4 层失效不可救药.

5. **触发 consolidation_trigger**: active_directions=22 ≥ 20 (条件 #2 立) + cross-direction zero-admit streak=4 (b086-b089). 优先升格 3 条 lessons (本批 narrative 已生成证据): (i) P004 律 path-integral 扩展; (ii) paper transfer 4 层失效律新例; (iii) alpha_surv > 1.0 单边不足律 (b072+b086+b087+b088+本批 = 5 次实证). **建议下轮先 consolidate 再开新方向**.

**Edge 评估**: 本方向 alpha edge 直接 dead — 不存在借记 reserve 火种 (max_corr LOW 但 ls_t 太弱), 不存在窗口/RHS swap 复活路径 (4 子假设全 dead 形式同质). idiosyncratic_momentum_residual 应在本批后立即翻 dead, 不开 batch_090.

**下一步建议**:
- (a) **本方向翻 dead**: 不再投入. Narrative log 记 "DISPROVEN at batch_089 by H1/H2/H3/H4 全证伪 + P004 律深层扩展 (path memory β-shift) + paper transferability 4 层失效".
- (b) **触发 consolidation** (active_directions=22 + zero_admit_streak=4): 优先升格 3 条 lessons 上述 narrative 已写明.
- (c) **下批 direction**: consolidation 完成后由 LLM 重选; 候选: (i) 等 lessons 升格后基于 frontier_priority refresh 重选; (ii) 切换到尚未投入的 paper-vetted exploring (e.g. **price_conditional_amplitude** [新探 round 89, 0/0]). 主切换不在 subagent context 内, 由 orchestrator 决定.

**Calibration trigger 检查** (本批 0 admit + 0 reserve):
- 错杀 flag 跨候选反思: 无 — C001-C004 dom=vol_20d 律边界扩展 + alpha_surv floor 真接近 (0.33-0.42), C005-C006 ls_t 太弱, 不存在错杀候选.
- 连续零 admit 警戒: 跨方向 streak=4 (b086-b089). 累计 reserve 满足"max_lib_corr<0.30 + incremental_ic>0.010"? 本批 0 reserve, b087 C001 max_corr=0.45 不满足 max_corr<0.30; b088 C002 max_corr=0.36 ic_oos=-0.010 不满足 strength; b086 C001 reserve max_corr 也 borderline. **跨 batch 累计 reserves 全 borderline cluster 不满足 LOW 库独立条件, 无错杀**. 不触发 calibration_trigger.
- Reserve 积压 > 40%: 累计 reserve count 当前 ~3-4 跨 b086/b087/b080, judged 88+ batch, 比例 << 40%. 不触发.
- 悖论复现: vol_20d-low-but-also-paradoxical 不立, 不触发.

**Calibration verdict**: **不触发 calibration**. 本批 reject 全部为真证伪 (alpha_surv FAIL + library reducer + ls_t 弱) 不存在错杀, P004 律深层扩展是真饱和不是阈值过严.

**Consolidation trigger**: **触发** (active_directions=22 ≥ 20 + zero_admit_streak=4 + 3 条强证据 lesson 待升格).
