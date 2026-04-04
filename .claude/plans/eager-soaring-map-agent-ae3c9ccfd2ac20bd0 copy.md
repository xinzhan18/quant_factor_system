# Implementation Plan: Logic System v1 → v2 Upgrade

## Overview

Upgrade the `/logic` skill from a simple CRUD system to a full proposal → review → admit → schedule pipeline. This touches 3 Python files, 1 skill file, 3 downstream skill files, creates 1 new Python module, and requires a data migration script.

**Estimated scope**: ~800 lines of new/modified Python, ~400 lines of new skill markdown, ~100 lines of migration script.

---

## Design Decisions (Answers to Open Questions)

### Q1: Should proposal/review generation be purely LLM or Python-backed?

**Decision: Hybrid.** Proposals and reviews are *LLM-generated content* (thesis, mechanism, review comments) — the LLM writes YAML files directly via the Write tool. But the Python backend provides:
- `logic propose init` — creates the `proposals/` directory, assigns next proposal ID (PXXX), prints the template schema for the LLM to fill
- `logic review init PXXX` — loads the proposal, prints it for LLM context, creates `reviews/` stub
- `logic admit PXXX` — reads proposal + review, validates gate scores, creates the formal logic card (or rejects/parks)
- `logic schedule` — pure Python scoring + contract generation

**Rationale**: This matches the existing pattern where `/judge` does LLM reasoning but calls `lib.admit()` for the mechanical part. The LLM decides *what* to write; Python decides *where* it goes and maintains the registry.

### Q2: How to migrate L001-L014?

**Decision: Lazy migration with a one-time script.** Provide `scripts/migrate_logic_v2.py` that:
1. Reads each `storage/logic/LXXX.yaml` (v1 schema)
2. Maps fields to v2 schema with sensible defaults
3. Writes to `storage/logic/cards/logic_LXXX.yaml`
4. Builds `registry.yaml` from all migrated cards
5. Does NOT delete the original files (keeps them as backup until verified)

The `MarketLogicLibrary` v2 class will detect `schema_version` on read and auto-upgrade in-memory if a v1 card is encountered (belt-and-suspenders for any files missed by migration).

### Q3: Should registry.yaml be auto-maintained?

**Decision: Auto-maintained by Python code.** Every mutation (create, status change, evidence update) calls `_sync_registry()` which rebuilds the registry from card files. The registry is a *derived* index, not a source of truth. This avoids drift.

### Q4: How to implement exploration contracts?

**Decision: `logic schedule` outputs a YAML file.** The new `logic schedule` CLI command writes `storage/logic/snapshots/schedule_YYYYMMDD_HHMMSS.yaml` containing an array of exploration contracts. The `/idea` skill reads the *latest* snapshot file instead of parsing CLI stdout. This is more reliable than stdout parsing and creates an audit trail.

---

## Phase 1: Storage Structure + Migration (no behavior change)

### Task 1.1: Create directory structure

Create empty directories (the Python code will also `mkdir -p` them, but having them in git via `.gitkeep` is cleaner):

```
storage/logic/proposals/.gitkeep
storage/logic/reviews/.gitkeep
storage/logic/cards/.gitkeep
storage/logic/snapshots/.gitkeep
```

### Task 1.2: Write migration script

**New file: `scripts/migrate_logic_v2.py`**

Field mapping from v1 → v2:

| v1 field | v2 field | Transform |
|----------|----------|-----------|
| `id` | `logic_id` | rename |
| (none) | `schema_version` | set `"v2"` |
| `name` | `name` | copy |
| `category` | `category` | copy |
| (none) | `origin_type` | set `"manual_seed"` |
| `hypothesis.condition` + `behavior` + `timeframe` + `direction` | `thesis` | concatenate into paragraph |
| (none) | `mechanism` | set `"(migrated from v1 — mechanism not yet documented)"` |
| `constraints.required_fields` | `observable_proxy.required_fields` | copy |
| (none) | `observable_proxy.optional_fields` | set `[]` |
| `constraints.window_range` | `expected_horizon.formation_window` + `holding_window` | use `window_range[0]` and `window_range[1]` |
| `constraints.suggested_ops` | `implementation_space.preferred_families` | copy |
| (none) | `implementation_space.suggested_ops` | copy from `constraints.suggested_ops` |
| (none) | `implementation_space.discouraged_ops` | set `[]` |
| (none) | `implementation_space.forbidden_patterns` | set `[]` |
| (none) | `relations` | set `{parent_logic: null, sibling_logics: [], overlaps_with: []}` |
| `status` | `research_status` | map: `active→active`, `exhausted→saturated`, `dead→dead`, `archived→parked` |
| (none) | `priority` | set `0.5` (neutral) |
| (none) | `scores` | set all to `0.5` (neutral) |
| (none) | `budget` | set defaults: `{direction_quota: 3, candidate_quota: 8, preferred_mode: "genesis"}` |
| `stats.factors_generated` | `evidence.eval_attempts` | copy |
| `stats.factors_admitted` | `evidence.admits` | copy |
| `stats.best_ic` | `evidence.best_ic` | copy |
| `stats.rounds_without_admit` | `evidence.current_bottleneck` | convert: if >2 set `"consecutive_failures"`, else `null` |
| (none) | `evidence.probe_attempts` | set `0` |
| (none) | `evidence.near_miss` | set `0` |
| (none) | `evidence.best_incremental_ic` | set `0.0` |
| (none) | `evidence.productive_families` | set `[]` |
| (none) | `evidence.failed_families` | set `[]` |
| (none) | `falsification_conditions` | set `[]` |
| (none) | `next_actions` | set `[]` |
| `created` | `created` | copy |

