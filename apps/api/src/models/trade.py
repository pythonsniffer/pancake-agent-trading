from sqlalchemy import Column, String, Float, DateTime, Enum as SQLEnum, JSON, Integer
from sqlalchemy.sql import func
from uuid import uuid4
from .database import Base
import enum


class TradeStatus(str, enum.Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    SIMULATED = "SIMULATED"


class TradeStrategy(str, enum.Enum):
    ARBITRAGE = "ARBITRAGE"
    TREND_FOLLOWING = "TREND_FOLLOWING"
    MEAN_REVERSION = "MEAN_REVERSION"
    LP_YIELD = "LP_YIELD"
    MOMENTUM = "MOMENTUM"


class Trade(Base):
    __tablename__ = "trades"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    signal_id = Column(String(64))
    tx_hash = Column(String(66), unique=True, nullable=True)

    # Trade details
    chain = Column(String(20), nullable=False)
    strategy = Column(SQLEnum(TradeStrategy), nullable=False)
    status = Column(SQLEnum(TradeStatus), nullable=False, default=TradeStatus.PENDING)

    # Tokens
    token_in_address = Column(String(42), nullable=False)
    token_in_symbol = Column(String(20))
    token_out_address = Column(String(42), nullable=False)
    token_out_symbol = Column(String(20))

    # Amounts
    amount_in = Column(String(78))
    amount_out = Column(String(78))
    amount_in_usd = Column(Float)
    amount_out_usd = Column(Float)

    # Pool
    pool_address = Column(String(42))

    # Gas
    gas_used = Column(String(78))
    gas_price_gwei = Column(Float)
    gas_cost_usd = Column(Float)

    # Profit/Loss
    profit_usd = Column(Float)
    profit_percent = Column(Float)
    slippage = Column(Float)

    # Timing
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    executed_at = Column(DateTime(timezone=True))
    confirmed_at = Column(DateTime(timezone=True))

    # Additional data
    trade_metadata = Column(JSON)
    error_message = Column(String(500))

    def to_dict(self):
        return {
            'id': str(self.id),
            'signal_id': self.signal_id,
            'tx_hash': self.tx_hash,
            'chain': self.chain,
            'strategy': self.strategy.value if self.strategy else None,
            'status': self.status.value if self.status else None,
            'token_in_address': self.token_in_address,
            'token_in_symbol': self.token_in_symbol,
            'token_out_address': self.token_out_address,
            'token_out_symbol': self.token_out_symbol,
            'amount_in': self.amount_in,
            'amount_out': self.amount_out,
            'amount_in_usd': self.amount_in_usd,
            'amount_out_usd': self.amount_out_usd,
            'pool_address': self.pool_address,
            'gas_used': self.gas_used,
            'gas_price_gwei': self.gas_price_gwei,
            'gas_cost_usd': self.gas_cost_usd,
            'profit_usd': self.profit_usd,
            'profit_percent': self.profit_percent,
            'slippage': self.slippage,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'executed_at': self.executed_at.isoformat() if self.executed_at else None,
            'confirmed_at': self.confirmed_at.isoformat() if self.confirmed_at else None,
            'trade_metadata': self.trade_metadata,
            'error_message': self.error_message,
        }
