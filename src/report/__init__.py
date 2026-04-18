"""Factor report generation — composite scoring + chart rendering.

The report pipeline consists of ``report.composite`` (scoring) and
``report.render`` (chart + markdown output), which consume ``result.yaml``
directly per R4 (no recomputation).
"""
