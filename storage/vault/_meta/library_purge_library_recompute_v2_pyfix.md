---
title: Library Purge v2 — Phase 2 mainline recompute under tradable_mask
generated_at: 2026-04-25T17:32:25Z
batch_id: batch_recompute_v2_pyfix
run_name: library_recompute_v2_pyfix
primary_universe: all_tradable
secondary_universes: [csi300, csi1000]
n_evaluated: 2
n_kept: 2
n_deleted: 0
---

# Library Purge v2

> [!danger]+ 系统级清算
> 全部 23 个因子通过 Phase 2 mainline 重算，启用 `tradability.filter_limit=true`
> （涨跌停 mask）。CP01 hard_gates 决定 keep/delete。DB `factor_values` 老表
> （`factor_001..factor_045`，mining_v1 遗留）已视为无效，单独 DROP。

**Result**: 2 kept, 0 deleted

## Decisions

| Factor | Name | Action | Coverage | IC mean | ICIR | Mono | L/S Sharpe | csi300 mono | csi1000 mono | Reasons |
|--------|------|--------|----------|---------|------|------|------------|-------------|--------------|---------|
| F004 | barra_residual_return | **KEEP** | 1.000 | 0.0237 | 0.275 | 1.00 | 4.913 | 0.10 | 0.90 | passed |
| F005 | barra_residual_alpha_60d | **KEEP** | 1.000 | 0.0237 | 0.275 | 1.00 | 4.913 | 0.10 | 0.90 | passed |

## Deletion artifacts

