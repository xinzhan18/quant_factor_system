---
direction_tag: tsrank_candlestick_ratio
status: saturated
priority: medium
rounds: 4
admits: 2
last_batch: batch_077
last_admits: []
last_goal: "Round 77 续探 (b073 admit F024 + b076 admit F025 hot streak). 假设:\n方向 admits=2\
  \ 后, frontier 真度律已实证 — 高阶 OHLC composition (b076 P019/P020 升格) 比\nsingle-atom 更彻底破\
  \ cross-section 几何同源 (F025 max_corr 0.29 vs C001/C005 0.45-0.47).\n本批沿 b076 next_hint\
  \ 三条路径续探 frontier 上限:\n  (1) 三层 OHLC composition 嵌套 — shadow_asymmetry × body_ratio\
  \ (C001 nested Div + C005 Mul form,\n      测 frontier 多层化是否仍守 max_corr<0.30 line)\n\
  \  (2) Std/CsRank 双量纲化 — TsRank(Std(range/close,20),60) + Mul(CsRank,CsRank) 跨域\
  \ cross-product\n  (3) 替换分母法 — range/midprice (C006) vs F021 H/L; range/(C+O) (C003)\
  \ double-arm normalization\n\n6 candidates 矩阵:\n  C001 三层 nested Div: TsRank(shadow_asym\
  \ / (body_ratio + 1e-9), 60) — frontier 上限测试\n  C002 range vol TsRank: TsRank(Std((H-L)/C,\
  \ 20), 60) — 双量纲化 (vol-of-vol-proxy)\n  C003 double-arm normalization: TsRank((H-L)/(C+O),\
  \ 60) — 替换分母 (vs C004 b076 H-L/C reject)\n  C004 cross-product Mul: Mul(CsRank(num_trades/volume),\
  \ CsRank(shadow_asym)) — F024 atom × F025 atom\n  C005 Mul composition: TsRank(body_ratio\
  \ * shadow_asym, 60) — Mul 替代 Div 的高阶 composition\n  C006 range/midprice TsRank:\
  \ TsRank((H-L)/midprice, 60) — midprice 替换分母\n\n红线 (P011/P014):\n  - max_corr <\
  \ 0.30 to library (incl F024+F025+F007+F008)\n  - alpha_survival >= 0.40 + ic_by_year\
  \ sign-stable + incr_ic POS\n  - |corr $market_cap| < 0.3\n  - +1e-9 epsilon 防 div-by-zero\
  \ (P018)\n\nAnti-recap (don't retread b068-b076):\n  - C001 close_position TsRank\
  \ (b076 reserve, max_corr 0.47@F008) — 本批 NOT retried (P019 复活路径需 Python residualize)\n\
  \  - C002 raw upper_shadow ratio (b076 reject) — NOT retried\n  - C003 raw body_ratio\
  \ TsRank (b076 hard_gate) — 本批 C005 是 body × shadow 复合形式 (composition 破 mean-reversion)\n\
  \  - C004 range/close TsRank (b076 reject sty_r²=0.13) — 本批 C002 加 Std 双量纲化, C003\
  \ 改分母 (C+O), C006 改分母 (midprice)\n  - C005 midprice/close TsRank (b076 reserve,\
  \ max_corr 0.45@F008) — NOT retried\n  - C006 shadow_asymmetry TsRank (b076 admit\
  \ F025) — NOT retried; 本批用作 atom 合成\n\n目标 ≥1 admit 验证 frontier 真度上限 (高阶 composition\
  \ / Std×TsRank / CsRank-Mul 三路径).\n失败模式: 全 reject → frontier 几何已饱和, b078 切换 direction\
  \ (e.g. python_ttm_residual_quality 复活 fundamental 路径)."
last_activity: '2026-05-01T22:47:24Z'
created_batch: batch_076
members:
- F025
retired_members: []
reserves:
- C001_b076
- C005_b076
merged_into: null
created_from: cockpit_round_76_b073_F024_frontier_extension_to_OHLC_shape
status_changed_at: '2026-05-02T06:30:00Z'
status_change_reason: b077 0 admit / 6 reject — frontier 上限饱和铁证 + hypothesis_promoter/013
  升格 absorbing 律. F025 已 cement 为 cross-section absorbing prototype, 同 family 续探无新维度.
---
# tsrank_candlestick_ratio