The script also builds `registry.yaml`:

```yaml
schema_version: v2
last_updated: "2026-04-04T..."
logics:
  - logic_id: L001
    name: 中期动量反转
    category: market_structure
    research_status: active
    priority: 0.5
    admits: 0
    best_ic: 0.0
  - logic_id: L002
    ...
```

### Task 1.3: Update `.gitignore`

Add `storage/logic/snapshots/` to `.gitignore` (schedule snapshots are ephemeral operational artifacts, not source-controlled).

---

## Phase 2: Python Backend — `logic_library.py` Rewrite

### Task 2.1: Rewrite `MarketLogicLibrary` class

**File: `src/mining/logic_library.py`** — expand from 146 lines to ~350 lines.

Key changes to internal helpers:

```python
# v1: self._dir / f"{logic_id}.yaml"
# v2: self._dir / "cards" / f"logic_{logic_id}.yaml"

_VALID_STATUSES_V2 = {"proposed", "active", "warm", "productive", "saturated", "parked", "dead"}

def _card_path(self, logic_id: str) -> Path:
    return self._dir / "cards" / f"logic_{logic_id}.yaml"

def _proposal_path(self, proposal_id: str) -> Path:
    return self._dir / "proposals" / f"proposal_{proposal_id}.yaml"

def _review_path(self, proposal_id: str) -> Path:
    return self._dir / "reviews" / f"review_{proposal_id}.yaml"

def _registry_path(self) -> Path:
    return self._dir / "registry.yaml"

def _snapshot_dir(self) -> Path:
    return self._dir / "snapshots"
```

New `_scan_ids()` logic:
```python
def _scan_ids(self) -> List[str]:
    """Scan cards/ for logic_LXXX.yaml files."""
    pattern = re.compile(r"^logic_L(\d+)\.yaml$")
    cards_dir = self._dir / "cards"
    if not cards_dir.exists():
        # Fallback: scan root for v1 files (backward compat)
        return self._scan_ids_v1()
    ...
```

New `_read()` with auto-upgrade:
```python
def _read(self, logic_id: str) -> Optional[Dict[str, Any]]:
    # Try v2 path first
    path = self._card_path(logic_id)
    if not path.exists():
        # Fallback to v1 path
        path = self._dir / f"{logic_id}.yaml"
        if not path.exists():
            return None
    data = yaml.safe_load(path.read_text())
    if data.get("schema_version") != "v2":
        data = self._upgrade_v1_to_v2(data)
    return data
```

**New public methods** (additions to existing API):

```python
# --- Proposal lifecycle ---
def next_proposal_id(self) -> str:
    """Return next available PXXX id."""

def save_proposal(self, proposal: Dict[str, Any]) -> None:
    """Persist a proposal YAML (written by LLM, validated here)."""

def get_proposal(self, proposal_id: str) -> Optional[Dict[str, Any]]:
    """Read a proposal."""

def list_proposals(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all proposals."""

# --- Review lifecycle ---
def save_review(self, proposal_id: str, review: Dict[str, Any]) -> None:
    """Persist a review for a proposal."""

def get_review(self, proposal_id: str) -> Optional[Dict[str, Any]]:
    """Read review for a proposal."""

# --- Admit (proposal → card) ---
def admit_proposal(self, proposal_id: str, verdict: str, scores: Dict[str, float]) -> Optional[Dict[str, Any]]:
    """
    verdict: "create_logic" | "downgrade_to_direction" | "park" | "reject"
    If create_logic: creates card in cards/, returns the card.
    If park/reject: updates proposal status, returns None.
    """

# --- Evidence feedback (from /judge) ---
def update_evidence(self, logic_id: str, **kwargs: Any) -> None:
    """Update the evidence block. Replaces update_stats for v2."""

# --- Registry ---
def _sync_registry(self) -> None:
    """Rebuild registry.yaml from all card files."""

def get_registry(self) -> Dict[str, Any]:
    """Read registry.yaml."""

# --- Schedule snapshots ---
def save_schedule_snapshot(self, snapshot: Dict[str, Any]) -> Path:
    """Write a timestamped schedule snapshot. Returns path."""

def latest_schedule_snapshot(self) -> Optional[Dict[str, Any]]:
    """Read the most recent schedule snapshot."""
```

