---
name: factor-mine
description: 双速编排器：快速循环（working_theme -> draft -> quick_execute -> rerun）与正式循环（logic_schedule -> /idea -> /execute -> /judge -> /report）
user_invocable: true
---

# 因子挖掘 — /mine v2

双速编排器，根据场景自动选择快速循环或正式循环。

可选参数：`/mine [主题]` — 指定主题时优先围绕该主题展开。

四个阶段也可独立调用：`/idea`、`/execute`、`/judge`、`/factor-report`。

---

## 速度选择

### 快速循环（within session）

适用场景：用户给出明确主题或上一轮 judge 留下 `next_round_hint`，且不需要正式 logic 审查。

流程：
1. **Working Theme** — 从用户输入或 `research_state.yaml` 的 `current_focus` 确定主题
2. **Draft** — 快速设计 2-3 个 probe 表达式
3. **Quick Execute** — probe 验证 + 构建 mini batch (2-4 candidates)
4. **Rerun** — 如果 probe 全灭，换变体重试一次

```
working_theme -> draft -> probe -> mini_batch -> execute -> judge
```

### 正式循环（formal loop）

适用场景：无明确主题、所有 logic 饱和、或用户显式要求。

流程：
1. `/logic schedule` — 检查调度器
2. `/idea` — 消费 logic contract，生成正式 batch
3. `/execute` — 评估 batch
4. `/judge` — 审判 + 回写 memory
5. `/report` — 为录取因子生成报告

---

## 阶段零：Pre-flight

在启动任何循环之前：

```bash
PYTHONPATH=src python3 -m research state
PYTHONPATH=src python3 -m research logic schedule
```

### 决策树

1. 如果 `research_state.yaml` 有 `current_focus` 且用户未否决 -> 快速循环
2. 如果用户传入了明确 `[主题]` -> 快速循环
3. 如果所有 logic 分数非正 -> 告诉用户建议 `/logic propose`，若同意则进入正式循环
4. 否则 -> 正式循环

---

## 快速循环详细流程

### Step 1: Working Theme

从以下来源确定主题（优先级递减）：
- 用户显式传入的 `[主题]`
- `research_state.yaml` -> `current_focus[0]`
- 最近 judge_report 的 `next_round_hint`

输出一句话主题描述。

### Step 2: Draft

基于主题，设计 2-3 个 probe 表达式。

检查清单：
- [ ] 算子可用？（参考 `storage/memory/mining-lessons.md`）
- [ ] 字段可用？（$vwap 为零，其余可用）
- [ ] 不命中 forbidden？

### Step 3: Probe + Mini Batch

并行运行所有 probe（**注意：只使用训练期**）：

```
PYTHONPATH=src python3 -m research probe '表达式' --start 2019-01-01 --end 2023-12-31
```

信号分类：
- |IC| >= 0.03: 强信号 STRONG
- 0.01 <= |IC| < 0.03: 中等信号 MODERATE
- |IC| < 0.01: 无信号 WEAK

对 |IC| >= 0.01 的 probe，展开为 2-3 个候选（窗口变异 + rank 变换），写入 mini batch。

### Step 4: Execute + Judge

```bash
PYTHONPATH=src python3 -m research execute storage/candidates/batch_XXX.yaml --skip-stage1
```

然后进入 `/judge` 流程。

### Step 5: Rerun（可选）

如果 Step 3 所有 probe 全灭（|IC| < 0.01），换一组变体重试一次。
如果重试仍全灭，建议切换到正式循环。

---

## 正式循环详细流程

### 阶段一：Logic Schedule

```bash
PYTHONPATH=src python3 -m research logic schedule
```

如果所有分数非正，建议 `/logic propose`。

### 阶段二：创意生成（/idea）

按 `factor-idea` skill 执行全部步骤。输出 `storage/candidates/batch_XXX.yaml`。

### 阶段三：评估执行（/execute）

按 `factor-execute` skill 执行。

```bash
PYTHONPATH=src python3 -m research execute storage/candidates/batch_XXX.yaml --skip-stage1
```

### 阶段四：审判（/judge）

按 `factor-judge` skill 执行全部步骤。

### 阶段五：报告生成（/report）

**仅在本轮有因子被录取时执行。** 如果本轮 0 录取，跳过此阶段。

按 `factor-report` skill 为每个**本轮新录取**的因子生成报告：

1. **并行生成报告数据**：
   ```
   Bash(command="PYTHONPATH=src python3 -m report.builder --factor-id {id} --vault", run_in_background=true)
   ```
2. 读取 `storage/evidence/vault/assets/F{id}/report_data.json`
3. 用 Write 工具生成 Obsidian Markdown 报告到 `storage/evidence/vault/factors/`
4. 更新总览页 `storage/evidence/vault/Factor Library.md`

---

## CLI 快速参考

```bash
# 探针（训练期内，轻量 IC 检查）
PYTHONPATH=src python3 -m research probe "Rank($close, 20)" --start 2019-01-01 --end 2023-12-31

# 批次评估（跳过 Stage1）
PYTHONPATH=src python3 -m research execute storage/candidates/batch_XXX.yaml --skip-stage1

# 研究状态
PYTHONPATH=src python3 -m research state

# 因子库状态
PYTHONPATH=src python3 -m research library

# 批次生命周期
PYTHONPATH=src python3 -m research batch list
PYTHONPATH=src python3 -m research batch next-id

# 市场逻辑
PYTHONPATH=src python3 -m research logic list
PYTHONPATH=src python3 -m research logic schedule

# 报告生成
PYTHONPATH=src python3 -m report.builder --factor-id 025 --vault
```
