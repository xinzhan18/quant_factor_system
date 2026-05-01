---
direction_tag: tsrank_candlestick_ratio
status: active
priority: high
rounds: 2
admits: 2
last_batch: batch_076
last_admits:
- F025
last_goal: "Round 76 NEW direction (b073 admit F024 frontier 几何扩展). 假设:\n把 F024 admit\
  \ 验证的 TsRank-60-on-dimensionless-ratio 几何 (vol_20d_exp 65%↓ 到 ~10.6,\nstyle_r² 75%↓\
  \ 到 0.051, max_corr 0.13@F001) 从 count ratio (num_trades/volume) 扩展到\nOHLC dimensionless\
  \ candlestick shape ratios. F024 是 \"trade density\" count 量纲,\n本批是 \"candlestick\
  \ shape\" geometric 量纲, 几何上 cross-section level 完全独立, 共享\nTsRank time-series rank-form\
  \ 量纲化机制. 库内现状: F006/F008 是 Mean(upper_shadow,N),\nF021 是 Mean(H/L,60) cross-section\
  \ level form, 本批 TsRank time-series 形式与 Mean\n几何不同 (位置 vs 持续性). 6 候选探索 OHLC shape\
  \ ratio × TsRank-60 矩阵:\n  (a) close_position TsRank: 收盘在日内位置 (Williams %R 反向)\n\
  \  (b) upper_shadow_ratio TsRank: 上影占全日 range 比例\n  (c) body_ratio TsRank: 实体占全日\
  \ range 比例\n  (d) range_to_close TsRank: 全日 range 占收盘价比 (波动率 proxy 但 normalized)\n\
  \  (e) midprice_to_close TsRank: 中价/收盘价 (intraday drift proxy)\n  (f) shadow_asymmetry\
  \ TsRank: 上下影长之比 (非对称性)\n红线: max_corr<0.30 to library (含 F024); alpha_survival>=0.40\
  \ + ic_by_year sign-stable\n+ incr_ic POS (P008/P011); |corr $market_cap|<0.3; +1e-9\
  \ epsilon 防 div-by-zero (P018).\nAnti-recap: 不重 b068-b075 reject; F006/F008 (Mean\
  \ shadow) / F021 (Mean H/L 60) /\nF011 williams_r_variant (cross-section level)\
  \ 时序量纲化形式都未被 admit, 库内 0\nTsRank-OHLC shape 几何. 警示与 F011 cross-section level 撞 atom\
  \ (close_position) — 重\n几何独立性靠 TsRank time-series rank-form 解耦. 目标 ≥1 admit 验证 TsRank-OHLC\
  \ frontier\n真度; 否则首批反向证伪 → 方向 dead."
last_activity: '2026-05-01T22:18:46Z'
created_batch: batch_076
members:
- F025
retired_members: []
reserves:
- C001_b076
- C005_b076
merged_into: null
created_from: cockpit_round_76_b073_F024_frontier_extension_to_OHLC_shape
status_changed_at: '2026-05-02T00:30:00Z'
status_change_reason: b076 1 admit (F025 shadow_asymmetry_tsrank_60). probing → active.
---
# tsrank_candlestick_ratio

> [!abstract]+ 方向概要
> - **状态**　🟢 `active` (round 76 首批 1 admit, frontier 真生效在 OHLC shape 域首例) · priority `high` · rounds = 1 · admits = 1
> - **一句话**　把 b073 admit F024 (TsRank-60-on-count_ratio) 验证的 frontier 几何, 扩展到 OHLC dimensionless candlestick shape ratio. b076 C006 shadow_asymmetry admit 验证高阶 composition 路径 (ratio-of-derived-quantity 比 single-atom ratio 更彻底破 cross-section 几何同源).
> - **来源**　cockpit_round_76 frontier extension; F024 admit (b073) + tsrank_timeseries_ratio direction saturated → 同 frontier 机制在 OHLC 几何域未被探索.

---

## Hypothesis

**核心机制 (b073 F024 + b076 F025 实证)**:

