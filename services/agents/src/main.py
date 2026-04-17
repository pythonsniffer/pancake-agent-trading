#!/usr/bin/env python3
"""
Main entry point for the Trading Agent Service.
Initializes all components and starts the multi-agent trading system.
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Optional

from web3 import Web3
from dotenv import load_dotenv

from .orchestrator import create_trading_graph
from .state import TradingState

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'logs/agent_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

# Ensure logs directory exists
os.makedirs('logs', exist_ok=True)


def load_config() -> dict:
    """Load configuration from environment"""
    load_dotenv()

    return {
        'bsc_rpc_url': os.getenv('BSC_RPC_URL', 'https://bsc-dataseed.binance.org/'),
        'eth_rpc_url': os.getenv('ETH_RPC_URL'),
        'arb_rpc_url': os.getenv('ARB_RPC_URL'),
        'private_key': os.getenv('PRIVATE_KEY'),
        'openai_api_key': os.getenv('OPENAI_API_KEY'),
        'initial_capital': float(os.getenv('INITIAL_CAPITAL', '10000')),
        'market': {
            'poll_interval': int(os.getenv('MARKET_POLL_INTERVAL', '2')),
            'whale_threshold_usd': float(os.getenv('WHALE_THRESHOLD', '100000')),
        },
        'risk': {
            'max_position_size_usd': float(os.getenv('MAX_POSITION_SIZE', '500')),
            'max_daily_loss_usd': float(os.getenv('MAX_DAILY_LOSS', '100')),
            'circuit_breaker_enabled': os.getenv('CIRCUIT_BREAKER', 'true').lower() == 'true',
        },
        'execution': {
            'simulate_before_execute': os.getenv('SIMULATE_TRADES', 'true').lower() == 'true',
            'deadline_minutes': int(os.getenv('TX_DEADLINE_MINUTES', '5')),
        },
    }


def initialize_web3(config: dict) -> Optional[W3]:
    """Initialize Web3 connection"""
    try:
        w3 = Web3(Web3.HTTPProvider(config['bsc_rpc_url']))

        if w3.is_connected():
            logger.info(f"Connected to BSC - Block: {w3.eth.block_number}")
            return w3
        else:
            logger.warning("Failed to connect to BSC RPC")
            return None

    except Exception as e:
        logger.error(f"Error initializing Web3: {e}")
        return None


async def main():
    """Main function"""
    logger.info("=" * 60)
    logger.info("PancakeSwap AI Trading Agent Service Starting")
    logger.info("=" * 60)

    # Load configuration
    config = load_config()
    logger.info("Configuration loaded")

    # Initialize Web3 (optional - can run in simulation mode)
    w3 = initialize_web3(config)

    if not w3:
        logger.warning("Running in simulation mode - no blockchain connection")
    elif not config.get('private_key'):
        logger.warning("No private key configured - trades will be simulated")

    # Create orchestrator
    orchestrator = create_trading_graph(w3=w3, config=config)
    logger.info("Trading graph created")

    # Initialize state
    await orchestrator.initialize()
    logger.info("Trading state initialized")

    # Run initial cycle
    logger.info("Running initial trading cycle...")
    await orchestrator.run_cycle()

    # Get status
    status = orchestrator.get_status()
    logger.info(f"Initial status: {status}")

    # Start continuous trading
    try:
        await orchestrator.run_continuous(interval_seconds=30)
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
        orchestrator.stop()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        orchestrator.stop()
        raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown complete")
