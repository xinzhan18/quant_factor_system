---
direction_tag: tsrank_candlestick_ratio
status: saturated
priority: medium
rounds: 5
admits: 2
last_batch: batch_092
last_admits: []
last_goal: 'Round 92 — reserve revival pool #2 (asset-driven, calibration finding/013).
  Target = revive b076/C005 TsRank((h+l)/2/close,60) midprice/close. b076 实测 alpha_surv=1.43
  + ls_t=+4.84 + mono=+0.90 + incr_ic=+0.042 (4 项 CP top) 仅 max_corr=0.449@F008 cluster
  阻断 (距 0.40 阈值仅 0.049 over). direction status=saturated, 本批显式 asset-driven 复活 — finding/013
  给出 3 revival path: (1) Python residualize on (F008, F026) — DSL 表达不出 的 cross-section
  OLS 残差化; (2) RHS swap close→Mean(close,5) 切 F008 close-position 几何耦合; (3) window
  sweep + rank-diff form. 本批 6 候选覆盖所有 path + P008 third-ratio probe (intentional high-collision
  测 F024 monotonic envelope).

  Round-92 Phase 1 generator self-check 新增 4 hard rule (P030 / P004-deep / Cov-equiv
  / reciprocal duplicate). 全候选自检: - P030 (alpha_surv>1.0 unilateral form 单独 ≠ admit
  充分): 本批每候选必带 multi-CP rationale, 不依赖 alpha_surv 单边. C001 expected incr_ic POS+max_corr<0.40,
  C002 expected max_corr<0.40, C003-C005 expected incr_ic+ls_t multi-CP, C006 known-near-dup
  probe; - P004-deep (N-day path-integral 累积形式 default reject): TsRank(x,N) 是 rank-of-current-value-in-window-N,
  非 cumulative sum/aggregation — 全候选 pass; Python C001 内部用 vectorized 单步 cross-section
  OLS 残差化, 不是 N-day path-integral; - Cov-equiv (Cov(.,.)/Cov-of-zero-mean-series 已知
  cross-field bug): 全候选无 Cov form, 无 Corr 跨字段; pass; - Reciprocal monotonic-invariant
  duplicate (round 92 新发现): TsRank((h+l)/2/close, N) 与 TsRank(close/(h+l)/2, N) 在
  monotonic 函数 (Div + 单调 RHS) 下 cross-section TsRank rank 几何 ≈ N+1-TsRank 单调反向 — 不另设
  reciprocal probe (b091/C005 已实证 sign-flip 等价).

  Cockpit hint round 91 P008 finding update: TsRank window>=60d on ratio 是 escape
  path, 但 b091 实测 window>90d alpha_surv 反单调下降, 上界 ~90d. F024 anchor basin 宽度>=90d
  — long-window TsRank ratio [30,120d] 全在 F024 引力盆地内. 本批 C003 window=30d 在 60d 阈值
  以下, C002/C005 维持 60d, 不试 120d (P008 上界).

  Anti-recapitulation (b076/b077 已 disproven 不重试): - 不重试 raw TsRank((h+l)/2/close,60)
  — 那是被复活的 reserve 本身, 直接重计算 = 重复 b076/C005; - 不重试 b077 三层 nested Div/Mul / Std×TsRank
  双量纲化 / cross-product CsRank-Mul / 分母替换 (H-L)/(C+O); - 不重试 b076 hard_gate body_ratio
  TsRank60 / raw upper_shadow TsRank60.

  Hard targets: ≥1 admit 验证 reserve revival 真红利; 关键 H1 = Python residualize (F008,F026)
  能否把 max_corr 从 0.449 降至 <0.30 同时维持 alpha_surv≥1.0 + incr_ic≥+0.02 (finding/013 expected_outcome).
  若 C001 admit + max_corr<0.30 → 升格"Python residualize 是 reserve cluster 突破真路径"律 (library_gap/013
  验证). H2 = RHS swap close→Mean(close,5) 是否切 F008 同根 (C002 expected max_corr<0.40).
  H3 = 30d 短窗是否比 60d 更脱 F008 cluster (C003). H4 = rank-diff 跨窗 form (C004) 是否独立. H5
  = open-close 中点 (C005) 是否避 F008 close-position 耦合. Fail (6/6 reject) → tsrank_candlestick_ratio
  direction 彻底 dead, 升格 ''family-level Python residualize 失败律'' + 切下一 direction.'
