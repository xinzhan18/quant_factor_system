---
name: factor-idea
description: 消费 logic schedule，规划实验路线，探针过滤，快速验证，冻结候选因子批次
user_invocable: true
---

# Factor Idea — 候选因子生成

## 目标

将 logic contract 拆成可验证的 batch-local 实验切片，用 train-only probe 过滤垃圾，冻结少量候选进入正式评估。

## 输入

**每轮必读**（按顺序）：
```
storage/governance/research_lessons.md   # 禁忌模式 + 经验教训（必须先读，避免重复踩坑）
storage/governance/research_config.yaml  # universe, 日期范围, 阈值
storage/governance/ledger.yaml           # search_ledger + batch_usage
storage/logic/snapshots/latest_schedule_snapshot.yaml
storage/logic/cards/*.yaml
storage/registry/factors/index.yaml
```

可用算子/字段查询：`PYTHONPATH=src python3 -m research capabilities`

## 流程

### Step 1：读取 Logic Schedule + Ledger 上下文

读取最新 schedule snapshot，获取 active logic 列表及其 contract：
- `current_focus_question`
- `direction_quota` / `candidate_quota`
- `preferred_families` / `suggested_ops` / `avoid_patterns`

读取 `storage/governance/ledger.yaml` 中的 `search_ledger` section：
- `by_logic[logic_id].logic_attempt_count_to_date` — 判断该 logic 已消耗的搜索预算
- `by_experiment_tag[ELT].latest_verdict` — 跳过已被 kill 的 ELT，优先 continue 的 ELT
- `by_family[FM_*].admitted_count_to_date` — 评估 family 饱和度

### Step 2：设计 Routes（batch-local 实验组）

每条 route 包含：
- `route_id`: batch-local ID
- `experiment_lineage_tag` (ELT): 跨 batch 追踪标签，格式 `ELT_{logic_id}_{route_type}_{mechanism}_{conditioning}_v{N}`
- `route_type`: genesis / mutate / crossover / repair / decorrelate
- `research_question`: 本组实验回答什么问题
- `family_id`: 已注册(FM_*) / 临时(PF_*) / 未知(FM_unknown)

### Step 3：Probe 过滤（train-only）

对每条 route 的核心 probe form 运行：
```bash
PYTHONPATH=src python3 -m research probe "expression"
```

Probe verdict：
- `pass`：进入 candidate expansion
- `reserve`：budget 允许时进入
- `fail`：跳过

Fail 条件（任一即 fail）：
- 不可计算 / valid_ratio < 0.30 / 无方差 / 命中 forbidden / 复杂度过高 / 无信号 / 分段崩塌

### Step 4：Quick Execute（可选，train-only）

在 candidate draft 上追加检查：
- `turnover_hint` / `nearest_factor_hint`
- `freeze_recommendation`: freeze_candidate / revise / drop

### Step 5：Freeze Boundary

冻结条件：
1. probe ≠ fail
2. quick_execute 给出 freeze_candidate
3. 无语法/可计算问题
4. 已有稳定的 ELT

### Step 6：Candidate Expansion

按 route_type 模板展开：
- genesis: 2 窗口变体 + 1 rank 变体（≤3）
- mutate: 1 参数 + 1 稳定性修复 + 1 decorrelate（≤3）
- crossover: 1 additive + 1 gated + 1 interaction

### Step 7：写入 Batch + 更新 State

```
storage/batches/batch_XXX/manifest.yaml
storage/batches/batch_XXX/idea_report.yaml
```

每个 candidate 必须包含：candidate_id, logic_id, route_id, family_id, route_type, experiment_lineage_tag, source_type, expression, rationale, implementation_reason, lineage。

**冻结后必须更新 research state**：
```bash
PYTHONPATH=src python3 -m research state set current_batch batch_XXX
PYTHONPATH=src python3 -m research state set current_batch_phase frozen
```

### Step 8：更新 Ledger

在 `storage/governance/ledger.yaml` 的 `batch_usage.batches` 中追加一条记录：

```yaml
- batch_id: batch_XXX
  train_range: (从 research_config.yaml 读取)
  validation_range: (从 research_config.yaml 读取)
  validation_window_id: val_2022_2023
  holdout_used: false
  logic_ids: [L021]              # 本批涉及的 logic
  candidate_count: 5             # 冻结的 candidate 数
  phase: frozen                  # idea 阶段写 frozen
```

## 预算纪律

- 总 route ≤ 3
- 总 candidate ≤ 6~8
- 不超过 logic contract 的 candidate_quota

## 样本约束

- idea 只看 **train**（日期从 `storage/governance/research_config.yaml` 的 `sample_policy.active_train_range` 读取）
- 不看 validation / holdout
- DSL 优先；Python 仅在 dsl_naturalness=low 时使用（≤30 行，≤3 参数）
