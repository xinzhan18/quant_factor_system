---
name: quant-factor-mine
description: Use when working in the quant_factor_system repository and the user asks to run `/factor-mine`, `factor-mine`, or the autonomous 5-phase factor-mining loop. This is a thin bridge to `.claude/skills/factor-mine/skill.md`, which remains the source of truth.
---

# Quant Factor Mine

Use this skill only inside the `quant_factor_system` repository.

## Workflow

1. Confirm `.claude/skills/factor-mine/skill.md` exists in the current repo.
2. Read `.claude/skills/factor-mine/skill.md` before taking action.
3. Treat that Claude skill file as the business source of truth for the mine loop.
4. Load subordinate Claude skill files when the mine flow delegates to them:
   - `.claude/skills/factor-idea/skill.md`
   - `.claude/skills/factor-judge/skill.md`
   - `.claude/skills/factor-report/skill.md`
   - `.claude/skills/factor-consolidate/skill.md`
5. Prefer the existing Python CLI and repo code paths named by the Claude skill. Do not invent alternative orchestration.
6. If the Claude skill and code disagree, cite concrete file paths and follow code-safe behavior.

## Boundaries

- Do not duplicate the mine procedure in this wrapper.
- Do not assume Codex can natively execute Claude slash-skills; read the repo files and perform the steps directly.
- Keep `.claude/skills/` as the single maintained workflow description.