**Backward compatibility**: Keep `update_stats()` and `update_status()` working. They delegate to `update_evidence()` and the new status field internally:

```python
def update_stats(self, logic_id: str, **kwargs: Any) -> None:
    """v1-compat wrapper. Maps v1 stat names to v2 evidence fields."""
    evidence_map = {
        "factors_generated": "eval_attempts",
        "factors_admitted": "admits",
        "best_ic": "best_ic",
        "rounds_without_admit": None,  # handled specially
    }
    v2_kwargs = {}
    for k, v in kwargs.items():
        mapped = evidence_map.get(k, k)
        if mapped:
            v2_kwargs[mapped] = v
    self.update_evidence(logic_id, **v2_kwargs)

def update_status(self, logic_id: str, status: str) -> None:
    """v1-compat wrapper. Maps v1 status names to v2."""
    status_map = {"exhausted": "saturated", "archived": "parked"}
    v2_status = status_map.get(status, status)
    if v2_status not in _VALID_STATUSES_V2:
        raise ValueError(...)
    record = self._read(logic_id)
    record["research_status"] = v2_status
    self._write_card(record)
    self._sync_registry()
```

**Coverage map update**: Count statuses that represent "active research" (`active`, `warm`, `productive`):

```python
def coverage_map(self) -> Dict[str, int]:
    active_statuses = {"active", "warm", "productive"}
    counts = {}
    for record in self.list_logics():
        if record.get("research_status") in active_statuses:
            cat = record.get("category", "unknown")
            counts[cat] = counts.get(cat, 0) + 1
    return counts
```

### Task 2.2: Ensure `__init__` creates subdirectories

```python
def __init__(self, logic_dir: str) -> None:
    self._dir = Path(logic_dir)
    self._dir.mkdir(parents=True, exist_ok=True)
    for sub in ("cards", "proposals", "reviews", "snapshots"):
        (self._dir / sub).mkdir(exist_ok=True)
```

---

## Phase 3: Scheduler Rewrite

### Task 3.1: Rewrite `Scheduler` class

**File: `src/mining/scheduler.py`** — expand from 130 lines to ~250 lines.

**New scoring formula** (replaces `potential - fatigue`):

```python
def _score_one_v2(self, logic: Dict[str, Any], coverage: Dict[str, int], library_avg_ic: float) -> float:
    """
    priority = 0.25 * coverage_gap
             + 0.20 * novelty
             + 0.20 * feasibility
             + 0.15 * expected_value
             + 0.10 * complementarity
             + 0.10 * recent_research_signal
             - 0.10 * failure_density
    """
    scores = logic.get("scores", {})
    evidence = logic.get("evidence", {})

    # coverage_gap: category underrepresentation (0.0 to 1.0)
    cat = logic.get("category", "")
    cat_count = coverage.get(cat, 0)
    coverage_gap = max(0, 1.0 - cat_count / 3.0)  # 0 logics → 1.0, 3+ → 0.0

    novelty = scores.get("novelty_score", 0.5)
    feasibility = scores.get("feasibility_score", 0.5)
    expected_value = scores.get("expected_value_score", 0.5)
    complementarity = scores.get("complementarity_score", 0.5)

    # recent_research_signal: based on evidence
    admits = evidence.get("admits", 0)
    eval_attempts = evidence.get("eval_attempts", 0)
    best_ic = evidence.get("best_ic", 0)
    recent_signal = 0.0
    if admits > 0:
        recent_signal = min(1.0, admits / 3.0)
    elif best_ic and abs(best_ic) > library_avg_ic:
        recent_signal = 0.3

    # failure_density
    near_miss = evidence.get("near_miss", 0)
    if eval_attempts > 0:
        fail_rate = 1.0 - (admits / eval_attempts)
        failure_density = fail_rate * min(eval_attempts / 10.0, 1.0)
    else:
        failure_density = 0.0

    score = (0.25 * coverage_gap
           + 0.20 * novelty
           + 0.20 * feasibility
           + 0.15 * expected_value
           + 0.10 * complementarity
           + 0.10 * recent_signal
           - 0.10 * failure_density)

    return round(score, 4)
```

**Backward compat**: `_score_one()` checks `schema_version`. If v1, delegates to the old formula. If v2, uses the new formula. This way old tests pass unchanged.

