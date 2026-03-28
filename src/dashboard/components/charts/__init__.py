"""
通用图表组件
Common Chart Components

提供可复用的Plotly图表组件
"""

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict


def create_line_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str = '',
    xlabel: str = '',
    ylabel: str = '',
    height: int = 400,
    color: str = None,
    hover_data: Dict = None
) -> go.Figure:
    """创建折线图"""
    fig = px.line(df, x=x, y=y, title=title, color=color, hover_data=hover_data)
    fig.update_layout(
        template='plotly_white',
        height=height,
        xaxis_title=xlabel,
        yaxis_title=ylabel
    )
    return fig


def create_candlestick_chart(
    df: pd.DataFrame,
    date_col: str = 'time',
    open_col: str = 'open',
    high_col: str = 'high',
    low_col: str = 'low',
    close_col: str = 'close',
    volume_col: str = 'volume',
    title: str = 'K线图',
    height: int = 600
) -> go.Figure:
    """创建K线图"""
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        subplot_titles=('K线', '成交量'),
        row_heights=[0.7, 0.3]
    )
    
    # K线
    fig.add_trace(
        go.Candlestick(
            x=df[date_col],
            open=df[open_col],
            high=df[high_col],
            low=df[low_col],
            close=df[close_col],
            name='K线'
        ),
        row=1, col=1
    )
    
    # 成交量
    colors = ['red' if df[close_col].iloc[i] >= df[open_col].iloc[i] else 'green' 
              for i in range(len(df))]
    fig.add_trace(
        go.Bar(
            x=df[date_col],
            y=df[volume_col],
            marker_color=colors,
            name='成交量'
        ),
        row=2, col=1
    )
    
    fig.update_layout(
        title=title,
        template='plotly_white',
        height=height,
        xaxis_rangeslider_visible=False
    )
    
    return fig


def create_heatmap(
    df: pd.DataFrame,
    x: str,
    y: str,
    z: str,
    title: str = '',
    colorscale: str = 'RdBu_r',
    height: int = 400
) -> go.Figure:
    """创建热力图"""
    fig = px.density_heatmap(
        df, x=x, y=y, z=z,
        title=title,
        colorscale=colorscale
    )
    fig.update_layout(template='plotly_white', height=height)
    return fig


def create_bar_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str = '',
    orientation: str = 'v',
    height: int = 400,
    color: str = None,
    text_auto: bool = True
) -> go.Figure:
    """创建柱状图"""
    if orientation == 'h':
        fig = px.bar(df, y=y, x=x, title=title, color=color, orientation='h')
    else:
        fig = px.bar(df, x=x, y=y, title=title, color=color)
    
    if text_auto:
        fig.update_traces(texttemplate='%{y:.2f}', textposition='outside')
    
    fig.update_layout(template='plotly_white', height=height)
    return fig


def create_scatter_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    size: str = None,
    color: str = None,
    hover_name: str = None,
    title: str = '',
    height: int = 400
) -> go.Figure:
    """创建散点图"""
    fig = px.scatter(
        df, x=x, y=y,
        size=size, color=color,
        hover_name=hover_name,
        title=title
    )
    fig.update_layout(template='plotly_white', height=height)
    return fig


def create_pie_chart(
    df: pd.DataFrame,
    names: str,
    values: str,
    title: str = '',
    height: int = 400
) -> go.Figure:
    """创建饼图"""
    fig = px.pie(df, names=names, values=values, title=title)
    fig.update_layout(template='plotly_white', height=height)
    return fig


def create_table(
    df: pd.DataFrame,
    title: str = '',
    height: int = 400
) -> go.Figure:
    """创建表格"""
    fig = go.Figure(data=[go.Table(
        header=dict(
            values=list(df.columns),
            fill_color='paleturquoise',
            align='left'
        ),
        cells=dict(
            values=[df[col] for col in df.columns],
            fill_color='lavender',
            align='left'
        )
    )])
    fig.update_layout(title=title, height=height)
    return fig


def create_equity_curve(
    equity_df: pd.DataFrame,
    benchmark_df: pd.DataFrame = None,
    title: str = '策略收益曲线',
    height: int = 400
) -> go.Figure:
    """创建收益曲线图"""
    fig = go.Figure()
    
    # 策略收益
    fig.add_trace(go.Scatter(
        x=equity_df.index,
        y=equity_df['equity'],
        mode='lines',
        name='策略',
        line=dict(color='blue', width=2)
    ))
    
    # 基准收益
    if benchmark_df is not None:
        fig.add_trace(go.Scatter(
            x=benchmark_df.index,
            y=benchmark_df['equity'],
            mode='lines',
            name='基准',
            line=dict(color='gray', width=1, dash='dash')
        ))
    
    fig.update_layout(
        title=title,
        template='plotly_white',
        height=height,
        xaxis_title='日期',
        yaxis_title='净值'
    )
    
    return fig


def create_drawdown_chart(
    drawdown_df: pd.DataFrame,
    title: str = '回撤曲线',
    height: int = 300
) -> go.Figure:
    """创建回撤曲线图"""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=drawdown_df.index,
        y=drawdown_df['drawdown'] * 100,
        mode='lines',
        fill='tozeroy',
        fillcolor='rgba(255, 0, 0, 0.1)',
        line=dict(color='red'),
        name='回撤'
    ))
    
    fig.update_layout(
        title=title,
        template='plotly_white',
        height=height,
        xaxis_title='日期',
        yaxis_title='回撤 (%)'
    )
    
    return fig


__all__ = [
    'create_line_chart',
    'create_candlestick_chart',
    'create_heatmap',
    'create_bar_chart',
    'create_scatter_chart',
    'create_pie_chart',
    'create_table',
    'create_equity_curve',
    'create_drawdown_chart',
]
