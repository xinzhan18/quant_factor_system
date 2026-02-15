"""
回测引擎核心
Backtest Engine Core

功能:
- 模拟交易流程
- 处理选股、仓位、止盈止损
- 生成交易记录
- 计算绩效指标

使用示例:
    from quant_factor_system.backtest import BacktestEngine, BacktestResult
    
    engine = BacktestEngine()
    result = engine.run(
        strategy=selection,
        start_date='20240101',
        end_date='20240131',
        initial_capital=1000000
    )
    
    # 查看结果
    print(result.summary())
    print(result.equity_curve)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime, date
from enum import Enum
import logging
from copy import deepcopy

logger = logging.getLogger(__name__)


class OrderSide(Enum):
    """交易方向"""
    BUY = 'buy'
    SELL = 'sell'


class OrderType(Enum):
    """订单类型"""
    MARKET = 'market'  # 市价单
    LIMIT = 'limit'    # 限价单


@dataclass
class Order:
    """交易订单"""
    order_id: str
    symbol: str
    side: str  # 'buy' or 'sell'
    quantity: int
    price: float
    order_type: str = 'market'
    commission: float = 0.0
    created_at: datetime = None
    filled_at: datetime = None
    filled_price: float = None
    filled_quantity: int = 0
    status: str = 'pending'  # pending, filled, cancelled
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class Position:
    """持仓"""
    symbol: str
    quantity: int = 0
    entry_price: float = 0.0
    entry_date: date = None
    current_price: float = 0.0
    stop_loss_price: float = None
    take_profit_price: float = None
    
    @property
    def market_value(self) -> float:
        return self.quantity * self.current_price
    
    @property
    def profit_loss(self) -> float:
        if self.quantity == 0 or self.entry_price == 0:
            return 0
        return (self.current_price - self.entry_price) / self.entry_price * self.quantity
    
    @property
    def profit_loss_ratio(self) -> float:
        if self.entry_price == 0:
            return 0
        return (self.current_price - self.entry_price) / self.entry_price


@dataclass
class Trade:
    """成交记录"""
    trade_id: str
    symbol: str
    side: str  # 'buy' or 'sell'
    quantity: int
    price: float
    commission: float
    timestamp: datetime
    pnl: float = 0.0  # 盈亏
    pnl_ratio: float = 0.0  # 盈亏比例


@dataclass
class DailyResult:
    """每日结果"""
    date: date
    equity: float
    cash: float
    positions_value: float
    daily_return: float
    accumulated_return: float
    benchmark_return: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            'date': str(self.date),
            'equity': self.equity,
            'cash': self.cash,
            'positions_value': self.positions_value,
            'daily_return': self.daily_return,
            'accumulated_return': self.accumulated_return,
            'benchmark_return': self.benchmark_return
        }


@dataclass
class BacktestResult:
    """回测结果"""
    # 基本信息
    start_date: str
    end_date: str
    initial_capital: float
    final_capital: float
    
    # 交易统计
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    
    # 收益指标
    total_return: float
    annual_return: float
    sharpe_ratio: float
    max_drawdown: float
    
    # 详细数据
    equity_curve: List[Dict] = field(default_factory=list)
    trades: List[Dict] = field(default_factory=list)
    daily_returns: List[float] = field(default_factory=list)
    
    def summary(self) -> Dict:
        return {
            '总收益率': f"{self.total_return*100:.2f}%",
            '年化收益率': f"{self.annual_return*100:.2f}%",
            '夏普比率': f"{self.sharpe_ratio:.2f}",
            '最大回撤': f"{self.max_drawdown*100:.2f}%",
            '总交易次数': self.total_trades,
            '胜率': f"{self.win_rate*100:.2f}%",
            '最终资金': f"{self.final_capital:.2f}",
        }
    
    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(self.equity_curve)


class BacktestEngine:
    """
    回测引擎
    
    功能:
    - 模拟日频交易
    - 处理选股信号
    - 管理仓位
    - 执行止盈止损
    """
    
    def __init__(
        self,
        commission_rate: float = 0.001,  # 佣金费率 (0.1%)
        slippage: float = 0.001,          # 滑点 (0.1%)
        min_commission: float = 5.0        # 最低佣金
    ):
        """
        初始化
        
        Args:
            commission_rate: 佣金费率
            slippage: 滑点
            min_commission: 最低佣金
        """
        self.commission_rate = commission_rate
        self.slippage = slippage
        self.min_commission = min_commission
        
        # 状态
        self.positions: Dict[str, Position] = {}
        self.cash: float = 0
        self.equity: float = 0
        self.orders: List[Order] = []
        self.trades: List[Trade] = []
        self.daily_results: List[DailyResult] = []
        
        # 价格数据缓存
        self.price_data: Dict[str, pd.DataFrame] = {}
    
    def run(
        self,
        strategy,
        price_data: Dict[str, pd.DataFrame],
        start_date: str,
        end_date: str,
        initial_capital: float = 1000000,
        benchmark_symbol: str = None,
        **kwargs
    ) -> BacktestResult:
        """
        运行回测
        
        Args:
            strategy: 策略对象 (包含选股和仓位信息)
            price_data: 价格数据 {symbol: DataFrame}
            start_date: 开始日期
            end_date: 结束日期
            initial_capital: 初始资金
            benchmark_symbol: 基准代码
            
        Returns:
            BacktestResult
        """
        # 1. 初始化
        self._init_backtest(strategy, price_data, initial_capital)
        
        # 2. 获取交易日历
        trading_days = self._get_trading_days(start_date, end_date, price_data)
        
        # 3. 遍历交易日
        current_date = None
        
        for day in trading_days:
            current_date = day
            
            # 更新价格
            self._update_prices(day)
            
            # 检查止盈止损
            self._check_stoploss(day)
            
            # 执行订单
            self._execute_orders(day)
            
            # 生成选股信号 (如果有新信号)
            if hasattr(strategy, 'get_signals'):
                signals = strategy.get_signals(day)
                if signals:
                    self._generate_orders(signals, day)
            
            # 计算每日结果
            self._calculate_daily_result(day)
        
        # 4. 平掉所有持仓
        self._close_all_positions(current_date)
        
        # 5. 计算绩效指标
        result = self._calculate_performance(initial_capital, start_date, end_date)
        
        # 6. 清理
        self._reset()
        
        return result
    
    def _init_backtest(
        self,
        strategy,
        price_data: Dict[str, pd.DataFrame],
        initial_capital: float
    ):
        """初始化回测"""
        self.price_data = price_data
        self.cash = initial_capital
        self.equity = initial_capital
        self.positions = {}
        self.orders = []
        self.trades = []
        self.daily_results = []
        
        logger.info(f"✅ 回测初始化: 初始资金={initial_capital}")
    
    def _get_trading_days(
        self,
        start_date: str,
        end_date: str,
        price_data: Dict[str, pd.DataFrame]
    ) -> List[date]:
        """获取交易日"""
        # 合并所有股票的日期
        all_dates = set()
        
        for symbol, df in price_data.items():
            if 'datetime' in df.columns:
                dates = pd.to_datetime(df['datetime']).dt.date
            elif 'date' in df.columns:
                dates = pd.to_datetime(df['date']).dt.date
            else:
                dates = pd.to_datetime(df.index).date
            
            all_dates.update(dates.tolist())
        
        # 过滤日期范围
        start = pd.to_datetime(start_date).date()
        end = pd.to_datetime(end_date).date()
        
        trading_days = sorted([d for d in all_dates if start <= d <= end])
        
        return trading_days
    
    def _update_prices(self, current_date: date):
        """更新价格"""
        for symbol, position in self.positions.items():
            if symbol in self.price_data:
                df = self.price_data[symbol]
                
                # 获取当日价格
                if 'datetime' in df.columns:
                    mask = pd.to_datetime(df['datetime']).dt.date == current_date
                elif 'date' in df.columns:
                    mask = pd.to_datetime(df['date']).dt.date == current_date
                else:
                    mask = df.index.date == current_date
                
                if mask.any():
                    price_row = df[mask].iloc[0]
                    if 'close' in price_row:
                        position.current_price = price_row['close']
                    else:
                        position.current_price = price_row.iloc[0]
    
    def _check_stoploss(self, current_date: date):
        """检查止盈止损"""
        orders_to_create = []
        
        for symbol, position in self.positions.items():
            if position.quantity == 0:
                continue
            
            # 检查是否触发止盈止损
            should_close = False
            reason = ''
            
            # 止损检查
            if position.stop_loss_price is not None:
                if position.current_price <= position.stop_loss_price:
                    should_close = True
                    reason = 'stop_loss'
            
            # 止盈检查
            if not should_close and position.take_profit_price is not None:
                if position.current_price >= position.take_profit_price:
                    should_close = True
                    reason = 'stop_profit'
            
            # 生成卖出订单
            if should_close:
                orders_to_create.append({
                    'symbol': symbol,
                    'side': 'sell',
                    'quantity': position.quantity,
                    'reason': reason
                })
        
        # 执行卖出订单
        for order_info in orders_to_create:
            self._create_order(
                symbol=order_info['symbol'],
                side='sell',
                quantity=order_info['quantity'],
                current_date=current_date,
                reason=order_info['reason']
            )
    
    def _generate_orders(
        self,
        signals: Dict[str, float],
        current_date: date
    ):
        """
        生成订单
        
        Args:
            signals: {symbol: factor_value} 选股信号
        """
        # 1. 卖出现在有但信号中没有的持仓
        for symbol in list(self.positions.keys()):
            if symbol not in signals and self.positions[symbol].quantity > 0:
                self._create_order(
                    symbol=symbol,
                    side='sell',
                    quantity=self.positions[symbol].quantity,
                    current_date=current_date
                )
        
        # 2. 买入信号中的股票
        for symbol, factor_value in signals.items():
            # 如果没有持仓，创建买入订单
            if symbol not in self.positions or self.positions[symbol].quantity == 0:
                # 获取当前价格
                if symbol in self.price_data:
                    df = self.price_data[symbol]
                    
                    if 'datetime' in df.columns:
                        latest = df.iloc[-1]
                        if 'open' in df.columns:
                            price = latest['open']
                        else:
                            price = latest.iloc[0]
                    else:
                        price = df.iloc[-1, 0]
                    
                    # 计算买入数量
                    available_cash = self.cash / len(signals)
                    quantity = int(available_cash / price / 100) * 100
                    
                    if quantity > 0:
                        self._create_order(
                            symbol=symbol,
                            side='buy',
                            quantity=quantity,
                            current_date=current_date,
                            price=price
                        )
    
    def _create_order(
        self,
        symbol: str,
        side: str,
        quantity: int,
        current_date: date,
        price: float = None,
        reason: str = ''
    ):
        """创建订单"""
        # 获取价格
        if price is None:
            if symbol in self.price_data:
                df = self.price_data[symbol]
                if 'open' in df.columns:
                    price = df.iloc[-1]['open']
                else:
                    price = df.iloc[-1].iloc[0]
            else:
                price = 10.0
        
        # 创建订单
        order = Order(
            order_id=f"{current_date}_{symbol}_{side}_{quantity}",
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=price,
            created_at=datetime.combine(current_date, datetime.min.time())
        )
        
        self.orders.append(order)
        
        logger.debug(f"📝 创建订单: {order.symbol} {order.side} {order.quantity}")
    
    def _execute_orders(self, current_date: date):
        """执行订单"""
        orders_to_remove = []
        
        for i, order in enumerate(self.orders):
            if order.status != 'pending':
                continue
            
            # 获取价格
            if order.price is None:
                if order.symbol in self.price_data:
                    df = self.price_data[order.symbol]
                    if 'open' in df.columns:
                        order.price = df.iloc[-1]['open']
                    else:
                        order.price = df.iloc[-1].iloc[0]
                else:
                    order.price = 10.0
            
            # 应用滑点
            execution_price = order.price
            if order.side == 'buy':
                execution_price = execution_price * (1 + self.slippage)
            else:
                execution_price = execution_price * (1 - self.slippage)
            
            # 计算佣金
            turnover = execution_price * order.quantity
            commission = max(turnover * self.commission_rate, self.min_commission)
            
            # 执行订单
            order.filled_at = datetime.combine(current_date, datetime.min.time())
            order.filled_price = execution_price
            order.filled_quantity = order.quantity
            order.status = 'filled'
            order.commission = commission
            
            # 更新现金
            if order.side == 'buy':
                self.cash -= (turnover + commission)
            else:
                self.cash += (turnover - commission)
            
            # 更新持仓
            self._update_position(order, current_date)
            
            # 记录成交
            self._record_trade(order, current_date)
            
            orders_to_remove.append(i)
        
        # 移除已完成的订单
        for i in reversed(orders_to_remove):
            self.orders.pop(i)
    
    def _update_position(self, order: Order, current_date: date):
        """更新持仓"""
        symbol = order.symbol
        
        if symbol not in self.positions:
            self.positions[symbol] = Position(
                symbol=symbol,
                quantity=0,
                entry_price=0,
                entry_date=current_date
            )
        
        position = self.positions[symbol]
        
        if order.side == 'buy':
            # 计算新的平均成本
            total_cost = position.quantity * position.entry_price + order.filled_quantity * order.filled_price
            total_qty = position.quantity + order.filled_quantity
            
            if total_qty > 0:
                position.entry_price = total_cost / total_qty
            
            position.quantity += order.filled_quantity
            
            if position.entry_date is None:
                position.entry_date = current_date
        
        else:  # sell
            position.quantity -= order.filled_quantity
            
            if position.quantity == 0:
                position.entry_price = 0
    
    def _record_trade(self, order: Order, current_date: date):
        """记录成交"""
        trade = Trade(
            trade_id=f"trade_{len(self.trades)+1}",
            symbol=order.symbol,
            side=order.side,
            quantity=order.filled_quantity,
            price=order.filled_price,
            commission=order.commission,
            timestamp=order.filled_at
        )
        
        # 计算盈亏
        position = self.positions.get(order.symbol)
        if position and order.side == 'sell':
            trade.pnl = (order.filled_price - position.entry_price) * order.filled_quantity
            if position.entry_price > 0:
                trade.pnl_ratio = (order.filled_price - position.entry_price) / position.entry_price
        
        self.trades.append(asdict(trade))
    
    def _calculate_daily_result(self, current_date: date):
        """计算每日结果"""
        # 计算持仓市值
        positions_value = sum(
            pos.current_price * pos.quantity
            for pos in self.positions.values()
            if pos.quantity > 0
        )
        
        # 计算权益
        self.equity = self.cash + positions_value
        
        # 计算日收益率
        if len(self.daily_results) > 0:
            prev_equity = self.daily_results[-1].equity
            daily_return = (self.equity - prev_equity) / prev_equity if prev_equity > 0 else 0
        else:
            daily_return = 0
        
        # 计算累计收益率
        if len(self.daily_results) > 0:
            accumulated_return = (self.equity - self.daily_results[0].equity) / self.daily_results[0].equity
        else:
            accumulated_return = 0
        
        # 记录
        result = DailyResult(
            date=current_date,
            equity=self.equity,
            cash=self.cash,
            positions_value=positions_value,
            daily_return=daily_return,
            accumulated_return=accumulated_return
        )
        
        self.daily_results.append(result)
    
    def _close_all_positions(self, current_date: date):
        """平掉所有持仓"""
        for symbol, position in list(self.positions.items()):
            if position.quantity > 0:
                self._create_order(
                    symbol=symbol,
                    side='sell',
                    quantity=position.quantity,
                    current_date=current_date,
                    reason='final_close'
                )
        
        # 执行所有订单
        self._execute_orders(current_date)
    
    def _calculate_performance(
        self,
        initial_capital: float,
        start_date: str,
        end_date: str
    ) -> BacktestResult:
        """计算绩效指标"""
        # 基本信息
        final_capital = self.equity
        total_return = (final_capital - initial_capital) / initial_capital
        
        # 交易日数
        trading_days = len(self.daily_results)
        
        # 年化收益率 (假设252交易日)
        annual_return = (1 + total_return) ** (252 / trading_days) - 1 if trading_days > 0 else 0
        
        # 夏普比率
        if len(self.daily_results) > 1:
            returns = [d.daily_return for d in self.daily_results]
            mean_return = np.mean(returns)
            std_return = np.std(returns)
            
            if std_return > 0:
                sharpe_ratio = mean_return / std_return * np.sqrt(252)
            else:
                sharpe_ratio = 0
        else:
            sharpe_ratio = 0
        
        # 最大回撤
        equity_curve = [d.equity for d in self.daily_results]
        max_drawdown = self._calculate_max_drawdown(equity_curve)
        
        # 交易统计
        winning_trades = len([t for t in self.trades if t.get('pnl', 0) > 0])
        losing_trades = len([t for t in self.trades if t.get('pnl', 0) <= 0])
        total_trades = len(self.trades)
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # 转换为DataFrame
        equity_curve_data = [d.to_dict() for d in self.daily_results]
        
        return BacktestResult(
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            final_capital=final_capital,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            total_return=total_return,
            annual_return=annual_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            equity_curve=equity_curve_data,
            trades=self.trades,
            daily_returns=[d.daily_return for d in self.daily_results]
        )
    
    def _calculate_max_drawdown(self, equity_curve: List[float]) -> float:
        """计算最大回撤"""
        if not equity_curve:
            return 0
        
        max_drawdown = 0
        peak = equity_curve[0]
        
        for equity in equity_curve:
            if equity > peak:
                peak = equity
            
            drawdown = (peak - equity) / peak if peak > 0 else 0
            max_drawdown = max(max_drawdown, drawdown)
        
        return max_drawdown
    
    def _reset(self):
        """重置状态"""
        self.positions = {}
        self.cash = 0
        self.equity = 0
        self.orders = []
        self.trades = []
        self.daily_results = []
        self.price_data = {}


# ==================== 导出 ====================

__all__ = [
    'BacktestEngine',
    'BacktestResult',
    'Trade',
    'Position',
    'Order',
    'DailyResult',
    'OrderSide',
    'OrderType',
]
