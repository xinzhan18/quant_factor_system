---
direction_tag: tsrank_timeseries_ratio
status: saturated
priority: medium
rounds: 4
admits: 1
last_batch: batch_074
last_admits: []
last_goal: '续探 b073 admit hot streak（F024 Grade A score=87.0 落地）— 沿 next_hint 三轴扩展
  frontier: (a) window ablation 30d/45d/90d 测 sweet spot 边界 (b073 锚定 60d>120d，本批补
  30d/45d/90d 完整曲线); (b) cross-atom dimensionless count ratio 拓展 ($num_trades/$circ_market_cap
  mass-normalized + 镜像 $volume/$num_trades = avg_trade_size) — P012 dimensionless
  count ratio 真红利原子类型续探; (c) cross-product Mul(F024_atom, CsRank(short-momentum))
  测复合 alpha 维度。红线: alpha_survival ≥ 0.40 + ic_by_year sign-stable + incr_ic POS +
  max_corr<0.30 to library (含 F024)。Anti-recap: 不重 b068-b073 reject 候选；不重 b072 C006
  mirror atom 几何 (Div($amount,$num_trades) 已 reject)。 目标: window 曲线找到 30d/45d 是否更优
  sweet spot + cross-atom 至少 1 admit + cross-product max_corr<0.30 to F024 验证独立维度。'
last_activity: '2026-05-01T21:23:41Z'
created_batch: batch_073
members:
- F024
retired_members: []
reserves: []
merged_into: null
created_from: cockpit_round_73_frontier_TsRank_window_60d_on_ratio_fields
status_changed_at: '2026-05-02T00:30:00Z'
status_change_reason: b074 6/6 reject — F024 已饱和核心 atom × window 几何; window ablation
  plateau (30/45/90d corr ≥0.91 to F024); mirror atom corr 0.96 镜像反号; cap 分母 frontier
  失效 + library reducer; Mul cross-product alpha_surv collapse — 三轴 ablation 完成 frontier
  scope 测绘, 核心几何空间已被 F024 占领
---
# tsrank_timeseries_ratio

> [!abstract]+ 方向概要
> - **状态**　🟡 `saturated` (round 74 三轴 ablation 完成 frontier scope 测绘, 核心几何已被 F024 占领) · priority `medium` · rounds = 2 · admits = 1
> - **一句话**　基于 lessons P008 frontier — TsRank window≥60d on dim-less count ratio 是新 vol_20d-escape 路径; b073 F024 (num_trades/volume, 60d) admit 验证 frontier 真度; b074 三轴扩展全军覆没确认 F024 已饱和此核心几何空间.
> - **来源**　Phase 5 round 73 consolidation 升格 P008 frontier; institutional_flow_proxy T001 partial-progress 余烬延展.

---

## Hypothesis

**机理 (TsRank-ratio frontier)**:

1. **核心 atom 是 ratio** (Div(A, B) where A, B 同量纲或 size-correlated cancel): 分子分母同量纲在 cross-section 上抵消 size scale; TsRank 在 60d 窗口把 cross-section level 替换为"个股自身分位", 绕过 vol_20d basis 上的 ranking 重叠.
2. **window≥60d 关键参数**: b072 C006 60d 实证, b073 C006 ablation 证实 60d 是 sweet spot, 120d 不优于 60d.
3. **alpha_survival ≥ 0.40 + ic_by_year sign-stable + incr_ic > 0**: lessons P011/P014 admission 三必要条件.
4. **frontier 真生效 atom 类型律 (b073 升格 P012)**: 仅当 ratio atom 自身已 dimensionless (counts per share / [0,1] body ratio) 时 frontier 真生效.

---

## Threads

### T001 — VWAP-proxy 时序分位是否携带 forward alpha? `[✗ DISPROVEN batch_073]`
**Question**: `TsRank(amount/volume, 60)` 是 VWAP proxy 个股 60d 历史分位; 高分位 = 当前成交均价异常高 (机构买在高位) → forward reversal 假设.
**Answer**: frontier 失效首例. C001 alpha_surv=0.24 + style_r²=0.49 + dom=vol_20d 三立 reject. ratio 含绝对价格量纲 → vol_20d 嵌入残留, 非所有 ratio 都享受 frontier 红利.
**Evidence trail**: [[batches/batch_073/candidates/C001|batch_073 C001]] alpha_surv=0.24 → reject.

