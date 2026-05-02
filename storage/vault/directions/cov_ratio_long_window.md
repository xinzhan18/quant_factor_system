---
direction_tag: cov_ratio_long_window
status: dead
priority: low
rounds: 2
admits: 0
last_batch: batch_079
last_admits: []
last_goal: 'Round 79 orchestrator-dispatch NEW direction. Validate TsRank≥60d wrap
  on long-window Corr(liquidity, valuation/quality_ratio) as P008-validated vol_20d-escape
  path for the otherwise-dead Cov(.,.,N) family (P018). 2 baseline candidates fill
  untouched peg_ratio_ttm + pcf_ratio_total_ttm (Step 1.5 律). 4 TsRank-Corr candidates
  probe (a) PE/PCF/dividend_yield/peg yield-basis × turnover/amount/num_trades/volume
  liquidity-basis cross-products (b) 60d vs 120d window selection (c) self-normalized
  inner Corr + outer TsRank time-series quantile dual-protection vs raw Cov vol_20d
  basis. Hard targets: ≥1 admit alpha_surv≥0.40 + ic_oos≥0.008 + max_corr<0.40 + ic_by_year
  2022/2023 sign-stable. Fail → direction dead, escalate lesson ''TsRank wrap insufficient
  for long-window covariation in csi1000 daily fundamental absorption family''.'
last_activity: '2026-05-02T07:46:42Z'
created_batch: batch_079
members: []
retired_members: []
reserves: []
merged_into: null
created_from: cockpit_round_79_orchestrator_dispatch
status_changed_at: '2026-05-02T07:45:00Z'
status_change_reason: b079 6/6 reject 首批反向证伪. TsRank-Corr 60d OHLCV 子族 (C003/C004/C005)
  几何独立 + alpha_surv PASS 但 ic_oos 0.004-0.006 全部 sub-threshold (60d 协动 daily 1d primary
  horizon 信噪比天花板); 120d 子族 (C006) 信号 completely collapse sign_flip; TTM single-atom
  baseline (C001/C002) 也 sign_flip + ic_oos sub-threshold 全 reject. P019 数据契约 (Qlib
  Corr cross-field start_index 不齐) + P018 边界扩展 (TsRank-Corr 包裹也走 vol_20d basis) +
  P008 适用域限定 (仅 daily-ratio 短窗 + 单原子, 不适用 ≥60d Cov/Corr 内层) 三律升格. 唯一保留火种 C005 升格至
  lessons.md alpha_surv-OOS-strength 解耦律.
---
# cov_ratio_long_window

> [!abstract]+ 方向概要
> - **状态**　🔴 `dead` (round 79 首批反向证伪) · priority `low` · rounds = 1 · admits = 0
> - **最近**　[[batches/batch_079/judge|batch_079]] · 2026-05-02 · 0/0/6（首批即方向证伪）
> - **一句话**　TsRank≥60d 包裹 Cov/Corr long-window 协动 family 在 csi1000 daily 上 alpha 真饱和 — 60d 子族几何独立 alpha_surv PASS 但 ic 强度天花板 ~0.006; 120d 信号完全 collapse; TTM single-atom baseline 也 sign_flip + ic sub-threshold; 与邻近 dead `cov_microstructure_valuation` (b075 raw Cov form) 形成 cluster 共封 long-window 协动 family.
> - **来源**　orchestrator round 79 dispatch — frontier #2 库内 admit=0 + Phase 5 round 73 P008 (TsRank window≥60d on ratio fields = vol_20d-escape) + 16 untouched fundamental fields (peg_ratio_ttm / pcf_ratio_total_ttm / etc).

