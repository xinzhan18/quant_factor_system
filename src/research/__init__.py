"""Research system for structured factor mining.

5-phase architecture:
  1. phases/phase1_start — START + DESIGN (candidate freeze)
  2. phases/phase2_execute — EXECUTE (vectorized compute)
  3. phases/phase3_judge — JUDGE (6 checkpoints + §7.MT)
  4. phases/phase4_archive — ARCHIVE (factor allocation + commit)
  5. phases/phase5_consolidate — CONSOLIDATION (memory rewrite)

Supporting layers:
  - compute/   vectorized metrics + cache + preprocess + python_runner
  - checkpoints/  hard gates + mt_budget + generator + audit
  - archive/   factor_writer + report_packer + git commit
  - memory/    direction_updater + index_refresher
  - storage/   yaml_io + paths + state
  - domain/    pure data contracts
  - cli/       mine loop + audit commands
"""

__version__ = "2.0.0"
