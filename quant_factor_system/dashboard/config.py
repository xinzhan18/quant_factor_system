"""
Dashboard 配置
"""

# 数据库配置
DATABASE_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "quant",
    "user": "postgres",
    "password": "postgres"
}

# 页面配置
PAGES = [
    {"name": "首页", "icon": "🏠", "path": "Home.py"},
    {"name": "数据浏览", "icon": "📊", "path": "pages/1_Data.py"},
    {"name": "因子评估", "icon": "📈", "path": "pages/2_Factors.py"},
    {"name": "Pipeline", "icon": "🔧", "path": "pages/3_Pipeline.py"},
]

# 默认参数
DEFAULTS = {
    "symbols": ["TEST_001", "TEST_002", "TEST_003"],
    "frequency": "daily",
    "start_date": "2024-01-01",
    "periods": 100,
}

# 图表配色
COLORS = {
    "primary": "#1f77b4",
    "secondary": "#ff7f0e",
    "success": "#2ca02c",
    "danger": "#d62728",
    "neutral": "#7f7f7f",
}