> [!abstract]+ 方向概要
> - **状态**　🔴 `saturated` (b077 frontier 上限饱和铁证 + finding/013/016/019 absorbing 律升格) · priority `medium` (admits=2 已落库) · rounds = 4 · admits = 2 (F024 b073 cross-link + F025 b076)
> - **一句话**　把 b073 admit F024 (TsRank-60-on-count_ratio) 验证的 frontier 几何, 扩展到 OHLC dimensionless candlestick shape ratio. b076 admit F025 shadow_asymmetry (高阶 composition 真红利铁证); b077 续探 (三层 nested / Std×TsRank / cross-product Mul / 分母替换) **全 reject** — F025 几何成 absorbing factor, 同 family 续探不再有新维度.
> - **来源**　cockpit_round_76 frontier extension; F024 admit (b073) + tsrank_timeseries_ratio direction saturated → 同 frontier 机制在 OHLC 几何域未被探索.
> - **饱和铁证 (锁方向)**　b077 max_corr 0.58-0.70@F025 (三层 / Mul / cross-product 三路径), sty_r² 0.13@vol_20d (range/normalized-price family vol proxy 不可解), in-batch dup C003/C006. b078+ 切换 cross-family direction; 同 family 续探唯一生还路径 = Python residualize on F025 (DSL 表达不出, 走 storage/python_factors/).

---

## Hypothesis

⚠️ **status=saturated**: 核心机制 (TsRank-60 + 高阶 composition 破 cross-section 几何同源) 已在 F025 落地; b077 实证 admit 后续探不再有新维度. 任何 DSL 内同 family 续探 default-skip — 唯一生还路径 = Python residualize on F025 / 跨 family rhs_change (microstructure → fundamental basis).

**核心机制 (b073 F024 + b076 F025 实证)**:

1. **TsRank 60d 时序量纲化**: 把 cross-section level 替换为"个股自身 60d 分位", 绕过 cross-section vol_20d basis 上的 ranking 重叠. F024 实测 vol_20d_exp = 10.6, F025 vol_20d_exp = 6.03 (更低), style_r² 分别 0.051 / 0.029.
2. **dimensionless ratio 是必要前提**: 分子分母同量纲在 cross-section 上抵消 scale.
3. **OHLC candlestick shape ratio 自然 dimensionless**: close_position ∈ [0,1], body/upper_shadow/lower_shadow ∈ [0,1], range/close ≈ 0.01-0.05.
4. **高阶 composition 是 frontier 第二阶 (b076 P019 实证, frontier 真红利顶级)**: ratio-of-derived-quantity (例 shadow_asymmetry = upper_shadow / lower_shadow) 比 single-atom ratio 更彻底破 cross-section 共线性 — 分子分母同消 base scale + base volatility (max_corr 0.29 vs single-atom 0.45-0.47).
5. **⚠️ admit 后 absorbing 律 (b077 反向证伪)**: 一旦 family 内有 admit (F025), 同 family 续探在 cross-section 上塌缩到 admit prototype — 三层 nested (Div/Mul) / cross-product CsRank-Mul / Std×TsRank 双量纲化 / 分母替换 max_corr 全部 ≥0.40@F025 (实测 0.58-0.70). risk 维度顶级 (vol_20d_exp 6.4-8.5) 也无法逃 cross-section absorbing — admit 已占 cluster 中心, 续探只是几何变体.

**库内现状对照**:

- F006 upper_shadow_persistence_5d = `Mean(Div(H-C, H-L), 5)` Grade B
- F008 upper_shadow_persistence_3d = `Mean(Div(H-C, H-L), 3)` Grade A
- F021 含 `Mean(H/L, 60)` Grade C
- F011 williams_r_variant cross-section level form
- **F025** shadow_asymmetry_tsrank_60 (b076, 本方向 admit) — 高阶 OHLC composition frontier 真红利铁证, family absorbing prototype

---

## Threads

### T003 — Range / midprice / asymmetry (高阶 composition 路径) `[✓ ANSWERED batch_076]` ⭐ admit F025

**Question**: range/midprice/asymmetry 类 OHLC shape ratio 60d TsRank 是否携带 forward alpha 且与库独立?

**Answer**: **PROVEN — frontier 真红利铁证**. C006 shadow_asymmetry (高阶 composition) admit 全 CP green: ic_oos=+0.019 / ls_t=+6.19 / mono PERFECT POS / alpha_surv=1.15 / style_r²=**0.029 batch min** / vol_20d_exp=**6.03 batch min** (比 F024 实证 10.6 还低 40%) / max_corr=**0.29@F007 UNDER 0.30 line** / incr_ic=+0.014 POS / ic_by_year 8/9 POS sign-stable. **frontier 真生效在 OHLC shape 域首例 + 高阶 composition 路径开辟**. C004 range/close 因 vol proxy 直接载 vol_20d basis 失效 (sty_r²=0.133). C005 midprice/close 信号顶级 (alpha_surv=1.43 batch best) 但与 F008 几何同源 (max_corr=0.45) reserve.

