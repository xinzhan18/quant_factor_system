---
batch_id: batch_054
direction: barra_residual_alpha
judged_at: 2026-04-25T09:00:00Z
candidates:
  - {candidate_id: C001, verdict: reject}
  - {candidate_id: C002, verdict: reject}
  - {candidate_id: C003, verdict: reject}
  - {candidate_id: C004, verdict: reject}
  - {candidate_id: C005, verdict: reject}
  - {candidate_id: C006, verdict: reject}
batch_summary: {total: 6, admit: 0, reserve: 0, reject: 6}
admit_count: 0
reserve_count: 0
reject_count: 6
candidate_count: 6
mt_bucket: high
---

# batch_054 Judge Summary

> [!abstract]+ batch_054 · [[directions/barra_residual_alpha]] · 6 candidates
> ❌ **admit=0** · ⏸ **reserve=0** · ❌ **reject=6** (6/6 hard_gate fail) — **rank-diff × residual paradigm 在数据契约层 + 信号设计层双重证伪**。
>
> **核心发现**（4 条独立机制）：
> 1. **residual + 20d rolling 在 csi1000 系统性 coverage ≈ 0.71** — 5/5 可计算候选 (C002-C006) 全部触发 coverage<0.80 hard_gate；residual base 覆盖率 99% 但 rolling Std/Sum/EMA 后因 (a) 残差 NaN 传播 + (b) 上市日异质性 + (c) min_periods 要求 ≥10 点，coverage 暴跌 28pp。**这是结构性数据契约边界，与信号设计无关。**
> 2. **T003 (loader 不响应 Python REQUIRED_FIELDS) 二次复现** — C001 missing $turnover_rate（与 [[batches/batch_015/candidates/C002|b015 C002]] missing $high/$low 同律），9 批之后第二次相同失败 → 升格 lessons.md 候选。
> 3. **残差 higher-moment regime sensitivity 第三次跨方向复现** — C002 mono_sign_flip(IS=-0.80→OOS=+0.70) + C003 sign_flip(IS=-0.016→OOS=+0.011) 同律 [[batches/batch_052/candidates/C001|b052 C001]] (PE Std) + [[batches/batch_053/candidates/C001|b053 C001]] (signed body-pos Std)。
> 4. **残差 SNR/momentum 类信号在日频 IC < 0.01 量级 noise** — C004 (autocorr) IC=0.006 + C006 (directional efficiency) IC=0.0003 双双 < 0.008 阈值；残差 path coherence/persistence 类几何 statistic 不能再生 alpha（残差已剥离 alpha-bearing component）。
>
> **方向状态决策**：维持 `saturated` (不退化为 `dead`)：本批揭示了**4 条新结构教训**——residual 数据契约层 + 残差 higher-moment regime / 残差路径噪声等独立机制——知识价值已交付。**T014 thread (rank-diff × residual paradigm) 在数据契约层失败，T002 saturated 框架进一步加固**。
>
> **MT Budget**: cumulative 282 → **288** · direction 21 → **27** · bucket `high` (search_adjusted → medium) · 本批 low=0 / med=0 / high=6

## 候选一览

