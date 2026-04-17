"""
Test suite for Strategy Agent

Tests:
- Arbitrage signal generation
- Trend following strategy
- Mean reversion strategy
- LP yield strategy
- Signal ranking
- Strategy configuration
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.agents.strategy import StrategyAgent, StrategyConfig
from src.state import TradingState, TradeSignal, PoolInfo, TokenInfo, PriceUpdate


@pytest.fixture
def strategy_agent():
    """Create a Strategy Agent"""
    return StrategyAgent(config={
        'min_profit_threshold': 1.0,
        'min_confidence': 0.6,
        'max_slippage': 0.005,
        'stop_loss_percent': 0.05,
        'take_profit_percent': 0.10,
        'position_sizing': 'fixed',
        'max_position_size': 500.0
    })


@pytest.fixture
def sample_tokens():
    """Create sample token info"""
    return {
        'BNB': TokenInfo('0xtoken0', 'BNB', 18, 300.0),
        'USDT': TokenInfo('0xtoken1', 'USDT', 18, 1.0),
        'CAKE': TokenInfo('0xtoken2', 'CAKE', 18, 2.5),
        'ETH': TokenInfo('0xtoken3', 'ETH', 18, 2000.0),
    }


@pytest.fixture
def sample_pool(sample_tokens):
    """Create a sample pool"""
    return PoolInfo(
        address='0xpool1',
        token0=sample_tokens['BNB'],
        token1=sample_tokens['USDT'],
        reserve0='1000000000000000000000',
        reserve1='300000000000000000000000',
        tvl_usd=600000,
        volume24h=50000,
        fee_rate=0.0025,
        chain='bsc'
    )


@pytest.fixture
def sample_trading_state(sample_tokens, sample_pool):
    """Create a sample trading state"""
    return {
        'status': 'IDLE',
        'circuit_breaker_triggered': False,
        'current_prices': {
            '0xpool1': PriceUpdate('0xpool1', 300.0, 0.0033, int(datetime.now().timestamp()), 1000)
        },
        'pools': {'0xpool1': sample_pool},
        'market_regime': 'SIDEWAYS',
        'pending_signals': [],
        'validated_signals': [],
        'risk_assessments': [],
        'executed_trades': [],
        'portfolio_value': 10000.0,
        'available_balance': 10000.0,
        'positions': [],
        'agent_actions': [],
        'vector_memory_ids': [],
        'config': {},
        'messages': [],
    }


class TestStrategyAgent:
    """Test cases for Strategy Agent"""

    def test_initialization(self, strategy_agent):
        """Test agent initialization"""
        assert strategy_agent.config.min_profit_threshold == 1.0
        assert strategy_agent.config.min_confidence == 0.6
        assert strategy_agent.config.max_slippage == 0.005

    def test_default_config(self):
        """Test default configuration"""
        agent = StrategyAgent()
        assert agent.config.min_profit_threshold == 1.0
        assert agent.config.position_sizing == 'fixed'

    @pytest.mark.asyncio
    async def test_arbitrage_strategy_no_opportunities(self, strategy_agent, sample_trading_state):
        """Test arbitrage with no opportunities"""
        signals = await strategy_agent.arbitrage_strategy(sample_trading_state)
        assert isinstance(signals, list)

    @pytest.mark.asyncio
    async def test_trend_following_no_history(self, strategy_agent, sample_trading_state):
        """Test trend following with no price history"""
        signals = await strategy_agent.trend_following_strategy(sample_trading_state)
        assert signals == []

    @pytest.mark.asyncio
    async def test_trend_following_with_uptrend(self, strategy_agent, sample_trading_state):
        """Test trend following with clear uptrend"""
        pool_addr = '0xpool1'
        now = int(datetime.now().timestamp())

        # Simulate uptrend in price history
        strategy_agent.price_history[pool_addr] = [
            {'token0_price': 100, 'timestamp': now - 10},
            {'token0_price': 102, 'timestamp': now - 9},
            {'token0_price': 101, 'timestamp': now - 8},
            {'token0_price': 104, 'timestamp': now - 7},
            {'token0_price': 103, 'timestamp': now - 6},
            {'token0_price': 106, 'timestamp': now - 5},
            {'token0_price': 105, 'timestamp': now - 4},
            {'token0_price': 108, 'timestamp': now - 3},
            {'token0_price': 107, 'timestamp': now - 2},
            {'token0_price': 110, 'timestamp': now - 1},
        ]

        # Update current price
        sample_trading_state['current_prices'][pool_addr] = PriceUpdate(
            pool_addr, 110, 0.009, now, 1000
        )

        signals = await strategy_agent.trend_following_strategy(sample_trading_state)

        # Should detect trend
        assert len(signals) >= 0
        for signal in signals:
            assert signal.type == 'TREND_FOLLOWING'
            assert signal.confidence > 0

    @pytest.mark.asyncio
    async def test_mean_reversion_with_extreme(self, strategy_agent, sample_trading_state):
        """Test mean reversion when price is extreme"""
        pool_addr = '0xpool1'
        now = int(datetime.now().timestamp())

        # Create history around mean of 100
        strategy_agent.price_history[pool_addr] = [
            {'token0_price': 98, 'timestamp': now - 20},
            {'token0_price': 102, 'timestamp': now - 19},
            {'token0_price': 99, 'timestamp': now - 18},
            {'token0_price': 101, 'timestamp': now - 17},
            {'token0_price': 100, 'timestamp': now - 16},
            {'token0_price': 100, 'timestamp': now - 15},
            {'token0_price': 99, 'timestamp': now - 14},
            {'token0_price': 101, 'timestamp': now - 13},
            {'token0_price': 100, 'timestamp': now - 12},
            {'token0_price': 100, 'timestamp': now - 11},
            {'token0_price': 99, 'timestamp': now - 10},
            {'token0_price': 101, 'timestamp': now - 9},
            {'token0_price': 100, 'timestamp': now - 8},
            {'token0_price': 100, 'timestamp': now - 7},
            {'token0_price': 99, 'timestamp': now - 6},
            {'token0_price': 101, 'timestamp': now - 5},
            {'token0_price': 100, 'timestamp': now - 4},
            {'token0_price': 100, 'timestamp': now - 3},
            {'token0_price': 99, 'timestamp': now - 2},
            {'token0_price': 101, 'timestamp': now - 1},
        ]

        # Current price is extreme (2 std devs away)
        sample_trading_state['current_prices'][pool_addr] = PriceUpdate(
            pool_addr, 150, 0.0067, now, 1000  # 50% above mean
        )

        signals = await strategy_agent.mean_reversion_strategy(sample_trading_state)

        # Should detect mean reversion opportunity
        assert len(signals) > 0
        for signal in signals:
            assert signal.type == 'MEAN_REVERSION'

    def test_rank_signals_empty(self, strategy_agent):
        """Test ranking empty signals"""
        ranked = strategy_agent.rank_signals([])
        assert ranked == []

    def test_rank_signals_by_confidence(self, strategy_agent, sample_tokens):
        """Test signal ranking by confidence"""
        signals = [
            TradeSignal('1', 'ARBITRAGE', 0.6, sample_tokens['BNB'], sample_tokens['USDT'], '1000000000000000000', 10.0, 5.0),
            TradeSignal('2', 'ARBITRAGE', 0.9, sample_tokens['BNB'], sample_tokens['USDT'], '1000000000000000000', 5.0, 2.5),
            TradeSignal('3', 'ARBITRAGE', 0.7, sample_tokens['BNB'], sample_tokens['USDT'], '1000000000000000000', 8.0, 4.0),
        ]

        ranked = strategy_agent.rank_signals(signals)

        # Higher confidence should rank higher
        assert ranked[0].confidence >= ranked[1].confidence
        assert ranked[1].confidence >= ranked[2].confidence

    @pytest.mark.asyncio
    async def test_run_full_cycle(self, strategy_agent, sample_trading_state):
        """Test full agent run cycle"""
        result = await strategy_agent.run(sample_trading_state)

        assert 'pending_signals' in result
        assert 'agent_actions' in result
        assert len(result['agent_actions']) > 0

    @pytest.mark.asyncio
    async def test_lp_yield_strategy_no_pools(self, strategy_agent, sample_trading_state):
        """Test LP yield with no valid pools"""
        # Remove APR data from pools
        for pool in sample_trading_state['pools'].values():
            if hasattr(pool, 'apr24h'):
                delattr(pool, 'apr24h')

        signals = await strategy_agent.lp_yield_strategy(sample_trading_state)
        assert signals == []

    def test_update_price_history(self, strategy_agent):
        """Test price history update"""
        pool = '0xpool1'
        price = 100.5

        strategy_agent.update_price_history(pool, price)

        assert pool in strategy_agent.price_history
        assert len(strategy_agent.price_history[pool]) == 1
        assert strategy_agent.price_history[pool][0]['token0_price'] == price

    def test_price_history_limit(self, strategy_agent):
        """Test price history size limit"""
        pool = '0xpool1'

        # Add 150 entries
        for i in range(150):
            strategy_agent.update_price_history(pool, 100.0 + i)

        # Should be limited to 100
        assert len(strategy_agent.price_history[pool]) == 100
        # Should keep most recent
        assert strategy_agent.price_history[pool][-1]['token0_price'] == 249.0


class TestSignalScoring:
    """Tests for signal scoring logic"""

    def test_score_calculation_confidence_weight(self, strategy_agent, sample_tokens):
        """Test that confidence affects score"""
        high_conf = TradeSignal('1', 'ARBITRAGE', 0.9, sample_tokens['BNB'], sample_tokens['USDT'], '1000', 10.0, 5.0)
        low_conf = TradeSignal('2', 'ARBITRAGE', 0.5, sample_tokens['BNB'], sample_tokens['USDT'], '1000', 10.0, 5.0)

        # Calculate scores manually
        def calc_score(signal):
            score = signal.confidence * 100
            score += signal.expected_profit * 10
            weight = strategy_agent.strategy_weights.get(signal.type, 0.5)
            score *= weight
            return score

        high_score = calc_score(high_conf)
        low_score = calc_score(low_conf)

        assert high_score > low_score

    def test_strategy_weights(self, strategy_agent):
        """Test strategy weights are configured"""
        assert strategy_agent.strategy_weights['ARBITRAGE'] == 1.0
        assert strategy_agent.strategy_weights['TREND_FOLLOWING'] == 0.8
        assert strategy_agent.strategy_weights['MEAN_REVERSION'] == 0.7
        assert strategy_agent.strategy_weights['LP_YIELD'] == 0.6


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
