---
name: factor-idea
description: 消费 logic schedule，将市场逻辑拆成 research routes，用训练期内 probe 过滤垃圾，并生成正式候选批次
user_invocable: true
---

# 因子创意生成 — /idea v2

`factor-idea` 是整个自动因子研究系统的**中层执行器**。
它不负责创建新的市场逻辑，而负责：

- 读取 `/logic schedule` 给出的 exploration contract
- 将 active logic 拆成本轮 research routes
- 为每条 route 设计 probe forms
- 在训练期内用轻量 probe 过滤垃圾
- 选择值得继续投资的 routes
- 将通过的 routes 展开成正式 candidates
- 输出 batch manifest 与 idea report

---

## 核心原则

1. **idea 不决定研究主题** — 研究主题由 `/logic schedule` 决定
2. **idea 的基本单位是 route** — 每条 route 回答一个具体研究问题
3. **idea 必须受预算控制** — `direction_quota` 和 `candidate_quota`
4. **probe 只负责过滤垃圾** — 不做正式评估，不碰样本外
5. **probe 只能使用训练期** — 2024 及之后数据禁止用于 probe
6. **candidate expansion 必须模板化** — 按 `route_type` 使用预定义模板
7. **默认优先 DSL** — Python 只在 DSL 无法自然表达时允许
8. **idea 不负责长期状态治理** — 不修改 logic 生命周期或全局 state

---

## Step 0：读取本轮上下文

读取：

```bash
PYTHONPATH=src python3 -m research logic schedule
PYTHONPATH=src python3 -m research library
cat storage/state/research_state.yaml
cat storage/logic/registry.yaml
cat storage/policy/capability_registry.yaml
cat storage/memory/forbidden.yaml
cat storage/memory/mining-lessons.md
```

对每个 `eligible_this_round: true` 的 logic，读取：
- `logic_id`, `priority`, `direction_quota`, `candidate_quota`
- `preferred_families`, `suggested_ops`, `required_fields`
- `avoid_patterns`, `current_focus_question`

---

## Step 1：确定本轮 research budget

### 推荐默认策略

| 库规模 | 展开 logic 数 |
|--------|--------------|
| < 20   | 最多 1 个    |
| 20-50  | 1 主 + 1 副  |
| >= 50  | 最多 2-3 个  |

全局预算：总 route 数不超过 3，总 candidate 数不超过 6-8。

---

## Step 2：为每个 logic 规划 routes

对每个被选中的 logic，按 `direction_quota` 生成 route。

### Route Schema

```yaml
route_id: R021_01
logic_id: L021
family_id: FM_breakout
route_type: genesis   # genesis / mutate / crossover / repair / decorrelate
research_question: "量能压缩条件是否能显著提升 breakout 的独立性"
probe_plan:
  core_probe_form: "..."
  neighbor_probe_form: "..."
```

### route_type 判定

| 来源 | route_type |
|------|-----------|
| logic-native hypothesis | `genesis` |
| 已有 factor 局部变形 | `mutate` |
| 两个已有结构组合 | `crossover` |
| 已有 route 修复缺陷 | `repair` |
| 降低与已有因子重叠 | `decorrelate` |

---

## Step 3：为每条 route 设计 probe forms

每条 route 至少设计两个 probe：
- `core_probe_form`：反映 route 核心研究问题
- `neighbor_probe_form`：局部邻近变体

### 实现形式选择

参考 `storage/policy/capability_registry.yaml` 中的 `implementation_policy`。

**DSL 优先场景**：breakout, reversal, momentum, rank_spread, rolling_corr, volatility_proxy 等，
且不需要多阶段 pipeline、不需要多状态切换。

**允许 Python 的场景**：
- `requires_multi_stage_pipeline = true`
- `requires_multi_state_logic = true`
- `dsl_naturalness = low`
- route_type 为 `repair` 或 `decorrelate`

---

## Step 4：运行 probe（只在训练期内）

### 数据范围

probe **只能使用训练期**：
- 训练期全段：`2019-01-01 ~ 2023-12-31`
- 分段 A：`2019-01-01 ~ 2021-12-31`
- 分段 B：`2022-01-01 ~ 2023-12-31`

### 并行运行

```
PYTHONPATH=src python3 -m research probe 'core_probe' --start 2019-01-01 --end 2023-12-31
PYTHONPATH=src python3 -m research probe 'neighbor_probe' --start 2019-01-01 --end 2023-12-31
```

使用 Bash 工具的 `run_in_background` 参数并行启动所有 probe。

### Fail 规则

满足任一条则 `route_verdict = fail`：
- `computable = false`
- `valid_ratio < 0.30`
- `abs(ic_mean_full) < 0.01`
- 分段 A / B 明显反向且都不强
- neighbor probe 完全崩掉
- 命中 forbidden

Verdict: `pass` / `borderline` / `fail`

---

## Step 5：选择要继续展开的 routes

### 5a. 硬过滤

去掉 `route_verdict = fail`、不符合 contract、命中 forbidden 的 route。

### 5b. 打分

```
route_select_score =
  0.35 * probe_quality_score
+ 0.20 * contract_alignment_score
+ 0.15 * novelty_score
+ 0.15 * local_robustness_score
+ 0.10 * logic_priority_score
+ 0.05 * diversity_bonus
```

### 5c. 按 quota 选

每个 logic 最多选前 `direction_quota` 条 route。

---

## Step 6：模板化展开正式 candidates

只对通过 Step 5 的 route 展开 candidate。

### 按 route_type 的默认模板

| route_type | 展开策略 | 数量上限 |
|------------|---------|---------|
| genesis    | 2 窗口变体 + 1 rank 变体 | 3 |
| mutate     | 1 参数 + 1 稳定性修复 + 1 decorrelate | 3 |
| crossover  | 1 additive + 1 gated + 1 interaction | 3 |
| repair     | 降复杂度 / 调阈值 / 换 proxy | 2 |
| decorrelate| residualization / 替换条件变量 | 2 |

### Candidate Schema

```yaml
candidate_id: C042_03
logic_id: L021
route_id: R021_01
family_id: FM_breakout
route_type: genesis
source_type: dsl   # dsl / python
name: "compression_rank_breakout_10"
expression: "..."
rationale: "..."
implementation_reason: "..."
lineage:
  parent_logic: L021
  parent_routes: [R021_01]
  parent_factors: []
  mutation_type: genesis
```

---

## Step 7：Batch-level sanity check

检查：
- 每个 logic 未超过 `candidate_quota`
- 总 candidate 未超过全局预算
- family 分布不过度集中
- Python candidate 不过多
- 无近似重复候选

---

## Step 8：写正式候选文件

写入 `storage/candidates/batch_XXX.yaml`。

```bash
PYTHONPATH=src python3 -m research batch next-id
```

---

## Step 9：写 idea report

写入 `storage/candidates/batch_XXX_idea_report.yaml`。

记录：本轮 logic schedule、route 规划、probe 结果、route 选择原因、candidate 展开分布。

---

## 预处理说明

评估器会自动对因子值和收益率进行预处理后再计算 IC。**不需要在因子表达式中添加 Winsorize/Zscore/Scale** — 管道会统一处理。
