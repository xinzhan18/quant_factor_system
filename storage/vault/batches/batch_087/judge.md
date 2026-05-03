---
batch_id: batch_087
direction: overnight_intraday_split
judged_at: 2026-05-03T08:20:00Z
candidates:
  - {candidate_id: C001, verdict: reserve}
  - {candidate_id: C002, verdict: reject}
  - {candidate_id: C003, verdict: reject}
  - {candidate_id: C004, verdict: reject}
  - {candidate_id: C005, verdict: reject}
  - {candidate_id: C006, verdict: reject}
batch_summary: {total: 6, admit: 0, reserve: 1, reject: 5}
admit_count: 0
reject_count: 5
reserve_count: 1
candidate_count: 6
mt_bucket: high
---

# batch_087 Judge Summary

> [!abstract]+ batch_087 · [[directions/overnight_intraday_split]] · 6 candidates
> ✅ **admit=0** · ⏸ **reserve=1** (C001 T017 Corr-60 extension) · ❌ **reject=5** (C002/C003/C004/C005/C006)
> **核心发现**: T017 axis (Corr volume × overnight_gap atom) 60d 长窗 + RHS swap 是本方向 **唯一未被结构性饱和的 thread** (b066 reserve → b087 reserve, 第 2 次 reserve fire), C001 9/9 年正 + mono=1.0 + IC anti-decay 但 vol_20d_exp=17.78 + max_corr=0.45@F019 + incr_ic=0.011 同时落 borderline cluster (alpha_surv=0.20 < rank_diff floor 0.30). T011 axis 4 fresh atom (C002/C003/C004/C005) 全失败再实证 b080 ANSWERED-saturated. **C005 揭示新升格律**: csi1000 daily zero-mean stationary return 下 `Cov(X,Y,N) ≈ Mean(XY,N)`, F023 已 admit (Mean of product) 让所有 Cov(o,i,N) atom 自动 near_dup.
> **MT Budget**: cumulative 480 → **486** · direction 51 → **57** · bucket `high` (search_adjusted=medium)

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ⏸ reserve | mixed·**borderline-weak**·poor·**borderline**·stable | ic_oos=0.032 ls_t=1.77 mono=1.00 alpha_surv=0.20 max_corr=0.45@F019 incr_ic=0.011 9/9_pos | T017 Corr-60 长窗 + RHS swap (range_60): vol_20d_exp=17.78 + 4 risk flags 联立, 但 sign_consistency=1.0 + horizon ladder 1d→20d IC 0.032→0.073 强长 horizon 信号火种 | [[batches/batch_087/candidates/C001]] |
| C002 | ❌ reject | hard_gate | ic_oos=0.0017<0.008 + max_corr=0.828@F003 | overnight gap / |intraday body| TsRank-60 standalone: 与 F003 单边 overnight 几何重叠 + cross-section 信号塌缩 noise | [[batches/batch_087/candidates/C002]] |
| C003 | ❌ reject | hard_gate | ic_oos=-0.0033<0.008 + max_corr=0.586@F012 | signed flow density Rank-60 rank-diff: 共享 amount denominator 撞 F012 amihud cluster + 整体 weak 反向 | [[batches/batch_087/candidates/C003]] |
| C004 | ❌ reject | hard_gate (3-fail) | sign_flip + ic≈0 + decay=-14.78 | |overnight| Rank-60 rank-diff × num_trades_60: P008 escape 不能拯救 magnitude-form, vol_20d 二阶载体律 b066 复现 | [[batches/batch_087/candidates/C004]] |
| C005 | ❌ reject | hard_gate | corr=0.927@F023 (>0.9) | Cov(o, i, 20) × amount_120: 与 F023 (Mean((o)*(i),20)) cross-section 0.927 — **Cov ≈ Mean of product 等价律新升格** | [[batches/batch_087/candidates/C005]] |
| C006 | ❌ reject | hard_gate (3-fail) | sign_flip catastrophic + ic≈0 + decay=-0.06 | num_trades × |Δret| / amount TsRank-60: train→val regime sign-flip + 库 max_corr=0.133 最 clean 但 OOS dead — "库 clean ≠ tradable alpha"反例 | [[batches/batch_087/candidates/C006]] |

## 跨候选对比

