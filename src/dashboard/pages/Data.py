"""
数据浏览页面
从TimescaleDB查询真实数据
"""

import streamlit as st
from datetime import datetime, timedelta

from data import TimescaleDB


def main():
    """数据浏览主函数"""
    st.set_page_config(
        page_title="数据浏览 - QuantFactor",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 数据浏览")
    
    # 侧边栏 - 查询设置
    with st.sidebar:
        st.header("📁 数据查询")
        
        # 股票代码
        symbols_input = st.text_area(
            "股票代码 (逗号分隔)",
            value="SH600000,SH600519"
        )
        symbols = [s.strip() for s in symbols_input.split(',') if s.strip()]
        
        # 日期范围
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "开始日期",
                value=datetime.now() - timedelta(days=30)
            )
        with col2:
            end_date = st.date_input(
                "结束日期",
                value=datetime.now()
            )
        
        # 限制
        limit = st.slider("最大行数", 100, 50000, 5000)
        
        st.divider()
        
        if st.button("🔄 查询数据", use_container_width=True):
            st.rerun()
    
    # 主内容
    try:
        db = TimescaleDB()
        
        # 查询数据
        data = db.query_daily(
            symbols=symbols,
            start_date=str(start_date),
            end_date=str(end_date)
        )
        
        if data.empty:
            st.warning("无数据，请调整查询条件")
            
            # 显示数据库中的示例数据
            st.info("数据库中的表:")
            with db.connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT table_name, 
                           pg_size_pretty(pg_total_relation_size(table_name::text)) as size,
                           (SELECT COUNT(*) FROM information_schema.tables t2 
                            WHERE t2.table_name = t1.table_name 
                            AND EXISTS (SELECT 1 FROM information_schema.columns 
                                       WHERE table_name = t1.table_name 
                                       AND column_name = 'symbol'))
                    FROM information_schema.tables t1
                    WHERE table_schema = 'public'
                    AND table_name LIKE 'price_%'
                """)
                tables = cursor.fetchall()
                for t in tables:
                    st.write(f"- {t[0]}: {t[1]}")
            return
        
        # 限制行数
        if len(data) > limit:
            data = data.head(limit)
            st.warning(f"数据已限制为 {limit} 行")
        
        st.success(f"✅ 查询 {len(symbols)} 只股票, 共 {len(data)} 行数据")
        
        # 统计信息
        if 'close' in data.columns and not data.empty:
            returns = data['close'].pct_change().dropna()
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_return = (data['close'].iloc[-1] / data['close'].iloc[0] - 1) if len(data) > 1 else 0
                st.metric("总收益率", f"{total_return * 100:.2f}%")
            
            with col2:
                st.metric("波动率", f"{returns.std() * 100:.2f}%")
            
            with col3:
                sharpe = returns.mean() / returns.std() if returns.std() > 0 else 0
                st.metric("夏普比率", f"{sharpe:.2f}")
            
            with col4:
                st.metric("样本数", len(data))
        
        # 数据表格
        st.subheader("📋 数据预览")
        st.dataframe(data, use_container_width=True)
        
        # 下载数据
        st.subheader("💾 导出数据")
        
        csv = data.to_csv(index=False).encode('utf-8')
        
        st.download_button(
            "📥 下载 CSV",
            data=csv,
            file_name=f"data_{start_date}_{end_date}.csv",
            mime="text/csv"
        )
        
    except Exception as e:
        st.error(f"错误: {e}")


if __name__ == "__main__":
    main()
