# Refactor Checklist

> Live progress tracker for the factor system refactor.
> North-star design: `docs/refactor_plan.md`
> Execution plan: `docs/superpowers/specs/2026-04-12-refactor-execution-plan.md`
> Chinese navigation: `~/.claude/plans/jolly-purring-cascade.md`

**Last updated**: 2026-04-12
**Current Part**: P1 — Phase 2 EXECUTE (P0 done)

## Subtask origin tags

Each subtask below is tagged with one of:
- **[A]** — Reuse as-is or with light touch from existing code
- **[B]** — Refactor: extract core logic from old file(s) into new structure (cite source in commit)
- **[N]** — New code, no old equivalent
- **[C]** — Cleanup/delete old code (P7 only)

When a task says `[B] from src/research/foo/bar.py`, the implementation pattern is:
1. Read old file for algorithm reference
2. Create new file in new location with new structure
3. Copy core formulas/math, restructure per new contract (vectorization, schema, etc.)
4. Do NOT edit old file in place — old file stays until P7

---

## P0 — Infrastructure & Skeleton [status: done]

Goal: lay down the new storage layout, state/config files, and the empty package skeleton so that later Parts have clean landing points.

- [x] **[N]** Create `storage/state.yaml` with initial schema (current_batch=null, round=0, rounds_since_last_consolidation=0, ...)
- [x] **[B]** Create `storage/config.yaml` — extract useful fields from `storage/governance/research_config.yaml`, restructure per refactor_plan §10 (sample_policy / evaluation / preprocess / thresholds / consolidation blocks); includes §7.MT `mt_budget` placeholder constants
- [x] **[B]** Create `storage/evidence/vault/lessons.md` — seed with the Data Facts / Operator Registry / Path Selection / Structural Constraints content from refactor_plan §10, cross-reference `storage/governance/research_lessons.md` for any additional facts
- [x] **[N]** Create `storage/evidence/vault/{INDEX.md,directions/,factors/,_meta/}` scaffolding (empty INDEX with headers only)
- [x] **[N]** Create `storage/_holdout_private/` with a marker file + `.gitignore` line
- [x] **[N]** Create `storage/cache/factor_values/` dir
- [x] **[N]** Create `storage/python_factors/` dir (pre-allocated for P4 Python factor archive)
- [x] **[B]** Write `src/research/storage/yaml_io.py` — kept existing atomic-write logic, added `load_yaml_unsafe()` for result.yaml (pandas DataFrame payloads)
- [x] **[B]** Write `src/research/storage/paths.py` — new `StoragePaths` class for new vault-first layout (state.yaml + config.yaml at root, vault under evidence/, batches/, cache/, python_factors/, _holdout_private/); old file fully overwritten
- [x] **[B]** Write `src/research/storage/state.py` — new `State` dataclass + `StateFile` facade with phase-transition DAG (designed → executing → judged → archived → idle), gives Q32 idempotency for free via `InvalidPhaseTransition`
- [x] **[N]** Create empty packages with `__init__.py`:
  - [x] `src/research/phases/`
  - [x] `src/research/checkpoints/`
  - [x] `src/research/memory/`
  - [x] `src/research/archive/`
- [x] **[N]** pytest: `tests/research/storage/test_yaml_io.py` (21 tests: roundtrip + atomic write + crash safety + unsafe_load)
- [x] **[N]** pytest: `tests/research/storage/test_state.py` (15 tests: read/write/phase transition/Q32 double-archive/consolidation reset)
- [x] **[N]** pytest: `tests/research/storage/test_paths.py` (17 tests: rewritten for new layout — old version tested legacy dirs)
- [x] R9 grep: new files import nothing from deprecated packages (verified)
- [x] Commit: `[refactor] P0: infrastructure and skeleton`

**Notes**:
- Old `storage/governance/{research_config,research_lessons}.md` stay in place until P7; new `config.yaml` + `vault/lessons.md` coexist.
- `StoragePaths` rewrite broke `tests/research/storage/test_state_store.py`, `test_finalizer.py`, `test_ledger_store.py`, `test_registry_store.py`, `test_manifest_validator.py` (44 tests). Expected — all will be deleted in P7 along with the old modules they test. Only the 53 new P0 tests must pass.

**Completed at**: _pending commit_

---

## P1 — Phase 2 EXECUTE (计算层核心) [status: pending]

