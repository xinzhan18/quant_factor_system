"""Factor report generation — analytics, scoring, and HTML rendering."""

from report.analytics.ic import ICAnalyzer
from report.analytics.groups import GroupReturnsAnalyzer
from report.analytics.decay import DecayAnalyzer
from report.analytics.distribution import DistributionAnalyzer
from report.scorer import CompositeScorer
from report.builder import ReportDataBuilder
from report.renderer import ReportRenderer

__all__ = [
    "ICAnalyzer",
    "GroupReturnsAnalyzer",
    "DecayAnalyzer",
    "DistributionAnalyzer",
    "CompositeScorer",
    "ReportDataBuilder",
    "ReportRenderer",
]
