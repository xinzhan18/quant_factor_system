"""
因子分析可视化模块
Factor Analysis Visualization Module

功能：
- 因子绩效仪表盘
- HTML 报告生成
- 交互式图表
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import os
import base64
from io import BytesIO

# 可选依赖
try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')  # 无 GUI 后端
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("⚠️ matplotlib 未安装，图表功能受限")


class FactorDashboard:
    """
    因子分析仪表盘
    
    生成可视化的因子分析报告
    """
    
    def __init__(self, output_dir: str = "./data/reports"):
        """
        初始化仪表盘
        
        Args:
            output_dir: 输出目录
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        self.data = {}
        self.charts = {}
    
    def add_factor_performance(self, factor_name: str, performance: Dict):
        """
        添加因子绩效数据
        
        Args:
            factor_name: 因子名称
            performance: 绩效数据
        """
        self.data[factor_name] = performance
    
    def add_ic_series(self, factor_name: str, ic_values: pd.Series):
        """
        添加 IC 时间序列
        
        Args:
            factor_name: 因子名称
            ic_values: IC 值序列
        """
        self.data[f"{factor_name}_ic"] = ic_values
    
    def add_factor_correlation(self, correlation_matrix: pd.DataFrame):
        """
        添加因子相关性
        
        Args:
            correlation_matrix: 相关性矩阵
        """
        self.data['correlation'] = correlation_matrix
    
    def generate_html_report(self, title: str = "因子分析报告") -> str:
        """
        生成 HTML 报告
        
        Args:
            title: 报告标题
            
        Returns:
            HTML 文件路径
        """
        if not HAS_MATPLOTLIB:
            return self._generate_simple_html(title)
        
        # 生成图表
        self._generate_all_charts()
        
        # 生成 HTML
        html = self._build_html(title)
        
        # 保存文件
        filename = f"factor_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return filepath
    
    def _generate_simple_html(self, title: str) -> str:
        """生成简单 HTML 报告（无图表）"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #333; }}
        .summary {{ background: #f5f5f5; padding: 20px; border-radius: 8px; }}
        .metric {{ margin: 10px 0; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        .success {{ color: green; }}
        .failed {{ color: red; }}
    </style>
</head>
<body>
    <h1>📊 {title}</h1>
    <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    
    <div class="summary">
        <h2>📈 因子绩效汇总</h2>
        <table>
            <tr>
                <th>因子名称</th>
                <th>IC</th>
                <th>IC IR</th>
                <th>IC 胜率</th>
                <th>换手率</th>
            </tr>
"""
        
        for name, data in self.data.items():
            if isinstance(data, dict) and 'ic' in data:
                html += f"""
            <tr>
                <td>{name}</td>
                <td>{data.get('ic', 'N/A'):.4f}</td>
                <td>{data.get('ic_ir', 'N/A'):.4f}</td>
                <td>{data.get('ic_sign_ratio', 'N/A'):.2%}</td>
                <td>{data.get('turnover', 'N/A'):.4f}</td>
            </tr>
"""
        
        html += """
        </table>
    </div>
    
    <div class="summary" style="margin-top: 20px;">
        <h2>📋 数据概览</h2>
        <p>系统运行正常，等待更多数据...</p>
    </div>
</body>
</html>
"""
        
        filename = f"factor_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return filepath
    
    def _generate_all_charts(self):
        """生成所有图表"""
        if not HAS_MATPLOTLIB:
            return
        
        # 1. IC 热力图
        if 'correlation' in self.data:
            self._plot_correlation_heatmap()
        
        # 2. 因子 IC 序列
        for name in self.data:
            if name.endswith('_ic') and isinstance(self.data[name], pd.Series):
                factor_name = name.replace('_ic', '')
                self._plot_ic_series(factor_name, self.data[name])
    
    def _plot_correlation_heatmap(self):
        """绘制相关性热力图"""
        corr = self.data['correlation']
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        im = ax.imshow(corr.values, cmap='RdBu_r', vmin=-1, vmax=1)
        
        ax.set_xticks(range(len(corr.columns)))
        ax.set_yticks(range(len(corr.columns)))
        ax.set_xticklabels(corr.columns, rotation=45, ha='right')
        ax.set_yticklabels(corr.columns)
        
        # 添加数值标签
        for i in range(len(corr)):
            for j in range(len(corr)):
                text = ax.text(j, i, f'{corr.values[i, j]:.2f}',
                              ha='center', va='center', fontsize=9)
        
        ax.set_title('因子相关性矩阵')
        plt.colorbar(im, ax=ax)
        plt.tight_layout()
        
        # 保存为 base64
        self.charts['correlation'] = self._fig_to_base64(fig)
        plt.close(fig)
    
    def _plot_ic_series(self, factor_name: str, ic_series: pd.Series):
        """绘制 IC 时间序列"""
        fig, axes = plt.subplots(2, 1, figsize=(12, 8))
        
        # IC 值
        axes[0].plot(ic_series.index, ic_series.values, 'b-', alpha=0.7)
        axes[0].axhline(y=0, color='r', linestyle='--', alpha=0.5)
        axes[0].axhline(y=ic_series.mean(), color='g', linestyle='--', alpha=0.5, 
                        label=f'均值: {ic_series.mean():.4f}')
        axes[0].fill_between(ic_series.index, ic_series.values, 0, alpha=0.3)
        axes[0].set_title(f'{factor_name} - IC 时间序列')
        axes[0].set_ylabel('IC')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)
        
        # IC 累积
        ic_cumsum = ic_series.cumsum()
        axes[1].plot(ic_cumsum.index, ic_cumsum.values, 'g-', linewidth=2)
        axes[1].axhline(y=0, color='r', linestyle='--', alpha=0.5)
        axes[1].set_title(f'{factor_name} - IC 累积和')
        axes[1].set_ylabel('累积 IC')
        axes[1].set_xlabel('日期')
        axes[1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        self.charts[f'{factor_name}_ic'] = self._fig_to_base64(fig)
        plt.close(fig)
    
    def _plot_factor_returns(self, factor_name: str, returns: pd.DataFrame):
        """绘制分组收益"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        colors = plt.cm.RdYlGn(np.linspace(0.2, 0.8, len(returns.columns)))
        
        for i, col in enumerate(returns.columns):
            ax.plot(returns.index, returns[col], label=col, color=colors[i], alpha=0.8)
        
        ax.set_title(f'{factor_name} - 分组收益')
        ax.set_xlabel('日期')
        ax.set_ylabel('累计收益')
        ax.legend(loc='upper left')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        self.charts[f'{factor_name}_returns'] = self._fig_to_base64(fig)
        plt.close(fig)
    
    def _fig_to_base64(self, fig) -> str:
        """将 matplotlib figure 转换为 base64"""
        buf = BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        buf.close()
        return f"data:image/png;base64,{img_str}"
    
    def _build_html(self, title: str) -> str:
        """构建 HTML 内容"""
        charts_html = ""
        
        for name, img_data in self.charts.items():
            charts_html += f"""
            <div class="chart">
                <img src="{img_data}" alt="{name}" style="max-width: 100%;">
            </div>
"""
        
        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: white;
            padding: 30px 40px;
        }}
        
        .header h1 {{
            font-size: 28px;
            margin-bottom: 10px;
        }}
        
        .header .meta {{
            opacity: 0.8;
            font-size: 14px;
        }}
        
        .content {{
            padding: 30px 40px;
        }}
        
        .section {{
            margin-bottom: 40px;
        }}
        
        .section h2 {{
            color: #1a1a2e;
            font-size: 22px;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
        }}
        
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
        }}
        
        .metric-card {{
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            transition: transform 0.3s;
        }}
        
        .metric-card:hover {{
            transform: translateY(-5px);
        }}
        
        .metric-card .value {{
            font-size: 32px;
            font-weight: bold;
            color: #667eea;
        }}
        
        .metric-card .label {{
            color: #666;
            margin-top: 5px;
        }}
        
        .table-container {{
            overflow-x: auto;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        
        th, td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}
        
        th {{
            background: #667eea;
            color: white;
            font-weight: 600;
        }}
        
        tr:hover {{
            background: #f5f5f5;
        }}
        
        .chart {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 12px;
            margin: 20px 0;
        }}
        
        .chart img {{
            width: 100%;
            border-radius: 8px;
        }}
        
        .status-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }}
        
        .status-success {{
            background: #d4edda;
            color: #155724;
        }}
        
        .status-warning {{
            background: #fff3cd;
            color: #856404;
        }}
        
        .status-failed {{
            background: #f8d7da;
            color: #721c24;
        }}
        
        .footer {{
            background: #f8f9fa;
            padding: 20px 40px;
            text-align: center;
            color: #666;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 {title}</h1>
            <div class="meta">
                生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 
                量化因子分析系统 v1.0
            </div>
        </div>
        
        <div class="content">
            <!-- 系统状态 -->
            <div class="section">
                <h2>🔧 系统状态</h2>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="value">🟢</div>
                        <div class="label">运行正常</div>
                    </div>
                    <div class="metric-card">
                        <div class="value">{len(self.data)}</div>
                        <div class="label">因子数量</div>
                    </div>
                    <div class="metric-card">
                        <div class="value">{datetime.now().strftime('%H:%M')}</div>
                        <div class="label">最后更新</div>
                    </div>
                    <div class="metric-card">
                        <div class="value">--</div>
                        <div class="label">数据点数</div>
                    </div>
                </div>
            </div>
            
            <!-- 因子绩效 -->
            <div class="section">
                <h2>📈 因子绩效汇总</h2>
                <div class="table-container">
                    <table>
                        <tr>
                            <th>因子名称</th>
                            <th>IC</th>
                            <th>IC IR</th>
                            <th>IC 胜率</th>
                            <th>换手率</th>
                            <th>多空收益</th>
                            <th>状态</th>
                        </tr>
"""
        
        for name, data in self.data.items():
            if isinstance(data, dict):
                ic = data.get('ic', 0)
                ic_ir = data.get('ic_ir', 0)
                ic_sr = data.get('ic_sign_ratio', 0)
                turnover = data.get('turnover', 0)
                spread = data.get('spread_return', 0)
                
                # 状态判断
                if ic > 0.03:
                    status = '<span class="status-badge status-success">推荐</span>'
                elif ic > 0:
                    status = '<span class="status-badge status-warning">中性</span>'
                else:
                    status = '<span class="status-badge status-failed">不推荐</span>'
                
                html += f"""
                        <tr>
                            <td><strong>{name}</strong></td>
                            <td>{ic:.4f}</td>
                            <td>{ic_ir:.4f}</td>
                            <td>{ic_sr:.2%}</td>
                            <td>{turnover:.4f}</td>
                            <td>{spread:.2%}</td>
                            <td>{status}</td>
                        </tr>
"""
        
        html += """
                    </table>
                </div>
            </div>
            
            <!-- 图表 -->
            <div class="section">
                <h2>📉 因子分析图表</h2>
                """ + charts_html + """
            </div>
            
            <!-- 建议 -->
            <div class="section">
                <h2>💡 投资建议</h2>
                <div class="table-container">
                    <table>
                        <tr>
                            <th>因子</th>
                            <th>建议权重</th>
                            <th>备注</th>
                        </tr>
"""
        
        for name, data in self.data.items():
            if isinstance(data, dict) and 'ic' in data:
                ic = data.get('ic', 0)
                if ic > 0.05:
                    weight = "增持 (+20%)"
                    note = "IC 表现优秀"
                elif ic > 0.02:
                    weight = "维持 (+0%)"
                    note = "IC 表现稳定"
                else:
                    weight = "减持 (-10%)"
                    note = "IC 表现一般"
                
                html += f"""
                        <tr>
                            <td><strong>{name}</strong></td>
                            <td>{weight}</td>
                            <td>{note}</td>
                        </tr>
"""
        
        html += """
                    </table>
                </div>
            </div>
        </div>
        
        <div class="footer">
            © 2024 量化因子分析系统 | Generated by Factor Analysis System
        </div>
    </div>
</body>
</html>
"""
        
        return html


class ReportGenerator:
    """
    报告生成器
    """
    
    def __init__(self, output_dir: str = "./data/reports"):
        """
        初始化
        
        Args:
            output_dir: 输出目录
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.dashboard = FactorDashboard(output_dir)
    
    def generate_daily_report(self, factor_results: Dict[str, Dict]) -> str:
        """
        生成日报
        
        Args:
            factor_results: 因子结果字典
            
        Returns:
            报告文件路径
        """
        for name, data in factor_results.items():
            self.dashboard.add_factor_performance(name, data)
        
        return self.dashboard.generate_html_report(title="每日因子分析报告")
    
    def generate_weekly_report(self, factor_results: Dict[str, Dict],
                              weekly_returns: pd.DataFrame) -> str:
        """
        生成周报
        
        Args:
            factor_results: 因子结果
            weekly_returns: 周收益数据
            
        Returns:
            报告文件路径
        """
        for name, data in factor_results.items():
            self.dashboard.add_factor_performance(name, data)
        
        # 添加周收益图表
        if not weekly_returns.empty:
            for col in weekly_returns.columns[:3]:  # 只显示前3个
                self.dashboard._plot_factor_returns(col, weekly_returns)
        
        return self.dashboard.generate_html_report(title="每周因子分析报告")
    
    def export_json(self, data: Dict, filename: str = None) -> str:
        """
        导出 JSON 数据
        
        Args:
            data: 数据字典
            filename: 文件名
            
        Returns:
            文件路径
        """
        if filename is None:
            filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = os.path.join(self.output_dir, filename)
        
        # 转换 datetime 为字符串
        serializable_data = self._make_serializable(data)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(serializable_data, f, ensure_ascii=False, indent=2)
        
        return filepath
    
    def _make_serializable(self, obj):
        """转换为可序列化格式"""
        if isinstance(obj, pd.Series):
            return obj.to_dict()
        elif isinstance(obj, pd.DataFrame):
            return obj.to_dict(orient='records')
        elif isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._make_serializable(i) for i in obj]
        elif isinstance(obj, datetime):
            return obj.isoformat()
        else:
            return obj


if __name__ == "__main__":
    print("🧪 测试可视化模块...")
    
    # 创建仪表盘
    dashboard = FactorDashboard()
    
    # 添加测试数据
    test_data = {
        'Momentum': {
            'ic': 0.0523,
            'ic_ir': 0.35,
            'ic_sign_ratio': 0.58,
            'turnover': 0.15,
            'spread_return': 0.08
        },
        'Value': {
            'ic': 0.0789,
            'ic_ir': 0.52,
            'ic_sign_ratio': 0.65,
            'turnover': 0.12,
            'spread_return': 0.12
        },
        'Quality': {
            'ic': 0.0312,
            'ic_ir': 0.18,
            'ic_sign_ratio': 0.54,
            'turnover': 0.08,
            'spread_return': 0.04
        }
    }
    
    for name, data in test_data.items():
        dashboard.add_factor_performance(name, data)
    
    # 生成报告
    report_path = dashboard.generate_html_report("量化因子分析报告")
    print(f"✅ 报告已生成: {report_path}")
    
    # 测试报告生成器
    generator = ReportGenerator()
    json_path = generator.export_json(test_data)
    print(f"✅ JSON 已导出: {json_path}")