last_activity: '2026-05-15T20:50:15Z'
created_batch: batch_076
members:
- F025
retired_members: []
reserves: []
reserves_disproven:
- C001_b076
- C005_b076
merged_into: null
created_from: cockpit_round_76_b073_F024_frontier_extension_to_OHLC_shape
status_changed_at: '2026-05-16T03:00:00Z'
status_change_reason: 'b092 reserve revival pool #2 6/6 reject + b077 frontier saturated.
  T001/T003/T004 fully-disproven. close-position cluster (F008/F025/F026/F027/F028)
  + F025 absorbing prototype joint inescapable basin; 5 axes (residualize/RHS-swap/window/rank-diff/alt-mid)
  all disproven. b093+ no retry.'
---
# tsrank_candlestick_ratio

> [!abstract]+ 方向概要
> - **状态**　🔴 `saturated` → 建议升格 `archived` (P032 + P033 双律封顶, hypothesis_promoter recommendation, Python refresh-index 接管 frontmatter 转移) · priority `medium` · rounds = 5 · admits = 2 (F024 b073 cross-link + F025 b076)
> - **一句话**　把 b073 admit F024 (TsRank-60-on-count_ratio) frontier 几何扩展到 OHLC dimensionless candlestick shape ratio. b076 admit F025 shadow_asymmetry (高阶 composition 真红利); b077 同 family 续探 6/6 reject (frontier 饱和) + b092 reserve revival pool #2 6/6 reject (reserve 边缘 cluster 不可救药). T001/T003/T004 全 fully-disproven.
> - **来源**　cockpit_round_76 frontier extension; F024 admit (b073) + tsrank_timeseries_ratio direction saturated → OHLC 几何域 frontier 机制扩展.
> - **archival 铁证**　(a) F025 absorbing prototype (max_corr ≥0.55@F025 三路径, b077); (b) close-position cluster F008/F025/F026/F027/F028 5 anchor 联合 inescapable basin (b092); (c) 5 reserve revival axes (residualize / RHS-swap / window / rank-diff / alt-mid) 全 disproven; (d) Python residualize "唯一生还路径" b092 first实证失败 (sign_flip).

---

## Hypothesis

⚠️ **status=saturated, 建议 archived (P032+P033 双律封顶)**: 核心机制 (TsRank-60 + 高阶 composition 破 cross-section 几何同源) 已在 F025 落地; b077 admit-后 family 续探无新维度; b092 reserve 边缘候选 5 axes 全 disproven 含 Python residualize. b093+ 不再触碰本 direction 任何 path.

**核心机制 (b073 F024 + b076 F025 实证)**:

1. **TsRank 60d 时序量纲化**: 把 cross-section level 替换为"个股自身 60d 分位", 绕过 cross-section vol_20d basis ranking 重叠. F024 vol_20d_exp=10.6, F025 vol_20d_exp=6.03, sty_r² 0.051/0.029.
2. **dimensionless ratio 是必要前提**: 分子分母同量纲在 cross-section 上抵消 scale.
3. **OHLC candlestick shape ratio 自然 dimensionless**: close_position ∈ [0,1], body/upper_shadow/lower_shadow ∈ [0,1], range/close ≈ 0.01-0.05.
4. **高阶 composition 是 frontier 第二阶 (P019)**: ratio-of-derived-quantity (shadow_asymmetry = upper_shadow / lower_shadow) 比 single-atom ratio 更彻底破共线性 — 分子分母同消 base scale + base volatility (max_corr 0.29 vs 0.45-0.47).
5. **⚠️ admit 后 absorbing 律 (P021, b077 实证)**: family 内 admit 后, 同 family 续探 cross-section 塌缩到 admit prototype (max_corr ≥0.55@F025), risk 维度顶级也无法逃 — admit 已占 cluster 中心.
6. **⚠️ reserve 边缘 cluster 不可救药律 (b092 实证)**: admit prototype 在 cluster 半径 ~0.45 内吞噬所有几何变体, 含 reserve 边缘候选 (b076/C005 max_corr=0.449). residualize / RHS-swap / window / rank-diff / alt-mid 5 axes 全 disproven.
7. **⚠️ Python residualize filter 律 (b092 实证)**: residualize 适用必须满足 atom 与 cluster 距离 ∈ [0.30, 0.45] **且** barra_residual_ic > 0.020. b076/C005 不满足 (距离上界 + 主信号在投影内) → residualize 自然失败.

**库内现状对照**:

