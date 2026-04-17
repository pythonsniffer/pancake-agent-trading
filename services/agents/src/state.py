from typing import TypedDict, List, Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum


class AgentStatus(Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    ERROR = "ERROR"
    COMPLETED = "COMPLETED"


@dataclass
class TokenInfo:
    address: str
    symbol: str
    decimals: int = 18
    price_usd: float = 0.0


@dataclass
class PoolInfo:
    address: str
    token0: TokenInfo
    token1: TokenInfo
    reserve0: str = "0"
    reserve1: str = "0"
    tvl_usd: float = 0.0
    volume24h: float = 0.0
    fee_rate: float = 0.0025
    chain: str = "bsc"


@dataclass
class PriceUpdate:
    pool_address: str
    token0_price: float
    token1_price: float
    timestamp: int
    block_number: int


@dataclass
class TradeSignal:
    id: str
    type: str  # ARBITRAGE, TREND_FOLLOWING, MEAN_REVERSION, LP_YIELD
    confidence: float
    token_in: TokenInfo
    token_out: TokenInfo
    amount_in: str
    expected_profit: float
    expected_profit_percent: float
    buy_pool: Optional[PoolInfo] = None
    sell_pool: Optional[PoolInfo] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RiskAssessment:
    signal_id: str
    approved: bool
    risk_score: float
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    checks: List[Dict[str, Any]] = field(default_factory=list)
    rejection_reason: Optional[str] = None


@dataclass
class TradeExecution:
    signal_id: str
    status: str  # PENDING, SUCCESS, FAILED, SIMULATED
    tx_hash: Optional[str] = None
    block_number: Optional[int] = None
    gas_used: Optional[int] = None
    gas_cost_usd: float = 0.0
    actual_profit: float = 0.0
    slippage: float = 0.0
    error_message: Optional[str] = None


@dataclass
class AgentAction:
    agent_name: str
    action: str
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    confidence: float
    timestamp: int
    duration_ms: int


class TradingState(TypedDict):
    """Main state for the trading agent system"""
    # System state
    status: str  # RUNNING, PAUSED, ERROR
    circuit_breaker_triggered: bool

    # Market data
    current_prices: Dict[str, PriceUpdate]
    pools: Dict[str, PoolInfo]
    market_regime: str  # BULL, BEAR, SIDEWAYS, VOLATILE

    # Signals and trades
    pending_signals: List[TradeSignal]
    validated_signals: List[TradeSignal]
    risk_assessments: List[RiskAssessment]
    executed_trades: List[TradeExecution]

    # Portfolio
    portfolio_value: float
    available_balance: float
    positions: List[Dict[str, Any]]

    # Agent memory
    agent_actions: List[AgentAction]
    vector_memory_ids: List[str]

    # Configuration
    config: Dict[str, Any]

    # Messages between agents
    messages: List[Dict[str, Any]]
