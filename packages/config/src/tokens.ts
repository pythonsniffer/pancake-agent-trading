import { Token, Chain, PoolCategory } from '@pancake/shared-types';

export const NATIVE_TOKENS: Record<Chain, Token> = {
  [Chain.BSC]: {
    address: '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c', // WBNB
    symbol: 'BNB',
    name: 'Wrapped BNB',
    decimals: 18,
    chain: Chain.BSC,
    logoURI: 'https://tokens.pancakeswap.finance/images/symbol/bnb.png',
  },
  [Chain.ETHEREUM]: {
    address: '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2', // WETH
    symbol: 'ETH',
    name: 'Wrapped Ether',
    decimals: 18,
    chain: Chain.ETHEREUM,
    logoURI: 'https://tokens.pancakeswap.finance/images/symbol/eth.png',
  },
  [Chain.ARBITRUM]: {
    address: '0x82aF49447D8a07e3bd95BD0d56f35241523fBab1', // WETH
    symbol: 'ETH',
    name: 'Wrapped Ether',
    decimals: 18,
    chain: Chain.ARBITRUM,
    logoURI: 'https://tokens.pancakeswap.finance/images/symbol/eth.png',
  },
};

export const STABLE_COINS: Record<Chain, Token[]> = {
  [Chain.BSC]: [
    {
      address: '0x55d398326f99059fF775485246999027B3197955',
      symbol: 'USDT',
      name: 'Tether USD',
      decimals: 18,
      chain: Chain.BSC,
      logoURI: 'https://tokens.pancakeswap.finance/images/symbol/usdt.png',
    },
    {
      address: '0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d',
      symbol: 'USDC',
      name: 'USD Coin',
      decimals: 18,
      chain: Chain.BSC,
      logoURI: 'https://tokens.pancakeswap.finance/images/symbol/usdc.png',
    },
    {
      address: '0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56',
      symbol: 'BUSD',
      name: 'Binance USD',
      decimals: 18,
      chain: Chain.BSC,
      logoURI: 'https://tokens.pancakeswap.finance/images/symbol/busd.png',
    },
  ],
  [Chain.ETHEREUM]: [
    {
      address: '0xdAC17F958D2ee523a2206206994597C13D831ec7',
      symbol: 'USDT',
      name: 'Tether USD',
      decimals: 6,
      chain: Chain.ETHEREUM,
      logoURI: 'https://tokens.pancakeswap.finance/images/symbol/usdt.png',
    },
    {
      address: '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
      symbol: 'USDC',
      name: 'USD Coin',
      decimals: 6,
      chain: Chain.ETHEREUM,
      logoURI: 'https://tokens.pancakeswap.finance/images/symbol/usdc.png',
    },
    {
      address: '0x6B175474E89094C44Da98b954EedeAC495271d0F',
      symbol: 'DAI',
      name: 'Dai Stablecoin',
      decimals: 18,
      chain: Chain.ETHEREUM,
      logoURI: 'https://tokens.pancakeswap.finance/images/symbol/dai.png',
    },
  ],
  [Chain.ARBITRUM]: [
    {
      address: '0xFd086bC7CD5C481DCC9C85ebE478A1C0b3F7C5d5',
      symbol: 'USDT',
      name: 'Tether USD',
      decimals: 6,
      chain: Chain.ARBITRUM,
      logoURI: 'https://tokens.pancakeswap.finance/images/symbol/usdt.png',
    },
    {
      address: '0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8',
      symbol: 'USDC',
      name: 'USD Coin',
      decimals: 6,
      chain: Chain.ARBITRUM,
      logoURI: 'https://tokens.pancakeswap.finance/images/symbol/usdc.png',
    },
  ],
};