- F006 upper_shadow_persistence_5d `Mean(Div(H-C, H-L), 5)` Grade B
- F008 upper_shadow_persistence_3d `Mean(Div(H-C, H-L), 3)` Grade A
- F021 含 `Mean(H/L, 60)` Grade C
- F011 williams_r_variant cross-section level form
- **F025** shadow_asymmetry_tsrank_60 (b076 admit, family absorbing prototype)
- 跨方向 cross-link anchor: F008/F026/F027/F028 (close-position cluster)

---

## Threads

### T003 — Range / midprice / asymmetry (高阶 composition 路径) `[✗ DISPROVEN b076+b092]` ⭐ admit F025 (b076)

**Question**: range/midprice/asymmetry 类 OHLC shape ratio 60d TsRank 是否携带 forward alpha 且与库独立?

**Answer**: **PARTIAL PROVEN → cluster saturated**. C006 shadow_asymmetry admit 全 CP green (ic_oos=+0.019, ls_t=+6.19, mono PERFECT POS, alpha_surv=1.15, sty_r²=0.029, vol_20d_exp=6.03, max_corr=0.29@F007, incr_ic=+0.014). C004 range/close vol-proxy 失败 (sty_r²=0.133). C005 midprice/close 信号顶级 (alpha_surv=1.43) 但 max_corr=0.45@F008 reserve. **b092 reserve revival**: C005 5 axes 全 disproven (Python residualize sign_flip / RHS swap 撞 F027 / 30d 窗 0.83@F026 / rank-diff 信号塌缩 / alt midpoint 0.64@F026). Reserve 边缘 cluster 不可救药铁证.

**Evidence trail**:
- [[batches/batch_076/candidates/C006|b076 C006]] shadow_asymmetry → **admit ⭐ → F025**
- [[batches/batch_076/candidates/C005|b076 C005]] midprice/close → reserve → b092 revival 全 disproven
- [[batches/batch_076/candidates/C004|b076 C004]] range/close → reject (vol proxy)
- [[batches/batch_092|b092]] 6/6 reject revival pool #2

### T001 — Close position & shadow ratio (cross-section 几何同源律) `[✗ DISPROVEN b076+b092]`

**Question**: close_position / upper_shadow ratio 60d TsRank 与库 F006/F008/F011 是否几何独立?

**Answer**: **DISPROVEN**. 单原子 atom 与 F006/F008 共线性 0.4-0.5 不可解 (TsRank 仅削弱). C001 信号顶级 (ls_t=-6.36, mono PERFECT NEG, alpha_surv=1.18) 但 max_corr=0.47@F008 阻断 reserve. **b092 Python residualize 唯一生还路径关闭** (C001 hard_gate sign_flip train_ic=+0.030/val_ic=-0.004, mono_flip 0.4→-0.4) — round 73 cross-section OLS residual OOS sign-flip 警告律 first实证案例.

**Evidence trail**:
- [[batches/batch_076/candidates/C001|b076 C001]] TsRank close_position 60 → reserve
- [[batches/batch_076/candidates/C002|b076 C002]] TsRank upper_shadow 60 → reject
- [[batches/batch_092|b092]] Python residualize first实证失败

### T002 — Body ratio TsRank `[✗ DISPROVEN b076]`

**Question**: body_ratio 60d TsRank 是否携带 forward NEG alpha (趋势耗尽假设)?

**Answer**: **DISPROVEN**. C003 hard_gate fail — train→val regime drift sign_flip (train -0.005 / val +0.008) + oos_decay -1.77. body_ratio 是日内动量信号, 60d TsRank 把动量 mean-reverted, 信号碎片化.

**Evidence trail**: [[batches/batch_076/candidates/C003|b076 C003]] → hard_gate sign_flip.

### T004 — admit-后 frontier 上限测试 `[✗ DISPROVEN b077]` (饱和铁证, P021 升格)

**Question**: F025 admit 后, 同 family 续探 (三层 nested / 双量纲化 / cross-product Mul / 分母替换) 是否突破 F025 absorbing?

**Answer**: **DISPROVEN — 6/6 reject**. 三种 frontier 路径全部塌缩:
- 三层 nested (C001 Div / C005 Mul) max_corr 0.58-0.63@F025
- CsRank-Mul cross-product (C004) max_corr 0.70@F025 完全 collapse
- Std×TsRank 双量纲化 (C002) vol_20d_exp 42, sty_r² 0.228 (Std 放大 vol proxy)
- 分母替换 (C003 (C+O) / C006 midprice) sty_r² 0.132-0.133 + C003/C006 IC daily corr=0.9996 in-batch dup

