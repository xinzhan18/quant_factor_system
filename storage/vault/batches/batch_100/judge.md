---
batch_id: batch_100
direction: institutional_flow_proxy
judged_at: 2026-05-16T07:00:00Z
candidates:
  - {candidate_id: C001, verdict: reserve}
  - {candidate_id: C002, verdict: reject}
  - {candidate_id: C003, verdict: reject}
  - {candidate_id: C004, verdict: reserve}
  - {candidate_id: C005, verdict: reject}
  - {candidate_id: C006, verdict: reject}
batch_summary: {total: 6, admit: 0, reserve: 2, reject: 4}
admit_count: 0
reject_count: 4
reserve_count: 2
candidate_count: 6
mt_bucket: high
---

# batch_100 Judge Summary

> [!abstract]+ batch_100 · [[directions/institutional_flow_proxy]] · 6 candidates
> ✅ **admit=0** · ⏸ **reserve=2** (C001, C004) · ❌ **reject=4** (C002/C003/C005/C006)
> **核心发现**: rank-diff revival path (a) shorter-RHS 真正脱 F024 anchor 邻域 — C001 (60-10) ls_t=-2.60 + alpha_surv=0.77 + max_corr=0.18@F028 + incr_ic=+0.010 真正超越 b091/C004 reserve（ls_t -2.20→-2.60，且脱 F024 anchor），但 mt_bucket=high 仍卡 borderline 不足 admit。Path (b) cross-field rank-diff 4 候选全 hard-gate sign_flip — **P032 law #2 'raw field 独立' 在 ratio-vs-ratio + cross-field-raw rank-diff 都 binding**。
> **MT Budget**: cumulative 552 → **558** · direction 6 → **12** · bucket `high`（满载）

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ⏸ reserve | 🟢·🟡·🟡·🟢·🟢 | ls_t=-2.60 alpha_surv=0.77 incr_ic=+0.010 max_corr=0.18 | 超越 b091/C004 reserve（脱 F024），但 mt=high CP03 cap borderline | [[batches/batch_100/candidates/C001]] |
| C002 | ❌ reject | hard_gate | sign_flip train+0.0057 val-0.0127 | P032 law #2 binding：LHS/RHS 共享 $amount numerator | [[batches/batch_100/candidates/C002]] |
| C003 | ❌ reject | hard_gate | sign_flip train+0.0297 val-0.0031 | RHS turnover_rate 不满足 P031 完整三条件，OOS decay | [[batches/batch_100/candidates/C003]] |
| C004 | ⏸ reserve | 🟢·🟡·🟠·🟢·🟢 | ls_t=-2.94 alpha_surv=0.39 incr_ic=+0.009 max_corr=0.22 | path (a) 极尖窗 60-5；ls_t 最强但 alpha_surv 卡线 | [[batches/batch_100/candidates/C004]] |
| C005 | ❌ reject | hard_gate | train ic ≈0 (4e-5) sign undefined | longer-LHS rank-diff degenerate — 长窗双向 cancellation | [[batches/batch_100/candidates/C005]] |
| C006 | ❌ reject | hard_gate | sign_flip train+0.0321 val-0.0027 | RHS raw $volume 不脱 size embedding | [[batches/batch_100/candidates/C006]] |

**档位编码**：🟢 最优档 · 🟡 次档 · 🟠 边际 · 🔴 阻断档 · `hard_gate` reject 不填色

## 跨候选对比

- **Path (a) shorter-RHS rank-diff (C001 / C004)**：唯一 hard-gate-pass 的两个候选，与 b091/C004 (60-20) 同形式但 RHS 进一步缩短（10d / 5d）。两候选都达到 ls_t<-2.5 + monotonicity_oos≥-0.90 + max_corr<0.25 + incr_ic>+0.005 + sign_consistency=1.0，构成 reserve 强候选。**真正脱 F024 anchor 邻域**：C001/C004 与 F024 相关分别 -0.02 / -0.06（vs b072/C006 raw -0.24@F009，b091/C004 -0.18@F016），证明 'rank-diff shorter-RHS' 是 F024 邻域之外的真新几何空间。
- **Path (b) cross-field rank-diff (C002/C003/C006)**：3/3 全 hard-gate sign_flip — 系统性失败。设计时 C002 已 flag P032 law #2 风险（LHS/RHS 共享 $amount numerator），事后 binding 实证；C003/C006 RHS 选用单字段 ratio/raw 不满足 P031 三条件，IS 段强 OOS 退至噪声。**升格候选 lesson**：'cross-field rank-diff' 路径在 csi1000 daily 表现出**结构性 IS-overfit/OOS-decay**，RHS 选择必须通过完整 P031 + P032 双 gate 才能尝试。
- **Path (a) longer-LHS direction (C005)**：60-120d 双长窗双向 cancellation 完全 degenerate — 与 round 91 lesson 'TsRank 长窗在 ratio 字段反而加重 vol_20d 嵌入 / window 越长信号越弱' 一致。**rank-diff direction-asymmetric 律**：LHS 是基础窗（60d），RHS 必须更短（5/10/20d），反方向 degenerate。
- **Style 聚合**：C001/C004 都 dominant_style=vol_20d，但 alpha_surv 0.77 vs 0.39 — 同结构候选 alpha_surv 差异巨大（C001 在 OOS 段信号更强反而剥离更彻底）。
- **MT 预算推进**：cumulative 552→558（+6）；direction 6→12（×2 — 本批 6 candidates 全计入 institutional_flow_proxy）；exposure 1.0 满载。bucket=high 已为天花板。

