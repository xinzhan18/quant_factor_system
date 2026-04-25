---
batch_id: batch_051
direction: gap_acceptance_structure
judged_at: 2026-04-25T06:30:00Z
candidates:
  - {candidate_id: C001, verdict: reserve}
  - {candidate_id: C002, verdict: admit, factor_name: gap_vol_body_ratio_rank_diff_20}
  - {candidate_id: C003, verdict: reject}
  - {candidate_id: C004, verdict: reject}
  - {candidate_id: C005, verdict: reject}
  - {candidate_id: C006, verdict: reject}
batch_summary: {total: 6, admit: 1, reserve: 1, reject: 4}
admit_count: 1
reserve_count: 1
reject_count: 4
candidate_count: 6
mt_bucket: high
---

# batch_051 Judge Summary

> [!abstract]+ batch_051 · [[directions/gap_acceptance_structure]] · 6 candidates
> ✅ **admit=1** (C002→F{next} `gap_vol_body_ratio_rank_diff_20`) · ⏸ **reserve=1** (C001 max_corr=0.55@F018 cluster + alpha_surv=0.31 边界) · ❌ **reject=4** (C003 hard_gate ic_oos_too_low; C004 alpha_surv=0.005 + incr=0.002; C005 max_corr=0.696@F017; C006 hard_gate sign_flip)
> **核心发现**：**rank-diff 范式第 6 次跨家族泛化 — gap_acceptance_structure 兑现**。C002 (Std(gap_ret,20) × body_ratio_20) 是首次让 rank-diff 几何在 gap 家族独立兑现：max_corr=0.246@F016 整库唯一 <0.30，与 5 个 admitted rank-diff (F015-F019) 全 |corr|<0.25，且与同字段 F010/F011 corr 仅 -0.076/-0.073 — **验证 b050 T012 "Mean vs Std of same atomic 不冗余" 律在第二个家族复现**。**6 跨 5 family tipping point 已超 b050 标记的 5-family，Phase 5 consolidation 升格 lessons.md "rank-diff geometry" 通用规则的硬证据完整**。
> **MT Budget**: cumulative 264 → **270** · direction 12 → **18** · bucket `high` (search_adjusted → medium) · 本批 low=0 / med=0 / high=6

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ⏸ reserve | 🟢·🟡·🔴·🟡·🟢 | ic_oos=+0.049 ls_t=3.75 mono=1.0/1.0 alpha_surv=0.31 max_corr=0.55@F018 incr=0.008 | rank-order 真实 + 9 年同号 + decay=2.09 健康；但 rank-diff cluster co-resonance + incr_ic 边际 + alpha_surv borderline 三 borderline 叠加；C002 admit 优先 | [[batches/batch_051/candidates/C001]] |
| C002 | ✅ **admit** | 🟢·🟢·🟡·🟢·🟢 | **ic_oos=-0.040 ls_t=-9.68(IS) mono=-1.0/-1.0 alpha_surv=0.404 max_corr=0.246@F016 incr=-0.013 9/9yr-** | rank-diff geometry 第 6 次 cross-family + 第 1 次 in gap 家族 + Std(gap_ret) higher-moment 兑现 + 整批 library-clean | [[batches/batch_051/candidates/C002]] · [[factors/F020]] |
| C003 | ❌ reject | hard_gate | ic_oos≈0.0006 (raw \|gap\| 60d 双 dilution) | 无 normalization + 60d 长窗超 signal_half_life 双重稀释 | [[batches/batch_051/candidates/C003]] |
| C004 | ❌ reject | 🟡·🟡·🔴·🟡·🟡 | ic_oos=+0.026 ls_t=1.17 alpha_surv=**0.005** max_corr=0.48@F019 incr=0.002 | cross-ratio LHS 完全被 Barra book-to-price + vol_20d 吸收 (alpha_surv 整批最低) + F019 已捕获 92% | [[batches/batch_051/candidates/C004]] |
| C005 | ❌ reject | 🟢·🟢·🔴·🔴·🟢 | ic_oos=+0.049 ls_t=3.76 mono=1.0/1.0 alpha_surv=0.20 max_corr=**0.696@F017** incr=0.003 | RHS 短窗 price_vol 与 F017/F010/F011 cluster 共振 (4 因子 0.43-0.70) + incr_ic 不足 | [[batches/batch_051/candidates/C005]] |
| C006 | ❌ reject | hard_gate | sign_flip train=-0.008 → val=+0.014 | C002 同 atomic 长窗 60d 包含多 regime cycle 导致符号失稳 (Std 算子比 Mean 更窗口敏感) | [[batches/batch_051/candidates/C006]] |