Goal: nail down the vectorized compute layer. This is the most numerically sensitive Part — everything downstream consumes `result.yaml`.

### P1.0 — Golden fixture generation (critical: do before any rewrite)
- [ ] **[B]** Write `tests/research/compute/_fixtures/generate_golden.py` — a one-shot script that uses the **old** code (`research.stats`, `research.risk.exposures`, `research.feasibility`, `research.redundancy.pairwise`) to compute reference values for 5-10 known factor expressions, writing outputs to `tests/research/compute/_fixtures/golden_*.parquet`
- [ ] Run the script once, commit the generated parquet fixtures to git
- [ ] These fixtures serve as the "equivalence gate" for P1.2 / P1.3 rewrites — new vectorized code must match within 1e-6

### P1.1 — Preprocess & cache
- [ ] **[B]** Write `src/research/compute/cache.py` — reference old `src/research/execute/compute_implementations.py` cache bits (if any); implement sha256 cache: key = expression|sample_policy_version|preprocess_version
- [ ] **[B]** Write `src/research/compute/preprocess.py` — extract winsorize_mad / zscore math from old `src/research/execute/preprocess.py` (per refactor_plan Q14 note: old had 4 dead code paths, keep only the 2 that matter); add tradability mask application
- [ ] **[N]** pytest: cache hit/miss + invalidation on sample_policy_version change
- [ ] **[N]** pytest: preprocess NaN handling + cross-sectional correctness

### P1.2 — Core vectorized metrics
- [ ] **[B]** Write `src/research/compute/vectorized_ic.py` — extract IC mean/std/ir/win_rate formulas from `src/research/stats/effect_strength.py`, restructure as batched groupby corrwith
- [ ] **[B]** Write `src/research/compute/vectorized_quintile.py` — extract quintile / monotonicity logic from old stats (likely in `effect_strength.py` or similar), rewrite with single groupby qcut
- [ ] **[B]** Write `src/research/compute/vectorized_feasibility.py` — extract coverage / half-life / turnover formulas from `src/research/feasibility/*.py` (5 files), drop all for-loops and rewrite as single groupby agg. **Note**: `src/research/feasibility/proxy_portfolio.py` uses `groupby().apply(_assign_weights)` which must be rewritten as vectorized per R5
- [ ] **[B]** Write `src/research/compute/vectorized_stability.py` — extract split_stability + expanding_window from old `src/research/stats/` (search for expanding / split), ensure window boundaries match config.yaml
- [ ] **[N]** pytest: each new metric numerically matches old implementation output within 1e-6 on a fixture (golden file generated from old code first)

### P1.3 — Redundancy & Barra (heaviest)
- [ ] **[B]** Write `src/research/compute/vectorized_redundancy.py` — reference `src/research/redundancy/pairwise.py`, simplify to batch `corrwith` against library_wide DataFrame; drop old `family.py` / `subspace.py` logic (not in scope)
- [ ] **[B]** Write `src/research/compute/vectorized_barra.py` — extract Barra OLS math from `src/research/risk/exposures.py` (old uses `np.linalg.lstsq` inside per-date loop; per-date loop is necessary because stock set differs per day, but the OLS itself **must be upgraded** to `np.linalg.pinv` + `np.einsum` on 3D tensor per refactor_plan §11); compute residual IC, style_r², alpha_survival in one pass
- [ ] **[N]** pytest: Barra residual IC matches old `research.risk.exposures` output within 1e-6 on a fixture
- [ ] **[N]** Benchmark: 1000 candidates × 1500 days × 1000 symbols finishes in < 60s

### P1.4 — Python factor runner
- [ ] **[N]** Write `src/research/compute/python_runner.py` (load module, runtime contract check per refactor_plan §6, timing warning) — no old equivalent, R8 is new
- [ ] **[N]** pytest: runtime contract catches wrong signature, non-Series return, duplicated index
- [ ] **[N]** pytest: vectorization timing warning triggers on slow implementation

### P1.5 — Phase 2 orchestrator
- [ ] **[B]** Write `src/research/phases/phase2_execute.py` — reference `src/research/execute/pipeline.py::ResearchExecutePipeline` for the overall flow shape, rewrite completely (old has mixed precheck/compute/gate/judge_packet; new phase2 only does compute+preprocess+metrics+result.yaml)
- [ ] **[N]** Freeze `result.yaml` schema (per refactor_plan §10, no holdout fields, includes derived_analytics block for P5 to consume)
- [ ] **[N]** pytest: end-to-end phase2 on a small 2-candidate manifest
- [ ] **[N]** Error handling: single candidate compute_error logged but others continue

