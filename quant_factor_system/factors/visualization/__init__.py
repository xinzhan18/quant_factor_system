"""
因子可视化模块
Factor Visualization Module

提供因子评估所需的各种图表和分析工具

主要组件:
- ICAnalyzer: IC分析器
- GroupReturnsAnalyzer: 分组收益分析器
- FactorReportGenerator: 报告生成器

使用方式:
    from quant_factor_system.factors.visualization import (
        ICAnalyzer,
        GroupReturnsAnalyzer,
        FactorReportGenerator
    )

    # IC分析
    ic_analyzer = ICAnalyzer('return_1d')
    result = ic_analyzer.compute_ic(factor_df, price_df)
    fig = ic_analyzer.plot_ic_timeseries(result['rolling_ic'])

    # 分组收益分析
    group_analyzer = GroupReturnsAnalyzer('return_1d')
    result = group_analyzer.compute_group_returns(factor_df, price_df)
    fig = group_analyzer.plot_group_returns_bar(result['mean_returns'])

    # 完整报告
    report = FactorReportGenerator('return_1d')
    report.analyze(factor_df, price_df, split_date)
    report.generate_charts()
    report.print_summary()
"""

from .ic_analyzer import (
    ICAnalyzer,
    create_ic_analyzer,
)

from .group_returns import (
    GroupReturnsAnalyzer,
    create_group_analyzer,
)

from .report import (
    FactorReportGenerator,
    create_report_generator,
)

__all__ = [
    # IC分析
    'ICAnalyzer',
    'create_ic_analyzer',
    
    # 分组收益
    'GroupReturnsAnalyzer',
    'create_group_analyzer',
    
    # 报告生成
    'FactorReportGenerator',
    'create_report_generator',
]
