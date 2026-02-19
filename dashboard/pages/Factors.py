"""
因子评估页面 - 后端计算模式
从数据库加载因子数据并计算IC，只传图表和统计结果给前端

重构：调用 data/loaders 抽取数据加载逻辑
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime as dt

from quant_factor_system.data import TimescaleDB
from quant_factor_system.data.loaders import (
    get_factor_data,
    get_price_data,
    get_factor_overview,
    get_available_factors,
)
from quant_factor_system.factors.visualization import ICAnalyzer


# ==================== 因子评估页面 ====================

@st.cache_data(ttl=3600)
def get_factor_overview_cached(connection):
    """获取因子概览（缓存）"""
    return get_factor_overview(connection)


def generate_ic_chart(rolling_ic_df: pd.DataFrame, split_date: dt, factor_name: str) -> go.Figure:
    """
    后端：计算IC分析（调用 ICAnalyzer）
    
    统一使用 ICAnalyzer 的逻辑，消除代码重复
    """
    if progress_bar:
        progress_bar.progress(10)
    
    # 使用 ICAnalyzer 计算 IC
    analyzer = ICAnalyzer()
    ic_result = analyzer.compute_ic(factor_df, price_df, split_date, method='spearman')
    
    if 'error' in ic_result:
        return ic_result
    
    if progress_bar:
        progress_bar.progress(50)
    
    # 转换分组标识（英文 → 中文）
    result = {}
    
    # IC值转换
    result['all'] = {
        'ic': ic_result.get('ic_all', 0),
        'samples': ic_result.get('samples_all', 0)
    }
    
    if 'ic_train' in ic_result:
        result['训练集'] = {
            'ic': ic_result['ic_train'],
            'samples': ic_result.get('samples_train', 0),
            'start': ic_result.get('start_train', ''),
            'end': ic_result.get('end_train', '')
        }
    
    if 'ic_test' in ic_result:
        result['测试集'] = {
            'ic': ic_result['ic_test'],
            'samples': ic_result.get('samples_test', 0),
            'start': ic_result.get('start_test', ''),
            'end': ic_result.get('end_test', '')
        }
    
    # 转换 rolling_ic 分组标识
    if 'rolling_ic' in ic_result:
        rolling_ic = ic_result['rolling_ic'].copy()
        if 'period' in rolling_ic.columns:
            rolling_ic['period'] = rolling_ic['period'].map({
                'train': '训练集',
                'test': '测试集'
            })
        result['rolling_ic'] = rolling_ic
    
    if progress_bar:
        progress_bar.progress(100)
    
    return result


def compute_group_returns(merged: pd.DataFrame, progress_bar=None) -> dict:
    """后端：计算分组收益"""
    if progress_bar:
        progress_bar.progress(0)
    
    merged = merged.dropna(subset=['value', 'future_return'])
    
    if progress_bar:
        progress_bar.progress(30)
    
    # 分组
    merged['group'] = pd.qcut(merged['value'], q=5, labels=['Q1(低)', 'Q2', 'Q3', 'Q4', 'Q5(高)'])
    
    if progress_bar:
        progress_bar.progress(50)
    
    # 计算收益（使用future_return）
    group_returns = merged.groupby(['time', 'group'])['future_return'].mean().reset_index()
    group_returns_pivot = group_returns.pivot(index='time', columns='group', values='future_return')
    cumulative_returns = (1 + group_returns_pivot).cumprod() - 1
    
    # 统计
    mean_returns = group_returns_pivot.mean() * 252
    stats = group_returns_pivot.std() * (252 ** 0.5)
    sharpe = mean_returns / stats
    
    result = {
        'group_returns_pivot': group_returns_pivot,
        'cumulative_returns': cumulative_returns,
        'mean_returns': mean_returns,
        'sharpe': sharpe,
        'std': stats
    }
    
    if progress_bar:
        progress_bar.progress(100)
    
    return result


def generate_ic_chart(rolling_ic_df: pd.DataFrame, split_date: dt, factor_name: str) -> go.Figure:
    """后端：生成IC时间序列图"""
    fig = px.line(
        rolling_ic_df, 
        x='date', 
        y='IC',
        color='period',
        title=f"{factor_name} 滚动IC (60日)",
        color_discrete_map={'训练集': 'green', '测试集': 'red'}
    )
    
    # 添加分隔线
    split_str = split_date.strftime('%Y-%m-%d')
    fig.add_shape(
        type="line",
        x0=split_str, x1=split_str,
        y0=0, y1=1,
        xref="x", yref="paper",
        line=dict(dash="dash", color="gray", width=2)
    )
    fig.add_annotation(
        x=split_str, y=1,
        xref="x", yref="paper",
        text="训练/测试分界",
        showarrow=False,
        yshift=10
    )
    
    fig.add_hline(y=0, line_dash="dot", line_color="black")
    fig.add_hline(y=0.02, line_dash="dot", line_color="blue", annotation_text="IC=0.02")
    fig.add_hline(y=-0.02, line_dash="dot", line_color="blue", annotation_text="IC=-0.02")
    
    fig.update_layout(template='plotly_white', height=400)
    return fig


def generate_group_returns_chart(cumulative_returns: pd.DataFrame, factor_name: str) -> go.Figure:
    """后端：生成分组累计收益图"""
    fig = px.line(
        cumulative_returns, 
        title=f"{factor_name} 各分组累计收益曲线",
        labels={'value': '累计收益', 'time': '日期', 'group': '分组'}
    )
    fig.update_layout(template='plotly_white', height=400)
    return fig


def generate_long_short_chart(cumulative_returns: pd.DataFrame) -> go.Figure:
    """后端：生成多空组合图"""
    if 'Q5(高)' not in cumulative_returns.columns or 'Q1(低)' not in cumulative_returns.columns:
        return None
    
    long_short = cumulative_returns['Q5(高)'] - cumulative_returns['Q1(低)']
    
    fig = px.line(
        long_short, 
        title="多空组合累计收益 (Q5-Q1)",
        labels={'value': '累计收益', 'index': '日期'}
    )
    fig.add_hline(y=0, line_dash="dot", line_color="black")
    fig.update_layout(template='plotly_white', height=350)
    return fig


def generate_group_bar_chart(mean_returns: pd.Series) -> go.Figure:
    """后端：生成分组年化收益柱状图"""
    fig = px.bar(
        x=mean_returns.index, 
        y=mean_returns.values * 100,
        title="各分组年化收益率",
        labels={'x': '分组', 'y': '年化收益率 (%)'},
        color=mean_returns.values,
        color_continuous_scale='RdYlGn'
    )
    fig.add_hline(y=0, line_dash="dot", line_color="black")
    fig.update_layout(template='plotly_white', height=350)
    return fig


def generate_multi_rolling_ic_chart(daily_ic: pd.DataFrame) -> go.Figure:
    """后端：生成多窗口滚动IC图（使用预计算的daily_ic）"""
    windows = [20, 60, 120]
    rolling_data = {}
    
    for w in windows:
        rolling_data[f'IC_{w}d'] = daily_ic['IC'].rolling(window=w, min_periods=10).mean()
    
    df = pd.DataFrame(rolling_data).dropna()
    
    if df.empty:
        return None
    
    fig = px.line(
        df, 
        title="不同窗口滚动IC对比",
        labels={'value': 'IC', 'index': '日期'}
    )
    fig.add_hline(y=0, line_dash="dot", line_color="black")
    fig.add_hline(y=0.02, line_dash="dot", line_color="blue", annotation_text="IC=0.02")
    fig.add_hline(y=-0.02, line_dash="dot", line_color="blue", annotation_text="IC=-0.02")
    fig.update_layout(template='plotly_white', height=400)
    return fig


def main():
    st.set_page_config(
        page_title="因子评估 - QuantFactor",
        page_icon="📈",
        layout="wide"
    )
    
    st.title("📈 因子评估")
    
    db = TimescaleDB()
    
    # ==================== 侧边栏 ====================
    with st.sidebar:
        st.header("⚙️ 因子设置")
        
        # 获取因子数据
        factor_names = get_available_factors()
        selected_factor = st.selectbox("选择因子", options=factor_names, index=0)
        
        with st.spinner('正在加载因子数据...'):
            factor_df, error = get_factor_data(selected_factor, conn)
        
        if error:
            st.warning(f"⚠️ {error}")
            st.subheader("📋 数据库中的因子表")
            overview = get_factor_overview(conn)
            if not overview.empty:
                st.dataframe(overview, use_container_width=True)
            return
        
        if factor_df is None or factor_df.empty:
            st.warning("无数据")
            return
        
        # 计算数据范围和分界日期
        min_date = factor_df['time'].min()
        max_date = factor_df['time'].max()
        split_date = min_date + (max_date - min_date) / 2
        
        # 划分训练/测试集
        factor_df['period'] = factor_df['time'].apply(
            lambda x: '🟢 训练集' if x <= split_date else '🔴 测试集'
        )
        
        train_df = factor_df[factor_df['period'] == '🟢 训练集']
        test_df = factor_df[factor_df['period'] == '🔴 测试集']
        
        st.success(f"✅ {selected_factor}")
        st.info(f"🟢 训练集: {len(train_df):,} 条 | 🔴 测试集: {len(test_df):,} 条")
        
        # 基本信息
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("数据条数", f"{len(factor_df):,}")
        with col2:
            st.metric("股票数", f"{factor_df['symbol'].nunique():,}")
        with col3:
            st.metric("开始日期", min_date.strftime('%Y-%m-%d'))
        with col4:
            st.metric("结束日期", max_date.strftime('%Y-%m-%d'))
        
        # ==================== IC 分析 ====================
        st.subheader("📈 IC分析 (信息系数)")
        
        # 获取价格数据
        symbols = factor_df['symbol'].unique().tolist()
        with st.spinner('正在获取价格数据...'):
            price_df = get_price_data(symbols, min_date.strftime('%Y-%m-%d'), max_date.strftime('%Y-%m-%d'), conn)
        
        if price_df is not None and not price_df.empty:
            # 计算IC
            progress_bar = st.progress(0)
            with st.spinner('正在计算IC分析...'):
                ic_result = compute_ic_analysis(factor_df, price_df, split_date, progress_bar)
            progress_bar.empty()
            
            if 'error' not in ic_result:
                # IC概览
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("整体IC", f"{ic_result.get('all', {}).get('ic', 0):.4f}")
                with col2:
                    st.metric("🟢 训练集IC", f"{ic_result.get('训练集', {}).get('ic', 0):.4f}")
                with col3:
                    st.metric("🔴 测试集IC", f"{ic_result.get('测试集', {}).get('ic', 0):.4f}")
                
                # IC解读
                st.write("**IC解读:**")
                for period, data in [('🟢 训练集', ic_result.get('训练集', {})), 
                                      ('🔴 测试集', ic_result.get('测试集', {}))]:
                    if data:
                        ic = data.get('ic', 0)
                        direction = "反转 ⬇️" if ic < 0 else "动量 ⬆️"
                        quality = "✅ 强" if abs(ic) > 0.03 else "⚠️ 中" if abs(ic) > 0.02 else "❌ 弱"
                        st.write(f"{period}: IC={ic:.4f} | {direction} | {quality} | 样本={data.get('samples', 0):,} | {data.get('start', '')}~{data.get('end', '')}")
                
                # IC时间序列图
                st.write("### 📉 IC时间序列")
                fig_ic = generate_ic_chart(ic_result['rolling_ic'], split_date, selected_factor)
                st.plotly_chart(fig_ic, use_container_width=True)
                
                # IC分布
                st.write("### 📊 IC分布")
                col1, col2 = st.columns(2)
                with col1:
                    fig_ic_hist = px.histogram(
                        ic_result['rolling_ic'], 
                        x='IC', 
                        nbins=30,
                        color='period',
                        color_discrete_map={'训练集': 'green', '测试集': 'red'},
                        title="IC分布直方图",
                        marginal='box'
                    )
                    fig_ic_hist.add_vline(x=0, line_dash="dot", line_color="black")
                    fig_ic_hist.update_layout(template='plotly_white', height=400)
                    st.plotly_chart(fig_ic_hist, use_container_width=True)
                with col2:
                    ic_stats = ic_result['rolling_ic'].groupby('period')['IC'].agg(['mean', 'std', 'min', 'max', 'median'])
                    win_rate = ic_result['rolling_ic'].groupby('period').apply(lambda x: (x['IC'] > 0).mean())
                    ic_rate = ic_result['rolling_ic'].groupby('period').apply(lambda x: (x['IC'].abs() > 0.02).mean())
                    
                    # 添加为新列
                    ic_stats['胜率(IC>0)'] = win_rate
                    ic_stats['|IC|>0.02比例'] = ic_rate
                    
                    st.write("**IC统计指标:**")
                    st.dataframe(ic_stats.style.format("{:.4f}"), use_container_width=True)
            else:
                st.warning(f"IC计算失败: {ic_result.get('error')}")
        else:
            st.warning("无法获取价格数据，无法计算IC")
        
        # ==================== 分组收益分析 ====================
        st.subheader("🎯 因子分组收益分析")
        
        # 合并数据用于分组分析
        if price_df is not None and not price_df.empty:
            merged = pd.merge(factor_df, price_df, on=['time', 'symbol'], how='inner')
            merged = merged.sort_values(['symbol', 'time'])
            merged['future_return'] = merged.groupby('symbol')['close'].pct_change().shift(-1)
            merged = merged.dropna(subset=['value', 'future_return'])
            merged = merged[merged['future_return'].abs() < 0.11]
            
            progress_bar = st.progress(0)
            with st.spinner('正在计算分组收益...'):
                group_result = compute_group_returns(merged, progress_bar)
            progress_bar.empty()
            
            # 分组年化收益柱状图
            st.write("### 📊 各分组年化收益率")
            fig_bar = generate_group_bar_chart(group_result['mean_returns'])
            st.plotly_chart(fig_bar, use_container_width=True)
            
            # 累计收益曲线
            st.write("### 📈 各分组累计收益曲线")
            fig_cum = generate_group_returns_chart(group_result['cumulative_returns'], selected_factor)
            st.plotly_chart(fig_cum, use_container_width=True)
            
            # 多空组合
            st.write("### 🔄 多空组合 (Q5-Q1)")
            fig_ls = generate_long_short_chart(group_result['cumulative_returns'])
            if fig_ls:
                st.plotly_chart(fig_ls, use_container_width=True)
            
            # 分组统计表
            st.write("**分组收益统计:**")
            stats_df = pd.DataFrame({
                '分组': group_result['mean_returns'].index,
                '年化收益(%)': (group_result['mean_returns'] * 100).round(2),
                '收益标准差(%)': (group_result['std'] * 100).round(2),
                '夏普比率': group_result['sharpe'].round(2)
            })
            st.dataframe(stats_df, use_container_width=True)
        
        # ==================== 滚动IC分析 ====================
        st.subheader("📈 滚动IC统计分析")
        
        if price_df is not None and not price_df.empty:
            progress_bar = st.progress(0)
            with st.spinner('正在计算滚动IC...'):
                # 使用预计算的daily_ic（已在compute_ic_analysis中完成）
                daily_ic = ic_result['rolling_ic'][['date', 'IC']].copy()
                fig_multi = generate_multi_rolling_ic_chart(daily_ic)
            progress_bar.empty()
            
            if fig_multi:
                st.plotly_chart(fig_multi, use_container_width=True)
                
                # 统计表
                rolling_df = fig_multi.data[0].y  # 从图中提取数据
                st.write("**滚动IC统计:**")
                st.info("请查看图中各条线的统计信息")
        
        # ==================== 因子概览 ====================
        st.divider()
        st.subheader("📋 所有因子表概览")
        
        with st.spinner('正在加载因子表概览...'):
            overview = get_factor_overview_cached(conn)
        if not overview.empty:
            st.dataframe(overview, use_container_width=True)
        else:
            st.info("暂无因子表信息")


if __name__ == "__main__":
    main()