### T002 — Normalized range 时序分位是否脱 vol_20d? `[✗ DISPROVEN batch_073]`
**Question**: `(H-L)/C` 是日内振幅归一, 60d TsRank 应在个股层定义"异常波动日". 猜测: 高分位 = 异常高波动 = forward reversal.
**Answer**: frontier 真生效但 incr_ic 强 NEG. C002 alpha_surv=0.99 + style_r²=0.13 真生效证实, 但 incr_ic=-0.034 → P008 library reducer reject. F022 close_position 已复合预测.
**Evidence trail**: [[batches/batch_073/candidates/C002|batch_073 C002]] frontier success but library_reducer.

### T003 — Body ratio 时序分位 (最干净 OHLC 组合) `[✗ DISPROVEN batch_073]`
**Question**: `(C-O)/(H-L)` 是实体 / 总幅度 (无量纲, 0-1 范围), TsRank60 个股层 conviction signal — 高分位 = 当前买盘 conviction 强.
**Answer**: frontier 强证实但同候 reject. C003 alpha_surv=1.14 + style_r²=0.082 整批最清洁, 但 max_corr=0.37@F008 同 candlestick 几何 + incr_ic=-0.032 + ic_2015 anomaly 三立阻断.
**Evidence trail**: [[batches/batch_073/candidates/C003|batch_073 C003]] cleanest frontier but admission triple-blocked.

### T004 — Trade density 时序分位 `[✓ ANSWERED batch_073]` (admit, frontier 真度铁证)
**Question**: `num_trades/volume` 是单笔均量倒数 (小单子比例 → retail 主导), TsRank60 = 个股层 retail attention 分位.
**Answer**: 完整证实. C004 全 CP green admit — ic_oos=+0.045 / ls_t=+9.08 整库顶级 / mono=+1.00 PERFECT POS / alpha_surv=0.58 + style_r²=0.051 (整批最低) + max_corr=0.13@F001 (整批最低) + incr_ic=+0.0085 POSITIVE + ic_by_year 2018-2023 全 POS + train_val_decay=3.91. retail-driven small-order frequency 在 csi1000 daily 上是 dimensionless count ratio 几何 sweet spot.
**Evidence trail**: [[batches/batch_073/candidates/C004|batch_073 C004]] TsRank(num_trades/volume, 60) → admit ⭐.

### T005 — Turnover-per-cap 时序分位 `[✗ DISPROVEN batch_073]`
**Question**: `$turnover_rate / $market_cap` 是每元市值 turnover, TsRank60 = 个股层"超常 turnover"分位.
**Answer**: frontier 部分失效 + library reducer. C005 alpha_surv=0.91 PASS 但 vol_20d_exp=17.4 + max_corr=0.38 + incr_ic=-0.036. ratio 含 market_cap 分母 → frontier 部分失效.
**Evidence trail**: [[batches/batch_073/candidates/C005|batch_073 C005]] partial frontier + library_reducer.

### T006 — Window 120d vs 60d 对照 `[✗ DISPROVEN batch_073]` (window ablation)
**Question**: T002 同 atom 换 window=120d; 测试是否 60d 是最优参数还是更长窗口更优. 120d 时序分位"长期 anomaly".
**Answer**: 120d 不优于 60d, 反向恶化. C006 vs C002: vol_20d_exp 12.6→21.0 (+66%), alpha_surv 0.99→0.92, style_r² 0.13→0.17. 120d 引入额外 vol_20d 嵌入路径 (longer window samples 更多 vol cycle). frontier window 参数曲线定锚 60d sweet spot.
**Evidence trail**: [[batches/batch_073/candidates/C006|batch_073 C006]] 120d window worse than 60d.