**档位编码**：🟢 最优档 · 🟡 次档 · 🟠 边际 · 🔴 阻断档 · `hard_gate` reject 不填色。

## 跨候选对比

**LHS 多元化结构 (本批 6 LHS 全唯一)**:
- C001: `Mean(gap/(H-L), 20)` — gap acceptance ratio (range-norm)
- C002: `Std(gap_ret, 20)` — **higher moment of F010/F011 atomic** (admit)
- C003: `Mean(|gap|, 60)` — raw |gap| 长窗 (reject hard_gate)
- C004: `Mean(|gap|/|body|, 20)` — cross-session magnitude ratio
- C005: `Mean(gap/(H-L), 5)` — C001 短窗对照
- C006: `Std(gap_ret, 60)` — C002 长窗对照 (reject hard_gate)

**关键 admit 路径分析**: 6 LHS 中只有 C002 在三个维度上同时脱 cluster：(1) **higher moment** (Std vs F010/F011 Mean，验证 b050 T012 律在 gap 家族复现)；(2) **RHS basis 类目** body_ratio (非 amount/turnover/overnight/price_vol 共振 RHS)；(3) **窗口适中 20d** 在 signal_half_life 内。三个维度叠加 → max_corr=0.246 整库最 library-clean。

**reject 模式分类**:
- **hard_gate dilution reject (C003, C006)**：长窗 60d 超 signal_half_life 19d 导致 (a) raw magnitude 被磨损 (C003 ic≈0) / (b) Std 算子在多 regime 窗口失稳 (C006 sign_flip)。**T002 b036 教训第 N 次复现**
- **Barra absorption reject (C004)**：cross-ratio LHS 折叠两个 OHLC magnitude → alpha_survival=0.005 (本批最低)。**rank-diff geometry 不能挽救 LHS 已被 style basis 吸收的因子**
- **rank-diff cluster co-resonance reject (C005)**：max_corr=0.696@F017 + 4 因子 cluster 0.43-0.70。**短窗 price_vol RHS + 短窗 gap LHS 与 F017 (overnight×turnover_5) + F010/F011 (overnight Mean) 必然 cluster — RHS 共振饱和律在 gap 家族首次复现**
- **rank-diff cluster co-resonance reserve (C001)**：max_corr=0.553@F018 + incr_ic=0.008 边际。比 C005 cluster 程度浅 (0.55 vs 0.70)，但仍未脱 — reserve 等待 (a) 与 C002 库独立后再测 / (b) 换 RHS 维度

**与 b050 admit (F019 body_disp×price_vol) 对照**: 
- F019: LHS=Std(body_ratio,20) higher moment OHLC × RHS=price_vol → max_corr=0.270 cluster-clean
- C002: LHS=Std(gap_ret,20) higher moment gap × RHS=body_ratio → max_corr=0.246 cluster-clean
- **跨方向同律**: higher-moment LHS (Std vs Mean) 是 rank-diff geometry 脱 cluster 的关键，b050 在 OHLC 家族验证、本批在 gap 家族复现 — **"higher-moment LHS independence axis" 律横跨 family 兑现**

**与 b049 (F018 overnight_sign × amount_20) RHS 共振对照**:
- b049/b050 已标"RHS 共振饱和律"endpoints: overnight_5 / turnover_5 / amount_20
- 本批 C002 RHS=body_ratio_20 (新 RHS 类目首次 admit) — **扩展 RHS 安全 basis 到 body_ratio_20** (non-resonant 类目)
- C005 RHS=price_vol_20 cluster 共振 reject — **新 dead RHS 类目: short-window price_vol_20** 加入 RHS 共振饱和律 endpoints

