"""
因子评估页面
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from config import (
    st, pd, np, init_session_state, get_database,
    get_csv_storage, BASE_DIR, FACTOR_CATEGORIES
)


def show_factor_selector(db, key: str = "factor_selector"):
    """因子选择器"""
    factors = db.list_factors()
    
    if factors.empty:
        st.warning("暂无因子，请先添加因子")
        return None
    
    factor_names = factors['name'].tolist()
    selected = st.selectbox("选择因子", factor_names, key=key)
    
    return selected


def show_factor_info(factor_name: str, db):
    """显示因子信息"""
    factor = db.get_factor(factor_name)
    
    if factor:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("类别", factor.get('category', 'N/A'))
        with col2:
            st.metric("创建时间", factor.get('created_at', 'N/A')[:10])
        with col3:
            params = factor.get('params', {})
            st.metric("参数", str(params))
    
    st.divider()


def show_evaluation_form(factor_name: str, db):
    """评估表单"""
    st.subheader("📊 运行评估")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        period_start = st.date_input(
            "开始日期",
            value=datetime.now() - timedelta(days=365)
        )
    
    with col2:
        period_end = st.date_input(
            "结束日期",
            value=datetime.now()
        )
    
    with col3:
        num_groups = st.selectbox("分组数", [3, 5, 10], index=1)
    
    # 运行评估按钮
    if st.button("🚀 运行评估", use_container_width=True):
        return True
    
    return False


def run_evaluation(factor_name: str, db, period_start, period_end, num_groups):
    """执行评估"""
    with st.spinner("评估中..."):
        try:
            # 获取因子数据
            csv = get_csv_storage()
            factor_data = csv.load_factor_data(factor_name)
            
            if factor_data is None:
                st.warning(f"找不到因子 {factor_name} 的数据")
                return
            
            # 导入评估模块
            from quant_factor_system import (
                FactorSystem, MomentumFactor, ValueFactor,
                QualityFactor, FactorEvaluator, BacktestConfig
            )
            
            # 创建因子系统
            system = FactorSystem()
            system.add_factor(MomentumFactor(20), weight=1.0)
            
            # 运行评估
            config = BacktestConfig(num_groups=num_groups)
            evaluator = FactorEvaluator(config)
            
            # 计算收益
            if 'close' in factor_data.columns:
                returns = factor_data.groupby('symbol')['close'].pct_change().dropna()
            else:
                returns = factor_data['close'].pct_change().dropna()
            
            # 获取因子值
            factor_values = system.calculate_all(factor_data)
            
            if factor_name not in factor_values.columns:
                st.error(f"因子 {factor_name} 不存在")
                return
            
            # 运行评估
            result = evaluator.evaluate(factor_name, factor_values[factor_name], returns)
            
            # 保存结果
            db.save_evaluation(factor_name, {
                'eval_date': datetime.now().strftime('%Y-%m-%d'),
                'period_start': str(period_start),
                'period_end': str(period_end),
                'ic': result.ic,
                'ic_ir': result.ic_ir,
                'ic_std': getattr(result, 'ic_std', 0),
                'win_rate': result.ic_sign_ratio,
                'long_short_return': result.long_short_return,
                'num_groups': num_groups,
                'num_samples': len(factor_values)
            })
            
            st.success("评估完成！")
            
            # 显示结果
            show_evaluation_result(result)
            
        except Exception as e:
            st.error(f"评估失败: {str(e)}")
            import traceback
            st.error(traceback.format_exc())


def show_evaluation_result(result):
    """显示评估结果"""
    st.divider()
    st.subheader("📈 评估结果")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("IC", f"{result.ic:.4f}")
    with col2:
        st.metric("IC IR", f"{result.ic_ir:.4f}")
    with col3:
        st.metric("胜率", f"{result.ic_sign_ratio:.2%}")
    with col4:
        st.metric("多空收益", f"{result.long_short_return:.4f}")


def show_ic_history(factor_name: str, db):
    """显示 IC 历史"""
    st.subheader("📉 IC 历史走势")
    
    evaluations = db.get_evaluations(factor_name, limit=50)
    
    if evaluations.empty:
        st.info("暂无历史评估数据")
        return
    
    # 准备数据
    if 'eval_date' in evaluations.columns and 'ic' in evaluations.columns:
        chart_data = evaluations[['eval_date', 'ic']].copy()
        chart_data['eval_date'] = pd.to_datetime(chart_data['eval_date'])
        chart_data = chart_data.sort_values('eval_date')
        
        st.line_chart(chart_data.set_index('eval_date'))


def show_group_returns(result):
    """显示分组收益"""
    st.subheader("📊 分组收益")
    
    if hasattr(result, 'group_returns') and result.group_returns:
        # 转换字典为 DataFrame
        if isinstance(result.group_returns, dict):
            df = pd.DataFrame(list(result.group_returns.items()), 
                            columns=['Group', 'Return'])
            df = df.sort_values('Group')
        else:
            df = result.group_returns
        
        st.bar_chart(df.set_index('Group'))


def show_factor_details(factor_name: str, db):
    """显示因子详情"""
    st.subheader("📋 因子详情")
    
    evaluations = db.get_evaluations(factor_name, limit=20)
    
    if not evaluations.empty:
        st.dataframe(
            evaluations[['eval_date', 'ic', 'ic_ir', 'win_rate', 'long_short_return', 'num_samples']],
            use_container_width=True,
            hide_index=True
        )


def main():
    """页面主函数"""
    init_session_state()
    
    st.title("📊 因子评估")
    
    # 获取数据库
    db = get_database()
    
    # 因子选择
    factor_name = show_factor_selector(db)
    
    if factor_name:
        # 显示因子信息
        show_factor_info(factor_name, db)
        
        # 评估表单
        if show_evaluation_form(factor_name, db):
            run_evaluation(factor_name, db, 
                          st.session_state.get('period_start', datetime.now() - timedelta(days=365)),
                          st.session_state.get('period_end', datetime.now()),
                          st.session_state.get('num_groups', 5))
        
        # IC 历史
        show_ic_history(factor_name, db)
        
        # 因子详情
        show_factor_details(factor_name, db)


if __name__ == "__main__":
    main()
