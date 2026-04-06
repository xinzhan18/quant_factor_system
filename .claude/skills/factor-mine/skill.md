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

### Phase 3.5：治理同步检查（Governance Sync Verification）

**Phase 3 (/judge) 完成后、Phase 4 (/report) 开始前**，验证治理闭环是否完整。

检查清单：
1. **Admission 写入完整**：每个 admitted factor 的 detail YAML 至少包含 15 个字段（factor_id, name, expression, direction, batch_id, logic_id, route_id, family_id, ic_mean_train, ic_mean_validation, ic_ir_validation, monotonicity_validation, ls_tstat, alpha_survival_ratio, max_lib_corr）。如不完整，从 research_result.yaml 补全。
2. **research_state.yaml** 中 `pending_admission_count = 0`。如有残留，说明 GuardedWriter 写入中断，需手动补完。
3. **Logic Card evidence_summary** 已更新（不为空）。
4. **Logic status** 与 judge_report 中 `logic_recommendations` 一致。
5. **Schedule snapshot** 的 `generated` 日期 = 今天。
6. **Family registry** 的 admitted_count 与 factor index 一致。
7. **Forbidden patterns** 涵盖所有 judge_report 中 killed 的 route 对应的失败模式。
8. **Discovery candidates** 中包含本轮 judge_report 的 discovery_flags。

如果任何检查失败，**先修复再进入 Phase 4**。这些不应手动补——judge skill 的 Step 7a 应该已经完成。如果遗漏了，说明 Step 7a 执行不完整，需要补做。

### Phase 4：/factor-report（仅在有 admit 时，后台并行）

如果 `admitted_count > 0`，为每个 admitted 因子启动**后台 subagent**：

```
对每个 admitted factor_id:
  Agent(run_in_background=true, description="Report F{id}"):
    "为因子 F{id}（batch_{batch_id}）生成报告。
     执行: PYTHONPATH=src python3 -m report.builder --factor-id {id} --vault
     然后读取 report_data.json 生成 Obsidian Markdown。"
```

**不要串行等待**——report 每个要 5-8 分钟，后台并行不阻塞主流程。
完成通知会自动返回。

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
| Phase 3 (/judge) | 全部 4 sections | search_ledger（累计计数）, batch_usage（phase → judged）, holdout_reviews（如触发）, write_audit_log（审计 receipt）, **logic cards**（evidence_summary）, **logic registry**（status 变更）, **schedule snapshot**, **forbidden_patterns**, **family_registry**, **discovery_candidates** |
| Phase 3.5 (验证) | 全部治理对象 | 仅补漏（正常情况无写入） |
| Phase 4 (/report) | — | — |

## 关键约束

- 快速回路只能看 **train**，不能看 validation/holdout
- 冻结后进入正式回路，不可回退修改
- 宇宙、日期范围等从 `storage/governance/research_config.yaml` 读取，不 hardcode
- judge 不直接修改治理对象，必须通过 guarded_writer
