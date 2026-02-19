"""
通用表单组件
Common Form Components

提供可复用的Streamlit表单组件
"""

import streamlit as st
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, date


def factor_selector_form(
    factors: List[str],
    key_prefix: str = 'factor'
) -> Dict[str, Any]:
    """
    因子选择表单
    
    Args:
        factors: 可选因子列表
        key_prefix: 表单key前缀
        
    Returns:
        选择的因子列表
    """
    col1, col2 = st.columns([3, 1])
    
    with col1:
        selected = st.multiselect(
            '选择因子',
            options=factors,
            key=f'{key_prefix}_multiselect'
        )
    
    with col2:
        select_all = st.checkbox('全选', key=f'{key_prefix}_select_all')
        if select_all:
            selected = factors
    
    return selected


def date_range_form(
    key_prefix: str = 'date',
    default_start: str = '2024-01-01',
    default_end: str = '2024-12-31'
) -> tuple:
    """
    日期范围表单
    
    Args:
        key_prefix: 表单key前缀
        default_start: 默认开始日期
        default_end: 默认结束日期
        
    Returns:
        (start_date, end_date)
    """
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input(
            '开始日期',
            value=datetime.strptime(default_start, '%Y-%m-%d').date(),
            key=f'{key_prefix}_start'
        )
    
    with col2:
        end_date = st.date_input(
            '结束日期',
            value=datetime.strptime(default_end, '%Y-%m-%d').date(),
            key=f'{key_prefix}_end'
        )
    
    return start_date, end_date


def backtest_config_form() -> Dict[str, Any]:
    """
    回测配置表单
    
    Returns:
        配置字典
    """
    config = {}
    
    # 基本配置
    st.subheader('📊 基本配置')
    
    col1, col2 = st.columns(2)
    
    with col1:
        config['initial_capital'] = st.number_input(
            '初始资金',
            min_value=10000,
            value=1000000,
            step=10000
        )
    
    with col2:
        config['commission'] = st.number_input(
            '手续费率',
            min_value=0.0,
            max_value=0.01,
            value=0.0003,
            step=0.0001,
            format='%.4f'
        )
    
    # 选股配置
    st.subheader('🎯 选股配置')
    
    col1, col2 = st.columns(2)
    
    with col1:
        config['top_n'] = st.slider('选股数量', 5, 100, 20)
    
    with col2:
        config['rebalance_freq'] = st.selectbox(
            '调仓频率',
            options=['daily', 'weekly', 'monthly'],
            index=0
        )
    
    # 仓位配置
    st.subheader('💰 仓位配置')
    
    config['position_method'] = st.selectbox(
        '仓位分配方式',
        options=['equal', 'factor_weighted', 'kelly'],
        format_func=lambda x: {
            'equal': '等权',
            'factor_weighted': '因子加权',
            'kelly': 'Kelly公式'
        }[x]
    )
    
    # 止损配置
    st.subheader('🛡️ 止损配置')
    
    col1, col2 = st.columns(2)
    
    with col1:
        config['use_stoploss'] = st.checkbox('启用止损', value=True)
    
    with col2:
        if config.get('use_stoploss'):
            config['stoploss_type'] = st.selectbox(
                '止损类型',
                options=['fixed', 'atr', 'trailing'],
                format_func=lambda x: {
                    'fixed': '固定止损',
                    'atr': 'ATR止损',
                    'trailing': '移动止损'
                }[x]
            )
    
    if config.get('use_stoploss') and config.get('stoploss_type') == 'fixed':
        config['stoploss_pct'] = st.slider(
            '止损比例',
            min_value=1,
            max_value=20,
            value=5
        ) / 100
    
    return config


def factor_evaluation_form() -> Dict[str, Any]:
    """
    因子评估配置表单
    
    Returns:
        配置字典
    """
    config = {}
    
    # 评估参数
    st.subheader('📈 评估参数')
    
    col1, col2 = st.columns(2)
    
    with col1:
        config['n_groups'] = st.slider('分组数量', 3, 10, 5)
    
    with col2:
        config['rolling_window'] = st.selectbox(
            '滚动窗口',
            options=[20, 60, 120],
            index=1
        )
    
    # 训练/测试集划分
    st.subheader('📊 数据划分')
    
    col1, col2 = st.columns(2)
    
    with col1:
        config['split_method'] = st.radio(
            '划分方式',
            options=['ratio', 'date'],
            format_func=lambda x: '比例' if x == 'ratio' else '日期'
        )
    
    if config['split_method'] == 'ratio':
        with col2:
            config['train_ratio'] = st.slider(
                '训练集比例',
                min_value=0.5,
                max_value=0.9,
                value=0.7
            )
    else:
        with col2:
            config['split_date'] = st.date_input(
                '分界日期',
                value=datetime(2022, 1, 1).date()
            )
    
    return config


def filter_form() -> Dict[str, Any]:
    """
    过滤条件表单
    
    Returns:
        过滤条件字典
    """
    filters = {}
    
    st.subheader('🔍 过滤条件')
    
    # 行业过滤
    filters['industry_filter'] = st.checkbox('启用行业过滤', value=False)
    if filters['industry_filter']:
        filters['include_industries'] = st.multiselect(
            '保留行业',
            options=['银行', '房地产', '医药', '消费', '科技', '能源', '材料', '工业'],
            default=[]
        )
    
    # 市值过滤
    filters['market_cap_filter'] = st.checkbox('启用市值过滤', value=False)
    if filters['market_cap_filter']:
        col1, col2 = st.columns(2)
        with col1:
            filters['min_market_cap'] = st.number_input('最小市值(亿)', value=50)
        with col2:
            filters['max_market_cap'] = st.number_input('最大市值(亿)', value=5000)
    
    # 流动性过滤
    filters['liquidity_filter'] = st.checkbox('启用流动性过滤', value=True)
    if filters['liquidity_filter']:
        filters['min_volume'] = st.number_input('最小成交量', value=10000000)
    
    # 涨跌停过滤
    filters['limit_filter'] = st.checkbox('排除涨跌停', value=True)
    
    return filters


__all__ = [
    'factor_selector_form',
    'date_range_form',
    'backtest_config_form',
    'factor_evaluation_form',
    'filter_form',
]
