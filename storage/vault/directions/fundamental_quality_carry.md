---
direction_tag: fundamental_quality_carry
status: dead
priority: low
rounds: 1
admits: 0
last_batch: batch_068
last_admits: []
last_goal: 首批 6 候选探索 TTM quality LEVEL × 价量 / institutional-flow proxy / Sloan accruals
  / GARP，绕开 OHLCV 饱和与 rate-form 失败律。目标 ≥1 admit 验证 fundamental level frontier 仍有 alpha。
last_activity: '2026-05-01T17:40:07Z'
created_batch: batch_068
members: []
retired_members: []
merged_into: null
---
# fundamental_quality_carry

> [!abstract]+ 方向概要
> - **状态**　🔴 `dead` · priority `low` · rounds = 1 · admits = 0
> - **最近**　[[batches/batch_068/judge|batch_068]] · 2026-05-02 · admit=0 / reserve=0 / reject=6
> - **一句话**　TTM quality × daily liquidity ratio 默认被 vol_20d 吸收（daily-aggregate liquidity denominator 是隐藏 vol_20d 路径）；first-batch dead，4 thread 全 disproven。

---

## Hypothesis

> [!warning]+ ⚠️ Hypothesis 已证伪（batch_068，6/6 reject；first-batch dead）
> **原假设**　TTM quality 字段族（ROE/ROA/margin/growth/avg_trade_size）与 OHLCV 几何独立 → quality × liquidity ratio 应携带 cross-section alpha，绕开 vol_20d 吸收律。
>
> **证伪证据**　5/5 PASS-hg 候选**全部** `dominant_style=vol_20d`，C001 vol_20d_exp=23.4 / C005 vol_20d_exp=31.1 整库历史顶级。机理：daily-aggregate liquidity (Mean($amount,20) / Mean($turnover_rate,20)) 作 denominator **本身 cross-section 嵌入 vol_20d**，把 TTM quality numerator 拉进 vol_20d basis。F002 (PB/amount) 之所以 admit 是 PB 自带 value Barra basis 抗衡 vol_20d，ROE/ROA/margin/ROIC 没有同等 Barra basis 对抗能力。
>
> **元教训（待 Phase 5 升格）**　
> 1. **TTM-quality / daily-aggregate-liquidity ratio 默认 vol_20d 吸收**（lessons.md `Forbidden Patterns` 候选）
> 2. **TTM × TTM 直接 Sub/Mul/Div 在 ref_financials sparse 字段需 Python 包装**（C003 retread 警示）
> 3. **Signed fundamental cross-product regime drift in 2022-2023**（C004 sign 翻号是 N+1 次实证）
> 4. **Cockpit "fundamental TTM 与 OHLCV 几何独立"假设需修正**：字段族独立 ≠ cross-section rank 独立；daily-aggregate liquidity 是隐藏的 vol_20d 路径

**经济学逻辑（原假设，已证伪）**：

1. **Quality carry** — 高 ROE / ROA / 高 gross margin 公司有持续的现金流产能，在 A 股 csi1000 上小盘高质量股**长期低估** + earnings drift（散户对 quality 修订反应慢），quality LEVEL 形式（不是 rate）应携带跨截面 alpha。F002（PB/amount level）已证 fundamental level 可用，failure 在于 rate 形式。

2. **Quality × liquidity 交互** — quality 因子单独受 size 共线性吞噬（`|corr|` to `$market_cap` 偏高），但 quality / liquidity 的 ratio 形式（quality per unit turnover）能在控住 size 的同时保留 quality alpha。同 F002 = `Div($pb_ratio, Mean($amount, 20))` 的同源思路。

3. **Institutional flow proxy** — `$amount / $num_trades = avg_trade_size` 是机构资金占比的最直接 daily 代理：单笔大额成交 = 机构主导；散户日 = 高 num_trades + 小 avg_trade_size。机构资金倾向流入 high-quality stocks → quality × institutional_flow 应放大 carry signal。

4. **Sloan-style accruals** — `$eps_ttm - $operating_cash_flow_per_share_ttm` cross-section 反向 = "应计盈余"反映盈余质量低（cash-light earnings）→ 已知 Sloan 异象在中国市场也部分有效。属 quality 子家族但有独立机制（应计 vs 净利润）。

