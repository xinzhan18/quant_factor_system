"""
Streamlit Dashboard 配置
"""

import streamlit as st
from pathlib import Path

# 页面配置
st.set_page_config(
    page_title="量化因子 Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 路径配置
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "storage" / "data"
DB_PATH = BASE_DIR / "storage" / "database" / "factors.db"

# 页面配置
PAGES = {
    "首页": "pages.home",
    "因子评估": "pages.factor_evaluation",
    "因子筛选": "pages.factor_screening",
    "因子交互": "pages.factor_interaction",
    "Pipeline编辑器": "pages.pipeline_editor",
    "选股": "pages.stock_selection",
    "历史回测": "pages.backtest_history",
}

# 因子类别
FACTOR_CATEGORIES = [
    "all",
    "momentum",
    "value",
    "quality",
    "volatility",
    "growth",
    "size",
    "liquidity",
]

# 评估阈值
DEFAULT_IC_THRESHOLD = 0.02
DEFAULT_WIN_RATE_THRESHOLD = 0.50


def init_session_state():
    """初始化会话状态"""
    if 'factor_list' not in st.session_state:
        st.session_state.factor_list = []
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = None


def get_database():
    """获取数据库连接"""
    from quant_factor_system.storage import FactorDatabase
    return FactorDatabase(str(DB_PATH))


def get_csv_storage():
    """获取 CSV 存储"""
    from quant_factor_system.storage import CSVStorage
    return CSVStorage(str(DATA_DIR))


# 样式
st.markdown("""
    <style>
    .main-header {
        font-size: 28px;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 20px;
    }
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 15px;
        margin: 5px;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
    }
    </style>
""", unsafe_allow_html=True)
