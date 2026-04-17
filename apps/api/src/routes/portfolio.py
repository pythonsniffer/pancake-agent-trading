from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta

from ..models.database import get_db
from ..models.portfolio import PortfolioSnapshot

router = APIRouter()


class PortfolioResponse(BaseModel):
    id: str
    total_value_usd: float
    available_balance_usd: float
    allocated_balance_usd: float
    total_pnl_usd: float
    total_pnl_percent: float
    win_rate: float
    total_trades: int
    sharpe_ratio: float
    max_drawdown_percent: float
    snapshot_at: str

    class Config:
        from_attributes = True


@router.get("/current", response_model=PortfolioResponse)
async def get_current_portfolio(db: Session = Depends(get_db)):
    """Get current portfolio snapshot"""
    portfolio = db.query(PortfolioSnapshot).order_by(
        PortfolioSnapshot.snapshot_at.desc()
    ).first()

    if not portfolio:
        # Return empty portfolio
        return PortfolioResponse(
            id="empty",
            total_value_usd=0,
            available_balance_usd=0,
            allocated_balance_usd=0,
            total_pnl_usd=0,
            total_pnl_percent=0,
            win_rate=0,
            total_trades=0,
            sharpe_ratio=0,
            max_drawdown_percent=0,
            snapshot_at=datetime.utcnow().isoformat()
        )

    return PortfolioResponse(**portfolio.to_dict())


@router.get("/history")
async def get_portfolio_history(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get portfolio history over time"""
    start_date = datetime.utcnow() - timedelta(days=days)

    snapshots = db.query(PortfolioSnapshot).filter(
        PortfolioSnapshot.snapshot_at >= start_date
    ).order_by(
        PortfolioSnapshot.snapshot_at.asc()
    ).all()

    return {
        "history": [snapshot.to_dict() for snapshot in snapshots],
        "count": len(snapshots)
    }


@router.get("/metrics")
async def get_portfolio_metrics(db: Session = Depends(get_db)):
    """Get detailed portfolio metrics"""
    from sqlalchemy import func

    # Get latest snapshot
    latest = db.query(PortfolioSnapshot).order_by(
        PortfolioSnapshot.snapshot_at.desc()
    ).first()

    # Get 24h ago snapshot
    day_ago = datetime.utcnow() - timedelta(days=1)
    day_ago_snapshot = db.query(PortfolioSnapshot).filter(
        PortfolioSnapshot.snapshot_at <= day_ago
    ).order_by(
        PortfolioSnapshot.snapshot_at.desc()
    ).first()

    # Calculate 24h change
    change_24h = 0
    if latest and day_ago_snapshot and day_ago_snapshot.total_value_usd > 0:
        change_24h = ((latest.total_value_usd - day_ago_snapshot.total_value_usd)
                      / day_ago_snapshot.total_value_usd * 100)

    # Get averages
    avg_metrics = db.query(
        func.avg(PortfolioSnapshot.sharpe_ratio).label('avg_sharpe'),
        func.avg(PortfolioSnapshot.win_rate).label('avg_win_rate'),
        func.avg(PortfolioSnapshot.max_drawdown_percent).label('avg_drawdown')
    ).first()

    return {
        "current": latest.to_dict() if latest else None,
        "change_24h_percent": round(change_24h, 2),
        "avg_sharpe_ratio": round(avg_metrics.avg_sharpe or 0, 2),
        "avg_win_rate": round(avg_metrics.avg_win_rate or 0, 2),
        "avg_max_drawdown": round(avg_metrics.avg_drawdown or 0, 2),
    }


@router.get("/pnl/breakdown")
async def get_pnl_breakdown(db: Session = Depends(get_db)):
    """Get P&L breakdown by different dimensions"""
    from sqlalchemy import func

    latest = db.query(PortfolioSnapshot).order_by(
        PortfolioSnapshot.snapshot_at.desc()
    ).first()

    if not latest:
        return {"error": "No portfolio data available"}

    breakdown = {
        "total_pnl_usd": latest.total_pnl_usd,
        "realized_pnl_usd": latest.realized_pnl_usd,
        "unrealized_pnl_usd": latest.unrealized_pnl_usd,
        "total_fees_usd": latest.total_fees_usd,
        "total_gas_usd": latest.total_gas_usd,
        "net_pnl_usd": latest.total_pnl_usd - latest.total_gas_usd - latest.total_fees_usd,
    }

    # Chain breakdown
    chain_breakdown = latest.chain_breakdown or {}

    return {
        "summary": breakdown,
        "by_chain": chain_breakdown,
        "win_rate": latest.win_rate,
        "profit_factor": latest.profit_factor,
    }


@router.get("/positions")
async def get_open_positions(db: Session = Depends(get_db)):
    """Get current open positions"""
    latest = db.query(PortfolioSnapshot).order_by(
        PortfolioSnapshot.snapshot_at.desc()
    ).first()

    if not latest:
        return {"positions": []}

    return {
        "positions": latest.positions or [],
        "total_positions": len(latest.positions or []),
    }


@router.get("/assets")
async def get_portfolio_assets(db: Session = Depends(get_db)):
    """Get portfolio asset allocation"""
    latest = db.query(PortfolioSnapshot).order_by(
        PortfolioSnapshot.snapshot_at.desc()
    ).first()

    if not latest:
        return {"assets": []}

    return {
        "assets": latest.tokens or [],
        "total_value_usd": latest.total_value_usd,
    }
