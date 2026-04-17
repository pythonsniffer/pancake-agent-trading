import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

from ..state import TradingState, TradeSignal, RiskAssessment, AgentAction

logger = logging.getLogger(__name__)


@dataclass
class RiskConfig:
    max_position_size_usd: float = 500.0
    max_portfolio_exposure_percent: float = 20.0
    max_daily_loss_usd: float = 100.0
    max_drawdown_percent: float = 10.0
    stop_loss_percent: float = 5.0
    take_profit_percent: float = 10.0
    max_slippage_percent: float = 1.0
    max_gas_price_gwei: int = 50
    min_profit_threshold_usd: float = 1.0
    circuit_breaker_enabled: bool = True
    circuit_breaker_threshold: float = 5.0  # 5% drawdown triggers halt


class RiskManagementAgent:
    """
    Risk Management Agent: Validates trade signals, enforces risk limits,
    implements circuit breakers, and protects the portfolio from excessive losses.
    """

    def __init__(self, config: Dict = None):
        self.config = RiskConfig(**(config or {}))
        self.daily_loss = 0.0
        self.daily_trades = 0
        self.last_reset = datetime.now()
        self.circuit_breaker_triggered = False
        self.circuit_breaker_reason = None
        self.circuit_breaker_time = None

    async def run(self, state: TradingState) -> TradingState:
        """Main entry point for the agent"""
        logger.info("Risk Management Agent running...")

        try:
            # Reset daily counters if needed
            self._reset_daily_counters()

            # Check circuit breaker
            if self.circuit_breaker_triggered:
                state['circuit_breaker_triggered'] = True
                state['status'] = 'PAUSED'
                logger.warning(f"Circuit breaker active: {self.circuit_breaker_reason}")
                return state

            # Validate pending signals
            pending_signals = state.get('pending_signals', [])
            validated_signals = []
            assessments = []

            for signal in pending_signals:
                assessment = await self.validate_signal(signal, state)
                assessments.append(assessment)

                if assessment.approved:
                    validated_signals.append(signal)
                    logger.info(f"Signal {signal.id} approved (risk score: {assessment.risk_score})")
                else:
                    logger.warning(f"Signal {signal.id} rejected: {assessment.rejection_reason}")

            # Update state
            state['validated_signals'] = validated_signals
            state['risk_assessments'] = assessments

            # Check portfolio-level risk
            await self.check_portfolio_risk(state)

            # Create agent action
            action = AgentAction(
                agent_name="RiskManagementAgent",
                action="validate_signals",
                input_data={"pending_signals": len(pending_signals)},
                output_data={
                    "approved": len(validated_signals),
                    "rejected": len(pending_signals) - len(validated_signals),
                    "circuit_breaker": self.circuit_breaker_triggered,
                },
                confidence=0.95,
                timestamp=int(datetime.now().timestamp()),
                duration_ms=50,
            )
            state['agent_actions'].append(action)

        except Exception as e:
            logger.error(f"Error in Risk Management Agent: {e}", exc_info=True)
            state['status'] = 'ERROR'

        return state

    async def validate_signal(self, signal: TradeSignal, state: TradingState) -> RiskAssessment:
        """Validate a trade signal against risk parameters"""
        checks = []
        approved = True
        risk_score = 0.0
        rejection_reason = None

        # Check 1: Minimum profit threshold
        if signal.expected_profit < self.config.min_profit_threshold_usd:
            checks.append({
                "name": "min_profit",
                "passed": False,
                "message": f"Expected profit (${signal.expected_profit:.2f}) below threshold (${self.config.min_profit_threshold_usd:.2f})"
            })
            approved = False
            rejection_reason = f"Insufficient expected profit: ${signal.expected_profit:.2f}"
            risk_score += 30
        else:
            checks.append({"name": "min_profit", "passed": True})

        # Check 2: Position size limit
        amount_in_usd = float(signal.amount_in) / (10 ** signal.token_in.decimals) * signal.token_in.price_usd
        if amount_in_usd > self.config.max_position_size_usd:
            checks.append({
                "name": "position_size",
                "passed": False,
                "message": f"Position size (${amount_in_usd:.2f}) exceeds max (${self.config.max_position_size_usd:.2f})"
            })
            approved = False
            rejection_reason = f"Position size too large: ${amount_in_usd:.2f}"
            risk_score += 40
        else:
            checks.append({"name": "position_size", "passed": True})

        # Check 3: Daily loss limit
        if self.daily_loss >= self.config.max_daily_loss_usd:
            checks.append({
                "name": "daily_loss",
                "passed": False,
                "message": f"Daily loss limit (${self.config.max_daily_loss_usd:.2f}) reached"
            })
            approved = False
            rejection_reason = "Daily loss limit reached"
            risk_score += 100
        else:
            checks.append({"name": "daily_loss", "passed": True})

        # Check 4: Portfolio exposure
        portfolio_value = state.get('portfolio_value', 0)
        if portfolio_value > 0:
            exposure_percent = (amount_in_usd / portfolio_value) * 100
            if exposure_percent > self.config.max_portfolio_exposure_percent:
                checks.append({
                    "name": "portfolio_exposure",
                    "passed": False,
                    "message": f"Exposure ({exposure_percent:.1f}%) exceeds max ({self.config.max_portfolio_exposure_percent:.1f}%)"
                })
                approved = False
                rejection_reason = f"Portfolio exposure too high: {exposure_percent:.1f}%"
                risk_score += 25
            else:
                checks.append({"name": "portfolio_exposure", "passed": True})

        # Check 5: Signal confidence
        if signal.confidence < 0.6:
            checks.append({
                "name": "signal_confidence",
                "passed": False,
                "message": f"Confidence ({signal.confidence:.2f}) too low"
            })
            approved = False
            rejection_reason = f"Low signal confidence: {signal.confidence:.2f}"
            risk_score += 20
        else:
            checks.append({"name": "signal_confidence", "passed": True})

        # Check 6: Gas price estimation
        estimated_gas = signal.metadata.get('estimated_gas', 0)
        if estimated_gas > signal.expected_profit * 0.5:  # Gas is >50% of profit
            checks.append({
                "name": "gas_cost_ratio",
                "passed": False,
                "message": f"Gas cost (${estimated_gas:.2f}) too high relative to profit (${signal.expected_profit:.2f})"
            })
            approved = False
            rejection_reason = "Gas cost too high relative to expected profit"
            risk_score += 15
        else:
            checks.append({"name": "gas_cost_ratio", "passed": True})

        # Check 7: Slippage tolerance
        if signal.metadata.get('slippage', 0) > self.config.max_slippage_percent:
            checks.append({
                "name": "slippage",
                "passed": False,
                "message": f"Slippage ({signal.metadata.get('slippage', 0):.2f}%) exceeds max ({self.config.max_slippage_percent:.2f}%)"
            })
            approved = False
            rejection_reason = "Slippage too high"
            risk_score += 25
        else:
            checks.append({"name": "slippage", "passed": True})

        # Check 8: Market regime
        market_regime = state.get('market_regime', 'UNKNOWN')
        if market_regime == 'VOLATILE':
            # Extra scrutiny in volatile markets
            if signal.confidence < 0.8:
                checks.append({
                    "name": "market_regime",
                    "passed": False,
                    "message": "Signal confidence too low for volatile market"
                })
                approved = False
                rejection_reason = "Volatile market - higher confidence required"
                risk_score += 10
            else:
                checks.append({"name": "market_regime", "passed": True})
        else:
            checks.append({"name": "market_regime", "passed": True})

        # Determine risk level
        risk_level = self._get_risk_level(risk_score)

        return RiskAssessment(
            signal_id=signal.id,
            approved=approved,
            risk_score=risk_score,
            risk_level=risk_level,
            checks=checks,
            rejection_reason=rejection_reason
        )

    async def check_portfolio_risk(self, state: TradingState) -> None:
        """Check portfolio-level risk metrics and trigger circuit breaker if needed"""
        if not self.config.circuit_breaker_enabled:
            return

        portfolio_value = state.get('portfolio_value', 0)
        positions = state.get('positions', [])

        # Calculate drawdown
        initial_value = state.get('config', {}).get('initial_portfolio_value', portfolio_value)
        if initial_value > 0 and portfolio_value > 0:
            drawdown = (initial_value - portfolio_value) / initial_value * 100

            if drawdown >= self.config.circuit_breaker_threshold:
                self._trigger_circuit_breaker(
                    f"Portfolio drawdown ({drawdown:.2f}%) exceeded threshold ({self.config.circuit_breaker_threshold:.2f}%)"
                )
                return

        # Check for flash crash indicators
        executed_trades = state.get('executed_trades', [])
        recent_losses = [
            t for t in executed_trades
            if t.actual_profit < 0
            and datetime.fromtimestamp(t.timestamp) > datetime.now() - timedelta(hours=1)
        ]

        if len(recent_losses) >= 3:
            self._trigger_circuit_breaker(
                f"Multiple consecutive losses detected: {len(recent_losses)} in last hour"
            )
            return

        # Check for abnormal volatility
        market_regime = state.get('market_regime', 'UNKNOWN')
        if market_regime == 'VOLATILE':
            # Reduce position sizes in volatile markets
            logger.info("Volatile market detected - reducing position sizes")

    def _get_risk_level(self, risk_score: float) -> str:
        """Convert risk score to risk level"""
        if risk_score >= 80:
            return "CRITICAL"
        elif risk_score >= 50:
            return "HIGH"
        elif risk_score >= 25:
            return "MEDIUM"
        else:
            return "LOW"

    def _trigger_circuit_breaker(self, reason: str) -> None:
        """Trigger circuit breaker to halt trading"""
        self.circuit_breaker_triggered = True
        self.circuit_breaker_reason = reason
        self.circuit_breaker_time = datetime.now()
        logger.critical(f"CIRCUIT BREAKER TRIGGERED: {reason}")

    def reset_circuit_breaker(self) -> None:
        """Reset circuit breaker after cooling off period"""
        if self.circuit_breaker_time:
            elapsed = (datetime.now() - self.circuit_breaker_time).total_seconds()
            if elapsed > 3600:  # 1 hour cooldown
                self.circuit_breaker_triggered = False
                self.circuit_breaker_reason = None
                self.circuit_breaker_time = None
                logger.info("Circuit breaker reset")

    def _reset_daily_counters(self) -> None:
        """Reset daily counters if new day"""
        if (datetime.now() - self.last_reset).days >= 1:
            self.daily_loss = 0.0
            self.daily_trades = 0
            self.last_reset = datetime.now()
            logger.info("Daily counters reset")

    def update_daily_loss(self, loss: float) -> None:
        """Update daily loss tracking"""
        self.daily_loss += abs(loss)
        self.daily_trades += 1

    def get_risk_metrics(self) -> Dict[str, Any]:
        """Get current risk metrics"""
        return {
            "daily_loss": self.daily_loss,
            "daily_trades": self.daily_trades,
            "circuit_breaker_triggered": self.circuit_breaker_triggered,
            "circuit_breaker_reason": self.circuit_breaker_reason,
            "config": {
                "max_daily_loss": self.config.max_daily_loss_usd,
                "max_drawdown": self.config.max_drawdown_percent,
                "circuit_breaker_enabled": self.config.circuit_breaker_enabled,
            }
        }
