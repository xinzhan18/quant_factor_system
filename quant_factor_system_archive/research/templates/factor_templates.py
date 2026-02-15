"""
因子模板模块
提供因子开发模板和论文复现框架
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from datetime import datetime
import json
import inspect
import warnings
warnings.filterwarnings('ignore')


@dataclass
class FactorTemplate:
    """
    因子模板定义
    """
    name: str
    category: str
    description: str
    author: str = ""
    version: str = "1.0"
    created_at: str = field(default_factory=lambda: datetime.now().strftime('%Y-%m-%d'))
    params: Dict = field(default_factory=dict)
    code: str = ""  # 因子代码
    paper_reference: str = ""  # 论文引用
    tags: List[str] = field(default_factory=list)


@dataclass
class FactorVersion:
    """
    因子版本
    """
    factor_name: str
    version: str
    created_at: str
    created_by: str
    changes: str
    code: str
    params: Dict
    performance: Dict = field(default_factory=dict)


class BaseFactorTemplate(ABC):
    """
    因子模板基类
    所有自定义因子都应该继承此类
    """
    
    # 元数据
    name: str = "BaseFactor"
    category: str = "custom"
    description: str = "自定义因子"
    author: str = ""
    version: str = "1.0"
    paper_reference: str = ""
    tags: List[str] = field(default_factory=list)
    
    def __init__(self, **params):
        """
        初始化
        
        Args:
            **params: 因子参数
        """
        self.params = params
        self._validate_params()
        self._init_params()
    
    def _validate_params(self):
        """验证参数"""
        pass
    
    def _init_params(self):
        """初始化参数"""
        for key, value in self.params.items():
            setattr(self, key, value)
    
    @abstractmethod
    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """
        计算因子值
        
        Args:
            data: 输入数据（必须包含需要的列）
            
        Returns:
            因子值序列
        """
        pass
    
    def get_required_columns(self) -> List[str]:
        """
        获取需要的列
        
        Returns:
            列名列表
        """
        return ['close']
    
    def get_output_name(self) -> str:
        """
        获取输出列名
        
        Returns:
            列名
        """
        return self.name
    
    def preprocess(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        数据预处理
        
        Args:
            data: 输入数据
            
        Returns:
            处理后的数据
        """
        return data.copy()
    
    def postprocess(self, factor: pd.Series) -> pd.Series:
        """
        后处理因子值
        
        Args:
            factor: 原始因子值
            
        Returns:
            处理后的因子值
        """
        return factor
    
    def __call__(self, data: pd.DataFrame) -> pd.Series:
        """
        执行因子计算
        
        Args:
            data: 输入数据
            
        Returns:
            因子值序列
        """
        # 预处理
        data = self.preprocess(data)
        
        # 计算
        factor = self.calculate(data)
        
        # 后处理
        factor = self.postprocess(factor)
        
        return factor
    
    def get_template(self) -> FactorTemplate:
        """
        获取因子模板
        
        Returns:
            FactorTemplate 对象
        """
        return FactorTemplate(
            name=self.name,
            category=self.category,
            description=self.description,
            author=self.author,
            version=self.version,
            params=self.params,
            code=inspect.getsource(type(self)),
            paper_reference=self.paper_reference,
            tags=self.tags
        )
    
    def get_config(self) -> Dict[str, Any]:
        """
        获取配置（用于保存）
        
        Returns:
            配置字典
        """
        return {
            'class_name': self.__class__.__name__,
            'module': self.__class__.__module__,
            'name': self.name,
            'category': self.category,
            'description': self.description,
            'author': self.author,
            'version': self.version,
            'paper_reference': self.paper_reference,
            'tags': self.tags,
            'params': self.params
        }


# ========== 常用因子模板 ==========

