---
name: plan-must-close-the-loop
description: Plans must trace the full data flow from source through every consumer — not just define a module in isolation
type: feedback
---

Plans must trace the complete input→output→consumer chain, not just design a module.

**Why:** User rejected a risk subsystem plan 3 times because it designed the internal module well but failed to verify: (1) whether the pipeline could actually supply the required inputs, (2) whether the data flow through batch_runner → pipeline → judge_packet → CandidateEvidence → judge was complete, (3) whether domain ownership of evidence schemas was changing, (4) which other files beyond the new module needed modification.

**How to apply:**
- For every function in the plan, verify the caller exists and can supply the parameters
- For every output, trace it through all downstream consumers to the final verdict/report
- List ALL files that need modification (not just the new module), including __init__.py, test files, runner files
- When a subsystem self-computes derived values (like buckets), explicitly state this is intentional domain ownership shift
- When inputs come from upstream, verify the upstream actually produces them in the expected format (MultiIndex vs flat, column names, date ranges)
