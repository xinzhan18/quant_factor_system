---
generated_at: 2026-05-01T17:40:07Z
round: 69
total_active_directions: 13
total_factors_admitted: 23
last_batch: batch_068
last_consolidation_round: null
---

# 🗺️ Factor Research Index

> [!info] MOC · Map of Content
> 路口页。人看下方 Bases 三表；**LLM 启动读此文件顶部 Cockpit 块**（派生状态 + 下一步指令）；拿数据用 `PYTHONPATH=src python3 -m research memory snapshot`。

<!-- BEGIN COCKPIT -->

> [!note]+ 🧭 LLM Cockpit
> **状态** · round=**69** · phase=`null` (idle) · no batch in flight
> **上一批** · [[batches/batch_068/judge|batch_068]] → [[directions/fundamental_quality_carry]] · admit=**0**/6 (reserve=0, reject=6) · direction.status=`dead`
> **健康** · rounds_since_consolidation=**9** · active_directions=**13** · zero-admit streak=**9**
> **⚠️ 预警** · 空 factor.md: F017.backtest
>
> **🎯 下一步（按优先级）**
> 1. ⚠️ **修空报告**：F017.backtest 的 `.md` 为空或缺 H1 → 对每个 F{id} 重新 dispatch `/factor-report` subagent
> 2. 🧪 **阈值校准**：连续 9 批零 admit → 先按 `lessons.md#Threshold Calibration` 扫 reserve 候选识别错杀；确认有库空间独立错杀 → 调阈；否则继续
> 3. 🧭 **硬性前置**：`research doctor`（drift 检测）→ `snapshot`（数据）→ 读目标 `directions/{tag}.md` → 进 `/factor-idea`

<!-- END COCKPIT -->