**Evidence trail**:
- [[batches/batch_076/candidates/C006|b076 C006]] TsRank shadow_asymmetry 60 → **admit ⭐ → F025**
- [[batches/batch_076/candidates/C004|b076 C004]] TsRank range/close 60 → reject (vol proxy poor sty_r²)
- [[batches/batch_076/candidates/C005|b076 C005]] TsRank midprice/close 60 → reserve (geometric overlap)

### T001 — Close position & shadow ratio (cross-section 几何同源律) `[✗ DISPROVEN batch_076]`

**Question**: close_position / upper_shadow ratio 60d TsRank 是否与库 F006/F008/F011 几何独立?

**Answer**: **partial DISPROVEN**. cross-section 几何同源律实证 — 单原子 atom 与库 F006/F008 共线性 0.4-0.5 不可解 (TsRank 时序量纲化仅削弱). C001 信号顶级 (ls_t=-6.36, mono PERFECT NEG, alpha_surv=1.18, sign-stable 8/9 NEG) 但 max_corr=0.47@F008 OVER 0.30 阻断 admit (reserve). C002 raw upper_shadow 信号弱 + 库 overlap 双重失败.

**Evidence trail**:
- [[batches/batch_076/candidates/C001|b076 C001]] TsRank close_position 60 → reserve (max_corr=0.47@F008)
- [[batches/batch_076/candidates/C002|b076 C002]] TsRank upper_shadow 60 → reject (weak signal + max_corr=0.38)

**复活路径 (新 paradigm)**: Python residualize on F008 / F025 (走 storage/python_factors/, library_gap/013 已识别为缺口).

### T002 — Body ratio TsRank `[✗ DISPROVEN batch_076]`

**Question**: body_ratio 60d TsRank 是否携带 forward NEG alpha (趋势耗尽假设)?

**Answer**: **DISPROVEN**. C003 hard_gate fail — train→val regime drift sign_flip (train -0.005 / val +0.008) + oos_decay -1.77. body_ratio 是日内动量信号, 60d TsRank time-series form 把动量 mean-reverted, 信号碎片化. 不适合 60d 长窗 (F020 用 Mean 短窗形式更优).

**Evidence trail**: [[batches/batch_076/candidates/C003|b076 C003]] TsRank body_ratio 60 → hard_gate sign_flip.

### T004 — admit-后 frontier 上限测试 `[✗ DISPROVEN batch_077]` (饱和铁证, hypothesis_promoter/013 + pattern_analyst/019 升格 absorbing 律)

**Question**: F025 admit 后, 同 family 续探 (三层 nested composition / 双量纲化 / cross-product Mul / 分母替换) 是否突破 F025 几何 absorbing 阻断?

**Answer**: **DISPROVEN — frontier 上限饱和**. 6/6 reject, 三种 frontier 路径全部塌缩到 F025:
- **三层 nested** (C001 Div / C005 Mul) 仅深化 F025 几何, max_corr 0.58-0.63@F025; risk 顶级 (vol_20d_exp 6.4, sty_r² 0.025-0.027) 但 cross-section ranking 仍 monotone-equiv F025
- **cross-product CsRank-Mul** (C004 = F024_atom × F025_atom) 完全 collapse 到 F025 (max_corr 0.70) — 两 admit 的 Mul 不引入新维度
- **Std×TsRank 双量纲化** (C002) 反向加重 vol basis: vol_20d_exp 42 (4× F024), sty_r² 0.228 (~2× poor line) — Std layer 不削弱反而**放大** vol proxy
- **分母替换** (C003 (C+O) / C006 midprice) sty_r² ∈ [0.132, 0.133] family-level vol proxy 不可解; 且 C003/C006 IC daily corr=0.9996 数学等价 in-batch dup