> [!warning] ⚠️ Hypothesis 完全证伪 (batch_079) + P019 数据契约 + P018 边界扩展
> 原假设三层 (TsRank-Corr wrap 救 P018 raw Cov form / 60d-120d 长窗协动 / TTM single-atom baseline) 全证伪.
>
> **6/6 reject 实测**:
> - **60d TsRank-Corr OHLCV 子族 (C003 volume×close, C004 amount×high, C005 num_trades×close)**: 几何独立 max_corr<0.05, alpha_surv 0.53/0.61/1.17 全 PASS 0.40 floor, sign-stable double-NEG, 但 ic_oos magnitude 0.004-0.006 全 sub-threshold (<0.008). **60d 协动 daily 1d primary horizon 信噪比天花板 ~0.006-0.007**.
> - **120d TsRank-Corr OHLCV (C006 volume×low,120)**: 信号 completely collapse, train ic ≈ 0 (-0.0008), val ic sign-flip (+0.0011), alpha_surv=4.19 整批最高但 ic 完全无方向. **120d 协动 ≥半年级别频率 mismatch daily 短期 alpha**.
> - **TTM single-atom baseline (C001 PEG, C002 PCF_total)**: peg_ratio_ttm 9-yr ic_by_year regime 翻转 + sign_flip; pcf_ratio_total_ttm TsRank-60 alpha_surv=0.109 + dom=vol_20d 三立 + ic_oos -0.0042 sub-threshold.
>
> **元教训 (3 律升格)**:
>
> 1. **P019 (数据契约) 升格 candidate**: Qlib Corr cross-field start_index 不齐导致 broadcast crash. **Corr-unsafe 字段集**: 全 PIT valuation (PE/PB/PS/PCF), 全 TTM ratio (peg/pcf_total/dividend_yield), $turnover_rate. **Corr-safe 字段集**: 仅 {$close, $open, $high, $low, $volume, $amount, $num_trades}. Generator 层 phase1 freeze 时建议预阻断 Corr/Cov 候选若两端字段不在 Corr-safe 集.
>
> 2. **P018 (Cov.,.,N vol_20d basis) 边界扩展**: TsRank≥60d 外层包裹 + Corr (self-normalize σ) 内层包裹双重防护**仍不破** csi1000 daily long-window 协动 vol_20d basis 在 ic 强度上的天花板 (~0.006). 60d 几何独立 + alpha_surv PASS 但 ic sub-threshold; 120d 信号 collapse.
>
> 3. **P008 (TsRank window≥60d ratio escape) 适用边界**: P008 律仅适用于 (a) 短窗口协动 (≤20d) 或 (b) 直接 ratio 字段单原子 (b072 C006 / F024 / F025 实证). **不适用于 (c) ≥60d Cov/Corr 内层包裹, (d) ≥120d 长窗, (e) TTM ratio 字段 baseline**. 本批 5 路径独立证伪 P008 应用扩展.
>
> **唯一保留火种**: C005 (`TsRank(Corr($num_trades, $close, 60), 60)`) alpha_surv=1.165 整批最高 GREEN + max_corr=0.047 几何独立 + sign-stable double-NEG, 仅 ic_oos=-0.0040 弱. 不 reserve (hard_gate fail), 升格 lessons.md alpha_surv-OOS-strength 解耦律 (P004 round 73) 第 N 个独立证据.

> [!warning] ⚠️ 直接 raw Cov 路径 P018 已封闭, 本方向必须走 TsRank 包裹 form
> Phase 5 round 73 lessons.md `P018` (cov_microstructure_valuation b075 6/6 reject 实证): **Cov(.,.,N) on csi1000 daily walks vol_20d basis** — 形态独立性 ≠ alpha 独立性. 6 raw `Cov(LHS_microstructure, RHS_valuation, 60-120)` 候选 alpha_surv 0.06-0.30, dom=vol_20d 全立.
>
> **本方向重新定义假设**: 把 long-window 协动信号 (Corr/Cov of liquidity × valuation_ratio over ≥60d) 用 **TsRank ≥60d 包裹** —— P008 lesson 实证 (b072 C006 vol_20d_exp 30.9 → 10.87 降 65%, style_r² 0.59 → 0.15 降 75%) 是当前唯一在 csi1000 daily 验证过的 vol_20d-escape 路径. 复用 Cov 的"协动方向信号"语义但通过 TsRank 把 cross-section level 替换成"个股自身分位", 可能保留 alpha 同时脱 vol_20d basis.
>
> **首批硬目标**: ≥1 候选在 TsRank-Corr 包裹形式上突破 alpha_surv≥0.40 + ic_oos≥0.008 + max_corr<0.40, 验证"协动 alpha 假设" + "TsRank ratio escape" 两律组合可行. 失败 → 方向 dead, 升格 lessons.

