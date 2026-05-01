---
batch_id: batch_070
direction: pit_valuation_pure
judged_at: 2026-05-02T00:00:00Z
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

# batch_070 Judge Summary

> [!abstract]+ batch_070 · [[directions/pit_valuation_pure]] · 6 candidates
> ❌ **reject=6** · 0 admit / 0 reserve
> **核心发现**: T002 (b069 C006 火种)续探完全证伪——RHS 替换 PB→PE/PCF 全部 ls_t 大跌（C001 +0.32, C002 +1.02, C006 +0.53 vs b069 C006 +2.17）+ 跨族 Mul 翻号（C004 mono OOS=-1.0）+ $eps_ttm 字段路径 NaN 双 reject (C003/C005)。**book yield basis (PB 端) 不可被 PE/PCF 替代**，dividend yield 是 b069 C006 强度的关键贡献者。
> **MT Budget**: cumulative 378 → 384 · direction 6 → 12 · bucket `high`（raw=0.797）· 本批 low=0 / med=0 / high=6（全 high）

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | 🟡·🔴·🔴·🟢·🟢 | ls_t=+0.32 mono_oos=+0.3 alpha_surv=0.32 | RHS PB→PE 替换 ls_t 灾难性衰减 (-84% vs b069 C006) + vol_20d_exp=14.0 恶化 (+66%) + ep_ratio=8.18 单端 dominant | [[batches/batch_070/candidates/C001]] |
| C002 | ❌ reject | 🟢·🔴·🟡·🟡·🟢 | ls_t=+1.02 incr_ic=+0.0034<floor alpha_surv=0.29 | yield × cash_flow_yield 比 yield × book_yield (b069 C006) 弱 53%，cash perspective 不能替代 book perspective | [[batches/batch_070/candidates/C002]] |
| C003 | ❌ reject | hard_gate | compute_error: $eps_ttm 路径 NaN | 字段可用性问题 — `Div($eps_ttm,$close)` preprocess 全 NaN，T002 future probes 应避开 $eps_ttm | [[batches/batch_070/candidates/C003]] |
| C004 | ❌ reject | hard_gate | ic_oos=+0.007<floor + mono_sign_flip (IS=+0.9 OOS=-1.0) | 跨族 Mul (value × quality) OOS regime drift 翻号——与同族 Mul 放大 basis 律形成对照 | [[batches/batch_070/candidates/C004]] |
| C005 | ❌ reject | hard_gate | compute_error: $eps_ttm level form NaN | 与 C003 同因——$eps_ttm 字段在 csi1000 cross-section 不可用 | [[batches/batch_070/candidates/C005]] |
| C006 | ❌ reject | 🟢·🔴·🟡·🟢·🟢 | ls_t=+0.53 sty_r²=0.36 alpha_surv=0.35 | 双 reciprocal Mul (1/PE × 1/PCF) 缺 atom 独立性——揭示 rank × rank Mul 假设需修订：两端必须几何独立 basis | [[batches/batch_070/candidates/C006]] |

**档位编码**：🟢 最优档（aligned/strong/good/low/stable）· 🟡 次档（mixed/borderline/acceptable/medium）· 🔴 阻断档（misaligned/weak/poor/high/unstable）· `hard_gate` reject 该列写 `hard_gate` 不填色。

## 跨候选对比

- **Style 聚合**：5/6 候选 dominant_style = `vol_20d`（C001=14.0, C002=11.3, C006=10.9 暴露），与 b069 同因——本方向系统性被 vol_20d 拉拽，**不是 PIT valuation 字段 hypothesis 的胜利**而是 vol_20d 的常态吸收
- **Value basis 显化异质性**（vs b069 C006 reserve）：
  - C001 (yield × 1/PE): b/p=**0.67** + ep_ratio=**8.18** → earnings 端独强 book 端弱化 → ls_t=+0.32
  - C002 (yield × 1/PCF): b/p=**0.87** + ep_ratio=**4.72** → 双端中等 → ls_t=+1.02
  - C006 (1/PE × 1/PCF): b/p=**0.79** + ep_ratio=**7.45** → earnings 端高位 + 缺 dividend → ls_t=+0.53
  - b069 C006 (yield × 1/PB): b/p=**2.21** + ep_ratio=3.96 → 双端强 + book 端突出 → ls_t=**+2.17**
  - **结论**: book_to_price exposure ≥ 2 是 ls_t 强度的**充分但不必要**条件——b/p=2.21 → ls_t=2.17，b/p<1.0 → ls_t<1.1