| ID | Verdict | 档位 (CP1) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | hard_gate | compute_error: market_df missing $turnover_rate | T003 (loader 不响应 REQUIRED_FIELDS) 二次复现，9 批之后跨方向同律失败 | [[batches/batch_054/candidates/C001]] |
| C002 | ❌ reject | hard_gate | coverage=0.709 + mono_sign_flip(-0.80→+0.70) | 残差 higher-moment regime 翻号 + residual+rolling 系统性 coverage 不达 | [[batches/batch_054/candidates/C002]] |
| C003 | ❌ reject | hard_gate | coverage=0.708 + sign_flip(-0.016→+0.011) + oos_decay=-0.644 | 残差短窗 cumsum 在 train (反转) vs validation (momentum) regime 完全反号 | [[batches/batch_054/candidates/C003]] |
| C004 | ❌ reject | hard_gate | coverage=0.717 + ic_oos_too_low(\|·\|=0.006) | 残差 lag-1 autocorr 在日频 csi1000 IC < 0.01 量级 noise floor | [[batches/batch_054/candidates/C004]] |
| C005 | ❌ reject | hard_gate | coverage=0.725 (单闸) | 信号本身良好 (ICIR_oos=-0.169 + alpha_surv=1.57 + style_r²=0.024 极清洁) 但被 coverage gate KO | [[batches/batch_054/candidates/C005]] |
| C006 | ❌ reject | hard_gate | coverage=0.717 + ic_oos_too_low(\|·\|=0.0003) | 残差 directional efficiency 完全 noise (\|sum\|/sum_abs 几何 statistic 不能再生 alpha) | [[batches/batch_054/candidates/C006]] |

## 跨候选对比

**LHS 多元化结构 (本批 6 LHS 全唯一)**:
- C001: CsRank(Mean(\|residual\|, 20)) — 残差 dispersion 水平
- C002: CsRank(Std(residual_ret, 20)) — 残差 second-moment
- C003: CsRank(Sum(residual_ret, 5)) — 残差短窗动量
- C004: residual lag-1 autocorr_20 — 残差时序结构
- C005: EMA(res,5) − EMA(res,20) — 残差多周期 decay 差
- C006: \|Sum(res,20)\| / Sum(\|res\|,20) — 残差 SNR

**RHS 多元化结构 (rank-diff 候选)**:
- C001: CsRank(Mean($turnover_rate, 20)) — 流动性原子
- C002: CsRank(Mean($amount, 60)) — amount 长窗
- C003: CsRank(Mean(Std($close, 5), 60)) — RV_60 (b051 admit C002 RHS)
- C004/C005/C006: 无 RHS（pure residual-only 路径）

**关键失败模式分类**:

1. **residual + rolling 数据契约层 fail (5/5 可计算候选 coverage<0.80)**: 这是**新发现**——F004 admit (batch_012) 时 coverage=0.999 因 F004 是 residual 本身（无后续 rolling），本批所有候选都对 residual 做 rolling Std/Sum/EMA → coverage 暴跌至 0.71-0.73。机理：(a) cross-sectional Barra residual 已有 ~1% NaN（style 缺失传播）；(b) rolling 算子 min_periods≥10 要求每只标的连续历史；(c) csi1000 上市日异质性；(d) 三者复合后早期日期 ~30% 标的 NaN，全期均值 coverage = 0.71 << 0.80。**升格 lessons.md 候选**："Python residual + rolling 在 csi1000 系统性 coverage ≈ 0.71，hard_gate 0.80 阈值与 residual paradigm 结构性不兼容"。

2. **Python factor 数据契约缺口二次复现 (C001)**: T003 thread 揭示的"loader 忽视 Python factor REQUIRED_FIELDS 声明"在 b015 C002 之后第二次独立触发——本 C001 missing $turnover_rate。**T003 thread 推进到 [已二次复现 待系统修复]**，升格 lessons.md "Python factor 数据契约 hard_gate 候选" Promising Unexplored 反向条目。

3. **残差 higher-moment regime sensitivity 第三次跨方向复现 (C002 + C003)**: C002 mono_sign_flip + C003 sign_flip 都在 train/validation 翻号——同律 b052 C001 (PE Std)、b053 C001 (signed body-pos Std)。**3 次独立确认 → 升格 lessons.md**: "higher-moment LHS（Std/Var/cumsum 类二阶聚合）在 train (低利率) vs validation (利率上行) regime 系统性翻号——这是跨方向（fundamental/intraday/residual）三层独立证实的硬律"。

