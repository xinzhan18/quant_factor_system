"""
数据加载模块
Data Loaders Module

职责：
- 从数据库加载因子数据、价格数据
- 返回标准化格式
- 被 Dashboard 页面调用

使用示例:
    from quant_factor_system.data.loaders import (
        get_factor_data,
        get_price_data,
        get_factor_overview,
    )
    
    # 获取因子数据
    factor_df, error = get_factor_data('momentum_20', connection)
    
    # 获取价格数据
    price_df = get_price_data(['SH600000'], '20240101', '20240131', connection)
"""

import pandas as pd
from typing import List, Tuple, Optional


# 数据库中实际存在的因子表映射
DATABASE_FACTORS = {
    'return_1d': 'factor_return_1d',
    'return_5d': 'factor_return_5d',
    'return_20d': 'factor_return_20d',
    'return_60d': 'factor_return_60d',
    'momentum_20': 'factor_momentum_20',
    'momentum_60': 'factor_momentum_60',
    'dist_ma10': 'factor_dist_ma10',
    'dist_ma20': 'factor_dist_ma20',
    'dist_ma60': 'factor_dist_ma60',
    'volatility_20': 'factor_volatility_20',
}


def get_factor_data(
    factor_name: str,
    connection,
    table_name: str = None
) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    从数据库获取因子数据
    
    Args:
        factor_name: 因子名称
        connection: 数据库连接
        table_name: 表名（可选，默认从映射获取）
        
    Returns:
        Tuple[DataFrame, error_msg]
        - 成功: (DataFrame, None)
        - 失败: (None, error_msg)
    """
    # 获取表名
    if table_name is None:
        table_name = DATABASE_FACTORS.get(factor_name)
    
    if table_name is None:
        return None, f"未知因子: {factor_name}"
    
    try:
        cursor = connection.cursor()
        
        # 查询数据
        cursor.execute(f"""
            SELECT time, symbol, value 
            FROM {table_name}
            ORDER BY time
        """)
        
        cols = ['time', 'symbol', 'value']
        rows = cursor.fetchall()
        
        if not rows:
            return None, "无数据"
        
        df = pd.DataFrame(rows, columns=cols)
        return df, None
        
    except Exception as e:
        return None, str(e)


def get_price_data(
    symbols: List[str],
    start_date: str,
    end_date: str,
    connection,
    table_name: str = 'price_daily'
) -> Optional[pd.DataFrame]:
    """
    从数据库获取价格数据
    
    Args:
        symbols: 股票代码列表
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        connection: 数据库连接
        table_name: 表名
        
    Returns:
        DataFrame 或 None
    """
    try:
        if not symbols:
            return None
        
        cursor = connection.cursor()
        
        placeholders = ','.join(['%s'] * len(symbols))
        cursor.execute(f"""
            SELECT time, symbol, close
            FROM {table_name}
            WHERE symbol IN ({placeholders})
            AND time >= %s AND time <= %s
            ORDER BY symbol, time
        """, symbols + [start_date, end_date])
        
        cols = ['time', 'symbol', 'close']
        rows = cursor.fetchall()
        
        if not rows:
            return None
        
        return pd.DataFrame(rows, columns=cols)
        
    except Exception:
        return None


def get_factor_overview(connection) -> pd.DataFrame:
    """
    获取所有因子表概览
    
    Args:
        connection: 数据库连接
        
    Returns:
        概览 DataFrame
    """
    try:
        cursor = connection.cursor()
        
        # 获取所有因子表
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name LIKE 'factor_%'
            ORDER BY table_name
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        data = []
        
        for table in tables:
            try:
                cursor.execute(f"""
                    SELECT COUNT(*), MIN(time), MAX(time)
                    FROM {table}
                """)
                stats = cursor.fetchone()
                
                cursor.execute(f"""
                    SELECT pg_size_pretty(pg_total_relation_size('{table}'::text))
                """)
                size = cursor.fetchone()[0]
                
                data.append({
                    '因子表': table,
                    '总记录': f"{stats[0]:,}",
                    '起始日期': stats[1].strftime('%Y-%m-%d') if stats[1] else '-',
                    '结束日期': stats[2].strftime('%Y-%m-%d') if stats[2] else '-',
                    '大小': size
                })
            except Exception:
                data.append({
                    '因子表': table,
                    '总记录': '?',
                    '起始日期': '-',
                    '结束日期': '-',
                    '大小': '?'
                })
        
        return pd.DataFrame(data)
        
    except Exception:
        return pd.DataFrame()


def get_database_tables(connection) -> List[str]:
    """
    获取数据库中所有表
    
    Args:
        connection: 数据库连接
        
    Returns:
        表名列表
    """
    try:
        cursor = connection.cursor()
        
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name NOT LIKE 'pg_%'
            AND table_name NOT LIKE 'sql_%'
            ORDER BY table_name
        """)
        
        return [row[0] for row in cursor.fetchall()]
        
    except Exception:
        return []


def get_available_factors() -> List[str]:
    """
    获取可用的因子列表
    
    Returns:
        因子名称列表
    """
    return list(DATABASE_FACTORS.keys())


__all__ = [
    'DATABASE_FACTORS',
    'get_factor_data',
    'get_price_data',
    'get_factor_overview',
    'get_database_tables',
    'get_available_factors',
]
