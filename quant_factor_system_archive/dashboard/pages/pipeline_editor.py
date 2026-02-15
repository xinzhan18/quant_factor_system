"""
Pipeline 编辑器页面
交互式创建和测试因子 Pipeline
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from config import st, pd, np, init_session_state, get_csv_storage


def show_pipeline_builder():
    """Pipeline 构建器"""
    st.subheader("🧱 Pipeline 构建器")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("#### 1. 添加因子")
        
        # 可用因子
        available_factors = [
            ("Momentum", "动量因子"),
            ("RSI", "相对强弱"),
            ("MovingAverage", "移动平均"),
            ("Volatility", "波动率"),
            ("Returns", "收益率"),
        ]
        
        factor_type = st.selectbox(
            "选择因子类型",
            [f[0] for f in available_factors]
        )
        
        factor_name = st.text_input(
            "因子名称",
            value=factor_type.lower()
        )
        
        # 参数设置
        params = {}
        
        if factor_type in ["Momentum", "Returns"]:
            params['window'] = st.slider(
                "窗口长度",
                min_value=5,
                max_value=250,
                value=20
            )
        
        elif factor_type == "RSI":
            params['window'] = st.slider(
                "RSI 周期",
                min_value=2,
                max_value=50,
                value=14
            )
        
        elif factor_type == "MovingAverage":
            params['window'] = st.slider(
                "MA 周期",
                min_value=5,
                max_value=200,
                value=20
            )
            params['etype'] = st.selectbox(
                "MA 类型",
                ['simple', 'exponential']
            )
        
        elif factor_type == "Volatility":
            params['window'] = st.slider(
                "周期",
                min_value=5,
                max_value=250,
                value=20
            )
        
        # 添加按钮
        if st.button("➕ 添加到 Pipeline", use_container_width=True):
            if 'pipeline_factors' not in st.session_state:
                st.session_state.pipeline_factors = []
            
            st.session_state.pipeline_factors.append({
                'name': factor_name,
                'type': factor_type,
                'params': params
            })
            
            st.success(f"已添加 {factor_name}")
    
    with col2:
        st.markdown("#### 2. 当前 Pipeline")
        
        if 'pipeline_factors' not in st.session_state or not st.session_state.pipeline_factors:
            st.info("Pipeline 为空，请添加因子")
        else:
            # 显示 Pipeline
            pipeline_data = []
            
            for i, factor in enumerate(st.session_state.pipeline_factors):
                pipeline_data.append({
                    '序号': i + 1,
                    '因子名称': factor['name'],
                    '因子类型': factor['type'],
                    '参数': str(factor['params'])
                })
            
            df = pd.DataFrame(pipeline_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # 删除按钮
            if st.button("🗑️ 清空 Pipeline"):
                st.session_state.pipeline_factors = []
                st.rerun()


def show_pipeline_test():
    """Pipeline 测试"""
    st.subheader("🧪 Pipeline 测试")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 测试参数
        test_symbols = st.multiselect(
            "选择测试股票",
            ['SH600000', 'SZ000001', 'SH600519', 'SH600036', 'SZ000002'],
            default=['SH600000', 'SZ000001']
        )
    
    with col2:
        date_range = st.date_input(
            "日期范围",
            value=(
                pd.Timestamp.now() - pd.DateOffset(months=3),
                pd.Timestamp.now()
            )
        )
    
    if not test_symbols:
        st.info("请选择测试股票")
        return
    
    # 测试按钮
    if st.button("▶️ 运行测试", use_container_width=True):
        with st.spinner("测试中..."):
            try:
                # 模拟测试结果
                from quant_factor_system.pipeline import (
                    Pipeline, Momentum, RSI, MovingAverage, Volatility
                )
                
                # 创建 Pipeline
                pipe = Pipeline("TestPipeline")
                
                for factor in st.session_state.get('pipeline_factors', []):
                    if factor['type'] == 'Momentum':
                        pipe.add_factor(factor['name'], 
                                      Momentum(window=factor['params'].get('window', 20)))
                    elif factor['type'] == 'RSI':
                        pipe.add_factor(factor['name'], 
                                      RSI(window=factor['params'].get('window', 14)))
                    elif factor['type'] == 'MovingAverage':
                        pipe.add_factor(factor['name'], 
                                      MovingAverage(window=factor['params'].get('window', 20)))
                    elif factor['type'] == 'Volatility':
                        pipe.add_factor(factor['name'], 
                                      Volatility(window=factor['params'].get('window', 20)))
                
                # 生成模拟数据
                dates = pd.date_range(date_range[0], date_range[1], freq='B')
                
                result_data = {}
                
                for symbol in test_symbols:
                    result_data[symbol] = {}
                    
                    for factor in st.session_state.get('pipeline_factors', []):
                        # 模拟因子值
                        np.random.seed(hash(factor['name'] + symbol) % 2**32)
                        
                        if factor['type'] == 'Momentum':
                            values = np.random.randn(len(dates)) * 0.1
                        elif factor['type'] == 'RSI':
                            values = np.random.uniform(30, 70, len(dates))
                        elif factor['type'] == 'MovingAverage':
                            values = np.random.uniform(10, 100, len(dates))
                        elif factor['type'] == 'Volatility':
                            values = np.random.uniform(0.1, 0.5, len(dates))
                        else:
                            values = np.random.randn(len(dates)) * 0.05
                        
                        result_data[symbol][factor['name']] = values
                
                # 创建结果 DataFrame
                result_dfs = []
                
                for symbol, data in result_data.items():
                    df = pd.DataFrame(data, index=dates)
                    df['symbol'] = symbol
                    result_dfs.append(df)
                
                result = pd.concat(result_dfs).reset_index()
                result = result.rename(columns={'index': 'date'})
                
                # 显示结果
                st.markdown("#### 测试结果")
                
                # 选择显示
                factor_cols = [f['name'] for f in st.session_state.get('pipeline_factors', [])]
                
                if factor_cols:
                    selected_factor = st.selectbox("选择因子查看", factor_cols)
                    
                    # 绘制时序图
                    fig = px.line(
                        result,
                        x='date',
                        y=selected_factor,
                        color='symbol',
                        title=f"{selected_factor} 时序图"
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # 显示数据
                    with st.expander("查看原始数据"):
                        st.dataframe(
                            result[['date', 'symbol'] + factor_cols],
                            use_container_width=True
                        )
                
                # 统计信息
                st.markdown("#### 统计信息")
                
                stats = result[factor_cols].describe()
                st.dataframe(stats)
                
                # 保存 Pipeline
                if st.button("💾 保存 Pipeline"):
                    st.session_state.saved_pipelines = st.session_state.get('saved_pipelines', [])
                    st.session_state.saved_pipelines.append({
                        'name': f"Pipeline_{len(st.session_state.saved_pipelines) + 1}",
                        'factors': st.session_state.pipeline_factors.copy(),
                        'test_date': pd.Timestamp.now().strftime('%Y-%m-%d')
                    })
                    st.success("Pipeline 已保存")
                
            except Exception as e:
                st.error(f"测试失败: {str(e)}")


def show_saved_pipelines():
    """已保存的 Pipeline"""
    st.subheader("💾 已保存的 Pipeline")
    
    if 'saved_pipelines' not in st.session_state or not st.session_state.saved_pipelines:
        st.info("暂无保存的 Pipeline")
        return
    
    for i, pipe in enumerate(st.session_state.saved_pipelines):
        with st.expander(f"{pipe['name']} ({pipe['test_date']})"):
            st.write(f"包含 {len(pipe['factors'])} 个因子")
            
            for factor in pipe['factors']:
                st.write(f"- {factor['name']} ({factor['type']})")
            
            # 加载按钮
            if st.button("📥 加载", key=f"load_{i}"):
                st.session_state.pipeline_factors = pipe['factors'].copy()
                st.success("已加载到 Pipeline 编辑器")
                st.rerun()
            
            # 删除按钮
            if st.button("🗑️ 删除", key=f"delete_{i}"):
                st.session_state.saved_pipelines.pop(i)
                st.rerun()


def show_factor_library():
    """因子库"""
    st.subheader("📚 因子库")
    
    # 展开/收起
    with st.expander("查看内置因子"):
        st.markdown("""
        ### 基础因子
        
        | 因子 | 说明 | 参数 |
        |------|------|------|
        | Momentum | 动量因子 | window: 窗口长度 |
        | RSI | 相对强弱指标 | window: RSI 周期 |
        | MovingAverage | 移动平均 | window: 周期, etype: 类型 |
        | Volatility | 波动率 | window: 周期 |
        | Returns | 收益率 | period: 周期 |
        
        ### 变换因子
        
        | 变换 | 说明 |
        |------|------|
        | .rolling(window) | 滚动窗口 |
        | .rank() | 排名 |
        | .zscore() | Z-Score 标准化 |
        | .clip(lower, upper) | 裁剪 |
        
        ### 过滤器
        
        | 过滤器 | 说明 |
        |------|------|
        | PercentileFilter | 百分位过滤 |
        | FactorFilter | 因子值过滤 |
        """)


def main():
    """页面主函数"""
    init_session_state()
    
    st.title("🔧 Pipeline 编辑器")
    
    st.info("""
    使用此页面交互式创建和测试因子 Pipeline。
    1. 在左侧添加因子到 Pipeline
    2. 设置测试参数
    3. 运行测试查看结果
    4. 保存 Pipeline 供后续使用
    """)
    
    # 主界面
    col1, col2 = st.columns([1, 2])
    
    with col1:
        show_pipeline_builder()
    
    with col2:
        show_pipeline_test()
    
    # 已保存的 Pipeline
    show_saved_pipelines()
    
    # 因子库
    show_factor_library()


if __name__ == "__main__":
    main()
