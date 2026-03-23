"""Factor report generation — compute metrics, score, and render HTML."""

from mining.report.builder import ReportDataBuilder
from mining.report.renderer import ReportRenderer
from mining.report.scorer import CompositeScorer

__all__ = ["ReportDataBuilder", "ReportRenderer", "CompositeScorer"]
