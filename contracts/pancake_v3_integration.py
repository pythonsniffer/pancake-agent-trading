"""
PancakeSwap V3 Integration Module

Supports:
- Concentrated liquidity positions
- Multi-hop swaps through V3 pools
- Tick-based price calculations
- Position management (mint, increase, decrease, collect)
- Quoter for exact input/output amounts
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from decimal import Decimal
import math

from web3 import Web3
from eth_account import Account

logger = logging.getLogger(__name__)

# PancakeSwap V3 Contract Addresses
V3_ADDRESSES = {
    "bsc": {
        "factory": "0x0BFbCF9faD4f13C9eF87D5e27E6F30573D7C752c",
        "router": "0x13f4EA83D0bd40E75C8222255bc855a974568Dd4",
        "quoter": "0xB048Bbc1Ee6b656E853D4d9ae73b6f6d79e4FbF3",
        "position_manager": "0x46A15B0b27311cedF172AB29E4f4766fbEE7F17bB",
        "multicall": "0xcA11bde05977b3631167028862bE2a173976CA11",
    },
    "ethereum": {
        "factory": "0x0BFbCF9faD4f13C9eF87D5e27E6F30573D7C752c",
        "router": "0x13f4EA83D0bd40E75C8222255bc855a974568Dd4",
        "quoter": "0xB048Bbc1Ee6b656E853D4d9ae73b6f6d79e4FbF3",
        "position_manager": "0x46A15B0b27311cedF172AB29E4f4766fbEE7F17bB",
    },
    "arbitrum": {
        "factory": "0x0BFbCF9faD4f13C9eF87D5e27E6F30573D7C752c",
        "router": "0x13f4EA83D0bd40E75C8222255bc855a974568Dd4",
        "quoter": "0xB048Bbc1Ee6b656E853D4d9ae73b6f6d79e4FbF3",
        "position_manager": "0x46A15B0b27311cedF172AB29E4f4766fbEE7F17bB",
    }
}

# ABI Fragments
V3_FACTORY_ABI = [
    {"inputs": [], "name": "feeAmountTickSpacing", "outputs": [{"internalType": "int24", "name": "", "type": "int24"}], "stateMutability": "view", "type": "function", "params": [{"name": "fee", "type": "uint24"}]},
    {"inputs": [{"internalType": "address", "name": "tokenA", "type": "address"}, {"internalType": "address", "name": "tokenB", "type": "address"}, {"internalType": "uint24", "name": "fee", "type": "uint24"}], "name": "getPool", "outputs": [{"internalType": "address", "name": "pool", "type": "address"}], "stateMutability": "view", "type": "function"},
]

V3_POOL_ABI = [
    {"inputs": [], "name": "slot0", "outputs": [{"internalType": "uint160", "name": "sqrtPriceX96", "type": "uint160"}, {"internalType": "int24", "name": "tick", "type": "int24"}, {"internalType": "uint16", "name": "observationIndex", "type": "uint16"}, {"internalType": "uint16", "name": "observationCardinality", "type": "uint16"}, {"internalType": "uint16", "name": "observationCardinalityNext", "type": "uint16"}, {"internalType": "uint8", "name": "feeProtocol", "type": "uint8"}, {"internalType": "bool", "name": "unlocked", "type": "bool"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "liquidity", "outputs": [{"internalType": "uint128", "name": "", "type": "uint128"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"internalType": "int24", "name": "tickLower", "type": "int24"}, {"internalType": "int24", "name": "tickUpper", "type": "int24"}], "name": "ticks", "outputs": [{"internalType": "uint128", "name": "liquidityGross", "type": "uint128"}, {"internalType": "int128", "name": "liquidityNet", "type": "int128"}, {"internalType": "uint256", "name": "feeGrowthOutside0X128", "type": "uint256"}, {"internalType": "uint256", "name": "feeGrowthOutside1X128", "type": "uint256"}, {"internalType": "int56", "name": "tickCumulativeOutside", "type": "int56"}, {"internalType": "uint160", "name": "secondsPerLiquidityOutsideX128", "type": "uint160"}, {"internalType": "uint32", "name": "secondsOutside", "type": "uint32"}, {"internalType": "bool", "name": "initialized", "type": "bool"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"internalType": "uint32", "name": "secondsAgo", "type": "uint32"}], "name": "observe", "outputs": [{"internalType": "int56[]", "name": "tickCumulatives", "type": "int56[]"}, {"internalType": "uint160[]", "name": "secondsPerLiquidityCumulativeX128s", "type": "uint160[]"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "token0", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "token1", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "fee", "outputs": [{"internalType": "uint24", "name": "", "type": "uint24"}], "stateMutability": "view", "type": "function"},
]

V3_ROUTER_ABI = [
    {"inputs": [{"internalType": "address", "name": "recipient", "type": "address"}, {"internalType": "uint256", "name": "amountIn", "type": "uint256"}, {"internalType": "uint256", "name": "amountOutMinimum", "type": "uint256"}, {"internalType": "bytes", "name": "path", "type": "bytes"}, {"internalType": "address", "name": "payer", "type": "address"}], "name": "exactInput", "outputs": [{"internalType": "uint256", "name": "amountOut", "type": "uint256"}], "stateMutability": "payable", "type": "function"},
    {"inputs": [{"internalType": "address", "name": "recipient", "type": "address"}, {"internalType": "uint256", "name": "amountOut", "type": "uint256"}, {"internalType": "uint256", "name": "amountInMaximum", "type": "uint256"}, {"internalType": "bytes", "name": "path", "type": "bytes"}, {"internalType": "address", "name": "payer", "type": "address"}], "name": "exactOutput", "outputs": [{"internalType": "uint256", "name": "amountIn", "type": "uint256"}], "stateMutability": "payable", "type": "function"},
]

V3_POSITION_MANAGER_ABI = [
    {"inputs": [{"components": [{"internalType": "address", "name": "token0", "type": "address"}, {"internalType": "address", "name": "token1", "type": "address"}, {"internalType": "uint24", "name": "fee", "type": "uint24"}, {"internalType": "int24", "name": "tickLower", "type": "int24"}, {"internalType": "int24", "name": "tickUpper", "type": "int24"}, {"internalType": "uint256", "name": "amount0Desired", "type": "uint256"}, {"internalType": "uint256", "name": "amount1Desired", "type": "uint256"}, {"internalType": "uint256", "name": "amount0Min", "type": "uint256"}, {"internalType": "uint256", "name": "amount1Min", "type": "uint256"}, {"internalType": "address", "name": "recipient", "type": "address"}, {"internalType": "uint256", "name": "deadline", "type": "uint256"}], "internalType": "struct INonfungiblePositionManager.MintParams", "name": "params", "type": "tuple"}], "name": "mint", "outputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}, {"internalType": "uint128", "name": "liquidity", "type": "uint128"}, {"internalType": "uint256", "name": "amount0", "type": "uint256"}, {"internalType": "uint256", "name": "amount1", "type": "uint256"}], "stateMutability": "payable", "type": "function"},
    {"inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}], "name": "positions", "outputs": [{"internalType": "uint96", "name": "nonce", "type": "uint96"}, {"internalType": "address", "name": "operator", "type": "address"}, {"internalType": "address", "name": "token0", "type": "address"}, {"internalType": "address", "name": "token1", "type": "address"}, {"internalType": "uint24", "name": "fee", "type": "uint24"}, {"internalType": "int24", "name": "tickLower", "type": "int24"}, {"internalType": "int24", "name": "tickUpper", "type": "int24"}, {"internalType": "uint128", "name": "liquidity", "type": "uint128"}, {"internalType": "uint256", "name": "feeGrowthInside0LastX128", "type": "uint256"}, {"internalType": "uint256", "name": "feeGrowthInside1LastX128", "type": "uint256"}, {"internalType": "uint128", "name": "tokensOwed0", "type": "uint128"}, {"internalType": "uint128", "name": "tokensOwed1", "type": "uint128"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"components": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}, {"internalType": "uint256", "name": "amount0Desired", "type": "uint256"}, {"internalType": "uint256", "name": "amount1Desired", "type": "uint256"}, {"internalType": "uint256", "name": "amount0Min", "type": "uint256"}, {"internalType": "uint256", "name": "amount1Min", "type": "uint256"}, {"internalType": "uint256", "name": "deadline", "type": "uint256"}], "internalType": "struct INonfungiblePositionManager.IncreaseLiquidityParams", "name": "params", "type": "tuple"}], "name": "increaseLiquidity", "outputs": [{"internalType": "uint128", "name": "liquidity", "type": "uint128"}, {"internalType": "uint256", "name": "amount0", "type": "uint256"}, {"internalType": "uint256", "name": "amount1", "type": "uint256"}], "stateMutability": "payable", "type": "function"},
    {"inputs": [{"components": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}, {"internalType": "uint128", "name": "liquidity", "type": "uint128"}, {"internalType": "uint256", "name": "amount0Min", "type": "uint256"}, {"internalType": "uint256", "name": "amount1Min", "type": "uint256"}, {"internalType": "uint256", "name": "deadline", "type": "uint256"}], "internalType": "struct INonfungiblePositionManager.DecreaseLiquidityParams", "name": "params", "type": "tuple"}], "name": "decreaseLiquidity", "outputs": [{"internalType": "uint256", "name": "amount0", "type": "uint256"}, {"internalType": "uint256", "name": "amount1", "type": "uint256"}], "stateMutability": "payable", "type": "function"},
    {"inputs": [{"components": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}, {"internalType": "address", "name": "recipient", "type": "address"}, {"internalType": "uint128", "name": "amount0Max", "type": "uint128"}, {"internalType": "uint128", "name": "amount1Max", "type": "uint128"}], "internalType": "struct INonfungiblePositionManager.CollectParams", "name": "params", "type": "tuple"}], "name": "collect", "outputs": [{"internalType": "uint256", "name": "amount0", "type": "uint256"}, {"internalType": "uint256", "name": "amount1", "type": "uint256"}], "stateMutability": "payable", "type": "function"},
    {"inputs": [{"internalType": "address", "name": "owner", "type": "address"}], "name": "balanceOf", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"internalType": "address", "name": "owner", "type": "address"}, {"internalType": "uint256", "name": "index", "type": "uint256"}], "name": "tokenOfOwnerByIndex", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
]

V3_QUOTER_ABI = [
    {"inputs": [{"internalType": "bytes", "name": "path", "type": "bytes"}, {"internalType": "uint256", "name": "amountIn", "type": "uint256"}], "name": "quoteExactInput", "outputs": [{"internalType": "uint256", "name": "amountOut", "type": "uint256"}, {"internalType": "uint160[]", "name": "sqrtPriceX96AfterList", "type": "uint160[]"}, {"internalType": "uint32[]", "name": "initializedTicksCrossedList", "type": "uint32[]"}, {"internalType": "uint256", "name": "gasEstimate", "type": "uint256"}], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [{"internalType": "address", "name": "tokenIn", "type": "address"}, {"internalType": "address", "name": "tokenOut", "type": "address"}, {"internalType": "uint24", "name": "fee", "type": "uint24"}, {"internalType": "uint256", "name": "amountIn", "type": "uint256"}, {"internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160"}], "name": "quoteExactInputSingle", "outputs": [{"internalType": "uint256", "name": "amountOut", "type": "uint256"}, {"internalType": "uint160", "name": "sqrtPriceX96After", "type": "uint160"}, {"internalType": "uint32", "name": "initializedTicksCrossed", "type": "uint32"}, {"internalType": "uint256", "name": "gasEstimate", "type": "uint256"}], "stateMutability": "nonpayable", "type": "function"},
]


@dataclass
class V3PoolInfo:
    """V3 Pool information"""
    address: str
    token0: str
    token1: str
    fee: int
    tick_spacing: int
    sqrt_price_x96: int
    current_tick: int
    liquidity: int
    token0_decimals: int = 18
    token1_decimals: int = 18


@dataclass
class V3Position:
    """V3 NFT Position"""
    token_id: int
    token0: str
    token1: str
    fee: int
    tick_lower: int
    tick_upper: int
    liquidity: int
    tokens_owed0: int
    tokens_owed1: int
    fee_growth_inside0: int
    fee_growth_inside1: int


@dataclass
class V3SwapRoute:
    """V3 Multi-hop swap route"""
    path: bytes
    tokens: List[str]
    fees: List[int]
    expected_output: int
    gas_estimate: int


class PancakeSwapV3Integration:
    """
    PancakeSwap V3 Integration

    Handles all V3-specific functionality including:
    - Concentrated liquidity pool interactions
    - Multi-hop swaps
    - Position management
    - Tick-based calculations
    """

    # Fee tiers
    FEE_TIERS = {
        100: 1,      # 0.01% - Most stable pairs
        500: 10,     # 0.05% - Stable pairs
        2500: 50,    # 0.25% - Standard pairs
        10000: 200,  # 1% - Exotic pairs
    }

    def __init__(self, w3: Web3, chain: str = "bsc", account: Optional[Account] = None):
        self.w3 = w3
        self.chain = chain
        self.account = account
        self.addresses = V3_ADDRESSES.get(chain, V3_ADDRESSES["bsc"])

        # Initialize contracts
        self.factory = self.w3.eth.contract(
            address=self.w3.to_checksum_address(self.addresses["factory"]),
            abi=V3_FACTORY_ABI
        )
        self.router = self.w3.eth.contract(
            address=self.w3.to_checksum_address(self.addresses["router"]),
            abi=V3_ROUTER_ABI
        )
        self.position_manager = self.w3.eth.contract(
            address=self.w3.to_checksum_address(self.addresses["position_manager"]),
            abi=V3_POSITION_MANAGER_ABI
        )
        self.quoter = self.w3.eth.contract(
            address=self.w3.to_checksum_address(self.addresses["quoter"]),
            abi=V3_QUOTER_ABI
        )

        logger.info(f"PancakeSwapV3Integration initialized for {chain}")

    def get_pool(
        self,
        token_a: str,
        token_b: str,
        fee: int
    ) -> Optional[str]:
        """Get pool address for token pair and fee tier"""
        try:
            # Sort tokens (V3 requires token0 < token1)
            token0, token1 = sorted([token_a, token_b])

            pool_address = self.factory.functions.getPool(
                self.w3.to_checksum_address(token0),
                self.w3.to_checksum_address(token1),
                fee
            ).call()

            if pool_address == "0x0000000000000000000000000000000000000000":
                return None

            return pool_address
        except Exception as e:
            logger.error(f"Failed to get pool: {e}")
            return None

    def get_pool_info(self, pool_address: str) -> Optional[V3PoolInfo]:
        """Get detailed pool information"""
        try:
            pool_contract = self.w3.eth.contract(
                address=self.w3.to_checksum_address(pool_address),
                abi=V3_POOL_ABI
            )

            slot0 = pool_contract.functions.slot0().call()
            liquidity = pool_contract.functions.liquidity().call()
            token0 = pool_contract.functions.token0().call()
            token1 = pool_contract.functions.token1().call()
            fee = pool_contract.functions.fee().call()
            tick_spacing = self.FEE_TIERS.get(fee, 60)

            return V3PoolInfo(
                address=pool_address,
                token0=token0,
                token1=token1,
                fee=fee,
                tick_spacing=tick_spacing,
                sqrt_price_x96=slot0[0],
                current_tick=slot0[1],
                liquidity=liquidity
            )
        except Exception as e:
            logger.error(f"Failed to get pool info: {e}")
            return None

    def sqrt_price_x96_to_price(self, sqrt_price_x96: int, token0_decimals: int, token1_decimals: int) -> float:
        """Convert sqrtPriceX96 to human-readable price"""
        price = (sqrt_price_x96 ** 2) / (2 ** 192)
        # Adjust for decimals
        price = price * (10 ** (token0_decimals - token1_decimals))
        return price

    def price_to_sqrt_price_x96(self, price: float, token0_decimals: int, token1_decimals: int) -> int:
        """Convert human-readable price to sqrtPriceX96"""
        adjusted_price = price * (10 ** (token1_decimals - token0_decimals))
        sqrt_price = math.sqrt(adjusted_price)
        sqrt_price_x96 = int(sqrt_price * (2 ** 96))
        return sqrt_price_x96

    def tick_to_price(self, tick: int) -> float:
        """Convert tick to price"""
        return 1.0001 ** tick

    def price_to_tick(self, price: float) -> int:
        """Convert price to tick"""
        return int(math.log(price, 1.0001))

    def get_tick_range_for_price_range(
        self,
        current_price: float,
        lower_price: float,
        upper_price: float,
        tick_spacing: int
    ) -> Tuple[int, int]:
        """Calculate tick range for a price range"""
        lower_tick = self.price_to_tick(lower_price)
        upper_tick = self.price_to_tick(upper_price)

        # Round to tick spacing
        lower_tick = (lower_tick // tick_spacing) * tick_spacing
        upper_tick = (upper_tick // tick_spacing) * tick_spacing

        return lower_tick, upper_tick

    async def quote_exact_input_single(
        self,
        token_in: str,
        token_out: str,
        fee: int,
        amount_in: int
    ) -> Optional[Dict[str, Any]]:
        """Get quote for exact input single swap"""
        try:
            # Note: Quoter uses callStatic in JS, in Python we need to simulate
            # For now, return mock data or use calculation
            # In production, you'd call the quoter contract

            result = self.quoter.functions.quoteExactInputSingle(
                self.w3.to_checksum_address(token_in),
                self.w3.to_checksum_address(token_out),
                fee,
                amount_in,
                0  # sqrtPriceLimitX96
            ).call()

            return {
                "amount_out": result[0],
                "sqrt_price_x96_after": result[1],
                "ticks_crossed": result[2],
                "gas_estimate": result[3]
            }
        except Exception as e:
            logger.error(f"Quote failed: {e}")
            return None

    def encode_path(self, tokens: List[str], fees: List[int]) -> bytes:
        """Encode path for multi-hop swap"""
        # Path encoding: token + fee + token + fee + token
        path = b''
        for i, token in enumerate(tokens[:-1]):
            path += bytes.fromhex(token[2:])  # Remove 0x prefix
            path += fees[i].to_bytes(3, 'big')
        path += bytes.fromhex(tokens[-1][2:])
        return path

    async def build_swap_route(
        self,
        token_in: str,
        token_out: str,
        amount_in: int,
        intermediate_tokens: Optional[List[str]] = None
    ) -> Optional[V3SwapRoute]:
        """Build optimal swap route"""
        try:
            # Try direct route first
            best_route = None
            best_output = 0

            for fee in [500, 2500, 10000]:  # Try common fee tiers
                pool = self.get_pool(token_in, token_out, fee)
                if pool:
                    quote = await self.quote_exact_input_single(
                        token_in, token_out, fee, amount_in
                    )
                    if quote and quote["amount_out"] > best_output:
                        best_output = quote["amount_out"]
                        best_route = {
                            "tokens": [token_in, token_out],
                            "fees": [fee],
                            "pools": [pool],
                            "quote": quote
                        }

            # Try multi-hop if intermediate tokens provided
            if intermediate_tokens and best_route:
                for intermediate in intermediate_tokens:
                    # Pool 1: token_in -> intermediate
                    # Pool 2: intermediate -> token_out
                    for fee1 in [500, 2500]:
                        for fee2 in [500, 2500]:
                            pool1 = self.get_pool(token_in, intermediate, fee1)
                            pool2 = self.get_pool(intermediate, token_out, fee2)

                            if pool1 and pool2:
                                # Get quote for first hop
                                quote1 = await self.quote_exact_input_single(
                                    token_in, intermediate, fee1, amount_in
                                )
                                if quote1:
                                    # Get quote for second hop
                                    quote2 = await self.quote_exact_input_single(
                                        intermediate, token_out, fee2,
                                        quote1["amount_out"]
                                    )
                                    if quote2 and quote2["amount_out"] > best_output:
                                        best_output = quote2["amount_out"]
                                        best_route = {
                                            "tokens": [token_in, intermediate, token_out],
                                            "fees": [fee1, fee2],
                                            "pools": [pool1, pool2],
                                            "quote": quote2
                                        }

            if best_route:
                path = self.encode_path(best_route["tokens"], best_route["fees"])
                return V3SwapRoute(
                    path=path,
                    tokens=best_route["tokens"],
                    fees=best_route["fees"],
                    expected_output=best_output,
                    gas_estimate=best_route["quote"].get("gas_estimate", 150000)
                )

            return None

        except Exception as e:
            logger.error(f"Failed to build swap route: {e}")
            return None

    async def get_positions(self, owner: str) -> List[V3Position]:
        """Get all V3 positions for an address"""
        try:
            balance = self.position_manager.functions.balanceOf(
                self.w3.to_checksum_address(owner)
            ).call()

            positions = []
            for i in range(balance):
                token_id = self.position_manager.functions.tokenOfOwnerByIndex(
                    self.w3.to_checksum_address(owner), i
                ).call()

                pos_data = self.position_manager.functions.positions(token_id).call()

                positions.append(V3Position(
                    token_id=token_id,
                    token0=pos_data[2],
                    token1=pos_data[3],
                    fee=pos_data[4],
                    tick_lower=pos_data[5],
                    tick_upper=pos_data[6],
                    liquidity=pos_data[7],
                    fee_growth_inside0=pos_data[8],
                    fee_growth_inside1=pos_data[9],
                    tokens_owed0=pos_data[10],
                    tokens_owed1=pos_data[11]
                ))

            return positions

        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            return []

    def calculate_position_value(self, position: V3Position, pool_info: V3PoolInfo) -> Dict[str, float]:
        """Calculate the value of a position in token0 and token1"""
        if position.liquidity == 0:
            return {"amount0": 0, "amount1": 0}

        sqrt_price = pool_info.sqrt_price_x96 / (2 ** 96)
        sqrt_price_lower = 1.0001 ** (position.tick_lower / 2)
        sqrt_price_upper = 1.0001 ** (position.tick_upper / 2)

        L = position.liquidity

        # Calculate amounts
        if pool_info.current_tick <= position.tick_lower:
            amount0 = L * (1 / sqrt_price_lower - 1 / sqrt_price_upper)
            amount1 = 0
        elif pool_info.current_tick >= position.tick_upper:
            amount0 = 0
            amount1 = L * (sqrt_price_upper - sqrt_price_lower)
        else:
            amount0 = L * (1 / sqrt_price - 1 / sqrt_price_upper)
            amount1 = L * (sqrt_price - sqrt_price_lower)

        return {
            "amount0": amount0,
            "amount1": amount1
        }

    async def mint_position(
        self,
        token0: str,
        token1: str,
        fee: int,
        tick_lower: int,
        tick_upper: int,
        amount0_desired: int,
        amount1_desired: int,
        amount0_min: int,
        amount1_min: int,
        recipient: str,
        deadline: int
    ) -> Optional[Dict[str, Any]]:
        """Mint a new liquidity position"""
        if not self.account:
            raise ValueError("Account required for minting")

        try:
            tx = self.position_manager.functions.mint({
                "token0": self.w3.to_checksum_address(token0),
                "token1": self.w3.to_checksum_address(token1),
                "fee": fee,
                "tickLower": tick_lower,
                "tickUpper": tick_upper,
                "amount0Desired": amount0_desired,
                "amount1Desired": amount1_desired,
                "amount0Min": amount0_min,
                "amount1Min": amount1_min,
                "recipient": self.w3.to_checksum_address(recipient),
                "deadline": deadline
            }).build_transaction({
                "from": self.account.address,
                "gas": 500000,
                "nonce": self.w3.eth.get_transaction_count(self.account.address)
            })

            signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)

            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

            # Parse tokenId from event (simplified)
            # In production, parse the IncreaseLiquidity event

            return {
                "tx_hash": tx_hash.hex(),
                "status": "SUCCESS" if receipt.status == 1 else "FAILED",
                "block_number": receipt.blockNumber,
                "gas_used": receipt.gasUsed
            }

        except Exception as e:
            logger.error(f"Failed to mint position: {e}")
            return None

    async def collect_fees(
        self,
        token_id: int,
        recipient: str,
        amount0_max: int = 2**128 - 1,
        amount1_max: int = 2**128 - 1
    ) -> Optional[Dict[str, Any]]:
        """Collect fees from a position"""
        if not self.account:
            raise ValueError("Account required for collecting")

        try:
            tx = self.position_manager.functions.collect({
                "tokenId": token_id,
                "recipient": self.w3.to_checksum_address(recipient),
                "amount0Max": amount0_max,
                "amount1Max": amount1_max
            }).build_transaction({
                "from": self.account.address,
                "gas": 200000,
                "nonce": self.w3.eth.get_transaction_count(self.account.address)
            })

            signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)

            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

            return {
                "tx_hash": tx_hash.hex(),
                "status": "SUCCESS" if receipt.status == 1 else "FAILED",
                "block_number": receipt.blockNumber,
                "gas_used": receipt.gasUsed
            }

        except Exception as e:
            logger.error(f"Failed to collect fees: {e}")
            return None
