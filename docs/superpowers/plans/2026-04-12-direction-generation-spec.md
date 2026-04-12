# Direction Generation Specification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement structured direction creation with LogicCard field mapping, thread lifecycle driven by judge verdicts, and auto-connection context chain across all 5 phases.

**Architecture:** Extend direction.md from a bare skeleton to a full LogicCard-mapped document with Hypothesis/Contract/Threads/Families/Narrative sections. Phase 3 judge writes `thread_impact` per candidate; Phase 4 cascades thread status changes to direction.md and enriches INDEX.md for LLM self-selection. manifest.yaml gains `thread_refs`, `design_rationale`, `context_loaded` fields.

**Tech Stack:** Python 3.8+, pytest, YAML frontmatter parsing, regex-based markdown section manipulation

---

## File Structure

### New files
- None (all changes are extensions to existing files)

### Modified files

| File | Responsibility |
|---|---|
| `src/research/phases/phase1_start.py` | Add `validate_direction()`, `DIRECTION_CATEGORIES`, new manifest fields |
| `src/research/memory/direction_updater.py` | Add `update_thread_statuses()`, parse/rewrite thread lines in body |
| `src/research/memory/index_refresher.py` | Add `category`, `priority`, `open_threads`, `top_ic` columns |
| `src/research/checkpoints/audit.py` | Add check #7: `thread_impact` validation |
| `src/research/checkpoints/generator.py` | Inject thread list from direction.md into judge_packet |
| `src/research/phases/phase4_archive.py` | Call extended `update_thread_statuses` with judge verdict data |
| `src/research/domain/contracts.py` | Mark `LogicCard` deprecated |
| `.claude/skills/factor-idea/skill.md` | Add direction creation spec + 5-step reasoning chain |
| `.claude/skills/factor-judge/skill.md` | Add `thread_impact` to judge.md schema |
| `.claude/skills/factor-mine/skill.md` | Add `context_loaded` to Step 2, adjust Step 1 |
| `tests/research/phases/test_phase1_start.py` | Tests for `validate_direction()` + new manifest fields |
| `tests/research/memory/test_direction_updater.py` | Tests for `update_thread_statuses()` |
| `tests/research/memory/test_index_refresher.py` | Tests for new columns |
| `tests/research/checkpoints/test_audit.py` | Tests for thread_impact audit check |

---

### Task 1: Add direction validation to phase1_start.py

**Files:**
- Modify: `src/research/phases/phase1_start.py`
- Test: `tests/research/phases/test_phase1_start.py`

- [ ] **Step 1: Write failing tests for validate_direction**

