---
direction_tag: cov_microstructure_valuation
status: dead
priority: low
rounds: 2
admits: 0
last_batch: batch_075
last_admits: []
last_goal: "Round 75 首批 — NEW direction (library_gap/010 顶上). 假设: Cov(microstructure_LHS,\n\
  valuation_RHS, window>=60d) 是 lessons.md 显式指认的 \"Cov(liquidity, valuation_ratio)\n\
  long-window family\" frontier (round 73 round 73 Phase 5 升格语句). 当前 24 admit 中 0\
  \ 个 Cov 形态;\npv_covariance dead 是因为 RHS=return/body 撞 reversal cluster (F001 amount_cv\
  \ / F009\novernight_spread / F012 amihud), 本批 RHS 是 valuation ratio (PE/PB/PCF/dividend_yield_ttm)\n\
  与 reversal cluster 几何独立. 6 候选探索 LHS×RHS 配对矩阵 + window 选择:\n  (a) Cov($turnover_rate,\
  \ $pe_ratio, 60) — flagship: liquidity × earning yield 60d\n  (b) Cov($turnover_rate,\
  \ $pcf_ratio, 60) — cash-flow yield, 2026-05-01 新字段\n  (c) Cov($num_trades, $pe_ratio,\
  \ 60) — institutional flow proxy × earning yield\n  (d) Cov($num_trades, $pb_ratio,\
  \ 60) — institutional flow × book yield\n  (e) Cov($amount, $pcf_ratio_total_ttm,\
  \ 120) — TTM cash flow, 长窗口, 注意 sparse risk\n  (f) Cov($num_trades, $dividend_yield_ttm,\
  \ 60) — institutional × yield TTM\n红线: max_corr<0.30 to library; alpha_survival>=0.40\
  \ + ic_by_year sign-stable\n(P008 lesson); avoid $market_cap proxy (|corr|<0.3);\
  \ 避开 cap-denominator dim-less\nratio frontier (P016). Anti-recap: 不重 b068-b074 reject\
  \ 候选 (那些是 Div/Mul DSL +\npython residualize, 与 Cov 形态几何不同); 不重 pv_covariance b039\
  \ 失败几何\n(RHS=return/body, 本批 RHS=valuation ratio). 目标: ≥1 admit 验证 Cov family 是新空间;\n\
  否则首批反向证伪 → 方向 dead."
last_activity: '2026-05-01T21:48:49Z'
created_batch: batch_075
members: []
retired_members: []
reserves: []
merged_into: null
created_from: cockpit_round_75_library_gap_010_cov_liquidity_valuation_long_window_family
status_changed_at: '2026-05-02T05:50:00Z'
status_change_reason: b075 6/6 reject 首批反向证伪 — 4 hard_gate-pass 候选 (C001-C004) alpha_surv
  0.06-0.30 全部 << 0.40 default min, dom_vol_20d 全部立 (exposure 5.34-22.06). Cov 形态几何独立
  (max_corr<0.40 to library) 但 alpha 真饱和走 vol_20d basis, 与 b068-b072 fundamental absorption
  同源. C005 (TTM long-window) hard_gate sign_flip + ic_oos<0.008. C006 唯一 risk-clean
  火种 (alpha_surv=1.94) 但 ic 不足 admission. P018 升格候选 — Cov(.,.,N) 在 csi1000 daily 走
  vol_20d basis — 几何独立 ≠ alpha 独立. lessons.md 首批反向证伪 律生效.
---
# cov_microstructure_valuation

> [!abstract]+ 方向概要
> - **状态**　🔴 `dead` (round 75 首批反向证伪) · priority `low` · rounds = 1 · admits = 0
> - **最近**　[[batches/batch_075/judge|batch_075]] · 2026-05-02 · 0/0/6（首批即方向证伪）
> - **一句话**　Cov(microstructure, valuation_level, 60-120d) 几何独立 (max_corr<0.40 to library) 但 alpha 走 vol_20d basis 系统吸收; 与 b068-b072 fundamental absorption 同源, csi1000 daily 频率第 6 形态实证证伪.
> - **来源**　Phase 5 round 73 lessons.md 显式指认 "Cov(liquidity, valuation_ratio) long-window family" frontier + library_gap/010 finding + 2026-05-01 新增字段提供 RHS 基础.

