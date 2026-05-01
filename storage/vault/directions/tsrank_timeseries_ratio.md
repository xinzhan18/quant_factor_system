---
direction_tag: tsrank_timeseries_ratio
status: active
priority: high
rounds: 2
admits: 2
last_batch: batch_073
last_admits:
- F024
last_goal: '首批 6 候选验证 lessons P008 frontier — TsRank window≥60d on ratio fields 是新
  vol_20d-escape 路径

  （b072 C006 vol_20d_exp 10.87 + style_r² 0.15 + max_corr 0.24 实证）。把成功几何扩展到其他 ratio
  字段族

  (amount/volume, H-L/C, C-O/H-L, num_trades/volume, turnover/market_cap)；window 60d
  起步，T006 用 120d

  对照。红线：alpha_survival ≥ 0.40 + ic_by_year 后期同号；max_corr<0.30 to library；|corr|>0.3
  to

  $market_cap reject。目标 ≥1 admit 验证 frontier 真度，否则 frontier 单点伪相关，方向 dead。'
last_activity: '2026-05-01T20:52:21Z'
created_batch: batch_073
members:
- F024
retired_members: []
reserves: []
merged_into: null
created_from: cockpit_round_73_frontier_TsRank_window_60d_on_ratio_fields
---
# tsrank_timeseries_ratio

> [!abstract]+ 方向概要
> - **状态**　🟢 `active` (round 73 NEW direction, 首批 admit 1 即验证 frontier 真度) · priority `high` · rounds = 1 · admits = 1
> - **一句话**　基于 lessons P008 frontier — TsRank window≥60d on ratio fields 是新 vol_20d-escape 路径 (b072 C006 实证 vol_20d_exp 65%↓, style_r² 75%↓). b073 C004 trade_density TsRank60 全 CP green admit 完整证实 frontier 真度.
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

---

## Known Failures

| Candidate | Expression | Reason |
|---|---|---|
| [[batches/batch_073/candidates/C001\|batch_073 C001]] | `TsRank(Div($amount, $volume), 60)` | alpha_surv=0.24 FAIL + style_r²=0.49 (poor) + dom=vol_20d 三立 — VWAP proxy ratio 含绝对价格量纲, frontier 失效首例 |
| [[batches/batch_073/candidates/C002\|batch_073 C002]] | `TsRank(Div(Sub($high,$low), $close), 60)` | frontier 真生效 (alpha_surv=0.99 + style_r²=0.13) 但 incr_ic=-0.034 strong NEG library reducer; F022 已复合预测 |
| [[batches/batch_073/candidates/C003\|batch_073 C003]] | `TsRank(Div(Sub($close,$open), Sub($high,$low)), 60)` | alpha_surv=1.14 整批最清洁 frontier 强证实, 但 max_corr=0.37@F008 同 candlestick 几何 + incr_ic=-0.032 + ic_2015 +0.017 anomaly 三立阻断 |
| [[batches/batch_073/candidates/C005\|batch_073 C005]] | `TsRank(Div($turnover_rate, $market_cap), 60)` | alpha_surv=0.91 PASS 但 ratio 含 market_cap 分母 → vol_20d_exp=17.4 偏高 + max_corr=0.38@F022 + incr_ic=-0.036 strong NEG library reducer |
| [[batches/batch_073/candidates/C006\|batch_073 C006]] | `TsRank(Div(Sub($high,$low), $close), 120)` | C002 60d window ablation — 120d 反向恶化: vol_20d_exp 12.6→21.0 (+66%), alpha_surv 0.99→0.92; frontier window 参数曲线定锚 60d sweet spot |

---

## Anti-Recap

- **避免 b072 reject 5 候选** ($num_trades 字段族 raw level / Std / Corr / Mul cross-product 形式)
- **避免 b068-b071 reject 18 候选** (fundamental TTM × daily-aggregate liquidity / rank × rank Mul / Python OLS residualize / TTM signed signal)
- **不重做 b072 C006 itself** — 本批所有 atom 都换字段, 不重 `Div($amount, $num_trades)`
- **不重做 C001/C002/C003/C005/C006 已 reject** — frontier 真生效 atom 类型律已锚定
- **红线**: raw `$num_trades` cross-section level 是 size co-linearity 陷阱 (lesson P008/P010) — 必先转 ratio + TsRank ≥60d 形式

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