5. **GARP** — `$net_profit_growth_ratio_ttm × Div(1, $pe_ratio)` = growth-at-reasonable-price，把成长 (TTM) 和 valuation reciprocal 乘起来——级别比 PEG 单看更解释 cross-section。

**与 OHLCV 几何独立性**：quality TTM 字段在 cross-section 上**不被 Barra vol_20d 吸收**（不同的 risk factor space），且与 F001-F022 admitted 因子的 OHLCV 形态正交（library 几何上独立）。这是当前最大未探索 frontier（cockpit round=68 confirmed）。

---

## Threads

### T001: quality LEVEL × liquidity 是否携带独立 alpha [✗ DISPROVEN batch_068]

> [!failure]+ Thread 结论
> **Question**: ROE/ROA/gross_margin 这类 TTM quality LEVEL signal，与 amount-based liquidity 形成 ratio / interaction（同 F002 套路），是否能在 csi1000 cross-section 提供超出 size + value Barra style 的增量 IC？
>
> **Answer**: **本形式证伪**。daily-aggregate liquidity denominator 把 TTM quality numerator 拉进 vol_20d basis。
>
> **Evidence trail**:
> - [[batches/batch_068/candidates/C001|batch_068 C001]] ROE/Mean(amount,20) → ic=+0.027 ls_t=1.83 mono=+0.7 vol_20d_exp=**23.4** asr=0.30 incr=+0.0057 → reject (vol_20d 三立 borderline + library reducer)
> - [[batches/batch_068/candidates/C005|batch_068 C005]] gross_margin/Mean(turnover,20) → ic=+0.038 ls_t=2.50 mono=+0.9 vol_20d_exp=**31.1** asr=0.12 incr=-0.0049 → reject (vol_20d 三立完整 + library reducer)
>
> **复活路径**: (a) Python OLS residualize TTM_quality on (size, vol_20d, value); (b) TTM × TTM (避开 daily liquidity); (c) 等 F002 anchor 退役。

### T002: institutional flow proxy 是否构成独立 cross-section signal [✗ DISPROVEN batch_068]

> [!failure]+ Thread 结论
> **Question**: `$amount / $num_trades` = avg_trade_size 作为机构占比代理，cross-section level 是否携带 forward IC？
>
> **Answer**: **DSL 直接版本证伪**。机构资金集中 = 高 vol stocks 双重指向，alpha_survival 仅 0.13 catastrophic。
>
> **Evidence trail**:
> - [[batches/batch_068/candidates/C002|batch_068 C002]] $amount/$num_trades level → ic=-0.076 ls_t=-6.19 mono=-1.0 PERFECT vol_20d_exp=9.75 asr=**0.13** → reject (vol_20d 三立完整 + library reducer)
> - [[batches/batch_068/candidates/C006|batch_068 C006]] ROIC × avg_trade_size → ic=-0.029 ls_t=-3.58 mono=-0.9 vol_20d_exp=8.50 asr=0.16 incr=-0.0001 → reject (vol_20d 三立 + 几乎零 incremental)
>
> **复活路径**: (a) cross-universe 替换 (csi300 vs csi1000); (b) Python residualize on vol; (c) intraday avg_trade_size (需 minute-bar)。

### T003: Sloan accruals proxy 是否在 csi1000 有效 [✗ DISPROVEN batch_068]（数据契约层）

> [!failure]+ Thread 结论
> **Question**: `$eps_ttm - $operating_cash_flow_per_share_ttm` 作为应计盈余近似（accruals），cross-section level 是否携带反向 forward IC？
>
> **Answer**: **DSL 直接 Sub 不可行**。两 TTM per-share 字段 sparse + Sub 不容错 → 全 NaN。信号设计未到 6CP 评估。
>
> **Evidence trail**:
> - [[batches/batch_068/candidates/C003|batch_068 C003]] Sub(eps_ttm, ocf_per_share_ttm) → compute_error all NaN → hard_gate fail
>
> **复活路径**: 必走 Python (cross-section ffill / z-score 包装后再做 Sub 或 (eps-ocf)/|eps+ocf| 标准化形式)。不复活 DSL 直接版本。

### T004: GARP（growth × valuation reciprocal）level 是否优于单独 PEG [✗ DISPROVEN batch_068]

