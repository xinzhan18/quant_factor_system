---
name: factor-evaluate
description: Evaluate a single Qlib factor expression through the full pipeline
user_invocable: true
---

# Factor Evaluation

Evaluate a factor expression passed as argument.

## Usage

```
/factor-evaluate Neg(Rank(Div(Sub($close, $vwap), $vwap)))
```

## Steps

1. Validate the expression using ExpressionValidator
2. Run it through the full evaluation pipeline
3. Display results: IC, ICIR, quantile returns, correlation with library

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
    print(f'Expression: {c[\"expression\"]}')
    if 'stage1' in c:
        print(f'Stage 1 IC: {c[\"stage1\"].get(\"ic_mean\", \"N/A\")}')
    if 'full_ic' in c:
        print(f'Full IC: {c[\"full_ic\"].get(\"ic_mean\", \"N/A\")}')
    if 'stage3' in c:
        print(f'Stage 3: {json.dumps(c[\"stage3\"], indent=2, default=str)}')
"
```
