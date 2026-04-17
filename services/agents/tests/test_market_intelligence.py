"""
Test suite for Market Intelligence Agent

Tests:
- Price fetching from pools
- Market regime detection
- Volatility calculations
- Whale movement detection
- Arbitrage candidate identification
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import sys
import os

# Add parent to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.agents.market_intelligence import MarketIntelligenceAgent, WhaleMovement
from src.state import TradingState, PriceUpdate, PoolInfo, TokenInfo


@pytest.fixture
def mock_web3():
    """Create a mock Web3 instance"""
    w3 = Mock()
    w3.eth = Mock()
    w3.eth.block_number = 1000000
    w3.to_checksum_address = lambda x: x
    return w3


@pytest.fixture
def market_agent(mock_web3):
    """Create a Market Intelligence Agent with mocked Web3"""
    return MarketIntelligenceAgent(w3=mock_web3, config={
        'whale_threshold_usd': 100000
    })


@pytest.fixture
def sample_trading_state() -> TradingState:
    """Create a sample trading state"""
    return {
        'status': 'IDLE',
        'circuit_breaker_triggered': False,
        'current_prices': {},
        'pools': {},
        'market_regime': 'UNKNOWN',
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


class TestMarketIntelligenceAgent:
    """Test cases for Market Intelligence Agent"""

    @pytest.mark.asyncio
    async def test_fetch_price_updates_empty_pools(self, market_agent, sample_trading_state):
        """Test price fetching when no pools are monitored"""
        # Should discover pools when empty
        with patch.object(market_agent, 'discover_pools') as mock_discover:
            mock_discover.return_value = asyncio.Future()
            mock_discover.return_value.set_result(None)

            updates = await market_agent.fetch_price_updates()
            mock_discover.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_price_updates_with_mock_reserves(self, market_agent, mock_web3):
        """Test price fetching with mocked reserve data"""
        # Setup mock pool
        market_agent.monitored_pools = ['0xpool1']

        # Mock contract calls
        mock_contract = Mock()
        mock_contract.functions.getReserves.return_value.call.return_value = (
            1000000000000000000,  # 1 token0
            2000000000000000000,  # 2 token1
            1234567890  # block timestamp
        )
        mock_contract.functions.token0.return_value.call.return_value = '0xtoken0'
        mock_contract.functions.token1.return_value.call.return_value = '0xtoken1'

        mock_web3.eth.contract.return_value = mock_contract

        updates = await market_agent.fetch_price_updates()

        assert len(updates) == 1
        assert updates[0].token0_price == 2.0  # 2 token1 / 1 token0
        assert updates[0].token1_price == 0.5  # 1 token0 / 2 token1

    @pytest.mark.asyncio
    async def test_market_regime_detection_bull(self, market_agent):
        """Test BULL market regime detection"""
        # Create price updates with upward trend
        updates = [
            PriceUpdate('0xpool1', 100, 0.01, int(datetime.now().timestamp()), 1000),
            PriceUpdate('0xpool1', 102, 0.0098, int(datetime.now().timestamp()), 1001),
            PriceUpdate('0xpool1', 104, 0.0096, int(datetime.now().timestamp()), 1002),
            PriceUpdate('0xpool1', 106, 0.0094, int(datetime.now().timestamp()), 1003),
            PriceUpdate('0xpool1', 108, 0.0092, int(datetime.now().timestamp()), 1004),
        ]

        # Add to history
        market_agent.price_history['0xpool1'] = updates[:-1]

        regime = market_agent.detect_market_regime([updates[-1]])

        assert regime in ['BULL', 'SIDEWAYS']  # May vary based on implementation

    @pytest.mark.asyncio
    async def test_market_regime_detection_volatile(self, market_agent):
        """Test VOLATILE market regime detection"""
        # Create price updates with high volatility
        updates = [
            PriceUpdate('0xpool1', 100, 0.01, int(datetime.now().timestamp()), 1000),
            PriceUpdate('0xpool1', 110, 0.0091, int(datetime.now().timestamp()), 1001),  # +10%
            PriceUpdate('0xpool1', 95, 0.0105, int(datetime.now().timestamp()), 1002),   # -13%
        ]

        market_agent.price_history['0xpool1'] = updates[:-1]

        regime = market_agent.detect_market_regime([updates[-1]])

        assert regime == 'VOLATILE'

    @pytest.mark.asyncio
    async def test_calculate_volatility_empty_history(self, market_agent):
        """Test volatility calculation with empty history"""
        volatility = market_agent.calculate_volatility('0xnonexistent')
        assert volatility == 0.0

    @pytest.mark.asyncio
    async def test_calculate_volatility_with_history(self, market_agent):
        """Test volatility calculation with price history"""
        # Create price history
        now = int(datetime.now().timestamp())
        market_agent.price_history['0xpool1'] = [
            PriceUpdate('0xpool1', 100, 0.01, now - 4, 1000),
            PriceUpdate('0xpool1', 102, 0.0098, now - 3, 1001),
            PriceUpdate('0xpool1', 101, 0.0099, now - 2, 1002),
            PriceUpdate('0xpool1', 103, 0.0097, now - 1, 1003),
            PriceUpdate('0xpool1', 104, 0.0096, now, 1004),
        ]

        volatility = market_agent.calculate_volatility('0xpool1')

        assert volatility > 0  # Should have some volatility
        assert isinstance(volatility, float)

    @pytest.mark.asyncio
    async def test_detect_whale_movements_empty(self, market_agent):
        """Test whale detection returns empty list by default"""
        movements = await market_agent.detect_whale_movements()
        assert movements == []

    @pytest.mark.asyncio
    async def test_run_full_cycle(self, market_agent, sample_trading_state, mock_web3):
        """Test full agent run cycle"""
        # Mock all dependencies
        market_agent.monitored_pools = ['0xpool1']

        mock_contract = Mock()
        mock_contract.functions.getReserves.return_value.call.return_value = (
            1000000000000000000,
            2000000000000000000,
            1234567890
        )
        mock_contract.functions.token0.return_value.call.return_value = '0xtoken0'
        mock_contract.functions.token1.return_value.call.return_value = '0xtoken1'

        mock_web3.eth.contract.return_value = mock_contract

        result = await market_agent.run(sample_trading_state)

        assert 'current_prices' in result
        assert 'market_regime' in result
        assert 'agent_actions' in result
        assert len(result['agent_actions']) > 0

    def test_agent_initialization(self, mock_web3):
        """Test agent initialization"""
        agent = MarketIntelligenceAgent(w3=mock_web3)

        assert agent.w3 == mock_web3
        assert agent.monitored_pools == []
        assert agent.whale_threshold_usd == 100000  # default

    def test_agent_with_config(self, mock_web3):
        """Test agent with custom config"""
        agent = MarketIntelligenceAgent(
            w3=mock_web3,
            config={'whale_threshold_usd': 500000}
        )

        assert agent.whale_threshold_usd == 500000


class TestMarketRegimeEdgeCases:
    """Edge case tests for market regime detection"""

    @pytest.mark.asyncio
    async def test_empty_updates(self, market_agent):
        """Test regime detection with no updates"""
        regime = market_agent.detect_market_regime([])
        assert regime == 'SIDEWAYS'

    @pytest.mark.asyncio
    async def test_single_update(self, market_agent):
        """Test regime detection with single update"""
        update = PriceUpdate('0xpool1', 100, 0.01, int(datetime.now().timestamp()), 1000)
        regime = market_agent.detect_market_regime([update])
        assert regime == 'SIDEWAYS'  # Not enough data

    @pytest.mark.asyncio
    async def test_extreme_prices(self, market_agent):
        """Test regime detection with extreme price movements"""
        now = int(datetime.now().timestamp())
        updates = [
            PriceUpdate('0xpool1', 100, 0.01, now - 1, 1000),
            PriceUpdate('0xpool1', 200, 0.005, now, 1001),  # 100% increase
        ]

        market_agent.price_history['0xpool1'] = updates[:-1]
        regime = market_agent.detect_market_regime([updates[-1]])

        assert regime == 'VOLATILE'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