class MomentumTemplate(BaseFactorTemplate):
    """
    动量因子模板
    
    常见动量因子：
    - 过去 N 个月累计收益
    - 动量反转
    - 相对强弱
    """
    
    name = "Momentum"
    category = "momentum"
    description = "动量因子：衡量过去N期收益表现"
    tags = ["momentum", "price"]
    
    def __init__(self, period: int = 20, method: str = "pct_change"):
        """
        初始化
        
        Args:
            period: 回看期数
            method: 计算方法 ('pct_change', 'log_return', 'excess_return')
        """
        super().__init__(period=period, method=method)
    
    def _validate_params(self):
        if self.params.get('period', 1) < 1:
            raise ValueError("period 必须大于 0")
        if self.params.get('method') not in ['pct_change', 'log_return', 'excess_return']:
            raise ValueError("method 必须是 'pct_change', 'log_return', 或 'excess_return'")
    
    def calculate(self, data: pd.DataFrame) -> pd.Series:
        if 'close' not in data.columns:
            raise ValueError("数据必须包含 'close' 列")
        
        close = data['close']
        period = self.params['period']
        method = self.params['method']
        
        if method == 'pct_change':
            factor = close.pct_change(period)
        elif method == 'log_return':
            factor = np.log(close / close.shift(period))
        else:  # excess_return
            market_return = close.pct_change(period).mean() if hasattr(close, 'mean') else 0
            factor = close.pct_change(period) - market_return
        
        return factor


class MeanReversionTemplate(BaseFactorTemplate):
    """
    均值回归因子模板
    
    常见变体：
    - 距离移动均线的偏离度
    - 过去 N 天收益的反转
    """
    
    name = "MeanReversion"
    category = "value"
    description = "均值回归因子：衡量价格偏离均值的程度"
    tags = ["mean_reversion", "value"]
    
    def __init__(self, period: int = 20, method: str = "zscore"):
        """
        初始化
        
        Args:
            period: 均值计算期数
            method: 计算方法 ('zscore', 'distance', 'ratio')
        """
        super().__init__(period=period, method=method)
    
    def calculate(self, data: pd.DataFrame) -> pd.Series:
        if 'close' not in data.columns:
            raise ValueError("数据必须包含 'close' 列")
        
        close = data['close']
        period = self.params['period']
        method = self.params['method']
        
        if method == 'zscore':
            # Z-score = (price - MA) / std
            ma = close.rolling(period).mean()
            std = close.rolling(period).std()
            factor = (close - ma) / (std + 1e-8)
        elif method == 'distance':
            # 价格偏离均线的百分比
            ma = close.rolling(period).mean()
            factor = (close - ma) / (ma + 1e-8)
        else:  # ratio
            ma = close.rolling(period).mean()
            factor = ma / (close + 1e-8)
        
        return factor


class VolatilityTemplate(BaseFactorTemplate):
    """
    波动率因子模板
    
    常见变体：
    - 历史波动率
    - 已实现波动率
    - 波动率偏度
    """
    
    name = "Volatility"
    category = "volatility"
    description = "波动率因子：衡量收益的波动程度"
    tags = ["volatility", "risk"]
    
    def __init__(self, period: int = 20, method: str = "std", annualized: bool = True):
        """
        初始化
        
        Args:
            period: 计算期数
            method: 计算方法 ('std', 'mad', 'range')
            annualized: 是否年化
        """
        super().__init__(period=period, method=method, annualized=annualized)
    
    def calculate(self, data: pd.DataFrame) -> pd.Series:
        if 'close' not in data.columns:
            raise ValueError("数据必须包含 'close' 列")
        
        close = data['close']
        returns = close.pct_change()
        period = self.params['period']
        method = self.params['method']
        annualized = self.params['annualized']
        
        if method == 'std':
            vol = returns.rolling(period).std()
        elif method == 'mad':
            vol = returns.rolling(period).mad()
        else:  # range
            high = data['high'] if 'high' in data.columns else close * 1.02
            low = data['low'] if 'low' in data.columns else close * 0.98
            vol = (high - low).rolling(period).mean()
        
        if annualized:
            vol = vol * np.sqrt(252)
        
        return -vol  # 低波动率因子取负值（低波动是优势）


