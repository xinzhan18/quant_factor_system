---
name: factor-mine
description: Run one Ralph Loop iteration — retrieve memory, generate candidates, evaluate, update library and memory
user_invocable: true
---

# Factor Mining — Ralph Loop

Run one complete mining iteration:
1. Retrieve Experience Memory
2. Generate candidate factors
3. Evaluate candidates
4. Update library and memory

## Step 1: Retrieve Memory

Read the Experience Memory files to understand current state:

```bash
cat mining/memory/state.yaml
cat mining/memory/patterns.yaml
cat mining/memory/insights.yaml
```

Use these to compose your search context for factor generation.

## Step 2: Generate Candidates

Based on the Memory context, generate **8 candidate factor expressions** using Qlib Alpha expression syntax.

**Rules:**
- Each expression must use only these operators: Add, Sub, Mul, Div, Abs, Log, Power, Sign, Neg, Mean, Std, Var, Skew, Kurt, Med, Sum, Rank, EMA, SMA, WMA, Ref, Delta, TsRank, TsMax, TsMin, Slope, Rsquare, Resi, If, Greater, Less, Correlation, SignedPower, Tanh, Scale
- Each expression must reference only valid fields: $open, $high, $low, $close, $volume, $amount, $vwap, $returns (and minute-agg fields if available)
- Category must be one of: vwap, momentum, volatility, volume, regime, efficiency, distribution, trend, candlestick, intraday_agg, other
- Avoid forbidden regions listed in patterns.yaml
- Prioritize recommended directions from patterns.yaml
- Expression depth must not exceed 10

Write candidates to `mining/candidates/batch_XXX.yaml` using this format:

```yaml
batch_id: "batch_XXX"
timestamp: "YYYY-MM-DDTHH:MM:SS"
candidates:
  - name: "descriptive_name"
    expression: "Qlib_expression_here"
    category: "category"
    rationale: "Why this factor should work"
```

## Step 3: Evaluate

Run the evaluation pipeline:

```bash
cd /Users/xinzhan/.openclaw/workspace/quant_factor_system
python -c "
from mining.evaluator import FactorMiningEvaluator
from mining.config import MiningConfig
import yaml

config = MiningConfig()
evaluator = FactorMiningEvaluator(config)

with open('mining/candidates/batch_XXX.yaml') as f:
    batch = yaml.safe_load(f)

result = evaluator.evaluate_batch(batch['candidates'])
print(f'Admitted: {len(result.admitted)}')
print(f'Rejected: {len(result.rejected)}')
print(f'Replacements: {len(result.replacements)}')

# Save results
import json
output = {
    'admitted': result.admitted,
    'rejected': result.rejected,
    'replacements': result.replacements,
}
with open('mining/candidates/batch_XXX_result.yaml', 'w') as f:
    yaml.dump(output, f, default_flow_style=False, allow_unicode=True)
"
```

## Step 4: Library Update

For each admitted factor, add to the library:

```python
from mining.library import FactorLibrary
from mining.config import MiningConfig

lib = FactorLibrary(MiningConfig())
# For each admitted factor:
# lib.admit(factor_dict)
```

For replacements, use `lib.replace(old_id, new_factor_dict)`.

## Step 5: Memory Evolution

Analyze the batch results and update Experience Memory:

1. Read batch results
2. For successful factors: add to `patterns.yaml` recommended_directions
3. For rejected (high correlation): add to `patterns.yaml` forbidden_regions
4. Update `state.yaml` with new library stats
5. Distill strategic insights and update `insights.yaml`
6. Save batch summary to `mining/memory/history/batch_XXX.yaml`

Write updates using the Write tool to the appropriate YAML files.
