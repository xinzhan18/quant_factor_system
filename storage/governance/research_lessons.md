# Research Lessons — 研究经验与禁忌

> 每轮 /idea 和 /judge 前**必读**此文件。
> 新发现的经验教训直接追加到对应 section。

## Forbidden Patterns（禁止模式）

以下模式经过实验验证为无效或有害，**不要再尝试**：

（当前为空——随着迭代积累，judge 和 idea 会在这里记录失败模式）

<!-- 格式示例：
### FP001: $vwap 字段全为零
- **发现时间**: batch_001
- **现象**: 所有使用 $vwap 的表达式 IC ≈ 0，coverage = 0
- **原因**: 数据源未填充 vwap 字段
- **规则**: 任何包含 $vwap 的表达式自动 reject
- **状态**: active
-->

## Near-Miss Lessons（差一点但没过的教训）

跨 batch 反复出现的 near-miss 模式，帮助理解信号空间的边界：

（当前为空）

## Style Trap Warnings（风格陷阱）

看起来信号强但本质是风格暴露的因子类型：

（当前为空——batch_002 的 6 个因子全部有 vol/turnover 风格暴露，是首个信号）

## Operator/Expression Gotchas（表达式陷阱）

- `Max($open, $close)` — `Max` 是 rolling max 不是 element-wise max，对两个字段取 max 应该用 `If(Gt($open,$close),$open,$close)`
- `Rank(expr)` — `Rank` 需要窗口参数 N，截面 rank 应该用 `CsRank(expr)`
- `Neg(x)` — 未注册，用 `Mul(x, -1)` 替代
- `SMA(x, N)` — 未注册，用 `Mean(x, N)` 替代