class VolumeTemplate(BaseFactorTemplate):
    """
    成交量因子模板
    
    常见变体：
    - 成交量变化率
    - 成交量偏度
    - 资金流
    """
    
    name = "Volume"
    category = "liquidity"
    description = "成交量因子：衡量交易活跃程度"
    tags = ["volume", "liquidity"]
    
    def __init__(self, period: int = 20, method: str = "avg_ratio"):
        """
        初始化
        
        Args:
            period: 计算期数
            method: 计算方法 ('avg_ratio', 'trend', 'flow')
        """
        super().__init__(period=period, method=method)
    
    def calculate(self, data: pd.DataFrame) -> pd.Series:
        if 'volume' not in data.columns:
            raise ValueError("数据必须包含 'volume' 列")
        
        volume = data['volume']
        period = self.params['period']
        method = self.params['method']
        
        if method == 'avg_ratio':
            # 成交量 / 平均成交量
            avg_vol = volume.rolling(period).mean()
            factor = volume / (avg_vol + 1e-8)
        elif method == 'trend':
            # 成交量趋势
            factor = volume.pct_change(period)
        else:  # flow
            close = data['close']
            factor = volume * close
        
        return factor


class QualityTemplate(BaseFactorTemplate):
    """
    质量因子模板
    
    常见指标：
    - ROE / ROA
    - 毛利率
    - 资产负债率
    """
    
    name = "Quality"
    category = "quality"
    description = "质量因子：衡量公司盈利质量"
    tags = ["quality", "profitability"]
    
    def __init__(self, metric: str = "roe"):
        """
        初始化
        
        Args:
            metric: 质量指标 ('roe', 'roa', 'gross_margin', 'net_profit_margin')
        """
        super().__init__(metric=metric)
    
    def calculate(self, data: pd.DataFrame) -> pd.Series:
        metric = self.params['metric']
        
        if metric == 'roe':
            if 'roe' not in data.columns:
                raise ValueError("数据必须包含 'roe' 列")
            factor = data['roe']
        elif metric == 'roa':
            if 'roa' not in data.columns:
                raise ValueError("数据必须包含 'roa' 列")
            factor = data['roa']
        elif metric == 'gross_margin':
            if 'gross_margin' not in data.columns:
                raise ValueError("数据必须包含 'gross_margin' 列")
            factor = data['gross_margin']
        else:  # net_profit_margin
            if 'net_profit_margin' not in data.columns:
                raise ValueError("数据必须包含 'net_profit_margin' 列")
            factor = data['net_profit_margin']
        
        return factor


class ValueTemplate(BaseFactorTemplate):
    """
    价值因子模板
    
    常见指标：
    - PE / PB / PS
    - 股息率
    """
    
    name = "Value"
    category = "value"
    description = "价值因子：衡量估值水平"
    tags = ["value", "valuation"]
    
    def __init__(self, metric: str = "pe"):
        """
        初始化
        
        Args:
            metric: 估值指标 ('pe', 'pb', 'ps', 'dividend_yield')
        """
        super().__init__(metric=metric)
    
    def calculate(self, data: pd.DataFrame) -> pd.Series:
        metric = self.params['metric']
        
        if metric == 'pe':
            if 'pe' not in data.columns:
                raise ValueError("数据必须包含 'pe' 列")
            factor = -data['pe']  # 低 PE 是优势
        elif metric == 'pb':
            if 'pb' not in data.columns:
                raise ValueError("数据必须包含 'pb' 列")
            factor = -data['pb']  # 低 PB 是优势
        elif metric == 'ps':
            if 'ps' not in data.columns:
                raise ValueError("数据必须包含 'ps' 列")
            factor = -data['ps']  # 低 PS 是优势
        else:  # dividend_yield
            if 'dividend_yield' not in data.columns:
                raise ValueError("数据必须包含 'dividend_yield' 列")
            factor = data['dividend_yield']
        
        return factor