> [!warning] ⚠️ Hypothesis 完全证伪 (batch_075) + P018 升格律
> 原假设：Cov 形态独立性 → alpha 独立性, 在 csi1000 daily 上 microstructure × valuation 协动是新空间.
> 实测：6/6 reject. 4 hard_gate-pass 候选 alpha_surv 0.06-0.30 全部 << 0.40, dom=vol_20d 全部立 (exposure 5.34-22.06), Barra basis 吸收 70-95% alpha. C005 (TTM 120d) hard_gate sign_flip. C006 唯一 risk-clean 火种 (alpha_surv=1.94) 但 ic_oos=0.0015 < 0.008.
> **元教训 (P018 升格)**: **Cov(.,.,N) 时间序列协动形态在 csi1000 daily 上仍走 vol_20d basis** — 形态独立性 ≠ alpha 独立性. Cov = Mean((LHS-Mean) × (RHS-Mean), N), 两去均值偏差项 × N 累积 = 被 vol_20d² 因子主导. 与 b068-b072 fundamental TTM × daily-aggregate absorption 同源, 形成 5+ 形态独立证伪 (cross-section level / Mean / Std / TsRank / Cov) — csi1000 daily 频率 microstructure × valuation 真饱和.
> **唯一火种**: C006 dividend_yield_TTM × num_trades 60d Cov risk-clean (alpha_surv=1.94, 不撞 ep_ratio basis) 但 ic 不足. 升格 lessons.md Path Selection.

---

## Hypothesis (已证伪)

**机理 (Cov-microstructure-valuation frontier)**:

1. **核心几何**: `Cov(LHS_microstructure, RHS_valuation, window=60d 或 120d)` 捕获两序列在 window 日窗口的协动方向. LHS ∈ {$turnover_rate, $num_trades, $amount} (流动性/活跃度), RHS ∈ {$pe_ratio, $pb_ratio, $pcf_ratio, $pcf_ratio_total_ttm, $dividend_yield_ttm} (估值通道).

2. **几何独立性主张** (实测 PASS): 当前 24 admit 全部是 cross-section level / Mean / Std / TsRank 形态, 0 个 Cov(.,.,N) 时间序列协动形态. 实测 max_corr 全部 < 0.40 (C001=0.27, C002=0.22, C003=0.20, C004=0.37, C006=0.287). **形态独立性成立**.

3. **alpha 独立性主张** (实测 FAIL): 4 hard_gate-pass 候选 alpha_surv 0.06-0.30 全部 << 0.40 default min, dominant_style=vol_20d 全部立, vol_20d_exp 5.34-22.06. **alpha 不独立, 走 vol_20d basis**.

4. **与 pv_covariance dead 的边界** (实测无意义): pv_covariance b039 是 RHS=return/body 撞反转簇 reject; 本方向 RHS=valuation level 与反转簇几何独立成立, 但失败机制不同 (反转簇 → vol_20d basis). 两个 Cov 方向独立证伪两条不同 absorption 路径.

5. **新字段红利** (实测无效): $num_trades + $pcf_ratio + $pcf_ratio_total_ttm + $dividend_yield_ttm 在 Cov 形态上未提供新独立 alpha. C006 dividend_yield_TTM 唯一 risk-clean 但 ic 弱.

---

## Current Focus

方向 dead, 无后续 batch 计划. 仅作为反例存档: 未来任何 "Cov(microstructure, valuation_level)" 候选必须先读本 direction 与 P018 升格条目, 明确为何不会再次走 vol_20d basis.

C006 唯一火种保留升格至 lessons.md Path Selection: "dividend_yield_TTM × institutional flow Cov 是 risk-clean 但 daily 1d primary 不达 alpha 阈值; 探索路径需 forward horizon 调整 + Python ffill rescue". 不在本 direction 续探.

---

## Threads

### T001 — Cov(turnover, valuation_level, 60d) `[✗ DISPROVEN batch_075]`
**Question**: $turnover_rate (流通占比) 与 cross-section valuation level (PE/PCF) 协动是否携带独立 forward alpha?
**Answer**: 否. C001 alpha_surv=0.295 + C002 alpha_surv=0.240 双 FAIL < 0.40 默认阈值. mono OOS -0.40 至 -0.90 + ic_by_year 9 年同号 NEG → 信号方向真实但 alpha 70-76% 被 Barra basis 吸收. RHS PE→PCF 替换不脱 vol_20d, 反而引入 ep_ratio basis (PCF: 2.99 vs PE: 1.04 三倍).
**Evidence trail**: [[batches/batch_075/candidates/C001|batch_075 C001]] alpha_surv=0.295 → reject; [[batches/batch_075/candidates/C002|batch_075 C002]] ep_ratio_exp=2.99 → reject.

