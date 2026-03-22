---
name: memory-review
description: Review and optionally adjust the Experience Memory
user_invocable: true
---

# Memory Review

Review the current state of Experience Memory and suggest adjustments.

## Steps

1. Read all memory files
2. Summarize current state
3. Identify potential improvements
4. Ask user before making changes

Read the following files:
- `mining/memory/state.yaml`
- `mining/memory/patterns.yaml`
- `mining/memory/insights.yaml`

List recent batch history from `mining/memory/history/`.

Present a summary to the user showing:
- Library size and target
- Domain saturation across categories
- Number of recommended directions vs forbidden regions
- Mining yield rate trends
- Key insights

Ask the user if they want to:
- Add/remove recommended directions
- Add/remove forbidden regions
- Update insights
- Adjust domain saturation assessments
