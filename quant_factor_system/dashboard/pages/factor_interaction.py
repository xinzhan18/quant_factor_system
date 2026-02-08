"""
因子交互分析页面
展示因子相关性、热力图、组合分析
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from config import (
    st, pd, np, init_session_state, get_database,
    get_csv_storage, FACTOR_CATEGORIES
)


def show_factor_correlation_matrix(db):
    """显示因子相关性矩阵"""
    st.subheader("🔗 因子相关性矩阵")
    
    # 获取所有因子
    factors = db.list_factors()
    
    if factors.empty:
        st.warning("暂无因子数据")
        return
    
    # 选择要分析的因子
    factor_names = factors['name'].tolist()
    selected_factors = st.multiselect(
        "选择因子进行相关性分析",
        factor_names,
        default=factor_names[:3] if len(factor_names) >= 3 else factor_names
    )
    
    if len(selected_factors) < 2:
        st.info("请至少选择2个因子进行相关性分析")
        return
    
    # 获取因子数据
    csv = get_csv_storage()
    
    correlation_data = []
    
    for factor_name in selected_factors:
        factor_data = csv.load_factor_data(factor_name)
        if factor_data is not None and 'value' in factor_data.columns:
            # 按日期聚合
            daily_mean = factor_data.groupby('date')['value'].mean()
            correlation_data.append({
                'factor': factor_name,
                'values': daily_mean
            })
    
    if len(correlation_data) < 2:
        st.warning("无法获取足够的因子数据进行相关性分析")
        return
    
    # 计算相关性矩阵
    align_data = pd.DataFrame({
        d['factor']: d['values'] for d in correlation_data
    }).dropna()
    
    if align_data.empty:
        st.warning("因子数据无法对齐")
        return
    
    corr_matrix = align_data.corr()
    
    # 绘制热力图
    fig = px.imshow(
        corr_matrix,
        text_auto='.2f',
        aspect="auto",
        color_continuous_scale='RdBu_r',
        zmin=-1, zmax=1,
        title="因子相关性热力图"
    )
    
    fig.update_layout(
        xaxis_title="因子",
        yaxis_title="因子",
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 显示高相关因子对
    show_high_correlation_pairs(corr_matrix)


def show_high_correlation_pairs(corr_matrix):
    """显示高相关因子对"""
    st.subheader("⚠️ 高相关因子对")
    
    high_corr = []
    threshold = 0.7
    
    for i in range(len(corr_matrix.columns)):
        for j in range(i + 1, len(corr_matrix.columns)):
            corr_val = corr_matrix.iloc[i, j]
            if abs(corr_val) >= threshold:
                high_corr.append({
                    '因子1': corr_matrix.columns[i],
                    '因子2': corr_matrix.columns[j],
                    '相关性': f"{corr_val:.3f}"
                })
    
    if high_corr:
        df = pd.DataFrame(high_corr)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.warning(f"发现 {len(high_corr)} 对高相关因子 (|r| >= {threshold})")
    else:
        st.success("未发现高相关因子对 (|r| >= 0.7)")


def show_factor_combiner(db):
    """因子组合器"""
    st.subheader("🧮 因子组合器")
    
    factors = db.list_factors()
    
    if factors.empty:
        st.warning("暂无因子数据")
        return
    
    factor_names = factors['name'].tolist()
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("#### 选择因子并设置权重")
        
        selected_factors = []
        weights = []
        
        for i, factor_name in enumerate(factor_names):
            col_a, col_b = st.columns([3, 1])
            with col_a:
                use = st.checkbox(f"使用 {factor_name}", value=(i < 2))
            with col_b:
                weight = st.number_input(
                    f"权重",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.5 if i < 2 else 0.5,
                    step=0.1,
                    key=f"weight_{factor_name}"
                )
            
            if use:
                selected_factors.append(factor_name)
                weights.append(weight)
        
        # 归一化权重
        if weights:
            total = sum(weights)
            weights = [w / total for w in weights]
    
    with col2:
        st.markdown("#### 组合预览")
        
        if len(selected_factors) >= 2:
            # 创建组合名
            combo_name = " + ".join([f"{w:.1f}*{name}" 
                                    for w, name in zip(weights, selected_factors)])
            
            st.info(f"组合公式: {combo_name}")
            
            # 显示权重条形图
            weight_df = pd.DataFrame({
                '因子': selected_factors,
                '权重': weights
            })
            
            fig = px.bar(
                weight_df,
                x='因子',
                y='权重',
                title="因子权重分布",
                color='权重',
                color_continuous_scale='Blues'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 保存组合按钮
            if st.button("💾 保存因子组合"):
                combo_id = f"combo_{len(selected_factors)}factors"
                db.save_factor_combo(combo_id, {
                    'factors': selected_factors,
                    'weights': weights,
                    'formula': combo_name,
                    'created_at': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
                })
                st.success(f"组合已保存: {combo_id}")
        else:
            st.info("请至少选择2个因子进行组合")


def show_ic_correlation_analysis(db):
    """IC 相关性分析"""
    st.subheader("📊 IC 相关性分析")
    
    factors = db.list_factors()
    
    if factors.empty:
        st.warning("暂无因子数据")
        return
    
    factor_names = factors['name'].tolist()
    
    # 选择要分析的因子
    selected = st.multiselect(
        "选择因子分析 IC 相关性",
        factor_names,
        default=factor_names[:3] if len(factor_names) >= 3 else factor_names
    )
    
    if len(selected) < 2:
        st.info("请至少选择2个因子")
        return
    
    # 获取评估结果
    ic_data = []
    
    for factor_name in selected:
        evals = db.get_evaluations(factor_name, limit=100)
        if not evals.empty and 'ic' in evals.columns:
            ic_data.append({
                'factor': factor_name,
                'ic_series': evals.set_index('eval_date')['ic'].dropna()
            })
    
    if len(ic_data) < 2:
        st.warning("无法获取足够的 IC 数据")
        return
    
    # 对齐 IC 序列
    align_df = pd.DataFrame({
        d['factor']: d['ic_series'] for d in ic_data
    }).dropna()
    
    if align_df.empty:
        st.warning("IC 数据无法对齐")
        return
    
    # 计算 IC 相关性
    ic_corr = align_df.corr()
    
    # 绘制热力图
    fig = px.imshow(
        ic_corr,
        text_auto='.2f',
        aspect="auto",
        color_continuous_scale='RdBu_r',
        zmin=-1, zmax=1,
        title="因子 IC 相关性"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # IC 稳定性分析
    show_ic_stability(align_df)


def show_ic_stability(ic_df):
    """IC 稳定性分析"""
    st.subheader("📈 IC 稳定性")
    
    stability = pd.DataFrame({
        '因子': ic_df.columns,
        'IC均值': ic_df.mean(),
        'IC标准差': ic_df.std(),
        'IC IR': ic_df.mean() / (ic_df.std() + 1e-8),
        '正IC占比': (ic_df > 0).mean()
    })
    
    stability = stability.sort_values('IC IR', ascending=False)
    
    # 绘制
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=stability['因子'],
        y=stability['IC IR'],
        name='IC IR',
        marker_color='steelblue'
    ))
    
    fig.add_trace(go.Bar(
        x=stability['因子'],
        y=stability['正IC占比'],
        name='正IC占比',
        marker_color='green',
        yaxis='y2'
    ))
    
    fig.update_layout(
        title="因子 IC 稳定性对比",
        yaxis=dict(title="IC IR"),
        yaxis2=dict(
            title="正IC占比",
            overlaying='y',
            side='right'
        ),
        barmode='group',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 显示表格
    st.dataframe(
        stability.style.background_gradient(subset=['IC IR'], cmap='Blues'),
        use_container_width=True
    )


def show_factor_decay_analysis(db):
    """因子衰减分析"""
    st.subheader("📉 因子衰减分析")
    
    factors = db.list_factors()
    
    if factors.empty:
        st.warning("暂无因子数据")
        return
    
    factor_name = st.selectbox("选择因子", factors['name'].tolist())
    
    # 获取评估结果
    evals = db.get_evaluations(factor_name, limit=100)
    
    if evals.empty:
        st.info("暂无评估数据")
        return
    
    # 模拟衰减数据（如果有）
    if 'ic_decay' in evals.columns:
        # 尝试解析 ic_decay
        decay_data = []
        for _, row in evals.iterrows():
            if isinstance(row.get('ic_decay'), dict):
                for lag, ic in row['ic_decay'].items():
                    decay_data.append({
                        'lag': int(lag.replace('lag_', '')),
                        'ic': ic,
                        'date': row['eval_date']
                    })
        
        if decay_data:
            decay_df = pd.DataFrame(decay_data)
            
            # 绘制衰减曲线
            fig = px.line(
                decay_df.groupby('lag')['ic'].mean().reset_index(),
                x='lag',
                y='ic',
                markers=True,
                title=f"{factor_name} IC 衰减"
            )
            
            fig.add_hline(y=0, line_dash="dash", color="gray")
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 衰减率
            first_ic = decay_df[decay_df['lag'] == 1]['ic'].mean()
            last_ic = decay_df[decay_df['lag'] == 20]['ic'].mean()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Lag 1 IC", f"{first_ic:.4f}")
            with col2:
                st.metric("Lag 20 IC", f"{last_ic:.4f}")
            with col3:
                decay_rate = (first_ic - last_ic) / (abs(first_ic) + 1e-8)
                st.metric("衰减率", f"{decay_rate:.1%}")
            
            return
    
    # 如果没有衰减数据，显示提示
    st.info("暂无 IC 衰减数据。请确保评估时计算了衰减分析。")


def show_multi_factor_backtest(db):
    """多因子回测"""
    st.subheader("🚀 多因子组合回测")
    
    factors = db.list_factors()
    
    if factors.empty:
        st.warning("暂无因子数据")
        return
    
    factor_names = factors['name'].tolist()
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 选择因子
        selected = st.multiselect(
            "选择组合因子",
            factor_names,
            default=factor_names[:2] if len(factor_names) >= 2 else factor_names
        )
    
    with col2:
        # 回测参数
        start_date = st.date_input(
            "开始日期",
            value=pd.Timestamp.now() - pd.DateOffset(months=6)
        )
        end_date = st.date_input("结束日期")
    
    if len(selected) < 2:
        st.info("请至少选择2个因子")
        return
    
    # 权重设置
    st.markdown("#### 权重设置")
    
    weights = {}
    cols = st.columns(len(selected))
    
    for i, (factor, col) in enumerate(zip(selected, cols)):
        with col:
            weights[factor] = st.slider(
                f"{factor} 权重",
                0.0, 1.0, 1.0 / len(selected),
                key=f"backtest_{factor}"
            )
    
    # 归一化
    total = sum(weights.values())
    weights = {k: v / total for k, v in weights.items()}
    
    # 显示权重
    weight_df = pd.DataFrame({
        '因子': list(weights.keys()),
        '权重': list(weights.values())
    })
    
    fig = px.pie(
        weight_df,
        values='权重',
        names='因子',
        title="因子权重分布"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 运行回测按钮
    if st.button("▶️ 运行回测", use_container_width=True):
        with st.spinner("回测中..."):
            try:
                # 这里模拟回测结果
                # 实际应该调用回测引擎
                
                # 生成模拟回测结果
                dates = pd.date_range(start_date, end_date, freq='B')
                cumulative_returns = np.cumprod(
                    1 + np.random.randn(len(dates)) * 0.02
                ) - 1
                
                benchmark = np.cumprod(
                    1 + np.random.randn(len(dates)) * 0.01
                ) - 1
                
                # 绘制收益曲线
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=dates,
                    y=cumulative_returns,
                    mode='lines',
                    name='组合',
                    line=dict(color='steelblue')
                ))
                
                fig.add_trace(go.Scatter(
                    x=dates,
                    y=benchmark,
                    mode='lines',
                    name='基准',
                    line=dict(color='gray', dash='dash')
                ))
                
                fig.update_layout(
                    title="多因子组合回测",
                    xaxis_title="日期",
                    yaxis_title="累计收益",
                    height=500
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # 回测统计
                returns = pd.Series(cumulative_returns)
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("总收益", f"{cumulative_returns[-1]:.2%}")
                with col2:
                    st.metric("年化收益", f"{cumulative_returns[-1] * 252 / len(dates):.2%}")
                with col3:
                    st.metric("最大回撤", f"{returns.min():.2%}")
                with col4:
                    sharpe = returns.mean() / (returns.std() + 1e-8) * np.sqrt(252)
                    st.metric("夏普比率", f"{sharpe:.2f}")
                
                # 保存回测结果
                if st.button("💾 保存回测结果"):
                    db.save_backtest({
                        'factors': selected,
                        'weights': weights,
                        'start_date': str(start_date),
                        'end_date': str(end_date),
                        'total_return': cumulative_returns[-1],
                        'sharpe': sharpe,
                        'max_drawdown': returns.min()
                    })
                    st.success("回测结果已保存")
                
            except Exception as e:
                st.error(f"回测失败: {str(e)}")


def main():
    """页面主函数"""
    init_session_state()
    
    st.title("🔗 因子交互分析")
    
    # Tab 切换
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🔗 相关性矩阵",
        "🧮 因子组合器",
        "📊 IC 相关性",
        "📉 IC 衰减",
        "🚀 多因子回测"
    ])
    
    db = get_database()
    
    with tab1:
        show_factor_correlation_matrix(db)
    
    with tab2:
        show_factor_combiner(db)
    
    with tab3:
        show_ic_correlation_analysis(db)
    
    with tab4:
        show_factor_decay_analysis(db)
    
    with tab5:
        show_multi_factor_backtest(db)


if __name__ == "__main__":
    main()
