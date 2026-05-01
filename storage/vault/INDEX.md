---
generated_at: 2026-05-01T18:29:09Z
round: 70
total_active_directions: 14
total_factors_admitted: 23
last_batch: batch_069
last_consolidation_round: null
---

# 🗺️ Factor Research Index

> [!info] MOC · Map of Content
> 路口页。人看下方 Bases 三表；**LLM 启动读此文件顶部 Cockpit 块**（派生状态 + 下一步指令）；拿数据用 `PYTHONPATH=src python3 -m research memory snapshot`。

<!-- BEGIN COCKPIT -->

> [!note]+ 🧭 LLM Cockpit
> **状态** · round=**70** · phase=`null` (idle) · no batch in flight
> **上一批** · [[batches/batch_069/judge|batch_069]] → [[directions/pit_valuation_pure]] · admit=**0**/6 (reserve=1, reject=5) · direction.status=`probing`
> **健康** · rounds_since_consolidation=**1** · active_directions=**14** · zero-admit streak=**10**
> **⚠️ 预警** · 空 factor.md: F017.backtest
>
> **🎯 下一步（按优先级）**
> 1. ⚠️ **修空报告**：F017.backtest 的 `.md` 为空或缺 H1 → 对每个 F{id} 重新 dispatch `/factor-report` subagent
> 2. 🧪 **阈值校准**：连续 10 批零 admit → 先按 `lessons.md#Threshold Calibration` 扫 reserve 候选识别错杀；确认有库空间独立错杀 → 调阈；否则继续
> 3. 🧭 **硬性前置**：`research doctor`（drift 检测）→ `snapshot`（数据）→ 读目标 `directions/{tag}.md` → 进 `/factor-idea`

<!-- END COCKPIT -->

<!-- BEGIN HOT-TOPICS-LLM -->
> [!danger]+ 🆕 系统级事件 · Phase 5 round 69 consolidation (2026-05-02)
> b068 fundamental_quality_carry first-batch all-reject 揭示 **TTM × OHLCV 隐藏 vol_20d 路径**（cockpit round=68 假设 fundamental TTM 是新 frontier 部分被证伪）；3 条 lesson 升格 + 方向 archived；OHLCV daily 饱和叠加首批 fundamental DSL-naive 失败后，下一步 productive frontier 转向**Python 包装**路径。
> - ✅ **3 lessons 升格**：(1) `Forbidden Patterns` "TTM-quality / daily-aggregate-liquidity ratio default-skip"；(2) `Path Selection` "TTM × TTM DSL Sub/Mul/Div 数据契约失败"；(3) `Forbidden Patterns` Higher-moment regime sign-flip 第 4 类 atom (signed fundamental cross-product)
> - ⚪ **fundamental_quality_carry archived**（dead → archived，元教训升格条件满足）
> - 📌 **下一步 frontier**（library_gap finding 提议 3 条）：`python_ttm_residual_quality`（Python OLS residualize TTM quality on size+vol_20d）/ `ttm_intra_field_interaction`（TTM × TTM Python 包装，避开 daily liquidity）/ `pit_valuation_pure`（PIT level dividend_yield/pcf/peg，自带 Barra value basis 抗衡 vol_20d）
> - **calibration verdict**：当前 zero_admit_streak=9 是真实 alpha 饱和（vol_20d + anchor cluster + algebraic mirror 三重锁），**不是阈值过严**——trigger #1-#5 全部不立，绝不放宽 hard_gate。详见 [[_consolidation/findings/calibration/004]]

