"""Factor report generation — analytics v2 + report packer.

Legacy exports (ICAnalyzer, ProfitAnalyzer, CompositeScorer, etc.) are
removed. New consumers use ``report.analytics_v2`` extractors which
consume ``result.yaml`` directly per R4 (no recomputation).
"""
