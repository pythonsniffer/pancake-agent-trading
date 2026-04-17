from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    app_name: str = Field(default="Pancake Trading Agent API")
    debug: bool = Field(default=False)
    version: str = Field(default="1.0.0")

    # Database
    database_url: str = Field(default="postgresql://pancake:pancake123@localhost:5432/trading_agent")

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0")
    redis_password: Optional[str] = Field(default=None)

    # Chroma Vector DB
    chroma_url: str = Field(default="http://localhost:8000")

    # Blockchain RPC URLs
    bsc_rpc_url: str = Field(default="https://bsc-dataseed.binance.org/")
    eth_rpc_url: Optional[str] = Field(default=None)
    arb_rpc_url: Optional[str] = Field(default=None)

    # Wallet
    private_key: Optional[str] = Field(default=None)
    wallet_address: Optional[str] = Field(default=None)

    # OpenAI
    openai_api_key: Optional[str] = Field(default=None)
    openai_model: str = Field(default="gpt-4-turbo-preview")

    # Trading Parameters
    min_profit_usd: float = Field(default=1.0)
    max_slippage_percent: float = Field(default=0.5)
    max_gas_price_gwei: int = Field(default=50)
    default_deadline_minutes: int = Field(default=5)

    # Risk Parameters
    max_position_size_usd: float = Field(default=500.0)
    max_portfolio_exposure_percent: float = Field(default=20.0)
    stop_loss_percent: float = Field(default=5.0)
    take_profit_percent: float = Field(default=10.0)
    max_daily_loss_usd: float = Field(default=100.0)
    circuit_breaker_threshold: float = Field(default=10.0)

    # Agent Parameters
    market_intelligence_interval_ms: int = Field(default=2000)
    strategy_interval_ms: int = Field(default=5000)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
