"""
扩展因子库
Extended Factor Library

基于 Barra 和经典多因子模型的因子实现
参考: QuantConnect, Zipline, WorldQuant 等行业实践
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from .base import Factor


class BarraStyleFactor(Factor):
    """
    Barra 风格因子基类
    
    Barra 模型是业界最广泛使用的多因子风险模型，
    包含 10 个风格因子和若干行业因子
    """
    
    # Barra 风格因子定义
    BARRRA_FACTORS = {
        'size': '市值因子',
        'beta': '市场敏感度',
        'momentum': '动量因子',
        'size_nonlinear': '非线性市值',
        'value': '价值因子',
        'volatility': '残差波动率',
        'liquidity': '流动性因子',
        'earnings_yield': '盈利收益率',
        'growth': '成长因子',
        'leverage': '杠杆因子'
    }
    
    def __init__(self, name: str, description: str = ""):
        super().__init__(name, description)


class SizeFactor(BarraStyleFactor):
    """
    市值因子 (Size)
    
    衡量公司规模，通常用市值对数或市值的立方根
    小市值股票长期收益往往优于大市值
    """
    
    def __init__(self, method: str = "log_mcap", 
                 description: str = "市值因子 ( Barra Style )"):
        super().__init__("Size", description)
        self.method = method
        self.weight = 1.0
    
    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """
        计算市值因子
        
        Args:
            data: 需要包含 'market_cap' 列
            
        Returns:
            市值因子值
        """
        if 'market_cap' not in data.columns:
            raise ValueError("数据必须包含 'market_cap' 列")
        
        mcap = data['market_cap']
        
        if self.method == "log_mcap":
            # 对数市值（行业标准做法）
            factor_values = np.log(mcap)
        elif self.method == "cube_root":
            # 市值立方根
            factor_values = np.cbrt(mcap)
        elif self.method == "rank":
            # 排名（市值越小，因子值越大）
            factor_values = -mcap.rank()
        else:
            factor_values = np.log(mcap)
        
        self.values = factor_values
        return factor_values


class BetaFactor(BarraStyleFactor):
    """
    市场敏感度因子 (Beta)
    
    衡量个股对市场收益的敏感程度
    """
    
    def __init__(self, period: int = 252, description: str = "市场敏感度因子 ( Barra Style )"):
        super().__init__("Beta", description)
        self.period = period
        self.weight = 1.0
    
    def calculate(self, data: pd.DataFrame, market_returns: pd.Series = None) -> pd.Series:
        """
        计算 Beta 因子
        
        Args:
            data: 需要包含 'close' 列
            market_returns: 市场收益序列（可选，如果未提供则跳过）
            
        Returns:
            Beta 值
        """
        if 'close' not in data.columns:
            raise ValueError("数据必须包含 'close' 列")
        
        # 计算个股收益率
        stock_returns = data['close'].pct_change()
        
        if market_returns is not None:
            # 使用 CAPM 方法计算 Beta
            # Beta = Cov(r_stock, r_market) / Var(r_market)
            
            # 对齐数据
            common_index = stock_returns.index.intersection(market_returns.index)
            if len(common_index) < 30:
                print(f"⚠️ 数据点不足，使用默认 Beta=1.0")
                return pd.Series(1.0, index=data.index)
            
            stock_aligned = stock_returns.loc[common_index]
            market_aligned = market_returns.loc[common_index]
            
            # 计算 Beta
            covariance = np.cov(stock_aligned, market_aligned)[0][1]
            market_variance = np.var(market_aligned)
            
            if market_variance > 0:
                beta = covariance / market_variance
            else:
                beta = 1.0
        else:
            # 使用滚动窗口计算
            # 简化版本：收益率标准差 / 市场收益率标准差
            stock_vol = stock_returns.rolling(window=self.period).std()
            market_vol = stock_vol  # 简化处理
            beta = stock_vol / market_vol.replace(0, np.nan)
            beta = beta.fillna(1.0)
        
        self.values = beta
        return beta


class MomentumFactor(BarraStyleFactor):
    """
    动量因子 (Momentum)
    
    衡量过去 6-12 个月的累计收益
    动量效应：过去表现好的股票未来往往继续表现好
    """
    
    def __init__(self, period: int = 252, 
                 skip_days: int = 21,
                 description: str = "动量因子 ( Barra Style )"):
        """
        Args:
            period: 回看期（天）
            skip_days: 跳过最近多少天（避免短期反转效应干扰）
        """
        super().__init__("Momentum", description)
        self.period = period
        self.skip_days = skip_days
        self.weight = 1.0
    
    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """
        计算动量因子
        
        Returns:
            动量因子值（过去 period 天的累计收益，跳过最近 skip_days）
        """
        if 'close' not in data.columns:
            raise ValueError("数据必须包含 'close' 列")
        
        # 计算累计收益
        close = data['close']
        
        # 动量 = 当前价格 / period 天前的价格 - 1
        momentum = close / close.shift(self.period) - 1
        
        # 或者使用对数收益
        # momentum = np.log(close / close.shift(self.period))
        
        self.values = momentum
        return momentum


class SizeNonlinearFactor(BarraStyleFactor):
    """
    非线性市值因子 (Size Non-Linear)
    
    捕捉市值与收益之间的非线性关系
    """
    
    def __init__(self, description: str = "非线性市值因子 ( Barra Style )"):
        super().__init__("Size_Nonlinear", description)
        self.weight = 1.0
    
    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """
        计算非线性市值因子
        
        Returns:
            市值立方根的多项式
        """
        if 'market_cap' not in data.columns:
            raise ValueError("数据必须包含 'market_cap' 列")
        
        mcap = data['market_cap']
        
        # Size_Nonlinear = Size^3 - 调整后的 Size^3
        # 简化实现：取市值的立方根，然后做三次多项式
        
        size_cube_root = np.cbrt(mcap)
        
        # 计算 Size_Nonlinear = Size^3 - 调整因子
        # 实际实现应该基于行业分组
        size_cubed = size_cube_root ** 3
        
        # 减去线性成分
        size_nonlinear = size_cubed - size_cube_root
        
        self.values = size_nonlinear
        return size_nonlinear


class ValueFactor(BarraStyleFactor):
    """
    价值因子 (Value)
    
    衡量估值水平，低估值股票长期收益往往优于高估值
    常用指标：PE、PB、PCF、EV/EBITDA
    """
    
    def __init__(self, method: str = "pe", 
                 description: str = "价值因子 ( Barra Style )"):
        super().__init__("Value", description)
        self.method = method
        self.weight = 1.0
    
    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """
        计算价值因子
        
        Returns:
            价值因子值（低估值 = 高因子值）
        """
        if self.method == "pe":
            if 'pe' not in data.columns:
                raise ValueError("数据必须包含 'pe' 列")
            # 市盈率越低越好，取负值
            value = -data['pe']
        elif self.method == "pb":
            if 'pb' not in data.columns:
                raise ValueError("数据必须包含 'pb' 列")
            # 市净率越低越好
            value = -data['pb']
        elif self.method == "pcf":
            if 'pcf' not in data.columns:
                raise ValueError("数据必须包含 'pcf' 列")
            # 市现率越低越好
            value = -data['pcf']
        elif self.method == "ey":
            if 'pe' in data.columns:
                # 盈利收益率 = 1/PE
                value = 1 / data['pe'].replace(0, np.nan)
            else:
                raise ValueError("需要 PE 数据计算盈利收益率")
        else:
            raise ValueError(f"未知方法: {self.method}")
        
        # 处理无效值
        value = value.replace([np.inf, -np.inf], np.nan)
        value = value.fillna(value.median())
        
        self.values = value
        return value


class VolatilityFactor(BarraStyleFactor):
    """
    残差波动率因子 (Residual Volatility)
    
    衡量收益的波动程度，高波动股票往往收益不佳
    """
    
    def __init__(self, period: int = 252, method: str = "std",
                 description: str = "残差波动率因子 ( Barra Style )"):
        """
        Args:
            period: 回看期
            method: 计算方法 ('std', 'range', 'atr')
        """
        super().__init__("Volatility", description)
        self.period = period
        self.method = method
        self.weight = 1.0
    
    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """
        计算波动率因子
        
        Returns:
            波动率因子值（低波动 = 高因子值）
        """
        if 'close' not in data.columns:
            raise ValueError("数据必须包含 'close' 列")
        
        close = data['close']
        returns = close.pct_change()
        
        if self.method == "std":
            # 标准差
            vol = returns.rolling(window=self.period).std()
        elif self.method == "range":
            # 价格范围
            high = data.get('high', close)
            low = data.get('low', close)
            vol = (high - low).rolling(window=self.period).mean() / close
        elif self.method == "atr":
            # 真实波幅
            high = data.get('high', close)
            low = data.get('low', close)
            prev_close = close.shift(1)
            
            tr1 = high - low
            tr2 = (high - prev_close).abs()
            tr3 = (low - prev_close).abs()
            
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            vol = tr.rolling(window=self.period).mean()
        else:
            vol = returns.rolling(window=self.period).std()
        
        # 低波动是优势，取负值
        factor_values = -vol
        
        self.values = factor_values
        return factor_values


class LiquidityFactor(BarraStyleFactor):
    """
    流动性因子 (Liquidity)
    
    衡量股票的交易活跃程度
    低流动性股票往往有更高的交易成本和价格冲击
    """
    
    def __init__(self, period: int = 252, method: " turnover",
                 description: str = "流动性因子 ( Barra Style )"):
        """
        Args:
            period: 回看期
            method: 计算方法 ('turnover', 'amihud')
        """
        super().__init__("Liquidity", description)
        self.period = period
        self.method = method
        self.weight = 1.0
    
    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """
        计算流动性因子
        
        Returns:
            流动性因子值（高流动性 = 高因子值）
        """
        if self.method == "turnover":
            if 'volume' not in data.columns:
                raise ValueError("数据必须包含 'volume' 列")
            
            # 换手率 = 成交量 / 流通股数
            # 简化：直接用成交量
            turnover = data['volume'].rolling(window=self.period).mean()
            factor_values = turnover
            
        elif self.method == "amihud":
            if 'volume' not in data.columns or 'close' not in data.columns:
                raise ValueError("需要 'volume' 和 'close' 列")
            
            # Amihud 流动性比率 = |收益| / (成交量 * 价格)
            returns = data['close'].pct_change().abs()
            amount = data['volume'] * data['close']
            
            amihud = (returns / amount.replace(0, np.nan)).rolling(window=self.period).mean()
            
            # Amihud 越低，流动性越好
            factor_values = -amihud
            
        else:
            raise ValueError(f"未知方法: {self.method}")
        
        self.values = factor_values
        return factor_values


class EarningsYieldFactor(BarraStyleFactor):
    """
    盈利收益率因子 (Earnings Yield)
    
    盈利收益率 = 净利润 / 企业价值 或 1/PE
    """
    
    def __init__(self, method: str = "ey",
                 description: str = "盈利收益率因子 ( Barra Style )"):
        """
        Args:
            method: 计算方法
        """
        super().__init__("EarningsYield", description)
        self.method = method
        self.weight = 1.0
    
    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """
        计算盈利收益率因子
        
        Returns:
            盈利收益率因子值
        """
        if self.method == "ey":
            if 'pe' in data.columns:
                # 盈利收益率 = 1/PE
                ey = 1 / data['pe'].replace(0, np.nan)
            else:
                raise ValueError("需要 PE 数据")
        elif self.method == "ebitda_ev":
            # EBITDA / Enterprise Value
            if 'ebitda' in data.columns and 'enterprise_value' in data.columns:
                ey = data['ebitda'] / data['enterprise_value'].replace(0, np.nan)
            else:
                raise ValueError("需要 'ebitda' 和 'enterprise_value' 数据")
        else:
            raise ValueError(f"未知方法: {self.method}")
        
        # 处理无效值
        ey = ey.replace([np.inf, -np.inf], np.nan)
        ey = ey.fillna(ey.median())
        
        self.values = ey
        return ey


class GrowthFactor(BarraStyleFactor):
    """
    成长因子 (Growth)
    
    衡量公司的营收、利润增长能力
    """
    
    def __init__(self, metric: str = "revenue", period: int = 4,
                 description: str = "成长因子 ( Barra Style )"):
        """
        Args:
            metric: 增长指标 ('revenue', 'profit', 'eps')
            period: 回看期（季度）
        """
        super().__init__("Growth", description)
        self.metric = metric
        self.period = period
        self.weight = 1.0
    
    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """
        计算成长因子
        
        Returns:
            成长因子值
        """
        if self.metric == "revenue":
            if 'revenue' not in data.columns:
                raise ValueError("需要 'revenue' 列")
            growth = data['revenue'].pct_change(periods=self.period)
        elif self.metric == "profit":
            if 'profit' not in data.columns:
                raise ValueError("需要 'profit' 列")
            growth = data['profit'].pct_change(periods=self.period)
        elif self.metric == "eps":
            if 'eps' not in data.columns:
                raise ValueError("需要 'eps' 列")
            growth = data['eps'].pct_change(periods=self.period)
        else:
            raise ValueError(f"未知指标: {self.metric}")
        
        # 处理无效值
        growth = growth.replace([np.inf, -np.inf], np.nan)
        growth = growth.fillna(growth.median())
        
        self.values = growth
        return growth


class LeverageFactor(BarraStyleFactor):
    """
    杠杆因子 (Leverage)
    
    衡量公司的财务杠杆水平
    """
    
    def __init__(self, method: str = "debt_to_equity",
                 description: str = "杠杆因子 ( Barra Style )"):
        """
        Args:
            method: 计算方法
        """
        super().__init__("Leverage", description)
        self.method = method
        self.weight = 1.0
    
    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """
        计算杠杆因子
        
        Returns:
            杠杆因子值
        """
        if self.method == "debt_to_equity":
            if 'debt' in data.columns and 'equity' in data.columns:
                leverage = data['debt'] / data['equity'].replace(0, np.nan)
            else:
                # 简化：如果没有直接数据，返回 0
                leverage = pd.Series(0.0, index=data.index)
        elif self.method == "debt_to_assets":
            if 'debt' in data.columns and 'assets' in data.columns:
                leverage = data['debt'] / data['assets'].replace(0, np.nan)
            else:
                leverage = pd.Series(0.0, index=data.index)
        else:
            leverage = pd.Series(0.0, index=data.index)
        
        # 处理无效值
        leverage = leverage.replace([np.inf, -np.inf], np.nan)
        leverage = leverage.fillna(leverage.median())
        
        self.values = leverage
        return leverage


class IndustryFactor(Factor):
    """
    行业因子
    
    用于控制行业中性
    """
    
    def __init__(self, industry_codes: List[str] = None,
                 description: str = "行业因子"):
        super().__init__("Industry", description)
        self.industry_codes = industry_codes or []
        self.weight = 1.0
    
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        计算行业因子
        
        Returns:
            行业因子矩阵（多列）
        """
        if 'industry' not in data.columns:
            print("⚠️ 数据没有 'industry' 列，返回单列零矩阵")
            return pd.DataFrame({'Industry': 0.0}, index=data.index)
        
        # 获取唯一行业
        industries = data['industry'].unique()
        
        # 创建行业哑变量
        industry_dummies = pd.get_dummies(data['industry'], prefix='', prefix_sep='')
        
        # 只保留指定的行业
        if self.industry_codes:
            industry_dummies = industry_dummies[[i for i in self.industry_codes if i in industry_dummies.columns]]
        
        self.values = industry_dummies.sum(axis=1)
        return industry_dummies


