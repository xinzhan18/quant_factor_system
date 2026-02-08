#!/usr/bin/env python3
"""
本地 CSV 数据导入工具

功能:
1. 导入日线 CSV 到 SQLite
2. 导入因子 CSV 到 SQLite
3. 导入股票列表 CSV

使用方式:
    python csv_importer.py --daily your_daily.csv
    python csv_importer.py --factors your_factors.csv
    python csv_importer.py --stocks your_stocks.csv
"""

import argparse
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import os
import sys

# 配置
DEFAULT_DB_PATH = "storage/database/market_data.db"


def get_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """获取数据库连接"""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    return sqlite3.connect(db_path)


def init_db(db_path: str = DEFAULT_DB_PATH):
    """初始化数据库"""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    # 股票列表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stocks (
            code TEXT PRIMARY KEY,
            name TEXT,
            exchange TEXT,
            list_date TEXT,
            delist_date TEXT,
            status TEXT
        )
    ''')
    
    # 日线数据
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT,
            date TEXT,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume REAL,
            amount REAL,
            turn REAL,
            pct_chg REAL,
            pre_close REAL,
            UNIQUE(code, date)
        )
    ''')
    
    # 因子数据
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS factor_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT,
            date TEXT,
            factor_name TEXT,
            value REAL,
            UNIQUE(code, date, factor_name)
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"✅ 数据库已初始化: {db_path}")


def import_daily_csv(csv_path: str, db_path: str = DEFAULT_DB_PATH):
    """
    导入日线 CSV
    
    CSV 格式要求:
        - 必须包含: code, date
        - 可选包含: open, high, low, close, volume, amount, turn, pct_chg, pre_close
    
    示例:
        code,date,open,high,low,close,volume
        000001.XSHE,2024-01-02,10.50,10.80,10.30,10.60,5000000
    """
    print(f"\n📥 导入日线数据: {csv_path}")
    
    # 检查文件
    if not os.path.exists(csv_path):
        print(f"❌ 文件不存在: {csv_path}")
        return
    
    # 读取 CSV
    try:
        df = pd.read_csv(csv_path)
        print(f"   读取: {len(df)} 行")
    except Exception as e:
        print(f"❌ 读取失败: {e}")
        return
    
    # 检查必要字段
    required = ['code', 'date']
    for col in required:
        if col not in df.columns:
            print(f"❌ CSV 必须包含 '{col}' 列")
            return
    
    # 确保日期格式
    if df['date'].dtype == 'object':
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
    
    # 标准化字段名
    field_mapping = {
        'open': 'open', 'high': 'high', 'low': 'low',
        'close': 'close', 'volume': 'volume', 'amount': 'amount',
        'turnover': 'turn', 'turn': 'turn',
        'pct_chg': 'pct_chg', 'pct_chg': 'pct_chg',
        'pre_close': 'pre_close'
    }
    
    df = df.rename(columns=field_mapping)
    
    # 选择标准字段
    standard_cols = ['code', 'date', 'open', 'high', 'low', 'close', 
                   'volume', 'amount', 'turn', 'pct_chg', 'pre_close']
    available = [c for c in standard_cols if c in df.columns]
    df = df[available]
    
    # 初始化数据库
    init_db(db_path)
    
    # 导入
    conn = get_connection(db_path)
    
    # 使用 INSERT OR REPLACE 处理重复
    df.to_sql('daily_data', conn, if_exists='append', index=False)
    
    # 统计
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM daily_data")
    total = cursor.fetchone()[0]
    conn.close()
    
    print(f"✅ 导入成功!")
    print(f"   新增: {len(df)} 行")
    print(f"   总计: {total} 行")


def import_stocks_csv(csv_path: str, db_path: str = DEFAULT_DB_PATH):
    """
    导入股票列表 CSV
    
    CSV 格式要求:
        - 必须包含: code
        - 可选包含: name, exchange, list_date, status
    """
    print(f"\n📥 导入股票列表: {csv_path}")
    
    if not os.path.exists(csv_path):
        print(f"❌ 文件不存在: {csv_path}")
        return
    
    try:
        df = pd.read_csv(csv_path)
        print(f"   读取: {len(df)} 行")
    except Exception as e:
        print(f"❌ 读取失败: {e}")
        return
    
    # 标准化
    df = df.rename(columns={
        'symbol': 'code',
        'ticker': 'code',
        'exchange': 'exchange',
        'market': 'exchange',
        'listed_date': 'list_date',
        'list_date': 'list_date',
        'status': 'status'
    })
    
    if 'code' not in df.columns:
        print("❌ CSV 必须包含 'code' 列")
        return
    
    init_db(db_path)
    conn = get_connection(db_path)
    df.to_sql('stocks', conn, if_exists='replace', index=False)
    
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM stocks")
    total = cursor.fetchone()[0]
    conn.close()
    
    print(f"✅ 导入成功! 总计: {total} 只股票")