```python
# In tests/research/phases/test_phase1_start.py — new class

class TestValidateDirection:
    def test_valid_direction_passes(self) -> None:
        reasons = validate_direction(
            direction_id="candlestick_micro",
            category="microstructure",
            hypothesis_text="Condition: ... Behavior: ... Mechanism: ... (300+ chars)",
            mechanism_text="Behavioral bias explanation here, more than 50 chars total.",
            anti_hypothesis_text="If shadow is noise then fail.",
            threads=["T001 [open] test shadow", "T002 [open] test body", "T003 [open] test lower"],
            existing_direction_ids=[],
        )
        assert reasons == []

    def test_short_hypothesis_rejected(self) -> None:
        reasons = validate_direction(
            direction_id="x", category="microstructure",
            hypothesis_text="short", mechanism_text="m" * 51,
            anti_hypothesis_text="anti", threads=["T001", "T002", "T003"],
            existing_direction_ids=[],
        )
        assert any("hypothesis_too_short" in r for r in reasons)

    def test_missing_mechanism_rejected(self) -> None:
        reasons = validate_direction(
            direction_id="test_dir", category="microstructure",
            hypothesis_text="h" * 301, mechanism_text="short",
            anti_hypothesis_text="anti", threads=["T001", "T002", "T003"],
            existing_direction_ids=[],
        )
        assert any("mechanism_too_short" in r for r in reasons)

    def test_missing_anti_hypothesis_rejected(self) -> None:
        reasons = validate_direction(
            direction_id="test_dir", category="microstructure",
            hypothesis_text="h" * 301, mechanism_text="m" * 51,
            anti_hypothesis_text="", threads=["T001", "T002", "T003"],
            existing_direction_ids=[],
        )
        assert any("missing_anti_hypothesis" in r for r in reasons)

    def test_too_few_threads_rejected(self) -> None:
        reasons = validate_direction(
            direction_id="test_dir", category="microstructure",
            hypothesis_text="h" * 301, mechanism_text="m" * 51,
            anti_hypothesis_text="anti", threads=["T001"],
            existing_direction_ids=[],
        )
        assert any("too_few_threads" in r for r in reasons)

    def test_invalid_category_rejected(self) -> None:
        reasons = validate_direction(
            direction_id="test_dir", category="invalid_cat",
            hypothesis_text="h" * 301, mechanism_text="m" * 51,
            anti_hypothesis_text="anti", threads=["T001", "T002", "T003"],
            existing_direction_ids=[],
        )
        assert any("invalid_category" in r for r in reasons)

    def test_bad_direction_id_rejected(self) -> None:
        reasons = validate_direction(
            direction_id="This Has Spaces And Is Way Too Long For A Direction ID Slug Really",
            category="microstructure",
            hypothesis_text="h" * 301, mechanism_text="m" * 51,
            anti_hypothesis_text="anti", threads=["T001", "T002", "T003"],
            existing_direction_ids=[],
        )
        assert any("invalid_direction_id" in r for r in reasons)

    def test_duplicate_direction_rejected(self) -> None:
        reasons = validate_direction(
            direction_id="existing_dir", category="microstructure",
            hypothesis_text="h" * 301, mechanism_text="m" * 51,
            anti_hypothesis_text="anti", threads=["T001", "T002", "T003"],
            existing_direction_ids=["existing_dir"],
        )
        assert any("duplicate_direction" in r for r in reasons)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/research/phases/test_phase1_start.py::TestValidateDirection -v`
Expected: FAIL — `validate_direction` not defined

- [ ] **Step 3: Implement validate_direction + DIRECTION_CATEGORIES**

In `src/research/phases/phase1_start.py`, add:

```python
DIRECTION_CATEGORIES: frozenset[str] = frozenset({
    "microstructure", "volume", "fundamental", "momentum",
    "volatility", "liquidity", "cross_field", "timing", "regime",
})

MIN_HYPOTHESIS_LENGTH = 300
MIN_MECHANISM_LENGTH = 50
MIN_THREADS = 3
MAX_DIRECTION_ID_LENGTH = 40
_DIRECTION_ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def validate_direction(
    direction_id: str,
    category: str,
    hypothesis_text: str,
    mechanism_text: str,
    anti_hypothesis_text: str,
    threads: list[str],
    existing_direction_ids: Iterable[str],
) -> list[str]:
    reasons: list[str] = []
    if not _DIRECTION_ID_RE.match(direction_id) or len(direction_id) > MAX_DIRECTION_ID_LENGTH:
        reasons.append(f"invalid_direction_id:{direction_id}")
    if direction_id in set(existing_direction_ids):
        reasons.append(f"duplicate_direction:{direction_id}")
    if category not in DIRECTION_CATEGORIES:
        reasons.append(f"invalid_category:{category}")
    if len((hypothesis_text or "").strip()) < MIN_HYPOTHESIS_LENGTH:
        reasons.append(f"hypothesis_too_short:{len((hypothesis_text or '').strip())}<{MIN_HYPOTHESIS_LENGTH}")
    if len((mechanism_text or "").strip()) < MIN_MECHANISM_LENGTH:
        reasons.append(f"mechanism_too_short:{len((mechanism_text or '').strip())}<{MIN_MECHANISM_LENGTH}")
    if not (anti_hypothesis_text or "").strip():
        reasons.append("missing_anti_hypothesis")
    if len(threads) < MIN_THREADS:
        reasons.append(f"too_few_threads:{len(threads)}<{MIN_THREADS}")
    return reasons
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/research/phases/test_phase1_start.py::TestValidateDirection -v`
Expected: all PASS

- [ ] **Step 5: Extend freeze_manifest to accept new fields**

