---
name: refactor-scope-principle
description: When user says "no backward compat", plan as a full subsystem rebuild — not incremental patches on existing code
type: feedback
---

When the user context is "major refactor, no backward compat", plans must be written as subsystem rebuilds, not incremental file additions.

**Why:** User rejected a plan that tried to add Barra files alongside existing risk_model.py while preserving old interfaces. The user's project context is explicitly "delete all compat code, clean architecture." A plan that says "don't modify old file, do schema mapping in engine" is a compat pattern in disguise.

**How to apply:**
- Create new packages (e.g., `src/research/risk/`) not files alongside old ones
- Delete old implementations, don't wrap them
- Own the full schema — bucket computation belongs in the subsystem, not in downstream consumers
- Inject the engine, not individual protocol functions
- Write breaking changes explicitly in the plan
- All tests rewritten to new schema, no old key assertions preserved
