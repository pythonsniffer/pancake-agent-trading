from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from ..models.database import get_db
from ..models.pool import Pool, PoolCategory

router = APIRouter()


class PoolResponse(BaseModel):
    id: str
    address: str
    chain: str
    dex: str
    version: str
    token0: dict
    token1: dict
    reserve0: Optional[str] = None
    reserve1: Optional[str] = None
    tvl_usd: float
    volume24h_usd: Optional[float] = None
    fee_rate: float
    category: Optional[str] = None
    apr24h: Optional[float] = None
    last_updated: Optional[str] = None

    class Config:
        from_attributes = True


class PoolListResponse(BaseModel):
    pools: List[PoolResponse]
    total: int
    page: int
    limit: int


# IMPORTANT: static routes MUST come before /{pool_address}

@router.get("/arbitrage/opportunities")
async def get_arbitrage_opportunities(
    min_spread_percent: float = Query(0.5, description="Minimum spread percentage"),
    db: Session = Depends(get_db)
):
    """Get current arbitrage opportunities across pools"""
    pools = db.query(Pool).filter(Pool.tvl_usd > 10000).all()

    pairs = {}
    for pool in pools:
        pair_key = tuple(sorted([pool.token0_address, pool.token1_address]))
        if pair_key not in pairs:
            pairs[pair_key] = []
        pairs[pair_key].append(pool)

    opportunities = []
    for pair_key, pair_pools in pairs.items():
        if len(pair_pools) < 2:
            continue

        prices = [(p, p.price0) for p in pair_pools if p.price0]
        if len(prices) < 2:
            continue

        prices.sort(key=lambda x: x[1])
        lowest_price_pool, lowest_price = prices[0]
        highest_price_pool, highest_price = prices[-1]

        spread_percent = ((highest_price - lowest_price) / lowest_price) * 100

        if spread_percent >= min_spread_percent:
            opportunities.append({
                "token0": pair_key[0],
                "token1": pair_key[1],
                "buy_pool": lowest_price_pool.address,
                "sell_pool": highest_price_pool.address,
                "buy_price": lowest_price,
                "sell_price": highest_price,
                "spread_percent": round(spread_percent, 4),
                "estimated_profit_usd": round(spread_percent * lowest_price_pool.tvl_usd * 0.001, 2),
            })

    opportunities.sort(key=lambda x: x["spread_percent"], reverse=True)

    return {
        "opportunities": opportunities[:20],
        "count": len(opportunities),
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/top/apy")
async def get_top_apys(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get top pools by APY"""
    pools = db.query(Pool).filter(
        Pool.apr24h.isnot(None)
    ).order_by(
        Pool.apr24h.desc()
    ).limit(limit).all()

    return {
        "pools": [pool.to_dict() for pool in pools],
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("", response_model=PoolListResponse)
async def get_pools(
    chain: Optional[str] = Query(None, description="Filter by chain"),
    category: Optional[str] = Query(None, description="Filter by category"),
    min_tvl: Optional[float] = Query(None, description="Minimum TVL in USD"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get all liquidity pools with optional filtering"""
    query = db.query(Pool)

    if chain:
        query = query.filter(Pool.chain == chain)
    if category:
        query = query.filter(Pool.category == category)
    if min_tvl:
        query = query.filter(Pool.tvl_usd >= min_tvl)

    total = query.count()
    pools = query.order_by(Pool.tvl_usd.desc()).offset((page - 1) * limit).limit(limit).all()

    return PoolListResponse(
        pools=[PoolResponse(**pool.to_dict()) for pool in pools],
        total=total,
        page=page,
        limit=limit
    )


@router.get("/{pool_address}", response_model=PoolResponse)
async def get_pool(pool_address: str, db: Session = Depends(get_db)):
    """Get a specific pool by address"""
    pool = db.query(Pool).filter(Pool.address == pool_address).first()
    if not pool:
        raise HTTPException(status_code=404, detail="Pool not found")
    return PoolResponse(**pool.to_dict())