**Evidence trail**: [[batches/batch_077|b077]] 全 6 candidates

**升格律** (Phase 5 lessons):
- P019 高阶 composition 路径反向证伪 (Mul/Div 几何等价)
- P021 几何 absorbing factor 律 → finding/019
- P022 double-quantization 反向律
- P023 CsRank-Mul cross-product 塌缩律 → finding/017
- P024 denominator family 等价性自检 → finding/021

---

## Known Failures

| Candidate | Expression | Reason |
|---|---|---|
| [[batches/batch_076/candidates/C002\|b076 C002]] | `TsRank(Div(H-O, H-L), 60)` | 信号弱 (ls_t=-0.44) + max_corr=0.38@F007 |
| [[batches/batch_076/candidates/C003\|b076 C003]] | `TsRank(Div(\|C-O\|, H-L), 60)` | hard_gate sign_flip + oos_decay -1.77 |
| [[batches/batch_076/candidates/C004\|b076 C004]] | `TsRank(Div(H-L, C), 60)` | sty_r²=0.133 (vol proxy) |
| [[batches/batch_077/candidates/C001\|b077 C001]] | 三层 nested Div (H-mid_oc)/(mid_oc-L)*body_ratio | max_corr=0.6272@F025 (P019) |
| [[batches/batch_077/candidates/C002\|b077 C002]] | `TsRank(Std((H-L)/C, 20), 60)` | vol_20d_exp=42, sty_r²=0.228 (P022) |
| [[batches/batch_077/candidates/C003\|b077 C003]] | `TsRank((H-L)/(C+O), 60)` | sty_r²=0.132, C006 数学等价 |
| [[batches/batch_077/candidates/C004\|b077 C004]] | `Mul(CsRank(num_trades/vol), CsRank((H-mid_oc)/(mid_oc-L)))` | max_corr=0.6972@F025 (P023) |
| [[batches/batch_077/candidates/C005\|b077 C005]] | `TsRank(Mul(body_ratio, shadow_asym), 60)` | max_corr=0.5817@F025 + decay 5.81 |
| [[batches/batch_077/candidates/C006\|b077 C006]] | `TsRank((H-L)/midprice, 60)` | C003 数学等价 in-batch dup |
| [[batches/batch_092|b092 C001]] | Python residualize TsRank((h+l)/2/close,60) on (F008,F026) | hard_gate sign_flip (train +0.030/val -0.004), mono_flip — Python residualize filter 律 first实证 |
| [[batches/batch_092|b092 C002]] | RHS swap close→Mean(close,5) | max_corr=0.60@F027 + sty_r²=0.128 |
| [[batches/batch_092|b092 C003]] | 30d 短窗 mid/close | max_corr=0.83@F026 (window<60d 撞 admit prototype) |
| [[batches/batch_092|b092 C004]] | rank-diff cross-window form | ic_oos=0.0015 hard_gate (close-position 域 dispersion 低, Sub self-cancel) |
| [[batches/batch_092|b092 C005]] | alt midpoint (O+C)/2 | max_corr=0.64@F026 (monotonic ≈ O/C) |
| [[batches/batch_092|b092 C006]] | (H-L)/close 第三 ratio | sty_r²=0.133 + incr_ic=-0.030 NEG + alpha_surv=0.986 (P030 集体失败) |

---

## Narrative Log

> **Archival recommendation (hypothesis_promoter)**: 本方向建议从 `saturated` → `archived`. 触发律 = P032 (5 reserve-revival-axes-all-disproven 含 Python residualize) + P033 (close-position cluster 5 anchor 联合 inescapable basin). frontmatter.status 由 Python refresh-index 转移, 此处仅 narrative 标注.

### batch_092 (2026-05-16) — reserve revival pool #2 彻底失败, 0/6 admit (direction fully-dead)

**Verdicts**: admit=0, reserve=0, reject=6 (2× hard_gate + 4× cluster/vol-proxy collapse).

**核心结论**:

1. **b076/C005 5 revival axes 全 disproven**:
   - Python residualize on (F008, F026) (C001): hard_gate sign_flip + mono_flip. round 73 cross-section OLS residual OOS sign-flip 律 first实证. 机制: atom 主信号在投影内, 残差 = 噪音, train OLS 过拟合该噪音, OOS sign 翻转
   - RHS swap close→Mean(close,5) (C002): max_corr=0.60@F027 (close-MA family 几何)
   - 30d 短窗 (C003): max_corr=0.83@F026 near_duplicate
   - rank-diff form (C004): ic_oos=0.0015 hard_gate (close-position 域 dispersion 低 → Sub self-cancel; 对比 b091/C004 amount/num_trades 域 escape success)
   - alt midpoint (O+C)/2 (C005): max_corr=0.64@F026 (monotonic ≈ O/C)
   - (H-L)/close 第三 ratio (C006): max_corr=0.30@F027 clean 但 sty_r²=0.133 + incr_ic NEG = P030 集体失败

