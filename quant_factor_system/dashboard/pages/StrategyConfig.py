"""
策略配置页面
Strategy Configuration Page

功能:
- 因子选择
- 参数配置
- 回测设置
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta


def render_strategy_config():
    """渲染策略配置页面"""
    st.title("📊 策略配置")
    
    # 1. 因子选择
    st.subheader("1. 选择因子")
    
    available_factors = [
        'momentum_5d', 'momentum_10d', 'momentum_20d',
        'return_1d', 'return_5d', 'return_20d',
        'rsi_14', 'ma_20', 'volatility_20d'
    ]
    
    selected_factors = st.multiselect(
        "选择因子",
        available_factors,
        default=['momentum_20d']
    )
    
    # 2. 选股参数
    st.subheader("2. 选股参数")
    
    col1, col2 = st.columns(2)
    
    with col1:
        top_n = st.number_input(
            "选股数量",
            min_value=5,
            max_value=100,
            value=20
        )
        
        sort_order = st.selectbox(
            "排序方向",
            ['desc', 'asc'],
            index=0,
            format_func=lambda x: "降序(因子值大的优先)" if x == 'desc' else "升序"
        )
    
    with col2:
        exclude_st = st.checkbox("排除ST股票", value=True)
        exclude_new = st.checkbox("排除次新股", value=True)
        new_stock_days = st.number_input(
            "次新股排除天数",
            min_value=30,
            max_value=365,
            value=60
        )
    
    # 3. 仓位管理
    st.subheader("3. 仓位管理")
    
    position_method = st.selectbox(
        "仓位管理方法",
        ['等权分配', '因子加权', '凯利公式']
    )
    
    if position_method == '等权分配':
        max_weight = st.slider(
            "单只最大权重",
            min_value=0.05,
            max_value=0.30,
            value=0.15
        )
        min_weight = st.slider(
            "单只最小权重",
            min_value=0.01,
            max_value=0.10,
            value=0.02
        )
    
    elif position_method == '凯利公式':
        kelly_fraction = st.selectbox(
            "凯利分数",
            ['全凯利', '半凯利', '三分之一']
        )
    
    # 4. 止盈止损
    st.subheader("4. 止盈止损")
    
    use_stoploss = st.checkbox("启用止盈止损", value=True)
    
    if use_stoploss:
        col1, col2 = st.columns(2)
        
        with col1:
            stop_profit = st.number_input(
                "止盈比例 (%)",
                min_value=0.0,
                max_value=50.0,
                value=10.0
            ) / 100
        
        with col2:
            stop_loss = st.number_input(
                "止损比例 (%)",
                min_value=0.0,
                max_value=50.0,
                value=5.0
            ) / 100
    
    # 5. 回测设置
    st.subheader("5. 回测设置")
    
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input(
            "开始日期",
            value=datetime.now() - timedelta(days=365)
        )
    
    with col2:
        end_date = st.date_input(
            "结束日期",
            value=datetime.now()
        )
    
    initial_capital = st.number_input(
        "初始资金",
        min_value=100000,
        value=1000000,
        step=100000
    )
    
    # 6. 生成配置
    st.subheader("6. 运行回测")
    
    if st.button("🚀 运行回测"):
        config = {
            'factors': selected_factors,
            'top_n': top_n,
            'sort_order': sort_order,
            'exclude_st': exclude_st,
            'exclude_new': exclude_new,
            'new_stock_days': new_stock_days,
            'position_method': position_method,
            'use_stoploss': use_stoploss,
            'stop_profit': stop_profit if use_stoploss else None,
            'stop_loss': stop_loss if use_stoploss else None,
            'start_date': str(start_date),
            'end_date': str(end_date),
            'initial_capital': initial_capital
        }
        
        return config
    
    return None


def main():
    """主函数"""
    config = render_strategy_config()
    
    if config:
        st.success("✅ 策略配置完成!")
        st.json(config)


if __name__ == "__main__":
    main()
