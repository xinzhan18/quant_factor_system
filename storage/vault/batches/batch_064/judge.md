---
batch_id: batch_064
direction: range_structure
judged_at: 2026-04-28T10:30:00Z
candidates:
  - {candidate_id: C001, verdict: reserve}
  - {candidate_id: C002, verdict: reserve}
  - {candidate_id: C003, verdict: reject}
  - {candidate_id: C004, verdict: reject}
  - {candidate_id: C005, verdict: reserve}
  - {candidate_id: C006, verdict: reject}
batch_summary: {total: 6, admit: 0, reserve: 3, reject: 3}
admit_count: 0
reject_count: 3
reserve_count: 3
candidate_count: 6
mt_bucket: high
---

# batch_064 Judge Summary

> [!abstract]+ batch_064 · [[directions/range_structure]] · 6 candidates
> ✅ **admit=0** · ⏸ **reserve=3** (C001 / C002 / C005) · ❌ **reject=3** (C003 / C004 / C006)
> **核心发现**: T003 sub-path A 在 (O-L)/(H-L) shared LHS atom 上系统验证了 RHS 跨字段族突破——5 alive 候选 alpha_survival 全部 < 0.40 (range 0.134-0.283) 且 dom=vol_20d 或 turnover_20d，**range_structure direction 在 b056 标记 saturated 后 admit-rate 持续 0%**；最佳候选 C005 incr_ic=0.0103 + cum_mdd=-1.79 + ic_by_year 单调加强但因 alpha_surv=0.261 + MT high 仅触 reserve；H/L geometry 60d→120d 扩展实验证明 H/L geometry 在 120d 仍 vol_20d-loaded（dead-endpoint 是 geometry-specific 而非 window-specific）；TsAutoCorr 60d-Mean RHS hard_gate fail 揭示 temporal-statistic RHS 信噪比下界。
> **MT Budget**: cumulative 342 → **348** · direction 24 → **30** · bucket `high` (维持) · 本批 high=6 / med=0 / low=0

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ⏸ reserve | 🟡·🟡·🟠·🟡·🟢 | ic_oos=0.0305 ICIR=0.256 ls_t=2.48 incr=0.0053 | turnover_60 RHS 与 F017 turnover_5 共载，库增值边缘；CP06 极稳但 alpha_surv=0.283 + dom=turnover_20d crowding=high | [[batches/batch_064/candidates/C001]] |
| C002 | ⏸ reserve | 🟡·🟡·🟠·🟡·🟢 | ic_oos=0.0392 ICIR=0.294 ls_t=2.24 incr=0.0089 | H/C 60d RHS 实现 incr=0.0089 比 C001 优，但 vol_20d 暴露 22.0 极深；anchor rule 限定共 LHS 仅 1 admit | [[batches/batch_064/candidates/C002]] |
| C003 | ❌ reject | 🔴·🔴·🔴·🟡·🟡 | ic_oos=-0.0436 ls_t=-1.91 incr=-0.008 NEG | L/C 60d 与 F021 H/L 60d 反号几何对偶，库 reducer 第 8 次重现 + cum_mdd=-57.7 警戒线 + ic_by_year 单调恶化 | [[batches/batch_064/candidates/C003]] |
| C004 | ❌ reject | 🔴·🟡·🔴·🟡·🟢 | ic_oos=0.0252 ls_t=2.40 alpha_surv=0.179 incr=0.0054 | PB level RHS 通过 book_to_price barra 渗漏 + vol_20d 双载体；P004 9+ direction 律第 10 次重现 | [[batches/batch_064/candidates/C004]] |
| C005 | ⏸ reserve | 🟡·🟡·🟠·🟡·🟢 | ic_oos=0.0393 ls_t=2.62 incr=0.0103 cum_mdd=-1.79 | H/L 120d 扩展 dead-endpoint 试探：信号最强 + cum_mdd 最浅 + ic_by_year 单调加强，但 alpha_surv=0.261 + MT high 抑制 admit | [[batches/batch_064/candidates/C005]] |
| C006 | ❌ reject | hard_gate | ic_oos=0.0014 < 0.008 | TsAutoCorr 60d-Mean RHS cross-section 信噪比近 0，证明 unitless temporal-statistic RHS 在 csi1000 daily 频率失败 | [[batches/batch_064/candidates/C006]] |

**档位编码**：🟢 最优档（aligned/strong/good/low/stable）· 🟡 次档（mixed/borderline/acceptable/medium）· 🟠 边际档（poor）· 🔴 阻断档（misaligned/weak/poor/high/unstable）· `hard_gate` reject 该列写 `hard_gate` 不填色。

## 跨候选对比

- **共 LHS atom**：C001-C005 全部共享 LHS=`Std((O-L)/(H-L),20)`（open-lower-position 离散度 20d Std），C006 也是同 LHS 但 RHS 失败。**P005 #5 anchor rule** 适用——本批最多 1 admit per shared LHS family，本批共 LHS 5 alive 候选实质上是 **RHS 跨字段族独立测试** 而非 LHS 多样性。
- **RHS 字段族测试结果**：
  - turnover_60（C001）→ reserve（max_corr=0.46@F017 turnover-family，incr 边缘）
  - H/C 60d（C002）→ reserve（max_corr=0.44@F020，dom=vol_20d 22.0 deep）
  - L/C 60d（C003）→ **reject** — 与 F021 H/L 几何反号对偶，库 reducer
  - PB level 60d（C004）→ **reject** — book_to_price barra style 渗漏 + vol_20d 双载体
  - H/L 120d（C005）→ reserve — 信号最强但 alpha_surv=0.261 仍 poor
  - TsAutoCorr 60d-Mean（C006）→ **reject** — temporal-statistic RHS 信噪比近 0
