"""
因子评估报告生成器
Factor Evaluation Report Generator

功能:
1. 整合IC分析和分组收益分析
2. 生成HTML/PDF报告
3. 保存图表到文件
"""

import os
import json
from datetime import datetime
from typing import Dict, Any
import pandas as pd

from .ic_analyzer import create_ic_analyzer
from .group_returns import create_group_analyzer


class FactorReportGenerator:
    """
    因子评估报告生成器
    
    整合所有分析结果，生成完整的因子评估报告
    """
    
    def __init__(self, factor_name: str = None, output_dir: str = './reports'):
        """
        初始化
        
        Args:
            factor_name: 因子名称
            output_dir: 输出目录
        """
        self.factor_name = factor_name
        self.output_dir = output_dir
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 初始化分析器
        self.ic_analyzer = create_ic_analyzer(factor_name)
        self.group_analyzer = create_group_analyzer(factor_name)
        
        self.results: Dict[str, Any] = {}
    
    def analyze(
        self,
        factor_df: pd.DataFrame,
        price_df: pd.DataFrame,
        split_date: datetime = None,
        n_groups: int = 5
    ) -> Dict:
        """
        执行完整分析
        
        Args:
            factor_df: 因子数据
            price_df: 价格数据
            split_date: 分界日期
            n_groups: 分组数量
            
        Returns:
            分析结果
        """
        # IC分析
        ic_result = self.ic_analyzer.compute_ic(
            factor_df, price_df, split_date
        )
        
        # 分组收益分析
        group_result = self.group_analyzer.compute_group_returns(
            factor_df, price_df, n_groups, split_date
        )
        
        self.results = {
            'factor_name': self.factor_name,
            'analyze_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'split_date': split_date.strftime('%Y-%m-%d') if split_date else None,
            'n_groups': n_groups,
            'ic_analysis': ic_result,
            'group_analysis': group_result,
            'status': 'success' if 'error' not in ic_result and 'error' not in group_result else 'error'
        }
        
        if 'error' in ic_result:
            self.results['error'] = ic_result['error']
        elif 'error' in group_result:
            self.results['error'] = group_result['error']
        
        return self.results
    
    def generate_charts(self) -> Dict:
        """
        生成所有图表
        
        Returns:
            图表字典
        """
        if 'ic_analysis' not in self.results:
            raise ValueError("请先执行 analyze() 方法")
        
        charts = {}
        
        # IC分析图表
        if 'rolling_ic' in self.results['ic_analysis']:
            rolling_ic = self.results['ic_analysis']['rolling_ic']
            split_date = self.results.get('split_date')
            split_dt = datetime.strptime(split_date, '%Y-%m-%d') if split_date else None
            
            charts['ic_timeseries'] = self.ic_analyzer.plot_ic_timeseries(
                rolling_ic, split_dt
            )
            charts['ic_distribution'] = self.ic_analyzer.plot_ic_distribution(rolling_ic)
            
            # 滚动IC对比
            if isinstance(rolling_ic, pd.DataFrame) and 'date' in rolling_ic.columns:
                charts['rolling_ic_comparison'] = self.ic_analyzer.plot_rolling_ic_comparison(
                    rolling_ic.set_index('date')['IC']
                )
        
        # 分组收益图表
        if 'cumulative_returns' in self.results['group_analysis']:
            cumulative = self.results['group_analysis']['cumulative_returns']
            mean_returns = self.results['group_analysis']['mean_returns']
            
            charts['group_returns_bar'] = self.group_analyzer.plot_group_returns_bar(mean_returns)
            charts['cumulative_returns'] = self.group_analyzer.plot_cumulative_returns(cumulative)
            
            # 多空组合
            if 'Q5' in cumulative.columns and 'Q1' in cumulative.columns:
                charts['long_short'] = self.group_analyzer.plot_long_short(cumulative)
        
        self.results['charts'] = charts
        return charts
    
    def save_charts(self, format: str = 'html') -> Dict:
        """
        保存图表到文件
        
        Args:
            format: 保存格式 (html/png)
            
        Returns:
            保存路径字典
        """
        if 'charts' not in self.results:
            raise ValueError("请先执行 generate_charts() 方法")
        
        saved_paths = {}
        
        for name, fig in self.results['charts'].items():
            if fig is None:
                continue
            
            # 生成文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{self.factor_name}_{name}_{timestamp}"
            
            if format == 'html':
                path = os.path.join(self.output_dir, f"{filename}.html")
                fig.write_html(path)
            elif format == 'png':
                path = os.path.join(self.output_dir, f"{filename}.png")
                fig.write_image(path, scale=2)
            
            saved_paths[name] = path
        
        self.results['saved_charts'] = saved_paths
        return saved_paths
    
    def save_results(self, filename: str = None) -> str:
        """
        保存分析结果到JSON
        
        Args:
            filename: 文件名 (不含扩展名)
            
        Returns:
            保存路径
        """
        if not self.results:
            raise ValueError("请先执行 analyze() 方法")
        
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{self.factor_name}_results_{timestamp}"
        
        # 转换不可序列化的对象
        results_to_save = self.results.copy()
        
        # 移除图表对象
        if 'charts' in results_to_save:
            del results_to_save['charts']
        
        # 转换DataFrame为dict
        for key in ['ic_analysis', 'group_analysis']:
            if key in results_to_save:
                for subkey, value in results_to_save[key].items():
                    if isinstance(value, pd.DataFrame):
                        results_to_save[key][subkey] = value.to_dict('records')
                    elif isinstance(value, pd.Series):
                        results_to_save[key][subkey] = value.to_dict()
        
        # 保存JSON
        path = os.path.join(self.output_dir, f"{filename}.json")
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(results_to_save, f, ensure_ascii=False, indent=2, default=str)
        
        return path
    
    def generate_summary(self) -> str:
        """
        生成文本摘要
        
        Returns:
            摘要文本
        """
        if not self.results or self.results.get('status') == 'error':
            return f"分析失败: {self.results.get('error', '未知错误')}"
        
        lines = [
            "=" * 60,
            f"因子评估报告 - {self.factor_name}",
            "=" * 60,
            f"分析时间: {self.results.get('analyze_date')}",
            f"数据分界: {self.results.get('split_date') or '无'}",
            "",
            "📈 IC分析:",
            "-" * 40,
        ]
        
        ic = self.results.get('ic_analysis', {})
        lines.append(f"  整体IC: {ic.get('ic_all', 0):.4f}")
        lines.append(f"  样本数: {ic.get('samples_all', 0):,}")
        
        if 'ic_train' in ic:
            lines.append(f"  训练集IC: {ic.get('ic_train', 0):.4f}")
            lines.append(f"  测试集IC: {ic.get('ic_test', 0):.4f}")
        
        lines.append("")
        lines.append("📊 分组收益:")
        lines.append("-" * 40)
        
        group = self.results.get('group_analysis', {})
        mean_returns = group.get('mean_returns', pd.Series())
        
        for group_name, ret in mean_returns.items():
            lines.append(f"  {group_name}: {ret*100:.2f}%")
        
        if 'Q5' in mean_returns.index and 'Q1' in mean_returns.index:
            ls_ret = mean_returns['Q5'] - mean_returns['Q1']
            lines.append(f"  多空(Q5-Q1): {ls_ret*100:.2f}%")
        
        lines.append("")
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def print_summary(self):
        """打印摘要"""
        print(self.generate_summary())
    
    def get_metrics(self) -> Dict:
        """
        获取关键指标
        
        Returns:
            指标字典
        """
        if not self.results or self.results.get('status') == 'error':
            return {'error': self.results.get('error', '未知错误')}
        
        ic = self.results.get('ic_analysis', {})
        group = self.results.get('group_analysis', {})
        mean_returns = group.get('mean_returns', pd.Series())
        
        metrics = {
            'factor_name': self.factor_name,
            'ic': ic.get('ic_all', 0),
            'samples': ic.get('samples_all', 0),
            'ic_train': ic.get('ic_train'),
            'ic_test': ic.get('ic_test'),
        }
        
        if not mean_returns.empty:
            metrics['q5_return'] = mean_returns.get('Q5', 0)
            metrics['q1_return'] = mean_returns.get('Q1', 0)
            if 'Q5' in mean_returns.index and 'Q1' in mean_returns.index:
                metrics['long_short_return'] = mean_returns['Q5'] - mean_returns['Q1']
        
        return metrics


def create_report_generator(
    factor_name: str = None,
    output_dir: str = './reports'
) -> FactorReportGenerator:
    """创建报告生成器"""
    return FactorReportGenerator(factor_name, output_dir)


# ==================== 导出 ====================

__all__ = [
    'FactorReportGenerator',
    'create_report_generator',
]