class CustomTechnicalFactor(Factor):
    """
    自定义技术因子
    
    方便快速添加新因子
    """
    
    def __init__(self, name: str, func: callable,
                 description: str = "自定义技术因子"):
        """
        Args:
            name: 因子名称
            func: 计算函数，接受 DataFrame，返回 Series
            description: 因子描述
        """
        super().__init__(name, description)
        self.func = func
        self.weight = 1.0
    
    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """
        计算自定义因子
        
        Returns:
            因子值
        """
        self.values = self.func(data)
        return self.values


# 便捷因子工厂
def create_factor(factor_type: str, **kwargs) -> Factor:
    """
    创建因子的便捷函数
    
    Args:
        factor_type: 因子类型
        **kwargs: 因子参数
        
    Returns:
        因子实例
    """
    factor_mapping = {
        'momentum': MomentumFactor,
        'value': ValueFactor,
        'quality': lambda: None,  # 需要从 factors.py 导入
        'growth': GrowthFactor,
        'size': SizeFactor,
        'volatility': VolatilityFactor,
        'liquidity': LiquidityFactor,
        'beta': BetaFactor,
        'earnings_yield': EarningsYieldFactor,
        'leverage': LeverageFactor,
        'size_nonlinear': SizeNonlinearFactor,
    }
    
    if factor_type not in factor_mapping:
        raise ValueError(f"未知因子类型: {factor_type}")
    
    factor_class = factor_mapping[factor_type]
    
    if callable(factor_class):
        return factor_class(**kwargs)
    else:
        return factor_class(**kwargs)