1. **TsRank 60d 时序量纲化**: 把 cross-section level 替换为"个股自身 60d 分位", 绕过 cross-section vol_20d basis 上的 ranking 重叠. F024 实测 vol_20d_exp = 10.6, F025 vol_20d_exp = 6.03 (更低), style_r² 分别 0.051 / 0.029.
2. **dimensionless ratio 是必要前提**: 分子分母同量纲在 cross-section 上抵消 scale.
3. **OHLC candlestick shape ratio 自然 dimensionless**: close_position ∈ [0,1], body/upper_shadow/lower_shadow ∈ [0,1], range/close ≈ 0.01-0.05.
4. **高阶 composition 是 frontier 第二阶 (b076 P019 升格)**: ratio-of-derived-quantity (例 shadow_asymmetry = upper_shadow / lower_shadow) 比 single-atom ratio 更彻底破 cross-section 共线性 — 分子分母同消 base scale + base volatility.

**库内现状对照**:

- F006 upper_shadow_persistence_5d = `Mean(Div(H-C, H-L), 5)` Grade B
- F008 upper_shadow_persistence_3d = `Mean(Div(H-C, H-L), 3)` Grade A
- F021 含 `Mean(H/L, 60)` Grade C
- F011 williams_r_variant cross-section level form
- F025 shadow_asymmetry_tsrank_60 (b076 NEW) — 高阶 OHLC composition frontier

---

## Threads

### T001 — Close position & shadow ratio (cross-section 几何同源律) `[✗ DISPROVEN batch_076]`

**Question**: close_position / upper_shadow ratio 60d TsRank 是否与库 F006/F008/F011 几何独立?

**Answer**: **partial DISPROVEN**. cross-section 几何同源律实证 — 单原子 atom 与库 F006/F008 共线性 0.4-0.5 不可解 (TsRank 时序量纲化仅削弱). C001 信号顶级 (ls_t=-6.36, mono PERFECT NEG, alpha_surv=1.18, sign-stable 8/9 NEG) 但 max_corr=0.47@F008 OVER 0.30 阻断 admit (reserve). C002 raw upper_shadow 信号弱 + 库 overlap 双重失败.

**Evidence trail**:
- [[batches/batch_076/candidates/C001|b076 C001]] TsRank close_position 60 → reserve (max_corr=0.47@F008 阻断)
- [[batches/batch_076/candidates/C002|b076 C002]] TsRank upper_shadow 60 → reject (weak signal + max_corr=0.38)

**复活路径**: Python residualize on F008; 替换 atom 为 close_position - body_position (高阶 composition).

### T002 — Body ratio TsRank `[✗ DISPROVEN batch_076]`

**Question**: body_ratio 60d TsRank 是否携带 forward NEG alpha (趋势耗尽假设)?

**Answer**: **DISPROVEN**. C003 hard_gate fail — train→val regime drift sign_flip (train -0.005 / val +0.008) + oos_decay -1.77. body_ratio 是日内动量信号, 60d TsRank time-series form 把动量 mean-reverted, 信号碎片化. 不适合 60d 长窗 (F020 用 Mean 短窗形式更优).

**Evidence trail**:
- [[batches/batch_076/candidates/C003|b076 C003]] TsRank body_ratio 60 → hard_gate sign_flip.

### T003 — Range / midprice / asymmetry (高阶 composition 路径) `[✓ ANSWERED batch_076]` (admit C006, frontier 真度铁证)

**Question**: range/midprice/asymmetry 类 OHLC shape ratio 60d TsRank 是否携带 forward alpha 且与库独立?

**Answer**: **partial PROVEN**. C006 shadow_asymmetry (高阶 composition) admit — 全 CP green: ic_oos=+0.019 / ls_t=+6.19 / mono PERFECT POS / alpha_surv=1.15 / style_r²=**0.029 batch min** / vol_20d_exp=**6.03 batch min** / max_corr=**0.29@F007 UNDER 0.30 line** / incr_ic=+0.014 POS / ic_by_year 8/9 POS sign-stable. **frontier 真生效在 OHLC shape 域首例铁证 + 高阶 composition 路径开辟**. C004 range/close 因 vol proxy 直接载 vol_20d basis 失效 (sty_r²=0.133 poor). C005 midprice/close 信号顶级 (alpha_surv=1.43 batch best) 但与 F008 几何同源 (max_corr=0.45) reserve.

