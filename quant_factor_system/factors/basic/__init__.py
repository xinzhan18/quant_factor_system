# Basic Factors - 基础因子
from .factors import (
    MomentumFactor, 
    ValueFactor, 
    QualityFactor, 
    VolatilityFactor,
    GrowthFactor,
    SizeFactor,
    LiquidityFactor,
)

from .return_factors import (
    # 收益率因子
    Return1dFactor,
    Return5dFactor,
    Return20dFactor,
    Return60dFactor,
    
    # 均值回归因子
    DistMA10Factor,
    DistMA20Factor,
    DistMA60Factor,
    ZScore60Factor,
    
    # 便捷函数
    create_return_factor,
    create_dist_ma_factor,
)

__all__ = [
    # 原有因子
    "MomentumFactor",
    "ValueFactor", 
    "QualityFactor",
    "VolatilityFactor",
    "GrowthFactor",
    "SizeFactor",
    "LiquidityFactor",
    
    # 收益率因子
    "Return1dFactor",
    "Return5dFactor",
    "Return20dFactor",
    "Return60dFactor",
    
    # 均值回归因子
    "DistMA10Factor",
    "DistMA20Factor",
    "DistMA60Factor",
    "ZScore60Factor",
    
    # 便捷函数
    "create_return_factor",
    "create_dist_ma_factor",
]
