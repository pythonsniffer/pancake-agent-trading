"""
Natural Language Command Interface

Parses natural language commands into structured actions:
- "show arbitrage on BNB chain" -> {action: "show", strategy: "arbitrage", chain: "bsc"}
- "start trading with $1000" -> {action: "start", capital: 1000}
- "explain why the last trade failed" -> {action: "explain", target: "last_trade"}
- "what is my portfolio value?" -> {action: "query", subject: "portfolio_value"}

Uses LangChain + OpenAI for intent classification and entity extraction.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime
import json
import re

logger = logging.getLogger(__name__)


@dataclass
class ParsedCommand:
    """Parsed natural language command"""
    original_text: str
    intent: str
    action: str
    entities: Dict[str, Any]
    chain: Optional[str] = None
    strategy: Optional[str] = None
    amount: Optional[float] = None
    token: Optional[str] = None
    confidence: float = 0.0


@dataclass
class CommandResponse:
    """Response to a natural language command"""
    command: ParsedCommand
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    action_taken: Optional[str] = None
    agent_explanation: Optional[str] = None


class NLPCommandInterface:
    """
    Natural Language Command Interface for the trading system.

    Supported commands:
    - Market queries: "show me BTC price", "what's the APY on ETH-USDC"
    - Strategy control: "start arbitrage strategy", "stop all trading"
    - Portfolio: "show my portfolio", "what's my PnL"
    - Risk: "what's my current risk level", "show circuit breaker status"
    - Execution: "execute trade on BNB-USDT with $100"
    - Analysis: "explain the last failed trade", "show agent decisions"
    - Backtest: "run backtest on mean reversion", "what-if gas doubles"
    """

    # Intent patterns for regex-based parsing (fallback)
    INTENT_PATTERNS = {
        "market_query": [
            r"(show|get|what|tell).*(price|market|trend|volume|liquidity)",
            r"(how is|what's).*(BTC|ETH|BNB|CAKE).*(doing|price|trading)"
        ],
        "strategy_control": [
            r"(start|begin|enable|activate).*(trading|strategy|arbitrage|bot)",
            r"(stop|pause|disable|deactivate).*(trading|strategy|all)"
        ],
        "portfolio_query": [
            r"(show|display|get|what).*(portfolio|balance|holdings|position)",
            r"(what's|what is).*(my|the).*(pnl|profit|loss|return)"
        ],
        "risk_query": [
            r"(show|get|what).*(risk|exposure|drawdown|variance)",
            r"(is|check).*(circuit breaker|safety|protection)"
        ],
        "trade_execution": [
            r"(execute|place|submit|make).*(trade|swap|order)",
            r"(buy|sell|swap).*(\$)?(\d+).*(worth of)?\s*(\w+)"
        ],
        "trade_analysis": [
            r"(explain|why|what happened).*(fail|loss|trade|decision)",
            r"(show|get).*(agent|bot).*(decision|thought|reason)"
        ],
        "backtest": [
            r"(run|start|execute).*(backtest|simulation|test)",
            r"(what.if|scenario).*(gas|price|volatility)"
        ],
        "system_status": [
            r"(status|health|state).*(system|agent|bot|trading)",
            r"(are|is).*(agent|bot|system).*(running|active|up)"
        ]
    }

    # Entity extraction patterns
    ENTITY_PATTERNS = {
        "amount": [
            r"\$(\d+(?:\.\d+)?)",
            r"(\d+(?:\.\d+)?)\s*(?:USD|dollars?)",
            r"(\d+(?:\.\d+)?)\s*(?:percent|%|pct)"
        ],
        "chain": [
            r"\b(bsc|bnb chain|binance|ethereum|eth|arbitrum|arb|polygon|poly)\b"
        ],
        "strategy": [
            r"\b(arbitrage|arb|trend following|mean reversion|lp yield|liquidity|yield)\b"
        ],
        "token": [
            r"\b(BTC|ETH|BNB|CAKE|USDT|USDC|BUSD|DAI|WETH|WBTC)\b"
        ]
    }

    # Chain name normalization
    CHAIN_MAP = {
        "bsc": "bsc", "bnb chain": "bsc", "binance": "bsc",
        "ethereum": "ethereum", "eth": "ethereum",
        "arbitrum": "arbitrum", "arb": "arbitrum",
        "polygon": "polygon", "poly": "polygon"
    }

    # Strategy normalization
    STRATEGY_MAP = {
        "arbitrage": "ARBITRAGE", "arb": "ARBITRAGE",
        "trend": "TREND_FOLLOWING", "trend following": "TREND_FOLLOWING",
        "mean reversion": "MEAN_REVERSION", "mean": "MEAN_REVERSION",
        "lp yield": "LP_YIELD", "liquidity": "LP_YIELD", "yield": "LP_YIELD"
    }

    def __init__(self, llm: Optional[Any] = None):
        self.llm = llm
        self.command_history: List[ParsedCommand] = []
        self.response_handlers: Dict[str, Callable] = {}

    def register_handler(self, intent: str, handler: Callable):
        """Register a handler for a specific intent"""
        self.response_handlers[intent] = handler

    async def parse_command(self, text: str) -> ParsedCommand:
        """
        Parse natural language command into structured intent.

        First tries LLM-based parsing if available, falls back to regex patterns.
        """
        text_lower = text.lower().strip()

        # Try LLM-based parsing first if available
        if self.llm:
            try:
                return await self._parse_with_llm(text)
            except Exception as e:
                logger.warning(f"LLM parsing failed, using fallback: {e}")

        # Fallback to regex-based parsing
        return self._parse_with_regex(text_lower)

    async def _parse_with_llm(self, text: str) -> ParsedCommand:
        """Use LLM to parse command"""
        # This would use LangChain/OpenAI for intent classification
        # For now, return a placeholder
        raise NotImplementedError("LLM parsing not implemented")

    def _parse_with_regex(self, text: str) -> ParsedCommand:
        """Parse command using regex patterns"""
        # Determine intent
        intent = self._detect_intent(text)

        # Extract entities
        entities = self._extract_entities(text)

        # Determine action
        action = self._determine_action(text, intent)

        # Build parsed command
        cmd = ParsedCommand(
            original_text=text,
            intent=intent,
            action=action,
            entities=entities,
            chain=entities.get("chain"),
            strategy=entities.get("strategy"),
            amount=entities.get("amount"),
            token=entities.get("token"),
            confidence=0.7  # Regex-based confidence
        )

        self.command_history.append(cmd)
        return cmd

    def _detect_intent(self, text: str) -> str:
        """Detect intent from text using patterns"""
        scores = {}

        for intent, patterns in self.INTENT_PATTERNS.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    score += 1
            scores[intent] = score

        # Return intent with highest score
        if scores:
            best_intent = max(scores, key=scores.get)
            return best_intent if scores[best_intent] > 0 else "unknown"

        return "unknown"

    def _extract_entities(self, text: str) -> Dict[str, Any]:
        """Extract entities from text"""
        entities = {}

        # Extract amount
        for pattern in self.ENTITY_PATTERNS["amount"]:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                entities["amount"] = float(match.group(1))
                break

        # Extract chain
        for pattern in self.ENTITY_PATTERNS["chain"]:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                chain_key = match.group(1).lower()
                entities["chain"] = self.CHAIN_MAP.get(chain_key, chain_key)
                break

        # Extract strategy
        for pattern in self.ENTITY_PATTERNS["strategy"]:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                strategy_key = match.group(1).lower()
                entities["strategy"] = self.STRATEGY_MAP.get(strategy_key, strategy_key.upper())
                break

        # Extract token
        for pattern in self.ENTITY_PATTERNS["token"]:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                entities["token"] = match.group(1).upper()
                break

        return entities

    def _determine_action(self, text: str, intent: str) -> str:
        """Determine specific action based on intent and text"""
        if intent == "strategy_control":
            if any(word in text for word in ["start", "begin", "activate", "enable"]):
                return "start_strategy"
            elif any(word in text for word in ["stop", "pause", "deactivate", "disable"]):
                return "stop_strategy"
            elif any(word in text for word in ["reset", "restart", "reload"]):
                return "reset_strategy"

        elif intent == "trade_execution":
            if any(word in text for word in ["buy", "purchase", "acquire"]):
                return "buy"
            elif any(word in text for word in ["sell", "dump", "exit"]):
                return "sell"
            elif any(word in text for word in ["swap", "exchange", "trade"]):
                return "swap"

        elif intent == "market_query"::
            if any(word in text for word in ["price", "worth", "value"]):
                return "get_price"
            elif any(word in text for word in ["apy", "yield", "apr", "return"]):
                return "get_yield"
            elif any(word in text for word in ["volume", "liquidity", "depth"]):
                return "get_liquidity"
            elif any(word in text for word in ["trend", "direction", "momentum"]):
                return "get_trend"

        elif intent == "trade_analysis":
            if any(word in text for word in ["explain", "why", "reason"]):
                return "explain_decision"
            elif any(word in text for word in ["agent", "bot", "strategy", "think"]):
                return "show_agent_decisions"

        elif intent == "system_status":
            return "get_status"

        elif intent == "risk_query":
            return "get_risk_metrics"

        elif intent == "portfolio_query":
            return "get_portfolio"

        elif intent == "backtest":
            if any(word in text for word in ["what.if", "scenario", "if", "suppose"]):
                return "what_if"
            return "run_backtest"

        return "unknown"

    async def execute_command(
        self,
        command: ParsedCommand,
        context: Optional[Dict[str, Any]] = None
    ) -> CommandResponse:
        """
        Execute a parsed command and generate a response.

        This is the main entry point for handling commands.
        """
        handler = self.response_handlers.get(command.intent)

        if handler:
            try:
                result = await handler(command, context)
                return result
            except Exception as e:
                logger.error(f"Command handler failed: {e}")
                return CommandResponse(
                    command=command,
                    success=False,
                    message=f"Failed to execute command: {str(e)}"
                )

        # Default response if no handler
        return CommandResponse(
            command=command,
            success=False,
            message=f"I don't know how to handle: '{command.original_text}'"
        )

    def generate_agent_explanation(
        self,
        agent_name: str,
        action: str,
        reasoning: Dict[str, Any],
        confidence: float
    ) -> str:
        """
        Generate human-readable explanation of agent decision.

        This translates technical agent outputs into natural language.
        """
        explanations = []

        # Context
        if "market_regime" in reasoning:
            regime = reasoning["market_regime"]
            explanations.append(f"Market was in {regime.lower()} regime")

        if "signals_found" in reasoning:
            signals = reasoning["signals_found"]
            explanations.append(f"Found {signals} potential trade signals")

        if "risk_score" in reasoning:
            risk = reasoning["risk_score"]
            if risk < 30:
                explanations.append("Risk level was low")
            elif risk < 60:
                explanations.append("Risk level was moderate")
            else:
                explanations.append("Risk level was high")

        if "expected_profit" in reasoning:
            profit = reasoning["expected_profit"]
            explanations.append(f"Expected profit was ${profit:.2f}")

        if "slippage" in reasoning:
            slippage = reasoning["slippage"]
            explanations.append(f"Estimated slippage was {slippage:.2%}")

        # Outcome
        if action == "EXECUTE_TRADE":
            explanations.append(f"Trade was executed with {confidence:.0%} confidence")
        elif action == "REJECT_SIGNAL":
            if "rejection_reason" in reasoning:
                explanations.append(f"Trade was rejected: {reasoning['rejection_reason']}")
            else:
                explanations.append("Trade was rejected due to risk constraints")
        elif action == "HOLD":
            explanations.append("No action taken - waiting for better conditions")

        return "; ".join(explanations) if explanations else "No specific reasoning recorded"

    def format_market_response(
        self,
        token: str,
        price: float,
        change_24h: float,
        volume: float,
        chain: str = "bsc"
    ) -> str:
        """Format market data into natural language response"""
        direction = "up" if change_24h >= 0 else "down"
        emoji = "🟢" if change_24h >= 0 else "🔴"

        return (
            f"{emoji} {token} is trading at ${price:.2f} on {chain.upper()}, "
            f"{direction} {abs(change_24h):.2f}% in the last 24h "
            f"with ${volume:,.0f} volume"
        )

    def format_portfolio_response(
        self,
        total_value: float,
        pnl: float,
        pnl_percent: float,
        positions: int
    ) -> str:
        """Format portfolio data into natural language response"""
        direction = "profit" if pnl >= 0 else "loss"
        emoji = "🟢" if pnl >= 0 else "🔴"

        return (
            f"{emoji} Your portfolio is worth ${total_value:,.2f} "
            f"with a {direction} of ${abs(pnl):,.2f} ({pnl_percent:+.2f}%). "
            f"You have {positions} active position{'s' if positions != 1 else ''}."
        )

    def format_trade_response(
        self,
        trade_type: str,
        token_in: str,
        token_out: str,
        amount: float,
        expected_profit: float,
        status: str
    ) -> str:
        """Format trade execution into natural language response"""
        status_emoji = {
            "SUCCESS": "✅",
            "FAILED": "❌",
            "PENDING": "⏳",
            "SIMULATED": "🧪"
        }.get(status, "❓")

        return (
            f"{status_emoji} {trade_type} trade: "
            f"Swapped {amount} {token_in} for {token_out}. "
            f"Expected profit: ${expected_profit:.2f}. "
            f"Status: {status.lower()}"
        )

    def get_command_suggestions(self, partial: str) -> List[str]:
        """Get command suggestions based on partial input"""
        suggestions = [
            "show BTC price",
            "start arbitrage strategy",
            "stop all trading",
            "show portfolio",
            "what is my PnL",
            "explain last trade",
            "show agent decisions",
            "run backtest on mean reversion",
            "what if gas doubles",
            "execute trade on BNB-USDT with $100"
        ]

        # Filter by partial match
        partial_lower = partial.lower()
        return [s for s in suggestions if partial_lower in s.lower()]

    def get_help_text(self) -> str:
        """Get help text with available commands"""
        return """
