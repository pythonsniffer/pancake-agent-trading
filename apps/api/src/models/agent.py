from sqlalchemy import Column, String, Float, DateTime, Enum as SQLEnum, Integer, JSON
from sqlalchemy.sql import func
from uuid import uuid4
from .database import Base
import enum


class AgentStatus(str, enum.Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    ERROR = "ERROR"
    STOPPED = "STOPPED"


class AgentType(str, enum.Enum):
    MARKET_INTELLIGENCE = "MARKET_INTELLIGENCE"
    STRATEGY = "STRATEGY"
    EXECUTION = "EXECUTION"
    RISK_MANAGEMENT = "RISK_MANAGEMENT"
    PORTFOLIO = "PORTFOLIO"
    LIQUIDITY_ANALYSIS = "LIQUIDITY_ANALYSIS"
    BACKTEST = "BACKTEST"


class AgentState(Base):
    __tablename__ = "agent_states"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))

    # Agent identification
    agent_id = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    type = Column(SQLEnum(AgentType), nullable=False)

    # Status
    status = Column(SQLEnum(AgentStatus), default=AgentStatus.IDLE)

    # Configuration
    config = Column(JSON, default=dict)

    # Memory
    short_term_memory = Column(JSON, default=list)
    long_term_memory_ids = Column(JSON, default=list)

    # Statistics
    success_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    total_actions = Column(Integer, default=0)

    # Last action
    last_action = Column(String(255))
    last_action_at = Column(DateTime(timezone=True))
    last_error = Column(String(500))

    # Metadata
    agent_metadata = Column(JSON, default=dict)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def to_dict(self):
        return {
            'id': str(self.id),
            'agent_id': self.agent_id,
            'name': self.name,
            'type': self.type.value if self.type else None,
            'status': self.status.value if self.status else None,
            'config': self.config,
            'short_term_memory': self.short_term_memory,
            'long_term_memory_ids': self.long_term_memory_ids,
            'success_count': self.success_count,
            'error_count': self.error_count,
            'total_actions': self.total_actions,
            'last_action': self.last_action,
            'last_action_at': self.last_action_at.isoformat() if self.last_action_at else None,
            'last_error': self.last_error,
            'agent_metadata': self.agent_metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
