---
name: factor-idea
description: 加载挖掘记忆，生成一批候选因子表达式
user_invocable: true
---

# 因子创意生成 — /idea

生成一批候选因子。可选地接受用户指定的探索方向。

## 第1步：确定批次编号

扫描 `mining/candidates/` 目录，找到现有 `batch_XXX.yaml` 中最大的编号，+1 作为本批次编号。如果目录为空，从 `batch_001` 开始。

## 第2步：加载全部记忆（强制 — 不得跳过）

必须读取以下所有文件并理解其内容，然后才能继续：

### 2a. 挖掘经验教训
```
mining/memory/mining-lessons.md
```

### 2b. 经验记忆
```
mining/memory/state.yaml
mining/memory/patterns.yaml
```

### 2c. 最近批次历史（最近3个批次）
```
ls mining/memory/history/
```
读取最近3个批次历史文件，了解已尝试过什么、失败了什么。

### 2d. 当前因子库
```
mining/library/library.yaml
```

## 第3步：上下文摘要（强制 — 生成候选前必须打印）

加载所有记忆后，必须输出结构化的上下文摘要：

```
=== 挖掘上下文 (批次 XXX) ===

因子库状态：
- 规模：X/100 个因子
- 因子列表：[列出每个 factor_id: 名称, 类别, IC]

算子状态：
- 可用：[从经验教训中列出]
- 不可用：[从经验教训中列出]
- 替代方案：[逐一列出]

字段状态：
- 可用：[列出]
- 不可用：[列出]

禁区（来自 patterns.yaml）：
- [列出每个方向 + 原因]

推荐方向（来自 patterns.yaml）：
- [列出每个模式 + 成功率 + 备注]

关键经验教训（来自 mining-lessons.md）：
- [列出与本批次最相关的前5条教训]

最近3个批次结果：
- 批次 N: X/8 录取, 关键发现: ...
- 批次 N-1: ...
- 批次 N-2: ...

候选策略：
基于以上信息，本批次将探索：
1. [方向 + 理由]
2. [方向 + 理由]
...
```

如果用户指定了探索方向，候选策略中至少 4 个方向应围绕该主题。

**关键检查**：如果任何候选表达式使用了不可用算子、不可用字段、或落入禁区，必须停止并重新设计。

## 第4步：生成候选因子

基于上下文摘要，使用 Qlib Alpha 表达式语法生成 **8 个候选因子表达式**。

**规则：**
- 算子：只使用上下文摘要中列为"可用"的算子
- 字段：只使用上下文摘要中列为"可用"的字段
- 替代方案：应用经验教训中的变通方法（如用 `Mul(x,-1)` 替代 `Neg`）
- 禁区：将每个候选与禁区逐一交叉检查 — 评估前就排除
- 推荐：优先选择成功率高的推荐方向
- 类别必须是以下之一：vwap, momentum, volatility, volume, regime, efficiency, distribution, trend, candlestick, intraday_agg, other
- 表达式深度不超过 10
- 避免对称 IfElse（x vs -x）— 无论条件如何都会产生相同因子值

**验证清单**（检查每个候选）：
- [ ] 所有算子都在可用列表中？
- [ ] 所有字段都在可用列表中？
- [ ] 未落入禁区？
- [ ] 与现有因子库中的因子不是近似重复？
- [ ] 表达式深度 ≤ 10？

## 第5步：写入候选文件

将候选写入 `mining/candidates/batch_XXX.yaml`：

```yaml
batch_id: "batch_XXX"
timestamp: "YYYY-MM-DDTHH:MM:SS"
candidates:
  - name: "descriptive_name"
    expression: "Qlib_expression_here"
    category: "category"
    rationale: "该因子应该有效的原因"
```

## 第6步：完成提示

打印候选摘要，然后提示用户：

> 候选已生成：`mining/candidates/batch_XXX.yaml`（8 个候选）
> 运行 `/execute` 开始评估，或 `/mine` 继续完整流程。

---

## 预处理说明

评估器会自动对因子值和收益率进行预处理后再计算 IC。**不需要在因子表达式中添加 Winsorize/Zscore/Scale** — 管道会统一处理：

1. **股票池过滤**：排除停牌股（成交量=0）和涨跌停股
2. **因子清洗**：inf→NaN，MAD 缩尾（5倍），zscore 标准化
3. **收益率遮罩**：不可交易股票的前向收益率设为 NaN
