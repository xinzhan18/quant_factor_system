---
name: quant-factor-idea
description: Use when working in the quant_factor_system repository and the user asks to run `/factor-idea`, `factor-idea`, or Phase 1 START and DESIGN for factor mining. This bridges to `.claude/skills/factor-idea/skill.md`, which remains the source of truth.
---

# Quant Factor Idea

Use this skill only inside the `quant_factor_system` repository.

## Workflow

1. Confirm `.claude/skills/factor-idea/skill.md` exists in the current repo.
2. Read `.claude/skills/factor-idea/skill.md` before doing Phase 1 work.
3. Follow its Python and LLM split exactly: direction selection, candidate design, validation, and manifest freeze.
4. Use the repo CLI commands referenced by that file instead of creating ad hoc substitutes.
5. If direction context or adjacent-scan rules matter, read the vault files named by the Claude skill.

## Boundaries

- Keep `.claude/skills/factor-idea/skill.md` as the single workflow definition.
- If code behavior differs from the skill text, surface the mismatch and prefer the safe code path.