---

## Hypothesis

**机理**:

1. **核心几何**: `TsRank(Corr(liquidity_proxy, valuation_or_quality_ratio, ≥60d), 60)` — 内层 60-120d 窗口捕捉协动方向, 外层 TsRank 把 cross-section level 替换为个股自身时序分位.

2. **几何独立性主张** (Step 1.5 baseline + Phase 2 验证):
   - Untouched fundamental fields (peg_ratio_ttm / pcf_ratio_total_ttm / dividend_yield_ttm 在 TsRank 包裹形式) 与 24 admit 全无字段重叠
   - F024 trade_density_tsrank_60 admit 是首例 TsRank 几何, 但 RHS 是 (amount/num_trades), 非协动形态; 几何不重叠
   - 内层 Corr 形式与 raw Cov 区别: Corr 已 self-normalize 量纲 (除以 σ_LHS·σ_RHS), 比 Cov 更不易载入 vol_20d² 量纲

3. **alpha 独立性主张**:
   - P008 实证 vol_20d_exp 降 60-65%, alpha_surv 从 < 0.30 提升到 > 0.40 配合 ic_by_year 后期同号 (P004 校准律)
   - 长窗口 (≥60d) 协动信号语义不同于短窗口 1-20d momentum/volatility — 60-120d 协动方向偏低频, 与 csi1000 reversal 簇 (F001/F009/F012) 几何分离
   - dividend_yield_TTM 是 b069 C006 reserve 火种 (b/p=2.21, sty_r²=0.578) 的 RHS 之一, 但本方向用 TsRank-Corr-60d, 几何形态不同

4. **Baseline-first 律覆盖** (Step 1.5 强制):
   - 16 untouched fields 中 peg_ratio_ttm / pcf_ratio_total_ttm / 多数 quality TTM 字段 0 atom 实验
   - C001 (CsRank peg_ratio_ttm) + C002 (TsRank pcf_ratio_total_ttm 60d) 是纯 baseline, 不做任何 composite, 直接验证字段是否独立 alpha; 失败也提供清晰归因

5. **避开 F073/F074/F075 直接重叠** (cockpit 守则): 实测 vault/factors/ 当前最高 F025, F073-F075 是 cockpit 历史 memory 的 ghost. 本方向无需避开, 但仍走最严格 max_corr<0.40 reserve threshold.

**与 lessons 风险位的对照**:

- **L (P018 Cov.,.,N vol_20d basis)**: 本方向 4/6 候选 (C003-C006) 全部用 TsRank-Corr 包裹, 不用 raw Cov. 内层 Corr 是 normalized covariance, 已脱量纲. 外层 TsRank 时序分位化 strip cross-section 嵌入. 双重防护.
- **L (P008 TsRank window≥60d ratio escape)**: 本方向核心机制. 仅适用于 ratio 字段; 4/6 候选 RHS 是 valuation/yield ratio (PE/PCF/yield) — ratio 形态 PASS.
- **L (alpha_surv 与 sign-stability 解耦, P004 校准律)**: Phase 3 必须 alpha_surv ≥ 0.40 PASS + ic_by_year 后期 (2022/2023) 不翻号 双立才 admit.
- **L (Linear OLS 不破 vol_20d 非线性吸收)**: 本方向不走 Python residualize, 走 DSL TsRank ratio escape (Phase 5 round 73 P008 实证).
- **L (TTM × TTM 数据契约失败)**: 本方向无 TTM × TTM 直接 Sub/Mul/Div; 仅做 Corr(daily_field, TTM_field, ≥60d) 单层, 非 TTM × TTM 嵌套.
- **L (rank-preserving 单算子律)**: 6 候选无 `f(F_admitted)` 形态.
- **L (signed fundamental cross-product regime drift)**: 本方向无 growth × value reciprocal 形态.

