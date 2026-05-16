---
batch_id: batch_102
direction: tsrank_diff_form
judged_at: 2026-05-16T08:10:00Z
candidates:
  - {candidate_id: C001, verdict: reject}
  - {candidate_id: C002, verdict: reject}
  - {candidate_id: C003, verdict: reserve}
  - {candidate_id: C004, verdict: reject}
  - {candidate_id: C005, verdict: reject}
  - {candidate_id: C006, verdict: reserve}
batch_summary: {total: 6, admit: 0, reserve: 2, reject: 4}
admit_count: 0
reject_count: 4
reserve_count: 2
candidate_count: 6
mt_bucket: medium
---
# batch_102 Judge Summary

> [!abstract]+ batch_102 · [[directions/tsrank_diff_form]] · 6 candidates
> ❌ **admit=0** · ⏸ **reserve=2** (C003 / C006) · ❌ **reject=4** (C001/C002 hard_gate sign_flip; C004 P030 paradox; C005 noise)
> **核心发现**: 跨字段 TsRank-diff hypothesis **部分成立 + 部分坍缩**. C006 (intraday vs overnight) **CP03 strong 3/3 + mono -0.9 + 9 年 robust** 但 **incr_ic=-0.006 NEGATIVE** — TsRank-diff 倾向坍缩到现有 raw alpha 的 ordinal rotation (与 F003 max_corr=-0.694 镜像). C003 (size-coupled vs scale-free 流量) **mono OOS -1.0 perfect + max_corr 0.26 库空间独立** 但 ls_t=-1.67 < 2.0 cross-section dispersion 不达 admit floor. **P032 律 (CsRank-diff cross-domain) 可能扩展至 TsRank-diff form**: 跨字段 TsRank-diff 不构成新几何空间, 仅 ordinal rotation 或 cross-section dispersion-ceiling-limited 信号.
> **MT Budget**: cumulative 570 → **576** · direction 0 → **6** · bucket `medium` (search_adjusted 0.22-0.59) · 本批 low=2 / medium=4 / high=0

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | hard_gate | sign_flip + oos_decay -16.6 | val 期强信号 (ls_t=-7.48 + mono -0.9) 但 train ≈ 0 → regime-dependent, val-only alpha | [[batches/batch_102/candidates/C001]] |
| C002 | ❌ reject | hard_gate | sign_flip + oos_decay -2.34 | 9 年 ic_by_year 从 -0.038 (2015) 单调漂到 +0.020 (2023), structural regime drift not noise | [[batches/batch_102/candidates/C002]] |
| C003 | ⏸ reserve | aligned·weak·acceptable·low·stable | ic_oos=-0.015 ls_t=-1.67 mono=-1.0 max_corr=0.26 alpha_surv=0.80 | 错杀件 4/4 全中 (mono perfect + 库独立 + 错号 vs F028 + sign 一致), ls_t magnitude 不足 → cross-section dispersion ceiling 律 (同 rank_diff_liquidity_microstructure) | [[batches/batch_102/candidates/C003]] |
| C004 | ❌ reject | misaligned·weak·**poor**·medium·**unstable** | alpha_surv=4.29 P030 + ls_t=-0.15 noise + mono OOS 1.0→-0.1 collapse | P030 paradox 严重 (Barra residual 反向放大 noise), PV-divergence 在 TsRank-diff 形式无 cross-section spread | [[batches/batch_102/candidates/C004]] |
| C005 | ❌ reject | mixed·weak·borderline·medium·mixed | ls_t=0.10 noise + mono OOS 50% collapse + Q5 reversal + vol_20d exposure 15.71 (本批最高) | body vs range mixing signed/magnitude info, range 与 vol_20d 频谱完全共振, residual sign flip | [[batches/batch_102/candidates/C005]] |
| C006 | ⏸ reserve | aligned·**strong**·acceptable·medium-high·stable | ic_oos=-0.027 ls_t=-3.69 alpha_surv=1.27 max_corr=-0.694@F003 **incr_ic=-0.006** | CP03 全 strong + 9 年 sign-consistent, 但 F003 (overnight gap) 已 capture 该 alpha — TsRank-diff 是 ordinal rotation 非新空间 | [[batches/batch_102/candidates/C006]] |

