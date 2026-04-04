---
name: factor-judge
description: 对评估结果进行 LLM 审判，决定录取/淘汰，按方向更新挖掘记忆
user_invocable: true
---

# 因子审判 — /judge

读取评估结果，对每个筛选通过的因子进行 6 维审判，执行录取，按方向维度更新记忆。

## 第1步：查找待审判结果

扫描 `storage/mining/candidates/` 目录：
- 找编号最大的 `batch_XXX_result.yaml`
- 如果没有结果文件 → 提示用户："没有待审判的结果。请先运行 `/execute` 评估候选。"

读取 `batch_XXX_result.yaml`。

## 第2步：LLM 审判（强制 — 不得跳过）

对每个 `screened` 因子，打印报告卡并做出判断：

```
=== 因子审判: {name} ===
表达式: {expression}
类别: {category}
方向: {direction}

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

### Hard Gates（代码强制 — 已在评估管道中自动执行）

以下条件由 `evaluator._apply_hard_gates()` 强制执行。触发任一条件的因子**不会出现在 screened 列表中**：

| 条件 | 阈值 | 配置项 |
|------|------|--------|
| `ic_sign_consistent = False` | — | 不可配置 |
| `oos_decay_ratio < X` | 0.2 | `hard_gate_oos_decay_min` |
| `coverage < X` | 0.3 | `hard_gate_coverage_min` |
| `monotonicity` IS/OOS 符号相反 | — | 不可配置 |
| `abs(ic_mean_oos) < X` | 0.008 | `hard_gate_ic_oos_min` |

如果在 `screened` 中仍看到触发上述条件的因子，说明代码层 hard gate 未生效，必须手动拒绝。

### 红旗（LLM 裁量 — Hard Gate 之上的额外判断）

- `oos_decay_ratio < 0.5` — 衰减较大（0.2 以下已被 hard gate 拦截）
- `coverage < 0.5` — 覆盖率偏低（0.3 以下已被 hard gate 拦截）
- `half_life_days < 1` — 信号存活不到一天

### 强信号（倾向录取）

- `ic_ir > 0.15` 且 `oos_decay_ratio > 0.7`
- `ls_tstat > 2.0` — 统计显著
- `monotonicity_is > 0.8` 且 `monotonicity_oos > 0.5`
- `incremental_ic > 0.02` — 真正的新信息
- 低 `expression_depth` + 高 IC — 奥卡姆剃刀

这些是**指导方针**而非硬规则。综合权衡所有维度做最终判断。

## 第3步：执行录取

## 强制步骤：录取前写 admission_history

```python
from mining.memory import ExperienceMemory
from mining.config import MiningConfig

mem = ExperienceMemory(MiningConfig())
mem.save_admission_history(batch_id, {
    'factor_id': factor['factor_id'],
    'name': factor['name'],
    'expression': factor['expression'],
    'decision': 'admit',  # or 'replace' or 'reject'
    'reason': '...',
    'metrics': report_card,
})
```

此步骤不可跳过。必须在 `lib.admit()` / `lib.replace()` 之前执行。

---

对判定**录取**的因子：

```python
from mining.registry import FactorLibrary
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
# admit() 会自动从 pickle 缓存加载因子值并写入 DB，不需要手动传 _factor_values
```

对判定**替换**的因子：

```python
lib.replace(old_id, new_factor)
# replace() 同样自动从 pickle 缓存加载因子值
```

#### Python 因子录取

对 `source: python` 的因子，向 `lib.admit()` 传递以下额外字段：
- `source`: "python"
- `code`: 因子代码体
- `logic_id`: 市场逻辑 ID
- `lineage`: `{"parents": [...], "mutation_type": "genesis|macro|crossover", "generation": N}`
- `params`: 优化后的参数值
- `param_space`: 参数搜索范围

## 第4步：Direction Feedback（强制 — 不得跳过）

### 4a. 按方向聚合结果

读取 `batch_XXX.yaml`（原始候选文件），提取每个候选的 `direction` 字段。将结果按方向分组：

```
=== 方向反馈 ===
方向 williams_r_mutation: 3个候选, 1个录取(IC=0.055), 2个淘汰
方向 alpha191_batch1: 3个候选, 0个录取, 最好IC=0.018
方向 trend_new: 2个候选, 0个录取, 最好IC=0.008
```

如果候选文件中没有 `direction` 字段（旧格式兼容），根据因子名称和类别推断方向，或跳过方向反馈。

### 4b. 更新方向文件

对每个参与本轮的方向，更新 `storage/mining/memory/directions/{方向名}.md`：

**Frontmatter 更新：**
- `attempts`: +1
- `best_ic`: 如果本轮有更好的 IC，更新
- `last_batch`: 当前批次编号

**Body 追加（Candidate History 部分）：**
```
- batch_XXX (YYYY-MM-DD): N个候选, M个录取
  - admitted: [因子名 IC=xxx, ...]
  - rejected: [因子名 IC=xxx 原因, ...]
