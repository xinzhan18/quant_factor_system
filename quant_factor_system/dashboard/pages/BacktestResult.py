"""
回测结果展示页面
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go


def render_backtest_result(result):
    """
    渲染回测结果
    
    Args:
        result: BacktestResult对象
    """
    st.title("📈 回测结果")
    
    if result is None:
        st.warning("暂无回测结果，请先运行回测")
        return
    
    # 1. 摘要指标
    st.subheader("📊 绩效摘要")
    
    summary = result.summary()
    
    # 指标卡片
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("总收益率", summary.get('总收益率', 'N/A'))
    with col2:
        st.metric("年化收益率", summary.get('年化收益率', 'N/A'))
    with col3:
        st.metric("夏普比率", summary.get('夏普比率', 'N/A'))
    with col4:
        st.metric("最大回撤", summary.get('最大回撤', 'N/A'))
    
    # 第二行
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("总交易次数", summary.get('总交易次数', 0))
    with col2:
        st.metric("胜率", summary.get('胜率', 'N/A'))
    with col3:
        st.metric("最终资金", summary.get('最终资金', 'N/A'))
    with col4:
        st.metric("卡玛比率", summary.get('卡玛比率', 'N/A'))
    
    # 2. 收益曲线
    if result.equity_curve:
        df = pd.DataFrame(result.equity_curve)
        
        if not df.empty and 'date' in df.columns and 'equity' in df.columns:
            st.subheader("📈 收益曲线")
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=df['date'],
                y=df['equity'],
                mode='lines',
                name='资金曲线',
                line=dict(color='#1f77b4', width=2)
            ))
            
            fig.add_hline(
                y=result.initial_capital,
                line_dash="dash",
                line_color="gray",
                annotation_text="初始资金"
            )
            
            fig.update_layout(
                title="资金曲线",
                xaxis_title="日期",
                yaxis_title="资金",
                hovermode='x unified',
                template='plotly_white'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 3. 回撤曲线
            st.subheader("📉 回撤分析")
            
            df['drawdown'] = (df['equity'].cummax() - df['equity']) / df['equity'].cummax()
            
            fig_dd = go.Figure()
            
            fig_dd.add_trace(go.Scatter(
                x=df['date'],
                y=df['drawdown'] * 100,
                fill='tozeroy',
                mode='lines',
                name='回撤',
                line=dict(color='#ff7f0e', width=1)
            ))
            
            fig_dd.update_layout(
                title="回撤曲线",
                xaxis_title="日期",
                yaxis_title="回撤 (%)",
                hovermode='x unified',
                template='plotly_white'
            )
            
            st.plotly_chart(fig_dd, use_container_width=True)
            
            # 4. 月度收益
            st.subheader("📅 月度收益")
            
            df['date'] = pd.to_datetime(df['date'])
            df['month'] = df['date'].dt.to_period('M')
            
            monthly_returns = df.groupby('month')['equity'].agg(['first', 'last'])
            monthly_returns['return_pct'] = (monthly_returns['last'] - monthly_returns['first']) / monthly_returns['first'] * 100
            
            fig_monthly = go.Figure()
            
            colors = ['green' if r > 0 else 'red' for r in monthly_returns['return_pct']]
            
            fig_monthly.add_trace(go.Bar(
                x=[str(m) for m in monthly_returns.index],
                y=monthly_returns['return_pct'],
                marker_color=colors,
                name='月度收益'
            ))
            
            fig_monthly.update_layout(
                title="月度收益率",
                xaxis_title="月份",
                yaxis_title="收益率 (%)",
                template='plotly_white'
            )
            
            st.plotly_chart(fig_monthly, use_container_width=True)
    
    # 5. 交易记录
    if result.trades:
        st.subheader("📝 交易记录")
        
        trades_df = pd.DataFrame(result.trades)
        
        if not trades_df.empty:
            display_cols = ['symbol', 'side', 'quantity', 'price', 'pnl']
            available_cols = [c for c in display_cols if c in trades_df.columns]
            
            st.dataframe(
                trades_df[available_cols].sort_values('timestamp', ascending=False),
                use_container_width=True
            )


def render_comparison_results(results_list):
    """渲染多个回测结果对比"""
    st.title("📊 回测结果对比")
    
    if not results_list:
        st.warning("暂无回测结果")
        return
    
    comparison_data = []
    
    for i, result in enumerate(results_list):
        summary = result.summary()
        comparison_data.append({
            '回测': f'策略{i+1}',
            '总收益率': summary.get('总收益率', 'N/A'),
            '年化收益率': summary.get('年化收益率', 'N/A'),
            '夏普比率': summary.get('夏普比率', 'N/A'),
            '最大回撤': summary.get('最大回撤', 'N/A'),
            '胜率': summary.get('胜率', 'N/A'),
        })
    
    comparison_df = pd.DataFrame(comparison_data)
    st.table(comparison_df)


def main():
    """主函数"""
    st.warning("请从 Pipeline 页面运行回测后查看结果")
    
    # 可以添加从数据库加载历史回测结果的功能
    st.info("💡 提示: 回测结果会自动保存到数据库")


if __name__ == "__main__":
    main()
