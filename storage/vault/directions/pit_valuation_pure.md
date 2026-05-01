---
direction_tag: pit_valuation_pure
status: probing
priority: medium
rounds: 2
admits: 0
last_batch: batch_069
last_admits: []
last_goal: 首批 6 候选探索 PIT/TTM valuation level cross-section（dividend_yield/pcf/peg/pcf_total）—
  不通过 daily-aggregate liquidity denominator（避开 b068 vol_20d 吸收路径），自带 Barra value basis
  抗衡 vol_20d。目标 ≥1 admit 验证 valuation level frontier 独立 alpha。
last_activity: '2026-05-01T18:29:09Z'
created_batch: batch_069
members: []
retired_members: []
reserves:
- batch_069_C006
merged_into: null
created_from: library_gap/008
---
# pit_valuation_pure

> [!abstract]+ 方向概要
> - **状态**　🟡 `probing` (round 69，library_gap/008 finding 提议) · priority `medium` · rounds = 0 · admits = 0
> - **一句话**　PIT/TTM valuation level（dividend_yield, pcf, peg, pcf_total）单独或两两 rank 复合，**不嵌入 daily-aggregate liquidity denominator**，自带 Barra value basis 抗衡 vol_20d 吸收。
> - **来源**　[[_consolidation/findings/library_gap/008]] — 51 admit 因子 valuation 端覆盖只有 F002（PB/amount）一例，dividend_yield/pcf/peg 完全无使用，是 fundamental_quality_carry dead 后的最简 productive frontier 候选。

---

## Hypothesis

**经济学逻辑**：

1. **dividend yield carry** — 高股息率股票在 csi1000 cross-section 上对应 cash-distributing mature firms，与 PE/PB 几何独立（dividend 决策 ≠ earnings/book ratio）；高 yield 股票在 A 股有独立 carry signal（防御属性 + 国资偏好分红）。

2. **cash-flow yield (1/pcf)** — 现金流不易操纵，比 earnings yield (1/PE) 更难被会计调节扭曲，期望在 csi1000 daily 上携带稳定 cross-section signal。pcf 与 pe 的 pearson 通常 >0.5 但 cross-section rank gap 携带"应计盈余质量"信息。

3. **PEG yield (1/peg)** — peg = pe/growth，1/peg = (growth × earnings yield)，整合 valuation × growth 的级别比 GARP cross-product (Mul(growth, 1/PE)) 更符合 P003 atom-orthogonality（peg 是单 ratio，不是 cross-product，regime drift 风险更低）。

4. **rank-diff valuation pair (dividend_yield rank − pe rank)** — 避开乘积量纲撞 + DSL Sub 在两端都是 daily PIT 字段时数据契约 OK（PIT 字段非 sparse TTM）。表达"高股息低 PE"组合（双重 value 信号）。

5. **TTM total cash-flow yield (1/pcf_total_ttm)** — pcf_total_ttm 包含全部 cash flow（OCF + ICF + FCF），覆盖更全的现金流 picture，与 PIT pcf_ratio 不同字段（一个 daily PIT 一个 TTM aggregate）。

**与 Barra basis 抗衡 vol_20d 的论证**：

- F002 admit 的关键不是 `Div by Mean(amount,20)`，而是 numerator `$pb_ratio` 自带 Barra value basis（cross-section 长期与 book/market 共线）。同理 `$dividend_yield_ttm` / `$pe_ratio` / `$pcf_ratio` 都属 Barra value style basis 字段，cross-section rank 自带 value exposure → 不被 vol_20d 单一吸收。
- **预期 pre-check**：style_r²（value%）应占主导，vol_20d_exp 应 < 15%（远低于 b068 fundamental_quality_carry 的 23-31%）。

**与 OHLCV 几何独立**：valuation 字段族不依赖任何 daily price/volume aggregate，与 F001-F023 admitted（全 OHLCV / microstructure / overnight）几何完全正交。库内 valuation 端只 F002 一例，几何空间稀疏。

**与 fundamental_quality_carry 的差异**：
- fundamental_quality_carry numerator = TTM quality (ROE/ROA/margin/growth)，**无 Barra basis 抗衡**
- pit_valuation_pure numerator = PIT/TTM valuation (dividend_yield/pcf/peg)，**自带 Barra value basis**
- 不通过 `Mean($amount/turnover, N)` 隐藏路径吸收

