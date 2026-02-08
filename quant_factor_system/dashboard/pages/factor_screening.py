"""
因子筛选页面
根据 IC 和胜率筛选有效因子
"""

import streamlit as st
import pandas as pd
from config import (
    st, pd, np, init_session_state, get_database,
    DEFAULT_IC_THRESHOLD, DEFAULT_WIN_RATE_THRESHOLD
)


def show_filters():
    """显示筛选条件"""
    st.subheader("🔍 筛选条件")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        ic_threshold = st.slider(
            "IC 阈值",
            min_value=0.0,
            max_value=0.1,
            value=DEFAULT_IC_THRESHOLD,
            step=0.005,
            help="只显示 IC 大于该值的因子"
        )
    
    with col2:
        win_rate_threshold = st.slider(
            "胜率阈值",
            min_value=0.0,
            max_value=1.0,
            value=DEFAULT_WIN_RATE_THRESHOLD,
            step=0.01,
            help="只显示胜率大于该值的因子"
        )
    
    with col3:
        sort_by = st.selectbox(
            "排序方式",
            ["ic", "win_rate", "long_short_return"],
            index=0
        )
    
    return ic_threshold, win_rate_threshold, sort_by


def filter_factors(db, ic_threshold: float, 
                   win_rate_threshold: float, sort_by: str):
    """筛选因子"""
    latest = db.get_latest_evaluations(limit=100)
    
    if latest.empty:
        return pd.DataFrame()
    
    # 筛选
    filtered = latest[
        (latest['ic'] >= ic_threshold) & 
        (latest['win_rate'] >= win_rate_threshold)
    ]
    
    # 排序
    filtered = filtered.sort_values(sort_by, ascending=False)
    
    return filtered


def show_factor_table(filtered: pd.DataFrame):
    """显示因子表格"""
    if filtered.empty:
        st.warning("没有符合条件的因子")
        return
    
    st.subheader(f"📋 符合条件的因子 ({len(filtered)} 个)")
    
    # 格式化
    display = filtered.copy()
    
    if 'ic' in display.columns:
        display['ic'] = display['ic'].apply(lambda x: f"{x:.4f}")
    if 'ic_ir' in display.columns:
        display['ic_ir'] = display['ic_ir'].apply(lambda x: f"{x:.4f}")
    if 'win_rate' in display.columns:
        display['win_rate'] = display['win_rate'].apply(lambda x: f"{x:.2%}")
    if 'long_short_return' in display.columns:
        display['long_short_return'] = display['long_short_return'].apply(lambda x: f"{x:.4f}")
    
    # 选择列
    cols = ['factor_name', 'category', 'ic', 'ic_ir', 'win_rate', 'long_short_return', 'eval_date']
    available = [c for c in cols if c in display.columns]
    
    st.dataframe(
        display[available],
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row"
    )
    
    return filtered


def show_factor_comparison(filtered: pd.DataFrame):
    """因子对比"""
    if filtered.empty or len(filtered) < 2:
        return
    
    st.subheader("📊 因子对比")
    
    # 选择要对比的因子
    selected = st.multiselect(
        "选择因子进行对比",
        filtered['factor_name'].tolist(),
        default=filtered['factor_name'].head(5).tolist()
    )
    
    if len(selected) < 2:
        st.info("请选择至少 2 个因子进行对比")
        return
    
    # 准备对比数据
    compare = filtered[filtered['factor_name'].isin(selected)].copy()
    
    # IC 对比图
    if len(compare) > 0:
        chart_data = compare[['factor_name', 'ic', 'win_rate']].set_index('factor_name')
        
        st.bar_chart(chart_data['ic'])
        
        with st.expander("查看详细数据"):
            st.dataframe(compare[['factor_name', 'ic', 'ic_ir', 'win_rate', 'long_short_return']])


def show_statistics(filtered: pd.DataFrame):
    """显示统计信息"""
    if filtered.empty:
        return
    
    st.subheader("📈 统计摘要")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("因子数量", len(filtered))
    
    with col2:
        avg_ic = filtered['ic'].mean()
        st.metric("平均 IC", f"{avg_ic:.4f}")
    
    with col3:
        avg_win_rate = filtered['win_rate'].mean()
        st.metric("平均胜率", f"{avg_win_rate:.2%}")
    
    with col4:
        avg_return = filtered['long_short_return'].mean()
        st.metric("平均多空收益", f"{avg_return:.4f}")


def main():
    """页面主函数"""
    init_session_state()
    
    st.title("🔍 因子筛选")
    
    # 获取数据库
    db = get_database()
    
    # 筛选条件
    ic_threshold, win_rate_threshold, sort_by = show_filters()
    
    st.divider()
    
    # 筛选因子
    filtered = filter_factors(db, ic_threshold, win_rate_threshold, sort_by)
    
    # 统计信息
    show_statistics(filtered)
    
    # 显示因子表格
    show_factor_table(filtered)
    
    # 因子对比
    show_factor_comparison(filtered)


if __name__ == "__main__":
    main()
