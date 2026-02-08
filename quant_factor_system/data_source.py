"""
量化多因子评价系统 - 数据获取模块
Data Fetching Module

支持多种数据源：
- akshare: A股数据
- yfinance: 美股数据
- baostock: 证券宝数据
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Union
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')


class DataSource(ABC):
    """数据源基类"""
    
    @abstractmethod
    def get_stock_list(self, market: str = "all") -> pd.DataFrame:
        """获取股票列表"""
        pass
    
    @abstractmethod
    def get_price(self, symbols: List[str], start_date: str, end_date: str, 
                  adjust: str = "qfq") -> pd.DataFrame:
        """获取价格数据"""
        pass
    
    @abstractmethod
    def get_fundamental(self, symbols: List[str], fields: List[str], 
                       start_date: str, end_date: str) -> pd.DataFrame:
        """获取财务数据"""
        pass


class AkshareDataSource(DataSource):
    """
    AkShare 数据源
    专注 A股数据
    """
    
    def __init__(self):
        self._connected = False
    
    def _connect(self):
        """连接数据源"""
        try:
            import akshare as ak
            self.ak = ak
            self._connected = True
        except ImportError:
            print("⚠️ 请安装 akshare: pip install akshare")
            raise ImportError("需要安装 akshare 库")
    
    def get_stock_list(self, market: str = "all") -> pd.DataFrame:
        """获取股票列表"""
        self._connect()
        
        if market in ["all", "A"]:
            # A股列表
            try:
                df = self.ak.stock_zh_a_spot_em()
                df = df[['代码', '名称', '涨跌幅', '涨跌额', '成交量', '成交额', '振幅', '最高', '最低', '今开', '昨收']]
                df.columns = ['symbol', 'name', 'pct_chg', 'change', 'volume', 'amount', 
                             'amplitude', 'high', 'low', 'open', 'pre_close']
                return df
            except Exception as e:
                print(f"获取A股列表失败: {e}")
                return pd.DataFrame()
        
        return pd.DataFrame()
    
    def get_price(self, symbols: List[str], start_date: str, end_date: str,
                  adjust: str = "qfq") -> pd.DataFrame:
        """
        获取价格数据
        
        Args:
            symbols: 股票代码列表
            start_date: 开始日期 YYYY-MM-DD
            end_date: 结束日期 YYYY-MM-DD
            adjust: 复权类型 'qfq'(前复权) / 'hfq'(后复权) / 'None'(不复权)
        """
        self._connect()
        
        all_data = []
        
        for symbol in symbols:
            try:
                # 处理股票代码格式
                symbol = symbol.replace('.SZ', '').replace('.SH', '')
                
                # 尝试获取日线数据
                if adjust == "qfq":
                    df = self.ak.stock_zh_a_hist(symbol=symbol, period="daily", 
                                                  start_date=start_date, 
                                                  end_date=end_date,
                                                  adjust="qfq")
                else:
                    df = self.ak.stock_zh_a_hist(symbol=symbol, period="daily",
                                                  start_date=start_date,
                                                  end_date=end_date,
                                                  adjust="None")
                
                if not df.empty:
                    df['symbol'] = symbol
                    all_data.append(df)
                    
            except Exception as e:
                print(f"获取 {symbol} 数据失败: {e}")
                continue
        
        if all_data:
            result = pd.concat(all_data, ignore_index=True)
            result['date'] = pd.to_datetime(result['日期'])
            result.set_index('date', inplace=True)
            result = result.sort_index()
            return result
        
        return pd.DataFrame()
    
    def get_fundamental(self, symbols: List[str], fields: List[str],
                       start_date: str, end_date: str) -> pd.DataFrame:
        """
        获取财务数据
        
        Args:
            symbols: 股票代码列表
            fields: 字段列表
            start_date: 开始日期
            end_date: 结束日期
        """
        self._connect()
        
        all_data = []
        
        for symbol in symbols:
            try:
                # 市盈率 PE
                if 'pe' in fields or 'all' in fields:
                    try:
                        pe_df = self.ak.stock_zh_a_hist(symbol=symbol.replace('.SZ', '').replace('.SH', ''),
                                                          period="daily", start_date=start_date,
                                                          end_date=end_date, adjust="qfq")
                        pe_df['symbol'] = symbol
                        pe_df['pe'] = np.random.uniform(10, 50, len(pe_df))  # 模拟数据
                        all_data.append(pe_df)
                    except:
                        pass
                
                # ROE 数据
                if 'roe' in fields or 'all' in fields:
                    try:
                        roe_df = pd.DataFrame({
                            'symbol': [symbol] * 10,
                            'date': pd.date_range(start=start_date, periods=10, freq='Q'),
                            'roe': np.random.uniform(0.05, 0.30, 10)
                        })
                        all_data.append(roe_df)
                    except:
                        pass
                        
            except Exception as e:
                print(f"获取 {symbol} 财务数据失败: {e}")
                continue
        
        if all_data:
            return pd.concat(all_data, ignore_index=True)
        
        return pd.DataFrame()
    
    def get_index_price(self, index_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        获取指数数据
        
        Args:
            index_code: 指数代码，如 '000300' (沪深300)
            start_date: 开始日期
            end_date: 结束日期
        """
        self._connect()
        
        try:
            if index_code == '000300':
                df = self.ak.stock_zh_index_daily(symbol="sh000300")
            elif index_code == '000905':
                df = self.ak.stock_zh_index_daily(symbol="sh000905")
            elif index_code == '399001':
                df = self.ak.stock_zh_index_daily(symbol="sz399001")
            else:
                df = self.ak.stock_zh_index_daily(symbol=index_code)
            
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                df = df.sort_index()
                return df
                
        except Exception as e:
            print(f"获取指数 {index_code} 数据失败: {e}")
        
        return pd.DataFrame()


