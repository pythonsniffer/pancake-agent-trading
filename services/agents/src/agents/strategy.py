import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
import uuid

from ..state import (
    TradingState, TradeSignal, PoolInfo, TokenInfo,
    PriceUpdate, AgentAction
)

logger = logging.getLogger(__name__)


@dataclass
class StrategyConfig:
    min_profit_threshold: float = 1.0  # USD
    min_confidence: float = 0.7
    max_slippage: float = 0.005  # 0.5%
    stop_loss_percent: float = 0.05  # 5%
    take_profit_percent: float = 0.10  # 10%
    position_sizing: str = "fixed"  # fixed, kelly, percentage
    max_position_size: float = 500.0  # USD


class StrategyAgent:
    """
    Strategy Agent: Generates trade signals using multiple strategies including
    arbitrage detection, trend following, mean reversion, and LP yield optimization.
    """

    def __init__(self, config: Dict = None, llm=None):
        self.config = StrategyConfig(**(config or {}))
        self.llm = llm

        # Strategy weights for signal scoring
        self.strategy_weights = {
            "ARBITRAGE": 1.0,
            "TREND_FOLLOWING": 0.8,
            "MEAN_REVERSION": 0.7,
            "LP_YIELD": 0.6,
        }

        # Price history for trend calculation
        self.price_history: Dict[str, List[Dict]] = {}

    async def run(self, state: TradingState) -> TradingState:
        """Main entry point for the agent"""
        logger.info("Strategy Agent running...")

        try:
            signals = []

            # Run each strategy in parallel
            arbitrage_signals = await self.arbitrage_strategy(state)
            trend_signals = await self.trend_following_strategy(state)
            reversion_signals = await self.mean_reversion_strategy(state)
            yield_signals = await self.lp_yield_strategy(state)

            signals.extend(arbitrage_signals)
            signals.extend(trend_signals)
            signals.extend(reversion_signals)
            signals.extend(yield_signals)

            # Score and rank signals
            ranked_signals = self.rank_signals(signals)

            # Filter by minimum confidence
            valid_signals = [
                s for s in ranked_signals
                if s.confidence >= self.config.min_confidence
            ]

            # Update state
            state['pending_signals'] = valid_signals[:10]  # Top 10 signals

            # Create agent action
            action = AgentAction(
                agent_name="StrategyAgent",
                action="generate_signals",
                input_data={
                    "market_regime": state.get('market_regime', 'UNKNOWN'),
                    "pools": len(state.get('pools', {})),
                },
                output_data={
                    "total_signals": len(signals),
                    "valid_signals": len(valid_signals),
                    "strategies_used": ["ARBITRAGE", "TREND", "MEAN_REVERSION", "LP_YIELD"],
                },
                confidence=0.8,
                timestamp=int(datetime.now().timestamp()),
                duration_ms=200,
            )
            state['agent_actions'].append(action)

            logger.info(f"Generated {len(signals)} signals, {len(valid_signals)} valid")

        except Exception as e:
            logger.error(f"Error in Strategy Agent: {e}", exc_info=True)
            state['status'] = 'ERROR'

        return state

    async def arbitrage_strategy(self, state: TradingState) -> List[TradeSignal]:
        """
        Cross-pool arbitrage strategy: Find price differences for the same
        token pair across different liquidity pools.
        """
        signals = []
        prices = state.get('current_prices', {})
        pools = state.get('pools', {})

        # Group prices by token pair
        token_groups: Dict[str, List[tuple]] = {}

        for pool_addr, price_update in prices.items():
            pool = pools.get(pool_addr)
            if not pool:
                continue

            # Create pair key
            pair_key = tuple(sorted([pool.token0.symbol, pool.token1.symbol]))

            if pair_key not in token_groups:
                token_groups[pair_key] = []

            token_groups[pair_key].append((pool, price_update))

        # Find arbitrage opportunities
        for pair_key, pool_prices in token_groups.items():
            if len(pool_prices) < 2:
                continue

            # Sort by price
            sorted_pools = sorted(pool_prices, key=lambda x: x[1].token0_price)

            for i in range(len(sorted_pools)):
                for j in range(i + 1, len(sorted_pools)):
                    buy_pool, buy_price = sorted_pools[i]
                    sell_pool, sell_price = sorted_pools[j]

                    if buy_price.token0_price <= 0:
                        continue

                    # Calculate spread
                    spread = sell_price.token0_price - buy_price.token0_price
                    spread_percent = (spread / buy_price.token0_price) * 100

                    # Estimate profit
                    amount_in = min(
                        self.config.max_position_size,
                        buy_pool.tvl_usd * 0.01  # 1% of pool liquidity
                    )

                    trading_fees = amount_in * (buy_pool.fee_rate + sell_pool.fee_rate)
                    estimated_gas = 3.0  # USD
                    expected_profit = spread - trading_fees - estimated_gas

                    if expected_profit > self.config.min_profit_threshold:
                        confidence = min(0.95, 0.7 + (spread_percent / 100))

                        signal = TradeSignal(
                            id=str(uuid.uuid4()),
                            type="ARBITRAGE",
                            confidence=confidence,
                            token_in=buy_pool.token0,
                            token_out=buy_pool.token1,
                            amount_in=str(int(amount_in * 10 ** buy_pool.token0.decimals)),
                            expected_profit=expected_profit,
                            expected_profit_percent=spread_percent,
                            buy_pool=buy_pool,
                            sell_pool=sell_pool,
                            metadata={
                                "strategy": "ARBITRAGE",
                                "buy_pool": buy_pool.address,
                                "sell_pool": sell_pool.address,
                                "spread_percent": spread_percent,
                                "trading_fees": trading_fees,
                                "estimated_gas": estimated_gas,
                            }
                        )
                        signals.append(signal)

        return signals

    async def trend_following_strategy(self, state: TradingState) -> List[TradeSignal]:
        """
        Trend following strategy: Identify assets with strong upward momentum
        and generate buy signals.
        """
        signals = []
        prices = state.get('current_prices', {})

        for pool_addr, current_update in prices.items():
            # Get price history
            history = self.price_history.get(pool_addr, [])

            if len(history) < 10:
                continue

            # Calculate moving averages
            recent_prices = [h['token0_price'] for h in history[-10:]]
            sma_5 = sum(recent_prices[-5:]) / 5
            sma_10 = sum(recent_prices) / 10

            # Trend detection
            if sma_5 > sma_10 * 1.02:  # 2% above long-term average
                # Upward trend detected
                price_change = ((recent_prices[-1] - recent_prices[0])
                               / recent_prices[0] * 100)

                if price_change > 3:  # >3% gain
                    # Get pool info
                    pools = state.get('pools', {})
                    pool = pools.get(pool_addr)

                    if pool:
                        confidence = min(0.9, 0.6 + (price_change / 100))

                        signal = TradeSignal(
                            id=str(uuid.uuid4()),
                            type="TREND_FOLLOWING",
                            confidence=confidence,
                            token_in=pool.token1,  # Sell stable
                            token_out=pool.token0,  # Buy trending
                            amount_in=str(int(100 * 10 ** pool.token1.decimals)),
                            expected_profit=price_change * 0.5,
                            expected_profit_percent=price_change * 0.5,
                            buy_pool=pool,
                            stop_loss=recent_prices[-1] * 0.95,
                            take_profit=recent_prices[-1] * 1.10,
                            metadata={
                                "strategy": "TREND_FOLLOWING",
                                "sma_5": sma_5,
                                "sma_10": sma_10,
                                "price_change_10": price_change,
                            }
                        )
                        signals.append(signal)

        return signals

    async def mean_reversion_strategy(self, state: TradingState) -> List[TradeSignal]:
        """
        Mean reversion strategy: Identify assets that have deviated significantly
        from their mean and generate buy/sell signals expecting a return to mean.
        """
        signals = []
        prices = state.get('current_prices', {})

        for pool_addr, current_update in prices.items():
            history = self.price_history.get(pool_addr, [])

            if len(history) < 20:
                continue

            # Calculate mean and standard deviation
            recent_prices = [h.get('token0_price', 0) for h in history[-20:]]
            mean_price = sum(recent_prices) / len(recent_prices)

            variance = sum((p - mean_price) ** 2 for p in recent_prices) / len(recent_prices)
            std_dev = variance ** 0.5

            current_price = current_update.token0_price

            if mean_price > 0 and std_dev > 0:
                z_score = (current_price - mean_price) / std_dev

                # Buy signal: price is significantly below mean (z-score < -2)
                # Sell signal: price is significantly above mean (z-score > 2)
                if abs(z_score) > 1.5:
                    pools = state.get('pools', {})
                    pool = pools.get(pool_addr)

                    if pool:
                        is_buy = z_score < -1.5

                        confidence = min(0.85, 0.5 + abs(z_score) / 10)

                        expected_move = abs(z_score) * std_dev

                        signal = TradeSignal(
                            id=str(uuid.uuid4()),
                            type="MEAN_REVERSION",
                            confidence=confidence,
                            token_in=pool.token1 if is_buy else pool.token0,
                            token_out=pool.token0 if is_buy else pool.token1,
                            amount_in=str(int(100 * 10 ** pool.token1.decimals)),
                            expected_profit=expected_move,
                            expected_profit_percent=(expected_move / current_price * 100),
                            buy_pool=pool,
                            metadata={
                                "strategy": "MEAN_REVERSION",
                                "z_score": z_score,
                                "mean_price": mean_price,
                                "std_dev": std_dev,
                                "direction": "BUY" if is_buy else "SELL",
                            }
                        )
                        signals.append(signal)

        return signals

    async def lp_yield_strategy(self, state: TradingState) -> List[TradeSignal]:
        """
        LP Yield strategy: Identify pools with high APY and low impermanent loss risk.
        """
        signals = []
        pools = state.get('pools', {})

        for pool_addr, pool in pools.items():
            # Skip if no APR data
            if not hasattr(pool, 'apr24h') or pool.apr24h is None:
                continue

            # High yield criteria
            if pool.apr24h > 0.5:  # >50% APR
                # Check impermanent loss risk
                il_risk = getattr(pool, 'impermanent_loss24h', 0) or 0

                # Risk-adjusted return
                risk_adjusted_return = pool.apr24h - il_risk

                if risk_adjusted_return > 0.2:  # >20% after IL
                    confidence = min(0.9, 0.6 + (risk_adjusted_return / 2))

                    signal = TradeSignal(
                        id=str(uuid.uuid4()),
                        type="LP_YIELD",
                        confidence=confidence,
                        token_in=pool.token0,
                        token_out=pool.token1,
                        amount_in=str(int(500 * 10 ** pool.token0.decimals)),
                        expected_profit=500 * risk_adjusted_return / 365,  # Daily
                        expected_profit_percent=risk_adjusted_return * 100,
                        buy_pool=pool,
                        metadata={
                            "strategy": "LP_YIELD",
                            "apr_24h": pool.apr24h,
                            "il_risk": il_risk,
                            "risk_adjusted_return": risk_adjusted_return,
                            "tvl_usd": pool.tvl_usd,
                        }
                    )
                    signals.append(signal)

        return signals

    def rank_signals(self, signals: List[TradeSignal]) -> List[TradeSignal]:
        """Rank signals by expected profitability and confidence"""

        def score_signal(signal: TradeSignal) -> float:
            # Base score from confidence
            score = signal.confidence * 100

            # Add expected profit
            score += signal.expected_profit * 10

            # Strategy weight
            weight = self.strategy_weights.get(signal.type, 0.5)
            score *= weight

            return score

        # Sort by score descending
        return sorted(signals, key=score_signal, reverse=True)

    def update_price_history(self, pool_address: str, price: float) -> None:
        """Update price history for a pool"""
        if pool_address not in self.price_history:
            self.price_history[pool_address] = []

        self.price_history[pool_address].append({
            'token0_price': price,
            'timestamp': int(datetime.now().timestamp())
        })

        # Keep only last 100 entries
        self.price_history[pool_address] = self.price_history[pool_address][-100:]
