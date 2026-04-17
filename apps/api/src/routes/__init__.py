from fastapi import APIRouter
from .trades import router as trades_router
from .pools import router as pools_router
from .portfolio import router as portfolio_router
from .agents import router as agents_router
from .websocket import router as websocket_router

api_router = APIRouter()

api_router.include_router(trades_router, prefix="/trades", tags=["trades"])
api_router.include_router(pools_router, prefix="/pools", tags=["pools"])
api_router.include_router(portfolio_router, prefix="/portfolio", tags=["portfolio"])
api_router.include_router(agents_router, prefix="/agents", tags=["agents"])
api_router.include_router(websocket_router, prefix="/ws", tags=["websocket"])

__all__ = ['api_router']
