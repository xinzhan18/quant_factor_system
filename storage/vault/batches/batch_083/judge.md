---
batch_id: batch_083
direction: range_structure
judged_at: 2026-05-02T16:30:00Z
candidates:
  - {candidate_id: C001, verdict: reject}
  - {candidate_id: C002, verdict: reject}
  - {candidate_id: C003, verdict: reject}
  - {candidate_id: C004, verdict: reject}
  - {candidate_id: C005, verdict: reject}
  - {candidate_id: C006, verdict: reserve}
batch_summary: {total: 6, admit: 0, reserve: 1, reject: 5}
admit_count: 0
reject_count: 5
reserve_count: 1
candidate_count: 6
mt_bucket: high
---
# batch_083 Judge Summary

> [!abstract]+ batch_083 · [[directions/range_structure]] · 6 candidates
> ❌ **reject=5** (C001/C002/C003/C004/C005) · ⏸ **reserve=1** (C006) · ✅ **admit=0**
> **核心发现**: **P008 escape mechanism cross-direction test FAILS** — daily-resolution intraday range/structure × TsRank 60d 在 raw range magnitude (C001/C005) 与 outer Std-wrap (C004) 形式下完全不成立；P008 机制是 **atom-specific 而非 wrap-pattern-general**——仅适用于"位置/比例"几何 (F026 close position low-anchor + F025 shadow asymmetry midpoint)，不适用于 raw range magnitude。
> **MT Budget**: cumulative 456 → **462** · direction 30 → **36** · bucket `high`（已超容忍）· 本批 low=2 (C002/C006) / med=3 (C001/C004/C005) / high=0

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | 🟡·🟢·🟡·🔴·🟡 | ic=-0.037 ls_t=-3.43 incr=**-0.033** | strong stats 是 vol_20d Q5 一桨假象，与 F022 反号镜像；P008 不适 raw range/close | [[batches/batch_083/candidates/C001]] |
| C002 | ❌ reject | 🟡·🔴·🟡·🟡·🟡 | ic=-0.017 ls_t=-0.39 max_corr=0.65@F025 | weak CP03 + F025 退化 open-anchor 单边变体；几何不独立 | [[batches/batch_083/candidates/C002]] |
| C003 | ❌ reject | 🟡·🔴·🟠·🟢·🟡 | ic=+0.009 IS_ic=+0.0015 alpha_surv=0.33 | body/range 几何独立但 IS_ic≈0 + train_val_decay=5.75 揭示 OOS regime overfit | [[batches/batch_083/candidates/C003]] |
| C004 | ❌ reject | 🟡·🟢·🟡·🔴·🟡 | ic=-0.030 ls_t=-3.93 incr=**-0.017** | outer Std-wrap 反深陷 vol_20d (16.4 本批最高)；P008 mechanism break by 5d Std | [[batches/batch_083/candidates/C004]] |
| C005 | ❌ reject | 🟡·🟢·🟡·🔴·🟡 | ic=-0.038 ls_t=-3.61 incr=**-0.033** | 与 C001 数值完全相同——open vs close anchor 在 csi1000 cross-section 完全同源 (F005 共动律延伸验证) | [[batches/batch_083/candidates/C005]] |
| C006 | ⏸ reserve | 🟢·🟡·🟡·🟡·🟡 | ic=**+0.017** mono=+0.30 9yr-positive cum_mdd=-2.15 | 唯一 9 年正向 sign-consistent + cum_mdd 库内最浅，但 ls_t=+0.48 weak + max_corr=0.65@F025 cluster | [[batches/batch_083/candidates/C006]] |

## 跨候选对比

- **库 reducer 律第 9-11 次重现**：C001/C004/C005 三个 strong-stats 候选（IC/ICIR/ls_t 三项 strong）全部 **incremental_ic NEG** (-0.033 / -0.017 / -0.033)。strong 表面源于 vol_20d 单 style 主导（exp 12.4-16.4）+ Q5 一桨驱动。与库内 [[factors/F022]] (close-position-amount-accel rank-diff) 反号镜像 corr=-0.27 至 -0.30 + 与 [[factors/F001]] amount_cv 同号 corr=+0.18 至 +0.29 → 同一 vol-CV family 减值簇。**P006 library-reducer 律应用次数累积达 11 次** (b042 C005 / b043 C005-C006 / b045 C006 / b055 C001-C002-C003-C006 / b056 C003-C004 / b064 C003-C004 / b083 C001-C004-C005)，已稳定到可作为 hard_block 自动 reject criterion 的成熟阶段（max_corr<0.40 + incr_ic≤-0.010 + alpha_surv>0.80 → reject without LLM judgment）。

- **C001 ↔ C005 数值同源**: 两候选所有 OOS metric 在小数点 2 位以内一致 (incr_ic 都是 -0.033, vol_20d 12.45 vs 12.64, max_corr 0.27@F022 同, ic_by_year 9 年同模式)——**denominator anchor (open vs close) 在 csi1000 cross-section 完全无差异**。这是 F005 OHLC algebraic 共动律的延伸验证（原文针对 prev_close gap / OHLC4_mean，本批证实 daily open ≈ close 在 vol-orthogonal cross-section 上同源）。**升格 lessons 候选**：A 股 csi1000 daily 频率上 open / close anchor 选择对 cross-section ranking 信号无影响——下一批设计可直接舍去任一一个。

