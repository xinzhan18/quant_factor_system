---
name: quant-factor-consolidate
description: Use when working in the quant_factor_system repository and the user asks to run `/factor-consolidate`, `factor-consolidate`, or Phase 5 memory consolidation. This bridges to `.claude/skills/factor-consolidate/skill.md`, which remains the source of truth.
---

# Quant Factor Consolidate

Use this skill only inside the `quant_factor_system` repository.

## Workflow

1. Confirm `.claude/skills/factor-consolidate/skill.md` exists in the current repo.
2. Read that file before starting consolidation work.
3. Follow its division of labor:
   - Python handles prechecks, packet generation, index refresh, state update, and commit
   - the agent handles rewrite steps for the target markdown files
4. Respect the packet sandbox and atomic rollback expectations described by the Claude skill.

## Boundaries

- Do not duplicate the consolidation algorithm here.
- Keep `.claude/skills/factor-consolidate/skill.md` as the single maintained workflow description.
- If git cleanliness or batch-state preconditions are not met, stop and report them instead of improvising.
