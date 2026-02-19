"""
通用表格组件
Common Table Components

提供可复用的Streamlit表格组件
"""

import streamlit as st
import pandas as pd
from typing import List, Dict, Any, Optional


def render_dataframe(
    df: pd.DataFrame,
    title: str = '',
    use_container_width: bool = True,
    height: int = 400,
    hide_index: bool = True,
    column_config: Dict = None
) -> None:
    """
    渲染DataFrame表格
    
    Args:
        df: 数据
        title: 标题
        use_container_width: 宽度自适应
        height: 高度
        hide_index: 隐藏索引
        column_config: 列配置
    """
    if title:
        st.subheader(title)
    
    st.dataframe(
        df,
        use_container_width=use_container_width,
        height=height,
        hide_index=hide_index,
        column_config=column_config
    )


def render_metric_card(
    label: str,
    value: Any,
    delta: Any = None,
    help: str = ''
) -> None:
    """
    渲染指标卡片
    
    Args:
        label: 标签
        value: 值
        delta: 变化值
        help: 帮助文本
    """
    st.metric(label=label, value=value, delta=delta, help=help)


def render_metrics_row(metrics: Dict[str, Any]) -> None:
    """
    渲染指标行
    
    Args:
        metrics: 指标字典 {label: value}
    """
    cols = st.columns(len(metrics))
    
    for i, (label, value) in enumerate(metrics.items()):
        with cols[i]:
            st.metric(label=label, value=value)


def render_comparison_table(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    labels: List[str] = None,
    title: str = ''
) -> None:
    """
    渲染对比表格
    
    Args:
        df1: 第一个DataFrame
        df2: 第二个DataFrame
        labels: 标签 ['训练集', '测试集']
        title: 标题
    """
    if title:
        st.subheader(title)
    
    if labels is None:
        labels = ['A', 'B']
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f'**{labels[0]}**')
        st.dataframe(df1, use_container_width=True, hide_index=True)
    
    with col2:
        st.write(f'**{labels[1]}**')
        st.dataframe(df2, use_container_width=True, hide_index=True)


def render_trade_log_table(
    trades: pd.DataFrame,
    max_rows: int = 100
) -> None:
    """
    渲染交易记录表格
    
    Args:
        trades: 交易记录DataFrame
        max_rows: 最大显示行数
    """
    st.subheader('📋 交易记录')
    
    if trades.empty:
        st.info('暂无交易记录')
        return
    
    # 显示最新交易
    display_df = trades.tail(max_rows).copy()
    
    # 格式化列
    if 'entry_date' in display_df.columns:
        display_df['entry_date'] = pd.to_datetime(display_df['entry_date']).dt.strftime('%Y-%m-%d')
    if 'exit_date' in display_df.columns:
        display_df['exit_date'] = pd.to_datetime(display_df['exit_date']).dt.strftime('%Y-%m-%d')
    if 'return' in display_df.columns:
        display_df['return'] = display_df['return'].apply(lambda x: f'{x*100:.2f}%')
    
    st.dataframe(
        display_df,
        use_container_width=True,
        height=400,
        hide_index=True
    )


def render_factor_ranking_table(
    factors: pd.DataFrame,
    sort_by: str = 'ic',
    ascending: bool = False
) -> None:
    """
    渲染因子排名表格
    
    Args:
        factors: 因子DataFrame
        sort_by: 排序列
        ascending: 升序
    """
    st.subheader('🏆 因子排名')
    
    if factors.empty:
        st.info('暂无因子数据')
        return
    
    # 排序
    df = factors.sort_values(sort_by, ascending=ascending).reset_index(drop=True)
    df.index = df.index + 1  # 从1开始
    
    # 格式化
    if 'ic' in df.columns:
        df['ic'] = df['ic'].apply(lambda x: f'{x:.4f}')
    if 'icir' in df.columns:
        df['icir'] = df['icir'].apply(lambda x: f'{x:.4f}')
    if 'return' in df.columns:
        df['return'] = df['return'].apply(lambda x: f'{x*100:.2f}%')
    
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=False
    )


def render_performance_table(metrics: Dict[str, Any]) -> None:
    """
    渲染绩效指标表格
    
    Args:
        metrics: 绩效指标字典
    """
    st.subheader('📊 绩效指标')
    
    rows = []
    for key, value in metrics.items():
        # 格式化值
        if isinstance(value, float):
            if 'rate' in key.lower() or 'ratio' in key.lower():
                formatted = f'{value*100:.2f}%'
            else:
                formatted = f'{value:.4f}'
        else:
            formatted = str(value)
        
        # 美化键名
        label = key.replace('_', ' ').title()
        
        rows.append({'指标': label, '值': formatted})
    
    df = pd.DataFrame(rows)
    st.table(df)


__all__ = [
    'render_dataframe',
    'render_metric_card',
    'render_metrics_row',
    'render_comparison_table',
    'render_trade_log_table',
    'render_factor_ranking_table',
    'render_performance_table',
]