### P1 — Close out
- [ ] R9 grep: no imports from deprecated packages
- [ ] `ruff check src/research/compute src/research/phases/phase2_execute.py`
- [ ] Update checklist: mark P1 subtasks `[x]`, set status=done, record commit hash
- [ ] Commit: `[refactor] P1: phase2 execute with vectorized compute`

**Completed at**: _pending_

---

## P2 — Phase 3 JUDGE (checkpoint 层) [status: pending]

Goal: build the 6-checkpoint judge pipeline with pre-packing + Python audit.

- [ ] **[B]** Write `src/research/checkpoints/hard_gates.py` — extract gate rules (sign_flip / coverage / forbidden / sample_policy / compute_error) from old `src/research/execute/execution_gate.py`, restructure as pure functions on result.yaml entries
- [ ] **[B]** Write `src/research/checkpoints/generator.py` — reference old `src/research/execute/judge_packet_builder.py` (per Q26 it has bugs), rewrite completely: pre-pack `_packets/judge_packet.md` from result.yaml + direction.md + lessons.md + nearest factor.md as single-input per R3
- [ ] **[B from src/research/stats/multiple_testing.py]** Write `src/research/stats/mt_budget.py` (per refactor_plan §7.MT):
  - [ ] `scan_batches_for_mt(batches_dir, current_batch_id, current_direction, sample_policy_version)` — pure function scanning `storage/batches/batch_*/manifest.yaml`, counting only "judged" batches (judge.md exists), returning `{cumulative_candidates, direction_candidates, validation_exposure, n_batches_scanned}`
  - [ ] `compute_mt_budget(counts)` — wraps existing `compute_multiple_testing_risk()` + `compute_search_adjusted_strength()`, returns dict ready to inject into numeric_hint
  - [ ] Constant calibration: backfit formula constants (`log_family_base`, `log_direction_base`, `exposure_divisor`) on existing `storage/batches/batch_001..102` and write into `storage/config.yaml.thresholds.mt_budget`
- [ ] **[N]** `checkpoints/generator.py` Phase 3 flow **must call** `scan_batches_for_mt + compute_mt_budget` before pre-packing (new Step 2 per refactor_plan §7 流程)
- [ ] **[N]** CP03 numeric_hint schema **must include** `mt_score / mt_bucket / search_adjusted_strength / mt_breakdown` (freeze in judge_packet template)
- [ ] **[N]** Write `src/research/checkpoints/audit.py` (judge.md schema + section existence + reference authenticity grep + packet-reference check + hard-gate-not-overridable + **CP03 body must cite `mt_bucket` string**) — no old equivalent, new audit contract
- [ ] **[N]** pytest: `scan_batches_for_mt` counts correctly on fixture batches (n=10, direction X=4, exposure=10)
- [ ] **[N]** pytest: `compute_mt_budget` returns correct bucket for three score tiers (low / medium / high)
- [ ] **[N]** pytest: audit check 6 raises when CP03 section omits `mt_bucket`
- [ ] **[N]** Freeze `judge.md` schema (frontmatter + body, per refactor_plan §7)
- [ ] **[B]** Write `src/research/phases/phase3_judge.py` — reference old `src/research/judge/candidate_judge.py` (dead code but has useful orchestration shape), rewrite: Python gates → pre-pack → LLM write → audit → cleanup
- [ ] **[N]** pytest: hard gate rejects as expected on fixture inputs
- [ ] **[N]** pytest: judge.md roundtrip (write then audit passes)
- [ ] **[N]** pytest: audit catches missing CP section, fabricated references, hard-gate override attempts
- [ ] R9 grep: no deprecated imports
- [ ] Update checklist: P2 `[x]` + commit hash
- [ ] Commit: `[refactor] P2: phase3 judge with checkpoints and audit`

**Completed at**: _pending_

---

## P3 — Phase 1 START + DESIGN [status: pending]

Goal: manifest freeze with DSL whitelist + Python candidate validation + dedup.

