"""Smoke test for visualization module imports."""


def test_visualization_imports():
    from visualization.ic_analyzer import ICAnalyzer
    from visualization.group_returns import GroupReturnsAnalyzer
    from visualization.report import FactorReportGenerator
    assert ICAnalyzer is not None
    assert GroupReturnsAnalyzer is not None
    assert FactorReportGenerator is not None
