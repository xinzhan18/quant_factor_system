---
batch_id: batch_093
direction: overnight_intraday_split
judged_at: 2026-05-15T21:35:00Z
candidates:
  - {candidate_id: C001, verdict: reject}
  - {candidate_id: C002, verdict: reject}
  - {candidate_id: C003, verdict: reject}
  - {candidate_id: C004, verdict: reject}
  - {candidate_id: C005, verdict: reserve}
  - {candidate_id: C006, verdict: reject}
batch_summary: {total: 6, admit: 0, reserve: 1, reject: 5}
admit_count: 0
reject_count: 5
reserve_count: 1
candidate_count: 6
mt_bucket: high
---

# batch_093 Judge Summary

> [!abstract]+ batch_093 · [[directions/overnight_intraday_split]] · 6 candidates · **reserve_revival_pool_4 (horizon-switch)**
> ✅ **admit=0** · ⏸ **reserve=1** (C005 num_trades LHS, fresh atom-class probe) · ❌ **reject=5** (C001 b087 duplicate / C002/C003/C006 同形 borderline / C004 T006 cross-window hard_gate)
> **核心发现 1 — Pool #4 horizon-switch mechanism diagnosis (CLI 限制)**: `research execute` 不支持 `--horizon` override, admit gate 锚定 1d (config.yaml `primary_horizon: 1`). 但 result.yaml.metrics.cp03.ic_by_horizon 自动产出 multi-horizon ladder [1,3,5,10,20]. C001 实测 horizon ladder 1d=0.032→3d=0.041→5d=0.045→10d=0.057→20d=0.073 (b087 ladder 复现), icir 同步从 0.22→0.41 单调上升, 验证 horizon-switch 机制存在但**不能改 admit gate**.
> **核心发现 2 — RHS 是 F019 cluster 真锁源 (新升格 lesson 候选)**: 5 candidates LHS 跨 4 个 fields ($volume/$num_trades/$amount/Div($volume,Mean($volume,20))) + 2 个 windows (20/60d) **全部 max_corr=0.44-0.45@F019 + dom_style=vol_20d + alpha_surv=0.18-0.20 (< 0.30 floor)**, 5/5 uniform. **结论**: T017 axis cluster anchor 不在 LHS Corr atom (volume/num_trades/amount 跨字段全锁同 cluster), 在 RHS `Mean(Sub($high,$low), 60)` — Mean H-L 60d 就是 vol_20d basis 的低频近似, F019 cluster 直接同源. **真复活路径必须改 RHS**, 不是 LHS.
> **核心发现 3 — C004 T006 cross-window 律跨 atom 普适 (Corr atom 实证)**: T006 同字段跨窗口抵消律 (b048 升格) 在 Corr atom 上**复现** — `Sub(CsRank(Corr_60), CsRank(Corr_20))` ic_oos=0.006 < 0.008 hard_gate fail + mono_oos=0.3 + ls_t=0.91 + max_corr=0.04 lib-clean 但 alpha 信号塌缩. T006 律不依赖 atom-class (aggregation 与 Corr 同律).
> **MT Budget**: cumulative 486 → **492** · direction 57 → **63** · bucket `high` (search_adjusted=medium)

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | pass·borderline·poor·**duplicate-of-reserve**·stable | ic_oos=0.032 ls_t=1.77 mono=1.00 alpha_surv=0.20 max_corr=0.45@F019 incr_ic=0.011 9/9_pos | T017 b087/C001 baseline replay — 与 b087 reserve 完全相同 canonical 表达式, 不再独立 reserve (b087 C001 reserve 仍有效). 验证目的: horizon ladder 自动产出 + alpha_surv/max_corr/incr_ic 三 borderline 稳定 (b087 复现) | [[batches/batch_093/candidates/C001]] |
| C002 | ❌ reject | pass·**borderline-weak**·poor·borderline·stable | ic_oos=0.027 ls_t=1.40 mono=1.00 alpha_surv=0.15 max_corr=0.45@F019 incr_ic=0.007 | Corr 短窗 20d + RHS Mean(H-L,60): 短 Corr 窗未改善, ls_t 1.77→1.40 退化 + alpha_surv 0.20→0.15 (更差). RHS 60d 仍锁 F019 vol_20d cluster, LHS 窗变化无解 | [[batches/batch_093/candidates/C002]] |
| C003 | ❌ reject | pass·borderline·poor·borderline·stable | ic_oos=0.028 ls_t=1.46 mono=1.00 alpha_surv=0.18 max_corr=0.44@F019 incr_ic=0.009 | Normalized-volume LHS (Div($volume, Mean($volume, 20))): 量内 detrend 后仍撞 F019. 假设 "ratio detrend → escape" 失败 — RHS H-L 60d 是 vol_20d 真源, LHS detrend 无效 | [[batches/batch_093/candidates/C003]] |
| C004 | ❌ reject | **hard_gate** (ic_too_low) | ic_oos=0.006<0.008 + mono_oos=0.3 + ls_t=0.91 + max_corr=0.04@F027 | T017 cross-window rank-diff diagnostic: T006 律跨 atom 普适 (Corr 同字段长短窗 cross-section ordering 高度相关 → rank-diff 抵消). 库 max_corr=0.04 最 clean 但 alpha 塌缩 — "库 clean ≠ tradable alpha" 第 4 次反例 (b059/b066/b087/b093) | [[batches/batch_093/candidates/C004]] |
| C005 | ⏸ **reserve** | pass·**borderline-strong**·poor·borderline·stable | ic_oos=0.033 ls_t=**1.94** mono=1.00 alpha_surv=0.20 max_corr=0.45@F019 incr_ic=**0.012** 9/9_pos | T017 axis 首次 num_trades LHS — atom-class 不同 (num_trades=order arrival, 与 volume/amount 微观正交) 但 alpha_surv/max_corr **uniform with volume LHS** = F019 cluster 锁源在 RHS 实证. 本批最强候选 (ls_t=1.94 trail $\to$2.0 阈值仅 3%) + 9/9 年正 + sign_consist=1.0. Horizon ladder 1d→20d 0.033→0.075 (验证). 跨 batch T017 火种第 3 个 (b066 C005 + b087 C001 + b093 C005). 等 F019 退役或 RHS axis 真换才能 admit | [[batches/batch_093/candidates/C005]] |
| C006 | ❌ reject | pass·borderline·poor·borderline·stable | ic_oos=0.032 ls_t=1.78 mono=1.00 alpha_surv=0.20 max_corr=0.45@F019 incr_ic=0.011 | Amount LHS — 与 C001 (volume LHS) metrics 几乎相同 (ic 0.032 vs 0.032, ls_t 1.78 vs 1.77, alpha_surv 0.20 vs 0.20, max_corr 0.45 vs 0.45). amount = price × volume 1st moment 在 Corr atom 内部退化为 volume 近似. duplicate-of-reserve (与 b087 C001 + 本批 C001 高 corr) | [[batches/batch_093/candidates/C006]] |

