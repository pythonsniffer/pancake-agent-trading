"""Seed the database with demo data for development."""
from datetime import datetime, timedelta
from uuid import uuid4
import random

from .models.database import SessionLocal
from .models.agent import AgentState, AgentStatus, AgentType
from .models.trade import Trade, TradeStatus, TradeStrategy
from .models.portfolio import PortfolioSnapshot
from .models.pool import Pool, PoolCategory


def seed_db():
    """Populate database with demo data if empty."""
    db = SessionLocal()
    try:
        # Only seed if agents table is empty
        if db.query(AgentState).count() > 0:
            return

        _seed_agents(db)
        _seed_trades(db)
        _seed_portfolio(db)
        _seed_pools(db)
        db.commit()
        print("[OK] Database seeded with demo data")
    except Exception as e:
        db.rollback()
        print(f"[WARN] Seed error: {e}")
    finally:
        db.close()


def _seed_agents(db):
    agents = [
        ("market_intelligence", "Market Intelligence", AgentType.MARKET_INTELLIGENCE, AgentStatus.RUNNING, 156, 3, 159, "market_scan"),
        ("strategy", "Strategy Engine", AgentType.STRATEGY, AgentStatus.RUNNING, 89, 2, 91, "generate_signals"),
        ("execution", "Trade Execution", AgentType.EXECUTION, AgentStatus.RUNNING, 234, 5, 239, "execute_swap"),
        ("risk_management", "Risk Management", AgentType.RISK_MANAGEMENT, AgentStatus.RUNNING, 45, 1, 46, "validate_trade"),
        ("portfolio", "Portfolio Manager", AgentType.PORTFOLIO, AgentStatus.IDLE, 78, 0, 78, "update_pnl"),
        ("liquidity_analysis", "Liquidity Analysis", AgentType.LIQUIDITY_ANALYSIS, AgentStatus.IDLE, 123, 2, 125, "scan_pools"),
        ("backtest", "Backtester", AgentType.BACKTEST, AgentStatus.IDLE, 12, 0, 12, "run_simulation"),
    ]
    now = datetime.utcnow()
    for agent_id, name, atype, status, success, errors, total, action in agents:
        db.add(AgentState(
            id=str(uuid4()),
            agent_id=agent_id,
            name=name,
            type=atype,
            status=status,
            config={"interval_ms": 5000},
            success_count=success,
            error_count=errors,
            total_actions=total,
            last_action=action,
            last_action_at=now - timedelta(seconds=random.randint(1, 120)),
        ))


def _seed_trades(db):
    tokens = [
        ("0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c", "BNB"),
        ("0x55d398326f99059fF775485246999027B3197955", "USDT"),
        ("0x2170Ed0880ac9A755fd29B2688956BD959F933F8", "ETH"),
        ("0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d", "USDC"),
        ("0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82", "CAKE"),
        ("0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c", "BTCB"),
    ]
    strategies = list(TradeStrategy)
    now = datetime.utcnow()

    for i in range(20):
        t_in = random.choice(tokens)
        t_out = random.choice([t for t in tokens if t[0] != t_in[0]])
        status = random.choices(
            [TradeStatus.SUCCESS, TradeStatus.FAILED, TradeStatus.SIMULATED],
            weights=[70, 15, 15]
        )[0]
        amount_usd = round(random.uniform(50, 2000), 2)
        profit = round(random.uniform(-20, 50), 2) if status == TradeStatus.SUCCESS else round(random.uniform(-30, -1), 2) if status == TradeStatus.FAILED else 0
        gas = round(random.uniform(0.5, 8), 2)

        db.add(Trade(
            id=str(uuid4()),
            signal_id=f"sig_{uuid4().hex[:8]}",
            tx_hash=f"0x{uuid4().hex}{uuid4().hex[:30]}" if status != TradeStatus.SIMULATED else None,
            chain="BSC",
            strategy=random.choice(strategies),
            status=status,
            token_in_address=t_in[0],
            token_in_symbol=t_in[1],
            token_out_address=t_out[0],
            token_out_symbol=t_out[1],
            amount_in=str(int(amount_usd * 1e18)),
            amount_out=str(int((amount_usd + profit) * 1e18)),
            amount_in_usd=amount_usd,
            amount_out_usd=round(amount_usd + profit, 2),
            profit_usd=profit,
            profit_percent=round((profit / amount_usd) * 100, 2) if amount_usd else 0,
            gas_cost_usd=gas,
            gas_price_gwei=round(random.uniform(3, 10), 1),
            slippage=round(random.uniform(0.01, 0.5), 2),
            created_at=now - timedelta(hours=random.randint(0, 168)),
            executed_at=now - timedelta(hours=random.randint(0, 168)),
        ))