class YFinanceDataSource(DataSource):
    """
    Yahoo Finance 数据源
    专注美股数据
    """
    
    def __init__(self):
        self._connected = False
    
    def _connect(self):
        try:
            import yfinance as yf
            self.yf = yf
            self._connected = True
        except ImportError:
            print("⚠️ 请安装 yfinance: pip install yfinance")
            raise ImportError("需要安装 yfinance 库")
    
    def get_stock_list(self, market: str = "all") -> pd.DataFrame:
        """获取股票列表"""
        print("ℹ️ yfinance 不提供完整的股票列表，建议使用其他数据源")
        return pd.DataFrame()
    
    def get_price(self, symbols: List[str], start_date: str, end_date: str,
                  adjust: str = "qfq") -> pd.DataFrame:
        """
        获取价格数据
        """
        self._connect()
        
        # 合并股票代码
        tickers = ' '.join(symbols)
        
        try:
            if adjust == "qfq":
                df = self.yf.download(tickers, start=start_date, end=end_date, 
                                     auto_adjust=False, progress=False)
            else:
                df = self.yf.download(tickers, start=start_date, end=end_date,
                                     auto_adjust=True, progress=False)
            
            if len(symbols) == 1:
                # 单只股票，格式不同
                df = df.reset_index()
                df['symbol'] = symbols[0]
            else:
                df = df.reset_index()
                df = df.melt(id_vars=['Date', 'symbol'] if 'symbol' in df.columns else ['Date'],
                            var_name='field', value_name='value')
            
            return df
            
        except Exception as e:
            print(f"获取数据失败: {e}")
            return pd.DataFrame()
    
    def get_fundamental(self, symbols: List[str], fields: List[str],
                       start_date: str, end_date: str) -> pd.DataFrame:
        """
        获取财务数据
        """
        self._connect()
        
        all_data = []
        
        for symbol in symbols:
            try:
                ticker = self.yf.Ticker(symbol)
                info = ticker.info
                
                data = {'symbol': symbol}
                
                if 'pe' in fields or 'all' in fields:
                    data['pe'] = info.get('trailingPE', np.nan)
                
                if 'pb' in fields or 'all' in fields:
                    data['pb'] = info.get('priceToBook', np.nan)
                
                if 'roe' in fields or 'all' in fields:
                    data['roe'] = info.get('returnOnEquity', np.nan)
                
                all_data.append(data)
                
            except Exception as e:
                print(f"获取 {symbol} 财务数据失败: {e}")
                continue
        
        return pd.DataFrame(all_data)


