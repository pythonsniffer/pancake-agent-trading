import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import random

from ..state import TradingState, TradeSignal, TradeExecution, AgentAction

logger = logging.getLogger(__name__)


@dataclass
class BacktestConfig:
    strategy: str = "ARBITRAGE"
    start_date: datetime = None
    end_date: datetime = None
    initial_capital: float = 10000.0
    slippage: float = 0.005
    gas_cost: float = 3.0
    fee_rate: float = 0.0025


@dataclass
class BacktestTrade:
    timestamp: datetime
    type: str
    token_in: str
    token_out: str
    amount: float
    price: float
    slippage: float
    gas_cost: float
    profit: float


class BacktestAgent:
    """
    Backtest Agent: Simulates trading strategies against historical data
    to evaluate performance before live deployment.
    """

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.active_backtests: Dict[str, Any] = {}
        self.results: Dict[str, Any] = {}

    async def run(self, state: TradingState) -> TradingState:
        """Main entry point for the agent"""
        logger.info("Backtest Agent running...")

        try:
            # Check if there's a pending backtest request
            pending_backtest = state.get('config', {}).get('pending_backtest')

            if pending_backtest:
                result = await self.run_backtest(pending_backtest)
                state['config']['backtest_result'] = result
                state['config']['pending_backtest'] = None

            # Create agent action
            action = AgentAction(
                agent_name="BacktestAgent",
                action="check_backtests",
                input_data={"pending": bool(pending_backtest)},
                output_data={
                    "active_backtests": len(self.active_backtests),
                    "completed_results": len(self.results),
                },
                confidence=0.95,
                timestamp=int(datetime.now().timestamp()),
                duration_ms=50,
            )
            state['agent_actions'].append(action)

        except Exception as e:
            logger.error(f"Error in Backtest Agent: {e}", exc_info=True)

        return state

    async def run_backtest(self, config: Dict) -> Dict[str, Any]:
        """Run a backtest simulation"""
        logger.info(f"Starting backtest: {config}")

        backtest_config = BacktestConfig(**config)

        # Generate mock historical data
        candles = self.generate_mock_candles(
            days=30,
            start_price=100.0,
            volatility=0.02
        )

        # Run strategy simulation
        trades = []
        capital = backtest_config.initial_capital
        position = None

        for candle in candles:
            # Simple mean reversion strategy
            if position is None:
                # Check for buy signal
                if candle['rsi'] < 30:  # Oversold
                    position = {
                        'entry_price': candle['close'],
                        'entry_time': candle['timestamp'],
                        'amount': capital * 0.1,  # 10% position
                    }

                    trade = BacktestTrade(
                        timestamp=candle['timestamp'],
                        type="BUY",
                        token_in="USDT",
                        token_out="TOKEN",
                        amount=position['amount'],
                        price=candle['close'],
                        slippage=backtest_config.slippage,
                        gas_cost=backtest_config.gas_cost,
                        profit=0
                    )
                    trades.append(trade)

            else:
                # Check for sell signal
                if candle['rsi'] > 70:  # Overbought
                    # Calculate profit
                    exit_price = candle['close']
                    price_change = (exit_price - position['entry_price']) / position['entry_price']
                    gross_profit = position['amount'] * price_change
                    fees = position['amount'] * backtest_config.fee_rate * 2
                    net_profit = gross_profit - fees - backtest_config.gas_cost

                    trade = BacktestTrade(
                        timestamp=candle['timestamp'],
                        type="SELL",
                        token_in="TOKEN",
                        token_out="USDT",
                        amount=position['amount'],
                        price=exit_price,
                        slippage=backtest_config.slippage,
                        gas_cost=backtest_config.gas_cost,
                        profit=net_profit
                    )
                    trades.append(trade)

                    capital += net_profit
                    position = None

        # Calculate metrics
        metrics = self.calculate_backtest_metrics(trades, backtest_config.initial_capital)

        result = {
            "config": config,
            "trades": [
                {
                    "timestamp": t.timestamp.isoformat(),
                    "type": t.type,
                    "profit": t.profit,
                    "price": t.price,
                }
                for t in trades
            ],
            "metrics": metrics,
            "timestamp": datetime.now().isoformat(),
        }

        self.results[str(datetime.now().timestamp())] = result

        logger.info(f"Backtest complete: {metrics['total_trades']} trades, {metrics['total_return_percent']:.2f}% return")

        return result

    def generate_mock_candles(self, days: int, start_price: float, volatility: float) -> List[Dict]:
        """Generate mock candle data for backtesting"""
        candles = []
        price = start_price

        for i in range(days * 24):  # Hourly candles
            # Random walk
            change = random.gauss(0, volatility)
            price *= (1 + change)

            # Generate OHLC
            open_price = price
            high_price = price * (1 + abs(random.gauss(0, volatility / 2)))
            low_price = price * (1 - abs(random.gauss(0, volatility / 2)))
            close_price = price * (1 + random.gauss(0, volatility / 2))

            # Simple RSI calculation (mock)
            rsi = 30 + random.random() * 40  # 30-70 range

            candles.append({
                'timestamp': datetime.now() - timedelta(hours=days * 24 - i),
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': random.uniform(1000, 10000),
                'rsi': rsi,
            })

        return candles

    def calculate_backtest_metrics(self, trades: List[BacktestTrade], initial_capital: float) -> Dict[str, Any]:
        """Calculate backtest performance metrics"""
        if not trades:
            return {
                "total_trades": 0,
                "win_rate": 0,
                "total_return": 0,
                "total_return_percent": 0,
            }

        total_trades = len([t for t in trades if t.type == "SELL"])
        winning_trades = len([t for t in trades if t.type == "SELL" and t.profit > 0])
        losing_trades = total_trades - winning_trades

        gross_profit = sum(t.profit for t in trades if t.profit > 0)
        gross_loss = abs(sum(t.profit for t in trades if t.profit < 0))

        total_fees = sum(t.amount * 0.0025 for t in trades) * 2
        total_gas = sum(t.gas_cost for t in trades)

        final_capital = initial_capital + sum(t.profit for t in trades)
        total_return = final_capital - initial_capital
        total_return_percent = (total_return / initial_capital) * 100

        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')

        # Calculate Sharpe ratio (simplified)
        returns = [t.profit / initial_capital for t in trades if t.type == "SELL"]
        if len(returns) > 1:
            avg_return = sum(returns) / len(returns)
            variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
            std_dev = variance ** 0.5
            sharpe_ratio = (avg_return / std_dev * (252 ** 0.5)) if std_dev > 0 else 0
        else:
            sharpe_ratio = 0

        # Max drawdown
        peak = initial_capital
        max_drawdown = 0
        current = initial_capital

        for trade in trades:
            if trade.type == "SELL":
                current += trade.profit
                if current > peak:
                    peak = current
                drawdown = (peak - current) / peak
                if drawdown > max_drawdown:
                    max_drawdown = drawdown

        return {
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": win_rate,
            "gross_profit": gross_profit,
            "gross_loss": gross_loss,
            "total_fees": total_fees,
            "total_gas": total_gas,
            "net_profit": total_return,
            "total_return": total_return,
            "total_return_percent": total_return_percent,
            "profit_factor": profit_factor,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown * 100,
            "final_capital": final_capital,
        }

    def get_backtest_results(self) -> Dict[str, Any]:
        """Get all backtest results"""
        return self.results

    def what_if_scenario(self, base_config: Dict, changes: Dict) -> Dict[str, Any]:
        """Run a what-if scenario with modified parameters"""
        modified_config = {**base_config, **changes}
        return asyncio.run(self.run_backtest(modified_config))
