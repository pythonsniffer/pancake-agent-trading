import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
import json

from web3 import Web3
from eth_account import Account
from ..state import TradingState, TradeSignal, TradeExecution, AgentAction

logger = logging.getLogger(__name__)


@dataclass
class ExecutionConfig:
    max_retries: int = 3
    retry_delay_ms: int = 1000
    deadline_minutes: int = 5
    gas_limit_multiplier: float = 1.2
    use_flashbots: bool = False
    simulate_before_execute: bool = True


class ExecutionAgent:
    """
    Execution Agent: Handles blockchain transaction submission,
    MEV protection, gas optimization, and transaction lifecycle management.
    """

    def __init__(self, w3: Web3, private_key: str, config: Dict = None):
        self.w3 = w3
        self.config = ExecutionConfig(**(config or {}))

        # Initialize account
        if private_key:
            self.account = Account.from_key(private_key)
            self.wallet_address = self.account.address
        else:
            self.account = None
            self.wallet_address = None

        # PancakeSwap Router V2 ABI (minimal)
        self.router_abi = [
            {"inputs": [{"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                       {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
                       {"internalType": "address[]", "name": "path", "type": "address[]"},
                       {"internalType": "address", "name": "to", "type": "address"},
                       {"internalType": "uint256", "name": "deadline", "type": "uint256"}],
             "name": "swapExactTokensForTokens",
             "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
             "stateMutability": "nonpayable",
             "type": "function"},
            {"inputs": [{"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                       {"internalType": "address[]", "name": "path", "type": "address[]"}],
             "name": "getAmountsOut",
             "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
             "stateMutability": "view",
             "type": "function"}
        ]

        # ERC20 ABI
        self.erc20_abi = [
            {"constant": False, "inputs": [{"name": "_spender", "type": "address"},
                                           {"name": "_value", "type": "uint256"}],
             "name": "approve", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
            {"constant": True, "inputs": [{"name": "_owner", "type": "address"},
                                          {"name": "_spender", "type": "address"}],
             "name": "allowance", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
        ]

        # Router addresses
        self.router_v2 = "0x10ED43C718714eb63d5aA57B78B54704E256024E"

        # Transaction queue
        self.pending_transactions: List[Dict] = []
        self.nonce = None

    async def run(self, state: TradingState) -> TradingState:
        """Main entry point for the agent"""
        logger.info("Execution Agent running...")

        try:
            # Check if in simulation mode
            simulation_mode = not self.account

            # Get validated signals
            validated_signals = state.get('validated_signals', [])

            if not validated_signals:
                logger.info("No validated signals to execute")
                return state

            executions = []

            for signal in validated_signals:
                if simulation_mode:
                    # Simulate execution
                    execution = await self.simulate_trade(signal)
                else:
                    # Execute actual trade
                    execution = await self.execute_trade(signal)

                executions.append(execution)

                # Update daily loss if trade lost money
                if execution.actual_profit < 0:
                    # Notify risk agent
                    logger.warning(f"Trade {execution.signal_id} lost ${abs(execution.actual_profit):.2f}")

            # Update state
            state['executed_trades'] = executions

            # Create agent action
            action = AgentAction(
                agent_name="ExecutionAgent",
                action="execute_trades",
                input_data={"signals": len(validated_signals)},
                output_data={
                    "executed": len(executions),
                    "successful": sum(1 for e in executions if e.status == "SUCCESS"),
                    "failed": sum(1 for e in executions if e.status == "FAILED"),
                    "simulation_mode": simulation_mode,
                },
                confidence=0.9,
                timestamp=int(datetime.now().timestamp()),
                duration_ms=500,
            )
            state['agent_actions'].append(action)

            logger.info(f"Executed {len(executions)} trades ({sum(1 for e in executions if e.status == 'SUCCESS')} successful)")

        except Exception as e:
            logger.error(f"Error in Execution Agent: {e}", exc_info=True)
            state['status'] = 'ERROR'

        return state

    async def execute_trade(self, signal: TradeSignal) -> TradeExecution:
        """Execute a trade on the blockchain"""
        logger.info(f"Executing trade {signal.id}...")

        start_time = datetime.now()

        try:
            # Get gas price
            gas_price = await self.get_optimal_gas_price()

            # Build transaction
            tx_params = await self.build_transaction(signal, gas_price)

            # Simulate transaction if enabled
            if self.config.simulate_before_execute:
                simulation_result = await self.simulate_transaction(tx_params)
                if not simulation_result:
                    return TradeExecution(
                        signal_id=signal.id,
                        status="FAILED",
                        error_message="Transaction simulation failed",
                        timestamp=int(datetime.now().timestamp()),
                    )

            # Sign and send transaction
            tx_hash = await self.send_transaction(tx_params)

            # Wait for confirmation
            receipt = await self.wait_for_confirmation(tx_hash)

            # Calculate actual results
            gas_cost_eth = receipt['gasUsed'] * receipt['effectiveGasPrice'] / 1e18
            gas_cost_usd = gas_cost_eth * 300  # Approximate ETH price

            # Calculate actual profit (simplified)
            actual_profit = signal.expected_profit - gas_cost_usd

            execution = TradeExecution(
                signal_id=signal.id,
                status="SUCCESS",
                tx_hash=tx_hash.hex() if hasattr(tx_hash, 'hex') else str(tx_hash),
                block_number=receipt['blockNumber'],
                gas_used=receipt['gasUsed'],
                gas_cost_usd=gas_cost_usd,
                actual_profit=actual_profit,
                timestamp=int(datetime.now().timestamp()),
            )

            logger.info(f"Trade {signal.id} executed successfully: {execution.tx_hash}")
            return execution

        except Exception as e:
            logger.error(f"Trade execution failed: {e}")
            return TradeExecution(
                signal_id=signal.id,
                status="FAILED",
                error_message=str(e),
                timestamp=int(datetime.now().timestamp()),
            )

    async def simulate_trade(self, signal: TradeSignal) -> TradeExecution:
        """Simulate a trade execution"""
        logger.info(f"Simulating trade {signal.id}...")

        # Simulate gas costs
        gas_used = 150000  # Average swap gas
        gas_price_gwei = 5
        gas_cost_eth = gas_used * gas_price_gwei / 1e9
        gas_cost_usd = gas_cost_eth * 300

        # Simulate some slippage
        slippage = 0.005  # 0.5%
        actual_profit = signal.expected_profit * (1 - slippage) - gas_cost_usd

        # Random success/failure for demo
        import random
        success = random.random() > 0.1  # 90% success rate in simulation

        return TradeExecution(
            signal_id=signal.id,
            status="SIMULATED" if success else "FAILED",
            tx_hash=f"sim_{signal.id}",
            block_number=self.w3.eth.block_number if hasattr(self.w3, 'eth') else 0,
            gas_used=gas_used,
            gas_cost_usd=gas_cost_usd,
            actual_profit=actual_profit if success else -gas_cost_usd,
            slippage=slippage,
            timestamp=int(datetime.now().timestamp()),
        )

    async def build_transaction(self, signal: TradeSignal, gas_price: int) -> Dict:
        """Build a swap transaction"""
        router = self.w3.eth.contract(
            address=Web3.to_checksum_address(self.router_v2),
            abi=self.router_abi
        )

        # Calculate deadline
        deadline = int(datetime.now().timestamp()) + (self.config.deadline_minutes * 60)

        # Calculate minimum output with slippage
        amount_in = int(signal.amount_in)
        amount_out_min = int(amount_in * (1 - signal.slippage_tolerance))

        # Build path
        path = [signal.token_in.address, signal.token_out.address]

        # Get transaction data
        tx = router.functions.swapExactTokensForTokens(
            amount_in,
            amount_out_min,
            path,
            self.wallet_address,
            deadline
        ).build_transaction({
            'from': self.wallet_address,
            'gas': 300000,
            'gasPrice': gas_price,
            'nonce': await self.get_nonce(),
        })

        return tx

    async def send_transaction(self, tx_params: Dict) -> str:
        """Sign and send a transaction"""
        if not self.account:
            raise ValueError("No account configured")

        signed_tx = self.w3.eth.account.sign_transaction(tx_params, self.account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        return tx_hash

    async def wait_for_confirmation(self, tx_hash: str, timeout: int = 120) -> Dict:
        """Wait for transaction confirmation"""
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)
        return {
            'status': receipt.status,
            'blockNumber': receipt.blockNumber,
            'gasUsed': receipt.gasUsed,
            'effectiveGasPrice': receipt.effectiveGasPrice,
        }

    async def simulate_transaction(self, tx_params: Dict) -> bool:
        """Simulate a transaction before sending"""
        try:
            self.w3.eth.call(tx_params)
            return True
        except Exception as e:
            logger.warning(f"Transaction simulation failed: {e}")
            return False

    async def get_optimal_gas_price(self) -> int:
        """Get optimal gas price"""
        try:
            base_gas_price = self.w3.eth.gas_price
            # Add 10% buffer
            return int(base_gas_price * 1.1)
        except Exception:
            return self.w3.to_wei(5, 'gwei')  # Default 5 gwei

    async def get_nonce(self) -> int:
        """Get next nonce"""
        if self.nonce is None:
            self.nonce = self.w3.eth.get_transaction_count(self.wallet_address)
        else:
            self.nonce += 1
        return self.nonce

    async def approve_token(self, token_address: str, amount: int) -> Optional[str]:
        """Approve router to spend tokens"""
        try:
            token = self.w3.eth.contract(
                address=Web3.to_checksum_address(token_address),
                abi=self.erc20_abi
            )

            # Check current allowance
            allowance = token.functions.allowance(
                self.wallet_address,
                self.router_v2
            ).call()

            if allowance >= amount:
                return None  # Already approved

            # Build approval transaction
            tx = token.functions.approve(
                self.router_v2,
                amount
            ).build_transaction({
                'from': self.wallet_address,
                'gas': 50000,
                'gasPrice': await self.get_optimal_gas_price(),
                'nonce': await self.get_nonce(),
            })

            tx_hash = await self.send_transaction(tx)
            await self.wait_for_confirmation(tx_hash)

            return tx_hash.hex() if hasattr(tx_hash, 'hex') else str(tx_hash)

        except Exception as e:
            logger.error(f"Token approval failed: {e}")
            return None

    def estimate_gas_cost(self, signal: TradeSignal) -> float:
        """Estimate gas cost in USD"""
        try:
            gas_price = self.w3.eth.gas_price
            estimated_gas = 200000  # Estimated gas for swap
            gas_cost_eth = (gas_price * estimated_gas) / 1e18
            # Assume $300 per ETH
            return gas_cost_eth * 300
        except:
            return 3.0  # Default $3