- **alpha_survival 全样本统计**：5 alive 候选 alpha_surv 范围 [0.134, 0.283]，**全部 < 0.40 threshold**——本方向所有 RHS 跨字段族尝试都被 vol_20d / turnover_20d 主导吸收。
- **ic_oos 强度对照**：本批 OOS IC 量级 0.025-0.044 远高于 b056 sub-path 同期 0.020-0.025，但 alpha_survival 全部 poor 说明信号增强主要来自 styles，非真 alpha component。
- **cum_ic_mdd 与库可用性**：C005 (-1.79) / C002 (-2.46) / C001 (-2.13) / C004 (-2.05) / C006 (-1.61) **远好于** C003 (-57.69) — 显示 4 个 reserve/reject 候选信号本身实在，仅 C003 是反号载体。
- **错杀侦测扫描**：所有 5 alive 候选 max_lib_corr 都 ∈ [0.376, 0.4629] **均 > 0.30**，**无候选满足 over-rejection criteria 第 1 条**；C005 monotonicity_oos=1.0 + sign_consist=1.0 + cum_mdd=-1.79 接近 over-rejection 边界但因 max_corr=0.425 不构成 flag。**本批不触发 calibration_trigger**。
- **MT 预算推进**：direction_candidates 24 → 30；MT bucket 维持 high；search_adjusted bucket=medium。

## Thread 进展

> [!note]+ T003 [[directions/range_structure#T003]] — `[◉ ACTIVE]`
> sub-path A 系统化测试 (O-L)/(H-L) atom × 6 RHS 跨字段族结论：**RHS 跨字段族独立性失败**——所有尝试的 RHS（turnover/H_C/L_C/PB/H_L_120/TsAutoCorr）在与 (O-L)/(H-L) LHS 复合后 alpha_survival 仍 < 0.40，证明 LHS 几何与 vol_20d/turnover_20d 紧密耦合非 RHS 选择能解决。**新升格 dead pattern**：(1) L/C N-d Mean 单独使用与 H/L 反号几何对偶，永久库 reducer；(2) PB level 60d RHS 通过 book_to_price barra style 渗漏；(3) TsAutoCorr 60d-Mean 在 csi1000 信噪比近 0；(4) H/L geometry 在 120d 仍 dead（dead 是 geometry-specific）。
>
> **下一步**: T003 已基本回答 sub-path A 不可行，sub-path B（(C-L)/(H-L) lower-shadow-close-position 不同 atom）独立尝试需评估必要性——若与 (O-L)/(H-L) 同 alpha-survival 结构则 T003 整体 DISPROVEN。

## 方向级反思

[[directions/range_structure]] 状态 b056 已标记 `saturated`。本批 6 候选 alpha_survival 全部 < 0.40 + admit=0，**与 saturated 状态一致**。range_structure 已 6 rounds 探索，cumulative direction candidates 30，admit 仅 2（F021 batch_055 + 历史 F019/F020），近 4 batches admit-rate 0%。

**核心结构性结论**（本批升格 lesson 候选）：
1. **(O-L)/(H-L) atom × 任意 RHS 在 csi1000 alpha_survival < 0.40**——LHS 几何与 vol_20d/turnover_20d 耦合根深；ortho-by-vol 工具未上线前不应继续 sub-path A
2. **L/C 60d RHS 是永久库 reducer**——与 H/L geometry 反号对偶，独立使用必反号载体
3. **fundamental level RHS 通过 barra style 渗漏**：PB→book_to_price，PE→ep_ratio，需先做 ortho-by-style 才能用作 vol-orthogonal RHS
4. **temporal-statistic RHS（TsAutoCorr 60d-Mean）信噪比下界**：cross-section 区分度过低；下次设计前需 RHS stand-alone IC pretest

**下轮建议（给 orchestrator）**：
- direction range_structure 应保持 saturated；若再 1-2 batch 仍 admit=0 → 升级 `dead`
- T003 sub-path B（(C-L)/(H-L)）需评估必要性；建议**先休 1-2 batch**，让 ortho-by-style 工具或 H/L 120d-only RHS 多样性验证后再回访
- 跨候选模式（同 dom_style + 同 LHS atom × 多 RHS 全 poor alpha_surv）应交 [[lessons.md]] consolidation-pattern-analyst 做正式升格
- C001/C002/C005 reserve 不进 admit 但保留观察；若后续 batch 出现 ortho-vol 工具，可重溯优先 C005（incr=0.0103 + cum_mdd=-1.79 最佳）

> [!info] **Calibration trigger 检查**：本批 admit=0；近 3 批（b062/b063/b064）累积 admit 检查需 orchestrator 评估；reserve 积压检查需 audit pass 后由 orchestrator 评估。本批 alpha_surv poor 全样本 + max_corr 全 ≥ 0.30 → **无单候选错杀 flag**；calibration_trigger=false。
