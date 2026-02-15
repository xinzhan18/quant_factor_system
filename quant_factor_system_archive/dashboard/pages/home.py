"""
Dashboard 首页
总览因子系统状态

功能:
- 系统统计概览
- 因子排名
- 评估历史
- 模块功能入口
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from config import (
    st, pd, init_session_state, get_database,
    BASE_DIR, PAGES
)


def show_header():
    """显示标题"""
    st.markdown("""
    <div style="text-align: center; padding: 20px; background: linear-gradient(90deg, #1f77b4 0%, #ff7f0e 100%); border-radius: 10px; margin-bottom: 20px;">
        <h1 style="color: white; margin: 0;">📊 量化因子 Dashboard</h1>
        <p style="color: white; opacity: 0.8; margin: 10px 0 0 0;">多因子评估与分析系统</p>
    </div>
    """, unsafe_allow_html=True)


def show_metrics(db):
    """显示统计卡片"""
    stats = db.get_factor_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("因子总数", stats.get('total_factors', 0))
    
    with col2:
        st.metric("已评估", stats.get('evaluated_factors', 0))
    
    with col3:
        latest = db.get_latest_evaluations(limit=10)
        if not latest.empty and 'ic' in latest.columns:
            avg_ic = latest['ic'].mean()
            st.metric("平均 IC", f"{avg_ic:.4f}")
        else:
            st.metric("平均 IC", "N/A")
    
    with col4:
        st.metric("评估记录", stats.get('total_evaluations', 0))


def show_best_factors(db):
    """显示最佳因子"""
    st.subheader("🏆 最佳因子 TOP 5")
    
    latest = db.get_latest_evaluations(limit=50)
    
    if latest.empty:
        st.info("暂无评估数据")
        return
    
    # 计算平均 IC
    avg_ic = latest.groupby('factor_name')['ic'].mean()
    top_factors = avg_ic.sort_values(ascending=False).head(5)
    
    # 显示
    cols = st.columns(5)
    
    for i, (name, ic) in enumerate(top_factors.items()):
        with cols[i]:
            st.markdown(f"""
            <div style="text-align: center; padding: 15px; background: #f0f2f6; border-radius: 10px;">
                <div style="font-size: 24px;">{'🥇' if i==0 else '🥈' if i==1 else '🥉' if i==2 else '⭐'}</div>
                <div style="font-weight: bold; margin-top: 5px;">{name}</div>
                <div style="color: #1f77b4; font-size: 18px;">IC: {ic:.4f}</div>
            </div>
            """, unsafe_allow_html=True)


def show_ic_trend(db):
    """显示 IC 趋势"""
    st.subheader("📈 IC 趋势")
    
    latest = db.get_latest_evaluations(limit=100)
    
    if latest.empty:
        st.info("暂无评估数据")
        return
    
    # 按日期聚合
    if 'eval_date' in latest.columns and 'ic' in latest.columns:
        daily_ic = latest.groupby('eval_date')['ic'].mean().reset_index()
        daily_ic['eval_date'] = pd.to_datetime(daily_ic['eval_date'])
        daily_ic = daily_ic.sort_values('eval_date')
        
        # 绘制
        fig = pd.DataFrame({
            'date': daily_ic['eval_date'],
            'IC': daily_ic['ic']
        }).set_index('date')
        
        st.line_chart(fig)
        
        # 显示统计
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("IC 均值", f"{daily_ic['ic'].mean():.4f}")
        with col2:
            st.metric("IC 标准差", f"{daily_ic['ic'].std():.4f}")
        with col3:
            positive_ratio = (daily_ic['ic'] > 0).mean()
            st.metric("正 IC 占比", f"{positive_ratio:.1%}")


def show_factor_categories(db):
    """显示因子类别分布"""
    st.subheader("📊 因子类别分布")
    
    factors = db.list_factors()
    
    if factors.empty:
        st.info("暂无因子数据")
        return
    
    if 'category' in factors.columns:
        category_counts = factors['category'].value_counts()
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.dataframe(category_counts)
        
        with col2:
            # 绘制饼图
            st.bar_chart(category_counts)


def show_recent_activity(db):
    """显示最近活动"""
    st.subheader("🕐 最近活动")
    
    latest = db.get_latest_evaluations(limit=10)
    
    if latest.empty:
        st.info("暂无活动")
        return
    
    # 显示最近评估
    recent = latest[['factor_name', 'ic', 'ic_ir', 'win_rate', 'eval_date']].copy()
    recent['eval_date'] = pd.to_datetime(recent['eval_date']).dt.strftime('%Y-%m-%d')
    
    st.dataframe(
        recent,
        use_container_width=True,
        hide_index=True
    )


def show_module_overview():
    """显示模块概览"""
    st.subheader("📁 模块概览")
    
    modules = [
        ("🔧 Pipeline", "pipeline", "因子管道构建", "Momentum, RSI, MA 等"),
        ("📊 评估", "evaluation", "因子性能评估", "IC, 分组收益, 换手率"),
        ("📈 风险", "risk_metrics", "风险指标计算", "夏普, VaR, 回撤"),
        ("🧮 交互", "factor_interaction", "因子相关性分析", "相关性矩阵, 组合分析"),
        ("📋 报告", "tearsheet", "Tearsheet 报告", "HTML 导出, Monte Carlo"),
        ("🔢 Pandas 扩展", "pandas_ext", "Pandas 扩展方法", "returns.quant.sharpe()"),
    ]
    
    # 创建卡片布局
    cols = st.columns(3)
    
    for i, (name, module, desc, features) in enumerate(modules):
        with cols[i % 3]:
            st.markdown(f"""
            <div style="padding: 15px; background: #f8f9fa; border-radius: 10px; margin: 5px;">
                <div style="font-size: 20px;">{name}</div>
                <div style="color: #666; font-size: 12px; margin: 5px 0;">{desc}</div>
                <div style="font-size: 11px; color: #888;">{features}</div>
            </div>
            """, unsafe_allow_html=True)


def show_quick_links():
    """显示快捷链接"""
    st.subheader("⚡ 快捷入口")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.page_link("pages/factor_evaluation.py", label="📊 因子评估")
    
    with col2:
        st.page_link("pages/factor_interaction.py", label="🔗 因子交互")
    
    with col3:
        st.page_link("pages/pipeline_editor.py", label="🔧 Pipeline 编辑器")
    
    with col4:
        st.page_link("pages/stock_selection.py", label="📈 股票筛选")


def main():
    """首页主函数"""
    init_session_state()
    
    show_header()
    
    db = get_database()
    
    # 统计卡片
    show_metrics(db)
    
    # 最佳因子
    show_best_factors(db)
    
    # 模块概览
    with st.expander("📁 查看所有模块"):
        show_module_overview()
    
    # IC 趋势
    show_ic_trend(db)
    
    col1, col2 = st.columns(2)
    
    with col1:
        show_factor_categories(db)
    
    with col2:
        show_recent_activity(db)
    
    # 快捷入口
    show_quick_links()


if __name__ == "__main__":
    main()
