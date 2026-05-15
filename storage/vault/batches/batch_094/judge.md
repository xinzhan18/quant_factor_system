---
batch_id: batch_094
direction: overnight_intraday_split
judged_at: 2026-05-16T05:50:00Z
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

# batch_094 Judge Summary

> [!abstract]+ batch_094 · [[directions/overnight_intraday_split]] · 6 candidates
> ❌ **admit=0** · ⏸ **reserve=0** · ❌ **reject=6** (all hard_gate fail: 5 ic_oos_too_low + 1 degenerate)
> **核心发现**: Pool #3 (rank-diff axis × overnight 域) 0/6 admit — **rank-diff form 是真 anchor-escape 路径但同步 cancel alpha** (C002 vs C006 实证: rank-diff 把 max_corr 从 0.86@F003 降至 0.27@F018 low cluster ✓ 但 ic_oos 同步从 b080/C006 raw form PASS 降至 hard_gate fail)。"cluster-breaking ↔ alpha-cancellation" trade-off 律新升格候选。3 reserve revival pool 全谱 (pool #1, #2, #3) 连续失败 → **触 calibration_trigger 强信号**。
> **MT Budget**: cumulative 522 → **528** · direction 63 → **69** · bucket `high` (search_adjusted=low — 0 admit 几何 search 未消耗)

## 候选一览

