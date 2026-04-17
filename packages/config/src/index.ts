import { Chain } from '@pancake/shared-types';

export * from './chains';
export * from './tokens';
export * from './abis';

// Default configuration values
export const DEFAULT_CONFIG = {
  // Trading parameters
  MIN_PROFIT_USD: 1.0,
  MAX_SLIPPAGE_PERCENT: 0.5,
  DEFAULT_DEADLINE_MINUTES: 5,
  GAS_LIMIT_MULTIPLIER: 1.2,

  // Risk parameters
  MAX_POSITION_SIZE_USD: 500,
  MAX_PORTFOLIO_EXPOSURE_PERCENT: 20,
  STOP_LOSS_PERCENT: 5,
  TAKE_PROFIT_PERCENT: 10,
  MAX_DAILY_LOSS_USD: 100,
  CIRCUIT_BREAKER_THRESHOLD: 10,

  // Agent parameters
  MARKET_INTELLIGENCE_INTERVAL_MS: 2000,
  STRATEGY_INTERVAL_MS: 5000,
  RISK_CHECK_INTERVAL_MS: 1000,
  PORTFOLIO_SNAPSHOT_INTERVAL_MS: 60000,
  LIQUIDITY_SCAN_INTERVAL_MS: 300000,

  // Memory parameters
  VECTOR_MEMORY_TOP_K: 5,
  MEMORY_SIMILARITY_THRESHOLD: 0.7,

  // API parameters
  API_PORT: 8000,
  WS_PORT: 8001,

  // Blockchain parameters
  CONFIRMATION_BLOCKS: 1,
  MAX_GAS_PRICE_GWEI: 50,

  // Cache parameters
  PRICE_CACHE_TTL_SECONDS: 10,
  POOL_CACHE_TTL_SECONDS: 300,
};

// Network-specific gas parameters
export const GAS_CONFIG = {
  [Chain.BSC]: {
    defaultGasLimit: 300000,
    maxPriorityFeePerGas: '5000000000', // 5 gwei
    maxFeePerGas: '10000000000', // 10 gwei
  },
  [Chain.ETHEREUM]: {
    defaultGasLimit: 300000,
    maxPriorityFeePerGas: '1500000000', // 1.5 gwei
    maxFeePerGas: '50000000000', // 50 gwei
  },
  [Chain.ARBITRUM]: {
    defaultGasLimit: 300000,
    maxPriorityFeePerGas: '100000000', // 0.1 gwei
    maxFeePerGas: '1000000000', // 1 gwei
  },
};

export const getGasConfig = (chain: Chain) => {
  return GAS_CONFIG[chain] || GAS_CONFIG[Chain.BSC];
};