4. **残差路径几何 statistic 在日频是 noise (C004 + C006)**: residual autocorr 和 directional efficiency 都 IC magnitude < 0.01。机理：残差已剥离 alpha-bearing component，对其再做 path coherence/persistence 类 transformation 不能再生 alpha。**与 [[directions/barra_residual_alpha#Lessons]] 第 1 条"时序平滑/标准化不改 cross-sectional rank"互补**：本批进一步——残差时序 statistic 本身在 IC magnitude 上 sub-threshold。

**与 b052/b053 反思对照**:
- b052 揭示"基本面 higher-moment regime sign_flip" + "factor-anchored cluster RHS 动态律 (F002 anchor)" + "compound moment LHS over-fit"
- b053 揭示"F020 anti-anchor cluster" + "F012 anchored RHS 窗口家族 cluster" + "vol_20d 在 intraday family 不可剥离"
- b054 在 residual family 揭示**4 条独立机制**：(1) residual+rolling coverage 数据契约层 + (2) loader REQUIRED_FIELDS 缺口 + (3) 残差 higher-moment regime sensitivity (跨方向三层) + (4) 残差路径几何 noise
- **rank-diff 范式三次连续中断 (b052 + b053 + b054)** 共揭示 **9-10 条新限制律**：rank-diff 不是万能钥匙的边界正在迅速被定义清楚。**Phase 5 consolidation 升格 lessons.md 的硬证据进一步累积**。

**Style 聚合**: 6 候选 dominant_style 全 vol_20d。残差化未能剥离 vol_20d cluster——验证 [[directions/barra_residual_alpha#T002]] 已 promote 的 lesson"vol_20d 主导残差空间"在残差 rolling statistic 上仍成立（不仅 residual 本身）。

**MT 预算**: direction_candidates 21 → 27, 远低于 70 上限。本方向 7 轮 (含本批) 仅 1 admit (F004)，**reserve 累计 0 + 本批也 0 reserve**，MT 预算空闲不构成放宽阈值依据。

## Calibration Check (Phase 3.5)

四个 calibration trigger 检查:

1. ❌ **错杀 flag**: 本批最强候选 C005（信号本身良好：ICIR_oos=-0.169 + alpha_surv=1.57 + style_r²=0.024 极清洁 + max_corr=0.441@F008），但 coverage=0.725 单闸 fail——coverage 是 hard_gate (data integrity 物理边界)，**lessons.md 明确禁止放宽 hard_gate**（"不放宽 hard_gate (coverage / sign_flip / ic_oos_min / mono_flip / near_duplicate) — CP01 硬闸代表数据质量 + 结构完整性的物理边界"）。**不构成错杀** —— 是结构性数据契约层失败，不能通过阈值调整解决。
2. ❌ **连续零 admit**: 本方向最近 3 batches admit: b013=1, b014=0, b015=0, b054=0 → 连续 admit=0 共 3 次 (b014/b015/b054)。**条件之一达到**，但同时要求 reserve ≥1 满足"max_corr<0.30 + incremental_ic>0.010"——本批 reserve=0 + C005 incr_ic=-0.019 (库减值)、C004 max_corr=0.117 但 incr_ic=0.003 (微增值)，不满足"库空间独立"完整 signature。**未触发**。
3. ❌ **Reserve 积压**: 本方向累计 reserve 数 = 1 (b012 C003) / judged 27 = 3.7% << 40%。
4. ❌ **悖论复现**: 本批新现象（residual+rolling 系统性 coverage<0.80）是**结构性数据契约**而非反直觉 metric 组合，不构成"低 style_r² + 低 alpha_survival" 类悖论。

→ **calibration_trigger = false**。本批结果是真实的"residual + rolling 数据契约层失败 + 信号 magnitude 不足"，不是"阈值过严"。Phase 4 archive 正常进行。

## Thread 进展

> [!failure]+ T014 [[directions/barra_residual_alpha#T014]] — `[✗ DISPROVEN batch_054]`
> rank-diff geometry × residual signals paradigm（barra_residual_alpha 复活路径）在本批 6 候选完整投放后宣告 **DISPROVEN**。四条独立机制揭示：
>
> 1. **数据契约层结构性 coverage<0.80**: residual + rolling 在 csi1000 系统性 coverage=0.71-0.73 (5/5 候选), 与 hard_gate 0.80 阈值结构性不兼容。这一层失败不能通过信号设计修复——必须 (a) 修改 loader 使 residual 不传播 NaN / (b) 改用 cross-sectional 算子代替 rolling 算子 / (c) 接受残差 base 信号（不做 rolling，但那就是 F004 本身）。
> 2. **Python factor 数据契约 (T003) 二次复现**: C001 missing $turnover_rate, 9 批之后第二次同律失败, **T003 升格为系统级修复优先级 high**.
> 3. **残差 higher-moment regime sensitivity (跨方向三次确认)**: 残差 Std/cumsum 在 train (低利率) vs validation (利率上行) 翻号——加上 b052/b053 的 fundamental + intraday family，**这是跨 3 大 family 独立证实的硬律**。
> 4. **残差路径几何 statistic 是 noise**: autocorr / directional efficiency 类信号 IC < 0.01 量级，残差已剥离 alpha-bearing component 后无法再生。
>
> **复活路径再次缩窄**：[[directions/barra_residual_alpha#Hypothesis|hypothesis 复活条件]] (a) 非 Barra style basis / (b) nonparametric residualization / (c) 与库非线性 ensemble 三条仍未尝试。**rank-diff × residual 路径 (T014) 已穷尽**。

> [!warning]+ T003 [[directions/barra_residual_alpha#T003]] — `[已二次复现 → 升格修复优先级 high]`
> Python factor REQUIRED_FIELDS loader 缺口在 C001 missing $turnover_rate 第二次独立触发（首次 b015 C002 missing $high/$low）。**T003 thread 中期方案推进至必须优先实施**: (a) Phase 1 freeze 静态 validate `set(REQUIRED_FIELDS) ⊆ load_market_data` 默认列；(b) load_market_data 接受 candidates union(REQUIRED_FIELDS) 动态扩列。

## 跨方向元教训 (Phase 5 consolidation 候选)

4 条新教训等待 Phase 5 升格 lessons.md:

1. **"Python residual + rolling 在 csi1000 系统性 coverage ≈ 0.71，hard_gate 0.80 阈值与该 paradigm 结构性不兼容"** — 5/5 可计算候选独立确认。**candidate to promote** → lessons.md "Structural Constraints" 新增 residual 类 factor 数据契约约束。
2. **"Python factor REQUIRED_FIELDS loader 缺口需 Phase 1 freeze 静态 validate / load_market_data 动态扩列"** — T003 二次复现 b015→b054。**candidate to promote** → lessons.md "Operator Registry" 或新增 "Python Factor Contract" 段落。
3. **"higher-moment LHS（Std/Var/cumsum 类二阶聚合）在 train/validation regime 系统性翻号——跨 3 大 family（fundamental/intraday/residual）独立确认"** — b052/b053/b054 三次独立。**candidate to promote** → lessons.md "Threshold Calibration" 段或新增 "Regime Sensitivity Pattern Library"。
4. **"残差 path coherence/persistence/SNR 类几何 statistic 不能再生 alpha (残差已剥离 alpha-bearing component)"** — C004 + C006 双例独立证伪。**candidate to promote** → lessons.md 与第 1 条"时序平滑/标准化不改 cross-sectional rank"合并扩展。

下批建议 (next_hint): zero_admit_streak 增至 **3** (b052/b053/b054)。**rounds_since_consolidation = 9 → 本批后达硬触发 10**。**强烈建议下批先 trigger Phase 5 consolidation**——累积 4 条 b052-b054 的新教训值得集中梳理。Consolidation 后再决定方向：(a) ohlc_temporal_aggregation / overnight_intraday_split / gap_acceptance_structure 三个 productive 方向延伸 admit；(b) 修复 T003 + residual coverage 后再启 barra_residual_alpha 完整 paradigm 测试。
