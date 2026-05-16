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
> - **状态**　🟡 `saturated` (round 74 三轴 ablation 完成 frontier scope 测绘) · priority `medium` · rounds = 4 · admits = 1 (F024)
> - **一句话**　TsRank window≥60d on dim-less microstructure ratio = vol_20d-escape 路径 (P008); F024 (num_trades/volume, 60d) admit; b074 三轴扩展全军覆没 → F024 absorbing prototype 占领 family。
> - **来源**　Phase 5 round 73 升格 P008 frontier; institutional_flow_proxy T001 余烬延展。

---

## Hypothesis

**P008 frontier 升格律 (本方向核心)**: TsRank window≥60d 作用于 dim-less ratio fields → cross-section level 替换为"个股自身分位", 绕过 vol_20d basis ranking 重叠 — csi1000 daily 实证的 vol_20d-escape 路径。

**机理 (TsRank-ratio frontier)**:
1. **核心 atom = ratio** (Div(A, B)): 同量纲 cross-section 抵消 size scale; TsRank 60d 把 level 替换为历史分位 → 脱 vol_20d basis。
2. **window 60d = risk-adjusted sweet spot** (P013 修正): 30d/45d/90d ic_oos 可单调上升, 但 60d 综合 mono PERFECT + lowest style_r² + alpha_surv 最优; 120d 反向恶化 (额外 vol_20d 嵌入)。
3. **frontier 真生效 atom 类型律 (P012/P016)**: 仅当两端都 microstructure-only (volume / num_trades / turnover / amount 互比) 或 [0,1] 无量纲组合时真生效; **cap 分母** ($market_cap / $circ_market_cap / Mean($amount, N)) 触发 vol_20d 嵌入残留 → frontier 失效。
4. **admission 三必要条件 (P014)**: alpha_surv ≥ 0.40 + ic_by_year sign-stable + incr_ic > 0 (frontier 真生效 ≠ admission)。

**⚠️ Saturation warning (finding/019 absorbing-factor 律, HIGH)**: F024 已成 absorbing prototype, 同 family 后续 frontier 续探 max_corr ≥0.91 @ F024。续探必须升级到:
- (a) **Python residualize on F024** (finding/013, DSL 不能表达 → 新方向 `library_residualize_python` 路径) — 唯一可行;
- (b) **cross-family RHS** (microstructure → fundamental basis, 已 saturated);
- (c) **structural transform** (Mean → Std/Skew — 需先验证不触发 higher-moment trap)。

**⛔ 禁忌路径 (P015-P018 / P025-P028 跨 finding 升格)**:
- **mirror atom** (reciprocal $volume/$num_trades): TsRank reciprocal-invariance, corr=-0.957 镜像反号。
- **window 单变量 ablation**: ±2x window-ratio 内 corr ≥0.91 — 不破共线 (P015)。
- **Mul(F_admit_atom_A, F_admit_atom_B) cross-product**: csi1000 daily 5+ 次 alpha_surv collapse / sign_flip / 塌缩 (finding/017)。
- **rank-form 仿射 no-op** (a*x+b under TsRank/CsRank): 数学等价。
- **同 family rhs_change minor revival** (P027/P028): saturation 单调累积, 推迟复活无收益 (finding/016)。
- **cap 分母 dim-less count ratio** (P016): vol_20d 嵌入 (finding/018)。

---

## Threads

### T004 — Trade density 时序分位 `[✓ ANSWERED batch_073]` ⭐ admit, frontier 真度铁证
**Q**: `num_trades/volume` 单笔均量倒数 (retail 主导), TsRank60 retail attention 分位?
**A**: 完整证实。ic_oos=+0.045 / ls_t=+9.08 整库顶级 / mono=+1.00 PERFECT / alpha_surv=0.58 / style_r²=0.051 整批最低 / max_corr=0.13@F001 整批最低 / incr_ic=+0.0085 POS / ic_by_year 2018-2023 全 POS。**dimensionless count ratio (counts per share) frontier sweet spot**。
**Trail**: [[batches/batch_073/candidates/C004|b073 C004]] → **F024 admit**。