def import_factor_csv(csv_path: str, db_path: str = DEFAULT_DB_PATH):
    """
    导入因子 CSV
    
    CSV 格式要求:
        - 必须包含: code, date, factor_name, value
        - 或者: code, date, momentum_20d, pe, roe...
    """
    print(f"\n📥 导入因子数据: {csv_path}")
    
    if not os.path.exists(csv_path):
        print(f"❌ 文件不存在: {csv_path}")
        return
    
    df = pd.read_csv(csv_path)
    print(f"   读取: {len(df)} 行, 列: {list(df.columns)}")
    
    # 检查格式
    if 'factor_name' in df.columns and 'value' in df.columns:
        # 长格式: code, date, factor_name, value
        init_db(db_path)
        conn = get_connection(db_path)
        df.to_sql('factor_data', conn, if_exists='append', index=False)
        print(f"✅ 导入成功: {len(df)} 行")
    else:
        # 宽格式: code, date, momentum_20d, pe, roe...
        # 需要拆分成多行
        print("   检测到宽格式，转换为长格式...")
        
        id_vars = [c for c in df.columns if c not in ['momentum', 'momentum_20d', 'momentum_60d', 
                  'pe', 'pb', 'roe', 'quality', 'volatility']]
        
        if 'code' not in df.columns or 'date' not in df.columns:
            print("❌ 宽格式必须包含 code 和 date 列")
            return
        
        # 找到因子列
        factor_cols = [c for c in df.columns if c not in ['code', 'date', 'open', 'high', 'low', 
                      'close', 'volume', 'amount']]
        
        if not factor_cols:
            print("❌ 未找到因子列")
            return
        
        # 转换
        df_long = df.melt(
            id_vars=['code', 'date'],
            value_vars=factor_cols,
            var_name='factor_name',
            value_name='value'
        )
        
        init_db(db_path)
        conn = get_connection(db_path)
        df_long.to_sql('factor_data', conn, if_exists='append', index=False)
        
        print(f"✅ 导入成功: {len(df_long)} 行")


def show_stats(db_path: str = DEFAULT_DB_PATH):
    """显示数据库统计"""
    print(f"\n📊 数据库统计: {db_path}")
    
    conn = get_connection(db_path)
    
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM stocks")
    stocks = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM daily_data")
    daily = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM factor_data")
    factors = cursor.fetchone()[0]
    
    cursor.execute("SELECT MIN(date), MAX(date) FROM daily_data")
    dates = cursor.fetchone()
    
    conn.close()
    
    print(f"   股票数量: {stocks}")
    print(f"   日线记录: {daily:,}")
    print(f"   因子记录: {factors:,}")
    print(f"   日期范围: {dates[0]} ~ {dates[1]}")


def query_sample(db_path: str = DEFAULT_DB_PATH, table: str = 'daily_data', limit: int = 5):
    """查询样本数据"""
    print(f"\n📋 {table} 样本 (前{limit}行):")
    
    conn = get_connection(db_path)
    df = pd.read_sql(f"SELECT * FROM {table} LIMIT {limit}", conn)
    conn.close()
    
    if not df.empty:
        print(df.to_string())


def main():
    parser = argparse.ArgumentParser(
        description='本地 CSV 数据导入工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  # 初始化数据库
  python csv_importer.py --init

  # 导入日线数据
  python csv_importer.py --daily daily_data.csv

  # 导入股票列表
  python csv_importer.py --stocks stocks.csv

  # 导入因子数据
  python csv_importer.py --factors factors.csv

  # 查看统计
  python csv_importer.py --stats

  # 查询样本
  python csv_importer.py --query --table daily_data
        '''
    )
    
    parser.add_argument('--init', action='store_true', help='初始化数据库')
    parser.add_argument('--daily', type=str, metavar='FILE', help='导入日线 CSV')
    parser.add_argument('--stocks', type=str, metavar='FILE', help='导入股票列表 CSV')
    parser.add_argument('--factors', type=str, metavar='FILE', help='导入因子 CSV')
    parser.add_argument('--stats', action='store_true', help='显示数据库统计')
    parser.add_argument('--query', action='store_true', help='查询样本')
    parser.add_argument('--table', type=str, default='daily_data', help='查询表名')
    parser.add_argument('--limit', type=int, default=5, help='查询数量')
    parser.add_argument('--db', type=str, default=DEFAULT_DB_PATH, help='数据库路径')
    
    args = parser.parse_args()
    
    if args.init:
        init_db(args.db)
    
    if args.daily:
        import_daily_csv(args.daily, args.db)
    
    if args.stocks:
        import_stocks_csv(args.stocks, args.db)
    
    if args.factors:
        import_factor_csv(args.factors, args.db)
    
    if args.stats:
        show_stats(args.db)
    
    if args.query:
        query_sample(args.db, args.table, args.limit)
    
    if not any([args.init, args.daily, args.stocks, args.factors, args.stats, args.query]):
        parser.print_help()


if __name__ == '__main__':
    main()