Add `thread_refs`, `design_rationale`, `context_loaded` to manifest.yaml output. These are pass-through fields — Phase 1 records them but doesn't validate their content (that's the LLM's job). The test verifies they round-trip through freeze.

- [ ] **Step 6: Write test for new manifest fields**

```python
def test_manifest_includes_thread_refs(self, tmp_path: Path) -> None:
    manifest_path = tmp_path / "batch_thr" / "manifest.yaml"
    report = freeze_manifest(
        batch_id="batch_thr",
        direction="volatility",
        batch_goal=self._goal(),
        candidates=[
            {
                "candidate_id": "C001",
                "source_type": "dsl",
                "expression": "Std($close, 20)",
                "thread_refs": ["T001", "T002"],
                "design_rationale": "Test vol clustering under high turnover",
            },
        ],
        existing_canonicals=[],
        manifest_path=manifest_path,
        context_loaded=["vault/INDEX.md", "vault/lessons.md"],
    )
    loaded = load_yaml(manifest_path)
    assert loaded["context_loaded"] == ["vault/INDEX.md", "vault/lessons.md"]
    assert loaded["candidates"][0]["thread_refs"] == ["T001", "T002"]
    assert loaded["candidates"][0]["design_rationale"].startswith("Test")
```

- [ ] **Step 7: Run full Phase 1 test suite**

Run: `pytest tests/research/phases/test_phase1_start.py -v`
Expected: all PASS

- [ ] **Step 8: Commit**

```
git add src/research/phases/phase1_start.py tests/research/phases/test_phase1_start.py
git commit -m "feat(phase1): add validate_direction + manifest thread_refs/context_loaded"
```

---

### Task 2: Extend direction_updater with thread status updates

**Files:**
- Modify: `src/research/memory/direction_updater.py`
- Test: `tests/research/memory/test_direction_updater.py`

- [ ] **Step 1: Write failing tests for update_thread_statuses**

```python
class TestUpdateThreadStatuses:
    def _make_direction(self, tmp_path: Path) -> Path:
        path = tmp_path / "dirs" / "micro.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "---\ndirection_id: micro\nrounds: 1\nadmits: 0\nmembers: []\nstatus: active\n---\n"
            "\n# micro\n\n## Threads\n\n"
            "- T001 [open] test shadow product signal\n"
            "- T002 [open] test body ratio variance\n"
            "- T003 [open] test lower shadow alpha\n",
            encoding="utf-8",
        )
        return path

    def test_updates_single_thread(self, tmp_path: Path) -> None:
        path = self._make_direction(tmp_path)
        update_thread_statuses(
            path,
            thread_impacts=[
                {"thread": "T001", "new_status": "confirmed", "evidence": "F053 mono=-1.0"},
            ],
        )
        text = path.read_text(encoding="utf-8")
        assert "T001 [answered:confirmed]" in text
        assert "T002 [open]" in text  # unchanged

    def test_updates_multiple_threads(self, tmp_path: Path) -> None:
        path = self._make_direction(tmp_path)
        update_thread_statuses(
            path,
            thread_impacts=[
                {"thread": "T001", "new_status": "confirmed", "evidence": "F053"},
                {"thread": "T003", "new_status": "refuted", "evidence": "all reject CP02"},
            ],
        )
        text = path.read_text(encoding="utf-8")
        assert "T001 [answered:confirmed]" in text
        assert "T003 [answered:refuted]" in text
        assert "T002 [open]" in text

    def test_unchanged_status_noop(self, tmp_path: Path) -> None:
        path = self._make_direction(tmp_path)
        update_thread_statuses(
            path,
            thread_impacts=[
                {"thread": "T002", "new_status": "unchanged"},
            ],
        )
        text = path.read_text(encoding="utf-8")
        assert "T002 [open]" in text

    def test_preserves_frontmatter(self, tmp_path: Path) -> None:
        path = self._make_direction(tmp_path)
        update_thread_statuses(
            path,
            thread_impacts=[
                {"thread": "T001", "new_status": "confirmed", "evidence": "F053"},
            ],
        )
        fm = _read_fm(path)
        assert fm["direction_id"] == "micro"
        assert fm["rounds"] == 1

    def test_missing_thread_id_ignored(self, tmp_path: Path) -> None:
        path = self._make_direction(tmp_path)
        update_thread_statuses(
            path,
            thread_impacts=[
                {"thread": "T999", "new_status": "confirmed", "evidence": "ghost"},
            ],
        )
        text = path.read_text(encoding="utf-8")
        # Body unchanged
        assert "T001 [open]" in text
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/research/memory/test_direction_updater.py::TestUpdateThreadStatuses -v`
Expected: FAIL — `update_thread_statuses` not importable