### T007 — Window ablation 30d/45d/90d on F024 atom `[✗ DISPROVEN batch_074]` (plateau confirmed)
**Question**: F024 (60d) 是单点 sweet spot 还是 plateau? b073 仅做 60d↔120d, 未测 30d/45d/90d。
**Answer**: 30d/45d/90d ic_oos 单调上升 (0.040→0.043→0.047) 但 corr to F024 ≥0.91 全部 hard_gate near_duplicate fail。**60d 不是 ic_oos 单点最大 (90d 高 0.002)，但综合 mono PERFECT + lowest style_r² 0.051 + alpha_surv 0.58 是 risk-adjusted 最优**。TsRank rolling 在 ±2x window-ratio 内 corr ≥0.91 — window 单变量 ablation 不是 library expansion 路径 (P015 升格候选)。
**Evidence trail**: [[batches/batch_074/candidates/C001|b074 C001]] 30d / [[batches/batch_074/candidates/C002|b074 C002]] 45d / [[batches/batch_074/candidates/C003|b074 C003]] 90d — 三 window plateau corr 0.914/0.977/0.962 to F024.

### T008 — Cross-atom $num_trades/$circ_market_cap `[✗ DISPROVEN batch_074]` (cap 分母 frontier 失效)
**Question**: 把 F024 的分母 $volume 换成 $circ_market_cap, 是否仍享受 P012 dim-less count ratio frontier 红利? 假设 mass-normalized retail intensity 是新独立信号。
**Answer**: frontier 部分失效 + library reducer。C004 alpha_surv=1.16 PASS 但 vol_20d_exp=19.1 高 + style_r²=0.150 borderline + mono OOS=-0.30 sign decay + incr_ic=-0.038 strong NEG to F022。**重演 b073 C005 ($turnover/$market_cap) 同失败模式**：cap 分母 → vol_20d 嵌入残留。**P016 升格候选**: dim-less count ratio frontier scope 仅适用于两端都 microstructure-pure 字段 (volume, num_trades) — cap 分母 触发 vol_20d 嵌入路径未脱。
**Evidence trail**: [[batches/batch_074/candidates/C004|b074 C004]] cap-denominator pollutes frontier.

### T009 — Mirror atom $volume/$num_trades (F024 reciprocal) `[✗ DISPROVEN batch_074]`
**Question**: F024 atom 倒数 ($volume/$num_trades = avg trade size) 是否是独立信号? 假设大单主导 vs 小单主导是不同 institutional flow proxy。
**Answer**: 几何上几乎等价 F024。corr=-0.957 镜像反号 (mono +1→-1, ic_oos +0.045→-0.045) + incr_ic=-0.034 NEG library reducer。TsRank rolling rank operator 对 reciprocal atom 几乎不变 (P017 升格候选)。Mirror atom 不是 library expansion 路径。
**Evidence trail**: [[batches/batch_074/candidates/C005|b074 C005]] reciprocal corr 0.957 to F024.

### T010 — Cross-product Mul(F024_atom, CsRank short-momentum) `[✗ DISPROVEN batch_074]`
**Question**: F024 retail-attention 分位 × 5d 价格变动 cross-section rank, 测试复合 alpha 维度。
**Answer**: triple hard_gate fail (sign_flip + oos_decay + mono_flip) + alpha_surv collapse 0.07 + incr_ic=-0.023 NEG。CsRank momentum 把 vol_20d 嵌入路径重新引入 + Mul cross-product 改变 cross-section moment structure → Barra style basis 重新捕捉。**P018 升格候选**: Mul cross-product wrapper (F admitted × F admitted) 在 csi1000 daily 普遍失败几何 (b070-b074 5+ 次实证)。
**Evidence trail**: [[batches/batch_074/candidates/C006|b074 C006]] Mul cross-product alpha_surv collapse.

---

## Known Failures

