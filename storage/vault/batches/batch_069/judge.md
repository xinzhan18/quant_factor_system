---
batch_id: batch_069
direction: pit_valuation_pure
judged_at: 2026-05-02T02:30:00Z
candidates:
  - {candidate_id: C001, verdict: reject}
  - {candidate_id: C002, verdict: reject}
  - {candidate_id: C003, verdict: reject}
  - {candidate_id: C004, verdict: reject}
  - {candidate_id: C005, verdict: reject}
  - {candidate_id: C006, verdict: reserve}
batch_summary: {total: 6, admit: 0, reserve: 1, reject: 5}
admit_count: 0
reject_count: 5
reserve_count: 1
candidate_count: 6
mt_bucket: medium
---

# batch_069 Judge Summary

> [!abstract]+ batch_069 · [[directions/pit_valuation_pure]] · 6 candidates (NEW direction, library_gap/008 提议)
> ✅ **admit=0** · ⏸ **reserve=1** · ❌ **reject=5**
> **核心发现**: T001-T003 三 thread NEW direction 假设**部分证伪 + 部分有救** —— PIT/TTM valuation level 单 atom 形式确实在 csi1000 daily-bar 上**仍被 vol_20d 吸收**（4/4 PASS-hg 候选 dominant_style=vol_20d），但 C006 `Mul(CsRank(div_yld), CsRank(1/PB))` rank × rank composite 出现**首次显著 value Barra basis 抗衡** (book_to_price=2.21 + ep_ratio=3.96, style_r²=0.578) + 强 ic_oos=0.039 + ls_t=2.17 + max_corr=0.33@F021 几何独立 — 但 alpha_survival=0.19 仍三立标记不达 default 0.40 threshold → **reserve 而非 admit**. C003/C005 (peg_ratio_ttm + pcf_ratio_total_ttm) 均 hard_gate sign_flip 失败 (TTM aggregate 字段 regime drift). 关键证据: 单字段 PIT valuation rank **远不足以**抗衡 vol_20d basis (C001 div_yld 单 rank vol_20d_exp=11.2 vs ep_ratio=5.34, vol_20d 仍主导), **必须双 valuation rank composite** 才显化 value basis (C006 ep_ratio=3.96 + b/p=2.21 双立).
> **MT Budget**: cumulative 372 → 378 · direction 0 → 6 · bucket `medium` (新方向 direction 项=0 拉低)

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | aligned·borderline·**poor**·low(F017)·**unstable** | ic_oos=+0.023 ls_t=+0.74 mono=+0.7 alpha_surv=0.31 sty_r²=0.22 vol_20d_exp=**11.2** ep_ratio=5.34 max_corr=0.23@F017 incr=+0.0051 | CsRank($dividend_yield_ttm) 单 atom rank — ic_oos 满足 floor + max_corr=0.23 几何独立 + alpha_surv=0.31 borderline, 但 ls_t=0.74 (远低 2.0 floor) + ic_is=0.014 弱 + style 主导仍是 vol_20d (虽 11.2 比 b068 fundamental quality 23-31 低很多). 反映 **PIT dividend yield 单 rank 不足以激活 value Barra basis**, ep_ratio=5.34 系数虽存在但被 vol_20d=11.2 压制. **机理**: 单字段 cross-section rank dispersion 不够强, value basis 信号弱于 vol noise. | [[batches/batch_069/candidates/C001]] |
| C002 | ❌ reject | aligned·borderline·**poor**·low(F002)·**unstable** | ic_oos=+0.021 ls_t=+0.88 mono=+0.6 alpha_surv=0.27 sty_r²=0.17 vol_20d_exp=5.63 b/p=1.03 max_corr=0.20@F002 incr=+0.0040 | Div(1, $pcf_ratio) cash-flow yield level — ic 健康 + max_corr=0.20 (与 F002 PB level 几何独立 ✓) + vol_20d_exp=5.63 是本批最低 (style_r²=0.17 全批最低 ✓), 但 alpha_surv=0.27 仍三立 + ls_t=0.88 不足 + incr_ic=0.004 不达 0.005 floor. **反映 1/pcf level 是本批唯一未被 vol_20d 显著拉拽的候选**, 但 cross-section 信号强度不足以达到 admit 门槛. **救援路径**: cash-flow yield × 双 valuation rank composite (类 C006 套路) 可能放大. | [[batches/batch_069/candidates/C002]] |
| C003 | ❌ reject | hard_gate | sign_flip: train +0.0035 vs val -0.0025 | Div(1, $peg_ratio_ttm) 1/PEG = (growth × earnings_yield) integrated form — train ic 正向 / val ic 负向 sign 翻号. peg_ratio_ttm 包含 growth_ttm，**与 b068 C004 GARP `Mul(growth, 1/PE)` 同样的 regime drift**: 2015-2021 成长占优 → 2022-2023 价值回归. peg 作为单 ratio 看似规避 P003 cross-product 但 numerator 仍含 growth 数值 → regime 切换暴露同样脆弱. **第 2 次 fundamental signed signal regime drift 跨 form (b068 cross-product → b069 single-ratio integrated form)** | [[batches/batch_069/candidates/C003]] |
| C004 | ❌ reject | aligned·borderline·**poor**·low(F017)·**unstable** | ic_oos=+0.025 ls_t=+1.52 mono=+0.7 alpha_surv=0.21 sty_r²=0.23 vol_20d_exp=9.62 b/p=0.98 max_corr=0.25@F017 incr=+0.0059 | Sub(CsRank($dividend_yield_ttm), CsRank($pe_ratio)) rank-diff 双 valuation — ic 健康 + max_corr=0.25 几何独立 + ic_oos>ic_is decay 健康, 但 alpha_surv=0.21 三立 + ls_t=1.52<2 + dominant_style=vol_20d (vol_20d=9.62 > b/p=0.98 + ep_ratio=4.45). 反映 **rank-diff Sub 形式没有有效激活 value basis** — 虽然两端都是 valuation atoms, 但 Sub 后值的 dispersion 来自 (div_yld - pe) 排序差异, 不是 Mul 乘积放大双方共有的 value basis. **C006 vs C004 对比是 batch 关键发现**: rank × rank vs rank-diff 在 value basis 激活上完全不对称 (Mul 放大共有 basis, Sub 抵消共有 basis). | [[batches/batch_069/candidates/C004]] |
| C005 | ❌ reject | hard_gate | sign_flip: train +0.0030 vs val -0.0019 | Div(1, $pcf_ratio_total_ttm) total cash-flow yield TTM — train ic 正向 / val ic 负向 sign 翻号 + magnitude 弱. pcf_total_ttm 是 TTM aggregate 字段 (含全部 cash flow), 与 PIT pcf_ratio (C002) 不同 base form, 但同样在 2015-2021 → 2022-2023 regime 切换暴露. **C005 sign_flip + C002 PASS-hg 对比**: PIT daily 字段 (C002 1/pcf_ratio) 比 TTM aggregate (C005 1/pcf_total_ttm) regime 稳定性更强 — TTM aggregate 字段含报告期累积, regime drift 风险更高. | [[batches/batch_069/candidates/C005]] |
| C006 | ⏸ **reserve** | aligned·strong·**poor**·medium(F021)·stable | ic_oos=**+0.039** ls_t=+2.17 mono=+0.9 alpha_surv=**0.19** sty_r²=**0.578** vol_20d_exp=8.42 **b/p=2.21 ep_ratio=3.96** max_corr=0.33@F021 incr=+0.0067 ls_sharpe=1.56 ls_calmar=1.16 | Mul(CsRank($dividend_yield_ttm), CsRank(Div(1, $pb_ratio))) rank × rank composite — **本批最强**且唯一非 hg_fail 候选呈 **strong CP3 quality**: ic_oos=0.039 + icir_oos=0.30 + mono=0.9 + ls_t=2.17 + ls_sharpe=1.56 + max_corr=0.33 几何独立 + incr_ic=+0.0067 真实 library 增量. **关键 finding**: style_r²=**0.578** (本批最高), 双 value basis (book_to_price=2.21 + ep_ratio=3.96) 共同活化 — **首次在 cross-section daily-bar 上观察到 value basis 与 vol_20d 同量级共存** (vol_20d=8.42 vs combined value=6.17). 但 **alpha_survival=0.19** 三立 + dominant_style=vol_20d 仍 hold, barra_residual_ic=0.0074 (仅原 ic 的 19%) → **reserve 而非 admit**: 信号几何独立 ✓ + ls_t 强 ✓ + 真实 incr_ic ✓, 但 Barra strip 后 alpha 衰减剧烈，不达 admit 阈值 default 0.40. **救援判定**: 与 b066/b067 reserve 候选不同, C006 是首次 PIT valuation rank composite 在 csi1000 cross-section 显化 value Barra basis — 价值在于"如果未来 vol_20d 拉拽机理被诊断/校准 (calibration)"或"在 risk model 之外有独立 alpha 价值（满足 ls_t/sharpe 强 + incr_ic 正）". 标记 **reserve = 火种**, 非 admit 决议. | [[batches/batch_069/candidates/C006]] |