2. **P030 first实证 (C006)**: alpha_surv/mono/max_corr 单边强 + sty_r²/incr_ic 反向 → reject. 不依赖 single CP score.

3. **TsRank window 在 close-position 域 sweet spot 律**: <30d 撞 admit prototype (F026 is 60d TsRank), 60d 唯一 sweet spot, >90d 进入 cumulative-style 几何 (P008 上界).

4. **F025/F026 absorbing prototype 律 (P021) 深化**: admit prototype 在 cluster 半径 ~0.45 内吞噬所有几何变体, 含 reserve 边缘 (max_corr=0.449).

5. **Python residualize filter 律 (升格 lessons)**: 适用条件 = atom 与 cluster 距离 ∈ [0.30, 0.45] **且** barra_residual_ic > 0.020. b076/C005 不满足.

6. **rank-diff axis atom-class 依赖律 (升格)**: amount/num_trades 域 escape success vs close-position 域 self-cancellation. 机制 = atom cross-section dispersion 决定 rank-diff 信息保留.

7. **方向状态铁证**: T001/T003/T004 全 fully-disproven. saturated 实质 = fully-dead. b093+ 不再触碰任何 path (含 cross-family / Python wrapper / new evaluation horizon).

### batch_077 (2026-05-02) — frontier 上限饱和铁证, 0/6 admit (status pivot → saturated)

**Verdicts**: admit=0, reserve=0, reject=6.

**核心结论**:

1. **F025 absorbing prototype 律 (P021 升格 → finding/019)**: 同 family 续探三种路径 max_corr ≥0.58@F025 (nested Div 0.6272, cross-product Mul 0.6972, nested Mul 0.5817). risk 顶级也无法逃 cross-section absorbing.
2. **range/normalized-price family vol proxy 不可解**: 三 form 分母替换 sty_r² ∈ [0.132, 0.133] OVER, alpha_surv 0.99-1.0 边缘.
3. **double-quantization 反向加重 vol (P022)**: Std×TsRank vol_20d_exp 42, sty_r² 0.228.
4. **CsRank-Mul cross-product 塌缩律 (P023 → finding/017)**: max_corr=0.70@F025. cross-product 续探需 directionally orthogonal atoms.
5. **in-batch denominator 等价性 bug (P024 → finding/021)**: C003 与 C006 IC daily corr=0.9996. Phase 1 checklist 加 "denominator pairwise 数学等价性测试".
6. **status pivot**: active → saturated, priority high → medium. admits=2 维持.
7. **唯一生还路径 (当时)** = Python residualize on F025 — b092 first实证失败, 路径关闭.

### batch_076 (2026-05-02) — NEW direction 首批, 1 admit (F025) ⭐ admit pivot

**Verdicts**: admit=1 (C006 → F025), reserve=2 (C001 close_position, C005 midprice/close), reject=3.

**核心结论**:

1. **F025 落地** — TsRank-60 frontier 在 OHLC shape 域首例铁证. ic_oos=+0.019, ls_t=+6.19, mono PERFECT POS, alpha_surv=1.15, sty_r²=0.029 (batch min), vol_20d_exp=6.03 (比 F024 实证 10.6 还低 40%), max_corr=0.29@F007.
2. **方向升格律 — 高阶 composition 破共线性 (P019)**: shadow_asymmetry (ratio of two derived shadow lengths) 比 single atom 更彻底破共线性 (max_corr 0.29 vs 0.45-0.47). 机制: 高阶 composition 在分子分母上抵消 base scale 与 base volatility.
3. **Cross-section 几何同源律 (P020)**: close_position ⇔ upper_shadow 同根; midprice/close ⇔ upper_shadow 同根. TsRank 仅削弱未破解 cross-section 几何同源.
4. **Frontier 真度律分级**: 顶级 (vol_20d_exp 6-10, sty_r² 0.03-0.06) = C006 高阶 composition; 部分 (vol_20d_exp 10-15) = C004 range_to_close; 失效 = C002/C003 (60d 长窗下信号碎片化).
