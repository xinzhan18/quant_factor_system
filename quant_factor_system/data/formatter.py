"""
量化数据格式化模块
符合主流平台风格（米筐、聚宽、Wind）

数据格式标准:
1. 日线数据 (OHLCV) - MultiIndex [symbol, date]
2. 因子数据 - MultiIndex [symbol, date]
3. 复权因子 - MultiIndex [symbol, date]
4. 交易日历 - DatetimeIndex
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


# ========== 标准字段定义 ==========

# 日线数据标准字段
STANDARD_DAILY_FIELDS = {
    'open': '开盘价',
    'high': '最高价',
    'low': '最低价',
    'close': '收盘价',
    'volume': '成交量',
    'amount': '成交额',
    'turn': '换手率',
    'pct_chg': '涨跌幅',
    'change': '涨跌额',
    'pre_close': '昨收价',
    'adj_factor': '复权因子',
}

# 因子数据标准字段
STANDARD_FACTOR_FIELDS = [
    'pe', 'pb', 'ps', 'pcf',
    'roe', 'roa', 'gross_margin',
    'market_cap', 'circulating_market_cap',
    'momentum', 'reversal', 'volatility',
    'volume', 'turnover',
]


# ========== 数据类定义 ==========

@dataclass
class BarData:
    """
    单只股票日线数据
    """
    symbol: str
    date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    amount: Optional[float] = None
    turn: Optional[float] = None
    pct_chg: Optional[float] = None
    pre_close: Optional[float] = None
    adj_factor: Optional[float] = None
    
    def to_series(self) -> pd.Series:
        """转换为 Series"""
        return pd.Series({
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume,
            'amount': self.amount,
            'turn': self.turn,
            'pct_chg': self.pct_chg,
            'pre_close': self.pre_close,
            'adj_factor': self.adj_factor,
        })


@dataclass
class FactorData:
    """
    单只股票因子数据
    """
    symbol: str
    date: datetime
    factor_name: str
    value: float
    
    def to_series(self) -> pd.Series:
        """转换为 Series"""
        return pd.Series({
            'symbol': self.symbol,
            'date': self.date,
            'factor_name': self.factor_name,
            'value': self.value,
        })


# ========== 数据格式化器 ==========

class QuantDataFormatter:
    """
    量化数据格式化器
    
    支持主流平台数据格式转换:
    - 米筐 (RiceQuant)
    - 聚宽 (JoinQuant)
    - Wind
    - Tushare
    """
    
    def __init__(self, output_format: str = 'standard'):
        """
        初始化
        
        Args:
            output_format: 输出格式 ('standard', 'ricequant', 'joinquant', 'tushare')
        """
        self.output_format = output_format
        
        # 字段名映射
        self.field_mapping = self._get_field_mapping(output_format)
    
    def _get_field_mapping(self, fmt: str) -> Dict[str, str]:
        """获取字段名映射"""
        mappings = {
            'standard': {
                'open': 'open', 'high': 'high', 'low': 'low',
                'close': 'close', 'volume': 'volume', 'amount': 'amount',
                'turn': 'turn', 'pct_chg': 'pct_chg',
            },
            'ricequant': {
                'open': 'open', 'high': 'high', 'low': 'low',
                'close': 'close', 'volume': 'volume', 'amount': 'total_turnover',
                'turn': 'turnover_rate', 'pct_chg': 'pct_chg',
            },
            'joinquant': {
                'open': 'open', 'high': 'high', 'low': 'low',
                'close': 'close', 'volume': 'volume', 'amount': 'amount',
                'turn': 'turnover_rate', 'pct_chg': 'pct_chg',
            },
            'tushare': {
                'open': 'open', 'high': 'high', 'low': 'low',
                'close': 'close', 'volume': 'vol', 'amount': 'amount',
                'turn': 'turnover_rate', 'pct_chg': 'pct_chg',
            },
            'wind': {
                'open': 'open', 'high': 'high', 'low': 'low',
                'close': 'close', 'volume': 'vol', 'amount': 'amount',
                'turn': 'turn', 'pct_chg': 'pct_chg',
            }
        }
        return mappings.get(fmt, mappings['standard'])
    
    def format_daily_data(self, data: pd.DataFrame, 
                         symbol_col: str = 'symbol',
                         date_col: str = 'date') -> pd.DataFrame:
        """
        格式化日线数据
        
        Args:
            data: 原始数据
            symbol_col: 股票代码列名
            date_col: 日期列名
            
        Returns:
            格式化后的 DataFrame (MultiIndex: [symbol, date])
        """
        df = data.copy()
        
        # 检查是否已经是 MultiIndex
        if isinstance(df.index, pd.MultiIndex):
            # 已经 是 MultiIndex，直接使用
            df = df.sort_index()
        else:
            # 需要设置索引
            # 确保日期列是 datetime 类型
            if df[date_col].dtype == 'object':
                df[date_col] = pd.to_datetime(df[date_col])
            
            # 设置索引
            df = df.set_index([symbol_col, date_col])
        
        # 重命名字段
        df = df.rename(columns=self.field_mapping)
        
        # 选择标准字段
        standard_cols = ['open', 'high', 'low', 'close', 'volume', 
                       'amount', 'turn', 'pct_chg', 'pre_close', 'adj_factor']
        available_cols = [c for c in standard_cols if c in df.columns]
        df = df[available_cols]
        
        # 排序
        df = df.sort_index()
        
        return df
    
    def format_factor_data(self, data: pd.DataFrame,
                         factor_name: str = None,
                         symbol_col: str = 'symbol',
                         date_col: str = 'date',
                         value_col: str = 'value') -> pd.Series:
        """
        格式化因子数据
        
        Args:
            data: 原始数据
            factor_name: 因子名称（如果数据中已有可省略）
            symbol_col: 股票代码列名
            date_col: 日期列名
            value_col: 因子值列名
            
        Returns:
            格式化后的因子 Series (MultiIndex: [symbol, date])
        """
        df = data.copy()
        
        # 确保日期列是 datetime 类型
        if df[date_col].dtype == 'object':
            df[date_col] = pd.to_datetime(df[date_col])
        
        # 重命名因子列
        if factor_name:
            df = df.rename(columns={value_col: factor_name})
            value_col = factor_name
        
        # 设置索引
        df = df.set_index([symbol_col, date_col])
        
        # 只保留因子值列
        df = df[[value_col]]
        
        # 排序
        df = df.sort_index()
        
        # 转换为 Series
        return df[value_col]
    
    def create_daily_from_dict(self, bars: Dict[str, List[Dict]],
                              symbol_name: str = 'symbol',
                              date_name: str = 'date') -> pd.DataFrame:
        """
        从字典创建日线数据
        
        Args:
            bars: {symbol: [{date, open, high, low, close, volume, ...}, ...]}
            symbol_name: 股票代码键名
            date_name: 日期键名
            
        Returns:
            DataFrame (MultiIndex: [symbol, date])
        """
        records = []
        
        for symbol, bar_list in bars.items():
            for bar in bar_list:
                record = {
                    'symbol': symbol,
                    'date': bar.get(date_name),
                    'open': bar.get('open'),
                    'high': bar.get('high'),
                    'low': bar.get('low'),
                    'close': bar.get('close'),
                    'volume': bar.get('volume'),
                    'amount': bar.get('amount'),
                    'turn': bar.get('turn'),
                    'pct_chg': bar.get('pct_chg'),
                }
                records.append(record)
        
        df = pd.DataFrame(records)
        
        return self.format_daily_data(df)
    
    def merge_daily_with_factors(self, 
                               daily: pd.DataFrame,
                               factors: Dict[str, pd.Series]) -> pd.DataFrame:
        """
        合并日线和因子数据
        
        Args:
            daily: 日线数据 DataFrame
            factors: 因子字典 {factor_name: Series}
            
        Returns:
            合并后的 DataFrame
        """
        result = daily.copy()
        
        for factor_name, factor_series in factors.items():
            # 确保索引一致
            result[factor_name] = factor_series
        
        return result
    
    def create_factor_matrix(self, 
                           factors: Dict[str, pd.Series]) -> pd.DataFrame:
        """
        创建因子矩阵
        
        Args:
            factors: 因子字典 {factor_name: Series (MultiIndex)}
            
        Returns:
            因子矩阵 DataFrame (MultiIndex: [symbol, date])
        """
        # 合并所有因子
        df = pd.DataFrame(factors)
        
        # 排序
        df = df.sort_index()
        
        return df
    
    def calculate_returns(self, 
                        close: pd.Series,
                        periods: List[int] = [1, 5, 10, 20]) -> pd.DataFrame:
        """
        计算收益率
        
        Args:
            close: 收盘价 Series
            periods: 计算周期列表
            
        Returns:
            收益率 DataFrame
        """
        returns = {}
        
        for period in periods:
            returns[f'return_{period}d'] = close.pct_change(period)
        
        return pd.DataFrame(returns)
    
    def normalize_prices(self, 
                       price: pd.Series,
                       method: str = 'open') -> pd.Series:
        """
        标准化价格
        
        Args:
            price: 价格序列
            method: 标准化方法 ('open', 'prev_close', 'first')
            
        Returns:
            标准化后的价格序列
        """
        if method == 'open':
            # 以开盘价标准化
            return price / price.groupby(level='symbol').transform('first')
        elif method == 'prev_close':
            # 以前收盘标准化
            prev_close = price.groupby(level='symbol').shift(1)
            return price / (prev_close + 1e-8)
        else:
            return price / price.groupby(level='symbol').transform('first')


# ========== 因子数据生成器 ==========

class FactorDataGenerator:
    """
    因子数据生成器
    从日线数据生成常用因子
    """
    
    def __init__(self, daily_data: pd.DataFrame):
        """
        初始化
        
        Args:
            daily_data: 日线数据 (MultiIndex: [symbol, date])
        """
        self.daily = daily_data
        self.formatter = QuantDataFormatter()
    
    def get_price(self) -> pd.Series:
        """获取收盘价"""
        if 'close' in self.daily.columns:
            return self.daily['close']
        raise ValueError("数据必须包含 'close' 列")
    
    def get_volume(self) -> pd.Series:
        """获取成交量"""
        if 'volume' in self.daily.columns:
            return self.daily['volume']
        raise ValueError("数据必须包含 'volume' 列")
    
    # ========== 动量因子 ==========
    
    def momentum(self, period: int = 20) -> pd.Series:
        """
        动量因子
        
        Args:
            period: 回看周期
            
        Returns:
            动量因子值
        """
        close = self.get_price()
        return close.pct_change(period)
    
    def momentum_rolling(self, periods: List[int] = [5, 10, 20, 60]) -> pd.DataFrame:
        """
        多周期动量
        
        Args:
            periods: 周期列表
            
        Returns:
            多周期动量 DataFrame
        """
        close = self.get_price()
        
        result = {}
        for period in periods:
            result[f'momentum_{period}d'] = close.pct_change(period)
        
        return pd.DataFrame(result)
    
    def reversal(self, period: int = 20) -> pd.Series:
        """
        反转因子（动量的相反数）
        
        Args:
            period: 回看周期
            
        Returns:
            反转因子值
        """
        return -self.momentum(period)
    
    # ========== 波动率因子 ==========
    
    def volatility(self, period: int = 20) -> pd.Series:
        """
        波动率因子
        
        Args:
            period: 计算周期
            
        Returns:
            波动率因子值（负值，越低越好）
        """
        close = self.get_price()
        returns = close.pct_change()
        
        # 按股票分组计算滚动标准差
        if isinstance(returns.index, pd.MultiIndex):
            vol = returns.groupby(level='symbol').transform(
                lambda x: x.rolling(period, min_periods=5).std()
            )
        else:
            vol = returns.rolling(period, min_periods=5).std()
        
        return -vol  # 低波动是优势
    
    def atr(self, period: int = 14) -> pd.Series:
        """
        真实波幅 (Average True Range)
        
        Args:
            period: 计算周期
            
        Returns:
            ATR 因子值
        """
        high = self.daily['high']
        low = self.daily['low']
        close = self.get_price()
        
        # True Range
        prev_close = close.groupby(level='symbol').shift(1)
        tr1 = high - low
        tr2 = abs(high - prev_close)
        tr3 = abs(low - prev_close)
        
        if isinstance(tr1.index, pd.MultiIndex):
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        else:
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # ATR
        if isinstance(tr.index, pd.MultiIndex):
            atr = tr.groupby(level='symbol').transform(
                lambda x: x.rolling(period, min_periods=5).mean()
            )
        else:
            atr = tr.rolling(period, min_periods=5).mean()
        
        return atr
    
    # ========== 成交量因子 ==========
    
    def volume_ratio(self, period: int = 20) -> pd.Series:
        """
        量比
        
        Args:
            period: 计算周期
            
        Returns:
            量比因子值
        """
        volume = self.get_volume()
        
        # 平均成交量
        if isinstance(volume.index, pd.MultiIndex):
            avg_vol = volume.groupby(level='symbol').transform(
                lambda x: x.rolling(period, min_periods=5).mean()
            )
        else:
            avg_vol = volume.rolling(period, min_periods=5).mean()
        
        return volume / (avg_vol + 1e-8)
    
    def turnover(self, period: int = 20) -> pd.Series:
        """
        换手率因子
        
        Args:
            period: 计算周期
            
        Returns:
            换手率因子值（负值，越低越好）
        """
        if 'turn' in self.daily.columns:
            turn = self.daily['turn']
        else:
            volume = self.get_volume()
            # 简化计算
            if isinstance(volume.index, pd.MultiIndex):
                avg_vol = volume.groupby(level='symbol').transform(
                    lambda x: x.rolling(period, min_periods=5).mean()
                )
            else:
                avg_vol = volume.rolling(period, min_periods=5).mean()
            turn = volume / (avg_vol + 1e-8)
        
        return -turn  # 低换手是优势
    
    # ========== 价值因子 ==========
    
    def pe(self, pe_series: pd.Series) -> pd.Series:
        """
        市盈率因子
        
        Args:
            pe_series: PE Series (MultiIndex)
            
        Returns:
            PE 因子值（负值，越低越好）
        """
        return -pe_series
    
    def pb(self, pb_series: pd.Series) -> pd.Series:
        """
        市净率因子
        
        Args:
            pb_series: PB Series (MultiIndex)
            
        Returns:
            PB 因子值（负值，越低越好）
        """
        return -pb_series
    
    # ========== 质量因子 ==========
    
    def roe(self, roe_series: pd.Series) -> pd.Series:
        """
        ROE 因子
        
        Args:
            roe_series: ROE Series (MultiIndex)
            
        Returns:
            ROE 因子值
        """
        return roe_series
    
    def gross_margin(self, gross_margin_series: pd.Series) -> pd.Series:
        """
        毛利率因子
        
        Args:
            gross_margin_series: 毛利率 Series (MultiIndex)
            
        Returns:
            毛利率因子值
        """
        return gross_margin_series
    
    # ========== 规模因子 ==========
    
    def size(self, market_cap: pd.Series) -> pd.Series:
        """
        规模因子
        
        Args:
            market_cap: 市值 Series (MultiIndex)
            
        Returns:
            规模因子值（取对数）
        """
        return np.log(market_cap)
    
    # ========== 综合因子 ==========
    
    def generate_all_factors(self, 
                           fundamental: Dict[str, pd.Series] = None) -> pd.DataFrame:
        """
        生成所有标准因子
        
        Args:
            fundamental: 财务数据字典 {'pe': Series, 'pb': Series, 'roe': Series, ...}
            
        Returns:
            因子矩阵 DataFrame
        """
        factors = {}
        
        # 动量因子
        factors['momentum_20d'] = self.momentum(20)
        factors['momentum_60d'] = self.momentum(60)
        factors['momentum_120d'] = self.momentum(120)
        
        # 波动率因子
        factors['volatility_20d'] = self.volatility(20)
        
        # 成交量因子
        factors['volume_ratio_20d'] = self.volume_ratio(20)
        factors['turnover_20d'] = self.turnover(20)
        
        # 财务因子
        if fundamental:
            if 'pe' in fundamental:
                factors['pe'] = self.pe(fundamental['pe'])
            if 'pb' in fundamental:
                factors['pb'] = self.pb(fundamental['pb'])
            if 'roe' in fundamental:
                factors['roe'] = self.roe(fundamental['roe'])
            if 'gross_margin' in fundamental:
                factors['gross_margin'] = self.gross_margin(fundamental['gross_margin'])
            if 'market_cap' in fundamental:
                factors['size'] = self.size(fundamental['market_cap'])
        
        # 合并为 DataFrame
        factor_df = pd.DataFrame(factors)
        
        # 排序
        factor_df = factor_df.sort_index()
        
        return factor_df


# ========== 便捷函数 ==========

def format_daily_data(data: pd.DataFrame,
                     symbol_col: str = 'symbol',
                     date_col: str = 'date') -> pd.DataFrame:
    """
    快速格式化日线数据
    """
    formatter = QuantDataFormatter()
    return formatter.format_daily_data(data, symbol_col, date_col)


def format_factor_data(data: pd.DataFrame,
                     factor_name: str = None,
                     symbol_col: str = 'symbol',
                     date_col: str = 'date',
                     value_col: str = 'value') -> pd.Series:
    """
    快速格式化因子数据
    """
    formatter = QuantDataFormatter()
    return formatter.format_factor_data(data, factor_name, symbol_col, date_col, value_col)


def create_factor_matrix(factors: Dict[str, pd.Series]) -> pd.DataFrame:
    """
    快速创建因子矩阵
    """
    formatter = QuantDataFormatter()
    return formatter.create_factor_matrix(factors)


if __name__ == '__main__':
    print("=" * 60)
    print("🧪 测试数据格式化模块")
    print("=" * 60)
    
    # 创建测试数据
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=100, freq='B')
    symbols = ['SH600000', 'SZ000001', 'SH600519']
    
    index_tuples = []
    for symbol in symbols:
        for date in dates:
            index_tuples.append((symbol, date))
    
    multi_index = pd.MultiIndex.from_tuples(index_tuples, names=['symbol', 'date'])
    
    # 日线数据
    daily_data = pd.DataFrame({
        'open': np.random.uniform(10, 100, len(multi_index)),
        'high': np.random.uniform(10, 100, len(multi_index)),
        'low': np.random.uniform(10, 100, len(multi_index)),
        'close': np.random.uniform(10, 100, len(multi_index)),
        'volume': np.random.uniform(1e6, 1e8, len(multi_index)),
        'amount': np.random.uniform(1e7, 1e9, len(multi_index)),
    }, index=multi_index)
    
    print(f"\n1. 日线数据: {daily_data.shape}")
    print(daily_data.head())
    
    # 测试格式化
    print("\n2. 测试格式化:")
    formatter = QuantDataFormatter('standard')
    formatted = formatter.format_daily_data(daily_data)
    print(f"   格式化后: {formatted.shape}")
    
    # 测试因子生成
    print("\n3. 测试因子生成:")
    generator = FactorDataGenerator(daily_data)
    
    momentum = generator.momentum(20)
    print(f"   动量因子: {momentum.shape}")
    
    volatility = generator.volatility(20)
    print(f"   波动率因子: {volatility.shape}")
    
    volume_ratio = generator.volume_ratio(20)
    print(f"   量比因子: {volume_ratio.shape}")
    
    # 生成所有因子
    print("\n4. 生成所有因子:")
    fundamental = {
        'pe': pd.Series(np.random.uniform(10, 50, len(multi_index)), index=multi_index),
        'roe': pd.Series(np.random.uniform(0.05, 0.25, len(multi_index)), index=multi_index),
    }
    
    factors = generator.generate_all_factors(fundamental)
    print(f"   因子矩阵: {factors.shape}")
    print(f"   因子列表: {list(factors.columns)}")
    
    # 测试合并
    print("\n5. 测试合并日线和因子:")
    merged = generator.daily.copy()
    merged['momentum'] = momentum
    merged['volatility'] = volatility
    print(f"   合并后: {merged.shape}")
    
    print("\n" + "=" * 60)
    print("✅ 数据格式化模块测试完成!")
    print("=" * 60)
