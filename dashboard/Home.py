"""
首页 - 系统总览
展示数据库状态、因子概览、数据统计
"""

import streamlit as st
import pandas as pd
from datetime import datetime

from quant_factor_system import __version__
from quant_factor_system.data import TimescaleDB
from quant_factor_system.mining import FactorLibrary, MiningConfig


def get_db_stats(db: TimescaleDB) -> dict:
    """获取数据库统计信息"""
    stats = {
        'connected': False,
        'version': '',
        'tables': {},
        'total_size': 'N/A',
        'price_records': 0,
        'factor_tables': 0,
        'date_range': ('N/A', 'N/A'),
        'stock_count': 0,
    }
    
    try:
        with db.connection() as conn:
            cursor = conn.cursor()
            
            # 版本
            cursor.execute("SELECT version()")
            stats['version'] = cursor.fetchone()[0]
            
            # 所有表信息
            cursor.execute("""
                SELECT table_name, 
                       pg_size_pretty(pg_total_relation_size(table_name::text)) as size
                FROM information_schema.tables
                WHERE table_schema = 'public'
            """)
            for row in cursor.fetchall():
                stats['tables'][row[0]] = row[1]
            
            # 总大小
            cursor.execute("""
                SELECT SUM(pg_total_relation_size(table_name::text))
                FROM information_schema.tables
                WHERE table_schema = 'public'
            """)
            result = cursor.fetchone()
            total_bytes = result[0] if result and result[0] else 0
            stats['total_size'] = f"{total_bytes / 1024 / 1024 / 1024:.2f} GB"
            
            # price_daily 记录数
            cursor.execute("SELECT COUNT(*) FROM price_daily")
            stats['price_records'] = cursor.fetchone()[0]
            
            # 因子表数量
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name LIKE 'factor_%'
            """)
            stats['factor_tables'] = cursor.fetchone()[0]
            
            # 日期范围
            cursor.execute("SELECT MIN(time), MAX(time) FROM price_daily")
            dates = cursor.fetchone()
            if dates[0]:
                stats['date_range'] = (str(dates[0])[:10], str(dates[1])[:10])
            
            # 股票数量
            cursor.execute("SELECT COUNT(DISTINCT symbol) FROM price_daily")
            stats['stock_count'] = cursor.fetchone()[0]
            
            stats['connected'] = True
            
    except Exception as e:
        stats['error'] = str(e)
    
    return stats


def get_factor_stats() -> dict:
    """获取因子统计信息（从 mining library 读取）"""
    try:
        lib = FactorLibrary(MiningConfig())
        factors = lib.list_factors()
    except Exception:
        factors = []

    result = {
        'total': len(factors),
        'categories': {},
        'top_factors': []
    }

    for f in factors:
        cat = f.get('category', '其他')
        result['categories'][cat] = result['categories'].get(cat, 0) + 1
        ic = f.get('ic_mean')
        if ic is not None:
            result['top_factors'].append({
                'name': f.get('name', ''),
                'ic': ic,
                'type': f.get('category', '未知'),
            })

    result['top_factors'].sort(key=lambda x: abs(x.get('ic', 0)), reverse=True)
    result['top_factors'] = result['top_factors'][:5]

    return result


def main():
    """首页主函数"""
    st.set_page_config(
        page_title="QuantFactor Dashboard",
        page_icon="📊",
        layout="wide"
    )
    
    # 标题
    st.title("📊 QuantFactor System Dashboard")
    st.markdown(f"**版本:** {__version__} | **{datetime.now().strftime('%Y-%m-%d %H:%M')}**")
    
    # 初始化数据库和因子
    db = TimescaleDB()
    db_stats = get_db_stats(db)
    factor_stats = get_factor_stats()
    
    # ==================== 第一行：数据库状态 ====================
    st.header("🗄️ 数据库状态")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if db_stats.get('connected'):
            st.success("✅ PostgreSQL 已连接")
            st.caption(f"{db_stats.get('version', 'N/A')[:50]}")
        else:
            st.error("❌ 数据库未连接")
            st.caption(db_stats.get('error', '未知错误'))
    
    with col2:
        st.metric("📈 数据记录", f"{db_stats.get('price_records', 0):,}")
        st.caption("price_daily 表")
    
    with col3:
        st.metric("📊 因子表", f"{db_stats.get('factor_tables', 0)}")
        st.caption("独立因子存储")
    
    with col4:
        st.metric("💾 总容量", db_stats.get('total_size', 'N/A'))
    
    st.divider()
    
    # ==================== 第二行：数据概览 ====================
    st.header("📈 数据概览")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📅 数据范围", f"{db_stats.get('date_range', ('N/A', 'N/A'))[0]}")
        st.caption(f"至 {db_stats.get('date_range', ('N/A', 'N/A'))[1]}")
    
    with col2:
        st.metric("📗 股票数量", f"{db_stats.get('stock_count', 0):,}")
        st.caption("已覆盖股票")
    
    with col3:
        st.metric("🧮 因子数量", f"{factor_stats.get('total', 0)}")
        st.caption("已注册因子")
    
    with col4:
        st.metric("📐 表数量", f"{len(db_stats.get('tables', {}))}")
        st.caption("数据库表")
    
    # ==================== 第三行：因子表现 ====================
    st.header("🎯 因子表现 (2022 训练集)")
    
    # 显示表
    st.subheader("表信息")
    if db_stats.get('tables'):
        table_df = pd.DataFrame([
            {'表名': k, '大小': v} 
            for k, v in db_stats.get('tables', {}).items()
        ])
        st.dataframe(table_df, use_container_width=True, hide_index=True)
    
    # 显示Top因子
    st.subheader("Top 5 因子 (按IC绝对值)")
    
    if factor_stats.get('top_factors'):
        top_df = pd.DataFrame(factor_stats['top_factors'])
        top_df['IC'] = top_df['ic'].apply(lambda x: f"{x:.4f}")
        top_df = top_df[['name', 'IC', 'type']]
        top_df.columns = ['因子名称', 'IC', '类型']
        st.dataframe(top_df, use_container_width=True, hide_index=True)
    
    st.info("💡 **负IC** = 反转效应 (短期下跌后反弹) | **正IC** = 动量效应 (强者恒强)")
    
    st.divider()
    
    # ==================== 侧边栏：导航 ====================
    with st.sidebar:
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
        
        st.divider()
        
        st.header("ℹ️ 系统信息")
        st.info("""
        **QuantFactor System**
        
        - 数据源: RiceQuant (米筐)
        - 存储: TimescaleDB
        - 训练集: 2022年
        - 测试集: 2023+
        """)


if __name__ == "__main__":
    main()