## Thread 进展

> [!note]+ T001 [[directions/institutional_flow_proxy#T001|T001]] — `[◉ ACTIVE]`
> Path (a) shorter-RHS rank-diff: C001 (60-10) + C004 (60-5) 双 reserve 真正脱 F024 anchor。Path (b) cross-field rank-diff: 3/3 全 hard-gate fail，**path (b) effective closure**。Path (a) longer-LHS: 1/1 fail (C005)，**direction-asymmetric 律**确立。下批可：(i) 跨批 reserve 累积 → 触发 calibration retro triage；(ii) Python residualize on F024+F012 重测 C001 incr_ic; (iii) 探索 path (c) 'CsRank second-wrap' — 但需先解 qlib custom-op re-parse 工程阻塞 (CsRankOp 接受 composite-with-TsRank 时 `str(self.feature)` 返回 'TsRankOp' 类名而非注册名 'TsRank'，re-parse fail)。

## 方向级反思

- **direction 状态**：维持 `probing` (round 4)。已 3 个 reserve 火种 (b072/C006, b091/C004, b100/C001 三选一 + b100/C004 → 4 个)；积累已显著但仍**无 admit**。
- **Edge 评估**：rank-diff shorter-RHS 几何**真有 alpha**（ls_t 系列稳健、monotonicity perfect、cum_ic_mdd 极浅、sign_consistency=1.0、library-orthogonal），但被三个工程性 caps 限制：
  - mt_bucket=high 'CP03 最高 borderline' 政策硬卡
  - ls_t ∈ [-2.60, -2.94] 仍未达 strong 阈值 3.0
  - alpha_surv 在 vol_20d-dominated 13-15 score 下被压低至 [0.39, 0.77]，C004 微低 threshold
- **calibration trigger 评估**：本批 admit=0；最近 3 批 (b098 admit=1, b099 admit=0, b100 admit=0) 累计 admit=1（非全零）→ trigger #2 'consecutive zero admit + 累积 reserve' 不立。但 reserve 积压 cumulative reserves ~20+ / judged 600+ ≈ 3.3% → trigger #3 'reserve 积压 > 40%' 远不满足。**无 calibration trigger**。
- **下批建议**：(a) 切方向，本方向 reserve pool 已强；或 (b) Python residualize path：把 C001 (60-10) 在 (F024+F012+F015+F016) 残差空间内重计 IC — 若 residualize 后 ls_t≥3 + incr_ic≥0.01 → 升格 admit 候选（这需要 Python escape hatch + 工程支持）。**当前批结论：reserve pool 升级，下批切方向或工程突破**。

## Engineering Block (本批新发现)

`CsRank(Sub(TsRank(...), TsRank(...)))` 在 Phase 2 compute 触发 qlib bug：CsRank 的 `_build_cs_cache` 用 `str(self.feature)` 序列化内部表达式，但 qlib 的 `Sub.__str__` 用类名 `TsRankOp` (非注册名 `TsRank`)，re-parse 时找不到 `TsRankOp` 注册 → `AttributeError: The operator [TsRankOp] is not registered`。本批 C004/C005 原设计已含 CsRank-wrap-rank-diff 候选，被迫替换。**建议 calibration**：在 `_build_cs_cache` 中把 `str(self.feature)` 后用类名→注册名映射替换（CUSTOM_OPS 反向 dict），1-line 修复，解锁所有 CsRank-of-custom-composite 候选。本批 path (c) CsRank-second-wrap 因此完全未触达。