**Evidence trail**:
- [[batches/batch_077/candidates/C001|b077 C001]] 三层 nested Div → reject (max_corr 0.6272@F025)
- [[batches/batch_077/candidates/C004|b077 C004]] CsRank-Mul cross-product → reject (max_corr 0.6972@F025)
- [[batches/batch_077/candidates/C005|b077 C005]] 三层 nested Mul → reject (max_corr 0.5817@F025 + decay 5.81)
- [[batches/batch_077/candidates/C002|b077 C002]] Std×TsRank 双量纲化 → reject (sty_r² 0.228 + vol_20d_exp 42)
- [[batches/batch_077/candidates/C003|b077 C003]] (H-L)/(C+O) → reject (sty_r² 0.132)
- [[batches/batch_077/candidates/C006|b077 C006]] (H-L)/midprice → reject (C003 数学等价 in-batch dup)

**升格律** (Phase 5 lessons consolidate 接管):
- P019 高阶 composition 路径反向证伪 (Mul/Div form 几何等价, 不构成新维度)
- P021 几何 absorbing factor 律 (admit 后 family 续探 max_corr ≥0.55@admit, 升格 → finding/019)
- P022 double-quantization 反向律 (Std×TsRank 放大 vol proxy)
- P023 CsRank-Mul cross-product 塌缩律 (升格 → finding/017)
- P024 denominator family 等价性自检 (Phase 1 系统级 checklist, 升格 → finding/021)

**唯一生还路径** (library_gap/013 升格): Python residualize on F025 — 把 b077 candidate expr 用 Python wrapper 对 F025 cross-section OLS 残差化, 重测 max_corr / incr_ic. 不是 DSL 内 minor-path (rhs_change 同 family / mean_centering / window_sweep / retro_post_floor 已 b078 全 disproven).

---

## Known Failures

| Candidate | Expression | Reason |
|---|---|---|
| [[batches/batch_076/candidates/C002\|b076 C002]] | `TsRank(Div(Sub($high,$open), Add(Sub($high,$low),1e-9)), 60)` | 信号弱 (ls_t=-0.44, mono OOS=-0.30) + max_corr=0.38@F007 — raw upper_shadow 长窗时序量纲化破坏短期信号 |
| [[batches/batch_076/candidates/C003\|b076 C003]] | `TsRank(Div(Abs(Sub($close,$open)), Add(Sub($high,$low),1e-9)), 60)` | hard_gate fail: sign_flip train -0.005/val +0.008 + oos_decay -1.77 |
| [[batches/batch_076/candidates/C004\|b076 C004]] | `TsRank(Div(Sub($high,$low), Add($close,1e-9)), 60)` | sty_r²=0.133 OVER 0.12 + alpha_surv=0.99 边缘; range/close 是 vol proxy 直接载 vol_20d basis |
| [[batches/batch_077/candidates/C001\|b077 C001]] | `TsRank(Div((H-mid_oc), (mid_oc-L)*body_ratio), 60)` | 三层 nested Div — risk 顶级 (alpha_surv=1.91) 但 max_corr=0.6272@F025 absorbing collapse (P019 反向证伪) |
| [[batches/batch_077/candidates/C002\|b077 C002]] | `TsRank(Std((H-L)/(C+1e-9), 20), 60)` | 双量纲化反向加重 vol: vol_20d_exp=42 (4×), sty_r²=0.228, alpha_surv=0.418 (P022 升格) |
| [[batches/batch_077/candidates/C003\|b077 C003]] | `TsRank(Div(Sub($high,$low), Add($close,$open),1e-9), 60)` | (H-L)/(C+O) 信号强 (ls_t=-3.54, ic_by_year 9/9 NEG) 但 sty_r²=0.132 + alpha_surv=0.99; 同 C006 数学等价 |
| [[batches/batch_077/candidates/C004\|b077 C004]] | `Mul(CsRank($num_trades/$volume), CsRank((H-mid_oc)/(mid_oc-L)))` | CsRank-Mul cross-product 完全 collapse 到 F025 (max_corr=0.6972@F025); P023 升格 |
| [[batches/batch_077/candidates/C005\|b077 C005]] | `TsRank(Mul(body_ratio, shadow_asym), 60)` | Mul-form nested — risk 顶级 (sty_r²=0.025) 但 max_corr=0.5817@F025 + train_val_decay=5.81; Mul/Div 几何等价 (P019 第二反向证伪) |
| [[batches/batch_077/candidates/C006\|b077 C006]] | `TsRank((H-L)/midprice, 60)` | **C003 数学等价 in-batch dup** (IC daily corr=0.9996); P024 升格系统级 |

---

## Narrative Log

### batch_077 (2026-05-02) — frontier 上限饱和铁证, 0 admit / 6 reject (status pivot → saturated)

**Verdicts**: admit=0, reserve=0, reject=6 (三层 nested Div/Mul + Std×TsRank + cross-product CsRank-Mul + 双 form 分母替换).