**档位编码**: 🟢 优档 · 🟡 次档 · 🟠 边际 · 🔴 阻断档 · `hard_gate` reject 该列不填色

## 跨候选对比

- **2 个 hard_gate sign_flip (C001/C002)**: train_ic ≈ 0 / val_ic 强非零, 不是 noise 而是 **A 股 9 年 cross-period structural drift** (C002 ic_by_year 2015 -0.038 → 2023 +0.020 单调漂); 不是机制设计错误, 是 **跨字段 TsRank-diff 在 a 股长 sample 上 sign-instability** 的方向级 finding. **P033 律 (OOS sign-flip 警示)** 在此触发: train≤2021 / val≥2022 的 split 把"机制翻转点" 包在 train period 内 — 不可挽救.

- **Style absorption pattern**: 6 候选 dominant_style 全部 `vol_20d`. exposure 量级 (低→高): C006 (6.30) < C001 (8.90) < C003 (7.98) < C002 (11.64) < C004 (12.26) < C005 (15.71). **C006 vol_20d 最低 + style_r² 0.042 最 clean** 说明 intraday/overnight return-leg TsRank-diff 比 raw price/volume/amount TsRank-diff 更 ⊥ vol_20d basis — 这是本批主要的 risk-cleanness 发现.

- **incr_ic 分布**:
  - C001: 0.013 (positive but hard_gate fail)
  - C002: -0.012 (negative)
  - C003: 0.004 (边缘 low/medium)
  - C004: 0.023 (high but P030 artifact)
  - C005: 0.024 (high but raw IC noise)
  - C006: **-0.006 (negative — 决定性)**
  → incr_ic 正负与 mechanism alignment 弱相关; **NEGATIVE incr_ic 在 admittable candidates 上是 reject 决定信号** (C006 case).

- **MT 预算推进**: direction_candidates 0 → 6; cumulative 570 → 576. bucket medium (search_adjusted 0.22-0.59 跨度大). 本批 search_adjusted bucket low=2 / medium=4, **C006 search_adjusted=0.587 是 medium 上界** — 提醒 multiple testing 风险在 admit 边界候选上仍生效.

- **错杀件检测 (4-piece)**:
  - C003: 4/4 满足 (max_corr 0.26 < 0.30 ✓; mono_oos |1.0| ≥ 0.80 ✓; sign_consist 1.0 ✓; F028 corr sign 与本候选 IC 异号 ✓) → **potential over-rejection flag**
  - C006: 部分满足 (mono ✓ sign ✓; max_corr 0.69 > 0.30 ✗; incr_ic 负 不构成"库空间独立") → 不进 over-rejection 类
  → batch_summary 含 ≥ 1 错杀 flag (C003), **触发 calibration_trigger 加强** (zero_admit_streak 累计已达 4).

## Thread 进展