**Evidence trail**:
- [[batches/batch_076/candidates/C006|b076 C006]] TsRank shadow_asymmetry 60 → **admit ⭐ → F025**
- [[batches/batch_076/candidates/C004|b076 C004]] TsRank range/close 60 → reject (vol proxy poor sty_r²)
- [[batches/batch_076/candidates/C005|b076 C005]] TsRank midprice/close 60 → reserve (geometric overlap)

**复活路径** (升格 lessons): atom 互补 — 后续 frontier 可探索 (a) 三层 composition (shadow ratio × body ratio); (b) Python residualize on F008 解 C001/C005 几何同源; (c) midprice/MeanClose60 替换分母破 C005 共线性.

---

## Known Failures

| Candidate | Expression | Reason |
|---|---|---|
| [[batches/batch_076/candidates/C002\|batch_076 C002]] | `TsRank(Div(Sub($high,$open), Add(Sub($high,$low),1e-9)), 60)` | 信号弱 (ls_t=-0.44, mono OOS=-0.30) + max_corr=0.38@F007 — raw upper_shadow 长窗时序量纲化破坏短期信号 |
| [[batches/batch_076/candidates/C003\|batch_076 C003]] | `TsRank(Div(Abs(Sub($close,$open)), Add(Sub($high,$low),1e-9)), 60)` | hard_gate fail: sign_flip train -0.005/val +0.008 + oos_decay -1.77; body_ratio TsRank 60d regime drift |
| [[batches/batch_076/candidates/C004\|batch_076 C004]] | `TsRank(Div(Sub($high,$low), Add($close,1e-9)), 60)` | sty_r²=0.133 OVER 0.12 poor + alpha_surv=0.99 边缘; range/close 是 vol proxy 直接载 vol_20d basis |

---

## Narrative Log

### batch_076 (2026-05-02) — NEW direction 首批, 1 admit (F025)

**Verdicts**: admit=1 (C006 → F025 shadow_asymmetry_tsrank_60), reserve=2 (C001 close_position, C005 midprice/close), reject=3 (C002 weak shadow, C003 hard_gate, C004 vol-proxy poor).

**核心结论**:

1. **F025 落地** — TsRank-60 frontier 真生效在 OHLC shape 域首例铁证. 全 CP green: ic_oos=+0.019, ls_t=+6.19, mono PERFECT POS, alpha_surv=1.15, sty_r²=0.029 (batch min), vol_20d_exp=6.03 (batch min, 比 F024 实证 10.6 还低 40%), max_corr=0.29@F007 (under 0.30 line), incr_ic=+0.014 POS, ic_by_year 8/9 POS sign-stable.

2. **方向升格律 — 高阶 composition 破共线性 (P019 升格 candidate)**: C006 shadow_asymmetry (ratio of two shadow lengths) 比 C001 close_position / C005 midprice/close 更彻底破 cross-section 共线性 — max_corr 0.29 vs 0.45-0.47. 机制: 高阶 composition 在分子分母上抵消 base scale 与 base volatility, single atom 仅时序量纲化无法破解 cross-section 几何同源.

3. **Cross-section 几何同源律 (P020 升格 candidate)**: close_position ⇔ "收盘相对日内位置" ⇔ upper_shadow 同根; midprice/close ⇔ "close 在日内偏低" ⇔ upper_shadow 同根. TsRank time-series 量纲化削弱 cross-section level 共线性但**未破解**几何同源 (cross-section 上几何同源量在 60d window 内仍呈 0.4-0.5 corr to F008).

4. **Frontier 真度律分级 (b076 实证)**:
   - 顶级生效 (vol_20d_exp 6-10, sty_r² 0.03-0.06): C006 高阶 composition + C001/C005 single atom but high signal
   - 部分生效 (vol_20d_exp 10-15, sty_r² 0.06-0.13): C004 range_to_close (vol proxy 直接载体)
   - 失效 (信号弱): C002/C003 raw shadow / body 在 60d 长窗时序量纲化下信号碎片化

**下一批 frontier**: 高阶 OHLC composition (ratio-of-derived-quantity 形式) 续探 — (upper_shadow/lower_shadow 倍率) × (body/range), 三层 composition 测 frontier 上限; 警示 close_position / midprice / range_to_close 形态已 frontier 局部失效.
