"""
选股页面
基于因子值选出表现好的股票
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from config import (
    st, pd, np, init_session_state, get_database,
    get_csv_storage
)


def show_stock_selector(db):
    """股票选择器"""
    st.subheader("📊 选择因子")
    
    factors = db.list_factors()
    
    if factors.empty:
        st.warning("暂无因子，请先添加因子")
        return None, None
    
    factor_names = factors['name'].tolist()
    selected_factor = st.selectbox("选择因子", factor_names)
    
    # 获取该因子的最新选股日期
    selections = db.get_stock_selections(selected_factor, limit=1)
    
    default_date = None
    if not selections.empty and 'selection_date' in selections.columns:
        default_date = selections['selection_date'].iloc[0]
    
    selection_date = st.date_input(
        "选股日期",
        value=datetime.now().date(),
        key="stock_date"
    )
    
    return selected_factor, str(selection_date)


def show_stock_params():
    """显示选股参数"""
    st.subheader("⚙️ 选股参数")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        num_stocks = st.slider("选股数量", 10, 100, 50, step=10)
    
    with col2:
        rank_type = st.selectbox("排序方式", ["升序", "降序"])
    
    with col3:
        direction = st.selectbox("因子方向", ["正向", "负向"])
    
    return num_stocks, rank_type, direction


def get_top_stocks(factor_name: str, num_stocks: int,
                   rank_type: str, direction: str, db, csv):
    """获取 top 股票"""
    # 加载因子数据
    factor_data = csv.load_factor_data(factor_name)
    
    if factor_data is None:
        st.warning(f"找不到因子 {factor_name} 的数据")
        return None
    
    # 排序
    ascending = (rank_type == "升序")
    
    if direction == "正向":
        # 值越大越好
        sorted_data = factor_data.sort_values(by='value', ascending=ascending)
    else:
        # 值越小越好
        sorted_data = factor_data.sort_values(by='value', ascending=not ascending)
    
    # 取 top N
    top_stocks = sorted_data.head(num_stocks)
    
    # 构建结果
    stocks = []
    for i, (idx, row) in enumerate(top_stocks.iterrows()):
        stock = {
            'stock_code': str(idx[1]) if isinstance(idx, tuple) else str(idx),
            'factor_value': row.get('value', row.get('pe', row.get('close', 0))),
            'rank': i + 1,
            'weight': 1.0 / num_stocks
        }
        stocks.append(stock)
    
    return stocks


def show_stock_selection(factor_name: str, selection_date: str,
                         stocks: list, db):
    """显示选股结果"""
    st.subheader(f"📈 选股结果 ({factor_name})")
    
    if not stocks:
        st.warning("没有选股结果")
        return
    
    # 保存选股结果
    if st.button("💾 保存选股结果", use_container_width=True):
        db.save_stock_selection(factor_name, selection_date, stocks)
        st.success("选股结果已保存！")
    
    # 转换为 DataFrame
    df = pd.DataFrame(stocks)
    
    # 显示
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )
    
    # 统计
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("股票数量", len(stocks))
    
    with col2:
        avg_value = df['factor_value'].mean()
        st.metric("因子均值", f"{avg_value:.4f}")
    
    with col3:
        total_weight = df['weight'].sum()
        st.metric("权重总和", f"{total_weight:.2f}")


def show_stock_chart(stocks: list):
    """显示选股图表"""
    if not stocks:
        return
    
    df = pd.DataFrame(stocks)
    
    # 因子值分布
    st.subheader("📊 因子值分布")
    
    chart_data = df.set_index('rank')['factor_value']
    st.bar_chart(chart_data)


def show_history_selections(factor_name: str, db):
    """显示历史选股记录"""
    st.subheader("📋 历史选股记录")
    
    selections = db.get_stock_selections(factor_name, limit=10)
    
    if selections.empty:
        st.info("暂无历史选股记录")
        return
    
    # 按日期分组显示
    dates = selections['selection_date'].unique()
    
    selected_date = st.selectbox("选择日期", dates)
    
    date_selections = selections[selections['selection_date'] == selected_date]
    
    st.dataframe(
        date_selections[['stock_code', 'factor_value', 'rank', 'weight']],
        use_container_width=True,
        hide_index=True
    )


def main():
    """页面主函数"""
    init_session_state()
    
    st.title("🎯 选股")
    
    # 获取数据库和存储
    db = get_database()
    csv = get_csv_storage()
    
    # 选择因子和日期
    factor_name, selection_date = show_stock_selector(db)
    
    if factor_name:
        # 选股参数
        num_stocks, rank_type, direction = show_stock_params()
        
        # 执行选股
        if st.button("🔍 执行选股", use_container_width=True):
            stocks = get_top_stocks(factor_name, num_stocks, 
                                    rank_type, direction, db, csv)
            
            if stocks:
                st.session_state['stocks'] = stocks
                st.session_state['last_selection'] = {
                    'factor': factor_name,
                    'date': selection_date
                }
        
        # 显示结果
        if 'stocks' in st.session_state:
            last = st.session_state.get('last_selection', {})
            
            if last.get('factor') == factor_name:
                show_stock_selection(
                    factor_name, 
                    last.get('date', selection_date),
                    st.session_state['stocks'],
                    db
                )
                
                show_stock_chart(st.session_state['stocks'])
        
        st.divider()
        
        # 历史记录
        show_history_selections(factor_name, db)


if __name__ == "__main__":
    main()
