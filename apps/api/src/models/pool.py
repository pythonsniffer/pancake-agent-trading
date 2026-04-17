from sqlalchemy import Column, String, Float, DateTime, Enum as SQLEnum, Integer
from sqlalchemy.sql import func
from uuid import uuid4
from .database import Base
import enum


class PoolCategory(str, enum.Enum):
    BLUE_CHIP = "BLUE_CHIP"
    MID_CAP = "MID_CAP"
    DEGEN = "DEGEN"
    UNKNOWN = "UNKNOWN"


class Pool(Base):
    __tablename__ = "pools"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))

    # Pool identification
    address = Column(String(42), unique=True, nullable=False, index=True)
    chain = Column(String(20), nullable=False)
    dex = Column(String(20), default="pancakeswap")
    version = Column(String(10), default="V2")

    # Tokens
    token0_address = Column(String(42), nullable=False)
    token0_symbol = Column(String(20))
    token0_decimals = Column(Integer, default=18)
    token1_address = Column(String(42), nullable=False)
    token1_symbol = Column(String(20))
    token1_decimals = Column(Integer, default=18)

    # Reserves
    reserve0 = Column(String(78))
    reserve1 = Column(String(78))
    total_supply = Column(String(78))

    # Prices
    price0 = Column(Float)
    price1 = Column(Float)

    # Metrics
    tvl_usd = Column(Float, default=0)
    volume24h_usd = Column(Float, default=0)
    fee_tier = Column(Float, default=0.0025)
    fee_rate = Column(Float, default=0.0025)

    # Category
    category = Column(SQLEnum(PoolCategory), default=PoolCategory.UNKNOWN)

    # Yield metrics
    apr24h = Column(Float)
    impermanent_loss24h = Column(Float)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated = Column(DateTime(timezone=True), onupdate=func.now())

    def to_dict(self):
        return {
            'id': str(self.id),
            'address': self.address,
            'chain': self.chain,
            'dex': self.dex,
            'version': self.version,
            'token0': {
                'address': self.token0_address,
                'symbol': self.token0_symbol,
                'decimals': self.token0_decimals,
            },
            'token1': {
                'address': self.token1_address,
                'symbol': self.token1_symbol,
                'decimals': self.token1_decimals,
            },
            'reserve0': self.reserve0,
            'reserve1': self.reserve1,
            'total_supply': self.total_supply,
            'price0': self.price0,
            'price1': self.price1,
            'tvl_usd': self.tvl_usd,
            'volume24h_usd': self.volume24h_usd,
            'fee_tier': self.fee_tier,
            'fee_rate': self.fee_rate,
            'category': self.category.value if self.category else None,
            'apr24h': self.apr24h,
            'impermanent_loss24h': self.impermanent_loss24h,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
        }