**红线**:
- max_corr ≥ 0.40 vs 现有 admit → reserve only (P006 codified)
- alpha_surv < 0.40 + dominant_style=vol_20d + style_r²>0.30 三立 → reject (P004)
- ic_oos < 0.008 → hard_gate fail
- ic_by_year 2022 OR 2023 翻号 → reject 不论 alpha_surv

---

## Current Focus

方向 dead, 无后续 batch 计划. 仅作为反例存档:
- 未来任何 "TsRank-Corr long-window" 候选必须先读本 direction + lessons P018 边界扩展 + P008 适用域限定
- 数据契约 P019 升格至 lessons.md "Available Fields" 段, 注明 Corr-safe / Corr-unsafe 字段集
- C005 升格 lessons.md alpha_surv-OOS-strength 解耦律 (P004 round 73) 第 N 个独立证据

---

## Threads

### T001 — Untouched fundamental TTM baseline `[✗ DISPROVEN batch_079]`
**Question**: peg_ratio_ttm / pcf_ratio_total_ttm 在最纯 CsRank/TsRank-60 baseline 形式上是否独立携带 cross-section alpha?
**Answer**: 否. **C001 CsRank($peg_ratio_ttm)** sign_flip train +0.0021 / val -0.0027 + 9-yr ic_by_year regime drift (2015/2016 NEG → 2017-2020 weak POS → 2022/2023 NEG). **C002 TsRank($pcf_ratio_total_ttm, 60)** alpha_surv=0.109 << 0.40 + dom=vol_20d + ic_oos=-0.0042 sub-threshold (sign-stable 但 magnitude 不达). 16 untouched fundamental TTM 字段中 2 个首测在最纯 baseline 形式即 disprove — confirm csi1000 daily TTM fundamental 真饱和不仅适用 composite (lessons macro), 也适用 single-atom baseline.
**Evidence trail**: [[batches/batch_079/candidates/C001|batch_079 C001]] sign_flip → reject; [[batches/batch_079/candidates/C002|batch_079 C002]] alpha_surv 0.11 + dom=vol_20d → reject.

### T002 — TsRank-Corr long-window pivot `[✗ DISPROVEN batch_079]`
**Question**: `TsRank(Corr(liquidity, valuation_ratio, ≥60d), 60)` 是否同时满足 (a) 协动方向语义保留 (b) vol_20d-escape 通过 (c) max_corr<0.40 几何独立?
**Answer**: **几何独立成立 + alpha_surv PASS, 但 ic 强度不达 + dom=vol_20d 残留**. 数据契约 P019 阻断设计阶段 PIT valuation × liquidity Corr 全 frontier (Qlib start_index 不齐 broadcast crash); OHLCV-only 退路实测: C003 (volume×close) ic_oos=-0.0064 alpha_surv=0.533 / C004 (amount×high) ic_oos=-0.0061 alpha_surv=0.605 / C005 (num_trades×close) ic_oos=-0.0040 alpha_surv=1.165 (批最高). 三候选 sign-stable double-NEG, max_corr<0.05 几何独立, alpha_surv PASS 0.40 floor, 但 ic_oos 0.004-0.006 全 sub-threshold (<0.008 admission). **60d 协动 daily 1d primary horizon 信噪比上限 ~0.006-0.007**. 升格 P018 边界扩展: TsRank-Corr 双重包裹 (Corr self-normalize σ + 外层 TsRank 时序分位) **仍不破**长窗口协动 vol_20d basis 在 ic 强度上的天花板. C005 alpha_surv=1.165 + max_corr=0.047 + sign-stable 但 ic 微弱 — 再次实证 P004 alpha_surv-OOS-strength 解耦律.
**Evidence trail**: [[batches/batch_079/candidates/C003|batch_079 C003]] OHLCV-only 退路 → reject; [[batches/batch_079/candidates/C004|batch_079 C004]] → reject; [[batches/batch_079/candidates/C005|batch_079 C005]] alpha_surv 批最高 但 ic 批最弱 → reject + lessons 升格火种.

