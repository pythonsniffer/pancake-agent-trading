"""
Test suite for Risk Management Agent

Tests:
- Signal validation
- Risk score calculation
- Circuit breaker logic
- Daily loss tracking
- Portfolio risk checks
"""

import pytest
import asyncio
from unittest.mock import Mock
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.agents.risk_management import RiskManagementAgent, RiskConfig
from src.state import TradingState, TradeSignal, RiskAssessment, TokenInfo


@pytest.fixture
def risk_agent():
    """Create a Risk Management Agent"""
    return RiskManagementAgent(config={
        'max_position_size_usd': 500.0,
        'max_portfolio_exposure_percent': 20.0,
        'max_daily_loss_usd': 100.0,
        'max_drawdown_percent': 10.0,
        'stop_loss_percent': 5.0,
        'take_profit_percent': 10.0,
        'max_slippage_percent': 1.0,
        'max_gas_price_gwei': 50,
        'min_profit_threshold_usd': 1.0,
        'circuit_breaker_enabled': True,
        'circuit_breaker_threshold': 5.0
    })


@pytest.fixture
def sample_token():
    """Create a sample token"""
    return TokenInfo('0xtoken', 'BNB', 18, 300.0)


@pytest.fixture
def sample_signal(sample_token):
    """Create a sample trade signal"""
    return TradeSignal(
        id='signal1',
        type='ARBITRAGE',
        confidence=0.85,
        token_in=sample_token,
        token_out=TokenInfo('0xtoken2', 'USDT', 18, 1.0),
        amount_in='1000000000000000000',
        expected_profit=50.0,
        expected_profit_percent=5.0,
        metadata={
            'estimated_gas': 3.0,
            'slippage': 0.3
        }
    )


@pytest.fixture
def sample_trading_state():
    """Create a sample trading state"""
    return {
        'status': 'RUNNING',
        'circuit_breaker_triggered': False,
        'current_prices': {},
        'pools': {},
        'market_regime': 'SIDEWAYS',
        'pending_signals': [],
        'validated_signals': [],
        'risk_assessments': [],
        'executed_trades': [],
        'portfolio_value': 10000.0,
        'available_balance': 8000.0,
        'positions': [],
        'agent_actions': [],
        'vector_memory_ids': [],
        'config': {'initial_portfolio_value': 10000.0},
        'messages': [],
    }


