"""
历史回测页面
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from config import (
    st, pd, np, init_session_state, get_database,
    get_csv_storage
)


def show_backtest_list(db):
    """显示回测列表"""
    st.subheader("📋 历史回测")
    
    backtests = db.get_backtests(limit=20)
    
    if backtests.empty:
        st.info("暂无回测记录")
        return None
    
    # 显示回测列表
    st.dataframe(
        backtests[['id', 'name', 'start_date', 'end_date', 'total_return', 'sharpe_ratio', 'created_at']],
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row"
    )
    
    # 获取选中的回测
    if len(st.session_state.get('st_data_state', {}).get('selection', [])) > 0:
        selected_idx = st.session_state['st_data_state']['selection'][0]['row'][0]
        return backtests.iloc[selected_idx]
    
    return None


def show_backtest_detail(backtest_id: int, db):
    """显示回测详情"""
    detail = db.get_backtest_detail(backtest_id)
    
    if detail is None:
        st.warning("找不到回测详情")
        return
    
    st.divider()
    st.subheader(f"📊 回测详情: {detail['name']}")
    
    # 基本信息
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("总收益", f"{detail['total_return']:.2%}")
    with col2:
        st.metric("夏普比率", f"{detail['sharpe_ratio']:.2f}")
    with col3:
        st.metric("最大回撤", f"{detail['max_drawdown']:.2%}")
    with col4:
        st.metric("回测期间", f"{detail['start_date']} ~ {detail['end_date']}")
    
    # 详细结果
    if detail['results']:
        st.subheader("📈 详细结果")
        
        results = detail['results']
        
        if isinstance(results, dict):
            # 显示结果字典
            result_df = pd.DataFrame(list(results.items()), columns=['指标', '值'])
            st.dataframe(result_df, hide_index=True)
        
        # 如果有净值数据，可以显示图表
        if 'nav' in str(results):
            st.line_chart(pd.DataFrame(results['nav']))


def show_new_backtest_form(db, csv):
    """新建回测表单"""
    st.subheader("➕ 新建回测")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        name = st.text_input("回测名称", value=f"回测_{datetime.now().strftime('%Y%m%d')}")
    
    with col2:
        start_date = st.date_input("开始日期", value=datetime.now() - timedelta(days=365))
    
    with col3:
        end_date = st.date_input("结束日期", value=datetime.now())
    
    # 选择因子
    factors = db.list_factors()
    if not factors.empty:
        selected_factors = st.multiselect(
            "选择因子",
            factors['name'].tolist()
        )
    else:
        selected_factors = []
        st.warning("请先添加因子")
    
    # 参数
    col1, col2 = st.columns(2)
    
    with col1:
        initial_capital = st.number_input("初始资金", value=1000000)
    
    with col2:
        rebalance_freq = st.selectbox("调仓频率", ["日", "周", "月"])
    
    # 运行回测按钮
    if st.button("🚀 运行回测", use_container_width=True):
        if not selected_factors:
            st.error("请选择至少一个因子")
            return
        
        # 这里应该调用回测引擎
        st.info("回测功能开发中...")
        
        # 保存回测记录
        # db.save_backtest(name, {...}, {...})


def main():
    """页面主函数"""
    init_session_state()
    
    st.title("📈 历史回测")
    
    # 获取数据库
    db = get_database()
    
    # 显示回测列表
    selected_backtest = show_backtest_list(db)
    
    if selected_backtest is not None:
        show_backtest_detail(int(selected_backtest['id']), db)
    
    st.divider()
    
    # 新建回测
    show_new_backtest_form(db, get_csv_storage())


if __name__ == "__main__":
    main()