```python
def _score_one(self, logic, coverage, library_avg_ic):
    if logic.get("schema_version") == "v2":
        return self._score_one_v2(logic, coverage, library_avg_ic)
    return self._score_one_v1(logic, coverage, library_avg_ic)
```

**New method: `generate_contracts()`**

```python
def generate_contracts(
    self,
    logics: List[Dict[str, Any]],
    coverage: Dict[str, int],
    library_avg_ic: float,
    top_n: int = 3,
) -> List[Dict[str, Any]]:
    """Generate exploration contracts for top-N logics.

    Each contract contains:
        logic_id, priority, direction_quota, candidate_quota,
        preferred_mode, preferred_families, suggested_ops,
        required_fields, avoid_patterns, current_focus_question
    """
    scored = self.score_logics(logics, coverage, library_avg_ic)
    contracts = []
    for logic_id, score in scored[:top_n]:
        if score <= 0:
            continue
        logic = next((l for l in logics if (l.get("logic_id") or l.get("id")) == logic_id), None)
        if not logic:
            continue
        budget = logic.get("budget", {})
        impl = logic.get("implementation_space", {})
        proxy = logic.get("observable_proxy", {})
        evidence = logic.get("evidence", {})
        contracts.append({
            "logic_id": logic_id,
            "priority": score,
            "direction_quota": budget.get("direction_quota", 3),
            "candidate_quota": budget.get("candidate_quota", 8),
            "preferred_mode": budget.get("preferred_mode", "genesis"),
            "preferred_families": impl.get("preferred_families", []),
            "suggested_ops": impl.get("suggested_ops", []),
            "required_fields": proxy.get("required_fields", []),
            "avoid_patterns": impl.get("forbidden_patterns", []),
            "current_focus_question": (evidence.get("next_actions") or ["explore broadly"])[0],
        })
    return contracts
```

**New method: `allocate_budget()`** (optional enhancement — adjusts quotas based on score distribution):

```python
def allocate_budget(self, contracts: List[Dict[str, Any]], total_candidates: int = 8) -> List[Dict[str, Any]]:
    """Adjust candidate_quota per contract proportional to priority score."""
    total_priority = sum(c["priority"] for c in contracts) or 1.0
    for c in contracts:
        c["candidate_quota"] = max(2, round(total_candidates * c["priority"] / total_priority))
    return contracts
```

---

## Phase 4: CLI Expansion

### Task 4.1: Expand `cmd_logic()` in `cli.py`

**File: `src/mining/cli.py`** — expand the `logic` subcommand from 4 actions to 8.

New `logic_action` choices: `["list", "coverage", "schedule", "create", "propose-init", "review-init", "admit", "review-state"]`