- [ ] **Step 3: Implement update_thread_statuses**

In `direction_updater.py`, add:

```python
_THREAD_LINE_RE = re.compile(
    r"^(?P<prefix>- (?P<tid>T\d+) )\[(?P<status>[^\]]+)\](?P<rest>.*)$",
    re.MULTILINE,
)

VALID_THREAD_STATUSES: frozenset[str] = frozenset({
    "confirmed", "refuted", "inconclusive", "unchanged",
})


def update_thread_statuses(
    direction_path: str | Path,
    thread_impacts: list[dict[str, str]],
) -> int:
    """Rewrite thread status markers in the direction body.

    Returns the number of threads actually updated.
    """
    path = Path(direction_path)
    if not path.exists():
        return 0

    fm, body = _parse_or_init(path)
    updated = 0

    impact_map = {
        ti["thread"]: ti for ti in thread_impacts
        if ti.get("new_status") and ti["new_status"] != "unchanged"
    }

    def _replace_thread(m: re.Match) -> str:
        nonlocal updated
        tid = m.group("tid")
        if tid not in impact_map:
            return m.group(0)
        new_status = impact_map[tid]["new_status"]
        if new_status in ("confirmed", "refuted", "inconclusive"):
            new_status = f"answered:{new_status}"
        updated += 1
        return f"{m.group('prefix')}[{new_status}]{m.group('rest')}"

    new_body = _THREAD_LINE_RE.sub(_replace_thread, body)

    path.write_text(_serialize(fm, new_body), encoding="utf-8")
    return updated
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/research/memory/test_direction_updater.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```
git add src/research/memory/direction_updater.py tests/research/memory/test_direction_updater.py
git commit -m "feat(direction): add update_thread_statuses for judge-driven thread lifecycle"
```

---

### Task 3: Extend index_refresher with new columns

**Files:**
- Modify: `src/research/memory/index_refresher.py`
- Test: `tests/research/memory/test_index_refresher.py`

- [ ] **Step 1: Write failing tests for new columns**

```python
class TestNewColumns:
    def test_direction_stats_include_category_and_priority(self, tmp_path: Path) -> None:
        paths = _bootstrap(tmp_path)
        # Write a direction with full frontmatter
        d = paths.direction_file("micro")
        d.write_text(
            "---\ndirection_id: micro\nstatus: active\npriority: high\n"
            "category: microstructure\nrounds: 2\nadmits: 1\n"
            "last_batch: batch_005\nmembers: [F053]\n---\n"
            "\n# micro\n\n## Threads\n\n"
            "- T001 [answered:confirmed] shadow\n"
            "- T002 [open] body ratio\n"
            "- T003 [open] lower shadow\n",
            encoding="utf-8",
        )
        rows = collect_direction_stats(paths.directions_dir)
        assert len(rows) == 1
        assert rows[0]["category"] == "microstructure"
        assert rows[0]["priority"] == "high"
        assert rows[0]["open_threads"] == "2/3"

    def test_render_includes_new_columns(self) -> None:
        rows = [{
            "direction_id": "micro", "status": "active", "category": "microstructure",
            "priority": "high", "rounds": 2, "admits": 1, "open_threads": "2/3",
            "top_ic": 0.021, "last_batch": "batch_005",
        }]
        text = render_auto_section(rows, total_admitted=1, round_counter=5, last_consolidation_round=None)
        assert "| micro |" in text
        assert "microstructure" in text
        assert "2/3" in text
