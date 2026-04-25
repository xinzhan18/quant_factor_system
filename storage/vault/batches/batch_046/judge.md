---
batch_id: batch_046
direction: microstructure_illiquidity
judged_at: 2026-04-25T03:05:00Z
candidates:
  - {candidate_id: C001, verdict: reject}
  - {candidate_id: C002, verdict: reject}
  - {candidate_id: C003, verdict: admit, factor_name: amihud_cv_rank_diff_20}
  - {candidate_id: C004, verdict: reject}
  - {candidate_id: C005, verdict: reject}
  - {candidate_id: C006, verdict: reserve}
batch_summary: {total: 6, admit: 1, reserve: 1, reject: 4}
admit_count: 1
reserve_count: 1
reject_count: 4
candidate_count: 6
mt_bucket: high
---

# batch_046 Judge Summary

> [!abstract]+ [[directions/microstructure_illiquidity]] · 6 candidates
> ✅ **admit=1** (C003 → amihud_cv_rank_diff_20) · ⏸ **reserve=1** (C006) · ❌ **reject=4**
> **核心发现**: **方向 saturated 状态被正确结构的新候选部分推翻**——C003 rank-diff symmetric interaction (CsRank(Amihud) − CsRank(amount_CV)) 在 F012 之外开辟独立 DSL 子空间 (max_corr=0.655 < 0.70, incr_ic=0.031, ls_t=6.63, 9 年全正, mono_oos=1.0 双端完美, alpha_surv=0.658 比 F012 的 0.443 高 48%)，兑现 direction 复活条件 (b)。
> **方向终结**: sign-conditional Amihud (C001/C002, up/down 对偶 max_corr 0.942/0.918) 在 20d 窗口几乎完全对称——sign-asymmetry 在 csi1000 日频被窗口均值吸收。
> **设计范式升格**: C004 证伪给 C003 成功机制提供硬证据——**rank-diff 结构成功依赖两端 signal family scale-free**（Std 失败 vs CV 成功，corr差 0.28）。
> **MT Budget**: cumulative 234 → **240** · direction 12 → **18** · bucket `high` (search_adjusted medium, C003 原档 strong 保留)

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | 🔴 hard_gate | max_corr=**0.942**@F012 | up-day Amihud 保序合并 | [[batches/batch_046/candidates/C001]] |
| C002 | ❌ reject | 🔴 hard_gate | max_corr=**0.918**@F012 | down-day Amihud 同 C001 对偶 | [[batches/batch_046/candidates/C002]] |
| C003 | ✅ admit | 🟢·🟢·🟡·🟡·🟢 | IC=+0.054 mono=+1.0 ls_t=+6.63 incr=+0.031 max_corr=0.655 | rank-diff symmetric interaction 兑现 | [[batches/batch_046/candidates/C003]] · [[factors/F015]] · F{id}@Phase4 |
| C004 | ❌ reject | 🔴 hard_gate | max_corr=**0.935**@F012 | Std (scale-dep) 破坏 rank-diff 范式 | [[batches/batch_046/candidates/C004]] |
| C005 | ❌ reject | 🔴 hard_gate | max_corr=**1.000**@F012 | SignedPower 0.5 保序 (lesson 二证) | [[batches/batch_046/candidates/C005]] |
| C006 | ⏸ reserve | 🟢·🔴·🔴·🟢·🟢 | IC=-0.042 alpha_surv=0.17 incr=**-0.031** max_corr=0.16 sign_c=1.0 | signed illiq 独立源但 CP04 severe | [[batches/batch_046/candidates/C006]] |

## 跨候选对比

- **C001/C002 sign-conditional 对偶结题**: max_corr 仅差 0.024 (0.942 vs 0.918)，**Amihud up/down 在 20d 平均下近完美对称**。A 股散户恐慌抛售 asymmetry 假设在日度数据 20d 窗口层级被平均化消除。升格教训: day-level sign gate + window mean aggregation 的组合会抹平 asymmetry——复活需 ≤ 5d 短窗 或 quantile-based asymmetry。

- **C003 vs C004 — rank-diff 设计范式的硬证据**: 同为 CsRank 差结构，C003 (Amihud vs amount_CV) 通过 (corr=0.655), C004 (Amihud vs Std_amount) 失败 (corr=0.935)。两者唯一差别: amount dispersion 端用 CV (scale-free) 还是 Std (scale-dep)。**结论**: rank-diff 结构 alpha 源于两端 signal family 都 **scale-invariant**；若一端 scale-dependent 会退化为主因子近重复。推广到其他方向: 设计 CsRank 差结构时两端必须都是 ratio/CV/correlation 等 scale-free 量。