```python
elif args.logic_action == "propose-init":
    # Print next proposal ID + template for LLM to fill
    pid = lib.next_proposal_id()
    template = {
        "proposal_id": pid,
        "schema_version": "v2",
        "name": "",
        "origin_type": "llm_generated",
        "category": "",
        "thesis": "",
        "mechanism": "",
        "observable_proxy": {"required_fields": [], "optional_fields": []},
        "expected_horizon": {"formation_window": "", "holding_window": ""},
        "implementation_space": {
            "preferred_families": [],
            "suggested_ops": [],
            "discouraged_ops": [],
            "forbidden_patterns": [],
        },
        "novelty_claim": "",
        "probe_readiness": "",
        "relations_guess": {"parent_logic": None, "sibling_logics": [], "overlaps_with": []},
    }
    yaml.dump(template, sys.stdout, default_flow_style=False, allow_unicode=True, sort_keys=False)
    print(f"\n# Proposal ID: {pid}")
    print(f"# Write to: storage/logic/proposals/proposal_{pid}.yaml")

elif args.logic_action == "review-init":
    # Load proposal, print for LLM context
    proposal = lib.get_proposal(args.proposal_id)
    if not proposal:
        print(f"ERROR: Proposal {args.proposal_id} not found")
        sys.exit(1)
    print("# === Proposal for Review ===")
    yaml.dump(proposal, sys.stdout, ...)
    print(f"\n# Write review to: storage/logic/reviews/review_{args.proposal_id}.yaml")

elif args.logic_action == "admit":
    # Read proposal + review, execute admission
    proposal = lib.get_proposal(args.proposal_id)
    review = lib.get_review(args.proposal_id)
    if not proposal or not review:
        print("ERROR: need both proposal and review")
        sys.exit(1)
    gate = review.get("gate_summary", {})
    verdict = gate.get("verdict", "reject")
    scores = {k: r.get("score", 0.5) for k, r in review.items() if k.endswith("_review")}
    result = lib.admit_proposal(args.proposal_id, verdict, scores)
    if result:
        print(f"Created logic card: {result['logic_id']}")
    else:
        print(f"Proposal {args.proposal_id} → {verdict}")

elif args.logic_action == "schedule":
    # ENHANCED: now also writes snapshot + prints contracts
    sched = Scheduler()
    logics = lib.list_logics(research_status=["active", "warm", "productive"])
    if not logics:
        print("No active logics.")
        return
    coverage = lib.coverage_map()
    flib = FactorLibrary(config)
    factors = flib.list_factors()
    avg_ic = sum(abs(f.get("ic_mean", 0)) for f in factors) / max(len(factors), 1)

    scores = sched.score_logics(logics, coverage, avg_ic)
    print("Logic priority scores:")
    for lid, score in scores:
        logic = lib.get(lid)
        name = logic["name"] if logic else "?"
        print(f"  {lid} {name:30s} score={score:.4f}")

    contracts = sched.generate_contracts(logics, coverage, avg_ic)
    contracts = sched.allocate_budget(contracts)

    if contracts:
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "contracts": contracts,
            "trigger_outer_loop": False,
        }
        path = lib.save_schedule_snapshot(snapshot)
        print(f"\nExploration contracts ({len(contracts)}):")
        for c in contracts:
            print(f"  {c['logic_id']}: quota={c['candidate_quota']}, "
                  f"mode={c['preferred_mode']}, focus={c['current_focus_question']}")
        print(f"\nSnapshot saved: {path}")
    else:
        snapshot = {"timestamp": datetime.now().isoformat(), "contracts": [], "trigger_outer_loop": True}
        lib.save_schedule_snapshot(snapshot)
        print("\nAll scores non-positive — recommend running /logic propose (outer loop)")

elif args.logic_action == "review-state":
    # Comprehensive status view
    registry = lib.get_registry()
    logics_by_status = {}
    for entry in registry.get("logics", []):
        s = entry.get("research_status", "unknown")
        logics_by_status.setdefault(s, []).append(entry)
    for status in ["active", "warm", "productive", "saturated", "proposed", "parked", "dead"]:
        items = logics_by_status.get(status, [])
        if items:
            print(f"\n{status.upper()} ({len(items)}):")
            for item in items:
                print(f"  {item['logic_id']} {item['name']} "
                      f"(admits={item.get('admits', 0)}, best_ic={item.get('best_ic', 0):.3f})")
    # Coverage
    coverage = lib.coverage_map()
    if coverage:
        print("\nCoverage:")
        for cat, count in sorted(coverage.items()):
            bar = "#" * count
            print(f"  {cat:20s} {count:3d} {bar}")
    # Pending proposals
    proposals = lib.list_proposals()
    if proposals:
        print(f"\nPending proposals: {len(proposals)}")
        for p in proposals:
            print(f"  {p['proposal_id']} {p['name']}")
```

### Task 4.2: Update argparse for new subcommands

Add `--proposal-id` argument for `review-init` and `admit` actions:

```python
p_logic = sub.add_parser("logic", help="Manage and inspect market logics")
p_logic.add_argument("logic_action",
    choices=["list", "coverage", "schedule", "create",
             "propose-init", "review-init", "admit", "review-state"],
    help="Action to perform")
p_logic.add_argument("--status", default=None, help="Filter by status")
p_logic.add_argument("--proposal-id", default=None, help="Proposal ID for review-init/admit")
```

### Task 4.3: Update `list_logics` filter

The `list` action should accept the new v2 statuses. The `--status` filter already passes through to `list_logics()`, but need to support comma-separated statuses for convenience:

```python
if args.logic_action == "list":
    status_filter = getattr(args, "status", None)
    logics = lib.list_logics(status=status_filter)
    for l in logics:
        ev = l.get("evidence", l.get("stats", {}))
        print(f"  {l.get('logic_id', l.get('id'))} [{l.get('research_status', l.get('status'))}] "
              f"{l['name']} (cat={l['category']}, "
              f"eval={ev.get('eval_attempts', ev.get('factors_generated', 0))}, "
              f"adm={ev.get('admits', ev.get('factors_admitted', 0))})")
```

---

## Phase 5: Skill Rewrite

### Task 5.1: Rewrite `.claude/skills/factor-logic/skill.md`

Replace the current 85-line skill with ~300 lines covering 5 commands.

**Structure:**

