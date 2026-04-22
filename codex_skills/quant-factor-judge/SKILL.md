---
name: quant-factor-judge
description: Use when working in the quant_factor_system repository and the user asks to run `/factor-judge`, `factor-judge`, or Phase 3 JUDGE for a mining batch. This bridges to `.claude/skills/factor-judge/skill.md` plus its `candidate-rubric.md`, which remain the source of truth.
---

# Quant Factor Judge

Use this skill only inside the `quant_factor_system` repository.

## Workflow

1. Confirm both files exist:
   - `.claude/skills/factor-judge/skill.md`
   - `.claude/skills/factor-judge/candidate-rubric.md`
2. Read `skill.md` first for the main-agent flow.
3. Read `candidate-rubric.md` whenever doing per-candidate judgment work.
4. Use the repo's Python `pre-hint` and `audit` commands exactly as prescribed by the Claude skill.
5. Treat `_hints.yaml` and the audited markdown outputs as the controlled interface; do not bypass that contract.

## Boundaries

- Do not restate the full rubric here.
- Keep the Claude files as the single maintained judge specification.
- If audit rules in code and skill text diverge, cite the concrete mismatch and preserve audit compliance.
