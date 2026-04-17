import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass

from web3 import Web3
from ..state import TradingState, PoolInfo, TokenInfo, AgentAction

logger = logging.getLogger(__name__)


@dataclass
class LiquidityMetrics:
    pool_address: str
    tvl_usd: float
    volume24h: float
    fee_apy: float
    impermanent_loss_24h: float
    liquidity_depth: float
    price_impact_1k: float
    reserve_imbalance: float


class LiquidityAnalysisAgent:
    """
    Liquidity Analysis Agent: Scans pools, analyzes liquidity depth,
    detects reserve imbalances, estimates yield, and discovers new opportunities.
    """

    def __init__(self, w3: Web3, config: Dict = None):
        self.w3 = w3
        self.config = config or {}

        # Factory ABI
        self.factory_abi = [
            {"constant": True, "inputs": [], "name": "allPairsLength", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
            {"constant": True, "inputs": [{"name": "", "type": "uint256"}], "name": "allPairs", "outputs": [{"name": "pair", "type": "address"}], "type": "function"},
        ]

        # Pair ABI
        self.pair_abi = [
            {"constant": True, "inputs": [], "name": "getReserves", "outputs": [
                {"name": "_reserve0", "type": "uint112"},
                {"name": "_reserve1", "type": "uint112"},
                {"name": "_blockTimestampLast", "type": "uint32"}
            ], "type": "function"},
            {"constant": True, "inputs": [], "name": "token0", "outputs": [{"name": "", "type": "address"}], "type": "function"},
            {"constant": True, "inputs": [], "name": "token1", "outputs": [{"name": "", "type": "address"}], "type": "function"},
            {"constant": True, "inputs": [], "name": "totalSupply", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
        ]

        self.factory_v2 = "0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73"
        self.discovered_pools: Dict[str, PoolInfo] = {}
        self.liquidity_metrics: Dict[str, LiquidityMetrics] = {}

    async def run(self, state: TradingState) -> TradingState:
        """Main entry point for the agent"""
        logger.info("Liquidity Analysis Agent running...")

        try:
            # Discover new pools
            new_pools = await self.discover_pools()

            # Analyze liquidity for monitored pools
            await self.analyze_liquidity()

            # Calculate yield estimates
            await self.calculate_yield()

            # Detect reserve imbalances
            imbalances = await self.detect_imbalances()

            # Update state
            state['pools'] = self.discovered_pools

            # Create agent action
            action = AgentAction(
                agent_name="LiquidityAnalysisAgent",
                action="analyze_liquidity",
                input_data={"pools_scanned": len(self.discovered_pools)},
                output_data={
                    "new_pools": len(new_pools),
                    "imbalances_detected": len(imbalances),
                    "high_yield_pools": sum(1 for m in self.liquidity_metrics.values() if m.fee_apy > 0.2),
                },
                confidence=0.85,
                timestamp=int(datetime.now().timestamp()),
                duration_ms=300,
            )
            state['agent_actions'].append(action)

            logger.info(f"Liquidity analysis complete: {len(self.discovered_pools)} pools scanned")

        except Exception as e:
            logger.error(f"Error in Liquidity Analysis Agent: {e}", exc_info=True)

        return state

    async def discover_pools(self) -> List[PoolInfo]:
        """Discover new liquidity pools from factory"""
        new_pools = []

        try:
            factory = self.w3.eth.contract(
                address=self.w3.to_checksum_address(self.factory_v2),
                abi=self.factory_abi
            )

            pool_count = factory.functions.allPairsLength().call()
            logger.info(f"Factory has {pool_count} pools")

            # Sample top pools by index
            for i in range(min(50, pool_count)):
                try:
                    pool_address = factory.functions.allPairs(i).call()

                    if pool_address not in self.discovered_pools:
                        pool_info = await self.get_pool_info(pool_address)
                        if pool_info:
                            self.discovered_pools[pool_address] = pool_info
                            new_pools.append(pool_info)

                except Exception as e:
                    logger.warning(f"Failed to get pool at index {i}: {e}")

        except Exception as e:
            logger.error(f"Pool discovery failed: {e}")

        return new_pools

    async def get_pool_info(self, pool_address: str) -> Optional[PoolInfo]:
        """Get detailed information about a pool"""
        try:
            pair = self.w3.eth.contract(
                address=self.w3.to_checksum_address(pool_address),
                abi=self.pair_abi
            )

            reserves = pair.functions.getReserves().call()
            token0_addr = pair.functions.token0().call()
            token1_addr = pair.functions.token1().call()

            # Create token info (simplified)
            token0 = TokenInfo(
                address=token0_addr,
                symbol=f"TKN_{token0_addr[:6]}",
                decimals=18,
                price_usd=1.0
            )
            token1 = TokenInfo(
                address=token1_addr,
                symbol=f"TKN_{token1_addr[:6]}",
                decimals=18,
                price_usd=1.0
            )

            return PoolInfo(
                address=pool_address,
                token0=token0,
                token1=token1,
                reserve0=str(reserves[0]),
                reserve1=str(reserves[1]),
                tvl_usd=0,  # Would need price data
                fee_rate=0.0025,
                chain="bsc"
            )

        except Exception as e:
            logger.warning(f"Failed to get pool info for {pool_address}: {e}")
            return None

    async def analyze_liquidity(self) -> None:
        """Analyze liquidity depth and metrics for all pools"""
        for pool_address, pool in self.discovered_pools.items():
            try:
                reserve0 = float(pool.reserve0) / (10 ** pool.token0.decimals)
                reserve1 = float(pool.reserve1) / (10 ** pool.token1.decimals)

                # Calculate liquidity depth
                liquidity_depth = min(reserve0, reserve1)

                # Estimate price impact for $1k trade
                trade_size = 1000
                if reserve0 > 0:
                    price_impact = (trade_size / (reserve0 + trade_size)) * 100
                else:
                    price_impact = 0

                # Calculate reserve imbalance
                if reserve0 > 0 and reserve1 > 0:
                    imbalance = abs(reserve0 - reserve1) / (reserve0 + reserve1)
                else:
                    imbalance = 0

                metrics = LiquidityMetrics(
                    pool_address=pool_address,
                    tvl_usd=pool.tvl_usd,
                    volume24h=getattr(pool, 'volume24h', 0),
                    fee_apy=0,
                    impermanent_loss_24h=0,
                    liquidity_depth=liquidity_depth,
                    price_impact_1k=price_impact,
                    reserve_imbalance=imbalance
                )

                self.liquidity_metrics[pool_address] = metrics

            except Exception as e:
                logger.warning(f"Failed to analyze liquidity for {pool_address}: {e}")

    async def calculate_yield(self) -> None:
        """Calculate yield estimates for liquidity provision"""
        for pool_address, pool in self.discovered_pools.items():
            try:
                # Calculate fee APY based on volume and TVL
                volume_24h = getattr(pool, 'volume24h', 0) or 10000  # Default 10k volume
                tvl = pool.tvl_usd or 10000  # Default 10k TVL

                if tvl > 0:
                    daily_fees = volume_24h * pool.fee_rate
                    annual_fees = daily_fees * 365
                    fee_apy = annual_fees / tvl
                else:
                    fee_apy = 0

                # Update metrics
                if pool_address in self.liquidity_metrics:
                    self.liquidity_metrics[pool_address].fee_apy = fee_apy

            except Exception as e:
                logger.warning(f"Failed to calculate yield for {pool_address}: {e}")

    async def detect_imbalances(self) -> List[Dict]:
        """Detect reserve imbalances that could indicate arbitrage opportunities"""
        imbalances = []

        for pool_address, metrics in self.liquidity_metrics.items():
            if metrics.reserve_imbalance > 0.2:  # >20% imbalance
                imbalances.append({
                    "pool_address": pool_address,
                    "imbalance": metrics.reserve_imbalance,
                    "severity": "HIGH" if metrics.reserve_imbalance > 0.4 else "MEDIUM",
                })

        return imbalances

    def get_high_yield_pools(self, min_apy: float = 0.2) -> List[Dict]:
        """Get pools with high yield"""
        return [
            {
                "pool_address": addr,
                "apy": metrics.fee_apy,
                "tvl": metrics.tvl_usd,
                "volume_24h": metrics.volume24h,
            }
            for addr, metrics in self.liquidity_metrics.items()
            if metrics.fee_apy >= min_apy
        ]

    def get_pool_ranking(self) -> List[Dict]:
        """Get pools ranked by combined score"""
        rankings = []

        for pool_address, metrics in self.liquidity_metrics.items():
            # Combined score based on multiple factors
            score = (
                metrics.fee_apy * 100 * 0.4 +  # 40% weight on yield
                (1 / (metrics.price_impact_1k + 0.01)) * 0.3 +  # 30% weight on liquidity depth
                (1 - metrics.reserve_imbalance) * 0.3  # 30% weight on balance
            )

            rankings.append({
                "pool_address": pool_address,
                "score": score,
                "tvl": metrics.tvl_usd,
                "apy": metrics.fee_apy,
                "liquidity_depth": metrics.liquidity_depth,
            })

        return sorted(rankings, key=lambda x: x["score"], reverse=True)
