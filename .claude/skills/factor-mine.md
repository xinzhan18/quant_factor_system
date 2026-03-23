---
name: factor-mine
description: Run one Ralph Loop iteration — retrieve memory, generate candidates, evaluate, update library and memory
user_invocable: true
---

# Factor Mining — Ralph Loop

Run one complete mining iteration:
1. Load exploration memory + experience memory
2. Generate candidate factors
3. Evaluate candidates
4. Update library and memory

## Step 0: Load Exploration Memory

**MUST READ FIRST** — contains critical engineering pitfalls and known issues:

```
~/.claude/projects/-Users-xinzhan--openclaw-workspace-quant-factor-system/memory/mining-exploration.md
```

Key things to remember:
- **Qlib multiprocessing**: Scripts MUST use `multiprocessing.set_start_method('fork', force=True)` + `if __name__ == '__main__':` guard
- **D.instruments('all')** returns dict, not list — use `custom_universe` instead
- **Broken operators**: `Correlation` is NOT registered. Use Rsquare or manual Cov formula
- **Broken fields**: `$amount` and `$vwap` are zero — do NOT use them in expressions
- **Evaluation scripts**: MUST be written to a .py file and run with `python3 file.py`, NOT inline `python -c` or heredoc (multiprocessing will crash)

## Step 1: Retrieve Experience Memory

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
- Confirmed working operators: Add, Sub, Mul, Div, Abs, Log, Power, Sign, Neg, Mean, Std, Var, Skew, Kurt, Med, Sum, Rank, EMA, SMA, WMA, Ref, Delta, TsRank, TsMax, TsMin, Slope, Rsquare, Resi, If, Greater, Less
- **Do NOT use**: Correlation (not registered), SignedPower/Tanh/Scale (untested)
- Valid fields: $open, $high, $low, $close, $volume, $returns (and minute-agg fields if synced)
- **Do NOT use**: $amount (all zeros), $vwap (all zeros)
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

## Step 3: Evaluate

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
4. For rejected (low IC): add to `patterns.yaml` forbidden_regions with reason
5. Update `state.yaml` with new library stats
6. Distill strategic insights and update `insights.yaml`
7. Save batch summary to `mining/memory/history/batch_XXX.yaml`
8. **Update exploration memory** at `~/.claude/projects/.../memory/mining-exploration.md` with any new engineering findings

Write updates using the Write tool to the appropriate YAML files.
