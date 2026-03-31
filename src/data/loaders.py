"""
数据加载模块 — 从 TimescaleDB (quant_data) 加载因子和价格数据

Tables used:
  factor_meta   — admitted factor metadata (factor_id, name, expression, category, ic_mean, ...)
  factor_values — factor time-series values  (time, symbol, factor_name, value)
  market_daily  — daily OHLCV price data     (time, symbol, open, high, low, close, volume, ...)
"""

import logging
import re

import pandas as pd
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)


def _validate_identifier(name: str) -> str:
    """验证SQL标识符（表名/列名）是否安全"""
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
        raise ValueError(f"不安全的SQL标识符: {name}")
    return name


def get_available_factors(connection) -> List[dict]:
    """Read admitted factor list from factor_meta table."""
    sql = """
        SELECT factor_id, name, expression, category,
               ic_mean, ic_ir, ic_mean_is, ic_mean_oos,
               ic_win_rate, ls_return, admitted_at
        FROM factor_meta
        WHERE status = 'admitted'
        ORDER BY admitted_at DESC
    """
    df = pd.read_sql(sql, connection)
    if df.empty:
        return []
    return df.to_dict("records")


def get_factor_data(
    factor_id: str,
    connection,
) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """Read factor values from factor_values table."""
    factor_name = f"factor_{factor_id}"
    sql = """
        SELECT symbol, time, value
        FROM factor_values
        WHERE factor_name = %s
        ORDER BY time, symbol
    """
    try:
        df = pd.read_sql(sql, connection, params=[factor_name])
        if df.empty:
            return None, f"No data for factor {factor_id}"
        return df, None
    except Exception as e:
        return None, str(e)


def get_factor_metrics(factor_id: str, connection) -> Optional[dict]:
    """Read full metrics for a single factor from factor_meta."""
    sql = "SELECT * FROM factor_meta WHERE factor_id = %s"
    df = pd.read_sql(sql, connection, params=[factor_id])
    if df.empty:
        return None
    return df.iloc[0].to_dict()


def get_price_data(
    symbols: List[str],
    start_date: str,
    end_date: str,
    connection,
    table_name: str = 'market_daily'
) -> Optional[pd.DataFrame]:
    """从 market_daily 获取价格数据"""
    if not symbols:
        return None
    try:
        _validate_identifier(table_name)
        sql = f"""
            SELECT time, symbol, close
            FROM {table_name}
            WHERE symbol = ANY(%s)
            AND time >= %s AND time <= %s
            ORDER BY symbol, time
        """
        df = pd.read_sql(sql, connection, params=[symbols, start_date, end_date])
        return df if not df.empty else None
    except Exception as e:
        logger.warning("Failed to load price data: %s", e)
        return None


def get_database_tables(connection) -> List[str]:
    """获取数据库中所有表"""
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


__all__ = [
    'get_available_factors',
    'get_factor_data',
    'get_factor_metrics',
    'get_price_data',
    'get_database_tables',
]
