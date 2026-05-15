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

### T003 — Range / midprice / asymmetry (高阶 composition 路径) `[✗ DISPROVEN batch_092]` ⭐ admit F025 (b076) / revival disproven b092

**Round 92 update (reserve revival pool #2)**: b076/C005 (TsRank((h+l)/2/close,60), 原 reserve max_corr=0.449@F008) 5 条 revival axes 全 disproven (Python residualize sign_flip / RHS swap 撞 F027 / 30d 窗 0.83@F026 near-dup / rank-diff 信号塌缩 / alt midpoint 0.64@F026 / range/close vol-proxy). Reserve cluster 边缘候选不可救药铁证.


**Question**: range/midprice/asymmetry 类 OHLC shape ratio 60d TsRank 是否携带 forward alpha 且与库独立?

**Answer**: **PROVEN — frontier 真红利铁证**. C006 shadow_asymmetry (高阶 composition) admit 全 CP green: ic_oos=+0.019 / ls_t=+6.19 / mono PERFECT POS / alpha_surv=1.15 / style_r²=**0.029 batch min** / vol_20d_exp=**6.03 batch min** (比 F024 实证 10.6 还低 40%) / max_corr=**0.29@F007 UNDER 0.30 line** / incr_ic=+0.014 POS / ic_by_year 8/9 POS sign-stable. **frontier 真生效在 OHLC shape 域首例 + 高阶 composition 路径开辟**. C004 range/close 因 vol proxy 直接载 vol_20d basis 失效 (sty_r²=0.133). C005 midprice/close 信号顶级 (alpha_surv=1.43 batch best) 但与 F008 几何同源 (max_corr=0.45) reserve.

**Evidence trail**:
- [[batches/batch_076/candidates/C006|b076 C006]] TsRank shadow_asymmetry 60 → **admit ⭐ → F025**
- [[batches/batch_076/candidates/C004|b076 C004]] TsRank range/close 60 → reject (vol proxy poor sty_r²)
- [[batches/batch_076/candidates/C005|b076 C005]] TsRank midprice/close 60 → reserve (geometric overlap)

### T001 — Close position & shadow ratio (cross-section 几何同源律) `[✗ DISPROVEN batch_092]` (initial b076 + revival b092)

**Round 92 update**: Python residualize 路径 (round 76 标记的"唯一生还路径") **first实证失败** (b092/C001 hard_gate sign_flip). round 73 cross-section OLS residual OOS sign-flip 警告律 first应用. close-position cluster 内 residualize 不适用 — atom 主信号在 cluster 投影内, residual 是噪音. **唯一生还路径关闭**.


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

### batch_092 (2026-05-16) — reserve revival pool #2 彻底失败, 0 admit / 6 reject (direction fully-dead 铁证)

**Verdicts**: admit=0, reserve=0, reject=6 (2× hard_gate fail + 4× cluster/vol-proxy collapse).

**核心结论**:

1. **复活 b076/C005 (TsRank((h+l)/2/close,60), 原 reserve max_corr=0.449@F008) 5 条 axes 全 disproven**:
   - **Python residualize on (F008, F026)** (C001): hard_gate sign_flip train_ic=+0.030 / val_ic=-0.004 + mono_flip 0.4→-0.4. **round 73 cross-section OLS residual OOS sign-flip 警告律 first实证案例**. 机制: atom 主信号在 (F008, F026) 投影内, 残差 = removed dominant projection 后噪音, train OLS 过拟合该噪音的某 sign, OOS 噪音独立性使 sign 翻转
   - **RHS swap close→Mean(close,5)** (C002): max_corr=0.60@F027 (close 4-MA cluster) + sty_r²=0.128 + vol_20d_exp=15.0. RHS 改 5d trend-mean 反而引入 F027 close-MA family 几何
   - **30d 短窗** (C003): max_corr=0.83@F026 near_duplicate. 短窗 mid/close TsRank ≈ F026 close-position 60d TsRank 几何收敛 (虽 window 不同 cross-section ranking 几乎同源)
   - **rank-diff form** (C004): ic_oos=0.0015 hard_gate fail, oos_decay 0.107. close-position 域双窗 Sub self-cancellation 极严重 (与 b091/C004 amount/num_trades 域 rank-diff escape success 强烈对比)
   - **alt midpoint (O+C)/2** (C005): max_corr=0.64@F026 cluster. (O+C)/(2C) monotonic ≈ O/C, 仍是 close-position 家族
   - **P008 third ratio (H-L)/close** (C006): max_corr=0.30@F027 唯一脱 cluster, 但 sty_r²=0.133 + dom_style=vol_20d + incr_ic=-0.030 NEG + alpha_surv=0.986 边缘 = P030 多 CP 集体失败. 重现 b076/C004 vol-proxy pattern

2. **P030 (alpha_surv unilateral ≠ admit 充分) first实证 (C006)**: alpha_surv=0.986 + mono PERFECT (-1.0) + max_corr=0.30 clean 三项单独看都 ≥1 admit-able 但 sty_r²=0.133 + incr_ic=-0.030 NEG = library 覆盖失败. 升格"P030 multi-CP 集体保护"律 first应用. 升格规则: alpha_surv / mono / max_corr 任 1 单边强 + 另 2 反向时直接 reject, 不依赖 single CP score 通过

3. **TsRank window 在 close-position 域 sweet spot 律 (round 92 first实证)**: round 91 cockpit "TsRank window>=60d escape, >90d alpha_surv 反单调下降"已 codified. 本批 C003 (30d) max_corr=0.83 实证 **window<60d 撞 admit prototype** (F026 is 60d TsRank), 完整律升格: TsRank window 在 close-position 域只在 60d sweet spot, **<30d 撞 admit prototype, >90d 进入 cumulative-style 几何**

4. **F025/F026 absorbing prototype 律 (P021) 深化 (b092 reserve revival 验证)**: round 91 lessons "admit 后 family 续探 max_corr ≥0.55@admit"已 codified, 本批进一步: **admit prototype 在 cluster 半径 ~0.45 内的所有几何变体, 包括 reserve 边缘候选 (b076/C005 max_corr=0.449), 都被吞噬**, reserve 复活路径 (residualize / RHS swap / window sweep / rank-diff / alt midpoint) 全 disproven

5. **Python residualize 路径适用 filter 律 (升格)**: residualize 适用场景必须满足 atom 与库 cluster 距离 ∈ [0.30, 0.45] **且** barra_residual_ic > 0.020 (signal not dominated by style proj). b076/C005 max_corr=0.449 在 filter 上界 + atom signal 主要在 F008 投影内 (b092/C001 barra_residual_ic=0.025 接近 floor) → residualize 自然失败. 升格 → lessons round 92

6. **rank-diff axis atom-class 依赖律 (升格)**: rank-diff axis 在不同 atom 类有不同 behavior:
   - b091/C004 amount/num_trades 域 escape success (alpha_surv=0.86, ls_t=-2.20, max_corr=0.18 LOW)
   - b092/C004 close-position 域 self-cancellation (ic_oos=0.0015 hard_gate)
   - **机制**: rank-diff 有效需 atom cross-section dispersion 高. amount/num_trades 域 cross-section IC dispersion 大, close-position 域 dispersion 小 → 短窗已 contain 长窗 ranking 主信息, Sub 让信息相互抵消

7. **方向状态铁证**: T001 (close position & shadow) / T003 (range / midprice / asymmetry) / T004 (admit-后 frontier 上限) 全 fully-disproven. status=saturated 维持, 实质 = **fully-dead** — b093+ 不再触碰本 direction 任何 path (含 cross-family / Python wrapper / new evaluation horizon).

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
