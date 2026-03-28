"""
因子评估页面 — 从 mining DB 表加载因子
Factor Evaluation Page — reads from mining_factors / mining_factor_values tables
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime as dt

from data import TimescaleDB
from data.loaders import (
    get_available_factors,
    get_factor_data,
    get_factor_metrics,
    get_price_data,
)
from report.analytics.ic import ICAnalyzer


def generate_ic_chart(rolling_ic_df: pd.DataFrame, split_date: dt, factor_name: str) -> go.Figure:
    """生成IC时间序列图"""
    fig = px.line(
        rolling_ic_df,
        x='date',
        y='IC',
        color='period' if 'period' in rolling_ic_df.columns else None,
        title=f"{factor_name} 滚动IC (60日)",
        color_discrete_map={'训练集': 'green', '测试集': 'red'}
    )
    if split_date:
        split_str = split_date.strftime('%Y-%m-%d')
        fig.add_shape(
            type="line", x0=split_str, x1=split_str, y0=0, y1=1,
            xref="x", yref="paper",
            line=dict(dash="dash", color="gray", width=2)
        )
        fig.add_annotation(
            x=split_str, y=1, xref="x", yref="paper",
            text="训练/测试分界", showarrow=False, yshift=10
        )
    fig.add_hline(y=0, line_dash="dot", line_color="black")
    fig.add_hline(y=0.02, line_dash="dot", line_color="blue", annotation_text="IC=0.02")
    fig.add_hline(y=-0.02, line_dash="dot", line_color="blue", annotation_text="IC=-0.02")
    fig.update_layout(template='plotly_white', height=400)
    return fig


def generate_group_returns_chart(cumulative_returns: pd.DataFrame, factor_name: str) -> go.Figure:
    """生成分组累计收益图"""
    fig = px.line(
        cumulative_returns,
        title=f"{factor_name} 各分组累计收益曲线",
        labels={'value': '累计收益', 'time': '日期', 'group': '分组'}
    )
    fig.update_layout(template='plotly_white', height=400)
    return fig


def generate_long_short_chart(cumulative_returns: pd.DataFrame) -> go.Figure:
    """生成多空组合图"""
    q5_col = [c for c in cumulative_returns.columns if 'Q5' in str(c)]
    q1_col = [c for c in cumulative_returns.columns if 'Q1' in str(c)]
    if not q5_col or not q1_col:
        return None
    long_short = cumulative_returns[q5_col[0]] - cumulative_returns[q1_col[0]]
    fig = px.line(long_short, title="多空组合累计收益 (Q5-Q1)")
    fig.add_hline(y=0, line_dash="dot", line_color="black")
    fig.update_layout(template='plotly_white', height=350)
    return fig


def generate_group_bar_chart(mean_returns: pd.Series) -> go.Figure:
    """生成分组年化收益柱状图"""
    fig = px.bar(
        x=mean_returns.index, y=mean_returns.values * 100,
        title="各分组年化收益率",
        labels={'x': '分组', 'y': '年化收益率 (%)'},
        color=mean_returns.values,
        color_continuous_scale='RdYlGn'
    )
    fig.add_hline(y=0, line_dash="dot", line_color="black")
    fig.update_layout(template='plotly_white', height=350)
    return fig


def generate_multi_rolling_ic_chart(daily_ic: pd.DataFrame) -> go.Figure:
    """生成多窗口滚动IC图"""
    windows = [20, 60, 120]
    rolling_data = {}
    for w in windows:
        rolling_data[f'IC_{w}d'] = daily_ic['IC'].rolling(window=w, min_periods=10).mean()
    df = pd.DataFrame(rolling_data).dropna()
    if df.empty:
        return None
    fig = px.line(df, title="不同窗口滚动IC对比")
    fig.add_hline(y=0, line_dash="dot", line_color="black")
    fig.add_hline(y=0.02, line_dash="dot", line_color="blue", annotation_text="IC=0.02")
    fig.add_hline(y=-0.02, line_dash="dot", line_color="blue", annotation_text="IC=-0.02")
    fig.update_layout(template='plotly_white', height=400)
    return fig


def compute_group_returns(merged: pd.DataFrame) -> dict:
    """计算分组收益"""
    merged = merged.dropna(subset=['value', 'future_return'])
    merged['group'] = pd.qcut(merged['value'], q=5, labels=['Q1(低)', 'Q2', 'Q3', 'Q4', 'Q5(高)'])
    group_returns = merged.groupby(['time', 'group'])['future_return'].mean().reset_index()
    group_returns_pivot = group_returns.pivot(index='time', columns='group', values='future_return')
    cumulative_returns = (1 + group_returns_pivot).cumprod() - 1
    mean_returns = group_returns_pivot.mean() * 252
    stats = group_returns_pivot.std() * (252 ** 0.5)
    sharpe = mean_returns / stats
    return {
        'group_returns_pivot': group_returns_pivot,
        'cumulative_returns': cumulative_returns,
        'mean_returns': mean_returns,
        'sharpe': sharpe,
        'std': stats,
    }


def main():
    st.set_page_config(page_title="因子评估 - QuantFactor", page_icon="📈", layout="wide")
    st.title("📈 因子评估")

    db = TimescaleDB()
    conn = db.connection

    # ==================== 侧边栏 ====================
    with st.sidebar:
        st.header("⚙️ 因子设置")

        factors = get_available_factors(conn)
        if not factors:
            st.warning("数据库中尚无已入库的因子。请先运行因子挖掘流程。")
            return

        # Build selector options
        factor_options = {
            f"{f['factor_id']}: {f['name']} (IC={f.get('ic_mean', 0):.4f})" if f.get('ic_mean') else f"{f['factor_id']}: {f['name']}": f
            for f in factors
        }
        selected_label = st.selectbox("选择因子", options=list(factor_options.keys()))
        selected = factor_options[selected_label]

        factor_id = selected["factor_id"]
        factor_name = selected["name"]

        # Load factor values
        with st.spinner('正在加载因子数据...'):
            factor_df, error = get_factor_data(factor_id, conn)

        if error:
            st.warning(f"⚠️ {error}")
            return

        if factor_df is None or factor_df.empty:
            st.warning("无数据")
            return

        # Load metrics
        metrics = get_factor_metrics(factor_id, conn)

        # Factor info
        st.success(f"✅ {factor_name}")
        if metrics:
            st.caption(f"表达式: `{metrics.get('expression', '')}`")
            st.caption(f"类别: {metrics.get('category', '')} | 入库: {metrics.get('admitted_at', '')}")

            # Report link
            report_path = metrics.get("report_path")
            if report_path:
                st.markdown(f"[📄 查看HTML报告]({report_path})")

    # ==================== 数据范围 ====================
    min_date = factor_df['time'].min()
    max_date = factor_df['time'].max()

    # Use train/test split from metrics if available
    if metrics and metrics.get('train_end'):
        split_date = pd.to_datetime(metrics['train_end'])
    else:
        split_date = min_date + (max_date - min_date) / 2

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("数据条数", f"{len(factor_df):,}")
    with col2:
        st.metric("股票数", f"{factor_df['symbol'].nunique():,}")
    with col3:
        st.metric("开始日期", min_date.strftime('%Y-%m-%d') if hasattr(min_date, 'strftime') else str(min_date))
    with col4:
        st.metric("结束日期", max_date.strftime('%Y-%m-%d') if hasattr(max_date, 'strftime') else str(max_date))

    # ==================== 指标概览 ====================
    if metrics:
        st.subheader("📊 评估指标概览")
        m1, m2, m3, m4, m5 = st.columns(5)
        with m1:
            st.metric("IC (IS)", f"{metrics.get('ic_mean_is', 0):.4f}" if metrics.get('ic_mean_is') else "N/A")
        with m2:
            st.metric("IC (OOS)", f"{metrics.get('ic_mean_oos', 0):.4f}" if metrics.get('ic_mean_oos') else "N/A")
        with m3:
            st.metric("IC IR", f"{metrics.get('ic_ir', 0):.2f}" if metrics.get('ic_ir') else "N/A")
        with m4:
            st.metric("多空收益", f"{metrics.get('ls_return', 0):.4f}" if metrics.get('ls_return') else "N/A")
        with m5:
            st.metric("单调性", f"{metrics.get('monotonicity', 0):.2f}" if metrics.get('monotonicity') else "N/A")

    # ==================== IC 分析 ====================
    st.subheader("📈 IC分析 (信息系数)")

    symbols = factor_df['symbol'].unique().tolist()
    with st.spinner('正在获取价格数据...'):
        price_df = get_price_data(
            symbols,
            min_date.strftime('%Y-%m-%d') if hasattr(min_date, 'strftime') else str(min_date),
            max_date.strftime('%Y-%m-%d') if hasattr(max_date, 'strftime') else str(max_date),
            conn
        )

    if price_df is not None and not price_df.empty:
        analyzer = ICAnalyzer(factor_name)
        with st.spinner('正在计算IC...'):
            ic_result = analyzer.compute_ic(factor_df, price_df, split_date)

        if 'error' not in ic_result:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("整体IC", f"{ic_result.get('ic_all', 0):.4f}")
            with col2:
                st.metric("🟢 训练集IC", f"{ic_result.get('ic_train', 0):.4f}")
            with col3:
                st.metric("🔴 测试集IC", f"{ic_result.get('ic_test', 0):.4f}")

            # IC 时间序列
            if 'rolling_ic' in ic_result:
                rolling_ic = ic_result['rolling_ic'].copy()
                if 'period' in rolling_ic.columns:
                    rolling_ic['period'] = rolling_ic['period'].map({'train': '训练集', 'test': '测试集'})

                st.write("### 📉 IC时间序列")
                fig_ic = generate_ic_chart(rolling_ic, split_date, factor_name)
                st.plotly_chart(fig_ic, use_container_width=True)

                # IC 分布
                st.write("### 📊 IC分布")
                col1, col2 = st.columns(2)
                with col1:
                    fig_ic_hist = px.histogram(
                        rolling_ic, x='IC', nbins=30,
                        color='period' if 'period' in rolling_ic.columns else None,
                        color_discrete_map={'训练集': 'green', '测试集': 'red'},
                        title="IC分布直方图", marginal='box'
                    )
                    fig_ic_hist.add_vline(x=0, line_dash="dot", line_color="black")
                    fig_ic_hist.update_layout(template='plotly_white', height=400)
                    st.plotly_chart(fig_ic_hist, use_container_width=True)
                with col2:
                    ic_stats = rolling_ic.groupby('period')['IC'].agg(['mean', 'std', 'min', 'max', 'median']) if 'period' in rolling_ic.columns else rolling_ic['IC'].agg(['mean', 'std', 'min', 'max', 'median']).to_frame().T
                    st.write("**IC统计指标:**")
                    st.dataframe(ic_stats.style.format("{:.4f}"), use_container_width=True)

                # 多窗口滚动IC
                st.write("### 📈 滚动IC对比")
                daily_ic = rolling_ic[['date', 'IC']].copy()
                fig_multi = generate_multi_rolling_ic_chart(daily_ic)
                if fig_multi:
                    st.plotly_chart(fig_multi, use_container_width=True)
        else:
            st.warning(f"IC计算失败: {ic_result.get('error')}")

        # ==================== 分组收益 ====================
        st.subheader("🎯 因子分组收益分析")
        merged = pd.merge(factor_df, price_df, on=['time', 'symbol'], how='inner')
        merged = merged.sort_values(['symbol', 'time'])
        merged['future_return'] = merged.groupby('symbol')['close'].pct_change().shift(-1)
        merged = merged.dropna(subset=['value', 'future_return'])
        merged = merged[merged['future_return'].abs() < 0.11]

        if len(merged) > 100:
            with st.spinner('正在计算分组收益...'):
                group_result = compute_group_returns(merged)

            st.write("### 📊 各分组年化收益率")
            fig_bar = generate_group_bar_chart(group_result['mean_returns'])
            st.plotly_chart(fig_bar, use_container_width=True)

            st.write("### 📈 各分组累计收益曲线")
            fig_cum = generate_group_returns_chart(group_result['cumulative_returns'], factor_name)
            st.plotly_chart(fig_cum, use_container_width=True)

            st.write("### 🔄 多空组合 (Q5-Q1)")
            fig_ls = generate_long_short_chart(group_result['cumulative_returns'])
            if fig_ls:
                st.plotly_chart(fig_ls, use_container_width=True)

            st.write("**分组收益统计:**")
            stats_df = pd.DataFrame({
                '分组': group_result['mean_returns'].index,
                '年化收益(%)': (group_result['mean_returns'] * 100).round(2),
                '收益标准差(%)': (group_result['std'] * 100).round(2),
                '夏普比率': group_result['sharpe'].round(2)
            })
            st.dataframe(stats_df, use_container_width=True)
    else:
        st.warning("无法获取价格数据")


if __name__ == "__main__":
    main()
