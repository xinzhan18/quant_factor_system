"""
Pipeline 页面
"""

import streamlit as st
import pandas as pd
import sys
import os

# 包已通过 pip 安装到 conda 环境中

from quant_factor_system.data import (
    DataManager,
    TimescaleDB,
)
from quant_factor_system.factors import Pipeline, list_factors, register_all_builtins


def main():
    st.set_page_config(
        page_title="Pipeline - QuantFactor",
        page_icon="🔧",
        layout="wide"
    )
    
    st.title("🔧 Pipeline")
    
    st.markdown("""
    **Pipeline** 是量化因子的处理管道，支持：
    - 多因子组合计算
    - 因子评估与筛选
    - 批量回测分析
    - 结果存储到数据库
    """)
    
    # 侧边栏 - 设置
    with st.sidebar:
        st.header("Pipeline 设置")
        
        # 确保因子已注册
        register_all_builtins()
        factors = list_factors()
        factor_names = [f['name'] for f in factors] if factors else []
        
        symbols = st.text_input(
            "股票代码",
            value="TEST_001"
        ).split(",")
        symbols = [s.strip() for s in symbols if s.strip()]
        
        frequency = st.selectbox(
            "数据频率",
            options=["daily", "1min", "5min", "15min", "1hour"],
            index=0
        )
        
        n_periods = st.slider("数据周期", 50, 500, 200)
        
        # 数据库选项
        st.divider()
        st.header("💾 存储设置")
        save_to_db = st.checkbox("保存结果到数据库", value=True)
        
        st.divider()
        
        run_button = st.button(
            "▶️ 运行 Pipeline",
            type="primary",
            use_container_width=True
        )
    
    # 主内容
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("📦 因子配置")
        
        # 选择因子
        factor1_type = st.selectbox(
            "因子1",
            options=factor_names,
            index=0 if 'momentum' in factor_names else 0
        )
        
        factor1_period = st.slider(
            f"{factor1_type} 周期",
            5, 60, 20, key="f1"
        )
        
        st.divider()
        
        factor2_type = st.selectbox(
            "因子2 (可选)",
            options=["none"] + factor_names,
            index=0
        )
        
        if factor2_type != "none":
            factor2_period = st.slider(
                f"{factor2_type} 周期",
                5, 60, 20, key="f2"
            )
        
        st.divider()
        
        factor3_type = st.selectbox(
            "因子3 (可选)",
            options=["none"] + factor_names,
            index=0
        )
        
        if factor3_type != "none":
            factor3_period = st.slider(
                f"{factor3_type} 周期",
                5, 60, 20, key="f3"
            )
        
        st.divider()
        
    with col2:
        if run_button:
            with st.spinner("运行中..."):
                try:
                    # 获取数据
                    dm = DataManager(use_db=False)
                    data = dm.get_price_data(
                        symbols=symbols,
                        frequency=frequency,
                        n_periods=n_periods
                    )
                    
                    if data.empty:
                        st.warning("无数据")
                        return
                    
                    # 创建 Pipeline
                    pipe = Pipeline("MyPipeline")
                    
                    # 添加因子
                    factors_added = []
                    
                    pipe.add_factor(factor1_type, factor1_type, period=factor1_period)
                    factors_added.append(factor1_type)
                    
                    if factor2_type != "none":
                        pipe.add_factor(factor2_type, factor2_type, period=factor2_period)
                        factors_added.append(factor2_type)
                    
                    if factor3_type != "none":
                        pipe.add_factor(factor3_type, factor3_type, period=factor3_period)
                        factors_added.append(factor3_type)
                    
                    # 运行
                    result = pipe.run(data)
                    
                    if result is None or result.data.empty:
                        st.error("Pipeline 运行无结果")
                        return
                    
                    st.success(f"✅ Pipeline 完成 | {len(result.data)} 行 | 因子: {', '.join(factors_added)}")
                    
                    # 保存到数据库
                    if save_to_db:
                        try:
                            db = TimescaleDB()
                            result_df = result.data
                            
                            # 计算组合 IC
                            close = result_df['close']
                            returns = close.pct_change().dropna()
                            
                            for fc in factors_added:
                                if fc in result_df.columns:
                                    fv = result_df[fc].dropna()
                                    common_idx = returns.index.intersection(fv.index)
                                    if len(common_idx) > 10:
                                        ic = returns.loc[common_idx].corr(fv.loc[common_idx])
                                        db.save_factor_results(result_df, fc, ic=ic)
                            
                            st.success("✅ 结果已保存到数据库")
                        except Exception as e:
                            st.warning(f"保存失败: {e}")
                    
                    # 结果展示
                    st.subheader("📊 计算结果")
                    
                    result_df = result.data
                    
                    # 因子值表格
                    factor_cols = [c for c in result_df.columns if c not in ['symbol', 'timestamp', 'close', 'volume']]
                    
                    if factor_cols:
                        st.write("#### 因子值")
                        st.dataframe(
                            result_df[['symbol', 'timestamp'] + factor_cols].head(15),
                            use_container_width=True
                        )
                    
                    # 收益分析
                    if 'close' in result_df.columns:
                        st.write("#### 收益分析")
                        
                        close = result_df['close']
                        returns = close.pct_change().dropna()
                        
                        # 指标
                        total_return = (close.iloc[-1] / close.iloc[0] - 1)
                        volatility = returns.std()
                        sharpe = returns.mean() / volatility if volatility > 0 else 0
                        max_dd = ((close - close.cummax()) / close.cummax()).min()
                        
                        col_a, col_b, col_c, col_d = st.columns(4)
                        
                        def fmt_percent(v):
                            if pd.isna(v):
                                return "N/A"
                            return f"{v * 100:.2f}%"
                        
                        with col_a:
                            st.metric("总收益", fmt_percent(total_return))
                        with col_b:
                            st.metric("波动率", fmt_percent(volatility))
                        with col_c:
                            st.metric("夏普比率", f"{sharpe:.2f}")
                        with col_d:
                            st.metric("最大回撤", fmt_percent(max_dd))
                        
                        # 累计收益曲线
                        st.write("#### 累计收益曲线")
                        
                        cum_return = (1 + returns).cumprod() - 1
                        
                        st.line_chart(cum_return)
                    
                    # 下载结果
                    st.write("#### 导出数据")
                    
                    csv = result_df.to_csv(index=False).encode('utf-8')
                    
                    st.download_button(
                        "📥 下载结果 CSV",
                        data=csv,
                        file_name="pipeline_result.csv",
                        mime="text/csv"
                    )
                
                except Exception as e:
                    st.error(f"错误: {e}")
                    st.exception(e)
        else:
            st.info("👈 在左侧配置因子，点击运行")


if __name__ == "__main__":
    main()
