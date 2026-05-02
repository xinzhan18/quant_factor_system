---
direction_tag: cov_ratio_long_window
status: archived
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
status_change_reason: b079 6/6 reject 首批反向证伪 + hypothesis_promoter/011 跨 3 dead 方向
  (b039 pv_covariance / b075 cov_microstructure_valuation / b079 cov_ratio_long_window)
  升格归档. Cov/Corr 长窗口协动 family 在 csi1000 daily 上系统性走 vol_20d basis (P018 + P018 边界扩展);
  TsRank-Corr 双重包裹仍不破 ic 强度天花板 ~0.006-0.007. 三律升格至 lessons.md (P018 扩展 / P019 数据契约
  / P008 适用边界). 唯一火种 C005 已升格至 P004 alpha_surv-OOS-strength 解耦律. 后续探索改走
  long_horizon_alpha_eval 新方向 (library_gap/012) 在 h>1d 上复活 firepit.
---
# cov_ratio_long_window

> [!abstract]+ 方向概要
> - **状态**　🪦 `archived` (round 79 首批反向证伪 + b075/b039 同律 dead 方向 cluster 升格归档) · priority `low` · rounds = 2 · admits = 0
> - **最近**　[[batches/batch_079/judge|batch_079]] · 2026-05-02 · 0/0/6（首批即方向证伪）
> - **一句话**　TsRank≥60d 包裹 Cov/Corr long-window 协动 family 在 csi1000 daily 上 alpha 真饱和 — 60d 几何独立 alpha_surv PASS 但 ic 强度天花板 ~0.006; 120d 信号完全 collapse; TTM single-atom baseline 也 sign_flip + ic sub-threshold; 与 b075 raw-Cov dead 方向 + b039 return-side Cov dead 方向形成 3-cluster 共封 long-window 协动 family.
> - **来源**　orchestrator round 79 dispatch — frontier #2 库内 admit=0 + Phase 5 round 73 P008 (TsRank window≥60d on ratio fields = vol_20d-escape) + 16 untouched fundamental fields (peg_ratio_ttm / pcf_ratio_total_ttm / etc).

> [!failure] ⚠️ HYPOTHESIS 完全证伪 + 方向归档 (b079 + hypothesis_promoter/011)
> 原假设三层 (TsRank-Corr wrap 救 P018 raw Cov form / 60d-120d 长窗协动 / TTM single-atom baseline) **全证伪**. b079 6/6 reject 首批反向证伪; hypothesis_promoter/011 跨 3 dead 方向 (b039 pv_covariance / b075 cov_microstructure_valuation / b079 本方向) 升格 "Cov/Corr 长窗口协动 family csi1000 daily 真饱和" 元教训 → 方向归档.
>
> **6/6 reject 实测**:
> - **60d TsRank-Corr OHLCV (C003 vol×close / C004 amount×high / C005 num_trades×close)**: 几何独立 max_corr<0.05, alpha_surv 0.53/0.61/1.17 全 PASS 0.40 floor, sign-stable double-NEG, 但 ic_oos 0.004-0.006 全 sub-threshold (<0.008). **60d 协动 daily 1d primary horizon 信噪比天花板 ~0.006-0.007**.
> - **120d TsRank-Corr OHLCV (C006 vol×low,120)**: 信号完全 collapse, train ic≈0 (-0.0008) val ic sign-flip (+0.0011), alpha_surv=4.19 批最高但 ic 无方向. **≥半年级别频率 mismatch daily t+1 alpha**.
> - **TTM single-atom baseline (C001 PEG, C002 PCF_total)**: peg_ratio_ttm 9-yr ic_by_year regime 翻转 + sign_flip; pcf_ratio_total_ttm TsRank-60 alpha_surv=0.109 + dom=vol_20d 三立 + ic_oos -0.0042.
>
> **3 律升格 (lessons.md)**:
> 1. **P019 数据契约 (新升格)**: Qlib `Corr/Cov(A, B, N)` cross-field start_index 不齐 broadcast crash. **Corr-safe**: {$close, $open, $high, $low, $volume, $amount, $num_trades}. **Corr-unsafe**: 全 PIT valuation / 全 TTM ratio / $turnover_rate. Generator phase1 freeze 应预阻断. (calibration/007 + hypothesis_promoter/012 + pattern_analyst/020 三方独立背书)
> 2. **P018 边界扩展**: TsRank≥60d 外层 + Corr (self-normalize σ) 内层双重防护**仍不破** csi1000 daily long-window 协动 vol_20d basis ic 强度天花板. 形态独立性 ≠ alpha 独立性.
> 3. **P008 适用边界**: TsRank ratio escape 律仅适用于 (a) 短窗 ≤20d 协动 (b) 直接 ratio 字段单原子. **不适用** ≥60d Cov/Corr 内层 / ≥120d 长窗 / TTM ratio baseline.
>
> **唯一保留火种**: C005 `TsRank(Corr($num_trades, $close, 60), 60)` alpha_surv=1.165 GREEN + max_corr=0.047 + sign-stable double-NEG, ic_oos=-0.0040 弱 — 升格 P004 alpha_surv-OOS-strength 解耦律第 N 个独立证据. 复活路径转交 [[directions/long_horizon_alpha_eval]] (library_gap/012 提议) 在 h={5,10,20} 重测.