```

- [ ] **Step 2: Run tests to verify failure**
- [ ] **Step 3: Implement new columns**

Extend `collect_direction_stats` to read `category`, `priority` from frontmatter, and count open/total threads by scanning body for `- T\d+ \[(open|answered:...)\]` lines. Extend `render_auto_section` table header.

- [ ] **Step 4: Run full index_refresher tests**

Run: `pytest tests/research/memory/test_index_refresher.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```
git add src/research/memory/index_refresher.py tests/research/memory/test_index_refresher.py
git commit -m "feat(index): add category/priority/open_threads/top_ic columns"
```

---

### Task 4: Add thread_impact audit check

**Files:**
- Modify: `src/research/checkpoints/audit.py`
- Test: `tests/research/checkpoints/test_audit.py`

- [ ] **Step 1: Write failing test**

```python
class TestThreadImpactAudit:
    def test_valid_thread_impact_passes(self, tmp_path: Path) -> None:
        # Build a judge.md with valid thread_impact
        judge_md = _build_judge_md(
            candidates=[{
                "candidate_id": "C001", "verdict": "admit",
                "hard_gate_result": "all_pass",
                "thread_impact": [
                    {"thread": "T001", "new_status": "confirmed", "evidence": "mono=-1.0"},
                ],
            }],
        )
        path = tmp_path / "judge.md"
        path.write_text(judge_md, encoding="utf-8")
        parsed = audit_judge_md(path)  # should not raise

    def test_invalid_thread_status_rejected(self, tmp_path: Path) -> None:
        judge_md = _build_judge_md(
            candidates=[{
                "candidate_id": "C001", "verdict": "admit",
                "hard_gate_result": "all_pass",
                "thread_impact": [
                    {"thread": "T001", "new_status": "invalid_status", "evidence": "x"},
                ],
            }],
        )
        path = tmp_path / "judge.md"
        path.write_text(judge_md, encoding="utf-8")
        with pytest.raises(JudgeAuditError, match="thread_impact.*invalid"):
            audit_judge_md(path)

    def test_admit_without_thread_impact_passes(self, tmp_path: Path) -> None:
        # thread_impact is optional — backward compat
        judge_md = _build_judge_md(
            candidates=[{
                "candidate_id": "C001", "verdict": "admit",
                "hard_gate_result": "all_pass",
            }],
        )
        path = tmp_path / "judge.md"
        path.write_text(judge_md, encoding="utf-8")
        parsed = audit_judge_md(path)  # should not raise
```

- [ ] **Step 2: Run tests to verify failure**
- [ ] **Step 3: Implement `_check_thread_impact`**

```python
VALID_THREAD_IMPACT_STATUSES: frozenset[str] = frozenset({
    "confirmed", "refuted", "inconclusive", "unchanged",
})

def _check_thread_impact(fm: dict[str, Any]) -> None:
    for c in fm["candidates"]:
        impacts = c.get("thread_impact")
        if impacts is None:
            continue
        if not isinstance(impacts, list):
            raise JudgeAuditError(
                f"candidate {c['candidate_id']!r}: thread_impact must be a list"
            )
        for ti in impacts:
            if not isinstance(ti, dict):
                raise JudgeAuditError(...)
            status = ti.get("new_status", "")
            if status not in VALID_THREAD_IMPACT_STATUSES:
                raise JudgeAuditError(
                    f"candidate {c['candidate_id']!r}: thread_impact new_status "
                    f"{status!r} invalid (must be one of {sorted(VALID_THREAD_IMPACT_STATUSES)})"
                )
```

Add `_check_thread_impact(parsed.frontmatter)` call to `audit_judge_md`.

- [ ] **Step 4: Run full audit tests**

Run: `pytest tests/research/checkpoints/test_audit.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```
git add src/research/checkpoints/audit.py tests/research/checkpoints/test_audit.py
git commit -m "feat(audit): add thread_impact validation (check #7)"
```

---

### Task 5: Extend generator.py to inject threads into judge_packet

**Files:**
- Modify: `src/research/checkpoints/generator.py`
- Test: `tests/research/checkpoints/test_generator.py`

- [ ] **Step 1: Add threads_excerpt field to PacketContext**

```python
@dataclass
class PacketContext:
    direction_excerpt: str = ""
    lessons_excerpt: str = ""
    nearest_factor_excerpt: str = ""
    threads_excerpt: str = ""  # NEW: thread list from direction.md
