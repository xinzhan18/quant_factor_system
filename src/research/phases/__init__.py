"""Phase orchestrators for the 5-phase mine loop.

Each module implements one phase:

* ``phase1_start.py`` — START + DESIGN (candidate freeze)
* ``phase2_execute.py`` — EXECUTE (vectorized compute)
* ``phase3_judge.py`` — JUDGE (6 checkpoint + LLM judge.md)
* ``phase4_archive.py`` — ARCHIVE (factor writer + direction update + commit)
* ``phase5_consolidate.py`` — CONSOLIDATION (lessons + directions + INDEX rewrite)

Skeleton only at P0. Actual implementations land in P1-P6 per
``docs/refactor_checklist.md``.
"""