> [!warning]+ 🔥 Hot Topics（LLM 维护 · 2026-05-02 scan recent=10, round 69 refresh）
> - 🟠 **P004 vol_20d 结构性吸收 ≥10 direction 全覆盖 + 跨字段族首例（fundamental TTM via daily-liquidity denominator 隐藏路径）** · dirs: range_structure, overnight_intraday_split, ohlc_temporal_aggregation, gap_acceptance_structure, value_liquidity_interaction, intraday_price_formation, barra_residual_alpha, microstructure_illiquidity, vwap_proxy_signals, **fundamental_quality_carry (新增)** → b068 C005 (gross_margin/Mean(turnover,20)) vol_20d_exp=**31.1 整库历史最高** + C001 (ROE/Mean(amount,20)) vol_20d_exp=23.4 — `Mean($amount,N)` / `Mean($turnover_rate,N)` 作 denominator 时本身嵌入 vol_20d，把 numerator (即使 fundamental TTM 几何独立) 拉进 vol_20d basis；F002 admit 是 PB Barra value basis 抗衡 vol_20d 的**特例**，ROE/ROA/margin/ROIC/growth 没有同等 Barra basis 抗衡能力。**逃离正路径**：(a) numerator ∈ {pe/pb/ps/dividend_yield 已 Barra basis 字段}；(b) Python OLS residualize on (size, vol_20d)；(c) TTM × TTM 完全去除 daily liquidity (Python 包装)
>   evidence: [[batches/batch_068/judge|batch_068]], [[_consolidation/findings/pattern_analyst/007]], [[lessons#Forbidden Patterns]]
> - 🆕 **P007 fundamental DSL semantics 数据契约层失败族 + signed fundamental cross-product P003 第 4 类 atom** · dirs: fundamental_quality_carry (archived), fundamental_momentum, asymmetric_momentum → b068 C003 `Sub($eps_ttm, $ocf_per_share_ttm)` 全 NaN compute_error（ref_financials TTM per-share 字段 sparse + DSL Sub 不容错复合，跨字段 NaN intersection ~40%）+ C004 `Mul($growth_TTM, Div(1, $pe))` GARP train +0.0019 / val -0.004 sign_flip + decay -2.145（P003 横向扩展第 4 类 atom: signed fundamental cross-product）。**Generator pre-check**：顶层 ∈ {Sub, Mul, Div} + 两端 atom 都 ∈ TTM_PER_SHARE_SET → DSL 不可行硬阻断；signed cross-product 跨 TTM × valuation 默认 regime drift
>   evidence: [[batches/batch_068/judge|batch_068]], [[_consolidation/findings/pattern_analyst/008]], [[_consolidation/findings/pattern_analyst/009]], [[lessons#Path Selection]]
> - 🔴 **P001 rank-diff geometry 范式边界进一步收窄 + close-position/cross-ratio atom 也归入死区** · dirs: value_liquidity_interaction, intraday_price_formation, barra_residual_alpha, vwap_proxy_signals, range_structure, overnight_intraday_split, gap_acceptance_structure → 连续累计 0-admit batches: b052/b053/b054/b056/b057 + b060/b061/b062；overnight_intraday_split close-position atom 与 gap_acceptance cross-ratio atom 4 代几何变体全失败 (T012 EXHAUSTED + T007 DISPROVEN)；新设计须验证 (a) LHS atom 不与已 admit rank-diff 因子同源 (b) RHS basis 不在饱和 endpoints (amount/turnover/overnight/body_ratio_20/H-L_60/price_vol_20/Amihud_20+其窗口家族 + F017 anchor 已泛化至任意 turnover-family RHS) (c) LHS atom 自身需 vol_20d 正交
>   evidence: [[batches/batch_060/judge|batch_060]], [[batches/batch_062/judge|batch_062]]
> - 🔴 **P003 higher-moment LHS regime sign-flip 三种失败模式补全 + atom-orthogonality 三件套** · dirs: vwap_proxy_signals, microstructure_illiquidity, gap_acceptance_structure, range_structure → 跨 b061/b062 新增 sign-flip + mono cross-sample reversal + regime-stable persistent loss 三种模式；**升格条件三件套**：atom 须 (a) multi-regime stable (b) 与单日 \|return\|/range 几何正交 (c) normalizer 不引入 regime drift。F019/F020 满足三件
>   evidence: [[batches/batch_061/judge|batch_061]], [[batches/batch_062/judge|batch_062]]
> - 🟠 **P005 F017 anchor cluster 占位律泛化 + RHS turnover-family 整体锁死** · dirs: microstructure_illiquidity, overnight_intraday_split, range_structure → b061 atp atom × turnover-family RHS 4/6 候选 max_corr 0.51-0.60@F017 — F017 anchor 占据任意 amount/volume-derived LHS × turnover-family RHS 几何位置；F021 (H/L_60) 同律。新设计 RHS 须脱 turnover/H-L_60 全 family
>   evidence: [[batches/batch_058/judge|batch_058]], [[batches/batch_061/judge|batch_061]]
> - 🔴 **P006 strong-mono+strong-ls_t but library-reducer 陷阱第 7 次复现 → 跨 family 通用化** · dirs: range_structure, microstructure_illiquidity, gap_acceptance_structure → 7 次独立案例 (b042 C005 / b043 C005-C006 / b045 C006 / b055 C002 / b056 C004 / b061 C005 / b062 C005) 跨 4 大 family 独立证实；hard_gate `library_reducer_hard_block` 已 codify (mono≥0.85 + |ls_t|≥2.5 + incr_ic≤-0.005 + alpha_surv≤0.30)
>   evidence: [[batches/batch_061/judge|batch_061]], [[batches/batch_062/judge|batch_062]]
<!-- END HOT-TOPICS-LLM -->

## 🎯 方向总览 (Bases)

![[_bases/directions.base]]

## 📚 因子库 (Bases)

![[_bases/factors.base]]

## 📊 最近 Batch (Bases)

![[_bases/recent_batches.base]]

---

> [!abstract]- 系统状态
> - Round: **70** · Admitted: **23** · Active directions: **14**
> - Last batch: **batch_069**
> - Last consolidation: **—**
> - 格式 audit：运行 `research audit index` 检查漂移
