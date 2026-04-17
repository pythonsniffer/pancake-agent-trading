// ============================================
// Shared Types for Pancake Trading Agent
// ============================================

// ============================================
// Enums
// ============================================

export enum Chain {
  BSC = 'bsc',
  ETHEREUM = 'ethereum',
  ARBITRUM = 'arbitrum',
  POLYGON = 'polygon'
}

export enum TradeStatus {
  PENDING = 'PENDING',
  SUCCESS = 'SUCCESS',
  FAILED = 'FAILED',
  CANCELLED = 'CANCELLED',
  SIMULATED = 'SIMULATED'
}

export enum TradeStrategy {
  ARBITRAGE = 'ARBITRAGE',
  TREND_FOLLOWING = 'TREND_FOLLOWING',
  MEAN_REVERSION = 'MEAN_REVERSION',
  LP_YIELD = 'LP_YIELD',
  MOMENTUM = 'MOMENTUM'
}

export enum AgentStatus {
  IDLE = 'IDLE',
  RUNNING = 'RUNNING',
  PAUSED = 'PAUSED',
  ERROR = 'ERROR',
  STOPPED = 'STOPPED'
}

export enum AgentType {
  MARKET_INTELLIGENCE = 'MARKET_INTELLIGENCE',
  STRATEGY = 'STRATEGY',
  EXECUTION = 'EXECUTION',
  RISK_MANAGEMENT = 'RISK_MANAGEMENT',
  PORTFOLIO = 'PORTFOLIO',
  LIQUIDITY_ANALYSIS = 'LIQUIDITY_ANALYSIS',
  BACKTEST = 'BACKTEST'
}

export enum PoolCategory {
  BLUE_CHIP = 'BLUE_CHIP',
  MID_CAP = 'MID_CAP',
  DEGEN = 'DEGEN',
  UNKNOWN = 'UNKNOWN'
}

export enum RiskLevel {
  LOW = 'LOW',
  MEDIUM = 'MEDIUM',
  HIGH = 'HIGH',
  CRITICAL = 'CRITICAL'
}

export enum SignalType {
  BUY = 'BUY',
  SELL = 'SELL',
  HOLD = 'HOLD',
  ARBITRAGE = 'ARBITRAGE'
}

// ============================================
// Core Interfaces
// ============================================

export interface Token {
  address: string;
  symbol: string;
  name: string;
  decimals: number;
  chain: Chain;
  logoURI?: string;
  priceUsd?: number;
  marketCap?: number;
  volume24h?: number;
}

export interface Pool {
  address: string;
  chain: Chain;
  dex: string;
  version: 'V2' | 'V3';
  token0: Token;
  token1: Token;
  reserve0: string;
  reserve1: string;
  totalSupply?: string;
  tvlUsd: number;
  volume24hUsd?: number;
  feeTier?: number;
  feeRate: number;
  price0?: number;
  price1?: number;
  category: PoolCategory;
  apr24h?: number;
  impermanentLoss24h?: number;
  createdAt: Date;
  lastUpdated: Date;
}

export interface PriceUpdate {
  poolAddress: string;
  token0: string;
  token1: string;
  reserve0: string;
  reserve1: string;
  price0: number;
  price1: number;
  timestamp: number;
  blockNumber: number;
  volume?: number;
}

export interface MarketSnapshot {
  id?: string;
  timestamp: number;
  blockNumber: number;
  chain: Chain;
  poolAddress: string;
  token0Price: number;
  token1Price: number;
  reserve0: string;
  reserve1: string;
  volume24h: number;
  volatility: number;
  liquidityDepth: number;
}

// ============================================
// Trade Interfaces
// ============================================

export interface TradeSignal {
  id: string;
  type: SignalType;
  strategy: TradeStrategy;
  chain: Chain;
  tokenIn: Token;
  tokenOut: Token;
  amountIn: string;
  amountOutMin?: string;
  expectedProfit: number;
  expectedProfitPercent: number;
  confidence: number;
  slippageTolerance: number;
  deadline: number;
  gasEstimate?: number;
  gasPrice?: string;
  buyPool?: Pool;
  sellPool?: Pool;
  stopLoss?: number;
  takeProfit?: number;
  metadata?: Record<string, any>;
  timestamp: number;
  agentId: string;
}

