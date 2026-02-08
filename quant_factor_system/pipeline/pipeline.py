"""
因子管道模块
基于 Zipline Pipeline 架构设计

核心特性:
- 记忆化: 相同参数返回相同实例
- 惰性计算: 按需计算
- DAG 执行: 自动处理依赖
- 窗口支持: 滚动窗口计算
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from datetime import datetime
import hashlib
import weakref


# ========== 类型定义 ==========

@dataclass
class FactorResult:
    """因子计算结果"""
    name: str
    data: pd.Series
    computed_at: datetime = field(default_factory=datetime.now)


# ========== Factor 基类 ==========

class Factor(ABC):
    """
    因子基类
    
    特性:
    - 记忆化: 相同参数返回相同实例
    - 窗口支持: 自动处理滚动窗口
    - 组合: 支持因子运算
    """
    
    # 子类重写
    name: str = "Factor"
    window_safe: bool = False
    
    def __init__(self, 
                 window_length: int = None,
                 inputs: Dict[str, pd.DataFrame] = None):
        """
        初始化
        
        Args:
            window_length: 窗口长度
            inputs: 输入数据字典
        """
        self.window_length = window_length
        self.inputs = inputs or {}
        self._cache = {}
        self._identity = None
    
    def __repr__(self):
        return f"{self.__class__.__name__}(window_length={self.window_length})"
    
    def __call__(self, data: pd.DataFrame = None) -> pd.Series:
        """计算因子值 (带缓存)"""
        # 使用输入数据
        inputs = data if data is not None else self.inputs
        
        # 生成缓存键
        cache_key = self._get_cache_key(inputs)
        
        # 检查缓存
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # 计算
        result = self.compute(inputs)
        
        # 缓存
        self._cache[cache_key] = result
        
        return result
    
    def _get_cache_key(self, inputs: Dict[str, pd.DataFrame]) -> str:
        """生成缓存键"""
        key_data = {
            'class': self.__class__.__name__,
            'window_length': self.window_length,
        }
        
        # 加入输入数据的形状信息
        if inputs:
            for name, df in inputs.items():
                if isinstance(df, pd.DataFrame):
                    key_data[f'input_{name}'] = (df.shape, df.columns.tolist())
        
        key_str = str(sorted(key_data.items()))
        return hashlib.md5(key_str.encode()).hexdigest()
    
    @abstractmethod
    def compute(self, inputs: Dict[str, pd.DataFrame]) -> pd.Series:
        """计算因子值 (子类重写)"""
        pass
    
    # ========== 运算符重载 ==========
    
    def __add__(self, other: Union['Factor', float, int]) -> 'CombinedFactor':
        return CombinedFactor(self, other, '+')
    
    def __sub__(self, other: Union['Factor', float, int]) -> 'CombinedFactor':
        return CombinedFactor(self, other, '-')
    
    def __mul__(self, other: Union['Factor', float, int]) -> 'CombinedFactor':
        return CombinedFactor(self, other, '*')
    
    def __truediv__(self, other: Union['Factor', float, int]) -> 'CombinedFactor':
        return CombinedFactor(self, other, '/')
    
    def __radd__(self, other: float) -> 'CombinedFactor':
        return CombinedFactor(self, other, '+')
    
    def __rmul__(self, other: float) -> 'CombinedFactor':
        return CombinedFactor(self, other, '*')
    
    # ========== 窗口方法 ==========
    
    def rolling(self, window: int) -> 'WindowedFactor':
        """创建滚动窗口因子"""
        return WindowedFactor(self, window)
    
    def rank(self, method: str = 'average') -> 'RankFactor':
        """排名因子"""
        return RankFactor(self, method)
    
    def zscore(self) -> 'ZScoreFactor':
        """标准化因子"""
        return ZScoreFactor(self)
    
    def clip(self, lower: float = None, upper: float = None) -> 'ClipFactor':
        """裁剪因子"""
        return ClipFactor(self, lower, upper)


# ========== 组合因子 ==========

class CombinedFactor(Factor):
    """组合因子 (支持运算)"""
    
    def __init__(self, 
                 left: Factor,
                 right: Union[Factor, float, int],
                 operator: str):
        super().__init__()
        self.left = left
        self.right = right
        self.operator = operator
        self.name = f"({left.name} {operator} {right})"
    
    def compute(self, inputs: Dict[str, pd.DataFrame]) -> pd.Series:
        left_values = self.left(inputs)
        
        if isinstance(self.right, Factor):
            right_values = self.right(inputs)
        else:
            right_values = self.right
        
        # 执行运算
        if self.operator == '+':
            return left_values + right_values
        elif self.operator == '-':
            return left_values - right_values
        elif self.operator == '*':
            return left_values * right_values
        elif self.operator == '/':
            return left_values / (right_values + 1e-8)
        else:
            raise ValueError(f"Unknown operator: {self.operator}")


# ========== 变换因子 ==========

class WindowedFactor(Factor):
    """窗口变换因子"""
    
    def __init__(self, factor: Factor, window: int):
        super().__init__(window_length=window)
        self.factor = factor
        self.name = f"{factor.name}.rolling({window})"
    
    def compute(self, inputs: Dict[str, pd.DataFrame]) -> pd.Series:
        values = self.factor(inputs)
        return values.rolling(window=self.window_length).mean()


class RankFactor(Factor):
    """排名因子"""
    
    def __init__(self, factor: Factor, method: str = 'average'):
        super().__init__()
        self.factor = factor
        self.method = method
        self.name = f"{factor.name}.rank({method})"
    
    def compute(self, inputs: Dict[str, pd.DataFrame]) -> pd.Series:
        values = self.factor(inputs)
        return values.rank(method=self.method)


class ZScoreFactor(Factor):
    """Z-Score 标准化因子"""
    
    def __init__(self, factor: Factor):
        super().__init__()
        self.factor = factor
        self.name = f"{factor.name}.zscore()"
    
    def compute(self, inputs: Dict[str, pd.DataFrame]) -> pd.Series:
        values = self.factor(inputs)
        return (values - values.mean()) / (values.std() + 1e-8)


class ClipFactor(Factor):
    """裁剪因子"""
    
    def __init__(self, factor: Factor, lower: float = None, upper: float = None):
        super().__init__()
        self.factor = factor
        self.lower = lower
        self.upper = upper
        self.name = f"{factor.name}.clip({lower}, {upper})"
    
    def compute(self, inputs: Dict[str, pd.DataFrame]) -> pd.Series:
        values = self.factor(inputs)
        return values.clip(self.lower, self.upper)


# ========== 基础因子模板 ==========

class Returns(Factor):
    """收益率因子"""
    
    name = "Returns"
    
    def __init__(self, 
                 price_col: str = 'close',
                 period: int = 1):
        super().__init__()
        self.price_col = price_col
        self.period = period
        self.name = f"Returns({period}d)"
    
    def compute(self, inputs: Dict[str, pd.DataFrame]) -> pd.Series:
        prices = inputs.get(self.price_col)
        if prices is None:
            return pd.Series(index=prices.index if hasattr(prices, 'index') else None)
        
        if isinstance(prices, pd.DataFrame):
            # DataFrame with MultiIndex
            return prices[self.price_col].groupby(level='symbol').pct_change(self.period)
        else:
            # Series (单资产)
            return prices.pct_change(self.period)


class Momentum(Factor):
    """动量因子"""
    
    name = "Momentum"
    
    def __init__(self, 
                 price_col: str = 'close',
                 window: int = 20):
        super().__init__(window_length=window)
        self.price_col = price_col
        self.window = window
        self.name = f"Momentum({window}d)"
    
    def compute(self, inputs: Dict[str, pd.DataFrame]) -> pd.Series:
        prices = inputs.get(self.price_col)
        if prices is None:
            return pd.Series(index=prices.index if hasattr(prices, 'index') else None)
        
        if isinstance(prices, pd.DataFrame):
            # DataFrame with MultiIndex
            return prices[self.price_col].groupby(level='symbol').apply(
                lambda x: x / x.shift(self.window) - 1
            )
        else:
            # Series (单资产)
            return prices / prices.shift(self.window) - 1


class RSI(Factor):
    """相对强弱指标"""
    
    name = "RSI"
    
    def __init__(self, window: int = 14):
        super().__init__(window_length=window + 1)
        self.window = window
        self.name = f"RSI({window})"
    
    def compute(self, inputs: Dict[str, pd.DataFrame]) -> pd.Series:
        close = inputs.get('close')
        if close is None:
            return pd.Series(index=close.index if hasattr(close, 'index') else None)
        
        # 处理 Series (单资产)
        if isinstance(close, pd.Series):
            delta = close.diff()
            
            gain = delta.copy()
            loss = delta.copy()
            gain[gain < 0] = 0
            loss[loss > 0] = 0
            
            avg_gain = gain.rolling(window=self.window, min_periods=1).mean()
            avg_loss = loss.abs().rolling(window=self.window, min_periods=1).mean()
            
            rs = avg_gain / (avg_loss + 1e-8)
            rsi = 100 - (100 / (1 + rs))
            
            return rsi
        else:
            # DataFrame - 暂不支持
            return pd.Series()


class MovingAverage(Factor):
    """移动平均"""
    
    name = "MA"
    
    def __init__(self, 
                 price_col: str = 'close',
                 window: int = 20,
                 etype: str = 'simple'):
        super().__init__(window_length=window)
        self.price_col = price_col
        self.window = window
        self.etype = etype
        self.name = f"MA({window},{etype})"
    
    def compute(self, inputs: Dict[str, pd.DataFrame]) -> pd.Series:
        prices = inputs.get(self.price_col)
        if prices is None:
            return pd.Series(index=prices.index if hasattr(prices, 'index') else None)
        
        if isinstance(prices, pd.DataFrame):
            prices = prices['close']
        
        # 检查是否为 MultiIndex Series
        is_multi = isinstance(prices.index, pd.MultiIndex)
        
        if self.etype == 'simple':
            if is_multi:
                return prices.groupby(level='symbol').rolling(
                    window=self.window, min_periods=1
                ).mean()
            else:
                return prices.rolling(window=self.window, min_periods=1).mean()
        elif self.etype == 'exponential':
            if is_multi:
                return prices.groupby(level='symbol').ewm(
                    span=self.window, adjust=False
                ).mean()
            else:
                return prices.ewm(span=self.window, adjust=False).mean()
        else:
            raise ValueError(f"Unknown MA type: {self.etype}")


class Volatility(Factor):
    """波动率因子"""
    
    name = "Volatility"
    
    def __init__(self, 
                 returns_col: str = 'returns',
                 window: int = 20):
        super().__init__(window_length=window)
        self.returns_col = returns_col
        self.window = window
        self.name = f"Volatility({window}d)"
    
    def compute(self, inputs: Dict[str, pd.DataFrame]) -> pd.Series:
        returns = inputs.get(self.returns_col)
        if returns is None:
            # 计算收益率
            close = inputs.get('close')
            if close is None:
                return pd.Series(index=close.index if hasattr(close, 'index') else None)
            
            if isinstance(close, pd.DataFrame):
                returns = close['close'].groupby(level='symbol').pct_change()
            else:
                returns = close.pct_change()
        
        # 检查是否为 MultiIndex Series
        is_multi = isinstance(returns.index, pd.MultiIndex)
        
        if is_multi:
            return returns.groupby(level='symbol').rolling(
                window=self.window, min_periods=1
            ).std() * np.sqrt(252)
        else:
            return returns.rolling(window=self.window, min_periods=1).std() * np.sqrt(252)


class AverageDollarVolume(Factor):
    """平均成交额"""
    
    name = "ADV"
    
    def __init__(self, 
                 volume_col: str = 'volume',
                 price_col: str = 'close',
                 window: int = 20):
        super().__init__(window_length=window)
        self.volume_col = volume_col
        self.price_col = price_col
        self.window = window
        self.name = f"ADV({window}d)"
    
    def compute(self, inputs: Dict[str, pd.DataFrame]) -> pd.Series:
        volume = inputs.get(self.volume_col)
        price = inputs.get(self.price_col)
        
        if volume is None or price is None:
            return pd.Series()
        
        dollar_volume = volume * price
        
        return dollar_volume.groupby(level='symbol').rolling(
            window=self.window, min_periods=1
        ).mean()


# ========== Pipeline 引擎 ==========

class Pipeline:
    """
    因子管道
    
    支持:
    - 添加多个因子
    - 设置过滤器
    - 设置输出列
    """
    
    def __init__(self, name: str = "Pipeline"):
        self.name = name
        self.factors: Dict[str, Factor] = {}
        self.filters: Dict[str, 'Filter'] = {}
        self.screens: List[Factor] = []
    
    def add_factor(self, 
                   name: str, 
                   factor: Factor,
                   output_name: str = None) -> 'Pipeline':
        """添加因子"""
        output = output_name or name
        self.factors[output] = factor
        return self
    
    def add_filter(self, 
                   name: str, 
                   filter_expr: 'Filter') -> 'Pipeline':
        """添加过滤器"""
        self.filters[name] = filter_expr
        return self
    
    def set_screen(self, screen: 'Filter') -> 'Pipeline':
        """设置筛选条件"""
        self.screens.append(screen)
        return self
    
    def run(self, 
            data: pd.DataFrame,
            start_date: str = None,
            end_date: str = None) -> pd.DataFrame:
        """
        执行 Pipeline
        
        Args:
            data: 输入数据
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            结果 DataFrame
        """
        # 筛选日期
        if start_date or end_date:
            if isinstance(data.index, pd.MultiIndex):
                dates = data.index.get_level_values('date')
                mask = True
                if start_date:
                    mask &= dates >= pd.Timestamp(start_date)
                if end_date:
                    mask &= dates <= pd.Timestamp(end_date)
                data = data[mask]
        
        results = {}
        
        # 计算所有因子
        for name, factor in self.factors.items():
            try:
                results[name] = factor(data)
            except Exception as e:
                print(f"计算因子 {name} 失败: {e}")
                results[name] = pd.Series(index=data.index)
        
        # 应用过滤器
        for name, filter_expr in self.filters.items():
            try:
                results[name] = filter_expr(data)
            except Exception as e:
                print(f"计算过滤器 {name} 失败: {e}")
        
        # 构建结果
        result_df = pd.DataFrame(results)
        
        # 应用筛选
        if self.screens:
            screen_mask = self.screens[0](data)
            result_df = result_df[screen_mask]
        
        return result_df


# ========== Filter 基类 ==========

class Filter(ABC):
    """过滤器基类"""
    
    def __init__(self, name: str = "Filter"):
        self.name = name
    
    @abstractmethod
    def compute(self, inputs: Dict[str, pd.DataFrame]) -> pd.Series:
        """计算过滤条件"""
        pass
    
    def __call__(self, data: pd.DataFrame) -> pd.Series:
        return self.compute(data)
    
    def __and__(self, other: 'Filter') -> 'CombinedFilter':
        return CombinedFilter(self, other, '&')
    
    def __or__(self, other: 'Filter') -> 'CombinedFilter':
        return CombinedFilter(self, other, '|')
    
    def __invert__(self) -> 'InvertedFilter':
        return InvertedFilter(self)


class CombinedFilter(Filter):
    """组合过滤器"""
    
    def __init__(self, left: Filter, right: Filter, operator: str):
        super().__init__()
        self.left = left
        self.right = right
        self.operator = operator
    
    def compute(self, inputs: Dict[str, pd.DataFrame]) -> pd.Series:
        left_mask = self.left(inputs)
        right_mask = self.right(inputs)
        
        if self.operator == '&':
            return left_mask & right_mask
        elif self.operator == '|':
            return left_mask | right_mask
        else:
            raise ValueError(f"Unknown operator: {self.operator}")


class InvertedFilter(Filter):
    """反转过滤器"""
    
    def __init__(self, filter_expr: Filter):
        super().__init__()
        self.filter = filter_expr
    
    def compute(self, inputs: Dict[str, pd.DataFrame]) -> pd.Series:
        return ~self.filter(inputs)


class FactorFilter(Filter):
    """基于因子的过滤器"""
    
    def __init__(self, 
                 factor: Factor,
                 threshold: float,
                 operator: str = '>'):
        super().__init__()
        self.factor = factor
        self.threshold = threshold
        self.operator = operator
        self.name = f"{factor.name} {operator} {threshold}"
    
    def compute(self, inputs: Dict[str, pd.DataFrame]) -> pd.Series:
        values = self.factor(inputs)
        
        if self.operator == '>':
            return values > self.threshold
        elif self.operator == '>=':
            return values >= self.threshold
        elif self.operator == '<':
            return values < self.threshold
        elif self.operator == '<=':
            return values <= self.threshold
        elif self.operator == '==':
            return values == self.threshold
        else:
            raise ValueError(f"Unknown operator: {self.operator}")


class PercentileFilter(Filter):
    """百分位过滤器"""
    
    def __init__(self, 
                 factor: Factor,
                 min_percentile: float = 0,
                 max_percentile: float = 100):
        super().__init__()
        self.factor = factor
        self.min_pct = min_percentile
        self.max_pct = max_percentile
        self.name = f"Percentile({min_percentile}-{max_percentile})"
    
    def compute(self, inputs: Dict[str, pd.DataFrame]) -> pd.Series:
        values = self.factor(inputs)
        
        min_val = np.nanpercentile(values, self.min_pct)
        max_val = np.nanpercentile(values, self.max_pct)
        
        return (values >= min_val) & (values <= max_val)


# ========== 便捷函数 ==========

def make_pipeline(name: str = "Pipeline") -> Pipeline:
    """创建 Pipeline"""
    return Pipeline(name)


if __name__ == '__main__':
    print("=" * 60)
    print("🧪 测试因子管道模块")
    print("=" * 60)
    
    import numpy as np
    
    # 创建测试数据
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=100, freq='B')
    symbols = ['SH600000', 'SZ000001', 'SH600519']
    
    index_tuples = []
    for date in dates:
        for symbol in symbols:
            index_tuples.append((date, symbol))
    
    multi_index = pd.MultiIndex.from_tuples(index_tuples, names=['date', 'symbol'])
    
    # 价格数据
    close = pd.Series(
        np.random.uniform(10, 100, len(multi_index)),
        index=multi_index,
        name='close'
    )
    
    volume = pd.Series(
        np.random.uniform(1e6, 1e8, len(multi_index)),
        index=multi_index,
        name='volume'
    )
    
    print(f"\n1. 测试数据: {close.shape}")
    
    # 创建 Pipeline
    print("\n2. 创建 Pipeline:")
    pipe = Pipeline("TestPipeline")
    
    # 添加因子
    pipe.add_factor('momentum', Momentum(close='close', window=20))
    pipe.add_factor('rsi', RSI(window=14))
    pipe.add_factor('ma20', MovingAverage(close='close', window=20))
    pipe.add_factor('volatility', Volatility(window=20))
    
    # 添加过滤器
    pipe.add_filter('high_rsi', FactorFilter(RSI(window=14), 70, '<'))
    pipe.add_filter('low_vol', FactorFilter(Volatility(window=20), 0.3, '<'))
    
    # 运行
    print("\n3. 执行 Pipeline:")
    inputs = {'close': close, 'volume': volume}
    result = pipe.run(inputs)
    
    print(f"   结果形状: {result.shape}")
    print(f"   列: {list(result.columns)}")
    print(result.head(10))
    
    # 测试因子组合
    print("\n4. 测试因子组合:")
    combined = Momentum(close='close', window=20) + RSI(window=14)
    combined_result = combined(inputs)
    print(f"   组合因子结果: {combined_result.shape}")
    
    # 测试滚动窗口
    print("\n5. 测试滚动窗口:")
    ma_factor = MovingAverage(close='close', window=20)
    rolling_ma = ma_factor.rolling(60)
    rolling_result = rolling_ma(inputs)
    print(f"   滚动 MA 结果: {rolling_result.shape}")
    
    # 测试过滤
    print("\n6. 测试过滤器:")
    high_momentum = FactorFilter(Momentum(close='close', window=20), 0.05, '>')
    mask = high_momentum(inputs)
    print(f"   高动量过滤: {mask.sum()} / {len(mask)} ({mask.mean():.2%})")
    
    print("\n" + "=" * 60)
    print("✅ 因子管道模块测试完成!")
    print("=" * 60)
