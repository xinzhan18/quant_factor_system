---
batch_id: batch_071
direction: python_ttm_residual_quality
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

# batch_071 Judge Summary

> [!abstract]+ batch_071 · [[directions/python_ttm_residual_quality]] · 6 candidates · **首批 Python R8 escape hatch 应用**
> ❌ **reject=6** · 0 admit / 0 reserve · 全部 hard_gate sign_flip
> **核心发现**: lessons.md L1 "逃离正路径 b" — Python OLS residualize TTM quality on Barra basis — **完全证伪**。6/6 候选 hard_gate `sign_flip` (train +α 0.001~0.014 / validation -α -0.001~-0.009 全部翻号)；同时 6/6 alpha_survival ≥ 0.93（全部 PASS 0.40 红线）但 5/6 dominant_style 仍是 `vol_20d`（C005 是 `ep_ratio`），style_crowding `medium`/`high`。**机制**: OLS linear residualization of (size, vol_20d, [book_to_price]) Barra basis 在 csi1000 daily cross-section 上**充分** strip Barra 已知 style basis（alpha_surv 高），但残差 IC 在 2022-2023 全部 regime 翻号 — TTM quality 在 csi1000 cross-section 上**真存在 alpha basis 但被 2022-2023 regime drift 杀死**，不是 vol_20d 吸收问题。
> **MT Budget**: cumulative 384 → 390 · direction 0 → 6 · bucket `high`（raw=0.797 + 全 high）

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | hard_gate | train_ic=+0.0142 val_ic=-0.0086 sign_flip; alpha_surv=0.93; vol_20d_exp=22.9 dom; max_corr=0.34@F002 | ROE 残差最强 IS IC 但 OOS 大翻号；alpha_survival 良好但残差仍载 vol_20d_exp=22.9 | [[batches/batch_071/candidates/C001]] |
| C002 | ❌ reject | hard_gate | train_ic=+0.0113 val_ic=-0.0031 sign_flip; alpha_surv=2.40; vol_20d_exp=17.3 dom; max_corr=0.18@F018 | ROIC 3-basis 残差 alpha_surv=2.40 极佳但 OOS 翻号；3-basis 控制比 2-basis 更紧但救不了 regime drift | [[batches/batch_071/candidates/C002]] |
| C003 | ❌ reject | hard_gate | train_ic=+0.0012 val_ic=-0.0033 sign_flip; alpha_surv=1.20; vol_20d_exp=11.6 dom; max_corr=0.15@F002 | gross_margin IS IC=+0.0012 接近零，cross-section 几乎无 alpha；OOS 翻号印证 dead | [[batches/batch_071/candidates/C003]] |
| C004 | ❌ reject | hard_gate | train_ic=+0.0100 val_ic=-0.0050 sign_flip; alpha_surv=1.49; vol_20d_exp=18.6 dom; max_corr=0.24@F018 | ROA 3-basis 残差 sign_consistency=1.0 IS 内全同号但 OOS 翻号——纯 unleveraged quality 也未逃 regime drift | [[batches/batch_071/candidates/C004]] |
| C005 | ❌ reject | hard_gate | train_ic=+0.0086 val_ic=-0.0029 sign_flip; alpha_surv=1.95; ep_ratio_exp=11.2 dom; max_corr=0.10 | growth 残差 dominant_style=ep_ratio（唯一非 vol_20d）— winsorize+narrow basis 让 ep_ratio 暴露替代了 vol_20d；但 OOS 仍翻号 | [[batches/batch_071/candidates/C005]] |
| C006 | ❌ reject | hard_gate | train_ic=+0.0070 val_ic=-0.0007 sign_flip; alpha_surv=7.23; vol_20d_exp=14.4 dom; max_corr=0.15 | inverse debt-to-asset solvency 残差 alpha_surv=7.23 整批最高；val_ic=-0.0007 接近零（最弱翻号）；solvency 维度独立 quality 仍 OOS dead | [[batches/batch_071/candidates/C006]] |

