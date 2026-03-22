---
name: factor-library
description: View and manage the factor library
user_invocable: true
---

# Factor Library

View and manage admitted factors.

## Commands

- `/factor-library` or `/factor-library status` — Show library summary
- `/factor-library detail <id>` — Show factor details
- `/factor-library remove <id>` — Remove a factor (with confirmation)

## Status View

```bash
cd /Users/xinzhan/.openclaw/workspace/quant_factor_system
python -m mining.cli library
```

Also read `mining/library/library.yaml` to show the full index.

## Detail View

Read `mining/library/factors/factor_<id>.yaml` to show full factor details including:
- Expression
- Category
- All metrics (IC, ICIR, quantile returns)
- Financial logic
- Correlation with other library factors