**档位编码**：🟢 最优档（aligned/strong/good/low/stable）· 🟡 次档（mixed/borderline/acceptable/medium）· 🟠 边际 · 🔴 阻断档（misaligned/weak/poor/high/unstable）· `hard_gate` reject 该列写 `hard_gate` 不填色.

## 跨候选对比

**Style 聚合 (4 PASS-hg 候选)**：dominant_style 全部 `vol_20d`, 但 vol_20d 系数与 b068 fundamental_quality_carry 比**显著降低**:
- C006 Mul(CsRank(div_yld), CsRank(1/PB)): vol_20d=8.42, **b/p=2.21 + ep_ratio=3.96** (本批 value basis 显化最强 ✓)
- C001 CsRank($dividend_yield_ttm): vol_20d=11.19, ep_ratio=5.34 (单 atom value basis 弱)
- C004 Sub(CsRank(div_yld), CsRank(pe)): vol_20d=9.62, b/p=0.98 + ep_ratio=4.45 (rank-diff 抵消 basis)
- C002 Div(1, $pcf_ratio): vol_20d=5.63 (本批最低), b/p=1.03 + ep_ratio=2.91 — 但 cross-section 信号强度不足

对比 b068 (fundamental_quality_carry)：vol_20d_exp 5.63-11.19 vs 8.5-31.1, **本批降低 50-70%** ✓ — 验证假设的部分: PIT/TTM valuation 字段不通过 daily-aggregate liquidity denominator 后 vol_20d 拉拽显著弱化. 但**未达**"完全脱 vol_20d basis"的强假设 — 4/4 PASS-hg 候选 dominant_style 仍是 vol_20d.

