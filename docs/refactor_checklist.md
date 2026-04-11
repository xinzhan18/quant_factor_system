# Refactor Checklist

> Live progress tracker for the factor system refactor.
> North-star design: `docs/refactor_plan.md`
> Execution plan: `docs/superpowers/specs/2026-04-12-refactor-execution-plan.md`
> Chinese navigation: `~/.claude/plans/jolly-purring-cascade.md`

**Last updated**: 2026-04-12
**Current Part**: P2 — Phase 3 JUDGE (P0 + P1 done)

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

**Completed at**: commit `62c3b05` (24 files, +2495/-291)

---

## P1 — Phase 2 EXECUTE (计算层核心) [status: done]

Goal: nail down the vectorized compute layer. This is the most numerically sensitive Part — everything downstream consumes `result.yaml`.

### P1.0 — Golden fixture generation (critical: do before any rewrite)
- [x] **[B]** Write `tests/research/compute/_fixtures/generate_golden.py` — deterministic synthetic panel (seed=20260412, 600 days × 200 symbols), runs OLD pure-function modules (core.factor_stats, research.stats, research.redundancy.pairwise, research.feasibility, research.risk.exposures)
- [x] Run the script once, commit the generated parquet fixtures + golden.yaml to git
- [x] Fully reproducible (zero-diff on re-run, no timestamps)
- [x] Inputs bundle: factor / returns / library signals (3 tiers) / tradable mask / amount / cap / style matrix / bench returns

### P1.1 — Preprocess & cache
- [x] **[B]** `src/research/compute/cache.py` — content-addressed sha256 cache, key = `expression|sample_policy_version|preprocess_version`; atomic parquet writes; no ledger dependency
- [x] **[B]** `src/research/compute/preprocess.py` — pure matrix MAD winsorize + z-score (long → wide → matrix → long), no groupby.transform, no neutralize (per config.yaml)
- [x] **[N]** pytest: 16 cache tests (key determinism, CRUD, atomic write, corrupt handling)
- [x] **[N]** pytest: 14 preprocess tests (winsorize boundary, zscore mean/std, NaN preservation, idempotent roundtrip)

### P1.2 — Core vectorized metrics
- [x] **[B]** `src/research/compute/vectorized_ic.py` — thin wrapper over `core.factor_stats.daily_cross_sectional_ic + ic_summary`, adds train/val split + support_window flip check
- [x] **[B]** `src/research/compute/vectorized_quintile.py` — wraps `core.factor_stats.quintile_returns + monotonicity`, unified dict output
- [x] **[B]** `src/research/compute/vectorized_feasibility.py` — full vectorization of legacy feasibility (proxy_portfolio `groupby().apply` → 3D mask broadcast; turnover for-loop → `wide.diff().abs().sum`; weighted_flag_ratio per-date loop → `groupby(level=0).sum`)
- [x] **[B]** `src/research/compute/vectorized_stability.py` — split_stability + sign_consistency + train_val_decay + expanding_window, copied pure functions from legacy stats
- [x] **[B]** `src/research/compute/vectorized_redundancy.py` — compute_pairwise_redundancy + batch_dedup, core logic from research.redundancy.pairwise
- [x] **[N]** pytest: all 4 ic tests + 4 quintile + 10 stability + 9 feasibility + 5 redundancy match golden within 1e-6

### P1.3 — Redundancy & Barra (heaviest)
- [x] **[B]** `src/research/compute/vectorized_barra.py` — **3D tensor batch OLS** via `np.einsum + np.linalg.pinv` per §11, replaces per-date lstsq loop. Handles varying valid-stock sets via zero-masking (invalid cells contribute nothing to XtX or Xty). Full pipeline: pivot → mask → Gram → pinv → beta → residual → IC → survival ratio
- [x] **[N]** pytest: 8 Barra golden-equivalence tests — style_exposures / style_r² / barra_residual_ic / alpha_survival / dominant_style / crowding risk all match legacy within 1e-5
- [x] **Benchmark**: 600 days × 200 symbols × 7 styles = **93 ms** (legacy ≈ 600 ms, ~6× speedup just from vectorization)

### P1.4 — Python factor runner
- [x] **[N]** `src/research/compute/python_runner.py` — AST whitelist (import + forbidden call + getattr guard) + module contract (REQUIRED_FIELDS / VECTORIZED=True / compute signature) + timing warning (5s threshold surfaces non-vectorized regressions via logging)
- [x] **[N]** pytest: 16 python_runner tests (forbidden imports: subprocess/os; forbidden calls: eval/open/getattr; missing attributes; wrong signature; non-Series return; flat-index return; syntax error)

### P1.5 — Phase 2 orchestrator
- [x] **[B]** `src/research/phases/phase2_execute.py` — thin orchestrator, all math delegated to `compute/vectorized_*`. Per-candidate try/except so one failure doesn't break the batch. `multiple_testing_risk_bucket: None` at Phase 2 (Phase 3 fills it via §7.MT mt_budget)
- [x] **[N]** Freeze `result.yaml` schema (constant `RESULT_SCHEMA_VERSION = "1"` + structured candidate dict with effect_strength / quintile / stability / redundancy / feasibility / barra / compute_error)
- [x] **[N]** `Phase2Inputs` dataclass — clean interface between Phase 1 data loading (future) and Phase 2 computation. End-to-end testable on synthetic data with no DB/Qlib dependency.
- [x] **[N]** pytest: 2 end-to-end tests (happy path: all metrics match ballpark + structural shape; error path: broken candidate reported as compute_error while siblings continue)

### P1 — Close out
- [x] R9 grep: no imports from deprecated packages (8 new P1 files all clean)
- [x] Full P0+P1 pytest: **142 new tests pass**, 44 legacy tests fail at collection (test_state_store / test_finalizer / test_ledger_store / test_registry_store / test_manifest_validator / test_factor_engine / test_data_provider / test_universe — all in P7 delete list, not regressions)
- [x] Commit: `[refactor] P1: phase2 execute with vectorized compute`

**Notes**:
- core/ is NOT deprecated — `core.factor_stats` is imported by multiple new vectorized_*.py modules as the authoritative IC/quintile math. R9 only forbids `research.{logic,governance,feasibility,redundancy,risk,stats}` imports.
- `factor_engine.py`, `data_provider.py`, `universe.py`, `operators.py` remain on disk until P7. `research.compute.__init__.py` was updated to re-export only new P1 API (no FactorEngine / Preprocessor class).
- The Barra 3D batch approach (X_masked = np.where(valid, X, 0) then einsum) gives mathematical equivalence because zero rows contribute zero to XtX and Xty, just like dropping them explicitly.

**Completed at**: _pending commit_

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