> [!failure]+ Thread 结论
> **Question**: `$net_profit_growth_ratio_ttm * Div(1, $pe_ratio)` cross-section level 是否优于单独 PE 倒数 / 单独 growth？
>
> **Answer**: **regime drift 否决**。growth × (1/pe) 对 2015-2021 成长占优 → 2022-2023 价值回归 regime 切换敏感。
>
> **Evidence trail**:
> - [[batches/batch_068/candidates/C004|batch_068 C004]] growth × (1/pe) → train ic=+0.0019 / val ic=-0.004 sign_flip + ic_too_low + decay -2.145 → reject (hard_gate, P003 第 N 次实证)
>
> **复活路径**: (a) 单独 1/pe (value carry); (b) 单独 growth_ttm + cross-section rank (regime-stable rank)。

---

## Known Failures

- [[batches/batch_068/candidates/C001]] · Div($return_on_equity_ttm, Mean($amount, 20)) → vol_20d 三立 borderline (asr=0.30 + sty_r²=0.40 + dom=vol_20d) + ls_t<2 + library reducer · vol_20d_exp=23.4 整库顶级
- [[batches/batch_068/candidates/C002]] · Div($amount, $num_trades) → vol_20d 三立完整 (asr=0.13 catastrophic) + library reducer (incr_ic=-0.008 NEG, F012 dead zone)
- [[batches/batch_068/candidates/C003]] · Sub($eps_ttm, $operating_cash_flow_per_share_ttm) → compute_error all NaN (TTM per-share Sub DSL 数据契约失败)
- [[batches/batch_068/candidates/C004]] · Mul($net_profit_growth_ratio_ttm, Div(1, $pe_ratio)) → hard_gate (sign_flip + ic_oos_too_low + oos_decay_neg) — fundamental cross-product regime drift
- [[batches/batch_068/candidates/C005]] · Div($gross_profit_margin_ttm, Mean($turnover_rate, 20)) → vol_20d 三立完整 (asr=0.12 catastrophic) + library reducer · vol_20d_exp=31.1 **整库历史最高**
- [[batches/batch_068/candidates/C006]] · Mul($return_on_invested_capital_ttm, Div($amount, $num_trades)) → vol_20d 三立完整 (asr=0.16) + incr_ic≈0 (P006 clean-but-empty)

---

## Related

- ✅ [[factors/F002]] — 对照组 + 模板：PB/amount level ratio admit 范例（同源思路：fundamental LEVEL × liquidity）
- 🔴 [[directions/fundamental_momentum]] `dead` — 警示：rate 形式失败；本方向严格 LEVEL 形式
- 🟡 [[directions/value_liquidity_interaction]] `saturated` — 邻近：已测 PE/PB × turnover；本方向用 TTM quality 字段（ROE/ROA/margins）正交于 PE/PB
- 🟡 [[directions/microstructure_illiquidity]] `saturated` — 邻近：F012/F015/F016 amihud 系列已饱和；本方向 avg_trade_size proxy 与 amihud 几何不同（amihud 是 |return|/$amount，avg_trade_size 是 $amount/$num_trades，分子分母都不同）

---

## Narrative Log

> [!quote]+ 2026-05-02 · [[batches/batch_068/judge|batch_068]] · 方向关闭（first-batch dead）
> **admit=0 / reserve=0 / reject=6**
> - T001/T002/T003/T004 全部 `[✗ DISPROVEN batch_068] → [✗ DISPROVEN]` (NEW direction born-near-disproven)
> - **核心反直觉发现**: TTM quality 字段族在字段层与 OHLCV 几何独立，但 cross-section rank **仍被 vol_20d 吸收**——通过 daily-aggregate liquidity denominator (Mean($amount,20) / Mean($turnover_rate,20)) 这条隐藏路径。C001/C005 vol_20d_exp=23.4/31.1 整库历史顶级。
> - F002 admit 是 PB 自带 value Barra basis 抗衡 vol_20d 的特例；ROE/ROA/margin/ROIC 没有同等 Barra basis。
> - MT budget: 6 tests 全 reject, direction 0→6 ; cumulative 366→372 (临近 high)
> - Direction ops: `exploring → dead`（first-batch dead 律）；priority `high → low`；不进入 retry pool
> - 升格 lessons 候选 (3 条): TTM-quality / daily-liquidity ratio default-skip / TTM × TTM Sub 需 Python / signed fundamental cross-product regime drift
