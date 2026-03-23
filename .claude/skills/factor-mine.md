---
name: factor-mine
description: Run one Ralph Loop iteration — retrieve memory, generate candidates, evaluate, update library and memory
user_invocable: true
---

# Factor Mining — Ralph Loop

Run one complete mining iteration. **Every step is mandatory — do NOT skip any step.**

## Step 1: Load ALL Memory (MANDATORY — DO NOT SKIP)

You MUST read ALL of the following files and absorb their content before proceeding:

### 1a. Engineering Memory (pitfalls, broken operators, workarounds)
```
~/.claude/projects/-Users-xinzhan--openclaw-workspace-quant-factor-system/memory/mining-exploration.md
```

### 1b. Experience Memory (library state, patterns, insights)
```
mining/memory/state.yaml
mining/memory/patterns.yaml
mining/memory/insights.yaml
```

### 1c. Recent Batch History (last 3 batches)
```
ls mining/memory/history/
```
Read the most recent 3 batch history files to understand what was tried and what failed.

### 1d. Current Factor Library
```
mining/library/library.yaml
```

## Step 2: Context Summary (MANDATORY — print before generating)

After loading all memory, you MUST output a structured context summary. This proves you have absorbed the memory and prevents repeating past mistakes.

**Print this summary to the user:**

```
=== Mining Context (Batch XXX) ===

LIBRARY STATUS:
- Size: X/100 factors
- Factors: [list each factor_id: name, category, IC]

OPERATOR STATUS:
- Working: [list from exploration memory]
- Broken: [list from exploration memory]
- Workarounds: [list each]

FIELD STATUS:
- Working: [list]
- Broken: [list]

FORBIDDEN REGIONS (from patterns.yaml):
- [list each direction + reason]

RECOMMENDED DIRECTIONS (from patterns.yaml):
- [list each pattern + success_rate + notes]

KEY INSIGHTS (from insights.yaml):
- [list the top 5 most relevant insights for this batch]

LAST 3 BATCH RESULTS:
- Batch N: X/8 admitted, key finding: ...
- Batch N-1: ...
- Batch N-2: ...

CANDIDATE STRATEGY:
Based on the above, this batch will explore:
1. [direction + rationale]
2. [direction + rationale]
...
```

**CRITICAL**: If any candidate expression uses a broken operator, broken field, or falls into a forbidden region, STOP and redesign before proceeding.

## Step 3: Generate Candidates

Based on the Context Summary, generate **8 candidate factor expressions** using Qlib Alpha expression syntax.

**Rules:**
- Operators: ONLY use operators listed as "Working" in your Context Summary
- Fields: ONLY use fields listed as "Working" in your Context Summary
- Workarounds: Apply workarounds from exploration memory (e.g., Mul(x,-1) for Neg)
- Forbidden: Cross-check EVERY candidate against forbidden regions — reject before evaluation
- Recommended: Prioritize recommended directions with high success_rate
- Category must be one of: vwap, momentum, volatility, volume, regime, efficiency, distribution, trend, candlestick, intraday_agg, other
- Expression depth must not exceed 10
- Avoid symmetric IfElse (x vs -x) — produces identical factors regardless of condition

**Validation checklist** (check each candidate):
- [ ] All operators are in the working list?
- [ ] All fields are in the working list?
- [ ] Not in a forbidden region?
- [ ] Not a near-duplicate of an existing library factor?
- [ ] Expression depth ≤ 10?

Write candidates to `mining/candidates/batch_XXX.yaml`:

```yaml
batch_id: "batch_XXX"
timestamp: "YYYY-MM-DDTHH:MM:SS"
candidates:
  - name: "descriptive_name"
    expression: "Qlib_expression_here"
    category: "category"
    rationale: "Why this factor should work"
```

## Preprocessing (Automatic)

The evaluator automatically preprocesses factor values and returns before IC calculation. **You do NOT need to add Winsorize/Zscore/Scale to factor expressions** — the pipeline handles this uniformly:

1. **Universe filtering**: Suspended stocks (volume=0) and limit-up/down stocks are excluded
2. **Factor cleaning**: inf→NaN, MAD winsorization (5×), zscore standardization
3. **Return masking**: Forward returns of untradable stocks are set to NaN