> [!failure]+ T001 [[directions/tsrank_diff_form#T001]] 🆕 — `[✗ DISPROVEN batch_102]`
> **流量场跨字段 TsRank-diff 同窗**: 3 candidates (C001 amount-num_trades, C002 num_trades-turnover, C003 amount-turnover). **2/3 hard_gate sign_flip** (C001/C002 — a 股 9 年 structural drift), **1/3 borderline reserve** (C003 mono -1.0 + 库独立 但 ls_t-1.67 不达 admit). 流量场跨字段 raw atom 路径 **大部分被 sign-instability 摧毁**, 仅 size-coupled vs scale-free pair (C003) 存活. T001 主体 disproven for $amount/$num_trades & $num_trades/$turnover pairs; $amount/$turnover (C003) 仍 active 等待复活路径.

> [!failure]+ T002 [[directions/tsrank_diff_form#T002]] 🆕 — `[✗ DISPROVEN batch_102]`
> **几何字段 TsRank-diff**: 2 candidates (C004 close-volume, C005 body-range). 双 reject. C004 classical PV-divergence + C005 body/range diff 都 **mono OOS collapse + ls_t noise + dom_style=vol_20d 严重共振**. 几何字段 TsRank-diff 不构成 cross-section spread — TsRank ordinal-normalize 过 close/volume/body/range 后, 信息密度过低. T002 完全 disproven.

> [!warning]+ T003 [[directions/tsrank_diff_form#T003]] 🆕 — `[◉ ACTIVE]`
> **intraday vs overnight TsRank-diff**: 1 candidate (C006). CP03 strong 3/3 + 9 年 robust + style_r² 最 clean — **真实 alpha 存在**, 但 **incr_ic=-0.006 negative + max_corr -0.694 with F003** = **alpha 与 F003 (overnight_gap_normalized) 同源**. T003 hypothesis 部分成立但 admit blocked by 库已含信号. reserve 等待 F003 residualize 或 retire 触发复活.

## 方向级反思

**tsrank_diff_form direction 一批后核心 finding**:

1. **跨字段 TsRank-diff 不构成新几何空间** — 6 候选 max_corr 分布:
   - C001 0.69@F024 (negative, RHS num_trades 同源)
   - C002 0.67@F024 (positive, RHS turnover 同源)
   - C003 0.26@F028 (低)
   - C004 0.32@F024 (medium-low)
   - C005 0.45@F026 (medium)
   - C006 0.69@F003 (negative, sign-flip mirror)
   - **3/6 max_corr ≥ 0.45**, 与库内 anchor 字段 / overnight family 同源高. b096 实证 TsRank-diff vs CsRank-diff (F018) max_corr 0.14-0.19 几何独立的结论 **仅适用 CsRank-diff cluster, 不适用 raw price/volume/overnight family**.

2. **P032 律扩展候选**: 原 P032 (Rank-Diff 第 8 cross-domain) 约束 CsRank-diff `cross-domain combinations are dead`. 本批揭示 **TsRank-diff cross-field 也 mostly dead 但机制不同**: CsRank-diff 是 cross-section domain 同构 ⇒ admitted F015-F023 已 capture; TsRank-diff 是 time-series ordinal rotation 形式 ⇒ 倾向坍缩到 raw price/volume/overnight 已 admit 信号. **建议 P032 律扩展**: `Sub(TsRank(X,N),TsRank(Y,N)) 在 X/Y 来自 same family (e.g. both microstructure flow, both return component) 时 cross-section corr ≥ 0.45 与 library nearest, incr_ic 倾向 negative — 整族 reject default`.

3. **本方向 status: probing → saturated (immediate)**: rounds=1, admits=0. 唯一 path forward 是 (a) C003/C006 Python OLS residualize 复活路径; (b) calibration 流程对 reserve pool 重评估. 不再下新批同形式候选.

4. **calibration_trigger 加强**:
   - zero_admit_streak: 3 (b099+b100+b101) → 4 (含 b102)
   - 错杀件 C003 4/4 全中 (max_corr<0.30 库独立 + mono_oos perfect + sign_consist=1.0 + F028 IC 异号)
   - 累计 reserve 池 + 本批 C003+C006 = 9 候选 待 calibration 复活
   - **强烈建议 orchestrator dispatch /consolidate-calibration** 处理 reserve 池

5. **下批建议**:
   - 不再走 TsRank-diff cross-field same-window (本批已耗尽 hypothesis space)
   - 切换至全新 unrelated direction (orchestrator 选)
   - 或 dispatch calibration retro triage 对 reserve pool 整体重评

**MT Budget 推进**: cumulative 570 → 576 (+6); direction_candidates 0 → 6 — 本方向 6 candidates 一次性 saturate. medium bucket 内.