<!-- BEGIN HOT-TOPICS-LLM -->
> [!danger]+ 🆕 系统级事件 · Library Recompute v2 (2026-04-26)
> 全库 23 因子通过 **Phase 2 mainline 重算**（[[batches/batch_recompute_v2/result|batch_recompute_v2]] + 修 scipy `pinv` rcond→rtol 后的 [[batches/batch_recompute_v2_pyfix/result|batch_recompute_v2_pyfix]]）；启用 `tradability.filter_limit=true`（涨跌停 mask）+ ST + 停牌 + 60d 新股；**primary = `all_tradable`**，csi300/csi1000 仅 robustness 参考。**DB `factor_values` 老表（`factor_001..factor_045` mining_v1 遗留）已视为无效。**
> - ✅ **22 active** （F001-F013, F015-F023, 含 python F004/F005）
> - 🗑️ **1 deleted**：F014 vwap_overnight_spread（ic_oos_too_low: \|0.0044\| < 0.008）— 物理删除 yaml/md/assets
> - 📌 **新教训**：(1) Phase 2 mainline + tradable_mask 是 admission 单一真相源；(2) batches/{id}/result.yaml 是 report 数据源，因此 revalidated 因子必须新建 batch；(3) python 因子源（vault/batches/python_candidates）应纳入代码版本追踪以避免 scipy 类 API 变更导致的"幽灵失败"。详见 [[lessons#Library Recompute v2]] / [[_meta/library_purge_library_recompute_v2]]

> [!warning]+ 🔥 Hot Topics（LLM 维护 · 2026-04-28 scan recent=10）
> - 🔴 **P001 rank-diff geometry 范式边界进一步收窄 + close-position/cross-ratio atom 也归入死区** · dirs: value_liquidity_interaction, intraday_price_formation, barra_residual_alpha, vwap_proxy_signals, range_structure, overnight_intraday_split, gap_acceptance_structure → 连续累计 0-admit batches: b052/b053/b054/b056/b057 + b060/b061/b062 (3 批 zero-admit streak)；overnight_intraday_split close-position atom 与 gap_acceptance cross-ratio atom **4 代几何变体全失败** (T012 EXHAUSTED + T007 DISPROVEN)；新设计须验证 (a) LHS atom 不与已 admit rank-diff 因子同源（F019-F023 anti-anchor）(b) RHS basis 不在饱和 endpoints（amount/turnover/overnight/body_ratio_20/H-L_60/price_vol_20/Amihud_20+其窗口家族 + F017 anchor 已泛化至任意 turnover-family RHS）(c) LHS atom 自身需 vol_20d 正交
>   evidence: [[batches/batch_060/judge|batch_060]], [[batches/batch_062/judge|batch_062]]
> - 🔴 **P003 higher-moment LHS regime sign-flip 三种失败模式补全 + atom-orthogonality 三件套** · dirs: vwap_proxy_signals, microstructure_illiquidity, gap_acceptance_structure, range_structure → 跨 b061/b062 新增 sign-flip (短窗 sample 不足) + mono cross-sample reversal (normalizer 自身 regime drift) + regime-stable persistent loss (vol_20d 几何嵌入) 三种模式；**升格条件三件套**：atom 须 (a) multi-regime stable (b) 与单日 \|return\|/range 几何正交 (c) normalizer 不引入 regime drift。F019/F020 满足三件，b061 C002 atp-Std / b062 C003 gap_ret-Std / b062 C006 normalized-\|gap\|-Std 全部至少违反一件
>   evidence: [[batches/batch_061/judge|batch_061]], [[batches/batch_062/judge|batch_062]]
> - 🟠 **P004 vol_20d 结构性吸收 9+ direction 全覆盖 + alpha_survival 单 flag 主导** · dirs: range_structure, overnight_intraday_split, ohlc_temporal_aggregation, gap_acceptance_structure, value_liquidity_interaction, intraday_price_formation, barra_residual_alpha, microstructure_illiquidity, vwap_proxy_signals → 最近 10 批 60 候选 dominant_style=vol_20d 占比 ~100%；b057 C003 vol_20d=48.04 / b060 C006 close-position=44.15 / b062 C004=42.86 库内顶级极值；**alpha_survival 比 style_r² 更敏感**已稳定（b056 C006 alpha_surv=0.0725 而 style_r² 仅 borderline）；direction-level alpha quality 中位数 b058 0.43 → b059 0.37 → b060 0.69(回升假象) → b061 0.36 → b062 0.26 整体衰减
>   evidence: [[batches/batch_060/judge|batch_060]], [[batches/batch_061/judge|batch_061]]
> - 🟠 **P005 F017 anchor cluster 占位律泛化 + RHS turnover-family 整体锁死** · dirs: microstructure_illiquidity, overnight_intraday_split, range_structure → b061 atp atom × turnover-family RHS 4/6 候选 max_corr 0.51-0.60@F017 — F017 anchor **不局限于原 RHS 字段 turnover_5**，而是占据**任意 amount/volume-derived LHS × turnover-family RHS** (turnover_5 / Std turnover_60 / Med turnover_20) 几何位置；F021 (H/L_60) 同律：b058 三候选 RHS=Mean(H/L,60) 全 cluster 命中。新设计 RHS 须脱 turnover/H-L_60 全 family
>   evidence: [[batches/batch_058/judge|batch_058]], [[batches/batch_061/judge|batch_061]]
> - 🔴 **P006 strong-mono+strong-ls_t but library-reducer 陷阱第 7 次复现 → 跨 family 通用化 + trigger 收紧** · dirs: range_structure, microstructure_illiquidity, gap_acceptance_structure → 7 次独立案例 (b042 C005 / b043 C005-C006 / b045 C006 / b055 C002 / b056 C004 / b061 C005 / b062 C005) 跨 4 大 family 独立证实；**trigger 应显式收紧**：max_corr ∈ borderline [0.30, 0.70] 死区 + alpha_surv 高时仍须 incr_ic ≥0.015 双重 gate；建议升格 lessons.md 顶部 Promising Patterns 反例段
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
> - Round: **69** · Admitted: **23** · Active directions: **13**
> - Last batch: **batch_068**
> - Last consolidation: **—**
> - 格式 audit：运行 `research audit index` 检查漂移
