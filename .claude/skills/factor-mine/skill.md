---
name: factor-mine
description: 执行一轮完整的挖掘迭代（Strategy → Probe → Decide → Execute → Judge → Report）
user_invocable: true
---

# 因子挖掘 — Ralph Loop

执行一轮完整的挖掘迭代：**创意 → 评估 → 审判 → 报告**。每一步都是强制性的，不得跳过。

可选参数：`/mine [探索方向]` — 指定方向时，Strategy 阶段优先围绕该方向发散。

四个阶段也可独立调用：`/idea`、`/execute`、`/judge`、`/factor-report`。

---

## 阶段零：Scheduler Pre-flight

在启动挖掘循环之前，检查调度器是否建议执行外循环：

```bash
PYTHONPATH=src python3 -m mining logic schedule
```

如果**所有**逻辑分数为非正：
- 告诉用户："所有市场逻辑已饱和。建议运行 `/logic new` 生成新的假设。"
- 如果用户同意，运行 `/logic new` 代替 `/idea`

如果存在正分数的逻辑，按正常流程继续 `/idea`。

## 阶段一：创意生成（/idea）

按 `factor-idea` skill 执行全部步骤：

1. 确定批次编号
2. **Strategy（发散）**：
   - 读 directions.yaml + state.yaml + 最近2个批次历史 + 因子库 + mining-lessons.md
   - 可选：web search（active 方向不足时触发）
   - 自动：变异分析（top5 因子未变异的生成变异方向）
   - 输出 6-8 个候选方向 + 探针表达式
3. **打印上下文摘要**（强制）
4. **Probe（探针验证）**：
   - 每方向1个探针，全量股票 + 2024年数据 + 只算IC
   - 命令：`PYTHONPATH=src python3 -m mining probe "表达式" --start 2024-01-01 --end 2024-12-31`
5. **Decide（收敛）**：
   - 基于探针IC选 top 2-3 方向
   - 每方向展开 2-3 个正式候选（共 6-8 个）
   - 写入 `storage/candidates/batch_XXX.yaml`
6. 更新探针方向状态

## 阶段二：评估执行（/execute）

按 `factor-execute` skill 执行全部步骤：

1. 找到刚生成的 `batch_XXX.yaml`
2. 运行评估管道（**加 `--skip-stage1`，不加 `--admit`**）：
   ```bash
   PYTHONPATH=src python3 -m mining batch storage/candidates/batch_XXX.yaml --skip-stage1
   ```
3. 等待完成，确认 `batch_XXX_result.yaml` 已生成
4. 打印评估摘要

## 阶段三：审判与录取（/judge）

按 `factor-judge` skill 执行全部步骤：

1. 读取 `batch_XXX_result.yaml`
2. **LLM 审判**（强制）：6 维报告卡，录取/淘汰/替换
3. **执行录取**：`lib.admit()` / `lib.replace()`（录取后因子 `status=active, evaluation_version=v2`）
4. **Direction Feedback**（强制）：
   - 按方向聚合结果
   - 更新方向文件（frontmatter + body 追加）
   - 自动状态流转（active/exhausted/dead）
   - 更新 directions.yaml 索引
5. 更新 state.yaml + next_round_hint
6. 保存批次历史
7. 验证记忆更新正确性

## 阶段四：报告生成（/factor-report）

**仅在本轮有因子被录取时执行。** 如果本轮 0 录取，跳过此阶段。

按 `factor-report` skill 为每个**本轮新录取**的因子生成报告：

1. **并行生成报告数据**：对所有新录取因子同时启动 report builder（使用 `run_in_background`）：
   ```
   Bash(command="PYTHONPATH=src python3 -m report.builder --factor-id {id1} --vault", run_in_background=true)
   Bash(command="PYTHONPATH=src python3 -m report.builder --factor-id {id2} --vault", run_in_background=true)
   ... 同时启动所有
   ```
2. 收集所有完成通知后，逐个读取 `storage/vault/assets/F{id}/report_data.json`
3. 用 Write 工具生成 Obsidian Markdown 报告到 `storage/vault/factors/`
4. 更新总览页 `storage/vault/Factor Library.md`

---

## CLI 快速参考

```bash
# 探针：轻量IC评估（全量股票，指定时间范围）
PYTHONPATH=src python3 -m mining probe "Rank(\$close, 20)" --start 2024-01-01 --end 2024-12-31

# 评估单个因子（完整管道）
PYTHONPATH=src python3 -m mining evaluate "Rank(\$close, 20)" --qlib-dir ~/.qlib/qlib_data/cn_data_1d

# 查看因子库状态
PYTHONPATH=src python3 -m mining library

# 查看挖掘记忆上下文
PYTHONPATH=src python3 -m mining memory

# 批次评估（跳过Stage1，不录取）
PYTHONPATH=src python3 -m mining batch storage/candidates/batch_XXX.yaml --skip-stage1

# 市场逻辑管理（外循环）
PYTHONPATH=src python3 -m mining logic list          # 列出所有逻辑
PYTHONPATH=src python3 -m mining logic coverage       # 查看类别覆盖地图
PYTHONPATH=src python3 -m mining logic schedule       # 调度器建议下一步

# 生成单因子报告
PYTHONPATH=src python3 -m report.builder --factor-id 025 --vault

# 生成所有因子报告
for id in $(ls storage/library/factors/factor_*.yaml | sed 's/.*factor_//;s/.yaml//'); do
  PYTHONPATH=src python3 -m report.builder --factor-id "$id" --vault
done
```