- **T017 vs T011 cleavage 显著**: 仅 T017 thread 候选 (C001) 通过 hard_gate; T011 axis 候选 (C002/C003/C004/C005 magnitude/ratio/Cov 形式) **4/4 hard_gate fail**, 与 b080 T011 axis 6 fresh atom 全失败同律. T017 Corr atom 时序 covariance 是该方向**唯一未饱和**的几何空间.
- **vol_20d 几何困境再实证**: C001 alpha_surv=0.20 dom=vol_20d (exposure=17.78) — "逃 vol_20d 必撞 anchor cluster" 几何困境 b066/b080 第 3 次实证 (F019/F021 cluster, max_corr=0.45 borderline + incr_ic=0.011 < F203 0.015 缺口 25%).
- **C005 Cov ≈ Mean of product 等价律 (新升格 lessons 候选)**: csi1000 个股 daily-bar overnight return Mean(20) ≈ 0 + intraday body Mean(20) ≈ 0 让 `Cov(X,Y,N) = E[XY] - E[X]E[Y] ≈ E[XY]` — F023 (Mean(X*Y, 20)) admit 让所有 Cov(overnight, intraday, N) 自动 cross-section near_dup (本批实测 0.927). 与 lessons.md "In-batch denominator family 等价性自检 (P024)" 同律, 应升格 Phase 1 self-check 第 9 条: "csi1000 daily zero-mean stationary return-pair 下 Cov(X,Y,N) 与 Mean(X*Y,N) 数学近似等价, 已 admit Mean(X*Y) 后 Cov(X,Y) 必 near_dup".
- **P008 escape 路径在 overnight family standalone 失败 (C002 + C006)**: TsRank-60 wrap on ratio fields 不能 standalone 兑现 — 必须配 rank-diff 几何 + 跨段 RHS basis (与 F024/F025 admit 路径同型). C002 (overnight/intraday body ratio) 撞 F003 单边 overnight 几何; C006 (num_trades × |Δret| / amount) 库 clean (max_corr=0.133) 但 OOS sign-flip — "库 clean ≠ tradable alpha" 反例 (alpha_surv 不达标且 train→val regime drift).
- **incr_ic 中位数趋势**: b080 0.0098 (1 reserve borderline) → b086 全负 (-0.016 cross-direction) → b087 仅 C001 +0.011 borderline (其余 hard_gate 不计算). 本方向 alpha edge 收窄: 从 b059 F023 admit 时 incr_ic=0.018 强 → b080 borderline 缺口 33% → b087 borderline 缺口 25% — 整体仍 vol_20d-locked + 4-anchor cluster 占据.
- **MT 预算推进**: direction_candidates 51 → 57; cumulative 480 → 486. 本方向 round 87 (第 14 round), zero_admit_streak 4 → 5.

## Thread 进展

