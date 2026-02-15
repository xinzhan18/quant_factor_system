"""
因子评估页面
"""

import streamlit as st
import pandas as pd
import numpy as np
import sys
import os

# 包已通过 pip 安装到 conda 环境中

from quant_factor_system.data import (
    DataManager,
    PostgresDB,
    get_postgres_db,
)
from quant_factor_system.pipeline import Pipeline
from quant_factor_system.factors import list_factors, register_all_builtins


def main():
    st.set_page_config(
        page_title="因子评估 - QuantFactor",
        page_icon="📈",
        layout="wide"
    )
    
    st.title("📈 因子评估")
    
    # 侧边栏
    with st.sidebar:
        st.header("因子设置")
        
        # 确保因子已注册
        register_all_builtins()
        factors = list_factors()
        
        # 因子选择 (从注册表)
        factor_names = [f['name'] for f in factors]
        if not factor_names:
            factor_names = ['momentum', 'ma', 'rsi', 'return_1d', 'return_20d']
        
        selected_factor = st.selectbox(
            "选择因子",
            options=factor_names,
            index=0 if 'momentum' in factor_names else 0
        )
        
        # 获取因子信息
        factor_info = next((f for f in factors if f['name'] == selected_factor), None)
        
        if factor_info:
            st.caption(f"类型: {factor_info.get('category', 'custom')}")
            st.caption(f"类: {factor_info['class_name']}")
        
        # 参数设置
        period = st.slider("回看期/周期", 5, 60, 20)
        
        symbols = st.text_input(
            "股票代码",
            value="TEST_001"
        ).split(",")
        symbols = [s.strip() for s in symbols if s.strip()]
        
        n_periods = st.slider("数据周期", 50, 500, 200)
        
        # 数据库选项
        st.divider()
        st.header("💾 存储设置")
        save_to_db = st.checkbox("保存结果到数据库", value=True)
        
        st.divider()
        
        if st.button("🔄 重新计算"):
            st.rerun()
    
    # 主内容
    try:
        # 获取数据
        dm = DataManager(use_db=False)
        data = dm.get_price_data(
            symbols=symbols,
            frequency="daily",
            n_periods=n_periods
        )
        
        if data.empty:
            st.warning("无数据")
            return
        
        # 创建 Pipeline
        pipe = Pipeline("Factor Evaluation")
        
        # 添加因子
        pipe.add_factor(selected_factor, selected_factor, period=period)
        
        # 计算
        result = pipe.run(data)
        
        if result is None or result.empty:
            st.warning("因子计算无结果")
            return
        
        st.success(f"✅ 因子计算完成 | {len(result)} 行数据")
        
        # 保存到数据库
        if save_to_db:
            try:
                db = get_postgres_db()
                
                # 计算 IC
                close = result['close']
                returns = close.pct_change().dropna()
                factor_col = [c for c in result.columns if c not in ['symbol', 'timestamp', 'close', 'volume']]
                if factor_col:
                    factor_values = result[factor_col[0]].dropna()
                    common_idx = returns.index.intersection(factor_values.index)
                    ic = returns.loc[common_idx].corr(factor_values.loc[common_idx])
                    
                    # 保存结果
                    db.save_factor_results(result, selected_factor, ic=ic)
                    st.success(f"✅ 已保存到数据库 (IC={ic:.4f})")
            except Exception as e:
                st.warning(f"保存失败: {e}")
        
        # 显示因子值
        st.subheader("📊 因子值")
        
        factor_col = [c for c in result.columns if c not in ['symbol', 'timestamp', 'close', 'volume']]
        
        if factor_col:
            st.dataframe(
                result[['symbol', 'timestamp'] + factor_col].head(20),
                use_container_width=True
            )
        
        # 因子分析
        st.subheader("📈 因子分析")
        
        if 'close' in result.columns and factor_col:
            close = result['close']
            returns = close.pct_change().dropna()
            factor_values = result[factor_col[0]].dropna()
            
            # 对齐数据
            common_idx = returns.index.intersection(factor_values.index)
            returns_aligned = returns.loc[common_idx]
            factor_aligned = factor_values.loc[common_idx]
            
            if len(returns_aligned) > 10:
                ic = returns_aligned.corr(factor_aligned)
                
                # 计算分组收益
                result_valid = result.dropna(subset=[factor_col[0]]).copy()
                try:
                    result_valid['quantile'] = pd.qcut(result_valid[factor_col[0]], q=5, labels=False, duplicates='drop')
                    group_returns = result_valid.groupby('quantile')['close'].apply(
                        lambda x: (x.iloc[-1] / x.iloc[0] - 1) if len(x) > 1 else 0
                    )
                except:
                    group_returns = pd.Series()
                
                # 显示指标
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("IC (信息系数)", f"{ic:.4f}")
                with col2:
                    st.metric("IC > 0.02", "✅" if abs(ic) > 0.02 else "❌")
                with col3:
                    if not group_returns.empty:
                        top_group_return = group_returns.max()
                        st.metric("最佳组收益", f"{top_group_return * 100:.2f}%")
                
                # IC 序列图
                st.write("### IC 序列")
                
                window = 20
                rolling_ic = []
                for i in range(window, len(returns_aligned)):
                    r = returns_aligned.iloc[i-window:i]
                    f = factor_aligned.iloc[i-window:i]
                    if len(r) > 0 and r.std() > 0:
                        rolling_ic.append(r.corr(f))
                    else:
                        rolling_ic.append(0)
                
                ic_df = pd.DataFrame({
                    'timestamp': returns_aligned.index[window:],
                    'rolling_ic': rolling_ic
                })
                
                st.line_chart(
                    ic_df.set_index('timestamp')['rolling_ic'],
                    color="#1f77b4"
                )
                
                # 分组收益柱状图
                if not group_returns.empty:
                    st.write("### 分组收益")
                    st.bar_chart(group_returns, color="#2ca02c")
                
                # 因子值分布
                st.write("### 因子值分布")
                st.histogram(factor_aligned, bins=30)
        
        # 原始数据
        with st.expander("📋 查看完整数据"):
            st.dataframe(result, use_container_width=True)
    
    except Exception as e:
        st.error(f"错误: {e}")
        st.exception(e)


if __name__ == "__main__":
    main()