```

- [ ] **Step 2: Inject threads section in build_judge_packet**

After the Direction Context section, add:

```python
if inputs.context.threads_excerpt.strip():
    parts.append("## Direction Threads")
    parts.append("")
    parts.append(inputs.context.threads_excerpt.strip())
    parts.append("")
```

- [ ] **Step 3: Add thread_refs from manifest to per-candidate section**

In `_candidate_section`, show `thread_refs` if present in candidate dict.

- [ ] **Step 4: Run generator tests**

Run: `pytest tests/research/checkpoints/test_generator.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```
git add src/research/checkpoints/generator.py tests/research/checkpoints/test_generator.py
git commit -m "feat(generator): inject direction threads into judge_packet"
```

---

### Task 6: Wire phase4_archive to cascade thread updates

**Files:**
- Modify: `src/research/phases/phase4_archive.py`
- Test: `tests/research/phases/test_phase4_archive.py`

- [ ] **Step 1: Parse thread_impact from judge frontmatter**

In `run_phase4_archive`, after reading `judge_fm`, collect all `thread_impact` entries:

```python
all_thread_impacts = []
for c in judge_fm.get("candidates", []):
    for ti in c.get("thread_impact") or []:
        all_thread_impacts.append(ti)
```

- [ ] **Step 2: Call update_thread_statuses**

```python
from research.memory.direction_updater import update_thread_statuses

if all_thread_impacts:
    update_thread_statuses(direction_path, all_thread_impacts)
```

- [ ] **Step 3: Run phase4 tests**

Run: `pytest tests/research/phases/test_phase4_archive.py -v`
Expected: all PASS

- [ ] **Step 4: Commit**

```
git add src/research/phases/phase4_archive.py
git commit -m "feat(phase4): cascade judge thread_impact to direction.md"
```

---

### Task 7: Update all 3 skill files

**Files:**
- Modify: `.claude/skills/factor-idea/skill.md`
- Modify: `.claude/skills/factor-judge/skill.md`
- Modify: `.claude/skills/factor-mine/skill.md`

- [ ] **Step 1: Rewrite factor-idea skill**

Add Step 0 "Direction Creation/Selection" with full 5-step reasoning chain (A-E), direction.md template with all LogicCard-mapped sections, contract section, anti-hypothesis requirement. Add `context_loaded` and `thread_refs`/`design_rationale` to manifest schema.

- [ ] **Step 2: Update factor-judge skill**

Add `thread_impact` to judge.md frontmatter schema. Add guidance: "For each non-reject candidate, assess impact on referenced threads."

- [ ] **Step 3: Update factor-mine skill**

Step 1: reference the direction creation logic now in `/factor-idea`. Add `context_loaded` field to manifest output. Adjust Step 5 to mention thread cascade.

- [ ] **Step 4: Commit**

```
git add .claude/skills/factor-idea/skill.md .claude/skills/factor-judge/skill.md .claude/skills/factor-mine/skill.md
git commit -m "feat(skills): direction generation spec + thread lifecycle + context chain"
```

---

### Task 8: Deprecate LogicCard + final cleanup

**Files:**
- Modify: `src/research/domain/contracts.py`

- [ ] **Step 1: Add deprecation notice**

```python
import warnings

class LogicCard:
    """DEPRECATED: Fields mapped to vault/directions/{tag}.md.

    See docs/superpowers/plans/2026-04-12-direction-generation-spec.md
    for the mapping. This class will be removed in a future cleanup.
    """
    def __init_subclass__(cls, **kwargs):
        warnings.warn("LogicCard is deprecated", DeprecationWarning, stacklevel=2)
        super().__init_subclass__(**kwargs)
    ...
```

- [ ] **Step 2: Run full test suite**

Run: `pytest -v`
Expected: all PASS

- [ ] **Step 3: Commit**

```
git add src/research/domain/contracts.py
git commit -m "chore: deprecate LogicCard — fields mapped to direction.md"
```
