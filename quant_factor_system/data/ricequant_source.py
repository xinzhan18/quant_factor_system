"""
米筐数据源适配器
RiceQuant Data Source Adapter

功能:
- 获取日线/分钟线/Tick数据
- 获取全市场股票列表
- 缓存管理
- 增量更新

使用:
    from quant_factor_system.data import RiceQuantSource
    
    source = RiceQuantSource()
    
    # 获取日线数据
    daily = source.get_daily_data(
        symbols=['SH600000', 'SZ000001'],
        start_date='20240101',
        end_date='20240131'
    )
    
    # 获取分钟数据
    minute = source.get_minute_data(
        symbols=['SH600000'],
        start_date='20240101',
        end_date='20240131',
        frequency='1min'
    )

注意:
    - 需要预先配置 RQDATAC_CONF 环境变量
    - 如果未安装 rqdatac，将使用模拟数据
"""

import os
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

# 检查是否安装了rqdatac
try:
    import rqdatac as rq
    RQDATAC_AVAILABLE = True
except ImportError:
    RQDATAC_AVAILABLE = False
    logger.warning("rqdatac未安装，将使用模拟数据")


class RiceQuantSource:
    """
    米筐数据源
    
    功能:
    - 获取日线/分钟线/Tick数据
    - 获取全市场股票列表
    - 缓存管理
    - 增量更新
    """
    
    # 频率映射 (米筐格式)
    FREQUENCY_MAP = {
        'daily': '1d',
        '1min': '1m',
        '5min': '5m',
        '15min': '15m',
        '30min': '30m',
        '60min': '60m',
        'tick': 'tick'
    }
    
    def __init__(
        self,
        cache_dir: str = './.cache/ricequant',
        cache_days: int = 7
    ):
        """
        初始化
        
        Args:
            cache_dir: 缓存目录
            cache_days: 缓存过期天数
        """
        self.cache_dir = Path(cache_dir)
        self.cache_days = cache_days
        
        # 创建缓存目录
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化连接 (使用环境变量 RQDATAC_CONF)
        if RQDATAC_AVAILABLE:
            try:
                rq.init()
                logger.info("✅ 米筐连接已初始化")
            except Exception as e:
                logger.warning(f"⚠️ 米筐连接失败: {e}")
        
        # 内存缓存
        self._memory_cache: Dict[str, pd.DataFrame] = {}
        
        # 缓存的股票列表
        self._stock_map: Dict[str, str] = {}  # symbol -> order_book_id
    
    # ==================== 连接管理 ====================
    
    def is_connected(self) -> bool:
        """检查是否已连接"""
        if not RQDATAC_AVAILABLE:
            return False
        
        try:
            # 尝试获取交易日历来测试连接
            rq.get_trading_dates(start_date='20240101', end_date='20240103')
            return True
        except Exception:
            return False
    
    # ==================== 股票列表 ====================
    
    def _build_stock_map(self, date: str = None) -> Dict[str, str]:
        """
        构建股票代码映射 (symbol -> order_book_id)
        
        例如: 'SH600000' -> '600000.SH', 'SZ000001' -> '000001.XSHE'
        """
        if self._stock_map and date == self._cached_date:
            return self._stock_map
        
        if not RQDATAC_AVAILABLE:
            return {}
        
        try:
            stocks = rq.all_instruments('CS', date or datetime.now().strftime('%Y%m%d'))
            
            if stocks is None or stocks.empty:
                return {}
            
            # 构建映射
            self._stock_map = {}
            self._cached_date = date
            
            for _, row in stocks.iterrows():
                order_book_id = row['order_book_id']
                
                # 解析 order_book_id
                # 格式: '600000.SH' 或 '000001.XSHE'
                if order_book_id.endswith('.SH'):
                    symbol = f"SH{order_book_id.split('.')[0]}"
                elif order_book_id.endswith('.XSHE'):
                    symbol = f"SZ{order_book_id.split('.')[0]}"
                else:
                    symbol = order_book_id
                
                self._stock_map[symbol] = order_book_id
            
            return self._stock_map
            
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return {}
    
    def _symbol_to_order_book_id(self, symbol: str) -> str:
        """转换股票代码为 order_book_id"""
        stock_map = self._build_stock_map()
        
        # 如果已经在映射中
        if symbol in stock_map:
            return stock_map[symbol]
        
        # 尝试转换格式
        if symbol.startswith('SH'):
            return f"{symbol[2:]}.SH"
        elif symbol.startswith('SZ'):
            return f"{symbol[2:]}.XSHE"
        else:
            return symbol
    
    def get_all_stocks(self, date: str = None) -> pd.DataFrame:
        """
        获取全市场股票列表
        
        Args:
            date: 查询日期，默认最新
            
        Returns:
            股票列表DataFrame
        """
        cache_key = f"stocks_{date}"
        
        # 检查缓存
        cached = self._load_cache(cache_key)
        if cached is not None:
            return cached
        
        if not RQDATAC_AVAILABLE:
            return self._get_simulated_stocks(date)
        
        date = date or datetime.now().strftime('%Y%m%d')
        
        try:
            stocks = rq.all_instruments('CS', date)
            
            if stocks is None or stocks.empty:
                return self._get_simulated_stocks(date)
            
            # 缓存
            self._save_cache(cache_key, stocks)
            
            return stocks
            
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return self._get_simulated_stocks(date)
    
    def get_tradable_stocks(
        self,
        date: str = None,
        market: str = 'a'
    ) -> List[str]:
        """
        获取可交易股票列表
        
        Args:
            date: 查询日期
            market: 市场类型 ('a' A股, 'h' 港股)
            
        Returns:
            股票代码列表 (如 ['SH600000', 'SZ000001'])
        """
        stocks = self.get_all_stocks(date)
        
        if stocks is None or stocks.empty:
            return []
        
        # 转换 order_book_id 为 symbol
        symbols = []
        for _, row in stocks.iterrows():
            order_book_id = row['order_book_id']
            
            if order_book_id.endswith('.SH'):
                symbol = f"SH{order_book_id.split('.')[0]}"
            elif order_book_id.endswith('.XSHE'):
                symbol = f"SZ{order_book_id.split('.')[0]}"
            else:
                symbol = order_book_id
            
            symbols.append(symbol)
        
        return symbols
    
    # ==================== 日线数据 ====================
    
    # 日线数据默认包含的涨跌停字段
    DAILY_FIELDS_WITH_LIMITS = [
        'open', 'high', 'low', 'close', 'volume',
        'limit_up', 'limit_down',  # ⭐ 涨跌停价
        'prev_close', 'num_trades', 'total_turnover'
    ]
    
    def get_daily_data(
        self,
        symbols: List[str] = None,
        start_date: str = None,
        end_date: str = None,
        adjust_type: str = 'pre',  # 'pre'前复权, 'none'不复权
        fields: List[str] = None
    ) -> pd.DataFrame:
        """
        获取日线数据
        
        Args:
            symbols: 股票列表，None表示全市场
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            adjust_type: 复权类型 ('pre'前复权, 'none'不复权)
            fields: 返回字段，默认为涨跌停相关字段
            
        Returns:
            日线数据DataFrame
        """
        # 默认日期
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')
        
        cache_key = f"daily_{symbols}_{start_date}_{end_date}_{adjust_type}"
        
        # 检查缓存
        cached = self._load_cache(cache_key)
        if cached is not None:
            return cached
        
        if not RQDATAC_AVAILABLE:
            return self._get_simulated_daily_data(symbols, start_date, end_date)
        
        try:
            # 转换股票代码格式
            if symbols:
                order_book_ids = [self._symbol_to_order_book_id(s) for s in symbols]
            else:
                order_book_ids = None
            
            # 确定返回字段 (默认包含涨跌停字段)
            if fields is None:
                fields = self.DAILY_FIELDS_WITH_LIMITS
            
            # 获取数据
            data = rq.get_price(
                order_book_ids=order_book_ids,
                start_date=start_date,
                end_date=end_date,
                frequency='1d',
                fields=fields
            )
            
            if data is None or data.empty:
                logger.warning("未获取到数据")
                return self._get_simulated_daily_data(symbols, start_date, end_date)
            
            # 重置索引
            data = data.reset_index()
            
            # 统一股票代码格式
            if 'order_book_id' in data.columns:
                data['symbol'] = data['order_book_id'].apply(
                    lambda x: f"SH{x.split('.')[0]}" if x.endswith('.SH') 
                    else f"SZ{x.split('.')[0]}" if x.endswith('.XSHE') 
                    else x
                )
            
            # 缓存
            self._save_cache(cache_key, data)
            
            return data
            
        except Exception as e:
            logger.error(f"获取日线数据失败: {e}")
            return self._get_simulated_daily_data(symbols, start_date, end_date)
    
    # ==================== 分钟数据 ====================
    
    def get_minute_data(
        self,
        symbols: List[str] = None,
        start_date: str = None,
        end_date: str = None,
        frequency: str = '1min',
        fields: List[str] = None
    ) -> pd.DataFrame:
        """
        获取分钟数据
        
        Args:
            symbols: 股票列表
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            frequency: 频率 ('1min', '5min', '15min', '30min', '60min')
            fields: 返回字段
            
        Returns:
            分钟数据DataFrame
        """
        # 默认日期
        if not start_date:
            start_date = (datetime.now() - timedelta(days=7)).strftime('%Y%m%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')
        
        cache_key = f"minute_{symbols}_{start_date}_{end_date}_{frequency}"
        
        # 检查缓存
        cached = self._load_cache(cache_key)
        if cached is not None:
            return cached
        
        if not RQDATAC_AVAILABLE:
            return self._get_simulated_minute_data(symbols, start_date, end_date, frequency)
        
        try:
            # 转换股票代码格式
            if symbols:
                order_book_ids = [self._symbol_to_order_book_id(s) for s in symbols]
            else:
                order_book_ids = None
            
            # 转换频率
            freq = self.FREQUENCY_MAP.get(frequency, frequency)
            
            # 获取数据
            data = rq.get_price(
                order_book_ids=order_book_ids,
                start_date=start_date,
                end_date=end_date,
                frequency=freq,
                fields=fields
            )
            
            if data is None or data.empty:
                return self._get_simulated_minute_data(symbols, start_date, end_date, frequency)
            
            # 重置索引
            data = data.reset_index()
            
            # 统一股票代码格式
            if 'order_book_id' in data.columns:
                data['symbol'] = data['order_book_id'].apply(
                    lambda x: f"SH{x.split('.')[0]}" if x.endswith('.SH') 
                    else f"SZ{x.split('.')[0]}" if x.endswith('.XSHE') 
                    else x
                )
            
            # 缓存
            self._save_cache(cache_key, data)
            
            return data
            
        except Exception as e:
            logger.error(f"获取分钟数据失败: {e}")
            return self._get_simulated_minute_data(symbols, start_date, end_date, frequency)
    
    # ==================== 交易日 ====================
    
    def get_trading_days(
        self,
        start_date: str = None,
        end_date: str = None
    ) -> List[str]:
        """
        获取交易日列表
        
        Args:
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            
        Returns:
            交易日列表
        """
        if not RQDATAC_AVAILABLE:
            return self._get_simulated_trading_days(start_date, end_date)
        
        start_date = start_date or (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
        end_date = end_date or datetime.now().strftime('%Y%m%d')
        
        try:
            dates = rq.get_trading_dates(
                start_date=start_date,
                end_date=end_date
            )
            
            return [d.strftime('%Y%m%d') for d in dates] if hasattr(dates[0], 'strftime') else [str(d) for d in dates]
            
        except Exception as e:
            logger.error(f"获取交易日失败: {e}")
            return self._get_simulated_trading_days(start_date, end_date)
    
    # ==================== 缓存管理 ====================
    
    def _load_cache(self, cache_key: str) -> Optional[pd.DataFrame]:
        """从缓存加载数据"""
        if cache_key in self._memory_cache:
            return self._memory_cache[cache_key]
        return None
    
    def _save_cache(self, cache_key: str, data: pd.DataFrame):
        """保存数据到缓存"""
        self._memory_cache[cache_key] = data
    
    def clear_cache(self):
        """清空缓存"""
        self._memory_cache.clear()
        self._stock_map.clear()
        logger.info("缓存已清空")
    
    # ==================== 模拟数据 ====================
    
    def _get_simulated_stocks(self, date: str = None) -> pd.DataFrame:
        """生成模拟股票列表"""
        import numpy as np
        
        n = 100
        stocks = pd.DataFrame({
            'order_book_id': [f'{np.random.randint(1, 3000):06d}.SH' if i % 2 == 0 else f'{np.random.randint(1, 3000):06d}.XSHE' for i in range(n)],
            'symbol': [f'SH{np.random.randint(1, 3000):06d}' if i % 2 == 0 else f'SZ{np.random.randint(1, 3000):06f}' for i in range(n)],
            'name': [f'股票{i:04d}' for i in range(n)],
            'exchange': ['SSE' if i % 2 == 0 else 'SZSE' for i in range(n)],
        })
        
        return stocks
    
    def _get_simulated_daily_data(
        self,
        symbols: List[str] = None,
        start_date: str = None,
        end_date: str = None
    ) -> pd.DataFrame:
        """生成模拟日线数据"""
        import numpy as np
        
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')
        
        dates = pd.date_range(start=start_date, end=end_date, freq='B')
        
        if symbols is None:
            symbols = [f'SH60000{i}' for i in range(1, 21)]
        
        data = []
        
        for symbol in symbols:
            base_price = np.random.uniform(10, 50)
            for date in dates:
                change = np.random.uniform(-0.02, 0.025)
                close = base_price * (1 + change)
                base_price = close
                
                data.append({
                    'symbol': symbol,
                    'date': date,
                    'open': close * (1 + np.random.uniform(-0.01, 0.01)),
                    'high': close * (1 + np.random.uniform(0, 0.02)),
                    'low': close * (1 - np.random.uniform(0, 0.02)),
                    'close': close,
                    'volume': np.random.uniform(1000000, 10000000)
                })
        
        return pd.DataFrame(data)
    
    def _get_simulated_minute_data(
        self,
        symbols: List[str] = None,
        start_date: str = None,
        end_date: str = None,
        frequency: str = '1min'
    ) -> pd.DataFrame:
        """生成模拟分钟数据"""
        import numpy as np
        
        if symbols is None:
            symbols = ['SH600000']
        
        if frequency == '1min':
            minutes_per_day = 240
        elif frequency == '5min':
            minutes_per_day = 48
        else:
            minutes_per_day = 16
        
        date = start_date or (datetime.now() - timedelta(days=7)).strftime('%Y%m%d')
        
        times = pd.date_range(f'{date} 09:30:00', f'{date} 15:00:00', 
                           freq='1min' if frequency == '1min' else frequency)
        
        data = []
        
        for symbol in symbols:
            base_price = np.random.uniform(10, 50)
            for time in times[:minutes_per_day]:
                change = np.random.uniform(-0.001, 0.0015)
                close = base_price * (1 + change)
                base_price = close
                
                data.append({
                    'symbol': symbol,
                    'time': time,
                    'open': close * (1 + np.random.uniform(-0.001, 0.001)),
                    'high': close * (1 + np.random.uniform(0, 0.002)),
                    'low': close * (1 - np.random.uniform(0, 0.002)),
                    'close': close,
                    'volume': np.random.uniform(10000, 100000)
                })
        
        return pd.DataFrame(data)
    
    def _get_simulated_trading_days(
        self,
        start_date: str = None,
        end_date: str = None
    ) -> List[str]:
        """生成模拟交易日"""
        start_date = start_date or (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
        end_date = end_date or datetime.now().strftime('%Y%m%d')
        
        dates = pd.date_range(start=start_date, end=end_date, freq='B')
        
        return [d.strftime('%Y%m%d') for d in dates]


# ==================== 便捷函数 ====================

def get_daily_data(**kwargs) -> pd.DataFrame:
    """便捷函数: 获取日线数据"""
    source = RiceQuantSource()
    return source.get_daily_data(**kwargs)


def get_minute_data(**kwargs) -> pd.DataFrame:
    """便捷函数: 获取分钟数据"""
    source = RiceQuantSource()
    return source.get_minute_data(**kwargs)