---

## Threads

### T001: 单 PIT valuation atom cross-section rank 是否携带独立 alpha [◉ ACTIVE]

> [!warning]+ Thread 结论
> **Question**: 单 atom `$dividend_yield_ttm` / `Div(1, $pcf_ratio)` cross-section level 是否携带 forward IC，且 vol_20d_exp 显著低于 fundamental_quality_carry 的 23-31%？
>
> **Answer**: vol_20d_exp **部分达标** (11.2/5.6 vs 假设<15) ✓ 但 alpha 强度不足. C001 (CsRank div_yld) ic_oos=+0.023 ls_t=0.74 alpha_surv=0.31, C002 (1/pcf level) ic_oos=+0.021 ls_t=0.88 alpha_surv=0.27 — vol_20d 拉拽显著弱化但单 atom value Barra basis (b/p=0.6-1.0) 不足以反超 vol_20d (5.6-11.2).
>
> **Evidence trail**:
> - [[batches/batch_069/candidates/C001|batch_069 C001]] CsRank($dividend_yield_ttm) → ic=+0.023 vol_20d_exp=11.2 ep_ratio=5.34 → reject (ls_t 弱)
> - [[batches/batch_069/candidates/C002|batch_069 C002]] Div(1,$pcf_ratio) → ic=+0.021 vol_20d_exp=5.63 (本批最低) → reject (ls_t 弱 + incr 不达 floor)
>
> **复活路径**: 转 T002 复合 rank 形式 (C006 已部分 reserve 验证).

### T002: 复合 valuation rank 是否优于单 atom [◉ ACTIVE]

> [!info]+ Thread 结论
> **Question**: 复合 valuation rank (rank-diff or rank × rank) 是否优于单 atom + max_lib_corr<0.5?
>
> **Answer**: **rank × rank Mul 形式部分验证 (C006 reserve 火种)**, rank-diff Sub 形式证伪 (C004 reject). C006 `Mul(CsRank(div_yld), CsRank(1/PB))`: ic_oos=0.039 + ls_t=2.17 + style_r²=**0.578** + b/p=2.21 + ep_ratio=3.96 双 value basis 共同活化 ✓ + max_corr=0.33@F021 几何独立 ✓ + incr_ic=+0.0067 真实增量 ✓, 但 alpha_survival=**0.19** 三立不达 admit default 0.40 → reserve. **关键不对称**: Mul 放大共有 basis (sty_r²=0.578), Sub 抵消共有 basis (sty_r²=0.23).
>
> **Evidence trail**:
> - [[batches/batch_069/candidates/C006|batch_069 C006]] Mul(CsRank(div_yld), CsRank(1/PB)) → ic=+0.039 ls_t=+2.17 mono=+0.9 sty_r²=0.578 alpha_surv=0.19 max_corr=0.33@F021 incr=+0.0067 → **reserve** (Barra strip 后 alpha 衰减)
> - [[batches/batch_069/candidates/C004|batch_069 C004]] Sub(CsRank(div_yld), CsRank(pe)) → ic=+0.025 ls_t=1.52 sty_r²=0.23 alpha_surv=0.21 → reject
>
> **进一步探索 (下批)**: (a) Mul(CsRank($dividend_yield_ttm), CsRank(1/PE)) RHS PB→PE 比对; (b) Mul(CsRank($dividend_yield_ttm), CsRank(1/$pcf_ratio)) yield × yield 复合; (c) 调研 alpha_survival 校准路径以保留 C006 火种.

### T003: TTM aggregate valuation (pcf_total / peg) 是否独立于 PIT 形式 [✗ DISPROVEN batch_069]

