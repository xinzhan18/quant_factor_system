---
name: factor-mine
description: 双速编排器：快速循环（working_theme → draft → quick_execute → rerun）与正式循环（logic_schedule → /idea → /execute → /judge → /report）
user_invocable: true
---

# Factor Mine — 双速研究循环编排器

## 总览

`/mine` 编排完整的因子挖掘迭代。系统有两条回路：

1. **快速回路**（会话内）：working_theme → expression draft → quick execute（train-only）→ feedback → rerun
2. **正式回路**（跨会话）：logic schedule → /idea → 评估阶段（`/execute` + `/judge`）→ /report

快速回路用于半小时内反复试错。只有被冻结进 `batch_XXX/manifest.yaml` 的 candidate 才进入正式回路。

## 正式回路流程

### Phase 0：调度前检查

读取经验教训（**每轮第一步**）：
```
storage/governance/research_lessons.md
```

读取研究状态：
```bash
PYTHONPATH=src python3 -m research state
```

根据输出决定：
- **current_batch 不为空** → 上一轮未完成，先完成它（继续 /execute 或 /judge）
- **pending_holdout_count > 0** → 优先处理 holdout review
- **两者都为空** → 可以开始新一轮

确认可以开始后，读取调度：
```bash
PYTHONPATH=src python3 -m research logic schedule
```

### Phase 1：/factor-idea（候选生成）

调用 `/factor-idea` skill：
- 读取 logic schedule → 设计 batch-local routes（带 experiment_lineage_tag）
- Probe 过滤垃圾（train-only）：`PYTHONPATH=src python3 -m research probe "expression"`
- Quick execute overlay → freeze boundary 判断
- 冻结 candidates → 写入 `storage/batches/batch_XXX/manifest.yaml`

### Phase 2：/factor-execute（正式评估）

调用 `/factor-execute` skill：
```bash
PYTHONPATH=src python3 -m research execute storage/batches/batch_XXX/manifest.yaml
```
产出：`storage/batches/batch_XXX/research_result.yaml` + `storage/batches/batch_XXX/judge_packet.yaml`

### Phase 3：/factor-judge（结构化裁决）

调用 `/factor-judge` skill：
- 读取 judge_packet（主输入）
- 6 维度裁决：mechanism_alignment, statistical_strength, stability, redundancy, feasibility, risk_model_review
- 候选 verdict: admit / reserve / reject / replace
- 路线 verdict: continue / pause / kill / promote_family
- 所有写入通过 guarded_writer

### Phase 4：/factor-report（仅在有 admit 时）

如果 `admitted_count > 0`，调用 `/factor-report`：
```bash
PYTHONPATH=src python3 -m report.builder --factor-id XXX --vault
```

## 快速回路

在 Phase 1 之前或期间，可以随时进入快速回路：

1. 给出 working_theme（基于 logic contract）
2. 设计表达式草稿
3. Quick execute：`PYTHONPATH=src python3 -m research probe "expression"`
4. 检查 IC hint、coverage、turnover
5. 迭代修改 → 直到 freeze_recommendation = freeze_candidate
6. 冻结进 batch manifest

## Ledger 生命周期

`storage/governance/ledger.yaml` 贯穿正式回路全流程，各 phase 的读写职责：

| Phase | 读 | 写 |
|---|---|---|
| Phase 0 (调度) | search_ledger（预算消耗）, holdout_reviews（pending 检查） | — |
| Phase 1 (/idea) | search_ledger（避免重复 ELT/family） | batch_usage（新建 frozen 条目） |
| Phase 2 (/execute) | — | batch_usage（phase → executed） |
| Phase 3 (/judge) | 全部 4 sections | search_ledger（累计计数）, batch_usage（phase → judged）, holdout_reviews（如触发）, write_audit_log（审计 receipt） |
| Phase 4 (/report) | — | — |

## 关键约束

- 快速回路只能看 **train**，不能看 validation/holdout
- 冻结后进入正式回路，不可回退修改
- 宇宙、日期范围等从 `storage/governance/research_config.yaml` 读取，不 hardcode
- judge 不直接修改治理对象，必须通过 guarded_writer
