from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta

from ..models.database import get_db
from ..models.trade import Trade, TradeStatus, TradeStrategy

router = APIRouter()


class TradeResponse(BaseModel):
    id: str
    signal_id: Optional[str] = None
    tx_hash: Optional[str] = None
    chain: str
    strategy: Optional[str] = None
    status: str
    token_in_address: str
    token_in_symbol: Optional[str] = None
    token_out_address: str
    token_out_symbol: Optional[str] = None
    amount_in: Optional[str] = None
    amount_out: Optional[str] = None
    amount_in_usd: Optional[float] = None
    amount_out_usd: Optional[float] = None
    profit_usd: Optional[float] = None
    profit_percent: Optional[float] = None
    gas_cost_usd: Optional[float] = None
    created_at: Optional[str] = None
    timestamp: Optional[str] = None

    class Config:
        from_attributes = True


class TradeListResponse(BaseModel):
    trades: List[TradeResponse]
    total: int
    page: int
    limit: int


# IMPORTANT: static routes MUST come before /{trade_id}

@router.get("/stats/summary")
async def get_trade_stats(db: Session = Depends(get_db)):
    """Get trade statistics summary"""
    from sqlalchemy import func

    total_trades = db.query(Trade).count()
    successful_trades = db.query(Trade).filter(Trade.status == TradeStatus.SUCCESS).count()
    failed_trades = db.query(Trade).filter(Trade.status == TradeStatus.FAILED).count()

    total_profit = db.query(func.sum(Trade.profit_usd)).filter(
        Trade.status == TradeStatus.SUCCESS
    ).scalar() or 0

    total_gas = db.query(func.sum(Trade.gas_cost_usd)).scalar() or 0

    day_ago = datetime.utcnow() - timedelta(days=1)
    trades_24h = db.query(Trade).filter(Trade.created_at >= day_ago).count()

    return {
        "total_trades": total_trades,
        "successful_trades": successful_trades,
        "failed_trades": failed_trades,
        "win_rate": (successful_trades / total_trades * 100) if total_trades > 0 else 0,
        "total_profit_usd": round(total_profit, 2),
        "total_gas_usd": round(total_gas, 2),
        "net_profit_usd": round(total_profit - total_gas, 2),
        "trades_24h": trades_24h,
    }


@router.get("/history/daily")
async def get_daily_trade_history(days: int = Query(30, ge=1, le=365), db: Session = Depends(get_db)):
    """Get daily trade history for charts"""
    from sqlalchemy import func

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    results = db.query(
        func.date(Trade.created_at).label('date'),
        func.count(Trade.id).label('count'),
        func.sum(Trade.profit_usd).label('profit'),
        func.sum(Trade.gas_cost_usd).label('gas_cost')
    ).filter(
        Trade.created_at >= start_date
    ).group_by(
        func.date(Trade.created_at)
    ).order_by('date').all()

    return [
        {
            "date": str(result.date) if result.date else None,
            "trades": result.count,
            "profit_usd": round(result.profit or 0, 2),
            "gas_cost_usd": round(result.gas_cost or 0, 2),
            "net_profit_usd": round((result.profit or 0) - (result.gas_cost or 0), 2),
        }
        for result in results
    ]


@router.get("", response_model=TradeListResponse)
async def get_trades(
    status: Optional[str] = Query(None, description="Filter by status"),
    strategy: Optional[str] = Query(None, description="Filter by strategy"),
    chain: Optional[str] = Query(None, description="Filter by chain"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get all trades with optional filtering"""
    query = db.query(Trade)

    if status:
        query = query.filter(Trade.status == status)
    if strategy:
        query = query.filter(Trade.strategy == strategy)
    if chain:
        query = query.filter(Trade.chain == chain)

    total = query.count()
    trades = query.order_by(Trade.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

    trade_list = []
    for trade in trades:
        d = trade.to_dict()
        d['timestamp'] = d.get('created_at')
        trade_list.append(TradeResponse(**d))

    return TradeListResponse(
        trades=trade_list,
        total=total,
        page=page,
        limit=limit
    )


@router.get("/{trade_id}", response_model=TradeResponse)
async def get_trade(trade_id: str, db: Session = Depends(get_db)):
    """Get a specific trade by ID"""
    trade = db.query(Trade).filter(Trade.id == trade_id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    d = trade.to_dict()
    d['timestamp'] = d.get('created_at')
    return TradeResponse(**d)
