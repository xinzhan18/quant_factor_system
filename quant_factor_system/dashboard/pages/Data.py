"""
数据浏览页面
"""

import streamlit as st
import pandas as pd
import sys
import os

# 包已通过 pip 安装到 conda 环境中

from quant_factor_system.data import DataManager


def format_number(value: float, decimals: int = 2) -> str:
    """格式化数字"""
    if pd.isna(value):
        return "N/A"
    return f"{value:.{decimals}f}"


def format_percent(value: float, decimals: int = 2) -> str:
    """格式化百分比"""
    if pd.isna(value):
        return "N/A"
    return f"{value * 100:.{decimals}f}%"


def create_summary_stats(data: pd.DataFrame) -> dict:
    """创建汇总统计"""
    stats = {}
    
    if 'close' in data.columns:
        returns = data['close'].pct_change().dropna()
        
        stats.update({
            "total_return": (data['close'].iloc[-1] / data['close'].iloc[0] - 1) if len(data) > 1 else 0,
            "volatility": returns.std(),
            "sharpe_ratio": returns.mean() / returns.std() if returns.std() > 0 else 0,
            "win_rate": (returns > 0).sum() / len(returns[returns != 0]) if len(returns[returns != 0]) > 0 else 0,
            "num_samples": len(data),
        })
    
    return stats


def main():
    """数据浏览主函数"""
    st.set_page_config(
        page_title="数据浏览 - QuantFactor",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 数据浏览")
    
    # 侧边栏 - 数据设置
    with st.sidebar:
        st.header("📁 数据设置")
        
        symbols = st.text_input(
            "股票代码",
            value="TEST_001,TEST_002,TEST_003"
        ).split(",")
        symbols = [s.strip() for s in symbols if s.strip()]
        
        frequency = st.selectbox(
            "数据频率",
            options=["daily", "1min", "5min", "15min", "1hour"],
            index=0
        )
        
        n_periods = st.slider("数据周期", 10, 500, 100)
        
        st.divider()
        
        if st.button("🔄 加载数据", use_container_width=True):
            st.rerun()
    
    # 主内容
    try:
        # 获取数据
        dm = DataManager(use_db=False)
        data = dm.get_price_data(
            symbols=symbols,
            frequency=frequency,
            n_periods=n_periods
        )
        
        if data.empty:
            st.warning("无数据，请调整参数")
            return
        
        st.success(f"✅ 加载 {len(symbols)} 只股票, 共 {len(data)} 行数据")
        
        # 统计信息
        stats = create_summary_stats(data)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("总收益率", format_percent(stats.get('total_return', 0)))
        with col2:
            st.metric("波动率", format_percent(stats.get('volatility', 0)))
        with col3:
            st.metric("夏普比率", format_number(stats.get('sharpe_ratio', 0)))
        with col4:
            st.metric("样本数", stats.get('num_samples', 0))
        
        # 数据表格
        st.subheader("📋 数据预览")
        
        st.dataframe(
            data.head(50),
            use_container_width=True
        )
        
        # 下载数据
        st.subheader("💾 导出数据")
        
        csv = data.to_csv(index=False).encode('utf-8')
        
        st.download_button(
            "📥 下载 CSV",
            data=csv,
            file_name="data_export.csv",
            mime="text/csv"
        )
        
    except Exception as e:
        st.error(f"错误: {e}")


if __name__ == "__main__":
    main()