> [!failure]+ Thread 结论
> **Question**: TTM aggregate valuation (pcf_total / peg) 是否独立于 PIT 形式提供信号?
>
> **Answer**: **完全证伪 (TTM aggregate sign_flip regime drift)**. C003 (1/peg_ratio_ttm) + C005 (1/pcf_total_ttm) 均 sign_flip hard_gate fail. 含 growth/累积量的 TTM aggregate valuation 在 2015-2021 → 2022-2023 regime 切换暴露脆弱 (与 b068 C004 GARP cross-product 同律, signed fundamental cross form). PIT 字段 (C001/C002) regime 稳定 vs TTM aggregate (C003/C005) regime drift, 字段层面 stationarity 不等价.
>
> **Evidence trail**:
> - [[batches/batch_069/candidates/C003|batch_069 C003]] 1/peg_ratio_ttm → train +0.0035 vs val -0.0025 sign_flip → reject (hard_gate)
> - [[batches/batch_069/candidates/C005|batch_069 C005]] 1/pcf_total_ttm → train +0.0030 vs val -0.0019 sign_flip → reject (hard_gate)
>
> **复活路径**: 不复活 TTM aggregate 直接 1/X 形式; 改用 PIT 字段优先 (C002 已 PASS-hg) 或 Python 包装 cross-section z-score.

---

## Known Failures

| Batch | Candidate | Expression | Reject reason |
|---|---|---|---|
| [[batches/batch_069/candidates/C001\|batch_069 C001]] | C001 | `CsRank($dividend_yield_ttm)` | ls_t=0.74<2 floor + ic_is=0.014 弱 + alpha_surv=0.31 borderline + dominant_style=vol_20d 仍主导 (单 atom value basis 弱不能反超 vol_20d_exp=11.2) |
| [[batches/batch_069/candidates/C002\|batch_069 C002]] | C002 | `Div(1, $pcf_ratio)` | ls_t=0.88<2 floor + alpha_surv=0.27 三立 + incr_ic=0.0040<0.005 floor (虽 vol_20d_exp=5.63 + style_r²=0.17 本批最低 验证 PIT 路径假设 ✓ 但 cross-section 信号强度不足) |
| [[batches/batch_069/candidates/C003\|batch_069 C003]] | C003 | `Div(1, $peg_ratio_ttm)` | hard_gate sign_flip (train +0.0035 vs val -0.0025); TTM aggregate 含 growth 字段 regime drift, 与 b068 C004 GARP 同律 |
| [[batches/batch_069/candidates/C004\|batch_069 C004]] | C004 | `Sub(CsRank(div_yld), CsRank(pe))` | alpha_surv=0.21 三立 + ls_t=1.52<2 floor + dominant_style=vol_20d (rank-diff Sub 抵消共有 value basis, sty_r²=0.23 弱 vs C006 Mul sty_r²=0.578 强) |
| [[batches/batch_069/candidates/C005\|batch_069 C005]] | C005 | `Div(1, $pcf_ratio_total_ttm)` | hard_gate sign_flip (train +0.0030 vs val -0.0019); TTM aggregate 含报告期累积量 regime drift, 与 C003 同 mechanism |

## Narrative Log

- **2026-05-02 round 69 创建** — fundamental_quality_carry dead 后 library_gap/008 提议；本批 6 候选探索 PIT/TTM valuation level form，绕开 daily liquidity denominator vol_20d 吸收陷阱。
- **2026-05-02 batch_069 first-batch 结果**: 6 候选 → admit=0 / reserve=1 (C006) / reject=5。**核心发现**: PIT/TTM valuation 单 atom rank 形式 vol_20d_exp 显著降低 (5.6-11.2 vs b068 fundamental_quality 8.5-31.1，**降 50-70%** ✓) 部分验证假设；但 dominant_style 仍是 vol_20d，单 atom value basis 不足以反超。**首次发现**: C006 `Mul(CsRank(div_yld), CsRank(1/PB))` rank × rank composite **首次在 PIT valuation 字段族显化 value Barra basis** (book_to_price=2.21 + ep_ratio=3.96, style_r²=0.578)，但 alpha_survival=0.19 仍不达 admit default 0.40 → **reserve 火种**。**关键不对称**: rank × rank Mul 放大共有 basis (C006 sty_r²=0.578) vs rank-diff Sub 抵消共有 basis (C004 sty_r²=0.23) — 这是本批最值得升格的元发现。T003 TTM aggregate (peg/pcf_total) 形式 sign_flip regime drift 完全证伪 (与 b068 GARP 同律, signed fundamental cross form)。Direction **probing 维持**，下批续 T002 子探索（C006 family RHS 替换）。
