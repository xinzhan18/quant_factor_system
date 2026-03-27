---
name: factor-evaluate
description: 对单个 Qlib 因子表达式进行完整管道评估
user_invocable: true
---

# 因子评估

评估作为参数传入的因子表达式。

## 用法

```
/factor-evaluate Neg(Rank(Div(Sub($close, $vwap), $vwap)))
```

## 步骤

1. 使用 ExpressionValidator 验证表达式
2. 通过完整评估管道运行
3. 展示结果：IC、ICIR、分位数收益、与因子库的相关性

```bash
cd /Users/xinzhan/.openclaw/workspace/quant_factor_system
python -c "
from mining.evaluator import FactorMiningEvaluator
from mining.config import MiningConfig
import json

config = MiningConfig()
evaluator = FactorMiningEvaluator(config)
expression = '$ARGUMENTS'
candidates = [{'name': 'user_factor', 'expression': expression, 'category': 'other'}]
result = evaluator.evaluate_batch(candidates)

for c in result.admitted + result.rejected:
    print(f'表达式: {c[\"expression\"]}')
    if 'stage1' in c:
        print(f'第1阶段 IC: {c[\"stage1\"].get(\"ic_mean\", \"N/A\")}')
    if 'full_ic' in c:
        print(f'全量 IC: {c[\"full_ic\"].get(\"ic_mean\", \"N/A\")}')
    if 'stage3' in c:
        print(f'第3阶段: {json.dumps(c[\"stage3\"], indent=2, default=str)}')
"
```