| ID | Verdict | 档位 (CP1·2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | hard_gate | ic_oos=0.0078 (差 0.0002), max_corr=0.30@F018 | T006 律 atom-class 普适在 TsRank 第三次实证 | [[batches/batch_094/candidates/C001]] |
| C002 | ❌ reject | hard_gate | ic_oos=0.0067, mono_oos=0.9 PERFECT, max_corr=0.27@F018 | Pool #3 主路径: rank-diff 破 cluster 但 cancel alpha | [[batches/batch_094/candidates/C002]] |
| C003 | ❌ reject | hard_gate | ic_oos=-0.0032, mono_oos=-0.5, max_corr=0.23@F018 | Window 不对称组合方向反转 (30/90 vs 60/20) informative ≠ tradable | [[batches/batch_094/candidates/C003]] |
| C004 | ❌ reject | hard_gate | n_days_oos=0 degenerate, max_corr=0.44@F022 | Cross-field rank-diff scale-mismatch 退化, volume≡turnover_rate rank | [[batches/batch_094/candidates/C004]] |
| C005 | ❌ reject | hard_gate | ic_oos=0.0006, max_corr=0.035@F007 库最 clean | "库 clean ≠ tradable alpha" 跨方向第 5 次复现 (lesson 强证据) | [[batches/batch_094/candidates/C005]] |
| C006 | ❌ reject | hard_gate | ic_oos=0.0068, max_corr=0.857@F003 critical | Single TsRank + smoothing 不 escape F003 overnight gap 引力盆地 | [[batches/batch_094/candidates/C006]] |

**档位编码**：本批 6/6 hard_gate fail，无 CP2-6 评分。`hard_gate` 列写明 hard_gate fail 类型。

## 跨候选对比

- **rank-diff form vs single TsRank form (C002 vs C006 控制对照实证)**: C002 (rank-diff, raw turnover) max_corr=0.27@F018 low cluster + ic_oos=0.0067 / C006 (single TsRank, smoothed turnover) max_corr=**0.857@F003** + ic_oos=0.0068 — **ic_oos 几乎相同** (信号强度不依赖 form), **max_corr 差 0.59** (form 决定 anchor cluster)。证实 rank-diff form 几何工艺是真效的 anchor-escape 路径, 但代价是 alpha 同步 cancel。**新 lesson 升格候选: "cluster-breaking ↔ alpha-cancellation" trade-off 律**, rank-diff form 不能同时实现 (a) anchor cluster 破除 + (b) alpha 强度保留 在 product LHS 上。
- **rank-diff axis 跨域适用律精化 (b091/b092/b094 三方向证据综合)**:
  - b091/C004 (institutional_flow_proxy, amount/num_trades 域): rank-diff PASS — atom-class 在 amount/num_trades 域是真 escape
  - b092 (tsrank_candlestick_ratio, close-position 域): rank-diff FAIL self-cancellation
  - b094 (overnight_intraday_split, overnight 域): rank-diff FAIL (C001 同字段跨窗 T006 律 + C002 product 跨窗 alpha-cancel)
  - **结论**: rank-diff axis 跨域适用律精化 — 仅在 amount/num_trades 域 (高 noise level, 高 cross-section dispersion) escape; close-position 和 overnight 域 (geometric saturated families) 均 self-cancel。**Lesson 升格: rank-diff escape 域非"非 close-position 域"而是"高 noise dispersion + ungeometrically-saturated 域"**。
- **Style 聚合**: 6 候选无 CP04 分析 (hard_gate fail 中断), 但 max_corr nearest 分布: F018 ×3 (C001/C002/C003 全 overnight sign-aggregation cluster), F022 ×1 (C004 close-position cluster 残留 0.44), F007 ×1 (C005 库最 clean), F003 ×1 (C006 overnight gap raw); 全部落入 overnight 家族 admit anchor 引力盆地内。
- **T006 律跨 atom-class 第三次普适证实 (lesson 升格)**: rank-diff hard rule 第 3 条 (不能同字段跨窗口) 已在 (b048 ratio atom / b093 Corr atom) 两 atom-class 实证, 本批 C001 (raw TsRank atom) 第 3 次复现 — ic_oos=0.0078 essentially zero。**TsRank atom 同字段跨窗 rank-diff 抵消律**新升格强证据 (rank-diff hard rule 跨 atom-class 普适, 无例外)。
- **MT 预算推进**: cumulative 522→528 · direction 63→**69** · 直径 increment 6 + 0 admit, search_adjusted 实际未消耗 → bucket high 表面 (raw), 实际 low (search-adjusted)。

## Thread 进展

> [!failure]+ T011 [[directions/overnight_intraday_split#T011]] — `[✗ DISPROVEN-comprehensive batch_087]` (magnitude-weighted product · Pool #3 续证)
> C001 (overnight 同字段跨窗 raw TsRank) ic_oos=0.0078 hard_gate fail — **T006 律 atom-class 普适律新证据** (TsRank atom 第三次复现同字段跨窗 rank-diff 抵消, 跨 ratio/Corr/TsRank 3 atom-class)。C002 (rank-diff form on overnight × turnover product) ic_oos=0.0067 hard_gate fail despite mono_oos=0.9 PERFECT + max_corr=0.27@F018 low cluster ✓ — **rank-diff form 把 anchor cluster 破除但同步 cancel alpha**, b080/C006 reserve 在 raw form alpha 是真的, 但 rank-diff form 抽离不出。C003 (window-asymmetric 30/90) momentum-reversal informative finding (mono_oos=-0.5 sign 反向一致) 但 ic_oos=-0.0032 不足。C004 (cross-field rank-diff) scale-mismatch degenerate。C006 (single TsRank smoothed) 落 F003 overnight gap 引力盆地。Pool #3 主复活路径 (rank-diff axis on product LHS) inconclusive — T011 axis DISPROVEN-comprehensive 状态不变, **Pool #3 rank-diff axis 在 overnight 域 self-cancel 律 升格 lesson 候选**。

> [!note]- T017 [[directions/overnight_intraday_split#T017]] — `[◉ ACTIVE]` (Corr-based)
> C005 (Cov atom + double TsRank diff) ic_oos=0.0006 essentially zero — Cov atom 多层 wash 律。本批不影响 T017 reserve 火种 (b066/b087/b093 3 火种保持)。

## 方向级反思

direction overnight_intraday_split status **saturated 不变**。
zero_admit_streak: 6 → **7** (b088-b094 连续 7 批 zero admit)。
**3 reserve revival pool 全谱失败累积**: 
- Pool #1 (round 91): expression-rewrite path → b091 mixed (institutional_flow_proxy admit, 但 overnight 方向无新 admit)
- Pool #2 (round 92): asset-driven Python residualize → b092 fail (tsrank_candlestick_ratio direction)
- Pool #3 (round 93+94): rank-diff axis × horizon-switch → b093 fail (T017 RHS 锁源) + b094 fail (rank-diff cancel alpha)
- Pool #4 (b093): horizon-switch CLI 限制 inconclusive

**🚨 calibration_trigger 命中**: zero_admit_streak=7 + 3 reserve revival pool 全谱失败 + 累计 reserve 积压未消化 + 4 lesson 升格候选 (rank-diff cancel alpha + T006 atom-class 普适 + "库 clean ≠ tradable" 第 5 次 + Cov 多层 wash)。**应触 [[lessons#Threshold Calibration]] 诊断流程** — 区分"信号真的都不够好"vs"阈值错杀"，可能需要:
- (a) 重审 reserve pool (b066/b080/b087/b093/b094 累计 5 reserve) 是否有真"错杀"候选
- (b) 检查 hard_gate ic_oos_min=0.008 阈值是否过严 (本批 C001 差 0.0002 ≈ 2.5%)
- (c) Pool #1-4 全失败说明 reserve revival 几何工艺本身可能不是答案, 需切 anchor retirement 或 new field expansion

**下一步建议** (orchestrator 决策):
1. 若 calibration_trigger 命中: 跳 Phase 4, 报 orchestrator 走 calibration 流程
2. 切换 active direction (overnight_intraday_split saturated streak 过长, 优先级 medium 可降至 low)
3. consolidation_trigger 候选: rounds_since_consolidation=3 但 zero_admit_streak=7 + 4 lesson 升格累积 → 可能下批触发 Phase 5

若下一轮 admit 率仍 0%, `priority: medium → low` 或 `status: saturated → dead` 候选。
