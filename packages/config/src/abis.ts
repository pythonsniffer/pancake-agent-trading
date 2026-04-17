// PancakeSwap V2 ABI snippets
export const FACTORY_V2_ABI = [
  'function allPairsLength() external view returns (uint256)',
  'function allPairs(uint256) external view returns (address)',
  'function getPair(address tokenA, address tokenB) external view returns (address pair)',
  'event PairCreated(address indexed token0, address indexed token1, address pair, uint256)',
];

export const PAIR_V2_ABI = [
  'function getReserves() external view returns (uint112 reserve0, uint112 reserve1, uint32 blockTimestampLast)',
  'function token0() external view returns (address)',
  'function token1() external view returns (address)',
  'function totalSupply() external view returns (uint256)',
  'function balanceOf(address owner) external view returns (uint256)',
  'function approve(address spender, uint256 value) external returns (bool)',
  'function transfer(address to, uint256 value) external returns (bool)',
  'function transferFrom(address from, address to, uint256 value) external returns (bool)',
  'event Swap(address indexed sender, uint256 amount0In, uint256 amount1In, uint256 amount0Out, uint256 amount1Out, address indexed to)',
  'event Sync(uint112 reserve0, uint112 reserve1)',
];

export const ROUTER_V2_ABI = [
  'function swapExactTokensForTokens(uint256 amountIn, uint256 amountOutMin, address[] calldata path, address to, uint256 deadline) external returns (uint256[] memory amounts)',
  'function swapExactETHForTokens(uint256 amountOutMin, address[] calldata path, address to, uint256 deadline) external payable returns (uint256[] memory amounts)',
  'function swapExactTokensForETH(uint256 amountIn, uint256 amountOutMin, address[] calldata path, address to, uint256 deadline) external returns (uint256[] memory amounts)',
  'function getAmountsOut(uint256 amountIn, address[] calldata path) external view returns (uint256[] memory amounts)',
  'function getAmountsIn(uint256 amountOut, address[] calldata path) external view returns (uint256[] memory amounts)',
  'function addLiquidity(address tokenA, address tokenB, uint256 amountADesired, uint256 amountBDesired, uint256 amountAMin, uint256 amountBMin, address to, uint256 deadline) external returns (uint256 amountA, uint256 amountB, uint256 liquidity)',
  'function removeLiquidity(address tokenA, address tokenB, uint256 liquidity, uint256 amountAMin, uint256 amountBMin, address to, uint256 deadline) external returns (uint256 amountA, uint256 amountB)',
];

// PancakeSwap V3 ABI snippets
export const FACTORY_V3_ABI = [
  'function getPool(address tokenA, address tokenB, uint24 fee) external view returns (address pool)',
  'function allPools(uint256) external view returns (address)',
  'function allPoolsLength() external view returns (uint256)',
];

export const POOL_V3_ABI = [
  'function slot0() external view returns (uint160 sqrtPriceX96, int24 tick, uint16 observationIndex, uint16 observationCardinality, uint16 observationCardinalityNext, uint8 feeProtocol, bool unlocked)',
  'function liquidity() external view returns (uint128)',
  'function token0() external view returns (address)',
  'function token1() external view returns (address)',
  'function fee() external view returns (uint24)',
  'function tickSpacing() external view returns (int24)',
  'function ticks(int24 tick) external view returns (uint128 liquidityGross, int128 liquidityNet, uint256 feeGrowthOutside0X128, uint256 feeGrowthOutside1X128, int56 tickCumulativeOutside, uint160 secondsPerLiquidityOutsideX128, uint32 secondsOutside, bool initialized)',
];

export const ROUTER_V3_ABI = [
  'function exactInputSingle((address tokenIn, address tokenOut, uint24 fee, address recipient, uint256 deadline, uint256 amountIn, uint256 amountOutMinimum, uint160 sqrtPriceLimitX96)) external payable returns (uint256 amountOut)',
  'function exactInput((bytes path, address recipient, uint256 deadline, uint256 amountIn, uint256 amountOutMinimum)) external payable returns (uint256 amountOut)',
  'function multicall(uint256 deadline, bytes[] calldata data) external payable returns (bytes[] memory results)',
];

// ERC20 Standard ABI
export const ERC20_ABI = [
  'function name() external view returns (string memory)',
  'function symbol() external view returns (string memory)',
  'function decimals() external view returns (uint8)',
  'function totalSupply() external view returns (uint256)',
  'function balanceOf(address owner) external view returns (uint256)',
  'function allowance(address owner, address spender) external view returns (uint256)',
  'function approve(address spender, uint256 value) external returns (bool)',
  'function transfer(address to, uint256 value) external returns (bool)',
  'function transferFrom(address from, address to, uint256 value) external returns (bool)',
  'event Transfer(address indexed from, address indexed to, uint256 value)',
  'event Approval(address indexed owner, address indexed spender, uint256 value)',
];

// Multicall ABI
export const MULTICALL_ABI = [
  'function aggregate(tuple(address target, bytes callData)[] calls) external view returns (uint256 blockNumber, bytes[] returnData)',
  'function tryAggregate(bool requireSuccess, tuple(address target, bytes callData)[] calls) external view returns (tuple(bool success, bytes returnData)[] returnData)',
  'function getBlockNumber() external view returns (uint256)',
  'function getCurrentBlockTimestamp() external view returns (uint256)',
  'function getEthBalance(address addr) external view returns (uint256)',
];

// Price Oracle ABI (Chainlink style)
export const PRICE_FEED_ABI = [
  'function latestRoundData() external view returns (uint80 roundId, int256 answer, uint256 startedAt, uint256 updatedAt, uint80 answeredInRound)',
  'function decimals() external view returns (uint8)',
  'function description() external view returns (string memory)',
];

// MasterChef ABI for yield farming
export const MASTERCHEF_ABI = [
  'function poolLength() external view returns (uint256)',
  'function poolInfo(uint256) external view returns (address lpToken, uint256 allocPoint, uint256 lastRewardBlock, uint256 accCakePerShare)',
  'function userInfo(uint256, address) external view returns (uint256 amount, uint256 rewardDebt)',
  'function pendingCake(uint256, address) external view returns (uint256)',
  'function deposit(uint256 _pid, uint256 _amount) external',
  'function withdraw(uint256 _pid, uint256 _amount) external',
  'function emergencyWithdraw(uint256 _pid) external',
];

// Aggregator for all PancakeSwap ABIs
export const PANCAKESWAP_ABIS = {
  factoryV2: FACTORY_V2_ABI,
  factoryV3: FACTORY_V3_ABI,
  pairV2: PAIR_V2_ABI,
  poolV3: POOL_V3_ABI,
  routerV2: ROUTER_V2_ABI,
  routerV3: ROUTER_V3_ABI,
  erc20: ERC20_ABI,
  multicall: MULTICALL_ABI,
  priceFeed: PRICE_FEED_ABI,
  masterChef: MASTERCHEF_ABI,
};
