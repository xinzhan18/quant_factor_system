---
generated_at: 2026-04-25T09:10:22Z
round: 55
total_active_directions: 13
total_factors_admitted: 20
last_batch: batch_055
last_consolidation_round: null
---

# 🗺️ Factor Research Index

> [!info] MOC · Map of Content
> 路口页。人看下方 Bases 三表；**LLM 启动读此文件顶部 Cockpit 块**（派生状态 + 下一步指令）；拿数据用 `PYTHONPATH=src python3 -m research memory snapshot`。

<!-- BEGIN COCKPIT -->

> [!note]+ 🧭 LLM Cockpit
> **状态** · round=**55** · phase=`null` (idle) · no batch in flight
> **上一批** · [[batches/batch_055/judge|batch_055]] → [[directions/range_structure]] · admit=**1**/6 (reserve=0, reject=5) · direction.status=`productive`
> **健康** · rounds_since_consolidation=**1** · active_directions=**13**
> **⚠️ 预警** · 空 factor.md: F021
>
> **🎯 下一步（按优先级）**
> 1. ⚠️ **修空报告**：F021 的 `.md` 为空或缺 H1 → 对每个 F{id} 重新 dispatch `/factor-report` subagent
> 2. 🧭 **硬性前置**：`research doctor`（drift 检测）→ `snapshot`（数据）→ 读目标 `directions/{tag}.md` → 进 `/factor-idea`

<!-- END COCKPIT -->

<!-- BEGIN HOT-TOPICS-LLM -->
> [!warning]+ 🔥 Hot Topics（LLM 维护 · 2026-04-25 scan recent=10）
> - 🔴 **P001 rank-diff geometry 范式边界已显形** · dirs: value_liquidity_interaction, intraday_price_formation, barra_residual_alpha → 连续 3 批 0-admit；rank-diff 不是万能钥匙。下设计须验证 (a) LHS atom 不与已 admit rank-diff 因子同源（F019/F020 anti-anchor）(b) RHS basis 不在饱和 endpoints（overnight_5/turnover_5/amount_20/body_ratio_20/price_vol_20）(c) 两端都 scale-free 且独立 raw field
>   evidence: [[batches/batch_052/judge|batch_052]], [[batches/batch_053/judge|batch_053]], [[batches/batch_054/judge|batch_054]]
> - 🟢 **P002 rank-diff geometry 6 跨家族成功 → lessons 升格已完成** · dirs: microstructure_illiquidity, overnight_intraday_split, ohlc_temporal_aggregation, gap_acceptance_structure → F015/F016/F017/F018/F019/F020 跨 4 family 6 admit；后续候选优先沿 "higher-moment LHS × 非饱和 RHS basis" 路径设计
>   evidence: [[batches/batch_046/judge|batch_046]], [[batches/batch_050/judge|batch_050]], [[batches/batch_051/judge|batch_051]]
> - 🔴 **P003 higher-moment LHS regime sign-flip 跨 3 大 family 硬律** · dirs: value_liquidity_interaction, intraday_price_formation, barra_residual_alpha → raw 基本面 / signed intraday / Barra residual 的 Std/Var/cumsum 类二阶聚合在 train(低利率) vs validation(利率上行) 系统性翻号；除非配 regime-aware gating，否则避免 second-moment LHS 单飞
>   evidence: [[batches/batch_052/judge|batch_052]], [[batches/batch_053/judge|batch_053]], [[batches/batch_054/judge|batch_054]]
> - 🟠 **P004 vol_20d 结构性吸收 8+ direction 不可剥离** · dirs: range_structure, overnight_intraday_split, ohlc_temporal_aggregation, gap_acceptance_structure, value_liquidity_interaction, intraday_price_formation, barra_residual_alpha, microstructure_illiquidity → 最近 10 批 60 候选几乎全部 dominant_style=vol_20d；CsRank ordinal 化无法剥离原子层 style；必须 portfolio 层 Barra neutralize 或显式 orth 设计
>   evidence: [[batches/batch_049/judge|batch_049]], [[batches/batch_053/judge|batch_053]]
> - 🟠 **P005 RHS basis 共振饱和律是动态的** · dirs: overnight_intraday_split, ohlc_temporal_aggregation, gap_acceptance_structure, value_liquidity_interaction → admit 一个 rank-diff 即消耗对应 RHS 类目余量（body_ratio_20 经 F020 admit 后从安全→饱和；overnight_5/turnover_5/amount_20/price_vol_20/Amihud_20 已全饱和）；新候选 RHS 须 max_corr@anchor < 0.30 + LHS 完全脱 family
>   evidence: [[batches/batch_051/judge|batch_051]], [[batches/batch_053/judge|batch_053]]
<!-- END HOT-TOPICS-LLM -->

## 🎯 方向总览 (Bases)

![[_bases/directions.base]]

## 📚 因子库 (Bases)

![[_bases/factors.base]]

## 📊 最近 Batch (Bases)

![[_bases/recent_batches.base]]

---

> [!abstract]- 系统状态
> - Round: **55** · Admitted: **20** · Active directions: **13**
> - Last batch: **batch_055**
> - Last consolidation: **—**
> - 格式 audit：运行 `research audit index` 检查漂移