**Style 聚合**: 6 候选 dominant_style 全 vol_20d。C002 crowding=medium (整批唯一非 high)，其余 high。**gap 家族 rank-diff 天然 vol_20d 暴露** — direction structural constraint。C002 vol_20d=21.96 < C001 30.5 < C005 38.88 (随窗口收紧 vol 暴露上升).

**MT 预算**: direction_candidates 12 → 18, 远低于 70 上限. 本方向 saturated → productive 重启 (C002 admit + C001 reserve 两个非 reject + 6 跨家族 tipping point 确认).

## Thread 进展

> [!success]+ T005 [[directions/gap_acceptance_structure#T005]] 🆕 — `[✓ ANSWERED batch_051]`
> rank-diff 范式第 6 次跨家族泛化首次在 gap 家族兑现——C002 LHS=Std(gap_ret,20) higher-moment gap atomic + RHS=body_ratio_20 新 basis 类目。max_corr=0.246@F016 整库唯一 <0.30 + incr_ic=-0.013 健康. **6 跨 5 family tipping point 已超 b050 标记的 5-family** (microstructure×2 + overnight×2 + OHLC×1 + gap×1)，**Phase 5 consolidation 升格 lessons.md "rank-diff geometry" 通用规则的硬证据完整**.
>
> 同步揭示三个新教训:
> 1. **higher-moment LHS independence axis 横跨 family 兑现**: Std vs Mean 的 corr structure 完全不同律在 OHLC (F019) 和 gap (C002) 家族独立成立
> 2. **新 RHS 安全类目 body_ratio_20**: 扩展 RHS 共振饱和律白名单 — body_ratio (OHLC structural) 非 vol-class basis 可脱 cluster
> 3. **新 dead RHS 类目 price_vol_20**: 短窗 price-vol RHS (Mean(Std($close,5),20)) 与 F017/F010/F011 短窗 overnight cluster 共振 — 加入 RHS 共振饱和律 endpoints

> [!failure]+ T006 [[directions/gap_acceptance_structure#T006]] 🆕 — `[✗ DISPROVEN batch_051]`
> raw |gap| 长窗 60d (C003) + Std(gap_ret) 60d (C006) 双 hard_gate fail. **T002 b036 教训第 N 次复现**: gap 家族信号在 csi1000 上必须 (a) scale-free normalization (raw |gap| 被股价水平 dominate → ic≈0) (b) 窗口 ≤20d (60d 包含 2-3 regime cycle → Std 算子失稳更甚 Mean)。**Std 算子比 Mean 算子对窗口长度更敏感**.

> [!info]+ T007 [[directions/gap_acceptance_structure#T007]] 🆕 — `[◉ ACTIVE]`
> cross-ratio LHS (C004 |gap|/|body|) **不能挽救 Barra 完全吸收**: alpha_surv=0.005 极端 collapse — 两个 OHLC magnitude 折叠后投影完全在 Barra book-to-price + vol_20d 子空间. rank-diff geometry 不替代 Barra orthogonality. **新失败模式**: ratio of two raw magnitudes (cross-session 或 within-session) 在 rank-diff 几何中是 style projection 的 rank rotation, 非新 alpha. 下批可探: ratio of two **rank-transformed** magnitudes 是否同病; 或 ratio + sign 复合是否破解.

## CP04 Reflection · `over-rejection check`

C001 alpha_surv=0.31 (在 0.30 acceptable 与 0.40 default 之间) + perfect mono=1.0/1.0 + 9/9 yr+ + decay=2.09 健康 — **接近 calibration §Step 1 错杀诊断 4 标志** (max_corr=0.55 > 0.30 + incremental_ic=0.008 < 0.010 两项不达，故 reserve 而非 admit). 本批不触发 retroactive admit — C001 与 C002 在 LHS 同 atomic 但 moment 不同, 后续可在 C002 admit 后重测 C001 controlled (C001 LHS 是 Mean atomic, F{next}=C002 是 Std atomic, 控制 F{next} 后 C001 incr 是否 >0.010 决定).

无系统级 over-rejection 信号. 本批 admit=1 + reserve=1 + 4 reject 全有明确多 dealbreaker / hard_gate 依据.