| Candidate | Expression | Reason |
|---|---|---|
| [[batches/batch_073/candidates/C001\|batch_073 C001]] | `TsRank(Div($amount, $volume), 60)` | alpha_surv=0.24 FAIL + style_r²=0.49 (poor) + dom=vol_20d 三立 — VWAP proxy ratio 含绝对价格量纲, frontier 失效首例 |
| [[batches/batch_073/candidates/C002\|batch_073 C002]] | `TsRank(Div(Sub($high,$low), $close), 60)` | frontier 真生效 (alpha_surv=0.99 + style_r²=0.13) 但 incr_ic=-0.034 strong NEG library reducer; F022 已复合预测 |
| [[batches/batch_073/candidates/C003\|batch_073 C003]] | `TsRank(Div(Sub($close,$open), Sub($high,$low)), 60)` | alpha_surv=1.14 整批最清洁 frontier 强证实, 但 max_corr=0.37@F008 同 candlestick 几何 + incr_ic=-0.032 + ic_2015 +0.017 anomaly 三立阻断 |
| [[batches/batch_073/candidates/C005\|batch_073 C005]] | `TsRank(Div($turnover_rate, $market_cap), 60)` | alpha_surv=0.91 PASS 但 ratio 含 market_cap 分母 → vol_20d_exp=17.4 偏高 + max_corr=0.38@F022 + incr_ic=-0.036 strong NEG library reducer |
| [[batches/batch_073/candidates/C006\|batch_073 C006]] | `TsRank(Div(Sub($high,$low), $close), 120)` | C002 60d window ablation — 120d 反向恶化: vol_20d_exp 12.6→21.0 (+66%), alpha_surv 0.99→0.92; frontier window 参数曲线定锚 60d sweet spot |
| [[batches/batch_074/candidates/C001\|batch_074 C001]] | `TsRank(Div($num_trades,$volume), 30)` | F024 atom 30d window ablation — corr=0.914 to F024 hard_gate near_duplicate fail; ic_oos=+0.040 mono OOS=1.00 frontier 强但库重叠 |
| [[batches/batch_074/candidates/C002\|batch_074 C002]] | `TsRank(Div($num_trades,$volume), 45)` | F024 atom 45d window ablation — corr=0.977 to F024 (整批最高); ic_oos=+0.043 强但 entropy 同信号 |
| [[batches/batch_074/candidates/C003\|batch_074 C003]] | `TsRank(Div($num_trades,$volume), 90)` | F024 atom 90d window ablation — corr=0.962 to F024; ic_oos=+0.047 整批最高但 mono 退化 0.90 + style_r² 升 0.064 |
| [[batches/batch_074/candidates/C004\|batch_074 C004]] | `TsRank(Div($num_trades,$circ_market_cap), 60)` | cap 分母重演 b073 C005 frontier 失效 — vol_20d_exp=19.1 + style_r²=0.150 borderline + incr_ic=-0.038 NEG to F022 + mono OOS sign decay |
| [[batches/batch_074/candidates/C005\|batch_074 C005]] | `TsRank(Div($volume,$num_trades), 60)` | F024 reciprocal mirror — corr=-0.957 镜像反号 (mono -1.00 / ic_oos -0.045) + incr_ic=-0.034 NEG; TsRank reciprocal-invariance |
| [[batches/batch_074/candidates/C006\|batch_074 C006]] | `Mul(TsRank($num_trades/$volume,60), CsRank(close-close[5]))` | Mul cross-product F024 wrapper — triple hard_gate fail (sign_flip + oos_decay + mono_flip both >0.5) + alpha_surv collapse 0.07 + incr_ic=-0.023 NEG |

---

## Anti-Recap

- **避免 b072 reject 5 候选** ($num_trades 字段族 raw level / Std / Corr / Mul cross-product 形式)
- **避免 b068-b071 reject 18 候选** (fundamental TTM × daily-aggregate liquidity / rank × rank Mul / Python OLS residualize / TTM signed signal)
- **避免 b073 全 5 reject + b074 全 6 reject** — frontier scope 测绘完成
- **不重做 b072 C006 itself** — 不重 `Div($amount, $num_trades)`
- **不重做 b073 C001/C002/C003/C005/C006** — frontier 真生效 atom 类型律已锚定
- **不重做 b074 C001/C002/C003/C005/C006** — F024 atom × window ablation + reciprocal mirror + Mul wrapper 全部 reject
- **红线**: raw `$num_trades` cross-section level 是 size co-linearity 陷阱 (lesson P008/P010) — 必先转 ratio + TsRank ≥60d 形式
- **新红线 (round 74)**: 不再做 F024 atom × window 单变量 ablation；不再做 cap 分母 dim-less count ratio (vol_20d 嵌入残留)；不再做 Mul(F admitted, F admitted) cross-product (alpha_surv collapse)

---

## Narrative Log

### batch_073 (round 73, NEW direction 首批)

**核心成果**: F024 trade_density_tsrank_60 admit (C004) — frontier 真度铁证落地, 13 连零 admit streak 终结.

