---
batch_id: batch_066
direction: overnight_intraday_split
judged_at: 2026-05-01T13:30:00Z
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
mt_bucket: medium
---

# batch_066 Judge Summary

> [!abstract]+ batch_066 · [[directions/overnight_intraday_split]] · 6 candidates
> ✅ **admit=0** · ⏸ **reserve=1** (C005 volume×overnight_gap Corr × volume_std) · ❌ **reject=5** (1 P006 borderline + 4 alpha_surv vol_20d 吞噬 含 1 reducer trap)
> **核心发现**: T014 (autocorr) / T015 (Skew/Kurt 形状 moment) / T016 (Rank wrap) / T017 (Corr atom) **四 thread 全在 csi1000 cross-section vol_20d basis 上撞墙** — 所有 6 候选 dominant_style=vol_20d, alpha_surv 最高 1.16 (C005, 唯一 Barra-clean) 最低 0.03 (C004). **关键反例**: C002 max_corr=0.13 库内最 clean + ls_t=2.46 + 9/9 年 7 positive 但 alpha_surv=0.06 — autocorr atom 也是 vol_20d 几何载体. **C005 reserve = direction 第二层 hot topic**: alpha_surv=1.16 cleanest in batch + sign_consistency=1.0 + 9/9 年正 + mono=1.0/1.0 完美; 但 train→val IC decay 0.019→0.009 (50% 衰减) + ls_t_oos=1.26 < 2 borderline + incr_ic=-0.001 — Barra-clean 但库已先吸收同 alpha 维度 (corr=0.46@F002 + 0.38@F012 + 0.37@F018 三方向饱和).
> **P003 形状 moment 验证**: Skew (C003 mono_oos=0.9 alpha_surv=0.07) + Kurt (C006 mono_oos=1.0 alpha_surv=0.07) 双独立证 — 形状 moment **不** sign-flip (C003/C006 sign consistency=1.0 train→val 同号), 但**仍被 vol_20d 吸收** — 与 P003 raw return Std/Var 不同律 (regime stable) 但与 P004 同律 (vol_20d structural absorption). 升格 lessons 候选: "Skew/Kurt of raw return 不 P003-flip 但 P004-absorb — 形状 moment cross-section rank 仍 monotone equivalent to vol_20d via heavy-tailedness ↔ daily vol covariation".
> **MT Budget**: cumulative 354 → **360** · direction 39 → **45** · bucket `medium`（6 candidates 全 hard_gate pass; raw bucket `high` 但 search_adjusted 因 direction.exposure 满 + family 0.92 高位 推到 `low/medium`）

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | 🟡·🟢·🟠·🔴·🟢 | ic_oos=0.010 ls_t=1.92 alpha_surv=0.32 max_corr=0.527@F002 incr_ic=-0.002 | T014 overnight autocorr × volume — alpha_surv 仅过 rank_diff floor 0.30; max_corr borderline [0.30,0.70] + incr_ic=-0.002<0.015 (F203) — P006 reducer trap | [[batches/batch_066/candidates/C001]] |
| C002 | ❌ reject | 🟡·🟢·🔴·🟢·🟡 | ic_oos=0.014 ls_t=2.46 alpha_surv=0.06 max_corr=0.131@F002 incr_ic=+0.005 | T014 mirror — intraday autocorr × PE — **库内最 clean** (max_corr=0.13 + incr_ic=+0.005) 且 ls_t 强 + mono=1.0 但 alpha_surv=0.06 critical (vol_20d=5.77 + book_to_price=0.62 + ep_ratio=1.22) — autocorr atom 也是 vol_20d 几何载体, T003 disprove "intraday body=random walk" 复现 (intraday autocorr ~0 时只能借 vol_20d basis 形成 cross-section signal) | [[batches/batch_066/candidates/C002]] |
| C003 | ❌ reject | 🟢·🔴·🔴·🟡·🟢 | ic_oos=0.023 ls_t=1.07 mono_oos=0.9 alpha_surv=0.07 max_corr=0.323@F002 | T015 overnight Skew × PB — ls_t weak + alpha_surv=0.07 (str_1m=1.99 + vol_20d=5.77 双吞噬) — **P003 形状 moment 验证: 不 sign-flip 但 P004 absorb** | [[batches/batch_066/candidates/C003]] |
| C004 | ❌ reject | 🟢·🟡·🔴·🔴·🟢 | ic_oos=0.021 ls_t=1.53 alpha_surv=0.03 max_corr=0.611@F010 incr_ic=-0.005 | T016 Rank wrap of F010 atom — max_corr=0.611@F010 borderline cluster + incr_ic=-0.005 negative library reducer + alpha_surv=0.03 critical (vol_20d=9.24 极值) — TsRank wrapper 不脱 F010 anchor cluster | [[batches/batch_066/candidates/C004]] |
| C005 | ⏸ reserve | 🟡·🟠·🟢·🟡·🟢 | ic_oos=0.009 ls_t=1.26 alpha_surv=**1.16** max_corr=0.461@F002 incr_ic=-0.001 mono=1.0/1.0 ic_by_year 9/9 正 | T017 量×overnight_gap Corr × volume_std — **库内首 alpha_surv>1.0 候选** (Barra residual IC > raw IC, 形式上 Barra-clean) + sign_consistency=1.0 + 9/9 年正 + mono 完美 + cum_mdd=-1.66 浅; 但 train→val IC decay 0.019→0.009 (52% 衰减) + ls_t_oos=1.26<2 + incr_ic=-0.001 — Barra-clean 但已被 F002/F012/F018 三方向 ~0.37-0.46 cluster 部分吸收, ls_t 不投资. CP05 borderline cluster + Barra-clean 矛盾值得保留追踪 (等 evaluation policy 调整或 horizon mismatch 验证) | [[batches/batch_066/candidates/C005]] |
| C006 | ❌ reject | 🟢·🟢·🔴·🟡·🟢 | ic_oos=0.024 ls_t=3.22 mono_oos=1.0 alpha_surv=0.07 max_corr=0.602@F012 incr_ic=+0.006 | T015 mirror — overnight Kurt × amount_120 — ls_t 本批最强 + mono 完美 + 9/9 年 8 positive + horizon anti-decay (1d=0.024→20d=0.079); 但 alpha_surv=0.07 critical + max_corr=0.602@F012 borderline + incr_ic=+0.006<0.015 (F203 borderline gate) — Kurt 4th moment 与 F012 amihud (2nd magnitude) 共 vol_20d basis — **P003 形状 moment 验证: 与 C003 同律, 形状 moment 不 sign-flip 但 P004 absorb** | [[batches/batch_066/candidates/C006]] |