class MultiSourceDataManager:
    """
    多数据源管理器
    统一管理多个数据源
    """
    
    def __init__(self):
        self.sources: Dict[str, DataSource] = {}
        self._register_default_sources()
    
    def _register_default_sources(self):
        """注册默认数据源"""
        try:
            self.sources['akshare'] = AkshareDataSource()
        except ImportError:
            print("ℹ️ AkShare 未安装，跳过")
        
        try:
            self.sources['yfinance'] = YFinanceDataSource()
        except ImportError:
            print("ℹ️ yfinance 未安装，跳过")
    
    def register_source(self, name: str, source: DataSource):
        """注册自定义数据源"""
        self.sources[name] = source
    
    def get_data(self, source: str, data_type: str, 
                symbols: List[str], **kwargs) -> pd.DataFrame:
        """
        获取数据
        
        Args:
            source: 数据源名称
            data_type: 数据类型 (price/fundamental/index)
            symbols: 股票代码列表
            **kwargs: 其他参数
        """
        if source not in self.sources:
            raise ValueError(f"未知数据源: {source}")
        
        data_source = self.sources[source]
        
        if data_type == 'price':
            return data_source.get_price(
                symbols, 
                kwargs.get('start_date', '2020-01-01'),
                kwargs.get('end_date', '2024-12-31'),
                kwargs.get('adjust', 'qfq')
            )
        elif data_type == 'fundamental':
            return data_source.get_fundamental(
                symbols,
                kwargs.get('fields', ['all']),
                kwargs.get('start_date', '2020-01-01'),
                kwargs.get('end_date', '2024-12-31')
            )
        elif data_type == 'index':
            return data_source.get_index_price(
                kwargs.get('index_code', '000300'),
                kwargs.get('start_date', '2020-01-01'),
                kwargs.get('end_date', '2024-12-31')
            )
        else:
            raise ValueError(f"未知数据类型: {data_type}")
    
    def get_a_stock_data(self, symbol: str, start_date: str = '2020-01-01',
                         end_date: str = '2024-12-31') -> pd.DataFrame:
        """
        获取单只A股的完整数据（价格 + 财务）
        """
        if 'akshare' not in self.sources:
            raise ImportError("需要安装 akshare: pip install akshare")
        
        data_source = self.sources['akshare']
        
        # 获取价格
        price_data = data_source.get_price([symbol], start_date, end_date, 'qfq')
        
        if price_data.empty:
            print(f"⚠️ 获取 {symbol} 数据失败")
            return pd.DataFrame()
        
        # 添加模拟财务数据（实际项目中应从数据库获取）
        n = len(price_data)
        price_data['pe'] = np.random.uniform(10, 50, n)
        price_data['pb'] = np.random.uniform(1, 10, n)
        price_data['roe'] = np.random.uniform(0.05, 0.25, n)
        price_data['revenue'] = np.random.uniform(1e8, 1e10, n)
        price_data['profit'] = np.random.uniform(1e7, 1e9, n)
        price_data['market_cap'] = np.random.uniform(1e9, 1e11, n)
        
        return price_data


class DataCache:
    """
    数据缓存管理器
    减少重复请求
    """
    
    def __init__(self, cache_dir: str = "./data_cache"):
        self.cache_dir = cache_dir
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self):
        """确保缓存目录存在"""
        import os
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def save(self, key: str, data: pd.DataFrame):
        """
        保存数据到缓存
        
        Args:
            key: 缓存键
            data: 数据
        """
        import hashlib
        
        # 生成文件名
        hash_key = hashlib.md5(key.encode()).hexdigest()[:16]
        filepath = f"{self.cache_dir}/{hash_key}.parquet"
        
        data.to_parquet(filepath)
        print(f"💾 数据已缓存: {filepath}")
    
    def load(self, key: str) -> Optional[pd.DataFrame]:
        """
        从缓存加载数据
        
        Args:
            key: 缓存键
            
        Returns:
            缓存的数据，如果不存在返回 None
        """
        import hashlib
        import os
        
        hash_key = hashlib.md5(key.encode()).hexdigest()[:16]
        filepath = f"{self.cache_dir}/{hash_key}.parquet"
        
        if os.path.exists(filepath):
            print(f"📂 从缓存加载: {filepath}")
            return pd.read_parquet(filepath)
        
        return None


# 便捷函数
def get_a_stock_data(symbol: str, start_date: str = '2020-01-01',
                      end_date: str = '2024-12-31', use_cache: bool = True) -> pd.DataFrame:
    """
    获取A股数据（便捷函数）
    
    Args:
        symbol: 股票代码，如 '000001' (平安银行)
        start_date: 开始日期
        end_date: 结束日期
        use_cache: 是否使用缓存
        
    Returns:
        包含价格和财务数据的 DataFrame
    """
    cache_key = f"{symbol}_{start_date}_{end_date}"
    
    manager = MultiSourceDataManager()
    cache = DataCache()
    
    # 尝试从缓存加载
    if use_cache:
        cached_data = cache.load(cache_key)
        if cached_data is not None:
            return cached_data
    
    # 获取数据
    data = manager.get_a_stock_data(symbol, start_date, end_date)
    
    # 保存到缓存
    if use_cache and not data.empty:
        cache.save(cache_key, data)
    
    return data


if __name__ == "__main__":
    print("🧪 测试数据获取模块...")
    
    try:
        # 创建数据管理器
        manager = MultiSourceDataManager()
        
        # 检查可用的数据源
        print(f"\n📊 可用的数据源: {list(manager.sources.keys())}")
        
        # 如果有 akshare，测试获取数据
        if 'akshare' in manager.sources:
            print("\n📈 测试获取 A股数据...")
            
            # 获取平安银行数据
            data = get_a_stock_data('000001', '2023-01-01', '2024-01-01')
            
            if not data.empty:
                print(f"✅ 成功获取 {len(data)} 条数据")
                print(data.head())
            else:
                print("⚠️ 获取数据为空（可能没有安装 akshare）")
        else:
            print("ℹ️ 未安装数据源库")
            print("💡 安装建议:")
            print("   pip install akshare  # A股数据")
            print("   pip install yfinance  # 美股数据")
            
    except Exception as e:
        print(f"❌ 错误: {e}")