## 跨候选对比

- **RHS 是 F019 anchor 真源 (新发现, lesson 候选)**: C001/C002/C003/C005/C006 LHS 跨 4 字段 ($volume / Div(vol/Mean(vol,20)) / $num_trades / $amount) + 2 窗口 (20/60d), max_corr **全部 0.44-0.45@F019** + dom_style 全部 vol_20d + alpha_surv 全部 0.18-0.21 (5/5 uniform 跨字段). 唯一变化是 ls_t (1.40-1.94) 和 ic_oos (0.027-0.033). **结论**: F019 cluster anchor 不在 LHS Corr atom 而在 RHS `Mean($high-$low, 60)` — Mean H-L 60d 是 vol_20d basis 的低频近似 (range = price volatility 1st moment, 60d 窗 = vol_20d 平滑). T017 axis 真复活路径**必须改 RHS** (Mean H-L 60d → 其它 fresh basis), 不是 LHS.
- **Pool #4 horizon-switch mechanism inconclusive at admit gate (CLI 限制)**: 6/6 candidates horizon ladder 1d→20d 单调上升 (C001/C005/C006 ladder ic 1d=0.032/0.033/0.032 → 5d=0.045/0.046/0.045 → 10d=0.057/0.059/0.058 → 20d=0.073/0.075/0.073), icir 同步从 0.22→0.40+ 强化. Horizon-switch mechanism **存在且显著** (3.5× IC 放大). 但 `research execute` 不支持 `--horizon`, admit gate 锚定 1d (config.yaml `primary_horizon: 1`). 本批 1d 评估 5/6 borderline 联立 reject — **pool #4 mechanism 在现有 CLI 下不能直接验证为 admit-tradable**, 需 CLI 扩展或 evaluation policy 改造. **下批切回 expression-rewrite revival 或 anchor-retirement 路径**.
- **T006 律跨 atom 普适 (C004 实证)**: T006 同字段跨窗口抵消律 (b048 升格, rank-diff hard rule 第 3 条) 之前仅在 aggregation atom (Mean/Std) 上证实. C004 显式 probe `Sub(CsRank(Corr_60), CsRank(Corr_20))` 同字段 Corr 跨窗口 — ic_oos=0.006 < 0.008 hard_gate + mono_oos=0.3 (sign-flip 边界) + ls_t=0.91. Corr atom 输出 [-1,1] bounded, 理论上长短窗 Corr 值非单调相关可能松动 T006 律, **但实测仍 cross-section 高度相关导致 rank-diff 抵消**. T006 律不依赖 atom-class, 跨 aggregation/Corr 普适. **lesson 升格候选**: "rank-diff 第 3 条硬约束 (不能同字段跨窗口) 跨 atom-class 普适, 不存在 atom 例外".
- **"库 clean ≠ tradable alpha" 第 4 次反例 (C004)**: max_corr=0.04@F027 库内最 clean (跨方向全库唯一接近), 但 alpha 塌缩 (ic_oos=0.006 + mono=0.3 + ls_t=0.91). 该反例累计 b059/b066/b087/b093 共 4 次跨方向独立复现, 应升格 lesson "库 clean ≠ tradable alpha" 在 cross-section 信号塌缩场景下普适警示.
- **num_trades atom-class 假设证伪 (round 93 finding 反向验证)**: round 93 calibration finding 暗示 "rank-diff axis atom-class 依赖律" — close-position 域 self-cancellation, amount/num_trades 域 escape success. **本批 C005 (num_trades) 与 C006 (amount) 实测 与 volume LHS uniform**, atom-class 假设在 T017 Corr family **不成立**. 反例: T017 axis 的 cluster anchor 不在 LHS atom-class, 在 RHS 量纲 (Mean H-L 60d = vol_20d 1st moment 平滑). round 93 finding 需 scope refinement: "atom-class 依赖律仅在 rank-diff LHS 上层 close-position cluster 域成立, 在 Corr atom 内部 LHS-swap 不能改 cluster anchor 归属".
- **incr_ic 中位数 5 candidates 0.007-0.012**: 全在 borderline gate 0.015 之下, 缺口 17%-50%. 与 b080 0.0098 (1 reserve) / b087 0.011 (1 reserve) 三连"borderline incr_ic"模式. 显示该方向 alpha edge 极窄 + 库内已 admit 因子 (尤其 F019) 占据该信号几何 majority 解释力.
- **MT 预算推进**: direction_candidates 57 → **63** (本方向 round 17, 累计 +6); cumulative 486 → **492**. zero_admit_streak 5 → **6** (b066/b080/b087/b088/b089/b090/b091/b092 + b093 全 zero-admit, 跨方向 9 连). **calibration_trigger 候选**: 累计 reserve pool b066/b080/b087/b093 等待复活 (4 candidates 同 T017 axis 一脉) + 2 reserve revival pool (b091 pool #1 失败 + b092 pool #2 失败) → **本批 pool #3 失败 (此 pool 编号实际是 #4 — pool #3 在 batch_092 之前已批次失败) 让 "reserve revival pool sequence 累计 ≥3 失败" 复现, calibration trigger 强化**.

## Thread 进展

> [!note]+ T017 [[directions/overnight_intraday_split#T017]] — `[◉ ACTIVE]` (火种续命再实证 + RHS lock 真因揭示)
> reserve 1 (C005). T017 axis 跨 batch 火种续命第 3 次:
> - **b066 C005** Corr-20 + Std(volume,60) RHS (alpha_surv=1.16 ls_t=1.26<2)
> - **b087 C001** Corr-60 + Mean(H-L,60) RHS (ic_oos=0.032 ls_t=1.77 alpha_surv=0.20)
> - **b093 C005** Corr-60 num_trades LHS + Mean(H-L,60) RHS (ic_oos=0.033 ls_t=1.94 alpha_surv=0.20)
>
> **新揭示 — RHS 锁源律**: b093 LHS 跨 4 字段 (volume / normalized-vol / num_trades / amount) + 2 窗口 全 alpha_surv 0.18-0.21 + max_corr 0.44-0.45@F019 + dom_style=vol_20d. **F019 cluster anchor 在 RHS Mean(H-L,60), 不在 LHS Corr atom**. b087 已 hint "真复活路径不是换 RHS 而是 horizon policy 或 anchor 退役" 但本批实测**换 LHS 也不行** — 必须**真换 RHS 出 vol_20d basis 域**.
>
> **真复活路径候选 (重排优先级)**: (a) RHS swap Mean(H-L,60) → fresh basis (e.g. $num_trades 60d Mean, $amount 60d Std, time-aware 60d ATR — 但 ATR 接近 H-L); (b) F019 anchor 退役 (本批 max_corr 仅 0.44-0.45, 与 0.30 high-corr 阈值仍差 0.14-0.15); (c) horizon-switch CLI 扩展 (longest-term solution, mechanism 已实证 1d→20d 3.5× IC 放大); (d) Python OLS residualize on vol_20d basis (b071 此路径 OOS sign-flip 风险, 不优先).

> [!failure]+ T011 [[directions/overnight_intraday_split#T011]] — `[✗ DISPROVEN-comprehensive b087 + b093]`（complementary 证据）
> 本批不直接探 T011 axis, 但 C004 (cross-window rank-diff Corr) 间接复证 T011 axis 同字段几何抵消 — T006 律跨 atom 普适, 与 T011 axis "≥10 fresh magnitude/ratio/signed/Cov atom 全失败" 同源.

## 方向级反思

本方向 round 17 (b093) 兑现率 0/6 admit + 1/6 reserve, 与 b066/b080/b087 形成**连续 4 round zero-admit borderline-reserve 模式**, 全在 T017 axis 持续探索. 主要新发现:

1. **RHS 锁源律 — T017 axis F019 cluster anchor 在 RHS `Mean(H-L,60)` 不在 LHS Corr atom (新升格 lesson 候选)**: b093 LHS 跨 4 fields ($volume/$num_trades/$amount/normalized-volume) + 2 windows uniform alpha_surv=0.18-0.21 + max_corr=0.44-0.45@F019 + dom_style=vol_20d. **5/5 uniform across atom-class** 强证据: cluster lock 在 RHS 量纲, LHS-swap 无效. 真复活路径: RHS swap Mean(H-L,60) → fresh basis (非 H-L 衍生, 非 vol_20d 1st moment 平滑形式).

2. **Pool #4 horizon-switch mechanism 在 CLI 现状下 inconclusive**: `research execute` 不支持 `--horizon`, admit gate 锚定 1d. horizon ladder 1d→20d 实测 3.5× IC 放大 + icir 0.22→0.41 强化 (mechanism 真实存在), 但 admit 在 1d 仍 borderline reject. **本路径需 CLI 扩展或 evaluation policy 改造才能验证 admit-tradable**, 短期不可直接行动. 下批切回 expression-rewrite revival 或 anchor-retirement 路径.

3. **T006 律跨 atom-class 普适 (C004 实证, lesson 候选)**: 同字段跨窗口 rank-diff 抵消律之前仅在 aggregation atom (Mean/Std) 实证, C004 Corr atom 实测复现 (ic=0.006 hard_gate + mono=0.3). atom 不依赖律. rank-diff hard rule 第 3 条 (不能同字段跨窗口) **跨 atom-class 普适, 不存在 atom 例外**.

4. **"库 clean ≠ tradable alpha" 第 4 次跨方向复现 (lesson 强化)**: C004 max_corr=0.04@F027 库内最 clean 但 alpha 塌缩. 累计 b059/b066/b087/b093 共 4 次. 该 reverse criterion 应升格 lessons.md "max_corr 极低 (<0.10) 是否 hint 信号塌缩" 警示规则.

5. **num_trades atom-class 假设证伪 (round 93 finding scope refinement)**: round 93 finding "rank-diff axis atom-class 依赖律 — num_trades/amount 域 escape close-position cluster fail" 在 T017 Corr family **不成立**. C005 (num_trades) + C006 (amount) 与 volume LHS metrics uniform. 反例: T017 axis cluster anchor 在 RHS 不在 LHS atom-class. **scope refinement**: "atom-class 依赖律仅在 rank-diff LHS 上层 close-position cluster 域成立, Corr atom 内部 LHS-swap 不改 cluster".

**Edge 评估**: 本方向 alpha edge 极度收窄 — round 14 b087 incr_ic=0.011 borderline → round 17 b093 incr_ic=0.007-0.012 (5/6 borderline), 三连"borderline reserve fire"已升 4 连. 该方向真正可挖空间已锁在 T017 axis RHS-replacement 单一路径, 但 RHS 实测无 fresh basis 可用 (H-L/Std/Mean 全 vol_20d 同源).

**下一步建议**:
- (a) **方向状态**: 已是 saturated (b087 翻牌), 本批 narrative 不再翻 status. Saturation 锁定.
- (b) **🚨 触发 consolidation_trigger (强信号)**: rounds_since_consolidation=2+1=3, 但 **zero_admit_streak=6 + 2 reserve revival pool 连续失败 (pool #1 b091 / pool #2 b092 / pool #4 b093)** 复合证据强化. **calibration_trigger 候选**: pool 失败 3 连 + reserve 累计 12+ + zero_admit 9 连 (跨方向). 应升格 4 条 lessons: (i) **RHS 锁源律** (T017 axis cluster anchor 在 RHS Mean H-L 60d); (ii) **T006 律跨 atom 普适** (Corr atom 同字段跨窗口实证); (iii) **库 clean ≠ tradable alpha** 第 4 次复现 (升格警示); (iv) **num_trades atom-class scope refinement** (atom-class 依赖律仅 close-position 域成立).
- (c) **T017 reserve 火种统一管理**: b066 C005 + b087 C001 + b093 C005 形成"Corr(X, overnight_gap, N) atom × LHS-family"系列 reserve (X ∈ {volume, num_trades}), 等 F019 anchor 退役或 RHS basis 真换才能批量 admit. 当前 reserve 池: T017 axis 3 个 + T011 axis 1 个 (b080 C006) = **本方向累计 reserve 4 个**.
- (d) **下批方向选择**: 本方向 saturated + ROI 极低. cockpit 应切换 direction (考虑: alpha191_universal_subset productive b085/b086 还有空间; range_structure productive; gap_acceptance_structure productive). 或 calibration_trigger 命中 → 进 Phase 5 consolidation.
- (e) **pool #4 mechanism 后续**: 标注 inconclusive, 不再设计 T017 axis horizon-switch 候选, 改 expression-rewrite revival (e.g. RHS swap to non-vol_20d basis) 或 anchor-retirement 路径.