```markdown
---
name: factor-logic
description: 管理市场逻辑假设生命周期（提案 → 审查 → 准入 → 调度）
user_invocable: true
---

# /logic — Market Logic Lifecycle Management

## /logic propose — 生成逻辑提案（外循环入口）

### 第1步：读取当前状态
- `PYTHONPATH=src python3 -m mining logic review-state`
- `PYTHONPATH=src python3 -m mining logic coverage`
- `cat storage/logic/taxonomy.yaml`
- `cat storage/memory/forbidden.yaml`

### 第2步：获取提案模板
- `PYTHONPATH=src python3 -m mining logic propose-init`
  (prints next ID + YAML template)

### 第3步：LLM 生成 2-5 个提案
For each coverage gap or new research direction:
- Fill in thesis (full paragraph explaining the market belief)
- Fill in mechanism (causal explanation)
- Fill in observable_proxy, expected_horizon, implementation_space
- Write each proposal via Write tool to `storage/logic/proposals/proposal_PXXX.yaml`

### 第4步：确认
- `ls storage/logic/proposals/`
- Print summary of generated proposals

## /logic review — 审查提案（四维评估）

### 第1步：选择待审查提案
- `PYTHONPATH=src python3 -m mining logic review-init --proposal-id PXXX`

### 第2步：LLM 四维审查
For the proposal, evaluate:
1. **mechanism_review**: Is the causal mechanism plausible?
2. **feasibility_review**: Can this be implemented with available data/ops?
3. **novelty_review**: Does this overlap with existing logics?
4. **research_value_review**: Is the expected information gain worth the compute?

Each review: `{verdict: pass/weak_pass/fail, score: 0.0-1.0, comments: "..."}`

Gate summary: `{verdict: create_logic/downgrade_to_direction/park/reject, ...}`

### 第3步：写入审查结果
Write via Write tool to `storage/logic/reviews/review_PXXX.yaml`

## /logic admit — 准入决策

### 第1步：执行准入
- `PYTHONPATH=src python3 -m mining logic admit --proposal-id PXXX`

### 第2步：确认结果
- `PYTHONPATH=src python3 -m mining logic list`

## /logic schedule — 调度与预算分配

### 第1步：生成调度快照
- `PYTHONPATH=src python3 -m mining logic schedule`
  (prints scores + contracts, writes snapshot)

### 第2步：解读结果
Explain the scheduling decisions to the user.

## /logic review-state — 综合状态查看

- `PYTHONPATH=src python3 -m mining logic review-state`
```

### Task 5.2: Update `/idea` skill to consume exploration contracts

**File: `.claude/skills/factor-idea/skill.md`**

In 第1.5步 (Scheduler & Mode Selection), replace:

```bash
# OLD:
PYTHONPATH=src python3 -m mining logic schedule
PYTHONPATH=src python3 -m mining logic coverage
```

With:

```bash
# NEW: Read latest schedule snapshot
PYTHONPATH=src python3 -m mining logic schedule
cat "$(ls -t storage/logic/snapshots/schedule_*.yaml | head -1)"
```

Then use the contracts array to:
- Select which logics to explore (from `contracts[].logic_id`)
- Respect `candidate_quota` per logic
- Use `preferred_families` and `suggested_ops` to guide generation
- Respect `avoid_patterns` as hard exclusions
- Use `current_focus_question` as the exploration prompt

Add to the candidate YAML:
```yaml
candidates:
  - name: "..."
    expression: "..."
    logic_id: L003        # from contract
    contract_mode: genesis  # from contract.preferred_mode
```

### Task 5.3: Update `/judge` skill for v2 evidence feedback

**File: `.claude/skills/factor-judge/skill.md`**

In step 4j (Logic Feedback), replace:

```python
# OLD:
logic_lib.update_stats(logic_id,
    factors_generated=N_generated,
    factors_admitted=N_admitted,
    best_ic=max_ic,
    rounds_without_admit=0 if N_admitted > 0 else current+1)
if rounds_without_admit >= 3:
    logic_lib.update_status(logic_id, "saturated")
```

With:

```python
# NEW:
logic_lib.update_evidence(logic_id,
    probe_attempts=probe_count,
    eval_attempts=eval_count,
    admits=admit_count,
    near_miss=near_miss_count,
    best_ic=max(current_best, new_best),
    best_incremental_ic=max_incremental,
    productive_families=productive_ops,
    failed_families=failed_ops,
    current_bottleneck=bottleneck_reason,
)

# Status transitions based on evidence
evidence = logic_lib.get(logic_id).get("evidence", {})
total_admits = evidence.get("admits", 0)
total_evals = evidence.get("eval_attempts", 0)
if total_admits >= 3:
    logic_lib.update_status(logic_id, "productive")
elif total_admits > 0:
    logic_lib.update_status(logic_id, "warm")
elif total_evals >= 15 and total_admits == 0:
    logic_lib.update_status(logic_id, "saturated")
```

The `update_stats()` v1-compat wrapper ensures this transition is smooth.

### Task 5.4: Update `/mine` skill for v2 schedule check

