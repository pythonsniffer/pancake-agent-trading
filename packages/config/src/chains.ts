import { Chain, ChainConfig } from '@pancake/shared-types';

export const CHAIN_CONFIGS: Record<Chain, ChainConfig> = {
  [Chain.BSC]: {
    chainId: 56,
    name: 'BNB Smart Chain',
    rpcUrl: process.env.BSC_RPC_URL || 'https://bsc-dataseed.binance.org/',
    wsUrl: process.env.BSC_WS_URL || 'wss://bsc-ws-node.nariox.org:443',
    explorerUrl: 'https://bscscan.com',
    nativeCurrency: {
      name: 'BNB',
      symbol: 'BNB',
      decimals: 18,
    },
    contracts: {
      factoryV2: '0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73',
      factoryV3: '0x0BFbCF9fa4f9C56B0F40a671Ad40E0805A091865',
      routerV2: '0x10ED43C718714eb63d5aA57B78B54704E256024E',
      routerV3: '0x13f4EA83D0bd40E75C8222255bc965a6f0725e5B',
      multicall: '0xcA11bde05977b3631167028862bE2a173976CA11',
    },
    testnet: false,
  },
  [Chain.BSC_TESTNET]: {
    chainId: 97,
    name: 'BNB Smart Chain Testnet',
    rpcUrl: process.env.BSC_TESTNET_RPC_URL || 'https://data-seed-prebsc-1-s1.binance.org:8545/',
    wsUrl: process.env.BSC_TESTNET_WS_URL,
    explorerUrl: 'https://testnet.bscscan.com',
    nativeCurrency: {
      name: 'tBNB',
      symbol: 'tBNB',
      decimals: 18,
    },
    contracts: {
      factoryV2: '0x6725F303b657a9451d4858CBd5567Dd06d96D2Be',
      factoryV3: '0x0BFbCF9fa4f9C56B0F40a671Ad40E0805A091865',
      routerV2: '0xD99D1c33F9fC3444f8101754aBC46c52416550D1',
      routerV3: '0x9a489505a00cE272eAa5e07Dba6491314CaE3796',
      multicall: '0xcA11bde05977b3631167028862bE2a173976CA11',
    },
    testnet: true,
  },
  [Chain.ETHEREUM]: {
    chainId: 1,
    name: 'Ethereum Mainnet',
    rpcUrl: process.env.ETH_RPC_URL || 'https://eth.llamarpc.com',
    wsUrl: process.env.ETH_WS_URL,
    explorerUrl: 'https://etherscan.io',
    nativeCurrency: {
      name: 'Ether',
      symbol: 'ETH',
      decimals: 18,
    },
    contracts: {
      factoryV2: '0x109705A13a9E8B8D0446b7BC85FF94469fF657d9',
      factoryV3: '0x0BFbCF9fa4f9C56B0F40a671Ad40E0805A091865',
      routerV2: '0xEfF92A1d27F91b5c5060159f56fB8f058E0C6B0F',
      routerV3: '0x13f4EA83D0bd40E75C8222255bc965a6f0725e5B',
      multicall: '0xcA11bde05977b3631167028862bE2a173976CA11',
    },
    testnet: false,
  },
  [Chain.ARBITRUM]: {
    chainId: 42161,
    name: 'Arbitrum One',
    rpcUrl: process.env.ARB_RPC_URL || 'https://arb1.arbitrum.io/rpc',
    wsUrl: process.env.ARB_WS_URL,
    explorerUrl: 'https://arbiscan.io',
    nativeCurrency: {
      name: 'Ether',
      symbol: 'ETH',
      decimals: 18,
    },
    contracts: {
      factoryV2: '0x02a84c1b3BBD28eed8e961cD7D93c178E4B84dAe',
      factoryV3: '0x0BFbCF9fa4f9C56B0F40a671Ad40E0805A091865',
      routerV2: '0x8cFe3277c5051e0Fd15313fC1C0f80E168d8D5e6',
      routerV3: '0x13f4EA83D0bd40E75C8222255bc965a6f0725e5B',
      multicall: '0xcA11bde05977b3631167028862bE2a173976CA11',
    },
    testnet: false,
  },
};

export const getChainConfig = (chain: Chain): ChainConfig => {
  const config = CHAIN_CONFIGS[chain];
  if (!config) {
    throw new Error(`No configuration found for chain: ${chain}`);
  }
  return config;
};

export const getRpcUrl = (chain: Chain): string => {
  return getChainConfig(chain).rpcUrl;
};

export const getChainId = (chain: Chain): number => {
  return getChainConfig(chain).chainId;
};

export const isTestnet = (chain: Chain): boolean => {
  return getChainConfig(chain).testnet;
};

export const SUPPORTED_CHAINS = [Chain.BSC, Chain.ETHEREUM, Chain.ARBITRUM];
