---
name: factor-mine
description: 执行一轮 Ralph Loop 因子挖掘迭代 — 加载记忆、生成候选、评估、更新因子库和记忆
user_invocable: true
---

# 因子挖掘 — Ralph Loop

执行一轮完整的挖掘迭代。**每一步都是强制性的，不得跳过任何步骤。**

## 第1步：加载全部记忆（强制 — 不得跳过）

必须读取以下所有文件并理解其内容，然后才能继续：

### 1a. 挖掘经验教训（工程陷阱、策略错误、市场洞察、Alpha101 笔记）
```
mining/memory/mining-lessons.md
```

### 1b. 经验记忆（因子库状态、模式、洞察）
```
mining/memory/state.yaml
mining/memory/patterns.yaml
mining/memory/insights.yaml
```

### 1c. 最近批次历史（最近3个批次）
```
ls mining/memory/history/
```
读取最近3个批次历史文件，了解已尝试过什么、失败了什么。

### 1d. 当前因子库
```
mining/library/library.yaml
```

## 第2步：上下文摘要（强制 — 生成候选前必须打印）

加载所有记忆后，必须输出结构化的上下文摘要。这证明你已经吸收了记忆，防止重复过去的错误。

**向用户打印以下摘要：**

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

关键洞察（来自 insights.yaml）：
- [列出与本批次最相关的前5条洞察]

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

**关键检查**：如果任何候选表达式使用了不可用算子、不可用字段、或落入禁区，必须停止并重新设计。

## 第3步：生成候选因子

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

## 预处理（自动完成）

评估器会自动对因子值和收益率进行预处理后再计算 IC。**不需要在因子表达式中添加 Winsorize/Zscore/Scale** — 管道会统一处理：

1. **股票池过滤**：排除停牌股（成交量=0）和涨跌停股
2. **因子清洗**：inf→NaN，MAD 缩尾（5倍），zscore 标准化
3. **收益率遮罩**：不可交易股票的前向收益率设为 NaN

可通过 `MiningConfig(neutralize_mode="market_cap")` 启用市值/行业中性化。

`MiningConfig` 中的所有预处理配置：
- `filter_suspend` / `filter_limit` — 股票池过滤（默认：True）
- `winsorize_method` / `winsorize_n` — 异常值处理（默认："mad" / 5.0）
- `standardize_method` — "zscore" 或 "rank"（默认："zscore"）
- `neutralize_mode` — "none", "market_cap", "industry", "both"（默认："none"）

## 第4步：评估

**重要**：将评估脚本写入 `.py` 文件，不要使用 `python -c` 或 heredoc。

创建 `run_batch_XXX.py`：

```python
"""批次 XXX 评估"""
import warnings; warnings.filterwarnings('ignore')
import os
os.environ['JOBLIB_START_METHOD'] = 'fork'
import multiprocessing
multiprocessing.set_start_method('fork', force=True)

import logging, yaml
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(name)s - %(message)s')
logger = logging.getLogger('mining')


def main():
    import qlib
    from qlib.config import REG_CN
    qlib.init(provider_uri='~/.qlib/qlib_data/cn_data_1d', region=REG_CN)
    from qlib.data import D

    # 加载股票池（D.instruments 返回 dict，需要解析为列表）
    inst_dict = D.instruments('all')
    df_temp = D.features(instruments=inst_dict, fields=['$close'],
                         start_time='2024-06-01', end_time='2024-06-30')
    all_instruments = df_temp.index.get_level_values('instrument').unique().tolist()

    from mining.config import MiningConfig
    from mining.evaluator import FactorMiningEvaluator

    config = MiningConfig(
        custom_universe=all_instruments,
        train_start='2020-01-01',
        train_end='2024-12-31',
        test_start='2024-07-01',
        fast_screening_universe_size=50,
    )
    evaluator = FactorMiningEvaluator(config)

    with open('mining/candidates/batch_XXX.yaml') as f:
        batch = yaml.safe_load(f)

    result = evaluator.evaluate_batch(batch['candidates'])

    # 打印结果
    logger.info(f"录取: {len(result.admitted)}, 淘汰: {len(result.rejected)}")
    for f in result.admitted:
        s1 = f.get('stage1', {})
        s3 = f.get('stage3', {})
        logger.info(f"  录取 {f['name']}: IC={s1.get('ic_mean',0):.4f}, OOS={s3.get('ic_mean_oos','?')}")
    for f in result.rejected:
        s1 = f.get('stage1', {})
        logger.info(f"  淘汰 {f['name']}: IC={s1.get('ic_mean','?')}")

    # 保存结果（使用白名单方式，只保留必要字段，自动过滤 DataFrame 等大对象）
    output = result.to_dict()
    output['batch_id'] = batch['batch_id']
    output['timestamp'] = datetime.now().isoformat()
    with open('mining/candidates/batch_XXX_result.yaml', 'w') as fp:
        yaml.dump(output, fp, default_flow_style=False, allow_unicode=True)


if __name__ == '__main__':
    main()
```

然后运行：`python3 run_batch_XXX.py`

用完后清理脚本：`rm run_batch_XXX.py`

## 第5步：更新因子库

对每个录取的因子：

1. 验证因子不是管道漏洞（检查 n_days > 100，分位数收益不是 NaN）
2. 添加到因子库：
```python
from mining.library import FactorLibrary
from mining.config import MiningConfig

lib = FactorLibrary(MiningConfig())
lib.admit(factor_dict)
```
3. 如果 `library.yaml` 中 `ic_mean` 为 null，手动修复（已知 bug：评估器将 IC 存储在 `full_ic.ic_mean` 下）
4. 写入详细的 `mining/library/factors/factor_XXX.yaml`，包含完整指标

对于替换，使用 `lib.replace(old_id, new_factor_dict)`。

**重要**：`evaluate_batch()` 不会自动持久化到 `library.yaml` — 必须对每个录取因子单独调用 `lib.admit()`。

## 第6步：更新记忆（强制 — 不得跳过）

评估后，更新所有记忆文件。这是下一轮迭代从本轮学习的方式。

### 6a. 更新 `mining/memory/patterns.yaml`
- 录取因子 → 添加到 `recommended_directions`，包含成功率和示例因子
- 淘汰（高相关性）→ 添加到 `forbidden_regions`，包含相关性值和冲突因子
- 淘汰（低 IC）→ 添加到 `forbidden_regions`，包含 IC 值和原因
- 淘汰（算子错误）→ 在现有模式条目中注明

### 6b. 更新 `mining/memory/insights.yaml`
- 新的实证发现（如"X 算子未注册"、"Y 类因子总是与 Z 相关"）
- 根据重复证据更新置信度
- 删除或降级已证明错误的洞察

### 6c. 更新 `mining/memory/state.yaml`
- 因子库规模、平均 IC、各领域饱和度
- 挖掘统计：总批次数、总候选数、录取率

### 6d. 保存批次历史到 `mining/memory/history/batch_XXX.yaml`
包含：所有候选因子、录取/淘汰及原因、关键教训、工程发现

### 6e. 更新挖掘经验教训（如有新工程发现）
```
mining/memory/mining-lessons.md
```
添加任何新的算子发现、运行时错误、变通方法、管道 bug、市场洞察。

### 6f. 验证
更新后，重新读取 `patterns.yaml` 并确认：
- 没有重复的禁区
- 所有新发现已被记录
- 推荐方向反映当前证据
