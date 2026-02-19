"""
因子管道模块
Pipeline Module

核心特性:
- 基于 Zipline Pipeline 架构
- 统一数据接口 (支持TimescaleDB)
- 频率自动适配
- 因子计算与存储

使用方式:
    from quant_factor_system.factors import Pipeline, Frequency
    from quant_factor_system.data import DataManager
    
    # 创建Pipeline
    pipe = Pipeline('MyPipeline')
    pipe.add_factor('momentum', Momentum(window=20))
    pipe.add_factor('rsi', RSI(window=14))
    
    # 从DataManager获取数据并运行
    dm = DataManager()
    data = dm.get_price_data(symbols=['SH600000'], frequency='daily')
    
    result = pipe.run(data)
"""

import pandas as pd
from typing import Dict, Callable
from dataclasses import dataclass, field
from datetime import datetime
import logging

from quant_factor_system.data.storage.frequency import Frequency

logger = logging.getLogger(__name__)


# ==================== 结果类 ====================

@dataclass
class PipelineResult:
    """Pipeline运行结果"""
    name: str
    data: pd.DataFrame
    factors: Dict[str, pd.Series]
    computed_at: datetime = field(default_factory=datetime.now)


# ==================== Pipeline 引擎 ====================

class Pipeline:
    """
    因子管道引擎
    
    特点:
    - 统一数据接口
    - 频率自动适配
    - 因子批量计算
    - 结果可存储
    """
    
    def __init__(self, name: str = "Pipeline"):
        self.name = name
        self.factors: Dict[str, Callable] = {}
        self.factor_configs: Dict[str, Dict] = {}
    
    def add_factor(
        self,
        name: str,
        factor_class_or_name,
        window: int = 20,
        period: int = None,
        **kwargs
    ) -> 'Pipeline':
        """
        添加因子
        
        Args:
            name: 因子名称 (唯一标识)
            factor_class_or_name: 因子类或注册表中的因子名称
            window: 窗口大小
            period: 回看期（与 window 通用）
            **kwargs: 其他参数
            
        Returns:
            self
        """
        # 如果传入了 period，使用它而不是 window
        if period is not None:
            kwargs['period'] = period
        
        # 如果是字符串，从因子工厂获取
        if isinstance(factor_class_or_name, str):
            from ..factors import FactorFactory
            factor_instance = FactorFactory.create(factor_class_or_name, kwargs)
            factor_class = type(factor_instance)
            # 尝试从实例获取窗口参数
            if window == 20:
                for attr in ['window', 'period']:
                    if hasattr(factor_instance, attr):
                        window = getattr(factor_instance, attr)
                        break
        else:
            factor_class = factor_class_or_name
        
        self.factors[name] = {
            'class': factor_class,
            'window': window,
            'params': kwargs
        }
        return self
    
    def run(
        self,
        data: pd.DataFrame,
        frequency: str = 'daily',
        save: bool = False,
        data_manager = None
    ) -> PipelineResult:
        """
        运行Pipeline
        
        Args:
            data: 价格数据 (DataFrame)
            frequency: 数据频率
            save: 是否保存到数据库
            data_manager: 数据管理器实例
            
        Returns:
            PipelineResult
        """
        logger.info(f"🚀 运行 Pipeline: {self.name}")
        logger.info(f"   数据形状: {data.shape}")
        logger.info(f"   频率: {frequency}")
        
        # 排序数据
        df = data.copy()
        if 'symbol' in df.columns and 'timestamp' in df.columns:
            df = df.sort_values(['symbol', 'timestamp'])
        elif 'symbol' in df.index.names and 'timestamp' in df.index.names:
            df = df.sort_index()
        
        # 计算因子
        factor_results = {}
        
        for name, config in self.factors.items():
            try:
                factor_class = config['class']
                window = config['window']
                params = config['params']
                
                # 创建因子
                factor = factor_class(window=window, **params)
                
                # 计算
                result = factor.compute(df, frequency=frequency)
                
                # 确保是Series
                if isinstance(result, pd.DataFrame):
                    result = result.iloc[:, 0]
                
                factor_results[name] = result
                logger.info(f"   ✅ {name}")
                
            except Exception as e:
                logger.error(f"   ❌ {name}: {e}")
        
        # 构建结果DataFrame
        result_df = pd.DataFrame(factor_results)
        
        # 对齐索引
        if 'symbol' in df.columns and 'timestamp' in df.columns:
            result_df['symbol'] = df['symbol'].values
            result_df['timestamp'] = df['timestamp'].values
            result_df = result_df.set_index(['symbol', 'timestamp'])
        elif isinstance(df.index, pd.MultiIndex):
            result_df.index = df.index
        
        # 保存到数据库
        if save and data_manager is not None:
            self._save_results(result_df, frequency, data_manager)
        
        return PipelineResult(
            name=self.name,
            data=result_df,
            factors=factor_results
        )
    
    def _save_results(
        self,
        result_df: pd.DataFrame,
        frequency: str,
        data_manager
    ):
        """保存结果到数据库"""
        try:
            # 转换为长表格式
            df_long = result_df.reset_index()
            
            # 获取因子列
            factor_cols = [c for c in df_long.columns if c not in ['symbol', 'timestamp']]
            
            for factor_name in factor_cols:
                df_factor = df_long[['symbol', 'timestamp', factor_name]].copy()
                df_factor = df_factor.rename(columns={factor_name: 'factor_value'})
                df_factor['factor_name'] = factor_name
                
                data_manager.save_factor_data(df_factor, frequency=frequency)
            
            logger.info(f"   💾 因子已保存 ({frequency})")
            
        except Exception as e:
            logger.error(f"   保存失败: {e}")


# ==================== 便捷因子 ====================

class BuiltInFactors:
    """
    内置因子工厂
    
    使用方式:
        pipe.add_factor('momentum', BuiltInFactors.momentum(20))
        pipe.add_factor('value', BuiltInFactors.value('pe'))
    """
    
    @staticmethod
    def momentum(window: int = 20) -> type:
        """动量因子"""
        from ..basic.factors import MomentumFactor
        return lambda **kwargs: MomentumFactor(period=window, **kwargs)
    
    @staticmethod
    def value(metric: str = 'pe') -> type:
        """价值因子"""
        from ..basic.factors import ValueFactor
        return lambda **kwargs: ValueFactor(metric=metric, **kwargs)
    
    @staticmethod
    def quality(metric: str = 'roe') -> type:
        """质量因子"""
        from ..basic.factors import QualityFactor
        return lambda **kwargs: QualityFactor(metric=metric, **kwargs)
    
    @staticmethod
    def volatility(window: int = 20) -> type:
        """波动率因子"""
        from ..basic.factors import VolatilityFactor
        return lambda **kwargs: VolatilityFactor(window=window, **kwargs)
    
    @staticmethod
    def size() -> type:
        """规模因子"""
        from ..basic.factors import SizeFactor
        return lambda **kwargs: SizeFactor(**kwargs)


# ==================== 便捷函数 ====================

def create_pipeline(name: str = "Pipeline") -> Pipeline:
    """创建Pipeline"""
    return Pipeline(name)


# ==================== 导出 ====================

__all__ = [
    'Pipeline',
    'PipelineResult',
    'Frequency',
    'BuiltInFactors',
    'create_pipeline',
]
