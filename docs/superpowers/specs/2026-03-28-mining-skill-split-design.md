# Mining Skill Split Design

Split the monolithic `factor-mine.md` skill into 3 independent sub-skills plus a lightweight orchestrator.

## Problem

`factor-mine.md` is 259 lines covering 6 distinct steps. This creates issues:
- Cannot rerun a single phase (e.g., re-judge with different criteria) without re-executing the whole loop
- A single massive prompt overwhelms context — the LLM must hold memory loading, expression generation, CLI execution, and judgment criteria simultaneously
- Adding new capabilities (e.g., a different idea generation strategy) requires modifying the monolithic file

## Design

### File Structure

```
.claude/skills/
├── factor-mine.md       ← /mine — orchestrator, chains idea → execute → judge
├── factor-idea.md       ← /idea [optional direction] — generate candidates
├── factor-execute.md    ← /execute — run CLI evaluation
└── factor-judge.md      ← /judge — LLM judgment + admission + memory update
```

### State Passing: File Convention

No parameters needed between skills. Each skill discovers its input by scanning `mining/candidates/`:

| Skill | Finds Input By | Produces |
|-------|---------------|----------|
| `/idea` | N/A (generates new) | `batch_XXX.yaml` |
| `/execute` | Highest-numbered `batch_XXX.yaml` without `_result.yaml` | `batch_XXX_result.yaml` |
| `/judge` | Most recent `batch_XXX_result.yaml` | Library updates + memory updates |

Batch numbering: scan existing files, take max number + 1.

### Invocation

| Command | Behavior |
|---------|----------|
| `/mine` | Full Ralph Loop: idea → execute → judge |
| `/mine 探索波动率因子` | Full loop, idea phase prioritizes given direction |
| `/idea` | Generate candidates only (autonomous direction) |
| `/idea momentum方向` | Generate candidates prioritizing given direction |
| `/execute` | Evaluate most recent unevaluated batch |
| `/judge` | Judge most recent result file |

---

## Skill 1: `/idea` — Factor Idea Generation

**File**: `.claude/skills/factor-idea.md`

### Responsibilities
1. Determine batch number (scan `mining/candidates/`, max + 1)
2. Load all memory (mandatory):
   - `mining/memory/mining-lessons.md`
   - `mining/memory/state.yaml`
   - `mining/memory/patterns.yaml`
   - `mining/memory/history/` (latest 3 batches)
   - `mining/library/library.yaml`
3. Print structured context summary
4. Generate 8 candidate factor expressions
   - If user provides direction hint → at least 4 candidates explore that direction
   - Validation checklist: operators available, fields available, not in forbidden zone, not duplicate, depth ≤ 10
5. Write `mining/candidates/batch_XXX.yaml`
6. Print candidate summary, prompt user to continue

### Inline Reference (self-contained)
- Available categories list
- Expression rules (depth limit, no symmetric IfElse)
- Preprocessing note (no need for Winsorize/Zscore in expressions)
- Batch YAML format template
- Context summary template

---

## Skill 2: `/execute` — Factor Evaluation

**File**: `.claude/skills/factor-execute.md`

### Responsibilities
1. Scan `mining/candidates/` for highest-numbered batch without `_result.yaml`
   - If none found → prompt "No pending batch. Run /idea first."
2. Run CLI: `python3 -m mining batch mining/candidates/batch_XXX.yaml`
   - No `--admit` flag
3. Wait for completion, verify `batch_XXX_result.yaml` exists
4. Print evaluation summary (screened/rejected/replacement counts)
5. Prompt user to continue

### Inline Reference
- CLI parameters (`--train-start`, `--test-start`, `--screening-size`)
- Preprocessing configuration (MiningConfig options)

---

## Skill 3: `/judge` — LLM Judgment & Memory Update

**File**: `.claude/skills/factor-judge.md`

### Responsibilities

**Phase A — Judgment:**
1. Find most recent `batch_XXX_result.yaml`
   - If none → prompt "No results to judge. Run /execute first."
2. Read result file
3. For each `screened` factor, print 6-dimension report card and make decision:
   - Format: structured report card template
   - Red flags / strong signals guidelines (inline)
   - Decision: Admit / Reject / Replace factor_XXX

**Phase B — Admission:**
4. Execute admission for accepted factors:
   - `lib.admit(factor)` / `lib.replace(old_id, new_factor)`

**Phase C — Memory Update (mandatory):**
5. Update all memory files:
   - `patterns.yaml` (recommended/forbidden directions)
   - `state.yaml` (library size, statistics)
   - `history/batch_XXX.yaml` (batch history)
   - `mining-lessons.md` (if new engineering discoveries)
6. Verify: re-read `patterns.yaml`, confirm no duplicates

### Inline Reference
- Report card template (6 dimensions, all field names)
- Red flags list
- Strong signals list
- Admission code template
- Memory update rules

---

## Skill 4: `/mine` — Orchestrator

**File**: `.claude/skills/factor-mine.md` (rewritten)

Lightweight orchestrator, no business logic:

```
1. Pass user arguments to idea phase
2. Execute all /idea steps
3. Execute all /execute steps
4. Execute all /judge steps
```

If any phase fails, stop there. The orchestrator simply references the three sub-skills by describing their steps inline (since Claude Code skills cannot "include" other skills).

### Implementation Note

Since Claude Code skills cannot programmatically invoke other skills, the orchestrator contains the full step descriptions from all three sub-skills. The difference from the current monolithic approach: each sub-skill ALSO exists as a standalone file, so users can invoke any phase independently.

---

## Content Allocation

What goes where (avoiding duplication where possible, accepting minimal duplication for independence):

| Content | idea | execute | judge | mine |
|---------|------|---------|-------|------|
| Memory loading instructions | Full | — | — | References idea |
| Context summary template | Full | — | — | References idea |
| Expression generation rules | Full | — | — | References idea |
| Categories list | Full | — | — | References idea |
| Preprocessing note | Brief | Brief | — | References idea |
| CLI parameters | — | Full | — | References execute |
| Report card template | — | — | Full | References judge |
| Red flags / strong signals | — | — | Full | References judge |
| Admission code | — | — | Full | References judge |
| Memory update rules | — | — | Full | References judge |
| Batch YAML format | Full | — | — | References idea |

Estimated sizes: idea ~120 lines, execute ~50 lines, judge ~140 lines, mine ~80 lines (total ~390 vs current 259, but each piece is focused and independently useful).

---

## Verification

After implementation:
1. `/idea` produces a valid `batch_XXX.yaml` and context summary
2. `/execute` finds the batch, runs CLI, produces `_result.yaml`
3. `/judge` reads result, prints report cards, updates memory
4. `/mine` chains all three seamlessly
5. Each sub-skill works independently when called alone
6. No skill references another skill file — each is self-contained
