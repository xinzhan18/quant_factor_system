# Factor Mining System Redesign

## Problem

The current `/idea` skill is a single-step operation: read flat memory files, then ask LLM to generate 8 candidate expressions within constraints. This has three fundamental problems:

1. **No strategic judgment** — every round does the same thing (generate 8 candidates) with no decision about *what kind* of exploration to pursue
2. **No external knowledge** — relies entirely on LLM's built-in knowledge + accumulated memory; doesn't search papers, factor libraries, or community resources
3. **No data-driven direction filtering** — generates 8 candidates blind, often resulting in 0/8 admission (batch_018: 8 novel constructs, all rejected)
4. **Flat memory** — patterns.yaml is a growing list with no per-direction lifecycle management; judge appends entries but can't answer "should we keep exploring this direction?"

Evidence: 270 candidates evaluated, 24 admitted (8.9% overall). Last batch 0/8. OHLCV daily signal space near exhaustion at current approach.

## Solution

Restructure `/mine` from `idea → execute → judge` into a five-phase pipeline with data-driven direction selection and per-direction memory tracking.

```
Strategy → Probe → Decide → Execute → Judge
```

## Detailed Design

### Phase 1: Strategy (Diverge)

Strategy reads from three knowledge channels and outputs 6-8 candidate directions, each with a rationale and a probe expression.

**Channel 1: Memory (required)**
- Read `directions.yaml` index — know each direction's current status
- Read last 2 batch histories from `storage/memory/history/`
- Read `state.yaml` for global stats and `next_round_hint`
- Read factor library for coverage gaps

**Channel 2: Web Search (optional)**
- Triggered when: fewer than 3 directions have status `active` or `new`, OR user specifies a new topic
- LLM constructs search queries dynamically based on current gaps (e.g., "A-share daily frequency volume anomaly factor")
- Extracts actionable leads (formulas, ideas) from results
- Creates new direction files with status `new`

**Channel 3: Mutation Analysis (automatic)**
- Scans top 5 factors by IC in the library
- Checks which haven't been systematically mutated (window scan, rank transform, combination)
- Generates mutation directions automatically

**Strategy Output:**
```yaml
directions:
  - name: "williams_r_window_scan"
    source: mutation
    rationale: "factor_011 IC=+0.070, never tried window variants"
    probe_expression: "Div(Sub(Max($high,7), $close), Sub(Max($high,7), Min($low,7)))"
  - name: "alpha191_045"
    source: search
    rationale: "Alpha191 formula, different from Alpha101 set"
    probe_expression: "..."
  # ... 6-8 total
```

**Context Summary (printed before probe):**

Strategy must print a structured context summary showing: library status, direction statuses, knowledge channels used, and the 6-8 candidate directions. This replaces the current idea skill's context summary.

### Phase 2: Probe (Explore Boundaries)

Run each probe expression through a lightweight evaluation: **full universe, 1 year of data (2024), IC only**. No correlation check, no report card.

Implementation: reuse `FactorMiningEvaluator` but truncate after Stage 1, or call `mining evaluate` CLI per expression.

Configuration:
- Universe: all stocks
- Period: 2024-01-01 to 2024-12-31
- Output: IC mean only
- Time per probe: ~10-20 seconds
- Total: ~1-2 minutes for 6-8 probes

**Probe Output:**
```
Direction 1: williams_r_window_7    IC=+0.061  signal:strong
Direction 2: alpha191_045           IC=-0.002  signal:none
Direction 3: volume_regime_cross    IC=-0.015  signal:weak
Direction 4: trend_resi_combo       IC=-0.038  signal:moderate
Direction 5: signed_range_accel     IC=-0.041  signal:moderate
Direction 6: paper_xyz_factor       IC=+0.028  signal:moderate
```

Note: Probe IC uses full universe + 1 year, so it's reasonably accurate for relative ranking. It is NOT used as admission criteria — only for direction selection.

### Phase 3: Decide (Converge)