### T003 — long-window 120d TsRank-Corr `[✗ DISPROVEN batch_079]`
**Question**: 120d (vs 60d) 窗口在 TsRank-Corr 包裹下是否 (a) 提供更稳协动 (lower-frequency signal) (b) 不被 sparse coverage 击穿?
**Answer**: **完全 collapse**. C006 (`TsRank(Corr($volume, $low, 120), 60)` — TTM RHS 因 P019 数据契约换 OHLCV) train ic=-0.0008 几乎 0, val ic=+0.0011 sign-flip, alpha_surv=4.194 整批最高但 ic 完全无方向, ls_t=-0.22 整批最弱. **120d 长窗口频率 mismatch daily 1d primary horizon**: 长周期协动信号反映 ≥半年级别 macro/sector regime, 与 t+1 daily alpha 时间尺度不符, 信号被 daily reversion noise 淹没. 升格 P008 适用边界限定 "TsRank wrap 不适用于 ≥120d 长窗".
**Evidence trail**: [[batches/batch_079/candidates/C006|batch_079 C006]] sign_flip + signal collapse → reject.

---

## Known Failures

| 失败模式 | 候选 | 关键指标 | 升格 |
|---|---|---|---|
| TsRank-60 baseline TTM ratio (PCF_total) | C002 | alpha_surv=0.11 dom=vol_20d ic_oos<0.008 | macro lesson 扩展 |
| CsRank baseline TTM (PEG) | C001 | sign_flip 9-yr regime drift | macro lesson 扩展 |
| 60d TsRank-Corr OHLCV (volume×close) | C003 | ic_oos=-0.006 alpha_surv=0.53 PASS dom=vol_20d | P018 边界扩展 |
| 60d TsRank-Corr OHLCV (amount×high) | C004 | ic_oos=-0.006 alpha_surv=0.61 PASS dom=vol_20d | P018 边界扩展 |
| 60d TsRank-Corr OHLCV (num_trades×close) | C005 | ic_oos=-0.004 alpha_surv=1.17 GREEN dom=vol_20d | P004 解耦律 升格火种 |
| 120d TsRank-Corr OHLCV (volume×low) | C006 | sign_flip alpha_surv=4.19 ic collapse | P008 适用边界 |
| 数据契约 PIT/TTM/turnover_rate Corr | (设计阶段全) | Qlib start_index 不齐 broadcast crash | P019 升格

---

## Related

- [[directions/cov_microstructure_valuation]] — 🔴 dead (b075 6/6 reject); raw Cov.,.,N 形态封闭, 本方向 TsRank 包裹绕过
- [[directions/tsrank_timeseries_ratio]] — 🟡 saturated; F024 trade_density_tsrank_60 admit 首例 TsRank 几何, RHS=avg_trade_size 非协动
- [[directions/tsrank_candlestick_ratio]] — ⚪ active; F025 admit; 同 TsRank 包裹路径但 RHS=candle ratio
- [[directions/institutional_flow_proxy]] — ⚪ probing (b072 C006 TsRank avg_trade_size 60d reserve 火种, incr_ic=-0.018 阻断); 同 TsRank 几何但 RHS 不同
- [[directions/pit_valuation_pure]] — 🟡 saturated; b069 C006 yield × 1/PB reserve 火种, 本方向不重 PB-anchor

---

## Narrative Log

> [!quote]+ Round 79 / [[batches/batch_079/judge|batch_079]] (2026-05-02) — orchestrator dispatch, NEW direction 首批 → DEAD
>
> **Goal**: 验证 TsRank ≥60d 包裹 long-window Corr 在 liquidity × valuation/quality TTM ratio 上是否提供独立 alpha + 补 16 untouched TTM 字段中 2 个的 baseline.
>
> **结果 (batch_079)**: **6/6 reject** 首批反向证伪. P018 raw Cov form vol_20d basis 律 + P008 TsRank ratio escape 律两律组合 **不破** csi1000 daily long-window 协动 family alpha 饱和. P019 (新, Qlib Corr 数据契约) + P018 边界扩展 + P008 适用边界 三律升格. batch_079 C005 alpha_surv=1.165 + max_corr=0.047 + sign-stable double-NEG + ic_oos=-0.0040 微弱 = P004 alpha_surv-OOS-strength 解耦律 第 N 个独立证据.
>
> **方向状态变更**: probing → dead (post-batch_079).