def _seed_portfolio(db):
    now = datetime.utcnow()
    base_value = 10000
    for day in range(7, -1, -1):
        pnl = round(random.uniform(-200, 500) + day * 50, 2)
        value = round(base_value + pnl, 2)
        db.add(PortfolioSnapshot(
            id=str(uuid4()),
            total_value_usd=value,
            available_balance_usd=round(value * 0.6, 2),
            allocated_balance_usd=round(value * 0.4, 2),
            total_pnl_usd=pnl,
            total_pnl_percent=round((pnl / base_value) * 100, 2),
            realized_pnl_usd=round(pnl * 0.7, 2),
            unrealized_pnl_usd=round(pnl * 0.3, 2),
            total_trades=156 + day * 5,
            winning_trades=106 + day * 3,
            losing_trades=50 + day * 2,
            win_rate=68.5,
            avg_profit_usd=23.5,
            avg_loss_usd=12.3,
            profit_factor=1.91,
            sharpe_ratio=1.85,
            max_drawdown_percent=4.2,
            total_gas_usd=round(234.5 + day * 10, 2),
            total_fees_usd=round(45.2 + day * 3, 2),
            tokens=[
                {"symbol": "BNB", "balance": 4.5, "value_usd": round(value * 0.35, 2)},
                {"symbol": "USDT", "balance": round(value * 0.25, 2), "value_usd": round(value * 0.25, 2)},
                {"symbol": "CAKE", "balance": 120, "value_usd": round(value * 0.15, 2)},
                {"symbol": "ETH", "balance": 0.8, "value_usd": round(value * 0.15, 2)},
                {"symbol": "BTCB", "balance": 0.05, "value_usd": round(value * 0.10, 2)},
            ],
            positions=[],
            chain_breakdown={"BSC": round(value * 0.85, 2), "ETH": round(value * 0.15, 2)},
            snapshot_at=now - timedelta(days=day),
        ))


def _seed_pools(db):
    pools_data = [
        ("0x16b9a82891338f9bA80E2D6970FddA79D1eb0daE", "BNB", "USDT", 580.0, 1.0, 45_000_000, 12_000_000, 0.0025, 42.5, PoolCategory.BLUE_CHIP),
        ("0x7EFaEf62fDdCCa950418312c6C91Aef321375A00", "CAKE", "BNB", 2.8, 580.0, 28_000_000, 5_500_000, 0.0025, 85.2, PoolCategory.BLUE_CHIP),
        ("0x74E4716E431f45807DCF19f284c7aA99F18a4fbc", "ETH", "BNB", 3200.0, 580.0, 35_000_000, 8_200_000, 0.0025, 38.7, PoolCategory.BLUE_CHIP),
        ("0x61EB789d75A95CAa3fF50ed7E47b96c132fEc082", "BTCB", "BNB", 62000.0, 580.0, 22_000_000, 4_100_000, 0.0025, 28.3, PoolCategory.BLUE_CHIP),
        ("0xEc6557348085Aa57C72514D67070dC863C0a5A8c", "USDC", "USDT", 1.0, 1.0, 18_000_000, 15_000_000, 0.0005, 12.1, PoolCategory.BLUE_CHIP),
        ("0xA39Af17CE4a8eb807E076805Da1e2B8EA7D0755b", "CAKE", "USDT", 2.8, 1.0, 8_500_000, 2_200_000, 0.0025, 95.8, PoolCategory.MID_CAP),
        ("0x346575fC7f07E6994d76199E41D13dC1575322E0", "BNB", "BUSD", 580.0, 1.0, 6_200_000, 1_800_000, 0.0025, 35.4, PoolCategory.MID_CAP),
    ]

    for addr, sym0, sym1, p0, p1, tvl, vol, fee, apr, cat in pools_data:
        db.add(Pool(
            id=str(uuid4()),
            address=addr,
            chain="BSC",
            dex="pancakeswap",
            version="V2",
            token0_address=f"0x{'0' * 38}01",
            token0_symbol=sym0,
            token0_decimals=18,
            token1_address=f"0x{'0' * 38}02",
            token1_symbol=sym1,
            token1_decimals=18,
            reserve0=str(int(tvl / 2 / p0 * 1e18)),
            reserve1=str(int(tvl / 2 / p1 * 1e18)),
            price0=p0,
            price1=p1,
            tvl_usd=tvl,
            volume24h_usd=vol,
            fee_rate=fee,
            fee_tier=fee,
            category=cat,
            apr24h=apr,
        ))