---

## Hypothesis (DISPROVEN — preserved as anti-pattern record)

**原核心几何**: `TsRank(Corr(liquidity_proxy, valuation_or_quality_ratio, ≥60d), 60)` — 内层 60-120d 窗口捕协动方向, 外层 TsRank 把 cross-section level 替换为个股自身时序分位.

**原 alpha 独立性主张** (全证伪):
1. ⚠️ ~~Corr (self-normalize σ) + TsRank (时序分位) 双重防护脱 vol_20d basis~~ → 60d 子族 alpha_surv PASS 但 ic 强度仍被 vol_20d 天花板锁死 ~0.006.
2. ⚠️ ~~长窗口 (≥60d) 协动信号与 csi1000 reversal 簇 (F001/F009/F012) 几何分离~~ → 几何独立成立 (max_corr<0.05) 但 alpha 独立性不成立, dom=vol_20d 三立.
3. ⚠️ ~~16 untouched TTM 字段 (peg/pcf_total/dividend_yield) 独立携带 cross-section alpha~~ → C001/C002 baseline 即 sign_flip + ic sub-threshold, csi1000 daily TTM 真饱和扩展至 single-atom baseline.

**已封闭红线** (后续 generator 应预阻断):
- 任何 `Corr/Cov(A, B, N)` N≥60d default-skip (P018 边界扩展)
- 任何 `Corr/Cov(safe_field, unsafe_field, N)` 候选 phase1 freeze 硬阻断 (P019 数据契约)
- 任何 ≥120d 长窗协动候选 daily 1d horizon default-skip (P008 适用边界)

**复活路径** (转交其他方向):
- (a) 短窗 ≤20d 协动 → 已在 [[directions/pv_covariance]] b039 反转簇撞死, 不再开放
- (b) 长 horizon h>1d 评估 → [[directions/long_horizon_alpha_eval]] (library_gap/012 提议, 含 b075 C006 / b079 C005 retro retest)
- (c) Python NaN-aware Corr wrapper 绕过 P019 → [[directions/python_corr_nan_aware]] (library_gap/014 提议, 但 P018 vol_20d basis 律下大概率仍 reject)

---

## Threads (all DISPROVEN — kept compact for archival)

### T001 — Untouched fundamental TTM baseline `[✗ DISPROVEN batch_079]`
**Q**: peg_ratio_ttm / pcf_ratio_total_ttm 在最纯 CsRank/TsRank-60 baseline 形式上是否独立携带 alpha?
**A**: 否. C001 CsRank($peg_ratio_ttm) sign_flip + 9-yr regime drift; C002 TsRank($pcf_ratio_total_ttm, 60) alpha_surv=0.109 + dom=vol_20d + ic_oos=-0.0042. csi1000 daily TTM fundamental 真饱和扩展至 single-atom baseline.
**Evidence**: [[batches/batch_079/candidates/C001|C001]] / [[batches/batch_079/candidates/C002|C002]].

### T002 — TsRank-Corr 60d wrap `[✗ DISPROVEN batch_079]`
**Q**: `TsRank(Corr(liquidity, valuation_ratio, ≥60d), 60)` 是否同时满足 (a) 协动语义保留 (b) vol_20d-escape (c) max_corr<0.40?
**A**: 几何独立 + alpha_surv PASS, **ic 强度不达 + dom=vol_20d 残留**. P019 阻断设计阶段 PIT/TTM RHS frontier; OHLCV-only 退路 C003/C004/C005 ic_oos 0.004-0.006 全 sub-threshold. 60d daily 1d horizon 信噪比上限 ~0.006-0.007. 升格 P018 边界扩展 + P004 解耦律火种.
**Evidence**: [[batches/batch_079/candidates/C003|C003]] / [[batches/batch_079/candidates/C004|C004]] / [[batches/batch_079/candidates/C005|C005]].

