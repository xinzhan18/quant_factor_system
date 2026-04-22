---
name: quant-factor-report
description: Use when working in the quant_factor_system repository and the user asks to run `/factor-report`, `factor-report`, or write a factor deep report during Phase 4 archive. This bridges to `.claude/skills/factor-report/skill.md`, which remains the source of truth.
---

# Quant Factor Report

Use this skill only inside the `quant_factor_system` repository.

## Workflow

1. Confirm `.claude/skills/factor-report/skill.md` exists in the current repo.
2. Read it before writing any `vault/factors/F{id}.md` report.
3. Follow its sandbox contract exactly:
   - read only the packet and structured report data it permits
   - write only the target factor markdown
   - do not recompute metrics or read forbidden files
4. Use only chart names and scalar values allowed by the packet and structured report payload.

## Boundaries

- Keep the detailed report template in the Claude skill, not here.
- If code, packet contents, and the skill disagree, prefer the stricter data-boundary interpretation and cite the mismatch.