**档位编码**：🟢 最优档（aligned/strong/good/low/stable）· 🟡 次档（mixed/borderline/acceptable/medium）· 🔴 阻断档（misaligned/weak/poor/high/unstable）· `hard_gate` reject 该列写 `hard_gate` 不填色。

## 跨候选对比

- **核心信号同构**：6/6 候选 hard_gate fail 的精确原因都是 `sign_flip`（train +α / validation -α），**没有一个候选 OOS IC 与 IS IC 同号**。这是迄今为止 csi1000 daily 上 fundamental TTM quality 类信号最一致的负结果。
- **alpha_survival 全部 ≥ 0.93**（C001=0.93, C002=2.40, C003=1.20, C004=1.49, C005=1.95, C006=7.23）— 证明 Python OLS residualize **机械上确实剔除了 Barra 已知 style 的线性 component**；但**这与"TTM quality 在 csi1000 携带 stable cross-section alpha"是两回事**。
- **dominant_style 仍 vol_20d 5/6**：C001=22.9, C002=17.3, C003=11.6, C004=18.6, C006=14.4；C005 唯一切换到 ep_ratio=11.2（growth 字段 winsorize 后被 ep_ratio 吸收）。Linear OLS 不能 strip 非线性 vol_20d basis loading。
- **IC by year (C001 揭示 regime drift)**: 2015 +0.0256 / 2016 +0.0241 / 2017 +0.0178 / 2018 +0.0143 / 2019 +0.0017 / 2020 +0.0150 / 2021 +0.0029 / **2022 -0.0034 / 2023 -0.0138** — 完美的"2022-2023 regime reversal"模板。其他 5 候选同型衰减。
- **库内冗余度**: max_corr 全部 < 0.34（C001 0.34@F002 最高，其余 < 0.24）— 残差 quality 信号与现有库内 51 admit 因子结构上独立，**这是 "如果 OOS 同号本可 admit" 的硬证据**——但 OOS 全 dead，所以独立性是 noise 独立性，不是 alpha 独立性。
- **MT 预算推进**：cumulative 384 → 390（+6 high bucket）；direction 0 → 6 (首批)；本批全部 sign_flip hard_gate 进 high bucket（raw 0.797 + 全负）。
- **错杀侦测**：6 候选**无一**满足"潜在错杀"4 条件（max_lib_corr<0.30 ✓ for 5/6, alpha_surv>0.40 ✓ for 6/6, 但 sign_flip hard_gate fail 三立 → 不是错杀边缘 — 是真翻号）→ 无 over-rejection flag，无 calibration trigger。

## Thread 进展