**档位编码**：🟢 最优档（aligned/strong/good/low/stable）· 🟡 次档（mixed/borderline/acceptable/medium）· 🟠 边际（borderline）· 🔴 阻断档（misaligned/weak/poor/high/unstable）· `hard_gate` reject 该列写 `hard_gate` 不填色。整列飘红 = 方向级警示。

## 跨候选对比

- **Style 聚合**: 6/6 候选 dominant_style=vol_20d, exposure 范围 5.77 (C002) → 18.95 (C005 极值). 整批 LHS atom (autocorr / Skew / Kurt / Rank / Corr) 全部 vol_20d 几何载体 — manifest 第 1 条 "LHS atom 必 vol_20d 几何正交" **整体破产**, 与 b065 trend_residual_geometry 同律 (operator-family novelty ≠ style novelty). C005 vol_20d=18.95 极值但 alpha_surv=1.16 反向 — Corr-atom 是 raw $volume × raw gap, vol_20d 共变但 Barra OLS residual 后 IC 反而上升 (rank-order 几何在 residual space 仍保留)
- **相关度 cluster**: C001/C002/C005 nearest=F002 (PB×amount value-liq anchor), C003/C006 nearest=F002/F012 (Amihud microstructure anchor), C004 nearest=F010 (本方向 5d overnight Mean). **F002 anchor 在 6/6 候选中均出现 corr 0.13-0.61** — fundamental_value × volume_proxy 几何位置在本方向 LHS 也共振. C005/C006 双双 corr~0.4@F018 也提示 sign-freq + magnitude × 量价共振几何位置部分共享. 候选互相关均 <0.40 (彼此独立 atom)
- **MT 预算推进**: cumulative_candidates 354→360; direction_candidates 39→45; 6 个 candidates 全过 hard_gate, raw bucket=high (direction.exposure=1.0 满 + family=0.918 高位); search_adjusted 推到 low (C001/C005) / medium (C002/C003/C004/C006)
- **关键观察**: C002 + C005 形成 "library-clean (max_corr<0.50) 与 Barra-clean (alpha_surv>1.0)" 的有趣对照:
  - C002 max_corr=0.13 ✓ + alpha_surv=0.06 ✗ → "库 clean 但 Barra 脏"
  - C005 max_corr=0.46 ✗ + alpha_surv=1.16 ✓ → "Barra clean 但库 cluster"
  - **不存在双 clean 候选** — 即"逃 vol_20d 必撞 library anchor" 的 csi1000 几何困境复现 (lessons.md "Barra-clean ≠ library-clean" 律实证) — F002/F012 anchor cluster 占据 vol_20d-orthogonal subspace, 反向也成立

