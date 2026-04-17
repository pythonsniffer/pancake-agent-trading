"""
MEV Protection Module: Flashbots-style bundle submission and MEV-aware execution.

Provides:
- Private transaction routing
- Bundle submission for atomic execution
- Sandwich attack protection
- Priority gas auctions
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime
import json
import time

from web3 import Web3
from eth_account import Account
from eth_account.datastructures import SignedTransaction

logger = logging.getLogger(__name__)


@dataclass
class BundleTransaction:
    """A transaction to be included in a Flashbots bundle"""
    signed_tx: SignedTransaction
    hash: str
    nonce: int
    gas_price: int
    priority: int = 0


@dataclass
class MEVBundle:
    """A bundle of transactions for atomic execution"""
    transactions: List[BundleTransaction]
    block_target: int
    min_timestamp: int
    max_timestamp: int
    reverting_tx_hashes: List[str]
    replacement_uuid: Optional[str] = None


@dataclass
class BundleResult:
    """Result of a bundle submission"""
    bundle_hash: str
    block_number: int
    status: str  # PENDING, INCLUDED, FAILED
    transactions: List[str]
    error: Optional[str] = None
    effective_gas_price: Optional[int] = None


@dataclass
class ProtectionConfig:
    """MEV protection configuration"""
    use_flashbots: bool = True
    use_mev_blocker: bool = False
    use_eden_network: bool = False
    use_private_tx: bool = True
    bundle_timeout_blocks: int = 5
    max_bundle_retries: int = 3
    priority_fee_premium: float = 1.1  # 10% premium
    block_deadline_buffer: int = 3


class MEVProtector:
    """
    MEV Protection for transaction execution.

    Protects against:
    - Sandwich attacks
    - Front-running
    - Back-running
    - Priority gas auction manipulation
    """

    # Flashbots relay endpoints
    FLASHBOTS_RELAYS = {
        "mainnet": "https://relay.flashbots.net",
        "goerli": "https://relay-goerli.flashbots.net",
        "sepolia": "https://relay-sepolia.flashbots.net",
    }

    # MEV-Blocker endpoints
    MEV_BLOCKER_ENDPOINTS = {
        "fast": "https://rpc.mevblocker.io/fast",
        "full": "https://rpc.mevblocker.io/full",
        "norebate": "https://rpc.mevblocker.io/norebate",
    }

    def __init__(
        self,
        w3: Web3,
        account: Optional[Account] = None,
        config: Optional[ProtectionConfig] = None,
        chain: str = "mainnet"
    ):
        self.w3 = w3
        self.account = account
        self.config = config or ProtectionConfig()
        self.chain = chain

        # Track pending bundles
        self.pending_bundles: Dict[str, MEVBundle] = {}
        self.bundle_results: Dict[str, BundleResult] = {}

        # Statistics
        self.total_bundles_submitted = 0
        self.total_bundles_included = 0
        self.total_bundles_failed = 0

        logger.info(f"MEVProtector initialized for {chain}")

    async def create_bundle(
        self,
        transactions: List[Dict[str, Any]],
        target_block: Optional[int] = None,
        deadline_blocks: int = 5
    ) -> MEVBundle:
        """
        Create a Flashbots bundle from transactions.

        Args:
            transactions: List of transaction dicts to sign and bundle
            target_block: Target block number (defaults to next block)
            deadline_blocks: How many blocks to try before giving up

        Returns:
            MEVBundle ready for submission
        """
        if not self.account:
            raise ValueError("Account required for bundle creation")

        current_block = self.w3.eth.block_number
        if target_block is None:
            target_block = current_block + 1

        bundle_txs = []
        for tx_params in transactions:
            # Sign transaction
            signed_tx = self.w3.eth.account.sign_transaction(
                tx_params,
                self.account.key
            )

            bundle_tx = BundleTransaction(
                signed_tx=signed_tx,
                hash=signed_tx.hash.hex(),
                nonce=tx_params['nonce'],
                gas_price=tx_params.get('gasPrice', 0),
                priority=tx_params.get('priority', 0)
            )
            bundle_txs.append(bundle_tx)

        bundle = MEVBundle(
            transactions=bundle_txs,
            block_target=target_block,
            min_timestamp=int(time.time()),
            max_timestamp=int(time.time()) + (deadline_blocks * 12),  # ~12s per block
            reverting_tx_hashes=[],
            replacement_uuid=f"bundle_{int(time.time())}_{self.account.address[:8]}"
        )

        return bundle

    async def submit_bundle(
        self,
        bundle: MEVBundle,
        simulate_only: bool = False
    ) -> BundleResult:
        """
        Submit bundle to Flashbots relay.

        Args:
            bundle: MEVBundle to submit
            simulate_only: If True, only simulate don't submit

        Returns:
            BundleResult with submission status
        """
        if not self.config.use_flashbots:
            logger.warning("Flashbots disabled, falling back to regular tx")
            return BundleResult(
                bundle_hash="",
                block_number=0,
                status="SKIPPED",
                transactions=[tx.hash for tx in bundle.transactions],
                error="Flashbots disabled"
            )

        try:
            # Build bundle params
            signed_txs = [tx.signed_tx.rawTransaction.hex()
                          for tx in bundle.transactions]

            params = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "eth_sendBundle",
                "params": [{
                    "txs": signed_txs,
                    "blockNumber": hex(bundle.block_target),
                    "minTimestamp": hex(bundle.min_timestamp),
                    "maxTimestamp": hex(bundle.max_timestamp),
                    "revertingTxHashes": bundle.reverting_tx_hashes,
                }]
            }

            if simulate_only:
                # Simulate the bundle
                sim_result = await self._simulate_bundle(bundle)
                return BundleResult(
                    bundle_hash=sim_result.get("bundleHash", ""),
                    block_number=bundle.block_target,
                    status="SIMULATED",
                    transactions=[tx.hash for tx in bundle.transactions],
                    effective_gas_price=sim_result.get("gasPrice")
                )

            # Submit to relay
            result = await self._send_to_relay(params)

            self.total_bundles_submitted += 1

            bundle_result = BundleResult(
                bundle_hash=result.get("bundleHash", ""),
                block_number=bundle.block_target,
                status="PENDING",
                transactions=[tx.hash for tx in bundle.transactions],
            )

            self.pending_bundles[bundle_result.bundle_hash] = bundle

            logger.info(f"Bundle submitted: {bundle_result.bundle_hash}")
            return bundle_result

        except Exception as e:
            logger.error(f"Bundle submission failed: {e}")
            self.total_bundles_failed += 1
            return BundleResult(
                bundle_hash="",
                block_number=0,
                status="FAILED",
                transactions=[tx.hash for tx in bundle.transactions],
                error=str(e)
            )

    async def _simulate_bundle(self, bundle: MEVBundle) -> Dict[str, Any]:
        """Simulate a bundle before submission"""
        # This would call Flashbots simulate endpoint
        # For now, return mock result
        return {
            "bundleHash": f"sim_{int(time.time())}",
            "gasPrice": self.w3.to_wei(20, 'gwei'),
            "success": True,
            "results": [{"gasUsed": 150000} for _ in bundle.transactions]
        }

    async def _send_to_relay(self, params: Dict) -> Dict:
        """Send bundle to Flashbots relay"""
        import aiohttp

        relay_url = self.FLASHBOTS_RELAYS.get(self.chain, self.FLASHBOTS_RELAYS["mainnet"])

        async with aiohttp.ClientSession() as session:
            async with session.post(
                relay_url,
                json=params,
                headers={"Content-Type": "application/json"}
            ) as response:
                result = await response.json()
                if "error" in result:
                    raise Exception(f"Relay error: {result['error']}")
                return result.get("result", {})

    async def send_private_transaction(
        self,
        signed_tx: SignedTransaction,
        max_block_number: Optional[int] = None
    ) -> str:
        """
        Send a transaction privately to avoid mempool exposure.

        Uses Flashbots eth_sendPrivateTransaction endpoint.
        """
        if not self.config.use_private_tx:
            # Fall back to public mempool
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            return tx_hash.hex()

        try:
            current_block = self.w3.eth.block_number
            if max_block_number is None:
                max_block_number = current_block + self.config.bundle_timeout_blocks

            params = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "eth_sendPrivateTransaction",
                "params": [{
                    "tx": signed_tx.rawTransaction.hex(),
                    "maxBlockNumber": hex(max_block_number),
                    "preferences": {
                        "fast": True,
                        "privacy": {"hints": ["calldata", "logs"]}
                    }
                }]
            }

            result = await self._send_to_relay(params)
            return result.get("txHash", "")

        except Exception as e:
            logger.error(f"Private transaction failed: {e}, falling back to public")
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            return tx_hash.hex()

    def calculate_mev_protection_gas(
        self,
        base_gas_price: int,
        priority_fee_wei: Optional[int] = None
    ) -> int:
        """
        Calculate gas price with MEV protection premium.

        For MEV protection, we often need to pay a small premium
        to ensure inclusion through private channels.
        """
        if priority_fee_wei is None:
            priority_fee_wei = self.w3.to_wei(2, 'gwei')

        # Add premium for MEV protection
        protected_gas = int(base_gas_price * self.config.priority_fee_premium)
        return protected_gas + priority_fee_wei

    async def wait_for_bundle_inclusion(
        self,
        bundle_hash: str,
        timeout_blocks: int = 5
    ) -> Optional[BundleResult]:
        """
        Wait for bundle to be included in a block.

        Polls the relay for bundle status.
        """
        start_block = self.w3.eth.block_number
        target_block = start_block + timeout_blocks

        while self.w3.eth.block_number < target_block:
            try:
                # Check bundle status
                params = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "eth_getBundleStats",
                    "params": [bundle_hash, hex(self.w3.eth.block_number)]
                }

                result = await self._send_to_relay(params)

                if result.get("isSimulated") and result.get("isSentToMiners"):
                    if result.get("isIncluded"):
                        self.total_bundles_included += 1
                        return BundleResult(
                            bundle_hash=bundle_hash,
                            block_number=result.get("blockNumber", 0),
                            status="INCLUDED",
                            transactions=[],
                            effective_gas_price=result.get("effectiveGasPrice")
                        )

                await asyncio.sleep(1)

            except Exception as e:
                logger.warning(f"Error checking bundle status: {e}")
                await asyncio.sleep(2)

        return BundleResult(
            bundle_hash=bundle_hash,
            block_number=0,
            status="TIMEOUT",
            transactions=[],
            error="Bundle not included within timeout"
        )

    def estimate_sandwich_risk(
        self,
        token_pair: str,
        amount_in: float,
        expected_slippage: float,
        pool_liquidity: float
    ) -> float:
        """
        Estimate the risk of a sandwich attack.

        Returns a risk score from 0 (low) to 1 (high).
        """
        # Factors that increase sandwich risk:
        # 1. Large trade size relative to pool liquidity
        # 2. High expected slippage
        # 3. High volatility tokens

        if pool_liquidity == 0:
            return 1.0  # Unknown liquidity = high risk

        # Size relative to liquidity
        size_ratio = amount_in / pool_liquidity

        # Base risk calculation
        risk = 0.0

        # Size component (trades > 1% of liquidity are high risk)
        if size_ratio > 0.05:  # >5% of liquidity
            risk += 0.4
        elif size_ratio > 0.01:  # >1% of liquidity
            risk += 0.2

        # Slippage component
        if expected_slippage > 0.01:  # >1% slippage
            risk += 0.3

        # Token volatility component (simplified)
        volatile_tokens = ["SHIB", "DOGE", "PEPE", "FLOKI"]
        if any(token in token_pair.upper() for token in volatile_tokens):
            risk += 0.2

        return min(risk, 1.0)

    async def execute_with_protection(
        self,
        tx_params: Dict[str, Any],
        sandwich_risk_threshold: float = 0.5
    ) -> Dict[str, Any]:
        """
        Execute a transaction with MEV protection.

        Automatically chooses the best protection method based on
        sandwich risk and current network conditions.
        """
        # Estimate sandwich risk
        sandwich_risk = self.estimate_sandwich_risk(
            token_pair=tx_params.get('token_pair', 'unknown'),
            amount_in=tx_params.get('value', 0),
            expected_slippage=tx_params.get('slippage', 0),
            pool_liquidity=tx_params.get('pool_liquidity', 0)
        )

        result = {
            "tx_hash": None,
            "method": None,
            "sandwich_risk": sandwich_risk,
            "gas_used": None,
            "effective_gas_price": None,
        }

        if sandwich_risk > sandwich_risk_threshold and self.config.use_flashbots:
            # High risk - use Flashbots bundle
            logger.info(f"High sandwich risk ({sandwich_risk:.2f}), using Flashbots")

            if not self.account:
                raise ValueError("Account required for Flashbots")

            signed_tx = self.w3.eth.account.sign_transaction(
                tx_params,
                self.account.key
            )

            # Create and submit bundle
            bundle = await self.create_bundle([tx_params])
            bundle_result = await self.submit_bundle(bundle)

            if bundle_result.status == "PENDING":
                # Wait for inclusion
                inclusion = await self.wait_for_bundle_inclusion(
                    bundle_result.bundle_hash
                )

                result["tx_hash"] = bundle_result.transactions[0] if bundle_result.transactions else None
                result["method"] = "flashbots_bundle"
                result["bundle_hash"] = bundle_result.bundle_hash
                result["status"] = inclusion.status

        elif self.config.use_private_tx:
            # Medium risk - use private transaction
            logger.info(f"Medium sandwich risk ({sandwich_risk:.2f}), using private tx")

            if not self.account:
                raise ValueError("Account required for private tx")

            signed_tx = self.w3.eth.account.sign_transaction(
                tx_params,
                self.account.key
            )

            tx_hash = await self.send_private_transaction(signed_tx)

            result["tx_hash"] = tx_hash
            result["method"] = "private_transaction"
            result["status"] = "PENDING"

        else:
            # Low risk or no protection - public mempool
            logger.info(f"Low sandwich risk ({sandwich_risk:.2f}), using public mempool")

            if self.account:
                signed_tx = self.w3.eth.account.sign_transaction(
                    tx_params,
                    self.account.key
                )
                tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            else:
                # Simulation mode
                tx_hash = f"sim_{int(time.time())}"

            result["tx_hash"] = tx_hash.hex() if hasattr(tx_hash, 'hex') else str(tx_hash)
            result["method"] = "public_mempool"
            result["status"] = "PENDING"

        return result

    def get_protection_stats(self) -> Dict[str, Any]:
        """Get MEV protection statistics"""
        return {
            "total_bundles_submitted": self.total_bundles_submitted,
            "total_bundles_included": self.total_bundles_included,
            "total_bundles_failed": self.total_bundles_failed,
            "success_rate": (
                self.total_bundles_included / self.total_bundles_submitted * 100
                if self.total_bundles_submitted > 0 else 0
            ),
            "pending_bundles": len(self.pending_bundles),
            "config": {
                "use_flashbots": self.config.use_flashbots,
                "use_private_tx": self.config.use_private_tx,
                "priority_fee_premium": self.config.priority_fee_premium,
            }
        }


class TransactionQueue:
    """
    Priority queue for transactions with MEV protection.

    Queues transactions and batches them into bundles for
    optimal execution.
    """

    def __init__(self, mev_protector: MEVProtector):
        self.mev_protector = mev_protector
        self.queue: List[Dict[str, Any]] = []
        self.processing = False

    async def add_transaction(
        self,
        tx_params: Dict[str, Any],
        priority: int = 0,
        callback: Optional[Callable] = None
    ):
        """Add transaction to queue"""
        item = {
            "tx_params": tx_params,
            "priority": priority,
            "callback": callback,
            "timestamp": time.time(),
        }
        self.queue.append(item)
        self.queue.sort(key=lambda x: x["priority"], reverse=True)

        # Start processing if not already running
        if not self.processing:
            asyncio.create_task(self._process_queue())

    async def _process_queue(self):
        """Process queued transactions"""
        self.processing = True

        try:
            while self.queue:
                # Get batch of transactions
                batch = self.queue[:10]  # Process up to 10 at a time
                self.queue = self.queue[10:]

                # Create bundle
                txs = [item["tx_params"] for item in batch]

                try:
                    bundle = await self.mev_protector.create_bundle(txs)
                    result = await self.mev_protector.submit_bundle(bundle)

                    # Call callbacks
                    for item in batch:
                        if item.get("callback"):
                            await item["callback"](result)

                except Exception as e:
                    logger.error(f"Failed to process batch: {e}")
                    # Re-queue failed transactions
                    self.queue.extend(batch)

                await asyncio.sleep(1)

        finally:
            self.processing = False

    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        return {
            "queue_length": len(self.queue),
            "processing": self.processing,
            "high_priority": len([i for i in self.queue if i["priority"] > 5]),
        }