LLM selects top 2-3 directions based on:
1. Probe IC strength (primary signal)
2. Direction history in memory (consecutive failures → downweight)
3. Expected correlation with existing library factors (structurally similar → downweight)
4. Diversity (don't pick 3 volatility variants)

For each selected direction, expand into 2-3 formal candidates:
- Window variants: probe used N=14, expand to N=7, 14, 21
- Structural variants: add Rank transform, combine with other signals
- Parameter tweaks: adjust internal parameters

**Output:** 6-8 formal candidates written to `storage/candidates/batch_XXX.yaml` (same format as current).

### Phase 4: Execute (unchanged)

Run the full multi-stage evaluation pipeline:
```bash
PYTHONPATH=src python3 -m mining batch storage/candidates/batch_XXX.yaml
```

Stages 0-3 + report card generation, identical to current implementation.

### Phase 5: Judge (enhanced)

**5a. Factor Judgment (unchanged)**

6-dimension report card + LLM judgment for each screened factor. Admit/reject/replace decisions. Execute `lib.admit()` / `lib.replace()`.

**5b. Direction Feedback (new)**

After factor judgment, aggregate results by direction:

```
Direction williams_r_mutation: 3 candidates, 1 admitted (IC=0.055), 2 rejected
Direction alpha191_batch1: 3 candidates, 0 admitted, best IC=0.018
Direction trend_new: 2 candidates, 0 admitted, best IC=0.008
```

For each direction, update its `.md` file:
- Frontmatter: `attempts`, `best_ic`, `last_batch`, `status`
- Body: append probe record and candidate results

**5c. Automatic Status Transitions**

| Condition | Transition |
|-----------|-----------|
| This round has admission | Stay `active`, priority may increase |
| 0 admissions but best IC > 0.02 | Stay `active` |
| 2 consecutive rounds with 0 admissions and best IC < 0.02 | → `exhausted` |
| 3 cumulative rounds with 0 admissions | → `dead` |

**5d. Update Global State**

Update `directions.yaml` index and `state.yaml`. Write `next_round_hint` into `state.yaml`:
```yaml
next_round_hint: "williams_r mutation admitted 1, continue rank transforms. alpha191 batch failed, try next formula group. trend direction near dead."
```

**5e. Save Batch History**

Write `storage/memory/history/batch_XXX.yaml` (same format as current).

## Memory System Restructure

### New Structure

```
storage/memory/
├── state.yaml              # Global stats (simplified)
├── mining-lessons.md       # Engineering lessons (unchanged)
├── directions/             # NEW: one file per direction
│   ├── volatility.md
│   ├── candlestick.md
│   ├── williams_r_mutation.md
│   ├── alpha191_batch1.md
│   └── ...
├── directions.yaml         # Direction index (lightweight)
└── history/                # Batch history (unchanged)
```

### Direction File Format

```markdown
---
name: williams_r_mutation
status: active
category: candlestick
source: mutation
parent_factor: "011"
attempts: 0
best_ic: null
last_batch: null
priority: high
created: "2026-03-28"
---

Williams %R variant window/structure mutation exploration.

## Rationale
factor_011 IC=+0.070 is the strongest in the library, but systematic window
variation and rank transforms have never been attempted.

## Probe Records
(judge appends automatically)

## Candidate History
(judge appends automatically)
```

### Direction Status Lifecycle

```
new → probing → active → exhausted → dead
                  ↑          |
                  └──────────┘  (revival if new data/approach)
```

- `new` — just discovered from search/analysis, not yet validated
- `probing` — probe is running
- `active` — probe showed signal, worth continuing
- `exhausted` — paused after consecutive failures
- `dead` — definitively no potential

### directions.yaml (Index)

```yaml
- name: williams_r_mutation
  status: active
  priority: high
  category: candlestick
  attempts: 0
  best_ic: null

- name: volatility
  status: exhausted
  priority: none
  category: volatility
  attempts: 15
  best_ic: -0.058
```

### state.yaml (Simplified)

```yaml
library:
  size: 24
  target_size: 100
  avg_ic: 0.0365
  correlation_max: 0.7

mining:
  total_batches: 23
  total_candidates: 270
  total_admitted: 24
  yield_rate: 0.089
  last_batch_time: "2026-03-28T17:00:00"

next_round_hint: null
```

Domain saturation info removed — now tracked per-direction in direction files.

### Migration Plan

**From patterns.yaml `recommended_directions` (14 entries):**
- Each becomes a direction `.md` file
- Status derived from state.yaml `domain_saturation` and patterns.yaml notes
- Example: "Alpha101 Composites" → `alpha101_composites.md`, status=active
- Example: "Robust Efficiency" → `robust_efficiency.md`, status=blocked

**From patterns.yaml `forbidden_regions` (22 entries):**
- Direction-specific bans (e.g., "RSI-like constructions") → written into corresponding direction file body, status=dead
- Generic engineering constraints (e.g., "unavailable operators") → stay in `mining-lessons.md`

**Deleted after migration:** `patterns.yaml`

## Skill Changes

### `/idea` (major rewrite)

Becomes Strategy + Probe + Decide. Steps:

1. Determine batch number (unchanged)
2. **Strategy**: read `directions.yaml` + `state.yaml` + last 2 batch histories + factor library. Optionally web search. Optionally mutation analysis. Output 6-8 candidate directions with probe expressions.
3. Print context summary (restructured to show directions and their statuses)
4. **Probe**: run each probe expression (full universe, 1 year, IC only). Print results.
5. **Decide**: select top 2-3 directions, expand to 6-8 formal candidates.
6. Write `batch_XXX.yaml`

### `/execute` (minimal change)

No changes to the evaluation pipeline itself. Minor: add a lightweight "probe mode" to the CLI or evaluator that runs Stage 1 only with configurable universe/period, for the Probe phase to call.

### `/judge` (moderate enhancement)

Steps 1-3 unchanged (find result, LLM judgment, execute admission). Add:
4. Direction Feedback: aggregate by direction, update direction files, auto status transitions
5. Update `directions.yaml` index
6. Update `state.yaml` (simplified) + `next_round_hint`
7. Save batch history (unchanged)

### `/mine` (orchestration update)

Still serial: `/idea` → `/execute` → `/judge`. But `/idea` now internally runs Strategy → Probe → Decide. The overall structure is the same for the user.

### `/factor-report` (no change)

Not affected by this redesign.

## What This Does NOT Change

- **Evaluation pipeline** (`FactorMiningEvaluator`): Stages 0-3 unchanged
- **Factor library** (`FactorLibrary`): admit/replace/list unchanged
- **CLI** (`mining` module): mostly unchanged, may add probe mode
- **Training period**: stays at current defaults (separate concern)
- **Report generation**: unchanged
- **Automation level**: stays semi-automatic, one `/mine` = one full cycle

## Success Criteria

1. A `/mine` round should never produce 0/8 admissions due to exploring dead directions — probe filtering should catch these
2. Direction lifecycle is visible: user can look at `directions.yaml` and instantly see what's worth exploring
3. Judge feedback loop works: consecutive failures automatically demote directions
4. Web search provides genuinely new leads when internal directions are exhausted
5. Memory migration preserves all existing knowledge from patterns.yaml