```

### 4c. 自动状态流转

对每个方向，检查并执行状态流转：

| 条件 | 转换 |
|------|------|
| 本轮有录取 | 维持 `active`，如果 priority 不是 high 则提升为 high |
| 0 录取但最好 IC > 0.02 | 维持 `active` |
| 连续 2 轮 0 录取且最好 IC < 0.02 | → `exhausted` |
| 累计 3 轮 0 录取 | → `dead` |

"连续轮数"从方向文件的 Candidate History 部分计算。

### 4d. 更新 directions.yaml 索引

读取所有方向文件的 frontmatter，重建 `storage/mining/memory/directions.yaml`。

或者使用 Python：
```python
from mining.memory import ExperienceMemory
from mining.config import MiningConfig

mem = ExperienceMemory(MiningConfig())
# update_direction 会自动同步索引
mem.update_direction("方向名", status="exhausted", attempts=3, last_batch="batch_XXX")
```

### 4e. 更新 state.yaml

更新全局统计：
- `library.size`, `library.avg_ic`
- `mining.total_batches` +1, `mining.total_candidates` +N, `mining.total_admitted` +M
- `mining.yield_rate` 重算
- `mining.last_batch_time`

**生成 next_round_hint：**
```yaml
next_round_hint: "williams_r 变异录取1个(IC=0.055)，继续 rank 变换。alpha191 本批全灭(best IC=0.018)，尝试下一组。trend 方向接近 dead(连续2轮0录取)。"
```

### 4f. 保存批次历史

保存到 `storage/mining/memory/history/batch_XXX.yaml`：

```yaml
batch_id: batch_XXX
timestamp: "YYYY-MM-DDTHH:MM:SS"
candidates: 8
admitted: N
rejected: M
replacements: K
yield_rate: N/8

direction_summary:
  - direction: williams_r_mutation
    candidates: 3
    admitted: 1
    best_ic: 0.055
  - direction: alpha191_batch1
    candidates: 3
    admitted: 0
    best_ic: 0.018

rejected_summary:
  - name: factor_name
    reason: "Stage X reject: ..."

key_learnings:
  - "..."
```

### 4g. 更新挖掘经验教训（如有新工程发现）

如果本轮遇到了新的工程问题、算子发现、或市场洞察，追加到：
```
storage/mining/memory/mining-lessons.md
```

### 4j. Logic Feedback

审判完所有因子后，更新市场逻辑统计：
```python
from mining.logic import MarketLogicLibrary
logic_lib = MarketLogicLibrary("storage/mining/logic")
# 对本批次中的每个 logic_id：
logic_lib.update_stats(logic_id,
    factors_generated=N_generated,
    factors_admitted=N_admitted,
    best_ic=max_ic,
    rounds_without_admit=0 if N_admitted > 0 else current+1)
# 如果 rounds_without_admit >= 3：标记为 saturated
if rounds_without_admit >= 3:
    logic_lib.update_status(logic_id, "saturated")
```

### 4k. Forbidden Region 自动检测

如果相同的表达式模式在多个批次中被拒绝 3 次以上，将其加入禁区：
```python
from mining.memory import ExperienceMemory
mem = ExperienceMemory(config)
mem.add_forbidden(pattern, reason)
```

### 4l. 谱系记录

对每个候选（录取或淘汰），记录其谱系：
- Genesis 因子：`parents: [], mutation_type: "genesis"`
- 变异因子：`parents: [parent_id], mutation_type: "macro"`
- 交叉因子：`parents: [id1, id2], mutation_type: "crossover"`

### 4h. 清理缓存

删除 evaluate 阶段生成的 pickle 缓存文件（因子值已写入 DB，不再需要）：

```bash
rm -f storage/mining/candidates/batch_XXX_values.pkl
```

### 4i. 验证

更新后，重新读取 `directions.yaml` 并确认：
- 状态流转正确
- 所有参与方向已更新
- next_round_hint 反映本轮结果

## 第5步：最终摘要

```
=== 批次 XXX 审判完成 ===
录取: N 个 [列出名称]
淘汰: M 个
替换: K 个
因子库规模: X/100

方向更新:
- [方向1]: active → active (录取1个)
- [方向2]: active → exhausted (连续2轮0录取)
- [方向3]: new → dead (探针无信号)
```
