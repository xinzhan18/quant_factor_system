---
generated_at: 2026-05-02T15:05:02Z
round: 82
total_active_directions: 23
total_factors_admitted: 25
last_batch: batch_081
last_consolidation_round: null
---

# 🗺️ Factor Research Index

> [!info] MOC · Map of Content
> 路口页。人看下方 Bases 三表；**LLM 启动读此文件顶部 Cockpit 块**（派生状态 + 下一步指令）；拿数据用 `PYTHONPATH=src python3 -m research memory snapshot`。

<!-- BEGIN COCKPIT -->

> [!note]+ 🧭 LLM Cockpit
> **状态** · round=**82** · phase=`null` (idle) · no batch in flight
> **上一批** · [[batches/batch_081/judge|batch_081]] → [[directions/ohlc_temporal_aggregation]] · admit=**0**/6 (reserve=1, reject=5) · direction.status=`saturated`
> **健康** · rounds_since_consolidation=**9** · active_directions=**23** · zero-admit streak=**5**
> **⚠️ 预警** · 空 factor.md: F017.backtest · consolidation 触发: active_directions=23 ≥ 20
>
> **🎯 下一步（按优先级）**
> 1. ⚠️ **修空报告**：F017.backtest 的 `.md` 为空或缺 H1 → 对每个 F{id} 重新 dispatch `/factor-report` subagent
> 2. 📚 **触发 consolidation**：active_directions=23 ≥ 20 → 先调 `/factor-consolidate`，再进 Phase 1
> 3. 🧪 **阈值校准**：连续 5 批零 admit → 先按 `lessons.md#Threshold Calibration` 扫 reserve 候选识别错杀；确认有库空间独立错杀 → 调阈；否则继续
> 4. 🧭 **硬性前置**：`research doctor`（drift 检测）→ `snapshot`（数据）→ 读目标 `directions/{tag}.md` → 进 `/factor-idea`

<!-- END COCKPIT -->

<!-- BEGIN HOT-TOPICS-LLM -->
> [!danger]+ 🆕 系统级事件 · Phase 5 round 73 consolidation (2026-05-02)
> b068-b072 5 批 fundamental escape 全部 0-admit（**5 路径独立证伪**）→ csi1000 daily TTM quality / valuation / institutional flow **alpha 真饱和**（不是阈值过严）；5 lesson 升格 + 2 方向状态变更。下一步 frontier 转 OHLC microstructure / Cov(liquidity, valuation_ratio) long-window family 续探（F073/F074/F075 已 admit Mono_OOS=-1.0 PERFECT，未饱和）。
> - ✅ **5 lessons 升格**：(1) `Path Selection` "alpha_survival ≥ 0.40 必须配 ic_by_year 后期同号 check"（CP02 校准律）；(2) `Path Selection` "Linear OLS residualize 不破 csi1000 vol_20d 非线性吸收"（限定逃离正路径 a 语义边界）；(3) `Path Selection` "TsRank window≥60d on ratio fields 是新 vol_20d-escape 路径"（库内首例 partial-progress）；(4) 新 H3 段 `csi1000 daily fundamental + institutional flow 真饱和`（顶层 macro lesson）；(5) 新 H3 段 `Composition Selection` "rank × rank Mul 需 book yield basis 显化"（b/p≥2 → ls_t≥2 充分但不必要条件）
> - 🟠 **方向状态变更**：pit_valuation_pure probing → **saturated**（C006 reserve 火种保留）；python_ttm_residual_quality probing → **dead**（mechanism dead zone）；institutional_flow_proxy 维持 **probing**（C006 TsRank reserve 火种 incr_ic 边缘）；fundamental_quality_carry 已 round 69 archived（维持）
> - 📌 **下一步 frontier**（library_gap finding 提议 3 条）：`tsrank_timeseries_ratio`（库内 TsRank admit=0 结构性空白，b072 C006 火种支持，medium 优先级）/ `cov_ratio_long_window`（F073/F074/F075 已 admit form 未饱和，dividend_yield × turnover / amount × pe 等变体未探）/ `python_residualize_non_quality`（工艺验证但 numerator 类型未试，需先验 cross-section 独立证据）
> - **calibration verdict**：calibration/005 维持 incr_ic floor=0.005 不放宽（b072 C006 reserve NOT admit via calibration，trigger #1-#4 全不立）；calibration/006 维持 alpha_survival_min=0.40 不变（判据 composition 显化为 lesson 升格，非阈值数字调整）；**绝不放宽 hard_gate**

