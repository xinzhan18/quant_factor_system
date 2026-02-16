"""
行业因子存储模块
Industry Factor Storage

功能:
- 创建行业因子表
- 存储/查询行业因子
- 增量更新

使用:
    from quant_factor_system.data import IndustryStorage
    
    storage = IndustryStorage()
    
    # 初始化表
    storage.create_tables()
    
    # 保存行业因子
    storage.save_industry_factors(df, date='2024-01-01')
    
    # 查询
    df = storage.get_industry_factors('2024-01-01')
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

# 尝试导入数据库连接
try:
    from .timescale_storage import TimescaleDB
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    logger.warning("数据库不可用，将使用模拟模式")


class IndustryStorage:
    """
    行业因子存储
    
    功能:
    - 存储行业归属信息 (低频)
    - 存储行业因子数据 (每日)
    - 增量更新
    """
    
    def __init__(self, db: TimescaleDB = None):
        """
        初始化
        
        Args:
            db: TimescaleDB实例
        """
        self.db = db
        self._cache: Dict[str, pd.DataFrame] = {}
    
    def _get_db(self) -> Optional[TimescaleDB]:
        """获取数据库连接"""
        if self.db is None:
            if DB_AVAILABLE:
                try:
                    self.db = TimescaleDB()
                except Exception as e:
                    logger.warning(f"数据库连接失败: {e}")
        return self.db
    
    # ==================== 表管理 ====================
    
    def create_tables(self):
        """创建行业相关表"""
        db = self._get_db()
        if db is None:
            logger.warning("⚠️ 数据库不可用，跳过表创建")
            return
        
        with db.connection() as conn:
            cursor = conn.cursor()
            
            # 行业归属表 (低频更新)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS industry_classification (
                    stock_code TEXT NOT NULL,
                    industry TEXT NOT NULL,
                    sub_industry TEXT,
                    update_date DATE NOT NULL,
                    PRIMARY KEY (stock_code, update_date)
                );
            """)
            logger.info("✅ industry_classification 表创建成功")
            
            # 行业因子表 (每日更新)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS factor_industry_daily (
                    time TIMESTAMP NOT NULL,
                    industry TEXT NOT NULL,
                    factor_name TEXT NOT NULL,
                    factor_value DOUBLE PRECISION,
                    PRIMARY KEY (time, industry, factor_name)
                );
            """)
            logger.info("✅ factor_industry_daily 表创建成功")
            
            # 创建索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_industry_class_date 
                ON industry_classification(update_date);
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_factor_industry_time 
                ON factor_industry_daily(time);
            """)
            
            conn.commit()
    
    # ==================== 行业归属 ====================
    
    def save_industry_classification(
        self,
        df: pd.DataFrame,
        if_exists: str = 'append'
    ) -> int:
        """
        保存行业归属信息
        
        Args:
            df: 需包含列: stock_code, industry, sub_industry, update_date
            if_exists: 'append' | 'replace'
            
        Returns:
            保存的记录数
        """
        db = self._get_db()
        if db is None:
            logger.info(f"⚠️ 模拟模式: 保存行业分类 {len(df)} 条")
            return len(df)
        
        if df.empty:
            return 0
        
        df = df.copy()
        
        # 确保日期格式
        if 'update_date' in df.columns:
            df['update_date'] = pd.to_datetime(df['update_date']).dt.strftime('%Y-%m-%d')
        
        with db.connection() as conn:
            cursor = conn.cursor()
            
            if if_exists == 'replace':
                # 不删除，保留历史版本
                pass
            
            records = 0
            for _, row in df.iterrows():
                try:
                    cursor.execute("""
                        INSERT INTO industry_classification 
                        (stock_code, industry, sub_industry, update_date)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (stock_code, update_date) 
                        DO UPDATE SET industry = EXCLUDED.industry,
                                     sub_industry = EXCLUDED.sub_industry
                    """, (
                        row['stock_code'],
                        row['industry'],
                        row.get('sub_industry'),
                        row['update_date']
                    ))
                    records += 1
                except Exception as e:
                    logger.warning(f"保存行业分类失败: {e}")
                    continue
            
            conn.commit()
        
        logger.info(f"✅ 保存行业分类: {records} 条")
        return records
    
    def get_industry_classification(
        self,
        date: str = None,
        stock_code: str = None
    ) -> pd.DataFrame:
        """
        获取行业归属信息
        
        Args:
            date: 查询日期 (获取该日期有效的分类)
            stock_code: 股票代码
            
        Returns:
            行业分类DataFrame
        """
        db = self._get_db()
        if db is None:
            logger.warning("⚠️ 数据库不可用")
            return pd.DataFrame()
        
        query = """
            SELECT stock_code, industry, sub_industry, update_date
            FROM industry_classification
            WHERE 1=1
        """
        params = []
        
        if date:
            query += " AND update_date <= %s"
            params.append(pd.to_datetime(date).strftime('%Y-%m-%d'))
        
        if stock_code:
            query += " AND stock_code = %s"
            params.append(stock_code)
        
        query += " ORDER BY update_date DESC"
        
        with db.connection() as conn:
            df = pd.read_sql(query, conn, params=params)
        
        if df.empty:
            return df
        
        # 去重，保留每个股票最新的分类
        if stock_code is None:
            df = df.drop_duplicates(subset=['stock_code'], keep='first')
        
        return df
    
    def get_stock_industry(
        self,
        stock_code: str,
        date: str = None
    ) -> Optional[str]:
        """
        获取单只股票的行业归属
        
        Args:
            stock_code: 股票代码
            date: 查询日期
            
        Returns:
            行业名称
        """
        df = self.get_industry_classification(date=date, stock_code=stock_code)
        
        if df.empty:
            return None
        
        return df.iloc[0]['industry']
    
    # ==================== 行业因子 ====================
    
    def save_industry_factors(
        self,
        df: pd.DataFrame,
        date: str = None
    ) -> int:
        """
        保存行业因子
        
        Args:
            df: 行业因子数据 (需包含: time, industry, factor_name, factor_value)
            date: 数据日期
            
        Returns:
            保存的记录数
        """
        db = self._get_db()
        if db is None:
            logger.info(f"⚠️ 模拟模式: 保存行业因子 {len(df)} 条")
            return len(df)
        
        if df.empty:
            return 0
        
        df = df.copy()
        
        # 确保时间格式
        if 'time' in df.columns:
            df['time'] = pd.to_datetime(df['time'])
        else:
            df['time'] = pd.to_datetime(date)
        
        with db.connection() as conn:
            cursor = conn.cursor()
            
            # 转换为长格式 (每个因子一行)
            factor_rows = []
            
            for _, row in df.iterrows():
                time = row['time']
                industry = row['industry']
                
                for col in df.columns:
                    if col not in ['time', 'industry']:
                        factor_rows.append({
                            'time': time,
                            'industry': industry,
                            'factor_name': col,
                            'factor_value': row[col]
                        })
            
            if not factor_rows:
                return 0
            
            factor_df = pd.DataFrame(factor_rows)
            
            records = 0
            for _, row in factor_df.iterrows():
                try:
                    cursor.execute("""
                        INSERT INTO factor_industry_daily 
                        (time, industry, factor_name, factor_value)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (time, industry, factor_name) 
                        DO UPDATE SET factor_value = EXCLUDED.factor_value
                    """, (
                        row['time'],
                        row['industry'],
                        row['factor_name'],
                        row['factor_value']
                    ))
                    records += 1
                except Exception as e:
                    logger.warning(f"保存行业因子失败: {e}")
                    continue
            
            conn.commit()
        
        logger.info(f"✅ 保存行业因子: {records} 条")
        return records
    
    def get_industry_factors(
        self,
        date: str = None,
        industry: str = None,
        factor_names: List[str] = None
    ) -> pd.DataFrame:
        """
        获取行业因子
        
        Args:
            date: 查询日期
            industry: 行业名称
            factor_names: 因子列表
            
        Returns:
            行业因子DataFrame
        """
        db = self._get_db()
        if db is None:
            logger.warning("⚠️ 数据库不可用")
            return pd.DataFrame()
        
        query = """
            SELECT time, industry, factor_name, factor_value
            FROM factor_industry_daily
            WHERE 1=1
        """
        params = []
        
        if date:
            query += " AND time::date = %s"
            params.append(pd.to_datetime(date).strftime('%Y-%m-%d'))
        
        if industry:
            query += " AND industry = %s"
            params.append(industry)
        
        if factor_names:
            placeholders = ','.join(['%s'] * len(factor_names))
            query += f" AND factor_name IN ({placeholders})"
            params.extend(factor_names)
        
        with db.connection() as conn:
            df = pd.read_sql(query, conn, params=params)
        
        if df.empty:
            return df
        
        # 转换为宽格式
        df = df.pivot_table(
            index=['time', 'industry'],
            columns='factor_name',
            values='factor_value'
        ).reset_index()
        
        return df
    
    def get_industry_factor_series(
        self,
        factor_name: str,
        industry: str = None,
        start_date: str = None,
        end_date: str = None
    ) -> pd.DataFrame:
        """
        获取行业因子时间序列
        
        Args:
            factor_name: 因子名称
            industry: 行业名称
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            时间序列DataFrame
        """
        db = self._get_db()
        if db is None:
            return pd.DataFrame()
        
        query = """
            SELECT time, industry, factor_value
            FROM factor_industry_daily
            WHERE factor_name = %s
        """
        params = [factor_name]
        
        if industry:
            query += " AND industry = %s"
            params.append(industry)
        
        if start_date:
            query += " AND time >= %s"
            params.append(pd.to_datetime(start_date))
        
        if end_date:
            query += " AND time <= %s"
            params.append(pd.to_datetime(end_date))
        
        query += " ORDER BY time"
        
        with db.connection() as conn:
            df = pd.read_sql(query, conn, params=params)
        
        if df.empty:
            return df
        
        df = df.pivot(index='time', columns='industry', values='factor_value')
        df.index = pd.to_datetime(df.index)
        
        return df
    
    # ==================== 增量更新 ====================
    
    def check_industry_update_needed(
        self,
        date: str = None
    ) -> bool:
        """
        检查行业归属是否需要更新
        
        Args:
            date: 查询日期
            
        Returns:
            是否需要更新
        """
        db = self._get_db()
        if db is None:
            return True
        
        date = pd.to_datetime(date).strftime('%Y-%m-%d') if date else None
        
        query = """
            SELECT COUNT(*) FROM industry_classification
            WHERE update_date = %s
        """
        
        with db.connection() as conn:
            df = pd.read_sql(query, conn, params=[date])
        
        return df.iloc[0][0] == 0
    
    def need_daily_update(
        self,
        date: str = None
    ) -> bool:
        """
        检查行业因子是否需要每日更新
        
        Args:
            date: 查询日期
            
        Returns:
            是否需要更新
        """
        db = self._get_db()
        if db is None:
            return True
        
        date_str = pd.to_datetime(date).strftime('%Y-%m-%d') if date else None
        
        query = """
            SELECT COUNT(*) FROM factor_industry_daily
            WHERE time::date = %s
        """
        
        with db.connection() as conn:
            df = pd.read_sql(query, conn, params=[date_str])
        
        return df.iloc[0][0] == 0


# ==================== 便捷函数 ====================

def get_industry_storage(db: TimescaleDB = None) -> IndustryStorage:
    """获取行业存储实例"""
    return IndustryStorage(db)


# ==================== 导出 ====================

__all__ = [
    'IndustryStorage',
    'get_industry_storage',
]