export const BLUE_CHIP_TOKENS: Record<Chain, Token[]> = {
  [Chain.BSC]: [
    {
      address: '0x2170Ed0880ac9A755fd29B2688956BD959F933F8',
      symbol: 'ETH',
      name: 'Ethereum Token',
      decimals: 18,
      chain: Chain.BSC,
      logoURI: 'https://tokens.pancakeswap.finance/images/symbol/eth.png',
    },
    {
      address: '0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c',
      symbol: 'BTCB',
      name: 'Bitcoin BEP2',
      decimals: 18,
      chain: Chain.BSC,
      logoURI: 'https://tokens.pancakeswap.finance/images/symbol/btcb.png',
    },
    {
      address: '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c',
      symbol: 'WBNB',
      name: 'Wrapped BNB',
      decimals: 18,
      chain: Chain.BSC,
      logoURI: 'https://tokens.pancakeswap.finance/images/symbol/wbnb.png',
    },
    {
      address: '0xB8c77482e45F1F44dE1745F52C74426C631bDD52',
      symbol: 'BNB',
      name: 'Binance Coin',
      decimals: 18,
      chain: Chain.BSC,
      logoURI: 'https://tokens.pancakeswap.finance/images/symbol/bnb.png',
    },
  ],
  [Chain.ETHEREUM]: [
    {
      address: '0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599',
      symbol: 'WBTC',
      name: 'Wrapped BTC',
      decimals: 8,
      chain: Chain.ETHEREUM,
      logoURI: 'https://tokens.pancakeswap.finance/images/symbol/wbtc.png',
    },
    {
      address: '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
      symbol: 'WETH',
      name: 'Wrapped Ether',
      decimals: 18,
      chain: Chain.ETHEREUM,
      logoURI: 'https://tokens.pancakeswap.finance/images/symbol/weth.png',
    },
  ],
  [Chain.ARBITRUM]: [
    {
      address: '0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f',
      symbol: 'WBTC',
      name: 'Wrapped BTC',
      decimals: 8,
      chain: Chain.ARBITRUM,
      logoURI: 'https://tokens.pancakeswap.finance/images/symbol/wbtc.png',
    },
    {
      address: '0x82aF49447D8a07e3bd95BD0d56f35241523fBab1',
      symbol: 'WETH',
      name: 'Wrapped Ether',
      decimals: 18,
      chain: Chain.ARBITRUM,
      logoURI: 'https://tokens.pancakeswap.finance/images/symbol/weth.png',
    },
  ],
};

export const POPULAR_TOKENS: Record<Chain, Token[]> = {
  [Chain.BSC]: [
    ...BLUE_CHIP_TOKENS[Chain.BSC],
    ...STABLE_COINS[Chain.BSC],
    {
      address: '0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82',
      symbol: 'CAKE',
      name: 'PancakeSwap Token',
      decimals: 18,
      chain: Chain.BSC,
      logoURI: 'https://tokens.pancakeswap.finance/images/symbol/cake.png',
    },
  ],
  [Chain.ETHEREUM]: [
    ...BLUE_CHIP_TOKENS[Chain.ETHEREUM],
    ...STABLE_COINS[Chain.ETHEREUM],
  ],
  [Chain.ARBITRUM]: [
    ...BLUE_CHIP_TOKENS[Chain.ARBITRUM],
    ...STABLE_COINS[Chain.ARBITRUM],
  ],
};

export const getTokenBySymbol = (chain: Chain, symbol: string): Token | undefined => {
  const tokens = POPULAR_TOKENS[chain];
  return tokens.find(t => t.symbol.toLowerCase() === symbol.toLowerCase());
};

export const getTokenByAddress = (chain: Chain, address: string): Token | undefined => {
  const tokens = POPULAR_TOKENS[chain];
  return tokens.find(t => t.address.toLowerCase() === address.toLowerCase());
};

export const categorizeToken = (token: Token, tvlUsd?: number): PoolCategory => {
  // Check if it's a stable coin
  const isStable = STABLE_COINS[token.chain].some(
    t => t.address.toLowerCase() === token.address.toLowerCase()
  );

  if (isStable) return PoolCategory.BLUE_CHIP;

  // Check if it's a blue chip
  const isBlueChip = BLUE_CHIP_TOKENS[token.chain].some(
    t => t.address.toLowerCase() === token.address.toLowerCase()
  );

  if (isBlueChip) return PoolCategory.BLUE_CHIP;

  // Categorize by TVL if available
  if (tvlUsd !== undefined) {
    if (tvlUsd >= 1_000_000) return PoolCategory.BLUE_CHIP;
    if (tvlUsd >= 100_000) return PoolCategory.MID_CAP;
  }

  return PoolCategory.DEGEN;
};