> [!warning]+ 🔥 Hot Topics（LLM 维护 · 2026-05-02 scan recent=14 findings, round 73 refresh）
> - 🟠 **P004 vol_20d 结构性吸收 ≥11 direction 全覆盖 + Linear OLS 不破非线性吸收（圈定逃离正路径 a 语义边界）** · dirs: range_structure, overnight_intraday_split, ohlc_temporal_aggregation, gap_acceptance_structure, value_liquidity_interaction, intraday_price_formation, barra_residual_alpha, microstructure_illiquidity, vwap_proxy_signals, fundamental_quality_carry, **python_ttm_residual_quality (新增)**, **institutional_flow_proxy (新增)** → b071 5/6 Python OLS residualize on (size, vol_20d, [b/p]) 残差 vol_20d_exp ∈ [11.6, 22.9] 仍 dom 5/6（C001 22.9 / C002 17.3 / C003 11.6 / C004 18.6 / C006 14.4）；alpha_survival 0.93~7.23 全 PASS 但残差仍载 vol_20d 二阶/非线性载荷。**csi1000 cross-section 上 vol_20d basis 是非线性 manifold 不是线性 hyperplane** — Linear OLS 仅 strip 线性 βvol component。**实操**：需要破 vol_20d 吸收时 (a) Python residualize 仅在 numerator 自身 OOS-stable alpha 时生效（不是工艺自动救活）；(b) TsRank 时序 form 量纲化（见 P008）；(c) 切 universe；不试 Polynomial/Kernel OLS 过拟合
>   evidence: [[batches/batch_071/judge|batch_071]], [[_consolidation/findings/pattern_analyst/011]], [[_consolidation/findings/hypothesis_promoter/010]], [[lessons#Path Selection]]
> - 🆕 **P008 TsRank window≥60d on ratio fields 是新 vol_20d-escape 路径（库内 admit=0 结构性新空间）** · dirs: institutional_flow_proxy (probing, C006 reserve), pv_covariance, turnover_structural_signal → b072 C006 `TsRank(avg_trade_size, 60)` vol_20d_exp=10.87 vs C001 Std(20)=26.7（**降 65%**）+ style_r² 0.59 → 0.15（**降 75%**）+ alpha_surv=0.447 PASS + max_corr=0.24@F009 LOW + ls_t=-7.54 整库顶级；唯 incr_ic=-0.018 微 NEG → reserve 火种。机理：时序 60d rank 把 cross-section level 替换为"个股自身分位"，绕过 cross-section vol_20d basis 上的 ranking 重叠，但保留 anomaly direction signal。**前提**：仅适用于 ratio 字段（`$amount/$num_trades` / H/L / `$close/Mean(...)` 等）；alpha_surv ≥ 0.40 必须 PASS。**衍生律**：raw `$num_trades` cross-section level **不构成新几何**（max_corr=0.75@F012 NEAR_DUPLICATE，F012 Amihud 通过 size 共线性已覆盖）；复活路径 Python size-residualize / TsRank 时序 / cross-section rank-diff 配独立 RHS basis
>   evidence: [[batches/batch_072/judge|batch_072]], [[_consolidation/findings/pattern_analyst/010]], [[_consolidation/findings/pattern_analyst/013]], [[_consolidation/findings/library_gap/009]], [[lessons#Path Selection]]
> - 🆕 **P009 alpha_survival ≥ 0.40 与 OOS sign-stability 完全解耦（CP02 判据 composition 校准律）** · dirs: python_ttm_residual_quality (dead), fundamental_quality_carry (archived), pit_valuation_pure (saturated) → b071 6/6 候选 alpha_surv ∈ [0.93, 7.23] 全 PASS 0.40 红线但 6/6 OOS sign_flip（train +α 0.001~0.014 / val -α -0.001~-0.009 全部翻号）；C006 inverse D/A alpha_surv=**7.23** 整批最高，val_ic=-0.0007 仍反号；IC by year (C001) 完整 regime drift profile 2015-2018 强正 → 2019-2021 衰减 → 2022-2023 翻号。**机理**：alpha_surv 仅捕捉"对线性 Barra basis 的剥离"，不预测"OOS sign alive"；csi1000 daily TTM quality 在 2022-2023 regime drift 独立失活（与 vol_20d 吸收**无关**）。**判据 composition 显化**：alpha_surv 不可独立作 admission gate，必须配 `ic_by_year` 后期 (2022/2023) 同号 check；alpha_surv >> 1.0 + ic_by_year 后期翻号 → 默认 reject。当前 sign_flip hard_gate 实际拦截 b071 全部 — 系统正确工作但语义未显化
>   evidence: [[batches/batch_071/judge|batch_071]], [[_consolidation/findings/pattern_analyst/011]], [[_consolidation/findings/calibration/006]], [[lessons#Path Selection]]
> - 🆕 **P010 csi1000 daily fundamental + institutional flow alpha 真饱和（5 路径独立证伪 macro lesson）** · dirs: fundamental_quality_carry (archived), pit_valuation_pure (saturated), python_ttm_residual_quality (dead), institutional_flow_proxy (probing reserve only) → b068-b072 5 批 0-admit；5 独立失败路径：(a) daily-aggregate liquidity ratio 嵌入 vol_20d；(b) PIT valuation rank composite 仅 1/PB book basis 显化（PB→PE/PCF 替换全衰减）；(c) Python OLS residualize TTM quality 6/6 OOS sign_flip（regime drift 独立失活）；(d) TTM aggregate signed signal 全 sign_flip；(e) institutional flow microstructure 几何独立但 forward reversal + incr_ic NEG。**结论**：TTM quality / TTM valuation / institutional flow 在 csi1000 daily-bar 频率上**不存在 OOS-stable cross-section alpha** — alpha 真饱和不是阈值过严。**未探路径仅**：minute/tick 数据 + csi300/500 universe；当前 daily csi1000 暂停此族 frontier 预算
>   evidence: [[batches/batch_068/judge|batch_068]], [[batches/batch_069/judge|batch_069]], [[batches/batch_070/judge|batch_070]], [[batches/batch_071/judge|batch_071]], [[batches/batch_072/judge|batch_072]], [[_consolidation/findings/pattern_analyst/014]], [[_consolidation/findings/hypothesis_promoter/008]], [[lessons#Path Selection]]
> - 🟠 **P005 F017 anchor cluster 占位律泛化 + RHS turnover-family 整体锁死** · dirs: microstructure_illiquidity, overnight_intraday_split, range_structure → b061 atp atom × turnover-family RHS 4/6 候选 max_corr 0.51-0.60@F017 — F017 anchor 占据任意 amount/volume-derived LHS × turnover-family RHS 几何位置；F021 (H/L_60) 同律。新设计 RHS 须脱 turnover/H-L_60 全 family
>   evidence: [[batches/batch_058/judge|batch_058]], [[batches/batch_061/judge|batch_061]]
> - 🔴 **P006 strong-mono+strong-ls_t but library-reducer 陷阱跨 family 通用化（hard_gate 已 codify）+ P008 软判定补丁** · dirs: range_structure, microstructure_illiquidity, gap_acceptance_structure, institutional_flow_proxy → 7 次独立案例 (b042 C005 / b043 C005-C006 / b045 C006 / b055 C002 / b056 C004 / b061 C005 / b062 C005) 跨 4 大 family 独立证实；hard_gate `library_reducer_hard_block` 已 codify (mono≥0.85 + |ls_t|≥2.5 + incr_ic≤-0.005 + alpha_surv≤0.30)；**软判定补丁**（P008 + alpha_surv 例外）：当 alpha_surv > 0.30 + incr_ic < 0 + max_corr ∈ [0.40, 0.50] borderline → 默认 reject（设计无独立新几何）；vs max_corr < 0.30 LOW + 设计层含独立新几何 → reserve 火种（b072 C005 vs C006 干净对照：max_corr=0.46 vs 0.24，reject vs reserve）
>   evidence: [[batches/batch_072/judge|batch_072]], [[_consolidation/findings/pattern_analyst/015]]
<!-- END HOT-TOPICS-LLM -->

## 🎯 方向总览 (Bases)

![[_bases/directions.base]]

## 📚 因子库 (Bases)

![[_bases/factors.base]]

## 📊 最近 Batch (Bases)

![[_bases/recent_batches.base]]

---

> [!abstract]- 系统状态
> - Round: **82** · Admitted: **25** · Active directions: **23**
> - Last batch: **batch_081**
> - Last consolidation: **—**
> - 格式 audit：运行 `research audit index` 检查漂移
