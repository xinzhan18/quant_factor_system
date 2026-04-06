---
name: factor-idea
description: 消费 logic schedule，规划实验路线，探针过滤，快速验证，冻结候选因子批次
user_invocable: true
---

# Factor Idea — 候选因子生成

## 目标

将 logic contract 拆成可验证的 batch-local 实验切片，用 train-only probe 过滤垃圾，冻结少量候选进入正式评估。

## 输入

当前 workflow 下，`/idea` 的输入已经收敛为 **logic 级编译态上下文**，不再散读旧 ledger /
snapshot / factor index。

可用算子/字段查询：`PYTHONPATH=src python3 -m research capabilities`

## 流程

### Step 1：读取认知状态（编译后上下文）

**必读（按顺序）：**
```
storage/logic/cards/LXXX.yaml                  # 执行态：contract, threads, next_actions, bottleneck
storage/logic/reflections/LXXX.md              # 认知叙事：为什么相信/不相信，机制洞察
storage/governance/research_config.yaml        # universe, thresholds, forbidden_patterns
```

**限读（仅在 card 信息不够时）：**
```
storage/batches/batch_XXX/judge_report.yaml    # 最近一轮的详细裁决
```

**不再读取：**
- ~~storage/governance/ledger.yaml~~ — 预算消耗信息已编译进 card.evidence_summary
- ~~storage/logic/snapshots/latest_schedule_snapshot.yaml~~ — 调度信息已编译进 card.contract

从 card.yaml 提取：
- `contract.current_focus_question` — 本轮的研究问题
- `contract.preferred_families` / `suggested_ops` / `avoid_patterns` — 约束边界
- `evidence_summary.current_bottleneck` — 当前阻塞点
- `deepening_threads` — 持久化的研究问题（核心消费对象）
- `next_actions` — reflect 建议的下一步

#### Thread 消费协议

1. 筛选 `deepening_threads` 中 `status: active` 的 threads，按 `priority` 排序（high > medium > low）
2. 每个 active thread 的 `next_probes` → **直接作为候选表达式来源**
3. 每个 thread 的 `stop_condition` → 影响 route 设计（试图回答 stop_condition 中的判别问题）
4. 如果所有 threads 都 parked/answered → 降级到 `next_actions`
5. 如果 `next_actions` 也为空 → 基于 `current_bottleneck` 自由探索

#### 深度 vs 广度决策

| 条件 | 策略 |
|------|------|
| 有 active thread 且 next_probes 非空 | **deepen** — 围绕 thread 设计 route |
| threads 全 parked + contract 还有空间 | **broaden** — 试新 family |
| contract 空间也耗尽 | **escape** — 向 reflect 报告 saturated 信号 |

### Step 2：设计 Routes（batch-local 实验组）

每条 route 包含：
- `route_id`: batch-local ID
- `experiment_lineage_tag` (ELT): 跨 batch 追踪标签，格式 `ELT_{logic_id}_{route_type}_{mechanism}_{conditioning}_v{N}`
- `route_type`: genesis / mutate / crossover / repair / decorrelate
- `research_question`: 本组实验回答什么问题
- `family_id`: 已注册(FM_*) / 临时(PF_*) / 未知(FM_unknown)

### Step 3：Probe 过滤（train-only，并行）

对每条 route 的核心 probe form 运行。**多个 probe 应在同一条消息中并行发出**（每个是独立进程，互不干扰）：
```bash
# 在一条消息里同时发出所有 Bash 调用
PYTHONPATH=src python3 -m research probe "expression_1"
PYTHONPATH=src python3 -m research probe "expression_2"
PYTHONPATH=src python3 -m research probe "expression_3"
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

### Step 7a：记录策略决策

在 `idea_report.yaml` 中追加 `strategy_decision` section：

```yaml
strategy_decision:
  selected_strategy: deepen|broaden|pivot|escape      # 枚举
  decision_basis_codes:                                 # 枚举列表
    - active_thread_has_clear_probe
    - expected_information_gain_high
    - no_strong_pivot_signal
    - all_threads_parked
    - contract_space_exhausted
    - escalation_signal_present
  selected_threads: [T001]
  rejected_threads_with_reason:
    - thread_id: T002
      reason_code: low_marginal_value|stop_condition_near|insufficient_evidence|superseded
      note: "可选自由文本"
  selected_families: [volume_distribution]
  why_now: "自由文本解释"
```

**decision_basis_codes 必须是枚举**，不能自由发挥。这保证了策略决策可审计、可统计。

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
