"""
数据验证器 - 验证数据质量
Data Validator

功能:
1. 检查数据完整性
2. 检查数据一致性
3. 检查数据异常值
4. 生成数据质量报告
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """验证结果"""
    passed: bool
    errors: List[str]
    warnings: List[str]
    metrics: Dict[str, Any]


class DataValidator:
    """
    数据验证器
    
    验证价格数据和因子数据的质量
    """
    
    def __init__(self, min_completeness: float = 0.95):
        """
        初始化
        
        Args:
            min_completeness: 最小完整率
        """
        self.min_completeness = min_completeness
    
    def validate_price_data(
        self,
        df: pd.DataFrame,
        required_columns: List[str] = None
    ) -> ValidationResult:
        """
        验证价格数据
        
        Args:
            df: 价格数据
            required_columns: 必需列
            
        Returns:
            ValidationResult
        """
        if required_columns is None:
            required_columns = ['time', 'symbol', 'open', 'high', 'low', 'close', 'volume']
        
        errors = []
        warnings = []
        metrics = {}
        
        # 1. 检查必需列
        missing_cols = set(required_columns) - set(df.columns)
        if missing_cols:
            errors.append(f"缺少必需列: {missing_cols}")
        
        # 2. 检查完整性
        total_cells = len(df) * len(required_columns)
        non_null_cells = df[required_columns].notna().sum().sum()
        completeness = non_null_cells / total_cells if total_cells > 0 else 0
        metrics['completeness'] = completeness
        
        if completeness < self.min_completeness:
            warnings.append(f"数据完整率 {completeness:.2%} 低于阈值 {self.min_completeness:.2%}")
        
        # 3. 检查价格有效性
        if 'close' in df.columns:
            invalid_price = (df['close'] <= 0).sum()
            metrics['invalid_price_count'] = invalid_price
            if invalid_price > 0:
                warnings.append(f"发现 {invalid_price} 条无效价格数据")
        
        # 4. 检查OHLC关系
        if all(c in df.columns for c in ['open', 'high', 'low', 'close']):
            ohlc_valid = ((df['high'] >= df['low']) & 
                         (df['high'] >= df['open']) & 
                         (df['high'] >= df['close']) &
                         (df['low'] <= df['open']) &
                         (df['low'] <= df['close'])).sum()
            ohlc_invalid = len(df) - ohlc_valid
            metrics['ohlc_invalid'] = ohlc_invalid
            if ohlc_invalid > 0:
                warnings.append(f"发现 {ohlc_invalid} 条OHLC关系错误")
        
        # 5. 检查成交量
        if 'volume' in df.columns:
            negative_volume = (df['volume'] < 0).sum()
            metrics['negative_volume'] = negative_volume
            if negative_volume > 0:
                errors.append(f"发现 {negative_volume} 条负成交量")
        
        passed = len(errors) == 0
        
        return ValidationResult(
            passed=passed,
            errors=errors,
            warnings=warnings,
            metrics=metrics
        )
    
    def validate_factor_data(
        self,
        df: pd.DataFrame,
        factor_name: str = None
    ) -> ValidationResult:
        """
        验证因子数据
        
        Args:
            df: 因子数据
            factor_name: 因子名称
            
        Returns:
            ValidationResult
        """
        errors = []
        warnings = []
        metrics = {}
        
        # 1. 检查必需列
        required_cols = ['time', 'symbol', 'value']
        missing_cols = set(required_cols) - set(df.columns)
        if missing_cols:
            errors.append(f"缺少必需列: {missing_cols}")
        
        # 2. 检查完整性
        total_cells = len(df) * len(required_cols)
        non_null_cells = df[required_cols].notna().sum().sum()
        completeness = non_null_cells / total_cells if total_cells > 0 else 0
        metrics['completeness'] = completeness
        
        if completeness < self.min_completeness:
            warnings.append(f"数据完整率 {completeness:.2%} 低于阈值")
        
        # 3. 检查因子值
        if 'value' in df.columns:
            # 检查NaN
            nan_count = df['value'].isna().sum()
            metrics['nan_count'] = nan_count
            if nan_count > 0:
                warnings.append(f"发现 {nan_count} 个NaN值")
            
            # 检查无穷值
            inf_count = np.isinf(df['value']).sum()
            metrics['inf_count'] = inf_count
            if inf_count > 0:
                errors.append(f"发现 {inf_count} 个无穷值")
            
            # 检查异常值 (3sigma)
            mean = df['value'].mean()
            std = df['value'].std()
            outlier_count = ((df['value'] < mean - 3*std) | 
                          (df['value'] > mean + 3*std)).sum()
            metrics['outlier_count'] = outlier_count
            metrics['outlier_ratio'] = outlier_count / len(df) if len(df) > 0 else 0
            
            if metrics['outlier_ratio'] > 0.05:
                warnings.append(f"异常值比例 {metrics['outlier_ratio']:.2%} 超过5%")
        
        # 4. 检查日期连续性
        if 'time' in df.columns:
            dates = pd.to_datetime(df['time']).sort_values()
            date_diffs = dates.diff().dropna()
            max_gap = date_diffs.max()
            metrics['max_date_gap_days'] = max_gap.days
            
            if max_gap.days > 30:
                warnings.append(f"最大日期缺口 {max_gap.days} 天")
        
        passed = len(errors) == 0
        
        return ValidationResult(
            passed=passed,
            errors=errors,
            warnings=warnings,
            metrics=metrics
        )
    
    def generate_report(
        self,
        result: ValidationResult,
        title: str = '数据验证报告'
    ) -> str:
        """
        生成验证报告
        
        Args:
            result: 验证结果
            title: 报告标题
            
        Returns:
            报告文本
        """
        lines = [
            "=" * 60,
            title,
            "=" * 60,
            "",
            f"状态: {'✅ 通过' if result.passed else '❌ 失败'}",
            "",
            "指标:",
            "-" * 40,
        ]
        
        for key, value in result.metrics.items():
            lines.append(f"  {key}: {value}")
        
        if result.errors:
            lines.extend([
                "",
                "错误:",
                "-" * 40,
            ])
            for error in result.errors:
                lines.append(f"  ❌ {error}")
        
        if result.warnings:
            lines.extend([
                "",
                "警告:",
                "-" * 40,
            ])
            for warning in result.warnings:
                lines.append(f"  ⚠️ {warning}")
        
        lines.append("")
        lines.append("=" * 60)
        
        return "\n".join(lines)


def validate_and_report(df: pd.DataFrame, data_type: str = 'price') -> ValidationResult:
    """
    便捷验证函数
    
    Args:
        df: 数据
        data_type: 数据类型 ('price' 或 'factor')
        
    Returns:
        ValidationResult
    """
    validator = DataValidator()
    
    if data_type == 'price':
        return validator.validate_price_data(df)
    else:
        return validator.validate_factor_data(df)


# ==================== 导出 ====================

__all__ = [
    'DataValidator',
    'ValidationResult',
    'validate_and_report',
]