### T003 — TsRank-Corr 120d wrap `[✗ DISPROVEN batch_079]`
**Q**: 120d 窗口是否提供更稳协动 + 不被 sparse coverage 击穿?
**A**: 完全 collapse. C006 train ic=-0.0008 / val ic=+0.0011 sign-flip, alpha_surv=4.19 批最高但 ic 无方向. ≥半年级别频率 mismatch daily t+1 alpha. 升格 P008 适用边界.
**Evidence**: [[batches/batch_079/candidates/C006|C006]].

---

## Known Failures

| 失败模式 | 候选 | 关键指标 | 升格 |
|---|---|---|---|
| CsRank TTM baseline (PEG) | C001 | sign_flip + 9-yr regime drift | macro lesson 扩展 |
| TsRank-60 TTM baseline (PCF_total) | C002 | alpha_surv=0.11 dom=vol_20d ic<0.008 | macro lesson 扩展 |
| 60d TsRank-Corr OHLCV (vol×close) | C003 | ic_oos=-0.006 alpha_surv=0.53 dom=vol_20d | P018 边界扩展 |
| 60d TsRank-Corr OHLCV (amount×high) | C004 | ic_oos=-0.006 alpha_surv=0.61 dom=vol_20d | P018 边界扩展 |
| 60d TsRank-Corr OHLCV (num_trades×close) | C005 | ic_oos=-0.004 alpha_surv=1.17 GREEN | P004 解耦律 火种 |
| 120d TsRank-Corr OHLCV (vol×low) | C006 | sign_flip alpha_surv=4.19 ic collapse | P008 适用边界 |
| Corr cross-field broadcast crash | (设计阶段 5/6 候选) | start_index 不齐 | P019 数据契约 |

---

## Related

- [[directions/cov_microstructure_valuation]] — 🪦 archived (b075 6/6 reject); raw `Cov(.,.,N)` form 同律 dead, 与本方向同 cluster 升格归档
- [[directions/pv_covariance]] — 🪦 archived (b039 6/6 reject); return-side Cov 撞反转簇, 与本方向 + cov_microstructure_valuation 形成 3-cluster 共封 long-window 协动 family
- [[directions/long_horizon_alpha_eval]] — 🆕 proposed (library_gap/012); h>1d 评估基础设施新方向, 复活 b079 C005 + b075 C006 firepit
- [[directions/python_corr_nan_aware]] — 🆕 proposed (library_gap/014); Python NaN-aware Corr wrapper 绕过 P019, 但 P018 律下 alpha 大概率仍饱和
- [[directions/tsrank_timeseries_ratio]] — 🟡 saturated; F024 trade_density_tsrank_60 admit (RHS=avg_trade_size 非协动)
- [[directions/tsrank_candlestick_ratio]] — ⚪ active; F025 admit (TsRank 包裹路径但 RHS=candle ratio)
- [[directions/pit_valuation_pure]] — 🟡 saturated; b069 C006 yield × 1/PB reserve 火种

---

## Narrative Log

> [!quote]+ Round 79 / [[batches/batch_079/judge|batch_079]] (2026-05-02) — orchestrator dispatch, NEW direction 首批 → DEAD → ARCHIVED
>
> **Goal**: TsRank≥60d 包裹 long-window Corr 在 liquidity × valuation/quality TTM ratio 是否提供独立 alpha + 补 16 untouched TTM baseline.
>
> **结果**: 6/6 reject 首批反向证伪. P018 raw Cov vol_20d basis 律 + P008 TsRank ratio escape 律两律组合**不破** csi1000 daily long-window 协动 family alpha 饱和. P019 数据契约 + P018 边界扩展 + P008 适用边界三律升格. C005 alpha_surv=1.165 + max_corr=0.047 + sign-stable + ic_oos=-0.0040 = P004 解耦律 N 次独立证据.
>
> **状态轨迹**: probing → dead (post-b079) → archived (post hypothesis_promoter/011 跨方向升格).

> [!quote]+ Phase 5 distillation (2026-05-02) — hypothesis_promoter/011 跨 3 dead 方向归档升格
>
> b039 pv_covariance (return-side Cov 撞反转簇) + b075 cov_microstructure_valuation (raw Cov(.,.,N) vol_20d basis) + b079 本方向 (TsRank-Corr 双重包裹仍不破 ic 天花板) 三路径独立证伪 csi1000 daily long-window 协动 alpha. 升格 lessons.md `## Structural Constraints` 段 vol_20d 律协动算子专项扩展. 本方向 dead → archived, 经验完全升格至 lessons, 不再单独开 batch.