**P004 vol_20d structural absorption 第 11+ direction 跨族复现 (首在 PIT valuation 字段族)**: 不再纯靠 daily-aggregate liquidity denominator 路径, **csi1000 cross-section 在 daily-bar 频率上 vol_20d 系数本身就远高于其他 Barra style**, 是 universe-frequency 级别的 risk model 现实. **逃离正路径**仅限 (a) 内嵌 size×book/market 双重 anchor (e.g. F002 PB level)，(b) 高 ls_t + 高 ls_sharpe + 几何独立的"alpha 在 risk-model 外"型 reserve (本批 C006).

**P003 fundamental signed signal regime drift 跨 form 复现 (b068 → b069)**: C003 (1/peg) + C005 (1/pcf_total) 均 sign_flip hard_gate fail. 无论 cross-product (b068 C004) 还是 single-ratio integrated form (本批 C003), 只要 numerator 含 growth/TTM aggregate (含报告期累积) → 2015-2021 → 2022-2023 regime 切换暴露. **PIT 单字段 (C001 dividend_yield, C002 1/pcf) 反而 regime 稳定** ✓, 验证 "PIT > TTM aggregate" 在 fundamental signal regime 稳定性上的偏序.

**P006 library-reducer trap**: 本批 incremental_ic 实际比 b068 改善 (C001 +0.0051 / C002 +0.0040 / C004 +0.0059 / **C006 +0.0067**) — C006 首次在 fundamental 方向触及 floor 0.005. **未撞 P006**.

**核心发现 (rank × rank vs rank-diff 不对称)**: C006 rank × rank composite (style_r²=0.578) 与 C004 rank-diff (style_r²=0.23) 在 value basis 激活上**完全不对称** — Mul 放大双方共有的 value basis 信号 (互相加强), Sub 抵消共有 basis (互相抵消, 留下噪声). 这是本批最值得升格的元教训. (待 Phase 5 consolidation 决议)

