---
generated_at: 2026-04-25T12:46:42Z
round: 59
total_active_directions: 13
total_factors_admitted: 22
last_batch: batch_059
last_consolidation_round: null
---

# 🗺️ Factor Research Index

> [!info] MOC · Map of Content
> 路口页。人看下方 Bases 三表；**LLM 启动读此文件顶部 Cockpit 块**（派生状态 + 下一步指令）；拿数据用 `PYTHONPATH=src python3 -m research memory snapshot`。

<!-- BEGIN COCKPIT -->

> [!note]+ 🧭 LLM Cockpit
> **状态** · round=**59** · phase=`null` (idle) · no batch in flight
> **上一批** · [[batches/batch_059/judge|batch_059]] → [[directions/overnight_intraday_split]] · admit=**1**/6 (reserve=2, reject=3) · direction.status=`productive`
> **健康** · rounds_since_consolidation=**5** · active_directions=**13**
> **⚠️ 预警** · 空 factor.md: F023
>
> **🎯 下一步（按优先级）**
> 1. ⚠️ **修空报告**：F023 的 `.md` 为空或缺 H1 → 对每个 F{id} 重新 dispatch `/factor-report` subagent
> 2. 🧭 **硬性前置**：`research doctor`（drift 检测）→ `snapshot`（数据）→ 读目标 `directions/{tag}.md` → 进 `/factor-idea`

<!-- END COCKPIT -->

<!-- BEGIN HOT-TOPICS-LLM -->
> [!warning]+ 🔥 Hot Topics（LLM 维护 · 2026-04-25 scan recent=10）
> - 🔴 **P001 rank-diff geometry 范式边界已显形 + VWAP basis 也归入死区** · dirs: value_liquidity_interaction, intraday_price_formation, barra_residual_alpha, vwap_proxy_signals → 连续 4 批 0-admit（b052/b053/b054/b057）+ b056 也 0-admit；rank-diff 不是万能钥匙。下设计须验证 (a) LHS atom 不与已 admit rank-diff 因子同源（F019/F020/F021 anti-anchor）(b) RHS basis 不在饱和 endpoints（overnight_5/turnover_5/amount_20/body_ratio_20/price_vol_20/Amihud_20+其窗口家族）(c) LHS atom 自身需 vol_20d 正交（VWAP-prev gap 失败因 gap 大小≈日内波动率）
>   evidence: [[batches/batch_052/judge|batch_052]], [[batches/batch_054/judge|batch_054]], [[batches/batch_057/judge|batch_057]]
> - 🔴 **P003 higher-moment LHS regime sign-flip 跨 3 大 family 硬律 + 不可 family-agnostic 迁移** · dirs: value_liquidity_interaction, intraday_price_formation, barra_residual_alpha, vwap_proxy_signals → raw 基本面 / signed intraday / Barra residual 的 Std/Var/cumsum 类二阶聚合在 train(低利率) vs validation(利率上行) 系统性翻号；**新 caveat**：F019/F020 (OHLC body / gap_ret) higher-moment 成功律 **不能** 迁移到 VWAP basis (b057 全部 Std 路径 hard_gate fail) — atom 自身必须与 vol_20d 正交才能成立
>   evidence: [[batches/batch_052/judge|batch_052]], [[batches/batch_054/judge|batch_054]], [[batches/batch_057/judge|batch_057]]
> - 🟠 **P004 vol_20d 结构性吸收 8+ direction 不可剥离 + alpha_survival 比 style_r² 更敏感** · dirs: range_structure, overnight_intraday_split, ohlc_temporal_aggregation, gap_acceptance_structure, value_liquidity_interaction, intraday_price_formation, barra_residual_alpha, microstructure_illiquidity, vwap_proxy_signals → 最近 10 批 60 候选几乎全部 dominant_style=vol_20d；b057 C003 vol_20d=48.04 整库历史新高；**新诊断要件**：当 alpha_survival<<0.10 (b056 C006=0.0725) 而 style_r² 仅 borderline 时 IC 仍是 vol_20d 假象 — alpha_survival 单 flag 比 style_r² 更敏感
>   evidence: [[batches/batch_056/judge|batch_056]], [[batches/batch_057/judge|batch_057]]
> - 🟠 **P005 RHS basis 共振饱和律持续动态扩张** · dirs: overnight_intraday_split, ohlc_temporal_aggregation, gap_acceptance_structure, value_liquidity_interaction, range_structure → admit 一个 rank-diff 即消耗对应 RHS 类目余量；F021 admit 后 H/L 60d 几何 ratio 仍可继续，但 amount/turnover/overnight/body_ratio_20/price_vol_20/Amihud_20 + 同 atom 整窗口家族（F012 Amihud_20 → Amihud-numerator_60 b053 同律）已锁死；新候选 RHS 须 max_corr@anchor < 0.30 + LHS 完全脱 family
>   evidence: [[batches/batch_053/judge|batch_053]], [[batches/batch_055/judge|batch_055]]
> - 🔴 **P006 strong-mono+strong-ls_t but library-reducer 陷阱第 5 次复现 → 升格 lessons 候选** · dirs: range_structure, gap_acceptance_structure → 判别要件已稳定：mono_oos≥0.9 + |ls_t_oos|≥3.0 + incr_ic<0 + alpha_surv<0.30；5 次独立案例 (b042 C005 / b043 C005-C006 / b045 C006 / b055 C002 / b056 C004) 跨方向独立证实，是 P005 RHS 共振饱和律下的具体表型 — 设计阶段不可只看 mono+ls_t，必须前置 incr_ic 估算
>   evidence: [[batches/batch_055/judge|batch_055]], [[batches/batch_056/judge|batch_056]]
<!-- END HOT-TOPICS-LLM -->

## 🎯 方向总览 (Bases)

![[_bases/directions.base]]

## 📚 因子库 (Bases)

![[_bases/factors.base]]

## 📊 最近 Batch (Bases)

![[_bases/recent_batches.base]]

---

> [!abstract]- 系统状态
> - Round: **59** · Admitted: **22** · Active directions: **13**
> - Last batch: **batch_059**
> - Last consolidation: **—**
> - 格式 audit：运行 `research audit index` 检查漂移
