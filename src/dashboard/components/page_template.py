"""
Dashboard 页面模板
提供页面通用配置和组件
"""

import streamlit as st


def set_page_config(
    title: str = "QuantFactor",
    page_icon: str = "📊",
    layout: str = "wide"
):
    """
    设置页面配置
    
    Args:
        title: 页面标题
        page_icon: 页面图标
        layout: 布局 ('wide' or 'centered')
    """
    st.set_page_config(
        page_title=f"{title} - QuantFactor",
        page_icon=page_icon,
        layout=layout
    )


def render_title(title: str, description: str = ""):
    """
    渲染页面标题
    
    Args:
        title: 标题
        description: 描述
    """
    st.title(title)
    if description:
        st.markdown(description)


def render_sidebar_nav(pages: list, current_page: str):
    """
    渲染侧边栏导航
    
    Args:
        pages: [(显示名, 文件名), ...]
        current_page: 当前页面文件名
    """
    with st.sidebar:
        st.header("📁 导航")
        
        for name, page in pages:
            if st.button(name, use_container_width=True):
                st.switch_page(page)
        
        st.divider()


def render_db_status(db):
    """
    渲染数据库状态
    
    Args:
        db: TimescaleDB 实例
    """
    col1, col2 = st.columns(2)
    
    with col1:
        connected = False
        if hasattr(db, 'connection_status'):
            connected = db.connection_status.get('connected', False)
        elif hasattr(db, '_pool') and db._pool is not None:
            connected = True

        if connected:
            st.success("✅ 数据库已连接")
        else:
            st.error("❌ 数据库未连接")


def render_factor_selector(key: str = "factor"):
    """
    渲染因子选择器（从 mining library 读取）
    """
    try:
        from mining import FactorLibrary, MiningConfig
        lib = FactorLibrary(MiningConfig())
        factors = lib.list_factors()
        factor_names = [f['name'] for f in factors] if factors else []
    except Exception:
        factor_names = []

    return st.selectbox("选择因子", factor_names, key=key)


def render_date_range(key: str = "date_range"):
    """
    渲染日期范围选择器
    
    Args:
        key: 组件 key
    """
    return st.date_input("日期范围", key=key)


# ==================== 导出 ====================

__all__ = [
    'set_page_config',
    'render_title',
    'render_sidebar_nav',
    'render_db_status',
    'render_factor_selector',
    'render_date_range',
]