## Thread 进展

> [!failure]+ T014 [[directions/overnight_intraday_split#T014]] — `[✗ DISPROVEN batch_066]`
> **Question**: lag-1 autocorr atom (overnight_ret 与 intraday_ret) 是否在 csi1000 cross-section rank-diff 几何下携带独立于 magnitude/sign atom 的新 alpha?
>
> **Answer**: **autocorr atom 也是 vol_20d 几何载体, 形式上的 ordinal 持续性度量 (Corr ∈ [-1,1]) 在 cross-section rank 上**仍 monotone equivalent to vol_20d**.
>
> reject C001 (overnight autocorr × volume_60: alpha_surv=0.32 仅过 rank_diff floor + max_corr=0.527 borderline + incr_ic=-0.002 — F203 borderline reducer) + reject C002 (intraday autocorr × pe_60: ls_t=2.46 strong + max_corr=0.13 库内最 clean + 9/9 年 7 positive 但 alpha_surv=0.06 critical — vol_20d=5.77 + ep_ratio=1.22 + book_to_price=0.62 共吞噬). **机理**: stocks with persistent overnight directionality 在 csi1000 上倾向于是 high-vol 名 (institutional accumulation 集中在小盘 vol-extreme), 所以 autocorr cross-section 排名与 vol_20d 排名 monotone-equivalent. 若改 minute-bar 数据 / 长 horizon evaluation, autocorr 可能脱 vol_20d basis — 当前 daily-bar + 1d horizon 下封闭.
>
> **Final state (b066 DISPROVEN)**: T014 双侧探针 (overnight + intraday) 0/2 admit. autocorr atom 在 csi1000 daily-bar cross-section 上 closed.

> [!failure]+ T015 [[directions/overnight_intraday_split#T015]] — `[✗ DISPROVEN batch_066]`
> **Question**: shape moment (Skew/Kurt of overnight_ret 20d) 作为 LHS 是否与 magnitude moment (F019 body Std / F020 gap Std) 几何独立, 且 P003 higher-moment regime sign-flip 律是否同样作用?
>
> **Answer**: **形状 moment 不 P003-flip (regime stable) 但 P004-absorb (vol_20d structural absorption)** — 跨阶 (3rd Skew + 4th Kurt) 双侧验证.
>
> reject C003 (Skew(overnight,20) × pb_60: ls_t=1.07 weak + mono=0.9 alpha_surv=0.07; sign_consistency=1.0 9/9 年 7 positive — **不 sign-flip**) + reject C006 (Kurt(overnight,20) × amount_120: ls_t=**3.22** 本批最强 + mono=1.0 完美 + horizon anti-decay (1d=0.024→20d=0.079) + 9/9 年 8 positive + 2023 IC=0.030 强势; 但 alpha_surv=0.07 critical + max_corr=0.602@F012 borderline + incr_ic=+0.006<0.015 — vol_20d=9.49 显著吞噬). **机理对比 P003**: P003 raw return Std/Var 在 train→val regime 翻号是因为 train (低利率成长) 与 val (利率上行价值回归) 的横截面 vol-magnitude 重排; **形状 moment (Skew/Kurt) 度量分布形状, 在 regime 切换中形状稳定** (csi1000 个股 daily return 总是右偏 + 高峰度, 不随 regime drift). 但**与 vol_20d 共变** — heavy-tailed 股票通常 = high-vol 股票, 所以 Kurt cross-section rank 与 vol_20d rank monotone-equivalent.
>
> **Lessons 升格候选**: "Skew/Kurt of raw return 形状 moment 在 csi1000 train→val regime stable (不 P003-flip), 但 cross-section rank 与 vol_20d 仍 monotone-equivalent (P004 absorb 同律) — heavy-tailedness ↔ daily-vol covariation. 跨阶证据: 3rd (b066 C003) + 4th (b066 C006) 同律."
>
> **Final state (b066 DISPROVEN)**: T015 形状 moment LHS 在 csi1000 daily-bar 几何上虽 regime-stable 但被 P004 vol_20d basis absorbed. 仅 minute-bar / 长 horizon evaluation 可能复活, 当前 daily-bar 下封闭.

> [!failure]+ T016 [[directions/overnight_intraday_split#T016]] — `[✗ DISPROVEN batch_066]`
> **Question**: TsRank/Rank wrap of admitted atom (F010 overnight_5 base) 是否生成新的 cross-section ordering, 独立于原始 atom?
>
> **Answer**: **Rank wrapper 仅是 within-name normalization, 不脱 F010 cluster** — TsRank/Rank 把 X 转换为 within-name historical 0-1 rank, cross-section ordering 与原 X 高度相关 (corr=0.61).
>
> reject C004 (Rank(Mean(overnight_ret,5),60) × ps_60: max_corr=0.611@F010 borderline cluster + incr_ic=-0.005 negative library reducer + alpha_surv=0.03 critical (vol_20d=9.24)). **机理**: TsRank wrapper 改变 within-name signal magnitude 但不改 cross-section ordering — F010 已 admit overnight_5 cross-section, Rank wrap 后只是缩放但 rank 几乎保留. 类比 Operator Registry "Rank-preserving 单算子变体零增量律".
>
> **Final state (b066 DISPROVEN)**: T016 Rank wrap 不脱已 admit atom anchor cluster, 在 csi1000 cross-section 几何上 closed.

> [!warning]+ T017 [[directions/overnight_intraday_split#T017]] — `[◉ ACTIVE]` (1 reserve, 待 evaluation policy 调整)
> **Question**: Corr($volume, overnight_gap, 20) within-name 时序 covariance atom 是否独立于 magnitude (F023) / sign-freq (F018) 维度?
>
> reserve C005 (Corr atom × volume_std: ic_oos=0.009 weak ls_t=1.26 + alpha_surv=**1.16** Barra-cleanest + sign_consistency=1.0 + mono=1.0/1.0 + 9/9 年正 + cum_mdd=-1.66 浅; 但 train→val IC decay 0.019→0.009 50% 衰减 + ls_t_oos=1.26 < 2 + incr_ic=-0.001 + max_corr=0.46@F002 cluster). **关键**: alpha_surv>1.0 极少见 (Barra residual IC > raw IC, 形式上 Barra-clean), 但 ls_t_oos 不投资 + 已被 F002/F012/F018 三方向 ~0.37-0.46 cluster 部分吸收. **CP05 borderline cluster + Barra-clean 矛盾**: F002 anchor (PB×amount) 在 vol_20d-orthogonal subspace 占据中心, Corr atom 即使 Barra-clean 也撞 anchor cluster — 验证 lessons.md "Barra-clean ≠ library-clean" 反向亦成立.
>
> **下一步**: T017 待 evaluation policy 调整 (e.g., 长 horizon admission 标准 / Barra residual 后 ls_t 重测) 或 F002/F012 退役后重测.

## 方向级反思

**核心律**: 本批揭示 csi1000 daily-bar cross-section 上 **"逃 vol_20d 必撞 library anchor" 几何困境**:
- C002: max_corr=0.13 库内最 clean ✓ + alpha_surv=0.06 vol_20d 吞噬 ✗
- C005: alpha_surv=1.16 Barra cleanest ✓ + max_corr=0.46@F002 anchor cluster ✗
- 整批 6/6 dominant_style=vol_20d (b065 trend_residual_geometry 同律)
- "**双 clean 候选不存在**" — F002/F012 anchor cluster 占据 vol_20d-orthogonal subspace

**hot_topic P003 形状 moment 边界律 (新升格候选)**:
- C003 (Skew) sign_consistency=1.0 + 9/9 年 7 positive — **不 P003-flip**
- C006 (Kurt) sign_consistency=1.0 + 9/9 年 8 positive + horizon anti-decay — **不 P003-flip 且强**
- 但 C003+C006 alpha_surv=0.07 双低 — **P004 absorb**
- 升格 lessons: "Skew/Kurt of raw return 形状 moment 与 P003 raw return Std/Var 不同律 — regime stable 但仍 P004 absorb"

**hot_topic P004 vol_20d structural absorption 跨阶复现**:
- 1st moment (Mean overnight): F010/F011 admit (本方向源头)
- 2nd moment (Std/Var): P003 sign-flip
- 3rd moment (Skew): C003 P004 absorb (b066)
- 4th moment (Kurt): C006 P004 absorb (b066)
- correlation moment (autocorr/Corr): C001/C002/C005 P004 absorb (b066)
- 整阶 moment family 在 csi1000 daily-bar cross-section 几何上 vol_20d-locked — operator family novelty 不解决 style 重表达

**zero_admit_streak**: b065=5→b066=6 (连续 6 批 zero admit). 仍未触 calibration trigger (3 批中无错杀候选 — 真正被错杀候选需满足 max_corr<0.30 + incr_ic>0.010 + mono>0.8 + sign_consistency=1.0; b066 C002 max_corr=0.13 + sign_consistency=1.0 + mono=1.0 ✓ 但 incr_ic=+0.005<0.010 不满足完整错杀 signature). 接近 consolidation trigger (rounds_since_last=6→7, 距 10 阈值 3 批).

**hot_topic P006 library_reducer 部分复现**:
- C001 (incr_ic=-0.002) + C004 (incr_ic=-0.005) 双 reducer 命中
- 但都未达到 hard-block 严格四要件 (mono≥0.85 ∧ ls_t≥2.5 ∧ incr_ic≤-0.005 ∧ alpha_surv≤0.30)
- C004 incr_ic=-0.005 ✓ alpha_surv=0.03 ✓ ls_t=1.53 ✗ — 仅 ls_t 不够强未触 hard-block, 走常规 reject

**MT Budget 状态**: cumulative 354→360 · direction 39→45 · bucket `medium` (search_adjusted)

**下轮建议**:
1. **本方向 status**: productive (已有 9 admit) → 转 saturated. 新形状 moment / autocorr / Corr atom 全部 vol_20d-locked, T012/T013/T014/T015/T016 已 closed, T017 仅 reserve 火种. 信号设计层证据 ≥3 路径 cluster (autocorr/Skew/Kurt/Rank 跨 4 atom 同 P004 absorb) + 数据契约层 minute-bar 不可达, 满足双层 saturated 证据律
2. **方向切换**: 鉴于 zero_admit_streak=6 + overnight_intraday_split saturated, 下批应切换 direction. 未饱和高产候选: amount_volatility_signal (productive, F004/F043/F045 等持续 admit) / microstructure_illiquidity (productive, F012/F015/F016) / range_structure (productive). 严避近期 saturated/dead (trend_quality_gated dead / log_value_liquidity dead / fundamental_momentum dead / pv_covariance dead / asymmetric_momentum dead)
3. **错杀侦测**: 本批无候选触发完整错杀 flag (max_corr<0.30 + incr_ic>0.010 + mono>0.8 + sign=1.0 + nearest 反号 五条件无候选全满足), 无 calibration trigger
4. **C005 reserve 火种**: 等 F002 retire / evaluation policy 调长 horizon (10d-20d C005 IC 显著上升 0.016-0.025 + ICIR 0.17-0.27) 或 Barra residual ls_t 重测
5. **consolidation 临近**: rounds_since_last=6→7, 距 10 阈值 3 批; 若下 3 批仍 zero_admit 应优先触 consolidation (lessons 升格 P003/P004 形状 moment 边界律 + autocorr P004 absorb + "逃 vol_20d 必撞 anchor" 律)
