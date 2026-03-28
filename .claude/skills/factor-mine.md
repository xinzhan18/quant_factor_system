---
name: factor-mine
description: 执行一轮完整的 Ralph Loop 因子挖掘迭代（串联 idea → execute → judge）
user_invocable: true
---

# 因子挖掘 — Ralph Loop

执行一轮完整的挖掘迭代：**创意 → 评估 → 审判**。每一步都是强制性的，不得跳过。

可选参数：`/mine [探索方向]` — 指定方向时，创意阶段至少 4 个候选围绕该方向。

三个阶段也可独立调用：`/idea`、`/execute`、`/judge`。

---

## 阶段一：创意生成（/idea）

按 `factor-idea.md` 执行全部步骤：

1. 确定批次编号（扫描 `mining/candidates/`，最大编号 +1）
2. **加载全部记忆**（强制）：
   - `mining/memory/mining-lessons.md` — 工程经验教训
   - `mining/memory/state.yaml` — 因子库状态
   - `mining/memory/patterns.yaml` — 推荐/禁区模式
   - `mining/memory/history/` — 最近 3 个批次历史
   - `mining/library/library.yaml` — 当前因子库
3. **打印上下文摘要**（强制）：因子库状态、算子/字段状态、禁区、推荐方向、最近批次结果、本批候选策略
4. **生成 8 个候选因子**：遵守算子/字段/禁区/深度规则，写入 `mining/candidates/batch_XXX.yaml`

## 阶段二：评估执行（/execute）

按 `factor-execute.md` 执行全部步骤：

1. 找到刚生成的 `batch_XXX.yaml`
2. 运行评估管道（**不加 `--admit`**）：
   ```bash
   python3 -m mining batch mining/candidates/batch_XXX.yaml
   ```
3. 等待完成，确认 `batch_XXX_result.yaml` 已生成
4. 打印评估摘要（通过/淘汰/替换数量）

## 阶段三：审判与录取（/judge）

按 `factor-judge.md` 执行全部步骤：

1. 读取 `batch_XXX_result.yaml`
2. **LLM 审判**（强制）：对每个 screened 因子打印 6 维报告卡，做出 录取/淘汰/替换 判定
3. **执行录取**：调用 `lib.admit()` / `lib.replace()`
4. **更新全部记忆**（强制）：
   - `patterns.yaml` — 推荐/禁区
   - `state.yaml` — 库规模、统计
   - `history/batch_XXX.yaml` — 批次历史
   - `mining-lessons.md` — 新工程发现
5. 验证记忆更新正确性

---

## CLI 快速参考

以下操作不需要启动完整挖掘流程，直接用 CLI 即可：

```bash
# 评估单个因子表达式
python3 -m mining evaluate "Rank(\$close, 20)" --qlib-dir ~/.qlib/qlib_data/cn_data_1d

# 查看因子库状态
python3 -m mining library

# 查看挖掘记忆上下文
python3 -m mining memory

# 批次评估（不录取，只看结果）
python3 -m mining batch mining/candidates/batch_XXX.yaml

# 批次评估 + 自动录取（跳过 LLM 审判）
python3 -m mining batch mining/candidates/batch_XXX.yaml --admit
```