- **C002 ↔ C006 几何对称配对**: (H-O)/(H-L) + (O-L)/(H-L) = 1 严格几何约束，但实证 corr 远不到 -1（约 -0.5）——TsRank 60d wrap 把直接配对关系 break 掉。验证了 cross-direction 加工对几何配对的非保形性。两者中 C006 OOS IC=+0.017 strong 但 C002 OOS IC=-0.017 weak → **anchor 方向 (from-low vs from-high) 在 csi1000 上有信息含量差异**——open-from-low ratio 是稳定 alpha (9 年正)，open-from-high ratio 是反向 weak signal。

- **MT 预算推进**: cumulative 456→462；direction 30→36 已 high 档。range_structure 累积 8+1=9 rounds，admits=2 维持，本批 admit=0 + 1 reserve。

## Thread 进展

> [!note]+ T004 [[directions/range_structure#T004]] 🆕 — `[◉ ACTIVE]`（新建本批）
> P008 escape mechanism cross-direction test 第 1 轮 0 admit + 1 reserve + 5 reject。**关键发现**：P008 机制不可 wrap-pattern-generalize——raw range magnitude (C001/C005) + outer Std-wrap (C004) 全部 incremental_ic NEG 重新落入 vol-CV family；body/range (C003) 虽 style_r² clean 但 IS IC≈0 regime overfit；唯一 reserve (C006 open-to-low fraction) 9 年 sign-consistent 但 ls_t weak + max_corr=0.65@F025 cluster。**T004 round 2 必要性低**：除非有显著新机制（如 minute-bar resolution / Python escape hatch barra ortho），否则下批 0 admit → DISPROVEN + direction 转 dead。

> [!note]- T003 [[directions/range_structure#T003]] — `[◉ ACTIVE]`（本批无推进）

> [!success]- T001 [[directions/range_structure#T001]] — `[✓ ANSWERED batch_055]`（本批无推进）

> [!failure]- T002 [[directions/range_structure#T002]] — `[✗ DISPROVEN batch_043]`（本批无推进）

## 方向级反思

range_structure direction 累积 9 rounds (b043/b045/b055/b056/b064/b083) + 36 candidates / 2 admits (F021 + 0 本批)，本批 0 admit 是 b056/b064/b083 连续 3 batch 0 admit 第 3 次。

**direction edge 已实质收窄**：
- T001 closed (rank-diff geometry 路径已饱和)
- T002 disproven
- T003 sub-path A 已基本 disproven (b056+b064 共 12 候选 0 admit)
- T004 round 1 disprove P008 escape cross-direction generalization

**剩余可挖空间**:
1. T003 sub-path B [(C-L)/(H-L) Std × 新 RHS] 待评估——但根据 T003 b056+b064 模式预期 ≤30% 概率成功
2. Python escape hatch barra orthogonalize：可拯救 C001/C005/C006 (style_r² clean 候选)，但工具链阻塞 (operators.py:428 bug + barra residual coverage limitation)
3. minute-bar resolution data：根本路径但 data infra 阻塞
4. C006 reserve 沿 (O-L)/(H-L) atom 衍生 batch_084 1 batch 探索

**status 转换建议**: 维持 saturated（不下转 dead 是因为 C006 reserve + T003 sub-path B 待评估）；priority: medium → low（连续 3 batch 0 admit + 4 个挖掘空间 3 个工具链阻塞 + sub-path B 期望 ≤30% 概率）。

**Calibration trigger 检查**（4 条 over-rejection criteria）：
- ❌ judge.md 跨候选反思无 "potential over-rejection" flag（C006 已检查 4 条件，max_corr=0.65>0.30 + mono_oos=+0.30<0.80 → 非真错杀）
- ❌ 本批 admit=0 但**累计 reserve/judged < 40%** (range_structure 整 direction 36 candidates / 2 admit + 4 reserve = 11% reserve rate)；F021 admit 是 admit_ok，不属于"零 admit + 大量 reserve" 模式
- ❌ 同一反直觉指标组合（low style_r² + low alpha_survival 等）≥ 2 次独立——本批 C001/C004/C005 是 P006 库 reducer 已知模式，非反直觉

`calibration_trigger = false`。

**下一步建议**: orchestrator 暂停 range_structure 1-2 rounds（无新机制 → 下批转 saturated→dead），切换到其它 direction（hot_topics 提及 anchor_proximity_momentum/ohlc_temporal_aggregation 仍有 reserve 待延展）；或测试 T003 sub-path B 1 个 candidate (低成本探索，与 batch_084 其它 direction 候选混编)。

**新 dead patterns 候选** (升格 lessons.md / `/pattern-scout` 处理)：
1. **P008 escape mechanism is atom-specific NOT wrap-pattern-general**: TsRank≥60d wrap 仅对"位置/比例" geometry (close position F026, shadow asymmetry F025) 有效，对 raw range magnitude (range/close, range/open) 与 outer Std-wrap 全部 incremental_ic NEG 落回 vol-CV family
2. **Daily open ≈ close in vol-orthogonal cross-section** (csi1000): denominator anchor (open vs close) 在单日 OHLC 几何 TsRank 形式下无独立 alpha——F005 共动律的 daily 频率延伸
3. **Geometric pair break under TsRank wrap**: (H-O)/(H-L) + (O-L)/(H-L) = 1 严格 sum-to-1 几何约束在 TsRank 60d wrap 下被破坏 (实证 corr ≈ -0.5 而非 -1.0)——anchor 方向 (from-high vs from-low) 在 csi1000 信号含量不对称
