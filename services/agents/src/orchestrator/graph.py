import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from langgraph.graph import StateGraph, END

from ..state import TradingState, AgentAction
from ..agents.market_intelligence import MarketIntelligenceAgent
from ..agents.strategy import StrategyAgent
from ..agents.risk_management import RiskManagementAgent
from ..agents.execution import ExecutionAgent
from ..agents.portfolio import PortfolioAgent
from ..agents.liquidity import LiquidityAnalysisAgent
from ..agents.backtest import BacktestAgent

logger = logging.getLogger(__name__)


class TradingOrchestrator:
    """
    Trading Orchestrator: Manages the state machine using LangGraph
    to coordinate all agents in the trading system.
    """

    def __init__(self, w3=None, config: Dict = None):
        self.config = config or {}
        self.w3 = w3

        # Initialize agents
        self.agents = {
            'market_intelligence': MarketIntelligenceAgent(w3=w3, config=config.get('market')),
            'strategy': StrategyAgent(config=config.get('strategy')),
            'risk_management': RiskManagementAgent(config=config.get('risk')),
            'execution': ExecutionAgent(w3=w3, private_key=config.get('private_key'), config=config.get('execution')),
            'portfolio': PortfolioAgent(w3=w3, config=config.get('portfolio')),
            'liquidity': LiquidityAnalysisAgent(w3=w3, config=config.get('liquidity')),
            'backtest': BacktestAgent(config=config.get('backtest')),
        }

        # Build the state graph
        self.graph = self._build_graph()

        # State management
        self.state: Optional[TradingState] = None
        self.is_running = False

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state graph"""

        # Define nodes
        def market_node(state: TradingState) -> TradingState:
            """Market Intelligence Agent node"""
            return asyncio.run(self.agents['market_intelligence'].run(state))

        def liquidity_node(state: TradingState) -> TradingState:
            """Liquidity Analysis Agent node"""
            return asyncio.run(self.agents['liquidity'].run(state))

        def strategy_node(state: TradingState) -> TradingState:
            """Strategy Agent node"""
            return asyncio.run(self.agents['strategy'].run(state))

        def risk_node(state: TradingState) -> TradingState:
            """Risk Management Agent node"""
            return asyncio.run(self.agents['risk_management'].run(state))

        def execution_node(state: TradingState) -> TradingState:
            """Execution Agent node"""
            return asyncio.run(self.agents['execution'].run(state))

        def portfolio_node(state: TradingState) -> TradingState:
            """Portfolio Agent node"""
            return asyncio.run(self.agents['portfolio'].run(state))

        def backtest_node(state: TradingState) -> TradingState:
            """Backtest Agent node"""
            return asyncio.run(self.agents['backtest'].run(state))

        # Create workflow
        workflow = StateGraph(TradingState)

        # Add nodes
        workflow.add_node("market", market_node)
        workflow.add_node("liquidity", liquidity_node)
        workflow.add_node("strategy", strategy_node)
        workflow.add_node("risk", risk_node)
        workflow.add_node("execution", execution_node)
        workflow.add_node("portfolio", portfolio_node)
        workflow.add_node("backtest", backtest_node)

        # Define edges
        # Market intelligence runs first
        workflow.set_entry_point("market")

        # Market → Liquidity (parallel)
        workflow.add_edge("market", "liquidity")

        # Liquidity → Strategy
        workflow.add_edge("liquidity", "strategy")

        # Strategy → Risk
        workflow.add_edge("strategy", "risk")

        # Risk → Conditional (Execution or End)
        def risk_router(state: TradingState) -> str:
            """Route based on risk validation"""
            if not state.get('validated_signals'):
                return "portfolio"
            if state.get('circuit_breaker_triggered'):
                return "portfolio"
            return "execution"

        workflow.add_conditional_edges(
            "risk",
            risk_router,
            {
                "execution": "execution",
                "portfolio": "portfolio"
            }
        )

        # Execution → Portfolio
        workflow.add_edge("execution", "portfolio")

        # Portfolio → End
        workflow.add_edge("portfolio", END)

        # Backtest can be run independently
        workflow.add_edge("backtest", END)

        return workflow.compile()

    async def initialize(self) -> None:
        """Initialize the trading system state"""
        self.state = {
            'status': 'IDLE',
            'circuit_breaker_triggered': False,
            'current_prices': {},
            'pools': {},
            'market_regime': 'UNKNOWN',
            'pending_signals': [],
            'validated_signals': [],
            'risk_assessments': [],
            'executed_trades': [],
            'portfolio_value': self.config.get('initial_capital', 10000.0),
            'available_balance': self.config.get('initial_capital', 10000.0),
            'positions': [],
            'agent_actions': [],
            'vector_memory_ids': [],
            'config': self.config,
            'messages': [],
        }
        logger.info("Trading state initialized")

    async def run_cycle(self) -> TradingState:
        """Run one complete trading cycle through the graph"""
        if not self.state:
            await self.initialize()

        if self.state.get('circuit_breaker_triggered'):
            logger.warning("Circuit breaker active - skipping cycle")
            return self.state

        try:
            # Execute the graph
            result = self.graph.invoke(self.state)
            self.state = result

            logger.info(f"Trading cycle complete: {len(self.state.get('executed_trades', []))} trades executed")

            return self.state

        except Exception as e:
            logger.error(f"Error in trading cycle: {e}", exc_info=True)
            self.state['status'] = 'ERROR'
            return self.state

    async def run_continuous(self, interval_seconds: int = 60) -> None:
        """Run trading cycles continuously"""
        self.is_running = True
        self.state['status'] = 'RUNNING'

        logger.info(f"Starting continuous trading with {interval_seconds}s interval")

        while self.is_running:
            try:
                await self.run_cycle()
                await asyncio.sleep(interval_seconds)
            except Exception as e:
                logger.error(f"Error in continuous trading: {e}", exc_info=True)
                await asyncio.sleep(5)  # Shorter interval on error

    def stop(self) -> None:
        """Stop continuous trading"""
        self.is_running = False
        self.state['status'] = 'STOPPED'
        logger.info("Trading stopped")

    def pause(self) -> None:
        """Pause trading"""
        self.is_running = False
        self.state['status'] = 'PAUSED'
        logger.info("Trading paused")

    def resume(self) -> None:
        """Resume trading"""
        self.state['status'] = 'RUNNING'
        logger.info("Trading resumed")

    def reset_circuit_breaker(self) -> None:
        """Reset circuit breaker"""
        self.state['circuit_breaker_triggered'] = False
        self.agents['risk_management'].reset_circuit_breaker()
        logger.info("Circuit breaker reset")

    def get_status(self) -> Dict[str, Any]:
        """Get current system status"""
        return {
            'status': self.state.get('status', 'UNKNOWN'),
            'is_running': self.is_running,
            'circuit_breaker': self.state.get('circuit_breaker_triggered', False),
            'market_regime': self.state.get('market_regime', 'UNKNOWN'),
            'portfolio_value': self.state.get('portfolio_value', 0),
            'pending_signals': len(self.state.get('pending_signals', [])),
            'validated_signals': len(self.state.get('validated_signals', [])),
            'executed_trades': len(self.state.get('executed_trades', [])),
            'positions': len(self.state.get('positions', [])),
            'last_update': datetime.now().isoformat(),
        }

    def get_agent_status(self) -> Dict[str, Dict]:
        """Get status of all agents"""
        return {
            name: {
                'type': agent.__class__.__name__,
                'active': True,
            }
            for name, agent in self.agents.items()
        }

    def get_recent_actions(self, limit: int = 20) -> List[Dict]:
        """Get recent agent actions"""
        actions = self.state.get('agent_actions', [])
        return [
            {
                'agent': action.agent_name,
                'action': action.action,
                'confidence': action.confidence,
                'timestamp': datetime.fromtimestamp(action.timestamp).isoformat(),
                'duration_ms': action.duration_ms,
            }
            for action in sorted(actions, key=lambda x: x.timestamp, reverse=True)[:limit]
        ]


def create_trading_graph(w3=None, config: Dict = None) -> TradingOrchestrator:
    """Factory function to create a trading orchestrator"""
    return TradingOrchestrator(w3=w3, config=config)
