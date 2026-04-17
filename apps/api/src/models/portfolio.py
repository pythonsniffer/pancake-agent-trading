from sqlalchemy import Column, String, Float, DateTime, Integer, JSON
from sqlalchemy.sql import func
from uuid import uuid4
from .database import Base


class PortfolioSnapshot(Base):
    __tablename__ = "portfolio_snapshots"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))

    # Portfolio values
    total_value_usd = Column(Float, nullable=False)
    available_balance_usd = Column(Float, default=0)
    allocated_balance_usd = Column(Float, default=0)

    # Performance metrics
    total_pnl_usd = Column(Float, default=0)
    total_pnl_percent = Column(Float, default=0)
    realized_pnl_usd = Column(Float, default=0)
    unrealized_pnl_usd = Column(Float, default=0)

    # Trade statistics
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    win_rate = Column(Float, default=0)

    # Financial metrics
    avg_profit_usd = Column(Float, default=0)
    avg_loss_usd = Column(Float, default=0)
    profit_factor = Column(Float, default=0)
    sharpe_ratio = Column(Float, default=0)
    max_drawdown_percent = Column(Float, default=0)

    # Costs
    total_gas_usd = Column(Float, default=0)
    total_fees_usd = Column(Float, default=0)

    # Holdings
    tokens = Column(JSON, default=list)
    positions = Column(JSON, default=list)

    # Chain breakdown
    chain_breakdown = Column(JSON, default=dict)

    # Timestamp
    snapshot_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self):
        return {
            'id': str(self.id),
            'total_value_usd': self.total_value_usd,
            'available_balance_usd': self.available_balance_usd,
            'allocated_balance_usd': self.allocated_balance_usd,
            'total_pnl_usd': self.total_pnl_usd,
            'total_pnl_percent': self.total_pnl_percent,
            'realized_pnl_usd': self.realized_pnl_usd,
            'unrealized_pnl_usd': self.unrealized_pnl_usd,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': self.win_rate,
            'avg_profit_usd': self.avg_profit_usd,
            'avg_loss_usd': self.avg_loss_usd,
            'profit_factor': self.profit_factor,
            'sharpe_ratio': self.sharpe_ratio,
            'max_drawdown_percent': self.max_drawdown_percent,
            'total_gas_usd': self.total_gas_usd,
            'total_fees_usd': self.total_fees_usd,
            'tokens': self.tokens,
            'positions': self.positions,
            'chain_breakdown': self.chain_breakdown,
            'snapshot_at': self.snapshot_at.isoformat() if self.snapshot_at else None,
        }
