"""
因子模板模块
提供因子开发模板
"""

from .factor_templates import (
    # 模板基类
    BaseFactorTemplate,
    FactorTemplate,
    FactorVersion,
    
    # 常用模板
    MomentumTemplate,
    MeanReversionTemplate,
    VolatilityTemplate,
    VolumeTemplate,
    QualityTemplate,
    ValueTemplate,
    CompositeFactorTemplate,
    
    # 管理器
    FactorTemplateManager,
    register_builtin_templates,
    create_template,
)

__all__ = [
    # 模板基类
    "BaseFactorTemplate",
    "FactorTemplate",
    "FactorVersion",
    
    # 常用模板
    "MomentumTemplate",
    "MeanReversionTemplate",
    "VolatilityTemplate",
    "VolumeTemplate",
    "QualityTemplate",
    "ValueTemplate",
    "CompositeFactorTemplate",
    
    # 管理器
    "FactorTemplateManager",
    "register_builtin_templates",
    "create_template",
]
