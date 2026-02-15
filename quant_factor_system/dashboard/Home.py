"""
首页 - 系统总览
"""

import streamlit as st
import pandas as pd
import sys
import os

# 包已通过 pip 安装到 conda 环境中，无需手动添加路径

from quant_factor_system import __version__
from quant_factor_system.data import (
    DataManager,
    PostgresDB,
    get_postgres_db,
    init_postgres_db,
)
from quant_factor_system.factors import (
    register_all_builtins,
    list_factors,
    register_factor,
)


def main():
    """首页主函数"""
    st.set_page_config(
        page_title="QuantFactor Dashboard",
        page_icon="📊",
        layout="wide"
    )
    
    # 标题
    st.title("📊 QuantFactor System Dashboard")
    st.markdown(f"**版本:** {__version__}")
    
    # 侧边栏 - 数据库设置
    with st.sidebar:
        st.header("⚙️ 数据库设置")
        
        # 检查数据库连接
        db = get_postgres_db()
        db_status = db.check()
        
        if db_status['connected']:
            st.success("✅ PostgreSQL 已连接")
            st.caption(f"{db_status['version'][:40]}...")
            
            # 显示统计
            stats = db.get_stats()
            st.metric("因子结果", stats['factor_results'])
            st.metric("因子元信息", stats['factor_meta'])
        else:
            st.error("❌ 数据库未连接")
            st.caption(db_status.get('message', '未知错误'))
        
        st.divider()
        
        # 初始化数据库按钮
        if st.button("🔄 初始化数据库表"):
            try:
                db.init()
                register_all_builtins()
                st.success("✅ 数据库初始化完成")
                st.rerun()
            except Exception as e:
                st.error(f"初始化失败: {e}")
        
        st.divider()
        
        # 因子统计
        st.header("📈 因子统计")
        
        # 初始化因子注册表
        register_all_builtins()
        factors = list_factors()
        
        st.metric("已注册因子", len(factors))
        
        # 显示因子列表
        if factors:
            st.write("**已注册因子:**")
            for f in factors[:5]:
                st.markdown(f"- {f['name']} ({f.get('category', 'custom')})")
            if len(factors) > 5:
                st.caption(f"... 共 {len(factors)} 个因子")
        
        st.divider()
        
        st.header("📁 导航")
        
        pages = [
            ("🏠 首页", "Home.py"),
            ("📊 数据浏览", "pages/Data.py"),
            ("📈 因子评估", "pages/Factors.py"),
            ("🔧 Pipeline", "pages/Pipeline.py"),
            ("⚙️ 策略配置", "pages/StrategyConfig.py"),
            ("📈 回测结果", "pages/BacktestResult.py"),
            ("📋 任务监控", "pages/TaskMonitor.py"),
        ]
        
        for name, page in pages:
            if st.button(name):
                st.switch_page(page)
    
    # 主内容区
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📈 快速演示")
        
        # 获取演示数据
        dm = DataManager(use_db=False)  # 使用模拟数据生成演示
        
        data = dm.get_price_data(
            symbols=["TEST_001"],
            frequency="daily",
            n_periods=100
        )
        
        if not data.empty:
            st.success(f"✅ 生成 {len(data)} 行演示数据")
            
            # 展示数据
            st.dataframe(
                data.head(10),
                use_container_width=True
            )
            
            # 统计
            returns = data['close'].pct_change().dropna()
            stats = {
                "总收益率": f"{(data['close'].iloc[-1] / data['close'].iloc[0] - 1) * 100:.2f}%",
                "波动率": f"{returns.std() * 100:.2f}%",
                "夏普比率": f"{returns.mean() / returns.std() if returns.std() > 0 else 0:.2f}",
                "最大回撤": f"{((data['close'] - data['close'].cummax()) / data['close'].cummax()).min() * 100:.2f}%"
            }
            
            st.write("### 统计指标")
            for k, v in stats.items():
                st.metric(k, v)
    
    with col2:
        st.subheader("🎯 快速操作")
        
        # 创建新因子
        with st.expander("➕ 创建新因子", expanded=False):
            new_factor_name = st.text_input("因子名称", key="new_factor_name")
            new_factor_class = st.selectbox(
                "基类",
                ["MomentumFactor", "MovingAverage", "RSI", "Return1dFactor", "DistMA10Factor"]
            )
            new_factor_period = st.number_input("周期参数", value=20, step=5)
            new_factor_desc = st.text_area("描述", "")
            
            if st.button("✅ 注册因子"):
                if new_factor_name:
                    register_factor(
                        name=new_factor_name,
                        class_name=new_factor_class,
                        category="custom",
                        params={"period": new_factor_period, "window": new_factor_period},
                        description=new_factor_desc
                    )
                    st.success(f"✅ 已注册因子: {new_factor_name}")
                    st.rerun()
                else:
                    st.error("请输入因子名称")
        
        st.divider()
        
        st.subheader("ℹ️ 系统信息")
        st.info("""
        **QuantFactor System v3.0**
        
        - 数据库: PostgreSQL 16
        - 存储: 数据库 + 模拟数据
        - 前端: Streamlit
        
        **数据流程:**
        1. 获取价格数据
        2. 计算因子值
        3. 存储到数据库
        4. Dashboard 展示
        """)


if __name__ == "__main__":
    main()
