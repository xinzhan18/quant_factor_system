---
name: factor-judge
description: 对评估结果进行 LLM 审判，决定录取/淘汰，执行录取并更新挖掘记忆
user_invocable: true
---

# 因子审判 — /judge

读取评估结果，对每个筛选通过的因子进行 6 维审判，执行录取，更新全部记忆。

## 第1步：查找待审判结果

扫描 `storage/candidates/` 目录：
- 找编号最大的 `batch_XXX_result.yaml`
- 如果没有结果文件 → 提示用户："没有待审判的结果。请先运行 `/execute` 评估候选。"

读取 `batch_XXX_result.yaml`。

## 第2步：LLM 审判（强制 — 不得跳过）

对每个 `screened` 因子，打印报告卡并做出判断：

```
=== 因子审判: {name} ===
表达式: {expression}
类别: {category}

预测力: IC={ic_mean:.4f}, ICIR={ic_ir:.2f}, 胜率={ic_win_rate:.1%}
  逐年: {ic_by_year}
稳健性: OOS衰减比={oos_decay_ratio:.2f}, 最差季度={worst_quarter_ic:.4f}, IC回撤={ic_max_drawdown:.4f}
经济性: 单调性IS={monotonicity_is:.2f}/OOS={monotonicity_oos:.2f}, 多空t={ls_tstat:.2f}, 符号一致={ic_sign_consistent}
衰减:   半衰期={half_life_days:.1f}天, 换手率={factor_turnover:.3f}
分布:   覆盖率={coverage:.1%}, 零值={zero_ratio:.1%}, 偏度={factor_skew:.2f}
唯一性: 最大库相关={max_lib_corr:.3f}({max_corr_factor_id}), 增量IC={incremental_ic:.4f}

判定: [录取 / 淘汰 / 替换 factor_XXX]
理由: [2-3句具体理由，引用报告卡中的数字]
```

### 红旗（通常应淘汰）

- `ic_sign_consistent = False` — IS/OOS 方向翻转
- `oos_decay_ratio < 0.3` — 严重过拟合
- `coverage < 0.5` — 覆盖率过低
- `monotonicity_oos` 与 `monotonicity_is` 符号相反
- `half_life_days < 1` — 信号存活不到一天

### 强信号（倾向录取）

- `ic_ir > 0.15` 且 `oos_decay_ratio > 0.7`
- `ls_tstat > 2.0` — 统计显著
- `monotonicity_is > 0.8` 且 `monotonicity_oos > 0.5`
- `incremental_ic > 0.02` — 真正的新信息
- 低 `expression_depth` + 高 IC — 奥卡姆剃刀

这些是**指导方针**而非硬规则。综合权衡所有维度做最终判断。

## 第3步：执行录取

对判定**录取**的因子：

```python
from mining.library import FactorLibrary
from mining.config import MiningConfig

lib = FactorLibrary(MiningConfig())
factor['metrics'] = {
    'ic_mean': report_card['ic_mean'],
    'ic_ir': report_card['ic_ir'],
    'ic_win_rate': report_card['ic_win_rate'],
    'ic_mean_oos': report_card['ic_mean_oos'],
    'ic_ir_oos': report_card['ic_ir_oos'],
    'quantile_returns': report_card['quantile_returns_is'],
    'ls_return': report_card['ls_return'],
    'monotonicity': report_card['monotonicity_is'],
}
lib.admit(factor)
```

对判定**替换**的因子：

```python
lib.replace(old_id, new_factor)
```

## 第4步：更新记忆（强制 — 不得跳过）

### 4a. 更新 `storage/memory/patterns.yaml`
- 录取因子 → 添加到 `recommended_directions`，包含成功率和示例因子
- 淘汰（高相关性）→ 添加到 `forbidden_regions`，包含相关性值和冲突因子
- 淘汰（低 IC）→ 添加到 `forbidden_regions`，包含 IC 值和原因
- 淘汰（算子错误）→ 在现有模式条目中注明

### 4b. 更新 `storage/memory/state.yaml`
- 因子库规模、平均 IC、各领域饱和度
- 挖掘统计：总批次数、总候选数、录取率

### 4c. 保存批次历史到 `storage/memory/history/batch_XXX.yaml`
包含：所有候选因子、录取/淘汰及原因、关键教训、工程发现

### 4d. 更新挖掘经验教训（如有新工程发现）
```
storage/memory/mining-lessons.md
```
添加任何新的算子发现、运行时错误、变通方法、管道 bug、市场洞察。

### 4e. 验证
更新后，重新读取 `patterns.yaml` 并确认：
- 没有重复的禁区
- 所有新发现已被记录
- 推荐方向反映当前证据

## 第5步：最终摘要

```
=== 批次 XXX 审判完成 ===
录取: N 个 [列出名称]
淘汰: M 个
替换: K 个
因子库规模: X/100
```