Optional neutralization (market cap / industry) can be enabled via `MiningConfig(neutralize_mode="market_cap")`.

All preprocessing config is in `MiningConfig`:
- `filter_suspend` / `filter_limit` — universe filters (default: True)
- `winsorize_method` / `winsorize_n` — outlier treatment (default: "mad" / 5.0)
- `standardize_method` — "zscore" or "rank" (default: "zscore")
- `neutralize_mode` — "none", "market_cap", "industry", "both" (default: "none")

## Step 4: Evaluate

**IMPORTANT**: Write the evaluation script to a `.py` file, do NOT use `python -c` or heredoc.

Create `run_batch_XXX.py`:

```python
"""Batch XXX evaluation"""
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

    # Load universe (D.instruments returns dict, must resolve to list)
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

    # Print results
    logger.info(f"Admitted: {len(result.admitted)}, Rejected: {len(result.rejected)}")
    for f in result.admitted:
        s1 = f.get('stage1', {})
        s3 = f.get('stage3', {})
        logger.info(f"  ADMIT {f['name']}: IC={s1.get('ic_mean',0):.4f}, OOS={s3.get('ic_mean_oos','?')}")
    for f in result.rejected:
        s1 = f.get('stage1', {})
        logger.info(f"  REJECT {f['name']}: IC={s1.get('ic_mean','?')}")

    # Save results
    output = {
        'batch_id': batch['batch_id'],
        'timestamp': datetime.now().isoformat(),
        'admitted': [{k: v for k, v in f.items() if not k.startswith('_')} for f in result.admitted],
        'rejected': [{k: v for k, v in f.items() if not k.startswith('_')} for f in result.rejected],
        'replacements': [{k: v for k, v in f.items() if not k.startswith('_')} for f in result.replacements],
    }
    with open('mining/candidates/batch_XXX_result.yaml', 'w') as fp:
        yaml.dump(output, fp, default_flow_style=False, allow_unicode=True)


if __name__ == '__main__':
    main()
```

Then run: `python3 run_batch_XXX.py`

Clean up the script after use: `rm run_batch_XXX.py`

## Step 5: Library Update

For each admitted factor:

1. Verify the factor is NOT a pipeline loophole (check n_days > 100, quantile returns not NaN)
2. Add to library:
```python
from mining.library import FactorLibrary
from mining.config import MiningConfig

lib = FactorLibrary(MiningConfig())
lib.admit(factor_dict)
```
3. Manually fix `ic_mean` in `library.yaml` if null (known bug: evaluator stores IC under `full_ic.ic_mean`)
4. Write detailed `mining/library/factors/factor_XXX.yaml` with full metrics

For replacements, use `lib.replace(old_id, new_factor_dict)`.

## Step 6: Memory Update (MANDATORY — DO NOT SKIP)

After evaluation, update ALL memory files. This is how the next iteration learns from this one.

### 6a. Update `mining/memory/patterns.yaml`
- Admitted factors → add to `recommended_directions` with success_rate and example_factors
- Rejected (high corr) → add to `forbidden_regions` with correlation value and correlated factor
- Rejected (low IC) → add to `forbidden_regions` with IC value and reason
- Rejected (operator error) → note in existing pattern entries

### 6b. Update `mining/memory/insights.yaml`
- New empirical findings (e.g., "X operator not registered", "Y factor type always correlates with Z")
- Updated confidence levels based on repeated evidence
- Remove or downgrade insights proven wrong

### 6c. Update `mining/memory/state.yaml`
- Library size, avg_ic, domain saturation counts
- Mining stats: total_batches, total_candidates, yield_rate

### 6d. Save batch history to `mining/memory/history/batch_XXX.yaml`
Include: all candidates, admitted/rejected with reasons, key_learnings, engineering_findings

### 6e. Update exploration memory (if new engineering findings)
```
~/.claude/projects/-Users-xinzhan--openclaw-workspace-quant-factor-system/memory/mining-exploration.md
```
Add any new operator discoveries, runtime errors, workarounds, pipeline bugs.

### 6f. Verification
After updating, re-read `patterns.yaml` and confirm:
- No duplicate forbidden regions
- All new findings are captured
- Recommended directions reflect current evidence