**File: `.claude/skills/factor-mine/skill.md`**

In 阶段零 (Scheduler Pre-flight), update the check:

```bash
# Enhanced: schedule now writes snapshot
PYTHONPATH=src python3 -m mining logic schedule
```

If output contains "recommend running /logic propose":
- Replace: `/logic new`
- With: `/logic propose` then `/logic review` then `/logic admit`

---

## Phase 6: Tests

### Task 6.1: Update existing tests to pass

**File: `tests/mining/test_logic_library.py`**

The existing tests create `MarketLogicLibrary(str(logic_dir))` and call `create()`, `get()`, etc. Since v2 backward compat is built in:
- `create()` should still work but now creates v2 cards in `cards/` subdirectory
- `get()` should still return records (with v2 schema)
- `update_stats()` should still work (delegates to `update_evidence()`)
- `update_status()` should still work (maps v1→v2 statuses)
- `list_logics()` should still work

Key changes needed:
- Assertions checking `record["id"]` should also accept `record["logic_id"]`
- Assertions checking `record["status"]` should also accept `record["research_status"]`
- Assertions checking `record["stats"]["factors_generated"]` should also accept `record["evidence"]["eval_attempts"]`

**Strategy**: Add a helper to normalize field access:

```python
def _get_id(record):
    return record.get("logic_id") or record.get("id")

def _get_status(record):
    return record.get("research_status") or record.get("status")
```

Then update assertions minimally. The `_VALID_STATUSES` set in the test for `update_status` needs updating to accept v2 status names.

**However**, the better approach is to keep the v1-compat `update_status()` accepting the old status names and mapping them. The test calls `update_status("L001", "exhausted")` — our compat wrapper maps `"exhausted"` → `"saturated"` and stores it. But then the test asserts `record["status"] == "exhausted"` which will fail since v2 stores `research_status: saturated`.

**Resolution**: The `get()` method returns v2 records. We need the `create()` method to return a v2 record but with backward-compat accessor. Best approach: add a property-like wrapper OR update the tests to check v2 fields. I recommend **updating the tests** since they are internal and the v1 schema is being retired.

### Task 6.2: New tests for v2 functionality

**File: `tests/mining/test_logic_library_v2.py`** (new file)

```python
class TestProposalLifecycle:
    def test_next_proposal_id_empty(self, library):
        assert library.next_proposal_id() == "P001"

    def test_save_and_get_proposal(self, library):
        proposal = {"proposal_id": "P001", "schema_version": "v2", "name": "test", ...}
        library.save_proposal(proposal)
        result = library.get_proposal("P001")
        assert result["name"] == "test"

    def test_list_proposals(self, library):
        ...

class TestReviewLifecycle:
    def test_save_and_get_review(self, library):
        ...

class TestAdmitProposal:
    def test_admit_creates_card(self, library):
        # Setup: save proposal + review
        # Call admit_proposal with verdict="create_logic"
        # Assert card exists in cards/
        # Assert registry updated

    def test_reject_does_not_create_card(self, library):
        ...

    def test_park_updates_proposal_status(self, library):
        ...

class TestUpdateEvidence:
    def test_update_evidence_merges(self, library):
        ...

    def test_update_evidence_nonexistent_raises(self, library):
        ...

class TestRegistry:
    def test_registry_auto_maintained(self, library):
        ...

    def test_registry_reflects_status_changes(self, library):
        ...

class TestCoverageMapV2:
    def test_counts_active_warm_productive(self, library):
        ...
```

### Task 6.3: New tests for v2 scheduler

**File: `tests/mining/test_scheduler_v2.py`** (new file)

```python
class TestScoreV2:
    def test_v2_formula_weights(self):
        ...

    def test_v2_coverage_gap_calculation(self):
        ...

    def test_v2_failure_density(self):
        ...

class TestGenerateContracts:
    def test_contracts_structure(self):
        ...

    def test_contracts_exclude_non_positive(self):
        ...

    def test_allocate_budget_proportional(self):
        ...
```

### Task 6.4: Update CLI tests

**File: `tests/mining/test_cli.py`**

Add tests for new subcommands:
- `test_propose_init_prints_template`
- `test_review_state_no_crash`
- `test_admit_missing_proposal_errors`

### Task 6.5: Ensure old scheduler tests pass

The key is that `_score_one()` dispatches based on `schema_version`. The existing `make_logic()` helper in `test_scheduler.py` creates v1-shaped dicts (no `schema_version` field), so they will route to `_score_one_v1()` and pass unchanged.

---

## Phase 7: Integration Verification

### Task 7.1: Run migration on real data

```bash
PYTHONPATH=src python3 scripts/migrate_logic_v2.py
```