> [!note]+ T017 [[directions/overnight_intraday_split#T017]] — `[◉ ACTIVE]` (推进 + 火种续命)
> reserve 1 (C001). T017 b066 C005 reserve fire (Corr(volume, overnight_gap, 20) × Std(volume,60) alpha_surv=1.16 ls_t=1.26<2) 60d 长窗 + RHS axis swap (range_60) 后, ic_oos 从 0.009 → 0.032 显著强化 + ls_t 1.26 → 1.77 (仍<2) + mono_oos 1.0 完美 + 9/9 年正 + IC anti-decay (IS=0.014 → OOS=0.032) + horizon ladder 1d=0.032→20d=0.073 长 horizon 真信号. 但 alpha_surv 从 1.16 → 0.20 大幅退化 (RHS Std(volume,60) 是 vol-magnitude basis 自然减除, 改 range_60 让 cross-section vol_20d basis 重新嵌入). max_corr=0.45@F019 borderline + incr_ic=0.011 < F203 borderline gate 0.015 缺口 25%. **T017 axis 跨 batch 火种续命** (b066 → b087), 复活路径仍 (a) F019 退役; (b) evaluation policy 调长 horizon (本候选 20d IC=0.073 显著); (c) Python OLS residualize on vol_20d (但 b071 此路径 OOS sign-flip 风险高).

> [!note]+ T011 [[directions/overnight_intraday_split#T011]] — `[✗ ANSWERED-saturated batch_080+batch_087]`（再实证）
> reject 4 (C002/C003/C004/C005). b080 T011 axis 6 fresh atom 全失败之后, 本批 4 fresh probes 再次 0/4 admit:
> - **C002 standalone TsRank ratio**: P008 escape 在 overnight family standalone 不能兑现, ic_oos=0.0017 sub-threshold + max_corr=0.828@F003;
> - **C003 signed flow density rank-diff**: 共享 amount denominator 撞 F012 cluster, ic_oos=-0.0033 反向 weak;
> - **C004 |overnight| Rank-60 rank-diff**: P008 escape 不能拯救 magnitude form, sign_flip + decay=-14.78;
> - **C005 Cov(o, i, 20)**: 数学近似 F023 Mean((o)*(i), 20), 0.927 near_dup hard_gate.
>
> T011 axis 进一步 saturation 证据增至 ≥10 fresh atom (b080 6 + b087 4) 全失败, magnitude / ratio / signed-flow / Cov 四类形式跨段几何全部撞 anchor cluster (F010/F018/F023/F012/F003). 仅 b080 C006 reserve (60d turnover-weighted overnight) 与 b087 C001 T017 reserve 是该 direction 仍存的火种.

## 方向级反思

本方向 round 14 (b087) 兑现率 0/6 admit + 1/6 reserve, 与 b066 (0+1) / b080 (0+1) 形成**连续 3 round zero-admit borderline-reserve** 模式. 主要发现:

1. **T017 thread 跨 batch 火种续命** (新机制): C001 是 T017 b066 C005 的"长窗 + RHS swap" 兑现尝试, ic_oos 显著强化 (0.009 → 0.032) 但 alpha_surv 退化 (1.16 → 0.20) — RHS axis swap 让 cross-section vol_20d basis 重新嵌入. 提示: T017 真正复活路径不是"换 RHS"而是"换 evaluation policy" (长 horizon 评估) 或 "换 LHS atom" (Python residualize on vol_20d basis).

2. **T011 axis 真饱和复证 (n=10+ fresh atom)**: b080 6 + b087 4 = 10+ fresh magnitude / ratio / signed / Cov / TsRank wrap 全失败. 本方向 magnitude product axis 真 absorbing prototype 锁定, F023 (Mean of product) admit 后所有跨段 magnitude 几何 cross-section 撞 cluster. **建议**: T011 thread 状态从 `ANSWERED-saturated b080` 升级到 `[✗ DISPROVEN-comprehensive b087]` 强信号 (≥10 atom 跨多 form 实证).

3. **C005 Cov ≈ Mean of product 等价律 lessons 候选**: 新发现 — csi1000 daily zero-mean stationary return-pair 下 Cov(X,Y,N) ≈ Mean(X*Y,N) 数学近似等价 (Mean(return) ≈ 0 让 cov 二阶项消失). 应升格 Phase 1 generator AST 自检第 9 条 (与 P024 In-batch denominator equivalence 同律). 实操: candidate 含 `Cov(return_A, return_B, N)` + 库内已 admit `Mean(return_A * return_B, M)` (相近窗口) → 必然 cross-section near_dup, Phase 1 reject.

4. **P008 escape 路径在 overnight family 不能 standalone 兑现** (C002+C006 双重证据): TsRank-60 wrap on ratio fields 必须配 rank-diff 几何 + 跨段 RHS basis (F024/F025 admit 路径同型). C002 (overnight/intraday body ratio) 撞 F003 单边 overnight (max_corr=0.828); C006 (num_trades × |Δret| / amount) 库 clean (max_corr=0.133) 但 OOS sign-flip + alpha_surv 不达标 — "库 clean ≠ tradable alpha" 又一反例.

**Edge 评估**: 本方向 alpha edge 极度收窄 — round 11 b066 incr_ic=0 borderline → round 13 b080 incr_ic=0.0098 borderline → round 14 b087 incr_ic=0.011 borderline. 三连"borderline reserve fire" 模式 (b066 C005 / b080 C006 / b087 C001) 显示**该方向真正可挖空间已锁在 T017 axis 单一 thread**, 且 evaluation policy 不调整无法兑现.

**下一步建议**:
- (a) **本方向应翻 saturated**: 14 rounds 9 admits + 连续 3 round zero-admit + 5/6 thread closed + 仅 T017 reserve 火种 — saturated 触发条件 (连续 2+ batch reject > 80%, 已超 3 倍). LLM 在本批 narrative 应翻 status `productive → saturated`.
- (b) **触发 consolidation_trigger** (rounds_since_consolidation=5+1=6 临近 10 阈值, zero_admit_streak=5 + 多方向 saturated 显化). 优先升格三条 lessons: (i) T011 axis comprehensive saturation (≥10 atom 跨 form 实证); (ii) Cov ≈ Mean of product 等价律 (P028 升格); (iii) "库 clean ≠ tradable alpha" 又一反例 (C006 max_corr=0.133 OOS sign-flip).
- (c) **T017 reserve 火种统一管理**: b066 C005 + b087 C001 形成"Corr(volume, overnight_gap, N) atom × varying RHS" 系列 reserve, 等 F019/F002/F012 anchor 任一退役或 long-horizon evaluation policy 后批量 retro audit.
- (d) **本方向新候选 ROI 极低**, 下批应切换 direction (按 cockpit 该方向是唯一 productive, 但 saturated 后应触 consolidation 找新方向).

**Calibration trigger 检查** (本 batch 0 admit + 1 reserve):
- 错杀 flag 跨候选反思: 无 — C001 alpha_surv=0.20 < 0.30 floor 是真 vol_20d-locked, 不满足 over-rejection 4 条件 (max_corr<0.30 + incr_ic>0.010 + mono>0.8 + sign_consistency=1.0 — 仅 2/4 满足: incr_ic=0.011 + mono+sign 均合格, 但 max_corr=0.45 + alpha_surv=0.20 不合格).
- 连续零 admit 警戒: 本方向 b066/b080/b087 3 batch 0 admit + 各有 1 reserve. 累计 reserve 满足 "max_lib_corr<0.30 + incremental_ic>0.010"? C001 max_corr=0.45 不满足; b066 C005 max_corr=0.46 不满足; b080 C006 max_corr=0.56 不满足. **3 reserves 全 borderline cluster, 不存在错杀候选**, 不触发 calibration.
- Reserve 积压: 不评估系统级数据.
- 悖论复现: T017 reserve 跨 batch 续命 (b066 → b087) 形成"alpha_surv 一高一低 (1.16 vs 0.20) + ls_t 都 <2" 悖论, 但已被 lessons.md "Barra-clean ≠ library-clean" 解释, 不触发 calibration.

无明确 calibration trigger. **触发 consolidation_trigger 候选** (rounds_since_consolidation=6 临近 10, 多方向 saturated + lessons 升格累积). 推进 Phase 4 archive.