- **相关度 cluster**：6 候选互相 correlation 在 [0.21, 0.65] 范围（基于 nearest_factor_id 一致性推断），但全部与 F021 max_corr ≈ 0.21-0.24 → 库内冗余低
- **MT 预算推进**：direction_candidates 6 → 12（rounds_in_direction 翻倍）；bucket 仍 `high`，下一批 candidates 必须经过更严的 borderline 上限审查
- **错杀侦测**：6 候选**无一**满足全部 4 条件（max_lib_corr<0.30 ✓ for C001/C002/C006, 但 incremental_ic>0.010 三立 fail）→ 无 over-rejection flag，无 calibration trigger

## Thread 进展

> [!failure]+ T002 [[directions/pit_valuation_pure#T002]] — `[✗ DISPROVEN batch_070]`
> b069 C006 火种续探**完全证伪**：(a) RHS PB→PE 替换 → C001 ls_t=+0.32（衰减-84%）；(b) yield × cash_flow_yield → C002 ls_t=+1.02（衰减-53%）；双 reciprocal valuation → C006 ls_t=+0.53；跨族 Mul → C004 OOS regime drift 翻号。**核心反 lesson**: rank × rank Mul 复合需要两端 atom 几何独立 + 至少一端 book yield basis 显化（b/p≥2）；纯 cash / 纯 earnings yield 端不足以替代 book 端。

> [!note]+ T004 [[directions/pit_valuation_pure#T004]] 🆕 — `[◉ ACTIVE]`
> 承接 T002 disproven 遗留——是否存在**完全独立于 b069 C006 (yield × 1/PB) 的 PIT valuation alpha basis**？还是 PIT valuation direction 已 saturated（仅 b069 C006 一例 reserve 是孤立点不可推广）？

> [!success]+ T003 [[directions/pit_valuation_pure#T003]] — `[✗ DISPROVEN batch_069]`（本批无推进）
> （上批已 disproven，本批未涉及 TTM aggregate）

> [!note]- T001 [[directions/pit_valuation_pure#T001]] — `[◉ ACTIVE]`（本批无推进）

## 方向级反思

本方向的 edge 显著收窄：

1. **首批 (b069)** 6 候选 → admit=0 / reserve=1 (C006 yield × 1/PB)：揭示 rank × rank Mul 同族 basis 放大律 + book yield 端 cross-section 强度
2. **续批 (b070)** 6 候选 → admit=0 / reserve=0 / reject=6：续探 T002 RHS 替换全部失败，揭示 b069 C006 的 ls_t=+2.17 是**孤立点**——RHS 端字段不可互换 (PB→PE/PCF 全衰减)，cross-section 强度依赖 dividend×book 的特定组合

**累计 direction 状态**：
- rounds: 2
- admit: 0
- reserve: 1（b069 C006，alpha_survival=0.19 三立未达 admit default 0.40）
- reject: 11（b069: 5 + b070: 6）
- admit/judged ratio: 0/12 = **0%**

**饱和判定（针对 status saturated 转换）**：
- 连续 2 批 admit=0 ✓
- reject 比例 > 80%: 11/12 = 92% ✓
- 但**仍存在 1 reserve 火种** (b069 C006)，且关键发现（rank × rank Mul 同族 basis 放大律）值得升 lessons.md
- → 建议 status: `probing → saturated`（条件满足）；但保留 reserve 等待潜在 calibration 复活

**下一步建议（给 orchestrator）**：
1. **不再续探 T002 RHS 变体**（PE/PCF/cross-族 Mul 全验完，无新探索路径）
2. **direction-level decision**：是否进 saturated 状态由 orchestrator 决策——本 subagent 不直接转 status，但 narrative log 标注饱和条件已满足
3. **lessons.md 升格候选**: "rank × rank Mul 复合两端必须几何独立 + 至少一端 book yield basis 显化（b/p≥2）"——可由 `/consolidate-pattern-analyst` 拾取
4. **如要继续此方向**，T004 应换非 b069 C006 family 路径（如 fundamental quality 单 atom 形式 + Python residualize 工艺）

**consolidation_trigger**: false（rounds_since_last_consolidation = 2，未到 10）
**calibration_trigger**: false（无 over-rejection flag，6 候选全部因 CP3 weak 或 hard_gate fail，非边缘错杀）
