"""
工程化因子评估框架
Engineering Factor Evaluation Framework

标准因子评估架构：
1. 数据对齐：因子(t) → 收益(t+1)
2. 因子预处理：去极值、标准化、中性化
3. IC计算：前一期因子 vs 当期收益
4. 分组回测：信号日选股，t+1计算收益
5. 交易成本：滑点、手续费、印花税
6. 绩效归因：收益分解、风险分析
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


# ========== 配置类 ==========

@dataclass
class BacktestConfig:
    """回测配置"""
    # 分组设置
    num_groups: int = 5           # 分组数量
    rebalance_period: int = 20    # 调仓周期（天）
    top_n: int = 10              # 选股数量
    
    # 交易成本
    commission_rate: float = 0.001  # 手续费 (0.1%)
    stamp_tax_rate: float = 0.001    # 印花税 (0.1%, 卖出时收)
    slippage_type: str = "fixed"    # 滑点类型: "fixed" 或 "percent"
    slippage_rate: float = 0.001     # 滑点率 (0.1%)
    
    # 因子处理
    winsorize: bool = True       # 是否去极值
    winsorize_level: float = 0.02  # 去极值比例
    standardize: bool = True     # 是否标准化
    neutralize_market_cap: bool = True  # 是否市值中性化
    neutralize_industry: bool = True     # 是否行业中性化
    
    # 数据过滤
    filter_limit: bool = True    # 是否过滤涨跌停
    min_price: float = 3.0       # 最低价格
    min_market_cap: float = 1e9  # 最低市值


@dataclass
class FactorResult:
    """因子评估结果"""
    factor_name: str
    ic: float = 0.0
    ic_ir: float = 0.0
    ic_sign_ratio: float = 0.0
    ic_series: pd.Series = None
    
    # 分组收益
    group_returns: Dict[str, float] = field(default_factory=dict)
    long_short_return: float = 0.0  # 多空收益
    long_short_sharpe: float = 0.0  # 多空夏普
    
    # 换手率
    turnover: float = 0.0
    
    # 交易成本
    total_commission: float = 0.0
    total_slippage: float = 0.0
    net_return: float = 0.0


# ========== 数据对齐工具 ==========

def align_factor_returns(factor: pd.Series, 
                        returns: pd.Series,
                        shift: int = 1) -> Tuple[pd.Series, pd.Series]:
    """
    对齐因子和收益数据
    
    关键：因子在 t 期，收益在 t+1 期
    使用 shift 实现前视偏差的规避
    
    Args:
        factor: 因子值
        returns: 收益率
        shift: 收益偏移期数 (1 = t+1)
        
    Returns:
        (对齐后的因子, 对齐后的收益)
    """
    # 因子保持不变
    factor_aligned = factor.dropna()
    
    # 收益向前移动（使用过去收益）
    # return_{t+1} 的 IC 计算需要 factor_t vs return_{t+1}
    # 实际操作：factor_t vs return_shifted (return_{t+1})
    returns_shifted = returns.shift(shift)
    
    # 取交集
    common_index = factor_aligned.index.intersection(returns_shifted.dropna().index)
    
    return factor_aligned.loc[common_index], returns_shifted.loc[common_index]


def create_return_series(price: pd.Series, 
                        forward: int = 1) -> pd.Series:
    """
    创建未来收益序列
    
    Args:
        price: 价格序列
        forward: 未来期数 (1 = t+1收益)
        
    Returns:
        未来收益率序列
    """
    return price.pct_change(forward).shift(-forward)


# ========== 因子预处理 ==========

class FactorPreprocessor:
    """
    因子预处理器
    """
    
    def __init__(self, config: BacktestConfig = None):
        self.config = config or BacktestConfig()
    
    def winsorize(self, factor: pd.Series, 
                  level: float = 0.02) -> pd.Series:
        """
        去极值 (Winsorize)
        
        将超出 [level, 1-level] 分位数的值截断
        """
        lower = factor.quantile(level)
        upper = factor.quantile(1 - level)
        
        factor_clean = factor.clip(lower, upper)
        return factor_clean
    
    def standardize(self, factor: pd.Series) -> pd.Series:
        """
        标准化 (Z-score)
        """
        mean = factor.mean()
        std = factor.std()
        
        if std == 0:
            return factor - mean
        
        return (factor - mean) / std
    
    def neutralize_market_cap(self, factor: pd.Series,
                               market_cap: pd.Series) -> pd.Series:
        """
        市值中性化
        """
        try:
            import statsmodels.api as sm
            
            # 对齐数据
            common = factor.index.intersection(market_cap.index)
            if len(common) < 10:
                return factor
            
            X = sm.add_constant(np.log(market_cap.loc[common]))
            y = factor.loc[common]
            
            model = sm.OLS(y, X).fit()
            residual = model.resid
            
            # 返回原始索引
            result = pd.Series(index=factor.index, dtype=float)
            result.loc[common] = residual
            result.loc[~result.index.isin(common)] = np.nan
            
            return result
            
        except ImportError:
            print("⚠️ statsmodels 未安装，跳过中性化")
            return factor
    
    def neutralize_industry(self, factor: pd.Series,
                           industry: pd.Series) -> pd.Series:
        """
        行业中性化
        """
        try:
            import statsmodels.api as sm
            
            common = factor.index.intersection(industry.index)
            if len(common) < 10:
                return factor
            
            # 行业虚拟变量
            industry_dummies = pd.get_dummies(industry.loc[common], prefix='ind')
            
            X = sm.add_constant(industry_dummies)
            y = factor.loc[common]
            
            model = sm.OLS(y, X).fit()
            residual = model.resid
            
            result = pd.Series(index=factor.index, dtype=float)
            result.loc[common] = residual
            result.loc[~result.index.isin(common)] = np.nan
            
            return result
            
        except ImportError:
            return factor
    
    def process(self, factor: pd.Series,
                market_cap: pd.Series = None,
                industry: pd.Series = None) -> pd.Series:
        """
        完整预处理流程
        """
        result = factor.copy()
        
        # 去极值
        if self.config.winsorize:
            result = self.winsorize(result, self.config.winsorize_level)
        
        # 标准化
        if self.config.standardize:
            result = self.standardize(result)
        
        # 中性化
        if self.config.neutralize_market_cap and market_cap is not None:
            result = self.neutralize_market_cap(result, market_cap)
        
        if self.config.neutralize_industry and industry is not None:
            result = self.neutralize_industry(result, industry)
        
        return result


# ========== IC 计算 ==========

class ICAnalyzer:
    """
    IC 分析器
    """
    
    @staticmethod
    def calculate_ic(factor: pd.Series, 
                     returns: pd.Series) -> Dict[str, float]:
        """
        计算 IC 统计量
        
        Args:
            factor: 因子值 (t期)
            returns: 收益率 (t+1期)
            
        Returns:
            IC 统计字典
        """
        # 对齐数据
        factor_aligned, returns_aligned = align_factor_returns(factor, returns)
        
        if len(factor_aligned) < 30:
            return {'ic': 0, 'ic_ir': 0, 'ic_sign_ratio': 0}
        
        # 确保索引一致
        common_idx = factor_aligned.index.intersection(returns_aligned.index)
        if len(common_idx) == 0:
            return {'ic': 0, 'ic_ir': 0, 'ic_sign_ratio': 0}
        
        factor_aligned = factor_aligned.loc[common_idx]
        returns_aligned = returns_aligned.loc[common_idx]
        
        # 计算 IC
        ic = factor_aligned.corr(returns_aligned)
        
        # IC 均值
        ic_mean = ic
        
        # IC 标准差
        ic_std = factor_aligned.corr(returns_aligned) if False else factor_aligned.std()
        
        # IC_IR = IC / IC标准差
        # 简化计算
        ic_ir = abs(ic) / (factor_aligned.std() + 1e-8)
        
        # IC 胜率 - 使用 pandas corr 确保索引一致
        ic_sign_ratio = (np.sign(factor_aligned.values) == np.sign(returns_aligned.values)).mean()
        
        return {
            'ic': ic,
            'ic_ir': ic_ir,
            'ic_sign_ratio': ic_sign_ratio
        }
    
    @staticmethod
    def calculate_ic_decay(factor: pd.Series,
                          returns: pd.Series,
                          lags: List[int] = None) -> pd.DataFrame:
        """
        计算 IC 衰减
        
        IC_decay(k) = corr(factor_{t-k}, return_t)
        """
        if lags is None:
            lags = [1, 2, 3, 4, 5, 10, 20, 60]
        
        decay = {}
        
        for lag in lags:
            factor_lagged = factor.shift(lag)
            
            common = factor_lagged.dropna().index.intersection(returns.dropna().index)
            
            if len(common) > 30:
                ic = factor_lagged.loc[common].corr(returns.loc[common])
                decay[f'lag_{lag}'] = ic
        
        return pd.Series(decay)


# ========== 分组回测 ==========

class GroupBacktester:
    """
    分组回测器
    """
    
    def __init__(self, config: BacktestConfig = None):
        self.config = config or BacktestConfig()
        self.preprocessor = FactorPreprocessor(config)
    
    def create_groups(self, factor: pd.Series, 
                      n_groups: int = 5) -> pd.Series:
        """
        创建分组标签
        
        Returns:
            分组标签序列
        """
        return pd.qcut(factor, q=n_groups, labels=[f'Q{i+1}' for i in range(n_groups)])
    
    def calculate_group_returns(self, 
                               factor: pd.Series,
                               returns: pd.Series,
                               n_groups: int = 5) -> Tuple[pd.DataFrame, Dict]:
        """
        计算分组收益
        
        Args:
            factor: 因子值 (t期)
            returns: 收益率 (t+1期)
            n_groups: 分组数
            
        Returns:
            (分组收益表, 统计信息)
        """
        # 对齐数据
        factor_aligned, returns_aligned = align_factor_returns(factor, returns, shift=1)
        
        if len(factor_aligned) < 100:
            return pd.DataFrame(), {}
        
        # 确保索引一致
        common_idx = factor_aligned.index.intersection(returns_aligned.index)
        if len(common_idx) == 0:
            return pd.DataFrame(), {}
        
        factor_aligned = factor_aligned.loc[common_idx]
        returns_aligned = returns_aligned.loc[common_idx]
        
        # 创建分组
        groups = self.create_groups(factor_aligned, n_groups)
        
        # 计算每组收益 - 使用 .loc 确保索引一致
        group_rets = {}
        for g in [f'Q{i+1}' for i in range(n_groups)]:
            mask = groups == g
            if mask.sum() > 0:
                group_rets[g] = returns_aligned.loc[mask].mean()
        
        # 计算多空收益
        if 'Q1' in group_rets and 'Q5' in group_rets:
            long_short = group_rets['Q5'] - group_rets['Q1']  # Long Q5, Short Q1
        else:
            long_short = 0
        
        stats = {
            'long_short_return': long_short,
            'num_groups': n_groups,
            'total_samples': len(factor_aligned)
        }
        
        # 转换为 DataFrame
        if group_rets:
            group_df = pd.DataFrame(pd.Series(group_rets), columns=['return'])
        else:
            group_df = pd.DataFrame()
        
        return group_df, stats
    
    def calculate_turnover(self,
                          factor: pd.Series,
                          n_groups: int = 5) -> float:
        """
        计算分组换手率
        """
        groups = self.create_groups(factor, n_groups)
        
        # 计算分组变化
        group_changes = groups != groups.shift(1)
        
        return group_changes.mean()
    
    def run_backtest(self,
                     factor: pd.Series,
                     returns: pd.Series,
                     n_groups: int = None) -> Tuple[pd.DataFrame, Dict]:
        """
        运行分组回测
        
        Returns:
            (分组收益表, 回测统计)
        """
        n_groups = n_groups or self.config.num_groups
        
        group_rets, stats = self.calculate_group_returns(
            factor, returns, n_groups
        )
        
        if group_rets.empty:
            return group_rets, stats
        
        # 计算换手率
        turnover = self.calculate_turnover(factor, n_groups)
        stats['turnover'] = turnover
        
        # 计算多空夏普
        if 'Q5' in group_rets.columns and 'Q1' in group_rets.columns:
            ls_ret = group_rets['Q5'] - group_rets['Q1']
            stats['long_short_sharpe'] = ls_ret.mean() / (ls_ret.std() + 1e-8) * np.sqrt(252)
        
        return group_rets, stats


# ========== 交易成本模型 ==========

class TransactionCostCalculator:
    """
    交易成本计算器
    """
    
    def __init__(self, config: BacktestConfig = None):
        self.config = config or BacktestConfig()
    
    def calculate_commission(self, trade_value: float, 
                            is_buy: bool = True) -> float:
        """
        计算手续费
        
        Args:
            trade_value: 交易金额
            is_buy: 是否买入
        """
        # 买入：只有手续费
        # 卖出：手续费 + 印花税
        if is_buy:
            return trade_value * self.config.commission_rate
        else:
            return trade_value * (self.config.commission_rate + self.config.stamp_tax_rate)
    
    def calculate_slippage(self, price: float, 
                          size: float = 1.0) -> float:
        """
        计算滑点
        
        Args:
            price: 成交价格
            size: 交易规模因子
        """
        if self.config.slippage_type == "fixed":
            # 固定滑点
            return price * self.config.slippage_rate * size
        else:
            # 比例滑点
            return price * self.config.slippage_rate * size
    
    def calculate_total_cost(self, 
                            portfolio_value: float,
                            turnover_rate: float) -> Dict[str, float]:
        """
        计算总交易成本
        
        Args:
            portfolio_value: 组合净值
            turnover_rate: 换手率
        """
        # 假设每次换仓交易金额 = 组合净值 × 换手率
        trade_value = portfolio_value * turnover_rate
        
        # 每次换仓涉及买卖，假设一次完整换仓
        # 买入 + 卖出
        buy_cost = self.calculate_commission(trade_value, is_buy=True)
        sell_cost = self.calculate_commission(trade_value, is_buy=False)
        
        total_commission = buy_cost + sell_cost
        total_slippage = self.calculate_slippage(1.0) * portfolio_value * turnover_rate
        
        return {
            'commission': total_commission,
            'slippage': total_slippage,
            'total_cost': total_commission + total_slippage
        }


# ========== 综合因子评估器 ==========

class FactorEvaluator:
    """
    综合因子评估器
    """
    
    def __init__(self, config: BacktestConfig = None):
        self.config = config or BacktestConfig()
        self.preprocessor = FactorPreprocessor(config)
        self.ic_analyzer = ICAnalyzer()
        self.backtester = GroupBacktester(config)
        self.cost_calculator = TransactionCostCalculator(config)
        
        self.results: Dict[str, FactorResult] = {}
    
    def evaluate(self, 
                factor_name: str,
                factor: pd.Series,
                returns: pd.Series,
                market_cap: pd.Series = None,
                industry: pd.Series = None) -> FactorResult:
        """
        综合因子评估
        
        Args:
            factor_name: 因子名称
            factor: 原始因子值
            returns: 收益率序列 (t期)
            market_cap: 市值序列
            industry: 行业序列
            
        Returns:
            因子评估结果
        """
        result = FactorResult(factor_name=factor_name)
        
        # 1. 预处理因子
        factor_processed = self.preprocessor.process(
            factor, market_cap, industry
        )
        
        # 2. 对齐数据 (因子t期, 收益t+1期)
        factor_aligned, returns_aligned = align_factor_returns(
            factor_processed, returns, shift=1
        )
        
        # 确保索引一致
        common_idx = factor_aligned.index.intersection(returns_aligned.index)
        if len(common_idx) < 30:
            print(f"⚠️ {factor_name}: 数据不足")
            return result
        
        factor_aligned = factor_aligned.loc[common_idx]
        returns_aligned = returns_aligned.loc[common_idx]
        
        # 3. IC 分析
        ic_stats = self.ic_analyzer.calculate_ic(factor_aligned, returns_aligned)
        result.ic = ic_stats['ic']
        result.ic_ir = ic_stats['ic_ir']
        result.ic_sign_ratio = ic_stats['ic_sign_ratio']
        
        # 4. 分组回测
        group_rets, stats = self.backtester.run_backtest(
            factor_aligned, returns_aligned
        )
        
        result.group_returns = group_rets.to_dict() if not group_rets.empty else {}
        result.long_short_return = stats.get('long_short_return', 0)
        result.long_short_sharpe = stats.get('long_short_sharpe', 0)
        result.turnover = stats.get('turnover', 0)
        
        # 5. 交易成本估算
        costs = self.cost_calculator.calculate_total_cost(
            portfolio_value=1.0,
            turnover_rate=result.turnover
        )
        result.total_commission = costs['commission']
        result.total_slippage = costs['slippage']
        
        # 6. 净收益 (扣除成本后)
        result.net_return = result.long_short_return - costs['total_cost']
        
        self.results[factor_name] = result
        
        return result
    
    def evaluate_multiple(self,
                         factors: Dict[str, pd.Series],
                         returns: pd.Series,
                         market_cap: pd.Series = None,
                         industry: pd.Series = None) -> Dict[str, FactorResult]:
        """
        批量评估多个因子
        """
        results = {}
        
        for name, factor in factors.items():
            results[name] = self.evaluate(
                name, factor, returns, market_cap, industry
            )
        
        return results
    
    def print_report(self):
        """打印评估报告"""
        print("\n" + "="*80)
        print("📊 工程化因子评估报告")
        print("="*80)
        
        print(f"\n🔧 配置信息:")
        print(f"  分组数: {self.config.num_groups}")
        print(f"  手续费率: {self.config.commission_rate:.3f}")
        print(f"  印花税率: {self.config.stamp_tax_rate:.3f}")
        print(f"  滑点率: {self.config.slippage_rate:.3f}")
        print(f"  去极值: {self.config.winsorize}")
        print(f"  市值中性化: {self.config.neutralize_market_cap}")
        print(f"  行业中性化: {self.config.neutralize_industry}")
        
        print(f"\n📈 因子评估结果:")
        print("-"*80)
        print(f"{'因子':<15} {'IC':<10} {'IC_IR':<10} {'胜率':<10} {'多空收益':<12} {'夏普':<10} {'换手率':<10}")
        print("-"*80)
        
        for name, result in self.results.items():
            status = "✅" if abs(result.ic) > 0.03 else ("⚠️" if abs(result.ic) > 0 else "❌")
            print(f"{status} {name:<13} {result.ic:<10.4f} {result.ic_ir:<10.4f} "
                  f"{result.ic_sign_ratio:<10.2%} {result.long_short_return:<12.4f} "
                  f"{result.long_short_sharpe:<10.4f} {result.turnover:<10.4f}")
        
        print("-"*80)
        
        print(f"\n💰 交易成本估算:")
        for name, result in self.results.items():
            print(f"  {name}: 佣金={result.total_commission:.6f}, 滑点={result.total_slippage:.6f}")
        
        print("\n" + "="*80)
    
    def get_summary(self) -> Dict[str, Any]:
        """获取汇总信息"""
        return {
            'config': self.config.__dict__,
            'results': {
                name: {
                    'ic': r.ic,
                    'ic_ir': r.ic_ir,
                    'ic_sign_ratio': r.ic_sign_ratio,
                    'long_short_return': r.long_short_return,
                    'long_short_sharpe': r.long_short_sharpe,
                    'turnover': r.turnover,
                    'net_return': r.net_return
                }
                for name, r in self.results.items()
            }
        }


# ========== 示例 ==========

if __name__ == "__main__":
    print("🧪 测试工程化因子评估框架...")
    
    # 创建配置
    config = BacktestConfig(
        num_groups=5,
        rebalance_period=20,
        commission_rate=0.001,  # 万1
        stamp_tax_rate=0.001,   # 千1
        slippage_rate=0.001,    # 千1
        winsorize=True,
        neutralize_market_cap=True,
        neutralize_industry=True
    )
    
    # 创建评估器
    evaluator = FactorEvaluator(config)
    
    # 创建测试数据
    np.random.seed(42)
    dates = pd.date_range('2020-01-01', periods=1000, freq='B')
    n = len(dates)
    
    factor = pd.Series(np.random.randn(n) * 0.1 + 0.02, index=dates)
    returns = pd.Series(np.random.randn(n) * 0.02 + 0.01, index=dates)
    market_cap = pd.Series(np.random.uniform(1e9, 1e11, n), index=dates)
    industry = pd.Series(np.random.choice(['银行', '科技', '消费'], n), index=dates)
    
    # 评估因子
    result = evaluator.evaluate('TestFactor', factor, returns, market_cap, industry)
    
    # 打印报告
    evaluator.print_report()
    
    print("\n✅ 工程化框架测试完成!")