- [ ] Write `src/research/phases/phase1_start.py` with:
  - [ ] **[B]** DSL whitelist validator — extract `DSL_FIELD_WHITELIST` / `DSL_OPERATOR_WHITELIST` / depth check from old `src/research/execute/precheck.py` (the "single source of truth" per CLAUDE.md), simplify — drop any `forbidden_patterns` / blacklist logic (Q43 / Q44.7)
  - [ ] **[N]** `validate_python_candidate()` (AST import whitelist + forbidden calls + REQUIRED_FIELDS / VECTORIZED / compute signature contract) — new, R8 is new concept
  - [ ] **[N]** `canonicalize_expression()` + `check_duplicate_expression()` against existing `factors/F*.yaml` — new, Q4 addressing
  - [ ] **[N]** `batch_goal` audit (non-empty, length ≥ 30)
  - [ ] **[B]** `manifest.yaml` atomic freeze — reuse `yaml_io.atomic_write` from P0
- [ ] **[N]** pytest: DSL whitelist accept + reject cases (forbidden field, unknown operator, depth>10)
- [ ] **[N]** pytest: Python validator catches forbidden imports (subprocess, os), forbidden calls (eval, open), missing REQUIRED_FIELDS
- [ ] **[N]** pytest: duplicate detection under commutativity (Mul(A,B) == Mul(B,A))
- [ ] **[N]** pytest: duplicate detection after retire allows re-submission
- [ ] **[N]** pytest: manifest freeze is atomic (no partial writes on failure)
- [ ] R9 grep
- [ ] Update checklist + commit: `[refactor] P3: phase1 start+design with whitelist and dedup`

**Completed at**: _pending_

---

## P4 — Phase 4 ARCHIVE (Python 侧) [status: pending]

Goal: the synchronous Python side of archive — factor allocation, frontmatter updates, INDEX refresh, main commit.

- [ ] **[B]** Write `src/research/archive/factor_writer.py` — reference old `src/research/storage/registry_store.py` + `finalizer.py` for F{id} allocation patterns (old has bug per Q39), rewrite cleanly: monotonic allocation, write `factors/F{id}.yaml`, signal_ref linking
- [ ] **[N]** Write `src/research/archive/python_archiver.py` (for source_type=python, copy `batches/.../python_candidates/C{id}.py` → `storage/python_factors/F{id}_{name}.py`) — R8 new
- [ ] **[N]** Write `src/research/memory/direction_updater.py` (surgical frontmatter update: rounds++, admits++, members append, last_batch, last_activity — body untouched via frontmatter library)
- [ ] **[N]** Write `src/research/memory/index_refresher.py` (regenerate INDEX.md lower half statistics table from all direction frontmatters)
- [ ] **[B]** Write `src/research/archive/commit.py` — reference any git-commit helpers in old `src/research/governance/` or `src/research/cli/`, rewrite with hard-fail on pre-commit hook failure (Q47.3)
- [ ] **[B]** Write `src/research/phases/phase4_archive.py` — reference old `finalize-batch` / `BatchFinalizer` logic, rewrite as 5-step sync pipeline (defer step 3 subagent to P5)
- [ ] **[N]** Idempotency guard: `archive()` raises if batch already in `archived` phase (Q32)
- [ ] **[N]** pytest: double-archive raises
- [ ] **[N]** pytest: F{id} allocation monotonic + no gaps
- [ ] **[N]** pytest: direction_updater preserves body + only changes frontmatter fields
- [ ] **[N]** pytest: index_refresher output matches snapshot
- [ ] **[N]** pytest: commit-failure path raises (mock pre-commit hook failure)
- [ ] R9 grep
- [ ] Update checklist + commit: `[refactor] P4: phase4 archive python side`

**Completed at**: _pending_

---

## P5 — Phase 4 ARCHIVE (LLM 侧) + Report Analytics [status: pending]

Goal: the async subagent side — report packing, PNG generation, factor.md sandbox protocol.

### P5.1 — New vectorized report analytics
- [ ] **[B]** Write `src/report/analytics_v2/` — extract the stateless math from old `src/report/analytics/{ic,profit,conditional,decay,risk,uniqueness}_analyzer.py`, rewrite as functions consuming `result.yaml.derived_analytics` directly (no recomputation per R4)
- [ ] **[B]** Map each old analyzer to a new function or delete if redundant; CP: record mapping in commit msg
- [ ] **[N]** pytest: each analytics function on fixture result.yaml

