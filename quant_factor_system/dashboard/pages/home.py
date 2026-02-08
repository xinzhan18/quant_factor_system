"""
Dashboard 首页
总览因子系统状态
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from config import (
    st, pd, init_session_state, get_database,
    BASE_DIR, PAGES
)


def show_header():
    """显示标题"""
    st.markdown('<p class="main-header">📊 量化因子 Dashboard</p>', unsafe_allow_html=True)


def show_metrics(stats: dict):
    """显示统计卡片"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("因子总数", stats.get('total_factors', 0))
    with col2:
        st.metric("已评估因子", stats.get('evaluated_factors', 0))
    with col3:
        best_factor = stats.get('best_factor', 'N/A')
        best_ic = stats.get('best_ic', 0)
        st.metric("最佳因子", f"{best_factor}" if best_factor else "N/A",
                 f"IC: {best_ic:.4f}" if best_ic else None)
    with col4:
        st.metric("评估记录", stats.get('total_evaluations', 0))


def show_factor_list(db):
    """显示因子列表"""
    st.subheader("📋 因子列表")
    
    factors = db.list_factors()
    
    if factors.empty:
        st.info("暂无因子数据")
        return
    
    # 格式化显示
    display_cols = ['name', 'category', 'description', 'created_at']
    available_cols = [c for c in display_cols if c in factors.columns]
    
    st.dataframe(
        factors[available_cols],
        use_container_width=True,
        hide_index=True
    )


def show_latest_evaluations(db):
    """显示最新评估"""
    st.subheader("📈 最新评估结果")
    
    latest = db.get_latest_evaluations(limit=10)
    
    if latest.empty:
        st.info("暂无评估数据")
        return
    
    # 显示关键指标
    cols = ['factor_name', 'ic', 'ic_ir', 'win_rate', 'long_short_return', 'eval_date']
    available_cols = [c for c in cols if c in latest.columns]
    
    st.dataframe(
        latest[available_cols],
        use_container_width=True,
        hide_index=True
    )


def show_ic_ranking(db):
    """显示 IC 排名"""
    st.subheader("🏆 因子 IC 排名")
    
    latest = db.get_latest_evaluations(limit=20)
    
    if latest.empty:
        st.info("暂无评估数据")
        return
    
    # 按 IC 排序
    sorted_df = latest.sort_values('ic', ascending=False)
    
    # 格式化
    if 'ic' in sorted_df.columns:
        sorted_df['ic'] = sorted_df['ic'].apply(lambda x: f"{x:.4f}")
    if 'win_rate' in sorted_df.columns:
        sorted_df['win_rate'] = sorted_df['win_rate'].apply(lambda x: f"{x:.2%}")
    
    st.dataframe(
        sorted_df[['factor_name', 'ic', 'win_rate', 'eval_date']],
        use_container_width=True,
        hide_index=True
    )


def show_quick_actions():
    """显示快捷操作"""
    st.subheader("⚡ 快捷操作")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 刷新数据", use_container_width=True):
            st.rerun()
    
    with col2:
        if st.button("➕ 添加因子", use_container_width=True):
            st.switch_page("pages.factor_evaluation")
    
    with col3:
        if st.button("📊 运行评估", use_container_width=True):
            st.switch_page("pages.factor_evaluation")


def main():
    """首页主函数"""
    init_session_state()
    
    show_header()
    
    # 获取数据库
    db = get_database()
    
    # 统计信息
    stats = db.get_factor_stats()
    
    # 显示统计卡片
    show_metrics(stats)
    
    st.divider()
    
    # 最新评估
    show_latest_evaluations(db)
    
    col1, col2 = st.columns(2)
    
    with col1:
        show_ic_ranking(db)
    
    with col2:
        show_quick_actions()
    
    st.divider()
    
    # 因子列表
    show_factor_list(db)


if __name__ == "__main__":
    main()