export interface TradeExecution {
  id: string;
  signalId: string;
  status: TradeStatus;
  chain: Chain;
  strategy: TradeStrategy;
  tokenIn: Token;
  tokenOut: Token;
  amountIn: string;
  amountOut?: string;
  poolAddress?: string;
  txHash?: string;
  blockNumber?: number;
  gasUsed?: string;
  gasPrice?: string;
  gasCostUsd?: number;
  priceExecuted?: number;
  profitUsd?: number;
  profitPercent?: number;
  slippage?: number;
  errorMessage?: string;
  executionTimeMs?: number;
  timestamp: number;
  confirmedAt?: number;
}

export interface TradeReceipt {
  txHash: string;
  status: boolean;
  blockNumber: number;
  gasUsed: string;
  gasPrice: string;
  effectiveGasPrice: string;
  logs: any[];
  events?: any[];
}

// ============================================
// Agent Interfaces
// ============================================

export interface Agent {
  id: string;
  type: AgentType;
  name: string;
  status: AgentStatus;
  config: AgentConfig;
  memory?: AgentMemory;
  lastAction?: string;
  lastActionAt?: number;
  errorCount: number;
  successCount: number;
  metadata?: Record<string, any>;
}

export interface AgentConfig {
  enabled: boolean;
  intervalMs?: number;
  maxConcurrentTasks?: number;
  retryAttempts?: number;
  timeoutMs?: number;
  params: Record<string, any>;
}

export interface AgentMemory {
  shortTerm: any[];
  longTerm: string[];
  vectorStoreId?: string;
}

export interface AgentAction {
  id: string;
  agentId: string;
  agentType: AgentType;
  action: string;
  input: any;
  output?: any;
  confidence: number;
  status: 'SUCCESS' | 'FAILED' | 'PENDING';
  timestamp: number;
  durationMs?: number;
  error?: string;
}

export interface AgentState {
  agentId: string;
  status: AgentStatus;
  currentTask?: string;
  queue: string[];
  results: any[];
  errors: any[];
  lastUpdated: number;
}

// ============================================
// Risk Management Interfaces
// ============================================

export interface RiskConfig {
  maxPositionSizeUsd: number;
  maxPortfolioExposurePercent: number;
  maxDailyLossUsd: number;
  maxDrawdownPercent: number;
  stopLossPercent: number;
  takeProfitPercent: number;
  maxGasPriceGwei: number;
  minProfitThresholdUsd: number;
  circuitBreakerEnabled: boolean;
  circuitBreakerThreshold: number;
  maxSlippagePercent: number;
  exposurePerToken: Record<string, number>;
}

export interface RiskAssessment {
  signalId: string;
  approved: boolean;
  riskScore: number;
  riskLevel: RiskLevel;
  checks: RiskCheck[];
  timestamp: number;
}

export interface RiskCheck {
  name: string;
  passed: boolean;
  message?: string;
  severity?: RiskLevel;
}

export interface CircuitBreakerState {
  triggered: boolean;
  triggeredAt?: number;
  reason?: string;
  resetAt?: number;
}

// ============================================
// Portfolio Interfaces
// ============================================

export interface Portfolio {
  id: string;
  chain: Chain;
  totalValueUsd: number;
  availableBalanceUsd: number;
  allocatedBalanceUsd: number;
  tokens: PortfolioToken[];
  positions: Position[];
  timestamp: number;
}

export interface PortfolioToken {
  token: Token;
  balance: string;
  balanceUsd: number;
  allocationPercent: number;
}

export interface Position {
  id: string;
  tradeId: string;
  token: Token;
  entryPrice: number;
  currentPrice?: number;
  amount: string;
  valueUsd: number;
  unrealizedPnl?: number;
  unrealizedPnlPercent?: number;
  stopLoss?: number;
  takeProfit?: number;
  openedAt: number;
  closedAt?: number;
}

export interface PortfolioMetrics {
  totalValueUsd: number;
  totalPnlUsd: number;
  totalPnlPercent: number;
  realizedPnlUsd: number;
  unrealizedPnlUsd: number;
  totalTrades: number;
  winningTrades: number;
  losingTrades: number;
  winRate: number;
  avgProfitUsd: number;
  avgLossUsd: number;
  profitFactor: number;
  sharpeRatio: number;
  maxDrawdownPercent: number;
  totalGasCostUsd: number;
  timestamp: number;
}

export interface PortfolioSnapshot {
  id?: string;
  timestamp: number;
  totalValueUsd: number;
  totalPnlUsd: number;
  winRate: number;
  totalTrades: number;
  totalGasUsd: number;
  metrics: PortfolioMetrics;
}

// ============================================
// Strategy Interfaces
// ============================================