### P5.2 — PNG rendering
- [ ] **[B]** Write `src/report/charts_v2/` — extract plotly chart rendering code from `src/report/charts/*.py` (largely reusable), adapt to new input schema; one function per chart type (ic_timeseries, quintile_bar, radar, decay_curve, ic_yearly, etc.)
- [ ] **[N]** pytest: each chart renders without error on fixture input

### P5.3 — Report packer
- [ ] **[B]** Write `src/research/archive/report_packer.py` — reference old `src/report/builder.py` + `src/report/data_prep.py` for pack structure, rewrite per refactor_plan §8 (Section 0-4) with single-input-packet principle (R3)
- [ ] **[N]** pytest: packer output contains all required sections (Section 0-4)

### P5.4 — Subagent protocol + phase4 step 3
- [ ] **[N]** Wire `phase4_archive.py` Step 3: dispatch background subagent per admit with sandboxed I/O (reads only packet, writes only factor.md) — R3 / new subagent protocol
- [ ] **[N]** Subagent on-complete hook: calls `research commit-report F{id}`
- [ ] **[N]** Subagent on-failure: log to `_subagent_failures.log`, main loop unaffected
- [ ] **[B]** Rewrite `.claude/skills/factor-report/skill.md` — old skill.md as starting point, restructure around sandbox protocol and single-input packet

### P5.5 — Manual verification
- [ ] Run full archive on a synthetic admit, verify `factors/F{id}.md` generated with all charts embedded
- [ ] R9 grep (including new `src/report/` code)
- [ ] Update checklist + commit: `[refactor] P5: phase4 archive llm side and new report analytics`

**Completed at**: _pending_

---

## P6 — Phase 5 CONSOLIDATION + Mine 主循环 [status: pending]

Goal: wire everything into the autonomous mine loop and rewrite all skills.

### P6.1 — Phase 5 consolidation
- [ ] **[B]** Write `src/research/phases/phase5_consolidate.py` — reference old `/factor-reflect` skill + any reflect/consolidation logic in `src/research/logic/reflect.py` (the "belief delta" concept is dead, but the md-rewrite orchestration shape is a useful starting point); new 5-step flow:
  - [ ] Pre-checks (git clean, no subagent failures, state.current_batch is None)
  - [ ] Parallel pre-pack `_consolidation/packet_*.md` per target
  - [ ] Dispatch parallel subagents (lessons + directions)
  - [ ] Sync subagent for INDEX (after directions finish)
  - [ ] Single commit `[consolidate] round N: ...`
- [ ] **[N]** pytest: consolidation pre-check fails on dirty state
- [ ] **[N]** pytest: manual trigger via `research consolidate --target lessons`

### P6.2 — Mine main loop
- [ ] **[B]** Write `src/research/cli/mine.py` — reference old `/factor-mine` skill for "dual-speed orchestrator" description, collapse to new 5-phase linear flow; keep autonomous-mode behavior (no user prompts per CLAUDE.md Autonomous Mining Mode)
- [ ] **[N]** State machine: designed → executing → judged → archived → (maybe consolidate) → next round
- [ ] **[N]** pytest: mine state transitions on fixture batch

### P6.3 — CLI router
- [ ] **[B]** Write new `src/research/cli/main.py` — reference old `src/research/cli/main.py` for argparse structure, rewrite subcommand table per refactor_plan §14 (mine, start, design, execute, judge, archive, consolidate, commit, commit-report, cache, audit, holdout-review, factor retire, state)
- [ ] **[N]** Register all sub-CLI modules per refactor_plan §14
- [ ] **[N]** `src/research/cli/audit.py` — add `research audit mt-budget` subcommand (per refactor_plan §7.MT):
  - [ ] no args: print global cumulative + validation_exposure under current sample_policy_version + predicted mt_bucket for the next batch
  - [ ] `--direction {name}`: break down per direction, show each direction's cumulative + predicted bucket
- [ ] **[N]** pytest: `research audit mt-budget` CLI output format is correct on fixture batches

