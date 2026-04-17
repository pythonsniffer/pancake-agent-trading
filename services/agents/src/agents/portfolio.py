import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

from web3 import Web3
from ..state import TradingState, TradeExecution, AgentAction

logger = logging.getLogger(__name__)


@dataclass
class Position:
    token_address: str
    token_symbol: str
    amount: float
    entry_price: float
    current_price: float
    value_usd: float
    unrealized_pnl: float
    unrealized_pnl_percent: float


class PortfolioAgent:
    """
    Portfolio Agent: Tracks portfolio value, calculates P&L,
    manages positions, and generates performance reports.
    """

    def __init__(self, w3: Web3 = None, config: Dict = None):
        self.w3 = w3
        self.config = config or {}

        # ERC20 ABI
        self.erc20_abi = [
            {"constant": True, "inputs": [{"name": "_owner", "type": "address"}],
             "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
            {"constant": True, "inputs": [],
             "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
            {"constant": True, "inputs": [],
             "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"},
        ]

        # Portfolio tracking
        self.initial_capital = self.config.get('initial_capital', 10000.0)
        self.current_value = self.initial_capital
        self.total_pnl = 0.0
        self.realized_pnl = 0.0
        self.unrealized_pnl = 0.0

        # Trade history
        self.trades: List[TradeExecution] = []
        self.positions: Dict[str, Position] = {}

        # Performance metrics
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_gas_cost = 0.0

    async def run(self, state: TradingState) -> TradingState:
        """Main entry point for the agent"""
        logger.info("Portfolio Agent running...")

        try:
            # Update portfolio from executed trades
            executed_trades = state.get('executed_trades', [])
            for trade in executed_trades:
                await self.process_trade(trade)

            # Update current prices for positions
            await self.update_position_prices(state)

            # Calculate portfolio metrics
            metrics = await self.calculate_metrics()

            # Update state
            state['portfolio_value'] = self.current_value
            state['positions'] = [
                {
                    'token': pos.token_symbol,
                    'amount': pos.amount,
                    'value_usd': pos.value_usd,
                    'unrealized_pnl': pos.unrealized_pnl,
                    'unrealized_pnl_percent': pos.unrealized_pnl_percent,
                }
                for pos in self.positions.values()
            ]

            # Create agent action
            action = AgentAction(
                agent_name="PortfolioAgent",
                action="update_portfolio",
                input_data={"trades_processed": len(executed_trades)},
                output_data={
                    "portfolio_value": self.current_value,
                    "total_pnl": self.total_pnl,
                    "total_pnl_percent": (self.total_pnl / self.initial_capital * 100),
                    "win_rate": metrics.get('win_rate', 0),
                    "sharpe_ratio": metrics.get('sharpe_ratio', 0),
                },
                confidence=0.95,
                timestamp=int(datetime.now().timestamp()),
                duration_ms=100,
            )
            state['agent_actions'].append(action)

            logger.info(f"Portfolio updated: ${self.current_value:.2f} (PnL: ${self.total_pnl:.2f})")

        except Exception as e:
            logger.error(f"Error in Portfolio Agent: {e}", exc_info=True)

        return state

    async def process_trade(self, trade: TradeExecution) -> None:
        """Process a trade execution and update portfolio"""
        self.trades.append(trade)
        self.total_trades += 1

        # Update P&L
        if trade.status == "SUCCESS":
            self.realized_pnl += trade.actual_profit
            self.total_pnl += trade.actual_profit
            self.current_value += trade.actual_profit

            if trade.actual_profit > 0:
                self.winning_trades += 1
            else:
                self.losing_trades += 1

        # Track gas costs
        self.total_gas_cost += trade.gas_cost_usd

        logger.info(f"Trade processed: {trade.status}, PnL: ${trade.actual_profit:.2f}")

    async def update_position_prices(self, state: TradingState) -> None:
        """Update position prices from current market data"""
        current_prices = state.get('current_prices', {})

        for position in self.positions.values():
            # Find current price for token
            for pool_addr, price_update in current_prices.items():
                # In real implementation, match token to pool
                pass

    async def calculate_metrics(self) -> Dict[str, Any]:
        """Calculate portfolio performance metrics"""
        if self.total_trades == 0:
            return {
                "win_rate": 0,
                "profit_factor": 0,
                "sharpe_ratio": 0,
                "max_drawdown": 0,
            }

        # Win rate
        win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0

        # Profit factor
        gross_profit = sum(t.actual_profit for t in self.trades if t.actual_profit > 0)
        gross_loss = abs(sum(t.actual_profit for t in self.trades if t.actual_profit < 0))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')

        # Calculate returns for Sharpe ratio
        returns = [t.actual_profit / self.initial_capital for t in self.trades]
        if len(returns) > 1:
            avg_return = sum(returns) / len(returns)
            variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
            std_dev = variance ** 0.5
            sharpe_ratio = (avg_return / std_dev * (252 ** 0.5)) if std_dev > 0 else 0  # Annualized
        else:
            sharpe_ratio = 0

        # Max drawdown
        peak = self.initial_capital
        max_drawdown = 0
        for trade in self.trades:
            current_value = self.initial_capital + sum(t.actual_profit for t in self.trades[:self.trades.index(trade) + 1])
            if current_value > peak:
                peak = current_value
            drawdown = (peak - current_value) / peak * 100
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        return {
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "win_rate": win_rate,
            "total_pnl": self.total_pnl,
            "total_pnl_percent": (self.total_pnl / self.initial_capital * 100),
            "realized_pnl": self.realized_pnl,
            "unrealized_pnl": self.unrealized_pnl,
            "profit_factor": profit_factor,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            "total_gas_cost": self.total_gas_cost,
            "avg_profit_per_trade": self.total_pnl / self.total_trades,
        }

    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get portfolio summary for dashboard"""
        return {
            "initial_capital": self.initial_capital,
            "current_value": self.current_value,
            "total_return": self.current_value - self.initial_capital,
            "total_return_percent": ((self.current_value - self.initial_capital) / self.initial_capital * 100),
            "total_trades": self.total_trades,
            "win_rate": (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0,
            "total_pnl": self.total_pnl,
            "positions": len(self.positions),
            "gas_cost": self.total_gas_cost,
        }

    def get_trade_history(self, limit: int = 100) -> List[Dict]:
        """Get recent trade history"""
        return [
            {
                "signal_id": t.signal_id,
                "status": t.status,
                "profit": t.actual_profit,
                "gas_cost": t.gas_cost_usd,
                "tx_hash": t.tx_hash,
                "timestamp": t.timestamp,
            }
            for t in reversed(self.trades[-limit:])
        ]