class CompositeFactorTemplate(BaseFactorTemplate):
    """
    复合因子模板
    合并多个因子
    """
    
    name = "Composite"
    category = "composite"
    description = "复合因子：合并多个子因子"
    tags = ["composite", "multi_factor"]
    
    def __init__(self, factors: List[BaseFactorTemplate], 
                 weights: List[float] = None,
                 method: str = "weighted_avg"):
        """
        初始化
        
        Args:
            factors: 子因子列表
            weights: 权重列表
            method: 合并方法 ('weighted_avg', 'zscore_avg', 'rank_avg')
        """
        super().__init__(
            factors=[f.name for f in factors],
            weights=weights,
            method=method
        )
        self.factors = factors
        self.weights = weights or [1.0 / len(factors)] * len(factors)
    
    def calculate(self, data: pd.DataFrame) -> pd.Series:
        method = self.params['method']
        
        # 计算所有子因子
        factor_values = []
        for factor in self.factors:
            fv = factor.calculate(data)
            factor_values.append(fv)
        
        # 合并
        if method == 'weighted_avg':
            # 加权平均
            combined = pd.Series(0, index=factor_values[0].index)
            for fv, w in zip(factor_values, self.weights):
                combined += fv * w
        elif method == 'zscore_avg':
            # Z-score 后平均
            combined = pd.Series(0, index=factor_values[0].index)
            for fv, w in zip(factor_values, self.weights):
                fv_zscore = (fv - fv.mean()) / (fv.std() + 1e-8)
                combined += fv_zscore * w
        else:  # rank_avg
            # 排名后平均
            combined = pd.Series(0, index=factor_values[0].index)
            for fv, w in zip(factor_values, self.weights):
                fv_rank = fv.rank(pct=True)
                combined += fv_rank * w
        
        return combined


# ========== 因子模板管理器 ==========

class FactorTemplateManager:
    """
    因子模板管理器
    管理因子模板的注册、查找、版本控制
    """
    
    def __init__(self):
        """初始化"""
        self.templates: Dict[str, FactorTemplate] = {}
        self.versions: Dict[str, List[FactorVersion]] = {}
        self.registry: Dict[str, type] = {}  # 类注册表
    
    def register(self, template_class: type, 
                 overwrite: bool = False) -> bool:
        """
        注册因子模板类
        
        Args:
            template_class: 因子模板类
            overwrite: 是否覆盖
            
        Returns:
            是否成功
        """
        name = getattr(template_class, 'name', template_class.__name__)
        
        if name in self.registry and not overwrite:
            return False
        
        self.registry[name] = template_class
        
        # 创建模板实例并保存
        template = template_class()
        self.templates[name] = template.get_template()
        
        # 初始化版本列表
        if name not in self.versions:
            self.versions[name] = []
        
        return True
    
    def create_instance(self, name: str, **params) -> BaseFactorTemplate:
        """
        创建因子实例
        
        Args:
            name: 因子名称
            **params: 因子参数
            
        Returns:
            因子实例
        """
        if name not in self.registry:
            raise ValueError(f"因子 {name} 未注册")
        
        return self.registry[name](**params)
    
    def get_template(self, name: str) -> Optional[FactorTemplate]:
        """
        获取因子模板
        
        Args:
            name: 因子名称
            
        Returns:
            FactorTemplate 或 None
        """
        return self.templates.get(name)
    
    def list_templates(self, category: str = None) -> List[str]:
        """
        列出因子模板
        
        Args:
            category: 筛选类别
            
        Returns:
            因子名称列表
        """
        if category:
            return [name for name, t in self.templates.items() 
                   if t.category == category]
        return list(self.templates.keys())
    
    def add_version(self, factor_name: str, version: str,
                    created_by: str, changes: str,
                    code: str, params: Dict,
                    performance: Dict = None) -> bool:
        """
        添加因子版本
        
        Args:
            factor_name: 因子名称
            version: 版本号
            created_by: 创建者
            changes: 变更说明
            code: 代码
            params: 参数
            performance: 性能指标
            
        Returns:
            是否成功
        """
        if factor_name not in self.templates:
            return False
        
        v = FactorVersion(
            factor_name=factor_name,
            version=version,
            created_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            created_by=created_by,
            changes=changes,
            code=code,
            params=params,
            performance=performance or {}
        )
        
        if factor_name not in self.versions:
            self.versions[factor_name] = []
        
        self.versions[factor_name].append(v)
        
        return True
    
    def get_versions(self, factor_name: str) -> List[FactorVersion]:
        """
        获取因子版本历史
        
        Args:
            factor_name: 因子名称
            
        Returns:
            版本列表
        """
        return self.versions.get(factor_name, [])
    
    def export_template(self, name: str) -> Dict[str, Any]:
        """
        导出因子模板配置
        
        Args:
            name: 因子名称
            
        Returns:
            配置字典
        """
        template = self.templates.get(name)
        if not template:
            return {}
        
        return {
            'name': template.name,
            'category': template.category,
            'description': template.description,
            'author': template.author,
            'version': template.version,
            'paper_reference': template.paper_reference,
            'tags': template.tags,
            'params': template.params,
            'code': template.code
        }
    
    def import_template(self, config: Dict[str, Any]) -> bool:
        """
        导入因子模板配置
        
        Args:
            config: 配置字典
            
        Returns:
            是否成功
        """
        try:
            # 创建临时类
            class_name = config.get('name', 'ImportedFactor')
            
            # 创建模板
            template = FactorTemplate(
                name=config.get('name', class_name),
                category=config.get('category', 'custom'),
                description=config.get('description', ''),
                author=config.get('author', ''),
                version=config.get('version', '1.0'),
                params=config.get('params', {}),
                code=config.get('code', ''),
                paper_reference=config.get('paper_reference', ''),
                tags=config.get('tags', [])
            )
            
            self.templates[template.name] = template
            
            return True
        except:
            return False