### [DISPROVEN] T001/T002/T003/T005/T006 (b073 reject 5)
**T001 VWAP proxy** `TsRank($amount/$volume, 60)`: alpha_surv=0.24 + style_r²=0.49 + dom=vol_20d — 含绝对价格量纲 frontier 失效。
**T002 Normalized range** `TsRank((H-L)/$close, 60)`: frontier 真生效 (alpha_surv=0.99) 但 incr_ic=-0.034 NEG library reducer (F022 复合)。
**T003 Body ratio** `TsRank((C-O)/(H-L), 60)`: frontier 强证实 (alpha_surv=1.14 整批最清洁) 但 max_corr=0.37@F008 + incr_ic=-0.032 三立。
**T005 Turnover/cap** `TsRank($turnover/$market_cap, 60)`: cap 分母 vol_20d_exp=17.4 + incr_ic=-0.036 (P016 实证 #1)。
**T006 Window 120d** `TsRank((H-L)/$close, 120)`: 反向恶化 (vol_20d_exp 12.6→21.0 +66%)。

### [DISPROVEN] T007/T008/T009/T010 (b074 reject 6, 三轴 ablation 全军覆没)
**T007 Window ablation 30/45/90d**: corr to F024 = 0.914 / 0.977 / 0.962 全 hard_gate near_dup; ic_oos 单调上升但同信号; **60d = risk-adjusted 综合最优** (P013 修正, P015 升格)。
**T008 Cross-atom $num_trades/$circ_market_cap**: vol_20d_exp=19.1 + style_r²=0.150 + incr_ic=-0.038 — 重演 b073 C005 cap-denominator 同失败 (P016 升格 #2)。
**T009 Mirror atom $volume/$num_trades**: corr=-0.957 镜像反号 + incr_ic=-0.034 — TsRank reciprocal-invariance (P017)。
**T010 Mul cross-product** `Mul(TsRank($num_trades/$volume,60), CsRank(close-close[5]))`: triple hard_gate fail + alpha_surv=0.068 collapse + incr_ic=-0.023 NEG (P018, finding/017)。

---

## Known Failures

| Candidate | Expression | Reason |
|---|---|---|
| [[batches/batch_073/candidates/C001\|b073 C001]] | `TsRank(Div($amount,$volume), 60)` | alpha_surv=0.24 + style_r²=0.49 + dom=vol_20d — VWAP proxy 含绝对价格量纲 |
| [[batches/batch_073/candidates/C002\|b073 C002]] | `TsRank(Div(Sub($high,$low),$close), 60)` | frontier 真生效但 incr_ic=-0.034 NEG (F022 复合) |
| [[batches/batch_073/candidates/C003\|b073 C003]] | `TsRank(Div(Sub($close,$open),Sub($high,$low)), 60)` | max_corr=0.37@F008 + incr_ic=-0.032 + ic_2015 anomaly |
| [[batches/batch_073/candidates/C005\|b073 C005]] | `TsRank(Div($turnover_rate,$market_cap), 60)` | cap 分母 vol_20d_exp=17.4 (P016 #1) |
| [[batches/batch_073/candidates/C006\|b073 C006]] | `TsRank(Div(Sub($high,$low),$close), 120)` | 120d window 反向恶化 |
| [[batches/batch_074/candidates/C001\|b074 C001]] | `TsRank(Div($num_trades,$volume), 30)` | corr=0.914 to F024 near_dup |
| [[batches/batch_074/candidates/C002\|b074 C002]] | `TsRank(Div($num_trades,$volume), 45)` | corr=0.977 to F024 (整批最高) |
| [[batches/batch_074/candidates/C003\|b074 C003]] | `TsRank(Div($num_trades,$volume), 90)` | corr=0.962 + mono 退化 0.90 |
| [[batches/batch_074/candidates/C004\|b074 C004]] | `TsRank(Div($num_trades,$circ_market_cap), 60)` | cap 分母 vol_20d_exp=19.1 (P016 #2) |
| [[batches/batch_074/candidates/C005\|b074 C005]] | `TsRank(Div($volume,$num_trades), 60)` | reciprocal mirror corr=-0.957 (P017) |
| [[batches/batch_074/candidates/C006\|b074 C006]] | `Mul(TsRank($num_trades/$volume,60), CsRank(close-close[5]))` | Mul triple hard_gate + alpha_surv=0.068 (P018) |

---

## Anti-Recap

- **不重做 b073/b074 全 11 reject** — frontier scope 三轴 ablation 测绘完成
- **不重做 b068-b072 reject 23 候选** (fundamental TTM × daily-aggregate liquidity / rank Mul / Python OLS residualize / TTM signed signal / $num_trades raw level)
- **红线**: raw `$num_trades` cross-section level = size co-linearity 陷阱 — 必先 ratio + TsRank ≥60d
- **红线 (round 74)**: F024 atom × window 单变量 ablation / cap 分母 dim-less count ratio / Mul(F admitted, F admitted) cross-product / mirror atom — 全部默认 skip
- **红线 (跨 finding 升格)**: rank-form 仿射 no-op (a*x+b under TsRank/CsRank); 同 family rhs_change minor revival (P027/P028)
- **唯一可行续探路径**: Python residualize on F024 (新方向 `library_residualize_python`, finding/013 high-severity)

---

## Related findings

- **finding/013 (library_gap, high)**: Library-residualize Python 路径 — F024 absorbing prototype 阻断的 9 跨批候选 (含 b074 C001/C002/C003/C005) 升级路径; 建议新方向 `library_residualize_python`。
- **finding/016 (pattern_analyst, high, P025-P028)**: Library saturation 单调累积律 — minor-path revival 系统性失败; 仅 Python residualize / cross-family / structural transform 值得预算。
- **finding/017 (pattern_analyst, high, P018)**: Mul cross-product wrapper 系统性塌缩律 — F024 wrapper b074 C006 alpha_surv=0.068 collapse 关键证据。
- **finding/018 (pattern_analyst, medium, P016)**: Cap-denominator 隐藏 vol_20d 嵌入路径 — b073 C005 + b074 C004 双实证; P008 frontier 仅适用于两端 microstructure-only 字段。
- **finding/019 (pattern_analyst, high)**: Geometric absorbing-factor 律 — F024 trade-density family 自动成 prototype, 同 family max_corr ≥0.91; 升级 = 高阶 composition 或 Python residualize。

---

## Narrative Log (compressed)

### batch_073 (round 73, NEW direction 首批) — 1 admit + 5 reject
**核心**: F024 trade_density_tsrank_60 admit (C004) 终结 13 连零 admit streak, frontier 真度铁证。同批 5 reject 跨 ablation 实证 P012 (atom 类型律) / P013 (window 60d>120d) / P014 (admission 三必要条件)。
**status**: probing → **active**。

### batch_074 (round 74, continue_direction) — 0 admit + 6 reject
**核心**: 三轴 ablation (window 30/45/90d / cross-atom cap-denominator / mirror atom / Mul cross-product) 全军覆没。F024 已 saturate 核心 atom × window 几何, frontier scope 测绘完成。
**升格律**: P015 (window auto-correlation) / P016 (cap-denominator vol_20d 嵌入) / P017 (TsRank reciprocal-invariance) / P018 (Mul cross-product 塌缩) / P013 修正 (60d risk-adjusted)。
**status**: active → **saturated** (F024 absorbing prototype 占领 family geometry)。

### Unexplored 路径 (cross-direction handoff)
1. **Python residualize on F024** (finding/013 新方向 `library_residualize_python` high-priority, infra 已就位 b071 工艺) — 唯一可行 expansion 路径。
2. **higher-moment LHS on count ratio** (Std/Skew(num_trades/volume, n)) — 需先验证不触发 higher-moment trap。
3. **minute-bar intraday count-ratio frontier** — 数据接入后探。