**6 candidates → 1 admit + 5 reject**:
- C004 ⭐ ADMIT — `TsRank(num_trades/volume, 60)`, ic_oos=+0.045 / ls_t=+9.08 / mono=+1.00 / alpha_surv=0.58 / style_r²=0.051 整批最低 / max_corr=0.13 整批最低 / incr_ic=+0.0085 POS — 全 CP green.
- C001/C002/C003/C005/C006 reject — frontier 真生效 atom 类型律 (P012) + window 参数曲线 (P013) + admission 三必要条件 (P014) 跨候 ablation 实证.

**升格候选 (待 Phase 5 consolidation 处理)**:
- **P012 frontier 真生效 atom 类型律**: dimensionless count ratio (counts per share, [0,1] body ratio) → 真生效; 含绝对量纲 → 部分失效.
- **P013 frontier window 参数曲线**: 60d sweet spot, 120d 引入额外 vol_20d 嵌入路径.
- **P014 P011 admission 三必要条件**: alpha_surv ≥ 0.40 + ic_by_year sign-stable + **incr_ic > 0** 三立 (frontier 真生效 ≠ admission).

**direction status**: probing → **active** (首 admit 落地 frontier 真度).

### batch_074 (round 74, continue_direction 续探 hot streak)

**核心成果**: 6/6 reject — F024 已饱和此核心几何空间，三轴 ablation 完成 frontier scope 测绘。direction 状态 active → **saturated**。

**6 candidates → 0 admit + 0 reserve + 6 reject**:
- C001/C002/C003 (window ablation 30/45/90d on F024 atom) — corr to F024 0.914/0.977/0.962 全部 hard_gate near_duplicate fail。ic_oos 单调上升 0.040→0.043→0.047 但 entropy 同信号。**60d 不是 ic_oos 单点最大但综合 mono PERFECT + lowest style_r² + alpha_surv 是 risk-adjusted sweet spot**。
- C004 (cross-atom $num_trades/$circ_market_cap, 60d) — hard_gate pass 但 incr_ic=-0.038 NEG to F022 + mono OOS sign decay -0.30 + vol_20d_exp 19.1 偏高 + style_r²=0.150 borderline。重演 b073 C005 cap-denominator frontier 失效模式。
- C005 (mirror atom $volume/$num_trades, 60d) — corr=-0.957 镜像反号几乎完全等价 F024 + incr_ic=-0.034 NEG。
- C006 (Mul(F024_atom, CsRank short-momentum)) — triple hard_gate fail (sign_flip + oos_decay + mono_flip) + alpha_surv collapse 0.07 + incr_ic=-0.023 NEG。Mul cross-product wrapper 在 csi1000 daily 第 5+ 次失败。

**升格候选 (待 Phase 5 consolidation 处理)**:
- **P015**: TsRank rolling-window auto-correlation — 同 atom 在 ±2x window-ratio 内 corr ≥0.91; window 单变量 ablation 不是 library expansion 路径。
- **P016**: dim-less count ratio frontier scope — 仅当 ratio 两端都是 microstructure-only 字段 (volume, num_trades) 时 frontier 真生效; cap 分母 触发 vol_20d 嵌入残留 (b073 C005 + b074 C004 双实证)。
- **P017**: TsRank rolling rank reciprocal invariance — corr(TsRank(x,n), -TsRank(1/x,n)) ≥0.95; mirror atom 不是 library expansion 路径。
- **P018**: Mul cross-product wrapper 在 csi1000 daily 普遍失败几何 (b070-b074 5+ 次实证) — F admitted × F admitted 类型 alpha_surv collapse + sign instability。
- **P013 修正**: frontier window 60d sweet spot 不是 ic_oos 单点最大 (90d 高 0.002) 而是 risk-adjusted 综合最优。

**direction status**: active → **saturated** (核心 atom × window 几何已 admit 占领, 三轴 ablation 完成 frontier scope 测绘)。

**unexplored 路径** (留给 Phase 5 / 跨方向):
1. higher-moment LHS on count ratio (Std/Skew(num_trades/volume, n)) — 需先验证不触发 higher-moment trap。
2. cross-direction residualize F024 残差 in another direction — 需 Python tooling。
3. minute-bar 数据接入后的 intraday count-ratio frontier。