# ========== 便捷函数 ==========

def create_template(config: Dict[str, Any]) -> BaseFactorTemplate:
    """
    根据配置创建因子模板
    
    Args:
        config: 配置字典
        
    Returns:
        因子模板实例
    """
    manager = FactorTemplateManager()
    
    # 注册内置模板
    register_builtin_templates(manager)
    
    # 创建实例
    return manager.create_instance(
        config.get('name', 'Custom'),
        **config.get('params', {})
    )


def register_builtin_templates(manager: FactorTemplateManager):
    """
    注册内置因子模板
    """
    manager.register(MomentumTemplate)
    manager.register(MeanReversionTemplate)
    manager.register(VolatilityTemplate)
    manager.register(VolumeTemplate)
    manager.register(QualityTemplate)
    manager.register(ValueTemplate)


if __name__ == '__main__':
    print("=" * 60)
    print("🧪 测试因子模板模块")
    print("=" * 60)
    
    # 1. 测试内置模板
    print("\n1. 测试内置模板:")
    manager = FactorTemplateManager()
    register_builtin_templates(manager)
    
    templates = manager.list_templates()
    print(f"   已注册 {len(templates)} 个模板: {templates}")
    
    # 2. 创建实例
    print("\n2. 创建因子实例:")
    momentum = manager.create_instance("Momentum", period=20)
    print(f"   Momentum 实例: period={momentum.params['period']}")
    
    # 3. 获取模板
    print("\n3. 获取模板信息:")
    template = manager.get_template("Momentum")
    print(f"   名称: {template.name}")
    print(f"   类别: {template.category}")
    print(f"   描述: {template.description}")
    
    # 4. 复合因子
    print("\n4. 创建复合因子:")
    momentum = manager.create_instance("Momentum", period=20)
    volatility = manager.create_instance("Volatility", period=20)
    
    composite = CompositeFactorTemplate(
        factors=[momentum, volatility],
        weights=[0.6, 0.4]
    )
    print(f"   复合因子: {composite.name}")
    print(f"   子因子: {composite.params['factors']}")
    
    # 5. 版本管理
    print("\n5. 版本管理:")
    manager.add_version(
        "Momentum", "1.1", "admin",
        "调整参数为20日", 
        "class Momentum...", 
        {'period': 20},
        {'ic': 0.05}
    )
    
    versions = manager.get_versions("Momentum")
    print(f"   版本数: {len(versions)}")
    print(f"   最新版本: {versions[0].version if versions else 'N/A'}")
    
    # 6. 导出/导入
    print("\n6. 导出/导入:")
    config = manager.export_template("Momentum")
    print(f"   导出配置: {list(config.keys())}")
    
    print("\n" + "=" * 60)
    print("✅ 因子模板模块测试完成!")
    print("=" * 60)
