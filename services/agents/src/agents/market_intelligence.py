import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
import json

from web3 import Web3
from ..state import TradingState, PriceUpdate, PoolInfo, TokenInfo, AgentAction

logger = logging.getLogger(__name__)


@dataclass
class WhaleMovement:
    tx_hash: str
    wallet: str
    token: str
    amount: float
    amount_usd: float
    type: str  # BUY, SELL
    timestamp: int


class MarketIntelligenceAgent:
    """
    Market Intelligence Agent: Monitors real-time prices, detects market regimes,
    tracks whale movements, and identifies arbitrage opportunities.
    """

    def __init__(self, w3: Web3, redis_client=None, config: Dict = None):
        self.w3 = w3
        self.redis = redis_client
        self.config = config or {}

        # PancakeSwap Factory V2 ABI (minimal)
        self.factory_abi = [
            {"constant": True, "inputs": [], "name": "allPairsLength", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
            {"constant": True, "inputs": [{"name": "", "type": "uint256"}], "name": "allPairs", "outputs": [{"name": "pair", "type": "address"}], "type": "function"},
        ]

        # Pair ABI (minimal)
        self.pair_abi = [
            {"constant": True, "inputs": [], "name": "getReserves", "outputs": [
                {"name": "_reserve0", "type": "uint112"},
                {"name": "_reserve1", "type": "uint112"},
                {"name": "_blockTimestampLast", "type": "uint32"}
            ], "type": "function"},
            {"constant": True, "inputs": [], "name": "token0", "outputs": [{"name": "", "type": "address"}], "type": "function"},
            {"constant": True, "inputs": [], "name": "token1", "outputs": [{"name": "", "type": "address"}], "type": "function"},
        ]

        # ERC20 ABI (minimal)
        self.erc20_abi = [
            {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"},
            {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
        ]

        self.monitored_pools: List[str] = []
        self.price_history: Dict[str, List[PriceUpdate]] = {}
        self.volatility_window: List[float] = []
        self.whale_threshold_usd = self.config.get('whale_threshold_usd', 100000)

        # Factory addresses
        self.factory_v2 = "0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73"

    async def run(self, state: TradingState) -> TradingState:
        """Main entry point for the agent"""
        logger.info("Market Intelligence Agent running...")

        try:
            # Step 1: Fetch latest prices from monitored pools
            price_updates = await self.fetch_price_updates()

            # Step 2: Detect market regime
            market_regime = self.detect_market_regime(price_updates)

            # Step 3: Detect whale movements
            whale_moves = await self.detect_whale_movements()

            # Step 4: Identify arbitrage candidates
            arbitrage_candidates = self.identify_arbitrage_candidates(price_updates)

            # Update state
            for update in price_updates:
                state['current_prices'][update.pool_address] = update

            state['market_regime'] = market_regime

            # Create agent action record
            action = AgentAction(
                agent_name="MarketIntelligenceAgent",
                action="market_scan",
                input_data={"pools_monitored": len(self.monitored_pools)},
                output_data={
                    "price_updates": len(price_updates),
                    "market_regime": market_regime,
                    "whale_movements": len(whale_moves),
                    "arbitrage_candidates": len(arbitrage_candidates),
                },
                confidence=0.85,
                timestamp=int(datetime.now().timestamp()),
                duration_ms=100,
            )
            state['agent_actions'].append(action)

            # Publish to Redis if available
            if self.redis:
                await self.publish_price_updates(price_updates)
                await self.redis.publish(
                    "market:regime",
                    json.dumps({"regime": market_regime, "timestamp": datetime.now().isoformat()})
                )

            logger.info(f"Market scan complete: {len(price_updates)} pools, regime: {market_regime}")

        except Exception as e:
            logger.error(f"Error in Market Intelligence Agent: {e}", exc_info=True)
            state['status'] = 'ERROR'

        return state

    async def fetch_price_updates(self) -> List[PriceUpdate]:
        """Fetch current price updates from all monitored pools"""
        updates = []

        # If no pools monitored, discover some
        if not self.monitored_pools:
            await self.discover_pools()

        for pool_address in self.monitored_pools[:20]:  # Limit to 20 pools for performance
            try:
                # Get reserves
                pair_contract = self.w3.eth.contract(
                    address=Web3.to_checksum_address(pool_address),
                    abi=self.pair_abi
                )

                reserves = pair_contract.functions.getReserves().call()
                reserve0, reserve1, block_timestamp = reserves

                # Get token addresses
                token0 = pair_contract.functions.token0().call()
                token1 = pair_contract.functions.token1().call()

                # Calculate price
                price0 = reserve1 / reserve0 if reserve0 > 0 else 0
                price1 = reserve0 / reserve1 if reserve1 > 0 else 0

                update = PriceUpdate(
                    pool_address=pool_address,
                    token0_price=price0,
                    token1_price=price1,
                    timestamp=int(datetime.now().timestamp()),
                    block_number=self.w3.eth.block_number,
                )
                updates.append(update)

                # Store in history
                if pool_address not in self.price_history:
                    self.price_history[pool_address] = []
                self.price_history[pool_address].append(update)

                # Keep only last 100 updates per pool
                self.price_history[pool_address] = self.price_history[pool_address][-100:]

            except Exception as e:
                logger.warning(f"Failed to fetch reserves for pool {pool_address}: {e}")

        return updates

    async def discover_pools(self) -> None:
        """Discover active pools from factory"""
        try:
            factory = self.w3.eth.contract(
                address=Web3.to_checksum_address(self.factory_v2),
                abi=self.factory_abi
            )

            # Get pool count
            pool_count = factory.functions.allPairsLength().call()
            logger.info(f"Found {pool_count} pools in factory")

            # Sample pools (first 20)
            for i in range(min(20, pool_count)):
                try:
                    pool_address = factory.functions.allPairs(i).call()
                    self.monitored_pools.append(pool_address)
                except Exception as e:
                    logger.warning(f"Failed to get pool at index {i}: {e}")

            logger.info(f"Monitoring {len(self.monitored_pools)} pools")

        except Exception as e:
            logger.error(f"Pool discovery failed: {e}")

    def detect_market_regime(self, price_updates: List[PriceUpdate]) -> str:
        """
        Detect market regime based on price movements and volatility.
        Returns: BULL, BEAR, SIDEWAYS, VOLATILE
        """
        if not price_updates:
            return "SIDEWAYS"

        # Calculate volatility from recent price changes
        price_changes = []
        for update in price_updates:
            history = self.price_history.get(update.pool_address, [])
            if len(history) >= 2:
                prev_price = history[-2].token0_price
                curr_price = update.token0_price
                if prev_price > 0:
                    change_pct = abs((curr_price - prev_price) / prev_price * 100)
                    price_changes.append(change_pct)

        if not price_changes:
            return "SIDEWAYS"

        avg_volatility = sum(price_changes) / len(price_changes)
        max_change = max(price_changes)

        # Regime detection logic
        if max_change > 5:  # >5% move
            return "VOLATILE"
        elif avg_volatility > 2:  # >2% average change
            # Determine direction from price trends
            upward_moves = sum(1 for p in price_changes if p > 0)
            if upward_moves > len(price_changes) * 0.6:
                return "BULL"
            elif upward_moves < len(price_changes) * 0.4:
                return "BEAR"

        return "SIDEWAYS"

    async def detect_whale_movements(self) -> List[WhaleMovement]:
        """Detect large transactions (whale movements)"""
        movements = []

        # This would scan recent blocks for large transfers
        # For now, return empty list as this requires event log parsing

        return movements

    def identify_arbitrage_candidates(self, price_updates: List[PriceUpdate]) -> List[Dict]:
        """
        Identify potential arbitrage opportunities across pools.
        Returns list of candidate opportunities with profit estimates.
        """
        candidates = []

        # Group by token pair
        token_groups: Dict[str, List[PriceUpdate]] = {}

        for update in price_updates:
            # Create a key from pool data (we'd need token symbols here)
            # For now, use pool address as key
            key = update.pool_address
            if key not in token_groups:
                token_groups[key] = []
            token_groups[key].append(update)

        # Find price differences between same token pairs on different pools
        # This is a simplified version - real implementation would track tokens across pools

        return candidates

    def calculate_volatility(self, pool_address: str) -> float:
        """Calculate volatility for a specific pool"""
        history = self.price_history.get(pool_address, [])
        if len(history) < 2:
            return 0.0

        prices = [h.token0_price for h in history[-20:]]  # Last 20 updates
        if len(prices) < 2 or any(p == 0 for p in prices):
            return 0.0

        # Calculate standard deviation of returns
        returns = [(prices[i] - prices[i-1]) / prices[i-1]
                   for i in range(1, len(prices)) if prices[i-1] > 0]

        if not returns:
            return 0.0

        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        volatility = variance ** 0.5 * 100  # As percentage

        return volatility

    async def publish_price_updates(self, updates: List[PriceUpdate]) -> None:
        """Publish price updates to Redis"""
        if not self.redis:
            return

        for update in updates:
            channel = f"prices:{update.pool_address}"
            message = json.dumps({
                "pool_address": update.pool_address,
                "token0_price": update.token0_price,
                "token1_price": update.token1_price,
                "timestamp": update.timestamp,
                "block_number": update.block_number,
            })
            await self.redis.publish(channel, message)

    async def get_market_snapshot(self) -> Dict[str, Any]:
        """Get complete market snapshot"""
        return {
            "timestamp": datetime.now().isoformat(),
            "block_number": self.w3.eth.block_number,
            "pools_monitored": len(self.monitored_pools),
            "price_updates_last_hour": sum(
                len(h) for h in self.price_history.values()
            ),
            "market_regime": self.detect_market_regime(
                list(self.price_history.values())[-1] if self.price_history else []
            ),
        }