Available Commands:

Market Queries:
- "show BTC price" - Get current price
- "what's the APY on ETH-USDC" - Get yield information
- "show arbitrage on BNB chain" - Find arbitrage opportunities

Strategy Control:
- "start arbitrage strategy" - Start a strategy
- "stop all trading" - Stop all activity
- "reset circuit breaker" - Reset safety mechanisms

Portfolio:
- "show my portfolio" - View holdings
- "what's my PnL" - Get profit/loss
- "show trade history" - View recent trades

Analysis:
- "explain last trade" - Get decision reasoning
- "show agent decisions" - View agent thought process
- "what happened with trade #123" - Analyze specific trade

Backtesting:
- "run backtest on mean reversion" - Run simulation
- "what if gas doubles" - Run scenario analysis

Risk:
- "show risk metrics" - View risk dashboard
- "is circuit breaker active" - Check safety status
        """


# Example usage handlers
async def example_market_handler(command: ParsedCommand, context: Dict) -> CommandResponse:
    """Example handler for market queries"""
    token = command.token or "BTC"

    # Mock data
    return CommandResponse(
        command=command,
        success=True,
        message=f"🟢 {token} is trading at $67,420.50 on BSC, up 2.3% in the last 24h",
        data={"token": token, "price": 67420.50, "change_24h": 2.3}
    )


async def example_portfolio_handler(command: ParsedCommand, context: Dict) -> CommandResponse:
    """Example handler for portfolio queries"""
    return CommandResponse(
        command=command,
        success=True,
        message="🟢 Your portfolio is worth $12,450.80 with a profit of $450.80 (3.8%). You have 5 active positions.",
        data={"total_value": 12450.80, "pnl": 450.80, "pnl_percent": 3.8, "positions": 5}
    )