### P6.4 — Skill rewrites
- [ ] **[B]** Rewrite `.claude/skills/factor-mine/skill.md` for new 5-phase flow (replaces the dual-speed orchestrator description)
- [ ] **[B]** Rewrite `.claude/skills/factor-idea/skill.md` → Phase 1 START + DESIGN (or rename to factor-start)
- [ ] **[B]** Rewrite/stub `.claude/skills/factor-execute/skill.md` (nearly empty — Phase 2 is pure Python)
- [ ] **[B]** Rewrite `.claude/skills/factor-judge/skill.md` → checkpoint-driven with packet protocol
- [ ] **[B]** Rewrite `.claude/skills/factor-report/skill.md` → subagent sandbox protocol (already touched in P5)
- [ ] **[C]** Delete `.claude/skills/factor-reflect/` (concept folded into Phase 5 consolidation)
- [ ] **[C]** Delete `.claude/skills/factor-logic/` (logic concept retired)

### P6.5 — Full loop verification
- [ ] Manual run: `research mine --once --direction bootstrap` completes all 5 phases successfully
- [ ] All commits happen (main archive commit + report commit + maybe consolidation commit)
- [ ] R9 grep across entire new code surface
- [ ] Update checklist + commit: `[refactor] P6: phase5 consolidate and mine orchestrator`

**Completed at**: _pending_

---

## P7 — 老代码清理 + CLAUDE.md 重写 [status: pending]

Goal: single big cleanup commit. Delete everything that's been replaced.

### P7.1 — Pre-cleanup verification
- [ ] Full pytest suite green on new code
- [ ] `research mine --once` verified end-to-end
- [ ] `grep -rn 'from research.logic\|from research.governance\|from research.feasibility\|from research.redundancy\|from research.risk\|from research.stats' src/` returns zero from new code

### P7.2 — Delete deprecated source packages
- [ ] `rm -rf src/research/logic/`
- [ ] `rm -rf src/research/governance/`
- [ ] `rm -rf src/research/feasibility/`
- [ ] `rm -rf src/research/redundancy/`
- [ ] `rm -rf src/research/risk/`
- [ ] `rm -rf src/research/stats/`
- [ ] `rm src/research/judge/{candidate_judge,mechanism_alignment,replace_protocol}.py`
- [ ] `rm src/research/storage/{finalizer,consistency,candidate_store,packet_store,result_store,ledger_store,registry_store}.py`
- [ ] `rm src/research/execute/{judge_packet_builder,execution_gate,compute_implementations}.py`
- [ ] `rm src/research/execute/precheck.py` (replaced by phase1 whitelist)
- [ ] `rm src/research/execute/pipeline.py` (replaced by phase orchestrators)

### P7.3 — Delete deprecated report code
- [ ] `rm src/report/renderer.py`
- [ ] `rm -rf src/report/templates/`
- [ ] `rm -rf src/report/analytics/` (if replaced by analytics_v2) OR rename analytics_v2 → analytics
- [ ] `rm src/report/builder.py` (replaced by archive/report_packer.py)

### P7.4 — Delete deprecated tests
- [ ] `grep -lr 'from research.logic\|from research.governance\|...' tests/ | xargs rm` — delete tests of removed modules

### P7.5 — Move legacy storage
- [ ] `mv storage/logic storage/_legacy/logic_v1`
- [ ] `mv storage/governance storage/_legacy/governance_v1`
- [ ] `mv storage/registry storage/_legacy/registry_v1`
- [ ] Old `storage/batches/batch_001..103/` → `storage/_legacy/batches_v1/`
- [ ] Old `storage/evidence/vault/factors/` (legacy location) → `_legacy/vault_v1_factors/`

### P7.6 — CLAUDE.md rewrite
- [ ] Rewrite `CLAUDE.md` per `refactor_plan.md` §17 outline
  - [ ] System constitution R1-R8 summary
  - [ ] 5-phase overview
  - [ ] New CLI reference
  - [ ] New storage layout
  - [ ] Keep: Qlib/pyqlib technical notes, environment, C.kernels=1
  - [ ] Delete: old logic/family/9-phase descriptions, old skill workflow, old factor counts/grades

### P7.7 — Final sweep
- [ ] Full pytest suite still green
- [ ] `ruff check src/` clean
- [ ] `research mine --once --direction bootstrap` still works
- [ ] Update checklist: mark P7 done + add "ALL DONE ✅" header with final commit hash
- [ ] Commit: `[refactor] P7: cleanup deprecated code and rewrite CLAUDE.md`

**Completed at**: _pending_

---

## Summary Stats (updated at completion)

- New files added: _pending_
- Old files deleted: _pending_
- Tests added: _pending_
- Total commits: _pending_ (expected: 8 Part commits + potentially small fix commits in between)