**核心结论**:

1. **F025 absorbing prototype 律 (P021 升格 → finding/019)**: 同 family 续探的三种 frontier 路径 max_corr 全部 ≥0.58@F025 (三层 nested Div 0.6272, cross-product Mul 0.6972, 三层 nested Mul 0.5817). 这些续探 risk 顶级 (vol_20d_exp 6.4-8.5, sty_r² 0.025-0.115) 但 cross-section 仍由 F025 几何主导 — admit 后该 family 续探无新几何维度.
2. **range/normalized-price family vol proxy 不可解**: 三 form 分母替换 (b076 C004 close / b077 C003 (C+O) / b077 C006 midprice) sty_r² 全部 ∈ [0.132, 0.133] OVER, alpha_surv 全部 0.99-1.0 边缘. 任何分母选择都无法把 sty_r² 压到 acceptable 线.
3. **double-quantization 反向加重 vol basis (P022)**: C002 Std×TsRank vol_20d_exp 42 (单 TsRank ~22), sty_r² 0.228 — Std layer 反向**放大** vol proxy.
4. **CsRank-Mul cross-product 塌缩律 (P023 升格 → finding/017)**: C004 = CsRank(F024 atom) × CsRank(F025 atom) max_corr=0.70@F025, cross-section 塌缩到 dominant prototype. cross-product 续探需 directionally orthogonal atoms (跨 family).
5. **in-batch denominator 等价性 bug (P024 系统级, 升格 → finding/021)**: C003 与 C006 IC daily corr=0.9996 (midprice = (C+O)/2 typical 日数学等价), 浪费 1 计算预算. Phase 1 设计 checklist 加 "denominator pairwise 数学等价性测试".
6. **方向状态判定**: status `active` → **`saturated`** (hypothesis_promoter/013 升格触发), priority high → medium. admits=2 维持 (F025 已落库). b078+ 切换 cross-family direction.
7. **唯一生还续探路径 (library_gap/013)**: Python residualize on F025 — 把 b077 顶级信号候选 (C001 alpha_surv=1.91 / C005 ls_t=+6.39) 用 Python wrapper 对 F025 cross-section OLS 残差化, 重测 max_corr. DSL 内 minor-path (rhs_change 同 family / mean_centering / window_sweep / retro_post_floor) 已 b078 全 disproven (P025-P028).

### batch_076 (2026-05-02) — NEW direction 首批, 1 admit (F025) ⭐ admit pivot

**Verdicts**: admit=1 (C006 → F025 shadow_asymmetry_tsrank_60), reserve=2 (C001 close_position, C005 midprice/close), reject=3 (C002 weak shadow, C003 hard_gate, C004 vol-proxy poor).

**核心结论**:

1. **F025 落地** — TsRank-60 frontier 真生效在 OHLC shape 域首例铁证. 全 CP green: ic_oos=+0.019, ls_t=+6.19, mono PERFECT POS, alpha_surv=1.15, sty_r²=0.029 (batch min), vol_20d_exp=6.03 (batch min, 比 F024 实证 10.6 还低 40%), max_corr=0.29@F007 (under 0.30 line), incr_ic=+0.014 POS, ic_by_year 8/9 POS sign-stable.
2. **方向升格律 — 高阶 composition 破共线性 (P019 升格)**: C006 shadow_asymmetry (ratio of two derived shadow lengths) 比 C001 close_position / C005 midprice/close 更彻底破 cross-section 共线性 — max_corr 0.29 vs 0.45-0.47. 机制: 高阶 composition 在分子分母上抵消 base scale 与 base volatility, single atom 仅时序量纲化无法破解 cross-section 几何同源.
3. **Cross-section 几何同源律 (P020 升格)**: close_position ⇔ "收盘相对日内位置" ⇔ upper_shadow 同根; midprice/close ⇔ "close 在日内偏低" ⇔ upper_shadow 同根. TsRank time-series 量纲化削弱 cross-section level 共线性但**未破解**几何同源 (60d window 内 0.4-0.5 corr to F008).
4. **Frontier 真度律分级 (b076 实证)**:
   - 顶级生效 (vol_20d_exp 6-10, sty_r² 0.03-0.06): C006 高阶 composition + C001/C005 single atom but high signal
   - 部分生效 (vol_20d_exp 10-15, sty_r² 0.06-0.13): C004 range_to_close (vol proxy 直接载体)
   - 失效 (信号弱): C002/C003 raw shadow / body 在 60d 长窗时序量纲化下信号碎片化