### T002 — Cov(num_trades, valuation_level, 60d) institutional flow `[✗ DISPROVEN batch_075]`
**Question**: $num_trades (institutional flow proxy) 与 valuation level 协动是否独立于 F012 Amihud + 不撞 size 共线?
**Answer**: 否. C003 alpha_surv=0.152 + C004 alpha_surv=**0.065 整批最低** 双 deep FAIL. **LHS turnover→num_trades 强化 vol_20d 吸收** (5.34/7.85 → 11.21/22.06 翻倍). C004 (PB RHS) vol_20d_exp=22.06 整批最高 + style_r²=0.258 borderline poor — PB Barra book_to_price 直接对应 + size 共线 三立. C006 dividend_yield_TTM 是唯一例外 (alpha_surv=1.94 risk-clean) 但 ic_oos=0.0015 hard_gate fail.
**Evidence trail**: [[batches/batch_075/candidates/C003|batch_075 C003]] vol_20d=11.21 → reject; [[batches/batch_075/candidates/C004|batch_075 C004]] alpha_surv=0.065 整批最低 → reject; [[batches/batch_075/candidates/C006|batch_075 C006]] alpha_surv=1.94 火种 ic 不足 → reject + lessons 升格.

### T003 — Cov(amount, TTM_valuation, 120d) 长窗口 `[✗ DISPROVEN batch_075]`
**Question**: 长窗口 Cov + TTM RHS (sparse) 是否在容忍 NaN 后仍提供 alpha?
**Answer**: 否. C005 hard_gate sign_flip (IS=+0.0006 / val=-0.0012) + ic_oos_too_low (|0.0012|<0.008). 长窗口 + TTM sparse RHS + Cov 不容错 NaN → 信号塌缩 (coverage 0.90 vs 同批 ≥0.999).
**Evidence trail**: [[batches/batch_075/candidates/C005|batch_075 C005]] sign_flip + ic_oos_too_low → reject. lessons L 段 "TTM × TTM DSL 不容错" 律扩展至 Cov(daily, TTM, long_window) 形式.

---

## Known Failures

| Candidate | Expression | Reject Reason |
|---|---|---|
| [[batches/batch_075/candidates/C001\|C001]] | `Cov($turnover_rate, $pe_ratio, 60)` | alpha_surv=0.295 < 0.40 + vol_20d_exp=7.85 dom + Barra basis 吸收 85% |
| [[batches/batch_075/candidates/C002\|C002]] | `Cov($turnover_rate, $pcf_ratio, 60)` | alpha_surv=0.240 << 0.40 + ep_ratio_exp=2.99 强 absorption + mono OOS=-0.40 弱化 |
| [[batches/batch_075/candidates/C003\|C003]] | `Cov($num_trades, $pe_ratio, 60)` | alpha_surv=0.152 deep FAIL + vol_20d_exp=11.21 (LHS num_trades 强化 size 共线) |
| [[batches/batch_075/candidates/C004\|C004]] | `Cov($num_trades, $pb_ratio, 60)` | alpha_surv=0.065 整批最低 + vol_20d_exp=22.06 整批最高 + style_r²=0.258 borderline poor |
| [[batches/batch_075/candidates/C005\|C005]] | `Cov($amount, $pcf_ratio_total_ttm, 120)` | hard_gate sign_flip + ic_oos_too_low (TTM sparse + 长窗口 + Cov 不容错) |
| [[batches/batch_075/candidates/C006\|C006]] | `Cov($num_trades, $dividend_yield_ttm, 60)` | hard_gate ic_oos_too_low (|0.0015|<0.008) — 唯一 risk-clean 火种 (alpha_surv=1.94) 但 ic 不足 |

---

## Narrative Log

### batch_075 (round 75, NEW direction 首批 → dead)

- **2026-05-02** (round 75 首批): 方向首创 → 首批反向证伪 dead. **关键发现**: Cov(microstructure, valuation_level) 几何独立 (max_corr<0.40 to library) 但 alpha 走 vol_20d basis 系统吸收 — 形态独立性 ≠ alpha 独立性. 与 b068-b072 fundamental absorption 同源, 形成 csi1000 daily 频率 microstructure × valuation 真饱和的第 6 形态实证 (cross-section level / Mean / Std / TsRank / Cov). LHS turnover→num_trades 强化 vol_20d 吸收 (P008 raw $num_trades size 共线律一致); RHS PE/PCF/PB 全被 ep_ratio + book_to_price Barra basis 吃掉; dividend_yield_TTM 唯一 risk-clean 但 ic 弱. 升格 P018 候选 + 升格 dividend_yield × institutional_flow Cov risk-clean 火种 to lessons.md Path Selection. 切换全新 direction (OHLC microstructure / intraday signals 未饱和族, 或 Mul(microstructure_admit, OHLC_atom) 不带 valuation RHS).