export interface Strategy {
  id: string;
  name: string;
  type: TradeStrategy;
  enabled: boolean;
  config: StrategyConfig;
  performance?: StrategyPerformance;
}

export interface StrategyConfig {
  minProfitThreshold: number;
  maxSlippage: number;
  positionSizing: 'FIXED' | 'PERCENTAGE' | 'KELLY';
  positionSize: number;
  stopLoss?: number;
  takeProfit?: number;
  timeInForce?: number;
  customParams: Record<string, any>;
}

export interface StrategyPerformance {
  totalTrades: number;
  winningTrades: number;
  losingTrades: number;
  winRate: number;
  totalProfitUsd: number;
  avgProfitUsd: number;
  avgLossUsd: number;
  profitFactor: number;
  maxDrawdownPercent: number;
  lastUpdated: number;
}

// ============================================
// Backtesting Interfaces
// ============================================

export interface BacktestConfig {
  strategy: TradeStrategy;
  startDate: number;
  endDate: number;
  initialCapital: number;
  chains: Chain[];
  tokenPairs: string[][];
  slippage: number;
  gasPrice: number;
  feeTier: number;
  parameters: Record<string, any>;
}

export interface BacktestResult {
  id: string;
  config: BacktestConfig;
  trades: TradeExecution[];
  metrics: BacktestMetrics;
  equityCurve: EquityPoint[];
  timestamp: number;
}

export interface BacktestMetrics {
  initialCapital: number;
  finalCapital: number;
  totalReturn: number;
  totalReturnPercent: number;
  totalTrades: number;
  winningTrades: number;
  losingTrades: number;
  winRate: number;
  avgProfit: number;
  avgLoss: number;
  profitFactor: number;
  sharpeRatio: number;
  sortinoRatio: number;
  maxDrawdown: number;
  maxDrawdownPercent: number;
  volatility: number;
  calmarRatio: number;
  totalFees: number;
  totalGasCost: number;
}

export interface EquityPoint {
  timestamp: number;
  value: number;
  trade?: TradeExecution;
}

// ============================================
// Market Data Interfaces
// ============================================

export interface Candle {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface OrderBook {
  poolAddress: string;
  token0: string;
  token1: string;
  bids: OrderBookEntry[];
  asks: OrderBookEntry[];
  timestamp: number;
}

export interface OrderBookEntry {
  price: number;
  amount: string;
  total: number;
}

export interface WhaleTransaction {
  txHash: string;
  type: 'BUY' | 'SELL';
  token: string;
  amount: string;
  amountUsd: number;
  wallet: string;
  timestamp: number;
  blockNumber: number;
}

// ============================================
// Vector Memory Interfaces
// ============================================

export interface VectorMemory {
  id: string;
  agentId: string;
  content: string;
  embedding?: number[];
  metadata: Record<string, any>;
  timestamp: number;
  relevanceScore?: number;
}

export interface MemoryQuery {
  query: string;
  agentId?: string;
  topK?: number;
  filter?: Record<string, any>;
}

export interface MemoryQueryResult {
  memories: VectorMemory[];
  query: string;
  totalResults: number;
}

// ============================================
// API/WebSocket Interfaces
// ============================================

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: ApiError;
  meta?: ApiMeta;
}

export interface ApiError {
  code: string;
  message: string;
  details?: any;
}

export interface ApiMeta {
  page?: number;
  limit?: number;
  total?: number;
  timestamp: number;
}

export interface WebSocketMessage {
  type: string;
  channel: string;
  data: any;
  timestamp: number;
}

// ============================================
// Configuration Interfaces
// ============================================

export interface ChainConfig {
  chainId: number;
  name: string;
  rpcUrl: string;
  wsUrl?: string;
  explorerUrl: string;
  nativeCurrency: {
    name: string;
    symbol: string;
    decimals: number;
  };
  contracts: {
    factoryV2: string;
    factoryV3: string;
    routerV2: string;
    routerV3: string;
    multicall: string;
  };
  testnet: boolean;
}

export interface AppConfig {
  environment: 'development' | 'staging' | 'production';
  database: {
    url: string;
  };
  redis: {
    url: string;
  };
  chroma: {
    url: string;
  };
  chains: Record<Chain, ChainConfig>;
  risk: RiskConfig;
  agents: Record<AgentType, AgentConfig>;
}

// ============================================
// Utility Types
// ============================================

export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;

export type RequiredFields<T, K extends keyof T> = T & Required<Pick<T, K>>;

export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};

export type EventCallback<T> = (data: T) => void | Promise<void>;
