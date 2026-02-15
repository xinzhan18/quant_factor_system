"""
统一数据管理器
Unified Data Manager

整合所有数据源:
1. TimescaleDB (主数据源)
2. 数据模拟器
3. CSV导入

使用方式:
    from quant_factor_system.data import DataManager
    
    # 初始化
    dm = DataManager()
    
    # 获取数据 (自动从数据库或模拟)
    data = dm.get_price_data(
        symbols=['SH600000'],
        frequency='1min',
        start='2024-01-01',
        use_cache=True
    )
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from contextlib import contextmanager
import logging

from .timescale_db import TimescaleDB, Frequency, get_db
from .simulator import create_multi_stock_data

logger = logging.getLogger(__name__)


class DataManager:
    """
    统一数据管理器
    
    功能:
    - 统一接口访问数据
    - 支持TimescaleDB和模拟数据
    - 缓存管理
    - 数据转换
    """
    
    def __init__(
        self,
        use_db: bool = True,
        connection_string: str = None,
        cache_dir: str = None
    ):
        """
        初始化
        
        Args:
            use_db: 是否使用TimescaleDB
            connection_string: 数据库连接字符串
            cache_dir: 缓存目录
        """
        self.use_db = use_db
        self.cache_dir = cache_dir
        self._db: Optional[TimescaleDB] = None
        self._cache: Dict[str, pd.DataFrame] = {}
        
        if use_db:
            try:
                self._db = get_db(connection_string)
                status = self._db.check()
                if status.get('timescaledb'):
                    logger.info("✅ TimescaleDB 已连接")
                else:
                    logger.warning("⚠️ TimescaleDB 未安装，将使用模拟数据")
                    self.use_db = False
            except Exception as e:
                logger.warning(f"⚠️ 数据库连接失败: {e}")
                self.use_db = False
    
    @property
    def db(self) -> Optional[TimescaleDB]:
        """获取数据库连接"""
        return self._db
    
    # ==================== 价格数据 ====================
    
    def get_price_data(
        self,
        symbols: List[str] = None,
        frequency: str = '1min',
        start: Union[str, datetime] = None,
        end: Union[str, datetime] = None,
        n_periods: int = None,
        use_cache: bool = False,
        use_aggregate: bool = False,
        force_simulate: bool = False
    ) -> pd.DataFrame:
        """
        获取价格数据
        
        Args:
            symbols: 股票代码
            frequency: 频率
            start: 开始时间
            end: 结束时间
            n_periods: 数据周期数 (用于模拟)
            use_cache: 是否使用缓存
            use_aggregate: 是否使用聚合视图 (仅数据库)
            force_simulate: 强制使用模拟数据
            
        Returns:
            DataFrame
        """
        # 1. 尝试从数据库获取
        if self.use_db and not force_simulate:
            try:
                df = self._db.query_price(
                    symbols=symbols,
                    frequency=frequency,
                    start=start,
                    end=end,
                    use_aggregate=use_aggregate
                )
                
                if not df.empty:
                    logger.info(f"📊 从数据库获取 {frequency}: {len(df)} 行")
                    return df
                    
            except Exception as e:
                logger.warning(f"数据库查询失败: {e}")
        
        # 2. 使用模拟数据
        logger.info(f"🎭 使用模拟数据: {frequency}")
        
        # 确定模拟参数
        if start is None:
            start = '2024-01-01'
        if n_periods is None:
            n_periods = self._get_periods(frequency)
        
        # 生成模拟数据
        df = create_multi_stock_data(
            symbols=symbols or ['STOCK_%03d' % i for i in range(1, 11)],
            start_date=start,
            periods=n_periods,
            freq=self._get_pandas_freq(frequency)
        )
        
        # 缓存
        if use_cache:
            cache_key = f"{frequency}_{start}_{n_periods}"
            self._cache[cache_key] = df
        
        return df
    
    def save_price_data(
        self,
        df: pd.DataFrame,
        frequency: str = '1min',
        if_exists: str = 'append'
    ) -> int:
        """
        保存价格数据到数据库
        
        Args:
            df: 价格数据
            frequency: 频率
            if_exists: 'append' | 'replace'
            
        Returns:
            写入行数
        """
        if not self.use_db:
            logger.warning("⚠️ 数据库未连接，无法保存")
            return 0
        
        if if_exists == 'replace':
            logger.warning("TimescaleDB不支持replace，将使用append")
        
        return self._db.insert_price(df, frequency=frequency)
    
    # ==================== 因子数据 ====================
    
    def get_factor_data(
        self,
        factor_names: List[str],
        symbols: List[str] = None,
        frequency: str = 'daily',
        start: Union[str, datetime] = None,
        end: Union[str, datetime] = None,
        pivot: bool = False,
        force_simulate: bool = False
    ) -> pd.DataFrame:
        """获取因子数据"""
        if self.use_db and not force_simulate:
            try:
                df = self._db.query_factor(
                    factor_names=factor_names,
                    symbols=symbols,
                    frequency=frequency,
                    start=start,
                    end=end,
                    pivot=pivot
                )
                
                if not df.empty:
                    logger.info(f"📊 获取因子数据: {len(df)} 行")
                    return df
                    
            except Exception as e:
                logger.warning(f"因子查询失败: {e}")
        
        # 返回空DataFrame
        return pd.DataFrame()
    
    def save_factor_data(
        self,
        df: pd.DataFrame,
        frequency: str = 'daily'
    ) -> int:
        """保存因子数据"""
        if not self.use_db:
            logger.warning("⚠️ 数据库未连接，无法保存")
            return 0
        
        return self._db.insert_factor(df, frequency=frequency)
    
    # ==================== 数据统计 ====================
    
    def get_data_stats(self) -> Dict[str, Any]:
        """获取数据统计"""
        stats = {
            'database_connected': self.use_db,
            'cache_size': len(self._cache),
        }
        
        if self.use_db:
            try:
                stats['price_count'] = self._db.get_stats()
                stats['aggregate_count'] = self._db.get_aggregate_stats()
            except:
                pass
        
        return stats
    
    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()
        logger.info("✅ 缓存已清空")
    
    # ==================== 辅助方法 ====================
    
    def _get_periods(self, frequency: str) -> int:
        """获取模拟数据周期数"""
        periods = {
            '1min': 500,
            '5min': 200,
            '15min': 100,
            '30min': 60,
            'daily': 100,
            'weekly': 52,
            'monthly': 24
        }
        return periods.get(frequency, 100)
    
    def _get_pandas_freq(self, frequency: str) -> str:
        """获取pandas频率字符串"""
        freq_map = {
            '1min': 'min',
            '5min': '5min',
            '15min': '15min',
            '30min': '30min',
            'daily': 'B',
            'weekly': 'W',
            'monthly': 'MS'
        }
        return freq_map.get(frequency, 'B')
    
    def close(self):
        """关闭连接"""
        if self._db:
            self._db.close()
        self._cache.clear()


# ==================== 便捷函数 ====================

def create_data_manager(use_db: bool = True, **kwargs) -> DataManager:
    """创建数据管理器"""
    return DataManager(use_db=use_db, **kwargs)


# ==================== 导出 ====================

__all__ = [
    'DataManager',
    'create_data_manager',
]
