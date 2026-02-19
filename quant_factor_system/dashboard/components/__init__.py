"""
Dashboard 通用组件
Dashboard Components

提供可复用的Dashboard组件:
- charts: 图表组件
- forms: 表单组件
- tables: 表格组件

使用示例:
    from quant_factor_system.dashboard.components import (
        create_line_chart,
        backtest_config_form,
        render_dataframe
    )
    
    # 创建图表
    fig = create_line_chart(df, x='date', y='equity')
    st.plotly_chart(fig)
    
    # 创建表单
    config = backtest_config_form()
    
    # 渲染表格
    render_dataframe(df, title='数据')
"""

from .charts import (
    create_line_chart,
    create_candlestick_chart,
    create_heatmap,
    create_bar_chart,
    create_scatter_chart,
    create_pie_chart,
    create_table,
    create_equity_curve,
    create_drawdown_chart,
)

from .forms import (
    factor_selector_form,
    date_range_form,
    backtest_config_form,
    factor_evaluation_form,
    filter_form,
)

from .tables import (
    render_dataframe,
    render_metric_card,
    render_metrics_row,
    render_comparison_table,
    render_trade_log_table,
    render_factor_ranking_table,
    render_performance_table,
)

__all__ = [
    # 图表
    'create_line_chart',
    'create_candlestick_chart',
    'create_heatmap',
    'create_bar_chart',
    'create_scatter_chart',
    'create_pie_chart',
    'create_table',
    'create_equity_curve',
    'create_drawdown_chart',
    
    # 表单
    'factor_selector_form',
    'date_range_form',
    'backtest_config_form',
    'factor_evaluation_form',
    'filter_form',
    
    # 表格
    'render_dataframe',
    'render_metric_card',
    'render_metrics_row',
    'render_comparison_table',
    'render_trade_log_table',
    'render_factor_ranking_table',
    'render_performance_table',
]