> [!failure]+ T001 [[directions/python_ttm_residual_quality#T001]] — `[✗ DISPROVEN batch_071]`
> **首批假设彻底证伪**: Python OLS residualize TTM quality on (size, vol_20d, [book_to_price]) → CsRank 路径 6/6 候选全部 OOS sign_flip。
> **二阶发现**:
> 1. **alpha_survival 与 OOS-stable 解耦** — alpha_survival 衡量"残差对 Barra style 线性独立"，但 csi1000 上 TTM quality 残差有"2022-2023 regime drift"独立失活机制，alpha_surv 高不预测 OOS sign 同号。
> 2. **TTM quality 在 csi1000 上的 cross-section alpha 是 regime-dependent**: 2015-2021 弱正（IS IC ≈ +0.01～+0.014），2022-2023 翻号（OOS IC ≈ -0.003～-0.014）。这与全市场 TTM quality alpha "2022-2023 价值回归 regime" 现象同构。
> 3. **Linear residualize 不破 vol_20d 非线性吸收**: 5/6 残差 dominant_style 仍 vol_20d_exp 11~22 — OLS 只 strip 线性 βvol_20d component，残差仍载 vol_20d 二阶/非线性载荷。
> 4. **OLS residualize 工艺本身可用但需选不同 numerator**: 同款 Python pinv+einsum 架构在 [[directions/barra_residual_alpha]] F004/F005 上是 admit 的；本批失败是 **TTM quality numerator 在 csi1000 daily 上无 alpha basis**，不是 residualize 工艺失败。

## 方向级反思

本方向为首批 (round 71) **完全证伪假设**：

1. **direction 状态判定**: rounds=1, admit=0, reserve=0, reject=6. admit/judged=0%。
2. **核心 mechanism dead**: 假设 "TTM quality 失败的核心机制是 daily-aggregate liquidity (Mean(amount/turnover)) 把 numerator 拉进 vol_20d basis；Python residualize 从源头剔除可救" — **完全证伪**。残差携带的 cross-section signal 在 2022-2023 全部翻号，TTM quality 类 alpha 在 csi1000 daily 上根本不存在 OOS-stable basis（不是 vol_20d 吸收问题）。
3. **逃离路径再无可探**：lessons.md L1 提供的 3 条"逃离正路径"中 (b) Python residualize 已证伪，(a) "numerator ∈ {pe/pb/ps/dividend_yield 已 Barra value basis}" 已在 [[directions/pit_valuation_pure]] b069/b070 探完且 saturated，(c) "TTM × TTM 内部交互" 等同于 b068 C001 类已 reject。
4. **首次 Python escape hatch 应用 negative result**: 工艺本身正确执行（6/6 compute success, alpha_surv 全过红线），失败原因纯粹是 csi1000 daily TTM quality 无 OOS alpha — 这对系统层面是有价值的 dead zone 证明。

**饱和判定（针对 status saturated 转换）**：
- 首批 admit=0 + 6/6 sign_flip + 关键 mechanism (residualize) 已 disproven ✓
- → 建议 status: `probing → dead`（不是 saturated — saturated 是"探完但留 reserve 火种"，本方向无 reserve 也无残余可探路径，是 mechanism dead zone）

**下一步建议（给 orchestrator）**：
1. **direction-level decision**: 建议 [[directions/python_ttm_residual_quality]] 转 `dead` 并升 lessons.md：(a) "csi1000 daily TTM quality OLS-residualized signal 在 2022-2023 regime 全翻号 — 不是 vol_20d 吸收，是 alpha 不存在"；(b) "alpha_survival metric 与 OOS sign-stability 解耦 — alpha_surv 高不蕴含 OOS alive"。
2. **Python escape hatch 工艺验证 OK**：架构（pinv+einsum vectorized OLS + parquet cache）跑通 6 候选无 error，**未来可复用**到其它 mechanism。
3. **下批方向建议**: 远离 fundamental TTM quality 路径，重新探 OHLC microstructure / intraday signals（lessons.md "Promising Unexplored" 区有候选）；或直接进 Phase 5 consolidation（`zero_admit_streak` 已 12，三方向 dead — quality_carry / pit_valuation / python_ttm_residual_quality），让 LLM 重写 lessons + INDEX。
4. **lessons.md 升格候选**:
   - "Linear OLS residualize 不破 csi1000 vol_20d 非线性吸收 — 5/6 残差 dominant_style 仍 vol_20d_exp 11~22"
   - "csi1000 daily TTM quality 类 alpha 2015-2021 → 2022-2023 全 regime sign-flip — quality 类信号在 A 股小盘 2022 后死区"
   - "alpha_survival 与 OOS sign-stability 解耦 — 不可单独依赖 alpha_surv 作 admission gate"

**consolidation_trigger**: false（rounds_since_last_consolidation = 3，未到 10；但 zero_admit_streak=12 + 三方向连续 dead 已是强信号，建议 orchestrator 启动）
**calibration_trigger**: false（无 over-rejection flag，6 候选全因 sign_flip hard_gate 三立翻号；非边缘错杀）