**MT 预算推进**: cumulative 372→378; direction 0→6; bucket `medium` (新方向 direction 项=0 强力拉低 family 项).

## Thread 进展

> [!warning]+ T001 [[directions/pit_valuation_pure#T001]] — `[~ PARTIALLY DISPROVEN batch_069]`
> **Question**: 单 PIT valuation atom cross-section rank 是否携带独立 alpha + vol_20d_exp <15%?
>
> **Answer**: **vol_20d_exp 部分达标 (11-12 vs 假设<15)**, 但 **alpha 强度不足以构成 admit**. C001 (CsRank div_yld) ic_oos=+0.023 ls_t=0.74 alpha_surv=0.31, 远低 admit 标准. C002 (1/pcf level) ic_oos=+0.021 alpha_surv=0.27 + 全批最低 vol_20d_exp=5.63 (优于假设), 但 incr_ic 不达 floor + ls_t=0.88. **机理**: 单 PIT valuation 字段 cross-section rank 信号强度被 vol_20d 噪声压制, value Barra basis 系数 (b/p=0.6-1.0, ep_ratio=2.9-5.3) 存在但不足以反超 vol_20d (8-11).
>
> **Evidence trail**:
> - [[batches/batch_069/candidates/C001|batch_069 C001]] CsRank($dividend_yield_ttm) → ic=+0.023 vol_20d_exp=11.2 ep_ratio=5.34 alpha_surv=0.31 → reject (ls_t 弱)
> - [[batches/batch_069/candidates/C002|batch_069 C002]] Div(1,$pcf_ratio) → ic=+0.021 vol_20d_exp=5.63 alpha_surv=0.27 → reject (ls_t 弱 + incr_ic 不达 floor)
>
> **复活路径**: (a) 双 PIT valuation rank composite (本批 C006 已部分验证, 见 T002); (b) PIT valuation × PIT short-window momentum interaction (避开 daily liquidity); (c) 等 vol_20d 拉拽诊断/校准.

> [!warning]+ T002 [[directions/pit_valuation_pure#T002]] — `[⏸ PARTIALLY VALIDATED batch_069 — reserve 火种]`
> **Question**: 复合 valuation rank (rank-diff 或 rank × rank) 是否优于单 atom 且 max_lib_corr<0.5?
>
> **Answer**: **rank × rank composite 部分验证 (C006 reserve)**, rank-diff Sub 形式证伪 (C004 reject). **关键不对称**: C006 (Mul rank×rank): style_r²=0.578 + b/p=2.21 + ep_ratio=3.96 双 value basis 显化 + ic_oos=0.039 + ls_t=2.17 + max_corr=0.33 (<0.5 ✓); C004 (Sub rank-diff): style_r²=0.23, b/p=0.98 单弱, ic_oos=0.025 ls_t=1.52. **机理**: Mul 放大双方共有的 value basis 共线信号, Sub 抵消共有 basis 留下噪声.
>
> **Evidence trail**:
> - [[batches/batch_069/candidates/C006|batch_069 C006]] Mul(CsRank(div_yld), CsRank(1/PB)) → ic=+0.039 ls_t=+2.17 mono=+0.9 sty_r²=0.578 alpha_surv=0.19 max_corr=0.33@F021 incr=+0.0067 → **reserve** (Barra strip 后 alpha 衰减但 ls_t 强 + 几何独立)
> - [[batches/batch_069/candidates/C004|batch_069 C004]] Sub(CsRank(div_yld), CsRank(pe)) → ic=+0.025 ls_t=1.52 sty_r²=0.23 alpha_surv=0.21 → reject
>
> **进一步探索**: (a) Mul(CsRank($dividend_yield_ttm), CsRank(Div(1, $pe_ratio))) 替换 RHS PB → PE (B/P 与 E/P value basis 不同细分); (b) Mul(CsRank($dividend_yield_ttm), CsRank(Div(1, $pcf_ratio))) — div_yld × cash-flow yield (避开 PB common anchor); (c) 调研 C006 reserve 火种保留路径.

> [!failure]+ T003 [[directions/pit_valuation_pure#T003]] — `[✗ DISPROVEN batch_069]` (TTM aggregate sign_flip)
> **Question**: TTM aggregate valuation (pcf_total / peg) 是否独立于 PIT 形式?
>
> **Answer**: **TTM aggregate 形式证伪 (regime drift)**. C003 (1/peg_ratio_ttm) + C005 (1/pcf_total_ttm) 均 sign_flip hard_gate fail. 含 growth/TTM 累积量的 valuation 在 2015-2021 → 2022-2023 regime 切换暴露脆弱. **PIT 形式 (C001/C002) regime 稳定 ≠ TTM aggregate 形式 regime 稳定**, 字段层面的 stationarity 不等价.
>
> **Evidence trail**:
> - [[batches/batch_069/candidates/C003|batch_069 C003]] 1/peg_ratio_ttm → train +0.0035 vs val -0.0025 sign_flip → reject
> - [[batches/batch_069/candidates/C005|batch_069 C005]] 1/pcf_total_ttm → train +0.0030 vs val -0.0019 sign_flip → reject
>
> **复活路径**: 不复活 TTM aggregate 直接 1/X 形式; 改用 (a) PIT 字段优先 (pcf_ratio daily PIT 已 C002 PASS-hg); (b) Python: TTM aggregate cross-section z-score 后再用; (c) 跨字段 TTM × TTM 内部 (避开 daily 路径) — 但需 Python 包装规避 P007 数据契约.

## 方向级反思

**核心律 (本方向 partial-validate)**: 6 候选覆盖 3 子机制:
- T001 单 PIT valuation rank → vol_20d_exp 部分降低 (11-12 vs 假设<15) 但 alpha 强度不足
- T002 复合 valuation rank → **rank × rank Mul 形式 (C006) 首次在 PIT valuation 显化 value basis** ✓ (reserve 火种), rank-diff Sub 证伪
- T003 TTM aggregate valuation → 完全证伪 (sign_flip regime drift, 与 b068 C004 同律)

**与 cockpit 假设的对比** (cockpit 推荐"PIT valuation 自带 Barra value basis 抗衡 vol_20d"):
- ✅ vol_20d_exp 显著降低 (本批 5.63-11.2 vs b068 fundamental_quality 8.5-31.1) — 验证 daily-aggregate liquidity denominator 是隐藏 vol_20d 路径的判断
- ✅ value Barra basis 在 C006 rank × rank composite 形式下**首次显化**到 b/p=2.21 + ep_ratio=3.96 同时活
- ❌ 但 **csi1000 daily-bar vol_20d 系数本身就远高于其他 Barra style**, 单 PIT valuation 字段 rank dispersion 不足以反超 — `dominant_style=vol_20d` 仍 hold
- 升级 cockpit 提示: "PIT valuation 字段 Barra value basis 在 cross-section 上**需 rank × rank composite 形式**才显化, 单 atom 不行"

**升格 lessons 候选** (本方向贡献 3 条, 待 Phase 5 consolidate 决议):
1. **rank × rank composite vs rank-diff 在 Barra basis 激活上不对称**: Mul(CsRank(value_atom_A), CsRank(value_atom_B)) 放大共有 basis (style_r²=0.578), Sub(CsRank(A), CsRank(B)) 抵消共有 basis (style_r²=0.23). 应升格至 lessons.md `Composition Selection`: "复合多 atom 同 basis 字段时 Mul 优于 Sub" (C006 vs C004 实证).
2. **TTM aggregate (peg/pcf_total/含 growth 累积) signed signal regime drift**: 与 cross-product (b068 C004 GARP) 不同 form 但同一 mechanism. 应作为 lessons.md `Path Selection` 现有"Signed fundamental signal regime drift"条目的补充实证: TTM aggregate 单 ratio 也算 signed fundamental, 不仅 cross-product.
3. **PIT 字段 (daily 价值字段) regime 稳定性 > TTM aggregate (累积字段)**: C001/C002 PASS-hg + C003/C005 sign_flip 实证. 字段层面的"PIT vs TTM aggregate"是 fundamental signal regime 稳定性偏序的关键.

**zero_admit_streak**: b068=8 → b069=9 (连续 9 批 zero admit) → 系统接近 calibration 触发条件 (本 skill `阈值校准 trigger #2` 阈值=连续零 admit). **C006 reserve 火种是潜在 calibration discussion candidate** — 但 max_corr=0.33 (>0.30) + alpha_survival=0.19 (低于 default 0.40) **不属错杀** (max_corr 不达 calibration 复活条件 <0.30 ✓ + incr_ic 0.0067 略超 0.005 floor 但未达"显著强独立"信号).

**rounds_since_consolidation**: 0 (刚 consolidate) — 距 10 阈值还远, **consolidation_trigger=false**.

**错杀侦测** (calibration trigger #1 检查):
- C006 max_corr=0.33 (>0.30) + alpha_survival=0.19 + incr_ic=0.0067 → 不属"max_lib_corr<0.30 + incremental_ic>0.010"双立 → **不属错杀**
- C004 max_corr=0.25 (<0.30 ✓) + incr_ic=0.0059 (<0.010) → 不属错杀
- C001 max_corr=0.23 (<0.30 ✓) + incr_ic=0.0051 (<0.010) → 不属错杀
- C002 max_corr=0.20 (<0.30 ✓) + incr_ic=0.0040 (<0.005 floor) → 不属错杀
- 无候选满足"错杀 flag"完整条件. 本批 alpha 真实在 vol_20d 拉拽 + ls_t 不足下 alpha 强度不足, **不属错杀**.

**Calibration trigger 评估**:
- Trigger #1 (judge.md "potential over-rejection"): 不存在 — C006 reserve 决议明确反映 alpha_survival 真实不足 default 0.40, 非过严
- Trigger #2 (连续零 admit 警戒): zero_admit_streak=9 + 累计最近 3 批 (b067/b068/b069) admit=0+0+0 = 0 ✓; 但 reserve 候选 (b066 / b069 C006) 未达"max_lib_corr<0.30 + incremental_ic>0.010"双立 → trigger #2 第二条件**不立** (没有真实被错杀 reserve 火种, C006 max_corr=0.33 + incr=0.0067 接近但不双立)
- Trigger #3 (Reserve 积压): 累计 reserve/judged 比例 (近 10 批 reserve=2 / total≈60 = 3.3%) — **远低于 40%** → 不立
- Trigger #4 (悖论复现): 不立
- **结论**: calibration_trigger = false. 当前是 alpha 真实在 csi1000 daily-bar vol_20d 拉拽下不足, 不是阈值过严. C006 reserve 是合理"火种"决议 (满足 ls_t/incr_ic 但 alpha_surv 不达 default 0.40).

**direction status 提议**:
- 现状: probing(medium) · 0 round before · 0 admits
- 本批 5 reject + 1 reserve (C006), 3 thread 中 T001 partial-disproven / T002 partial-validated (reserve 火种) / T003 disproven
- 信号设计层证据: 3 子机制覆盖, T002 救活 (C006 reserve 是首次 PIT valuation rank composite 显化 value basis)
- NEW direction first-batch dead 律不适用 (有 reserve 火种, 不算 born-near-disproven)
- **status 提议: probing → probing (维持)** + 推进 T002 子探索 (C006 改 RHS PB→PE / cash-flow yield 比对)
- priority: medium (维持) — value basis 显化但 alpha_surv 仍弱

**MT Budget 状态**: cumulative 372→378 · direction 0→6 · bucket `medium`

**下轮建议** (orchestrator 级):
1. **本方向 probing 维持**: T002 救活, 下批续探 C006 family — Mul(CsRank($dividend_yield_ttm), CsRank(1/PE)) 替换 RHS PB→PE; Mul(CsRank($dividend_yield_ttm), CsRank(1/$pcf_ratio)) 跨字段 yield composite. 目标: ≥1 admit 验证 rank × rank composite 是否能脱"alpha_surv<0.40"魔咒.
2. **calibration 极临近 trigger #2**: zero_admit_streak=9, 1 批后达 10 警戒. 但 trigger #2 双立条件 (max_lib_corr<0.30 + incremental_ic>0.010) 仍未满足, **不实质触发**. 建议 orchestrator 关注 b070 是否产出真"火种 reserve" (双立).
3. **下批方向选择**: 若 orchestrator 决定继续 pit_valuation_pure, 续 T002. 若切换, 优先 productive direction (overnight_intraday_split / ohlc_temporal_aggregation) 平衡 zero_admit_streak.
4. **新发现升格点**: rank × rank composite vs rank-diff 在 Barra basis 激活上的不对称 (C006 vs C004) 是 lessons.md 升格价值最高的本批发现; PIT vs TTM aggregate regime 稳定性偏序是第二条.