Verify:
- 14 cards created in `storage/logic/cards/`
- `registry.yaml` has 14 entries
- All statuses mapped correctly
- `taxonomy.yaml` untouched

### Task 7.2: End-to-end smoke test

1. `PYTHONPATH=src python3 -m mining logic review-state` — shows all 14 migrated logics
2. `PYTHONPATH=src python3 -m mining logic schedule` — generates contracts, writes snapshot
3. `PYTHONPATH=src python3 -m mining logic propose-init` — prints P001 template
4. Manually create a proposal, review, and admit it
5. `PYTHONPATH=src python3 -m mining logic list` — shows 15 logics (14 migrated + 1 new)

### Task 7.3: Run full test suite

```bash
pytest -v
```

All existing tests must pass. New tests must pass.

---

## Execution Order & Dependencies

```
Phase 1 (Storage + Migration)
  ├── Task 1.1: directories      (no deps)
  ├── Task 1.2: migration script  (no deps)
  └── Task 1.3: .gitignore        (no deps)

Phase 2 (logic_library.py rewrite)
  └── Task 2.1-2.2                (depends on Phase 1 design decisions)

Phase 3 (scheduler.py rewrite)
  └── Task 3.1                    (depends on Phase 2 for v2 schema shape)

Phase 4 (cli.py expansion)
  └── Task 4.1-4.3                (depends on Phase 2 + 3)

Phase 5 (skill rewrite)
  ├── Task 5.1: /logic skill      (depends on Phase 4)
  ├── Task 5.2: /idea skill       (depends on Phase 3 contracts)
  ├── Task 5.3: /judge skill      (depends on Phase 2 update_evidence)
  └── Task 5.4: /mine skill       (depends on Phase 4 schedule)

Phase 6 (tests)
  ├── Task 6.1: update existing   (depends on Phase 2)
  ├── Task 6.2-6.4: new tests     (depends on Phase 2-4)
  └── Task 6.5: verify old tests  (depends on Phase 3)

Phase 7 (integration)
  └── Task 7.1-7.3                (depends on all above)
```

**Recommended implementation order for parallel work:**
1. Phase 1 (quick, mechanical)
2. Phase 2 + Phase 6.1 in parallel (library + test updates)
3. Phase 3 + Phase 6.3 (scheduler + new scheduler tests)
4. Phase 4 + Phase 6.4 (CLI + CLI tests)
5. Phase 5 (skills — can be done last since they are markdown)
6. Phase 6.2 (new library tests, after API is stable)
7. Phase 7 (integration, last)

---

## Risk Assessment

| Risk | Mitigation |
|------|-----------|
| Breaking `/judge` feedback loop | v1-compat `update_stats()`/`update_status()` wrappers |
| Breaking `/idea` contract consumption | `/idea` falls back to old `logic schedule` stdout if no snapshot file exists |
| Migration data loss | Original v1 files kept as backup; script is idempotent |
| Registry drift | Auto-sync on every mutation; registry is derived, not authoritative |
| Test breakage from schema change | `_score_one()` dispatches on `schema_version`; old test dicts have no version → old formula |
| Skill step ordering mistakes | Each skill command is self-contained; LLM writes YAML, Python validates |

---

## Files Modified (Summary)

| File | Action | Est. Lines |
|------|--------|-----------|
| `src/mining/logic_library.py` | **Major rewrite** | 146 → ~400 |
| `src/mining/scheduler.py` | **Major rewrite** | 130 → ~280 |
| `src/mining/cli.py` | **Expand** cmd_logic section | +120 |
| `src/mining/config.py` | Minor: no changes needed (`logic_dir` already correct) | 0 |
| `src/mining/__init__.py` | No changes needed (already exports both classes) | 0 |
| `.claude/skills/factor-logic/skill.md` | **Full rewrite** | 85 → ~300 |
| `.claude/skills/factor-idea/skill.md` | **Update** step 1.5 | ~20 lines changed |
| `.claude/skills/factor-judge/skill.md` | **Update** step 4j | ~15 lines changed |
| `.claude/skills/factor-mine/skill.md` | **Update** phase 0 | ~10 lines changed |
| `scripts/migrate_logic_v2.py` | **New** | ~120 |
| `tests/mining/test_logic_library.py` | **Update** assertions | ~30 lines changed |
| `tests/mining/test_logic_library_v2.py` | **New** | ~200 |
| `tests/mining/test_scheduler_v2.py` | **New** | ~100 |
| `tests/mining/test_cli.py` | **Expand** | +40 |
| `storage/logic/cards/.gitkeep` | **New** | 0 |
| `storage/logic/proposals/.gitkeep` | **New** | 0 |
| `storage/logic/reviews/.gitkeep` | **New** | 0 |
| `storage/logic/snapshots/.gitkeep` | **New** | 0 |
