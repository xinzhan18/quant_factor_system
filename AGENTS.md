# Repository Guidelines

## Project Structure & Module Organization

Code lives under `src/` with four active modules:

- `src/core/`: pure math and shared metrics
- `src/data/`: TimescaleDB, Qlib sync, loaders, and storage helpers
- `src/report/`: report analytics, chart builders, and templates
- `src/research/`: the 5-phase mining pipeline (`cli/`, `compute/`, `phases/`, `archive/`, `memory/`, `storage/`)

Tests mirror the source tree in `tests/` (`tests/research/phases/test_phase4_archive.py`, etc.). Operational state and LLM-visible artifacts live in `storage/vault/`. Project docs and design notes live in `docs/`. Automation and maintenance scripts belong in `scripts/`.

Keep the architecture split from `CLAUDE.md`: YAML is Python-consumed state, Markdown is LLM-consumed narrative. In `research/`, the 5-phase loop is `START → EXECUTE → JUDGE → ARCHIVE → CONSOLIDATION`.

## Build, Test, and Development Commands

Install in editable mode:

```bash
pip install -e .
```

Run the full test suite:

```bash
pytest
```

Run a focused test file:

```bash
pytest tests/research/compute/test_vectorized_ic.py -v
```

Run CLI workflows with package imports enabled:

```bash
PYTHONPATH=src python3 -m research mine --once --direction bootstrap
PYTHONPATH=src python3 -m research execute batch_001
PYTHONPATH=src python3 -m research judge batch_001 pre-hint
PYTHONPATH=src python3 -m research audit mt-budget
PYTHONPATH=src python3 -m research archive batch_001
```

Common data commands:

```bash
./scripts/db.sh start|stop|shell
PYTHONPATH=src python3 scripts/sync_index_constituents.py --all
PYTHONPATH=src python3 scripts/resync_qlib.py
```

## Coding Style & Naming Conventions

Use Python with 4-space indentation, type hints, and small focused functions. Prefer `snake_case` for modules, functions, YAML keys, and test files; use `PascalCase` for classes and dataclasses. Follow the existing `src/research/domain/` style: explicit schemas, minimal adapter layers, and no speculative backward-compatibility shims.

Honor the repo constitution from `CLAUDE.md`: keep compute fully vectorized, do not re-run Phase 2 analytics in Phase 4 reports, and prefer Qlib DSL over Python unless DSL cannot express the factor. Use `load_yaml_unsafe()` only for result-like files that may contain DataFrames; use safe YAML loaders for config, state, and manifests.

## Testing Guidelines

Use `pytest`; `pytest.ini` already sets `pythonpath=src`. Add tests alongside the touched module and name files `test_<unit>.py`. For pipeline changes, cover both happy path and audit/validation failures. Prefer targeted regression tests for bugs in state transitions, archive backfill, and report packing.

## Commit & Pull Request Guidelines

Recent history uses scoped subjects such as `[infra] ...`, `[mine] ...`, and `[report] ...`. Follow that pattern and keep the first line specific. PRs should include: purpose, affected paths, commands/tests run, and any storage or vault side effects. Include screenshots only for UI or rendered report changes; otherwise prefer diffs and sample command output.

## Configuration & Safety Notes

Qlib data and TimescaleDB are local dependencies; see `CLAUDE.md` for environment details. Use `pyqlib`, not `qlib`. Treat `vault/factors/F{id}.yaml` as the metadata truth source; DB `factor_meta` is derived cache only. Treat `storage/vault/` markdown as user-visible state: do not rewrite or delete it casually, and never use destructive Git commands to “clean up” repository state.
