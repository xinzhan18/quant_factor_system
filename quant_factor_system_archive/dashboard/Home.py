"""
量化因子 Dashboard
主入口文件

运行方式:
    cd quant_factor_system/dashboard
    streamlit run Home.py
"""

import streamlit as st
import os
from pathlib import Path

# 添加项目路径
import sys
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import st, PAGES

# 页面标题
st.set_page_config(
    page_title="量化因子 Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 侧边栏
st.sidebar.title("📊 导航")
st.sidebar.divider()

# 页面选择
page = st.sidebar.selectbox(
    "选择页面",
    list(PAGES.keys())
)

# 加载页面
page_file = PAGES[page]
if page_file:
    # 动态导入页面
    import importlib
    module_path = f"pages.{page_file.split('.')[-1]}"
    try:
        page_module = importlib.import_module(module_path)
        page_module.main()
    except Exception as e:
        st.error(f"加载页面失败: {e}")
        st.info("请检查页面文件是否存在")

# 侧边栏信息
st.sidebar.divider()
st.sidebar.markdown("### ℹ️ 关于")
st.sidebar.info(
    "量化因子 Dashboard\n\n"
    "用于因子评估、筛选、交互分析和选股\n\n"
    "版本: 2.0"
)

# 功能说明
st.sidebar.markdown("""
### 📌 功能说明

| 页面 | 功能 |
|------|------|
| 首页 | 系统概览 |
| 因子评估 | 单因子性能分析 |
| 因子筛选 | 因子池管理 |
| 因子交互 | 相关性/组合分析 |
| Pipeline编辑器 | 创建因子管道 |
| 选股 | 股票筛选 |
| 历史回测 | 回测记录 |
""")

# 刷新按钮
if st.sidebar.button("🔄 刷新数据"):
    st.rerun()
