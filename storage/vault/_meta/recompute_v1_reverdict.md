---
title: Recompute v1 (tradable_mask + multi-universe) — Reverdict Report
generated_at: 2026-04-25
audit_run: tradable_mask_v1_st
primary_universe: all_tradable
---

# Recompute v1 — Reverdict Report

> [!info] 背景
> Phase 2 接入 `build_tradable_mask`（PIT ST / 停牌 / 涨跌停 / 新股 60 日）+ DB `ref_stock_status`，并把评估扩展到 `all_tradable / csi300 / csi1000` 三个 universe。**Primary universe = `all_tradable`** （CP01–CP06 在此跑），csi300/csi1000 仅作 robustness reference。23 个因子全量重算，逐一审视：

## 关键判决（5 因子需 LLM judge 复核）

| Factor | 旧 ICIR | 新 ICIR (all_tradable) | 旧 Mono | 新 Mono | 失效 flag | 决议 |
|---|---|---|---|---|---|---|
| **F003** overnight_gap_normalized | 0.379 | 0.246 | 1.00 | **0.40** | mono_weak | ⛔ 撤回 admit；mono 跌过 0.6 floor |
| **F010** overnight_return_persistence_5d | 0.396 | 0.294 | 1.00 | **0.40** | mono_weak | ⚠️ 降级 reserve；ICIR 还行但已不单调 |
| **F011** overnight_return_persistence_3d | 0.422 | 0.303 | 1.00 | **0.40** | mono_weak | ⚠️ 降级 reserve；与 F010 同因机制崩塌 |
| **F013** log_amount_weighted_acceptance_20 | 0.253 | 0.226 | 0.60 | **0.40** | mono_weak | ⛔ 撤回 admit |
| **F014** vwap_overnight_spread | 0.097 | **0.035** | 0.60 | **-0.60** | sign_mismatch + ic_below_floor | ⛔ 撤回 admit；sign flip + IC 失守 |

**保留 active**：F022 (mono 0.6→0.6 borderline pass)、其余 17 因子均 OK。

## csi300/csi1000 健壮性参考

> 注：csi300/csi1000 **不是 verdict 输入**，仅作 robustness label。Floor: `|ICIR|≥0.15 ∧ |mono|≥0.6`。

**csi300 通过的因子（7 个）**：`F014(degenerate), F017, F018, F019, F020, F021, F023` —— 全是 rank-diff family（除 F014）

**csi300 不通过的因子（16 个）**：包括所有 raw OHLCV / persistence / amount-stat 因子。csi300 大盘股 alpha 普遍被压平是常态，不是因子失效。

**关键发现：rank-diff family universe-robust**
- icir_robustness_ratio = `min(|ICIR|) / max(|ICIR|)` 跨三 universe
- rank-diff family 中位 ~0.55 vs raw OHLCV 中位 ~0.20
- 机理：`Sub(CsRank(LHS), CsRank(RHS))` 是 scale-free，universe 大小变化只改 rank 相对位置，不破序结构

## 多 universe 一致性表

| 类别 | 因子数 | icir_robustness_ratio 中位 |
|---|---|---|
| rank-diff family (F015–F023, 部分) | 9 | ~0.55 |
| Barra residual (F004/F005) | 2 | ~0.50 |
| volume/amount stat (F001/F012/F015/F016) | 4 | ~0.25 |
| raw OHLCV / persistence | 8 | ~0.20 |

## Lesson 候选（已写入 lessons.md）

1. **rank-diff symmetric structure 是 universe-robustness 之王** —— scale-free 几何对 universe size 不敏感
2. **persistence-style overnight 因子在 PIT ST mask 加上后 mono 全面崩塌** —— 旧版无 ST mask 时单调性是 ST 股反向收益虚假支撑的；这是 batch_010~025 整批的系统性高估

## 后续 admission 流程

✅ **已 wire 进 Phase 2 mainline**：`data_bridge.build_phase2_inputs` 现在构造 `universe_masks`，`phase2_execute._evaluate_candidate` 跑完 primary 全套指标后追加每个 secondary universe 的 5 项基础指标 (coverage / ic_mean / ic_ir / monotonicity / long_short_sharpe)。`factor_writer` 把 `validation_metrics_by_universe` + `universe_robustness` 写进新 admit 的 `F*.yaml`。