- **C005 延续 batch_031 C004 保序教训**: SignedPower(F012, 0.5) max_corr=1.000, 与 CsZscore(F012)=1.000 形成"rank-preserving monotonic 变换对单因子零信息增量"第二个独立证据。lesson 升格建议: 把 DSL 层 `{Linear, SignedPower(p>0), Sigmoid, Tanh, Exp, Softmax}` 对已 admit 因子的单元包装 **hard_gate 预拦截**，省试错 slot。

- **C006 signed illiquidity proxy — 独立但弱**: max_corr=0.16 本批最低 + 9 年全负 sign_consistency=1.0 的 rank-order 真实，但 alpha_surv=0.17 严重 + signed incremental_ic=-0.031 (admit 反稀释库)。属 "真 signal 但 alpha 不达标 + 库稀释" 象限，归 reserve 负参考。

- **方向兑现**: 1 admit / 6 candidates, admit 命中率 17%；但 **C003 机制质量极高**——alpha_surv 比 F012 admit 时 (0.443) 高 48%；9 年全正；mono_oos=1.0；IC 随 horizon 单调递增至 20d=0.121 —— rank-diff alpha 质量优于 F012 raw level。

## Thread 进展

> [!success]+ T005 [[directions/microstructure_illiquidity#T005]] — `[✗ PARTIAL-DISPROVEN batch_046]`
> **sign-conditional Amihud (up/down 分离)**: C001/C002 对偶 max_corr 0.942/0.918 → 日频 20d 窗口对称性几乎完美。
> **Kyle-lambda signed turnover illiq (C006)**: 库空间独立 (max_corr=0.16) + 9 年同号，但 alpha_surv=0.17 + signed neg incr_ic → reserve 负参考。
> **结论**: T005 signed illiquidity 子空间 DSL 层 20d 窗口**本质为 symmetric space**; short-window / quantile-asymmetry / 更强 residualize 未测 → thread 保留 ACTIVE 等待 minute-bar 或 5d-window 变体。

> [!success]+ T006 [[directions/microstructure_illiquidity#T006]] — `[✓ ANSWERED batch_046]`
> **rank-diff symmetric interaction**: C003 admit → **amihud_cv_rank_diff_20** (Phase 4 F{id} 分配)。CsRank(Amihud) − CsRank(amount_CV) 兑现 direction 复活条件 (b)。C004 证伪提供设计范式: 两端 scale-invariance 是必要条件。Thread 第一子问题结题，后续可沿 "rank-diff 扩展"（vs F002, vs F003 等不同 signal family）继续探索。

## 方向级反思

`microstructure_illiquidity` 方向从 `saturated` 转 **revived-productive**：rank-diff 结构 (T006) 在被正式宣告 saturated 2 批后找到有效子空间，证实 saturated 定性不是**永久结论**，只是对当时探索范式的局部最优陈述。admit F013 → amihud_cv_rank_diff_20 是库第 14 个独立因子，max_corr 0.655 接近阈上限但 incremental_ic 0.031 证明库增值；9 年全正 + mono_oos=1.0 + ls_t=6.63 OOS 让质量档位 strong。

**设计范式升格到 lessons 候选**（Phase 5 consolidation 待确认）:
1. **"rank-diff 符合率 range"**: rank-diff 两端 **scale-invariant**（CV, ratio, correlation）时有效；scale-dependent（Std, Mean, 绝对 level）时退化为主因子近重复。C003/C004 对照是首个硬证据。
2. **"sign-conditional 在 20d 窗口保序"**: day-level If gate + 20d mean aggregation 的组合近完全抹平 sign asymmetry。未来 sign-conditional 设计需 ≤ 5d 窗或 quantile-based 非 mean 聚合。

**方向操作**: 本批 admit 后从 `saturated` 转回 `productive`（或 `revived`）;  priority 从 `low` 回升 `medium`；rounds = 3（batch_030 / batch_031 / batch_046）；admits = 2 (F012, F013-to-be)。T006 ANSWERED; T005 保留 ACTIVE；下轮可开 T007 "rank-diff 扩展到其他 signal family" 探索。

**Calibration**: 无错杀侦测——C006 reserve 非错杀（alpha_surv 真 poor + signed neg incr），reject 4 个均 hard_gate 近重复或保序 proof。C003 admit 符合所有阈值。**本批破除 5 批零 admit 警戒线**，cockpit zero_admit_streak 重置为 0。无需 calibration。

**MT budget**: cumulative 234 → 240, direction 12 → 18, bucket `high`（search_adjusted 0.9 → 0.54 降至 medium，C003 strong 档无需进一步降档）。