class TestRiskManagementAgent:
    """Test cases for Risk Management Agent"""

    def test_initialization(self, risk_agent):
        """Test agent initialization"""
        assert risk_agent.config.max_position_size_usd == 500.0
        assert risk_agent.config.max_daily_loss_usd == 100.0
        assert risk_agent.config.circuit_breaker_enabled is True
        assert risk_agent.circuit_breaker_triggered is False

    @pytest.mark.asyncio
    async def test_validate_safe_signal(self, risk_agent, sample_signal, sample_trading_state):
        """Test validation of a safe signal"""
        assessment = await risk_agent.validate_signal(sample_signal, sample_trading_state)

        assert isinstance(assessment, RiskAssessment)
        assert assessment.approved is True
        assert assessment.signal_id == sample_signal.id

    @pytest.mark.asyncio
    async def test_validate_low_confidence(self, risk_agent, sample_signal, sample_trading_state):
        """Test rejection of low confidence signal"""
        sample_signal.confidence = 0.4  # Below threshold

        assessment = await risk_agent.validate_signal(sample_signal, sample_trading_state)

        assert assessment.approved is False
        assert 'confidence' in assessment.rejection_reason.lower()

    @pytest.mark.asyncio
    async def test_validate_excessive_position_size(self, risk_agent, sample_signal, sample_trading_state):
        """Test rejection due to position size"""
        sample_signal.amount_in = '10000000000000000000'  # 10 tokens at $300 = $3000

        assessment = await risk_agent.validate_signal(sample_signal, sample_trading_state)

        assert assessment.approved is False
        assert 'size' in assessment.rejection_reason.lower()

    @pytest.mark.asyncio
    async def test_validate_insufficient_profit(self, risk_agent, sample_signal, sample_trading_state):
        """Test rejection due to insufficient expected profit"""
        sample_signal.expected_profit = 0.5  # Below $1 threshold

        assessment = await risk_agent.validate_signal(sample_signal, sample_trading_state)

        assert assessment.approved is False
        assert 'profit' in assessment.rejection_reason.lower()

    @pytest.mark.asyncio
    async def test_validate_high_gas_ratio(self, risk_agent, sample_signal, sample_trading_state):
        """Test rejection when gas is too high relative to profit"""
        sample_signal.expected_profit = 5.0
        sample_signal.metadata['estimated_gas'] = 3.0  # 60% of profit

        assessment = await risk_agent.validate_signal(sample_signal, sample_trading_state)

        assert assessment.approved is False
        assert 'gas' in assessment.rejection_reason.lower()

    @pytest.mark.asyncio
    async def test_validate_volatile_market(self, risk_agent, sample_signal, sample_trading_state):
        """Test extra scrutiny in volatile markets"""
        sample_trading_state['market_regime'] = 'VOLATILE'
        sample_signal.confidence = 0.7  # Below 0.8 required for volatile

        assessment = await risk_agent.validate_signal(sample_signal, sample_trading_state)

        assert assessment.approved is False
        assert 'volatile' in assessment.rejection_reason.lower()

    @pytest.mark.asyncio
    async def test_validate_daily_loss_limit(self, risk_agent, sample_signal, sample_trading_state):
        """Test rejection when daily loss limit reached"""
        risk_agent.daily_loss = 100.0  # At limit

        assessment = await risk_agent.validate_signal(sample_signal, sample_trading_state)

        assert assessment.approved is False
        assert 'daily loss' in assessment.rejection_reason.lower()

    def test_risk_level_calculation(self, risk_agent):
        """Test risk level calculation from score"""
        assert risk_agent._get_risk_level(10) == 'LOW'
        assert risk_agent._get_risk_level(30) == 'MEDIUM'
        assert risk_agent._get_risk_level(60) == 'HIGH'
        assert risk_agent._get_risk_level(90) == 'CRITICAL'

    def test_circuit_breaker_trigger(self, risk_agent):
        """Test circuit breaker triggering"""
        assert risk_agent.circuit_breaker_triggered is False

        risk_agent._trigger_circuit_breaker("Test trigger")

        assert risk_agent.circuit_breaker_triggered is True
        assert risk_agent.circuit_breaker_reason == "Test trigger"
        assert risk_agent.circuit_breaker_time is not None

    def test_circuit_breaker_reset_after_cooldown(self, risk_agent):
        """Test circuit breaker reset after cooldown"""
        risk_agent._trigger_circuit_breaker("Test trigger")
        risk_agent.circuit_breaker_time = datetime.now() - timedelta(hours=2)

        risk_agent.reset_circuit_breaker()

        assert risk_agent.circuit_breaker_triggered is False
        assert risk_agent.circuit_breaker_reason is None

    def test_circuit_breaker_no_reset_during_cooldown(self, risk_agent):
        """Test circuit breaker won't reset during cooldown"""
        risk_agent._trigger_circuit_breaker("Test trigger")

        risk_agent.reset_circuit_breaker()

        # Should still be triggered (only 0 time passed)
        assert risk_agent.circuit_breaker_triggered is True

    @pytest.mark.asyncio
    async def test_run_with_circuit_breaker(self, risk_agent, sample_trading_state):
        """Test that circuit breaker stops processing"""
        risk_agent._trigger_circuit_breaker("Test trigger")

        result = await risk_agent.run(sample_trading_state)

        assert result['circuit_breaker_triggered'] is True
        assert result['status'] == 'PAUSED'

    @pytest.mark.asyncio
    async def test_run_validates_pending_signals(self, risk_agent, sample_trading_state, sample_signal):
        """Test that pending signals are validated"""
        sample_trading_state['pending_signals'] = [sample_signal]

        result = await risk_agent.run(sample_trading_state)

        assert 'validated_signals' in result
        assert 'risk_assessments' in result
        assert len(result['risk_assessments']) == 1

    def test_daily_counters_reset(self, risk_agent):
        """Test daily counters reset after new day"""
        risk_agent.daily_loss = 50.0
        risk_agent.daily_trades = 5
        risk_agent.last_reset = datetime.now() - timedelta(days=1)

        risk_agent._reset_daily_counters()

        assert risk_agent.daily_loss == 0.0
        assert risk_agent.daily_trades == 0

    def test_update_daily_loss(self, risk_agent):
        """Test daily loss tracking"""
        risk_agent.update_daily_loss(25.0)

        assert risk_agent.daily_loss == 25.0
        assert risk_agent.daily_trades == 1

        risk_agent.update_daily_loss(-30.0)  # Negative gets converted to positive

        assert risk_agent.daily_loss == 55.0
        assert risk_agent.daily_trades == 2

    def test_get_risk_metrics(self, risk_agent):
        """Test risk metrics reporting"""
        risk_agent.daily_loss = 50.0
        risk_agent.daily_trades = 3
        risk_agent._trigger_circuit_breaker("Test")

        metrics = risk_agent.get_risk_metrics()

        assert metrics['daily_loss'] == 50.0
        assert metrics['daily_trades'] == 3
        assert metrics['circuit_breaker_triggered'] is True


class TestPortfolioRiskChecks:
    """Tests for portfolio-level risk checks"""

    @pytest.mark.asyncio
    async def test_drawdown_circuit_breaker(self, risk_agent, sample_trading_state):
        """Test circuit breaker triggers on drawdown"""
        sample_trading_state['portfolio_value'] = 9400.0  # 6% drawdown

        await risk_agent.check_portfolio_risk(sample_trading_state)

        assert risk_agent.circuit_breaker_triggered is True
        assert 'drawdown' in risk_agent.circuit_breaker_reason.lower()

    @pytest.mark.asyncio
    async def test_consecutive_losses_circuit_breaker(self, risk_agent, sample_trading_state):
        """Test circuit breaker on consecutive losses"""
        from src.state import TradeExecution

        # Add 3 recent losses
        now = datetime.now()
        sample_trading_state['executed_trades'] = [
            TradeExecution('1', 'SUCCESS', actual_profit=-10, timestamp=int(now.timestamp())),
            TradeExecution('2', 'SUCCESS', actual_profit=-15, timestamp=int((now - timedelta(minutes=20)).timestamp())),
            TradeExecution('3', 'SUCCESS', actual_profit=-20, timestamp=int((now - timedelta(minutes=40)).timestamp())),
        ]

        await risk_agent.check_portfolio_risk(sample_trading_state)

        assert risk_agent.circuit_breaker_triggered is True
        assert 'losses' in risk_agent.circuit_breaker_reason.lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