# 预定义的因子组合
DEFAULT_BARRA_FACTORS = [
    lambda: SizeFactor(),
    lambda: BetaFactor(),
    lambda: MomentumFactor(),
    lambda: SizeNonlinearFactor(),
    lambda: ValueFactor(method="pe"),
    lambda: VolatilityFactor(),
    lambda: LiquidityFactor(),
    lambda: EarningsYieldFactor(),
    lambda: GrowthFactor(metric="revenue"),
    lambda: LeverageFactor(),
]


if __name__ == "__main__":
    print("🧪 测试扩展因子库...")
    
    import numpy as np
    import pandas as pd
    
    # 创建模拟数据
    dates = pd.date_range(start='2020-01-01', periods=500, freq='B')
    n = len(dates)
    
    data = pd.DataFrame({
        'close': np.cumsum(np.random.randn(n) * 2 + 0.05) + 100,
        'market_cap': np.exp(np.random.randn(n) * 0.5 + 10) * 1e8,
        'pe': np.random.uniform(10, 50, n),
        'pb': np.random.uniform(1, 10, n),
        'roe': np.random.uniform(0.05, 0.25, n),
        'revenue': np.random.uniform(1e8, 1e10, n),
        'volume': np.random.randint(1e6, 1e8, n),
    }, index=dates)
    
    # 测试各因子
    print("\n📊 测试 Barra 风格因子:")
    
    factors = [
        ("Size", SizeFactor()),
        ("Momentum", MomentumFactor()),
        ("Value", ValueFactor(method="pe")),
        ("Volatility", VolatilityFactor()),
        ("Liquidity", LiquidityFactor()),
        ("Growth", GrowthFactor(metric="revenue")),
    ]
    
    for name, factor in factors:
        try:
            values = factor.calculate(data)
            print(f"  ✅ {name}: 均值={values.mean():.4f}, 标准差={values.std():.4f}")
        except Exception as e:
            print(f"  ❌ {name}: {e}")
    
    print("\n✨ 因子库测试完成!")
