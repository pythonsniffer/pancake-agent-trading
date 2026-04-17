# Architecture Documentation

## System Overview

The PancakeSwap AI Trading System is a production-grade, multi-agent autonomous trading platform built with a microservices architecture. It leverages LangGraph for agent orchestration, FastAPI for the backend, and Next.js for the frontend.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          Client Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │   Web App    │  │  Mobile App  │  │   Third-party API    │ │
│  │   (Next.js)  │  │   (Future)   │  │      Consumers       │ │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘ │
└─────────┼─────────────────┼────────────────────┼───────────────┘
          │                 │                    │
          └─────────────────┴────────────────────┘
                            │
                    WebSocket/HTTP
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                      Gateway Layer                               │
│                     ┌──────────────┐                            │
│                     │   Nginx/     │                            │
│                     │   Traefik    │                            │
│                     └──────┬───────┘                            │
└────────────────────────────┼────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                      API Layer                                   │
│              ┌─────────────────────────┐                        │
│              │      FastAPI            │                        │
│              │   ┌───────────────┐     │                        │
│              │   │  REST Routes  │     │                        │
│              │   ├───────────────┤     │                        │
│              │   │  WebSocket    │     │                        │
│              │   │    Handler    │     │                        │
│              │   └───────────────┘     │                        │
│              └─────────────────────────┘                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                   Service Layer                                  │
│                                                                  │
│  ┌────────────────┐    ┌────────────────┐    ┌────────────────┐│
│  │     Agent      │    │    Market      │    │      Risk      ││
│  │   Orchestrator │    │     Data       │    │     Engine     ││
│  │   (LangGraph)  │    │    Service     │    │                ││
│  └────────────────┘    └────────────────┘    └────────────────┘│
│                                                                  │
│  ┌────────────────┐    ┌────────────────┐    ┌────────────────┐│
│  │   Execution    │    │    Vector      │    │   Backtest     ││
│  │    Service     │    │    Memory      │    │    Engine      ││
│  │                │    │   (ChromaDB)   │    │                ││
│  └────────────────┘    └────────────────┘    └────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                    Data Layer                                      │
│  ┌────────────────┐    ┌────────────────┐    ┌────────────────┐ │
│  │   PostgreSQL   │    │    Redis       │    │   ChromaDB     │ │
│  │  (Primary DB)  │    │   (Cache/      │    │   (Vector      │ │
│  │                │    │    Pub/Sub)    │    │    Memory)     │ │
│  └────────────────┘    └────────────────┘    └────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                  Blockchain Layer                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              Multi-Chain RPC Connections                     │  │
│  │  ┌──────────┐    ┌──────────┐    ┌──────────┐            │  │
│  │  │   BSC    │    │Ethereum  │    │ Arbitrum │            │  │
│  │  │  Node    │    │   Node   │    │   Node   │            │  │
│  │  └──────────┘    └──────────┘    └──────────┘            │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              PancakeSwap Contracts                         │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐ │  │
│  │  │ Factory V2   │  │  Router V2   │  │  Position Mgr   │ │  │
│  │  │ Factory V3   │  │  Router V3   │  │    V3 NFT       │ │  │
│  │  └──────────────┘  └──────────────┘  └─────────────────┘ │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Agent Orchestration

### LangGraph State Machine

The trading system uses LangGraph to coordinate multiple agents through a state machine pattern.

```
┌─────────────────────────────────────────────────────────────────┐
│                     Trading State Graph                          │
│                                                                  │
│  Entry Point                                                     │
│      │                                                           │
│      ▼                                                           │
│  ┌──────────────┐                                                │
│  │   Market     │───────────────────────────────────────────┐    │
│  │Intelligence  │                                           │    │
│  └──────┬───────┘                                           │    │
│         │                                                   │    │
│         ▼                                                   │    │
│  ┌──────────────┐     ┌──────────────┐                      │    │
│  │   Liquidity  │────▶│   Strategy   │                      │    │
│  │   Analysis   │     │    Agent     │                      │    │
│  └──────────────┘     └──────┬───────┘                      │    │
│                             │                                │    │
│                             ▼                                │    │
│                      ┌──────────────┐                        │    │
│                      │     Risk     │──────┬──────────┐     │    │
│                      │ Management   │      │          │     │    │
│                      └──────────────┘      │          │     │    │
│                             │              │          │     │    │
│                    Approved │              │ Rejected │     │    │
│                             ▼              │          │     │    │
│                      ┌──────────────┐      │          │     │    │
│                      │   Execution  │──────┘          │     │    │
│                      │    Agent     │◄─────────────────┘     │    │
│                      └──────┬───────┘                      │    │
│                             │                                │    │
│                             ▼                                │    │
│                      ┌──────────────┐                        │    │
│                      │   Portfolio  │────────────────────────┘    │
│                      │    Agent     │                             │
│                      └──────┬───────┘                             │
│                             │                                     │
│                             ▼                                     │
│                           [END]                                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### State Transitions

1. **Market Intelligence** → **Liquidity Analysis** (Sequential)
   - Market data must be fetched before liquidity analysis

2. **Liquidity Analysis** → **Strategy** (Sequential)
   - Pool data informs strategy decisions

3. **Strategy** → **Risk Management** (Sequential)
   - All signals must be validated

4. **Risk Management** → **Execution** OR **Portfolio** (Conditional)
   - Approved signals go to execution
   - Rejected signals skip to portfolio update

5. **Execution** → **Portfolio** (Sequential)
   - All executions update portfolio

## Agent Responsibilities

### Market Intelligence Agent

**Purpose**: Monitor real-time market conditions

**Inputs**: RPC data, subgraph data, mempool

**Outputs**: Price updates, market regime, whale alerts

**Key Functions**:
```python
async def fetch_price_updates() -> List[PriceUpdate]
def detect_market_regime(updates: List[PriceUpdate]) -> str
def calculate_volatility(pool_address: str) -> float
async def detect_whale_movements() -> List[WhaleMovement]
```

### Strategy Agent

**Purpose**: Generate trade signals using multiple strategies

**Strategies**:
- Cross-pool arbitrage
- Trend following (momentum)
- Mean reversion
- LP yield optimization

**Signal Scoring**:
```
score = (
    confidence * 100 +
    expected_profit * 10
) * strategy_weight
```

### Risk Management Agent

**Purpose**: Validate signals and enforce risk limits

**Risk Checks**:
1. Position size limits
2. Daily loss limits
3. Portfolio exposure
4. Signal confidence
5. Gas cost ratio
6. Slippage tolerance
7. Market regime

**Circuit Breakers**:
- Portfolio drawdown > 5%
- Flash crash detection
- Multiple consecutive losses
- Abnormal volatility

### Execution Agent

**Purpose**: Execute trades with MEV protection

**Features**:
- Flashbots bundle submission
- Private transaction routing
- Gas optimization
- Slippage protection
- Retry logic

**Transaction Flow**:
```
1. Build transaction
2. Simulate (if enabled)
3. Sign transaction
4. Submit via Flashbots OR public mempool
5. Wait for confirmation
6. Update state with receipt
```

### Portfolio Agent

**Purpose**: Track portfolio and calculate metrics

**Metrics**:
- Total P&L
- Realized/Unrealized P&L
- Win rate
- Sharpe ratio
- Max drawdown
- Profit factor

### Liquidity Analysis Agent

**Purpose**: Analyze DEX liquidity conditions

**Functions**:
- Pool discovery
- Liquidity depth analysis
- Impermanent loss estimation
- Fee APY calculation
- Reserve imbalance detection

### Backtest Agent

**Purpose**: Validate strategies on historical data

**Features**:
- Candle replay
- Fee simulation
- Slippage modeling
- Gas variation
- What-if scenarios

## Data Flow

### Price Data Flow

```
Blockchain → RPC → Market Intelligence Agent → Redis Pub/Sub
                                                  ↓
Frontend ← WebSocket ← API ← Redis Subscriber
```

### Trade Execution Flow

```
Strategy Agent → Risk Agent → Execution Agent
                                         ↓
                              Blockchain (via Flashbots)
                                         ↓
                              Transaction Receipt
                                         ↓
                              Portfolio Agent → Database
```

### Memory/Learning Flow

```
Trade Execution → Vector Memory Store (ChromaDB)
                         ↓
              Similar Scenario Query
                         ↓
              Retrieved Memories → Strategy Agent
```

## Database Schema

### Core Tables

```sql
-- Trades
CREATE TABLE trades (
    id UUID PRIMARY KEY,
    signal_id UUID,
    status VARCHAR(20),
    tx_hash VARCHAR(66),
    block_number BIGINT,
    token_in VARCHAR(42),
    token_out VARCHAR(42),
    amount_in NUMERIC,
    amount_out NUMERIC,
    expected_profit NUMERIC,
    actual_profit NUMERIC,
    gas_cost_eth NUMERIC,
    gas_cost_usd NUMERIC,
    strategy VARCHAR(50),
    confidence FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Portfolio Snapshots
CREATE TABLE portfolio_snapshots (
    id UUID PRIMARY KEY,
    total_value_usd NUMERIC,
    available_balance NUMERIC,
    total_pnl NUMERIC,
    unrealized_pnl NUMERIC,
    realized_pnl NUMERIC,
    positions JSONB,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Agent Actions
CREATE TABLE agent_actions (
    id UUID PRIMARY KEY,
    agent_name VARCHAR(50),
    action VARCHAR(100),
    input_data JSONB,
    output_data JSONB,
    confidence FLOAT,
    duration_ms INTEGER,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Pools
CREATE TABLE pools (
    address VARCHAR(42) PRIMARY KEY,
    chain VARCHAR(20),
    dex VARCHAR(20),
    version INTEGER,
    token0 VARCHAR(42),
    token1 VARCHAR(42),
    fee_tier INTEGER,
    tvl_usd NUMERIC,
    volume_24h NUMERIC,
    apr_24h NUMERIC,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Security Architecture

### Authentication Flow

```
Client Request → API Gateway → JWT Validation → Rate Limiting
                                    ↓
                            Route to Service
                                    ↓
                    Service Auth Check (if required)
```

### Transaction Security

1. **Private Key Management**
   - Hardware wallet support (Ledger, Trezor)
   - AWS KMS integration
   - Environment variable only (dev)

2. **MEV Protection**
   - Flashbots relay for bundle submission
   - Private mempool for sensitive transactions
   - Sandwich attack detection

3. **Circuit Breakers**
   - Automatic halt on excessive loss
   - Manual reset required
   - Audit logging

## Scalability

### Horizontal Scaling

```
                    Load Balancer
                         │
         ┌──────────────┼──────────────┐
         │              │              │
    ┌────▼────┐    ┌────▼────┐    ┌────▼────┐
    │ API #1  │    │ API #2  │    │ API #3  │
    └────┬────┘    └────┬────┘    └────┬────┘
         │              │              │
         └──────────────┼──────────────┘
                        │
                  Redis Cluster
                   (Pub/Sub)
                        │
         ┌──────────────┼──────────────┐
         │              │              │
    ┌────▼────┐    ┌────▼────┐    ┌────▼────┐
    │ Agent 1 │    │ Agent 2 │    │ Agent 3 │
    └─────────┘    └─────────┘    └─────────┘
```

### Database Sharding Strategy

- **Trades**: Sharded by `created_at` (time-based)
- **Portfolio**: Single table (one row per user)
- **Agent Actions**: Sharded by `agent_name`

### Caching Strategy

| Data Type | Cache Layer | TTL |
|-----------|-------------|-----|
| Prices | Redis | 30s |
| Pool Info | Redis | 5min |
| Portfolio | Redis | 1min |
| Static Config | Local | Forever |

## Monitoring & Observability

### Metrics Collection

```python
# Agent metrics
AGENT_EXECUTION_TIME = Histogram('agent_execution_seconds', 'Time spent executing agent', ['agent_name'])
AGENT_ACTIONS_TOTAL = Counter('agent_actions_total', 'Total agent actions', ['agent_name', 'action'])

# Trading metrics
TRADES_EXECUTED = Counter('trades_executed_total', 'Total trades', ['status', 'strategy'])
PNL_GAUGE = Gauge('portfolio_pnl', 'Current P&L')

# System metrics
REQUEST_DURATION = Histogram('request_duration_seconds', 'API request duration')
ACTIVE_CONNECTIONS = Gauge('active_websocket_connections', 'Active WS connections')
```

### Logging Levels

- **ERROR**: Circuit breaker triggers, execution failures
- **WARNING**: High risk scores, gas spikes
- **INFO**: Trade executions, strategy switches
- **DEBUG**: Agent decision details (dev only)

### Alerting Rules

1. Circuit breaker triggered
2. P&L drops below threshold
3. Agent error rate > 5%
4. API latency > 500ms
5. Database connection failures

## Testing Strategy

### Unit Tests
- Individual agent logic
- Strategy calculations
- Risk validation rules

### Integration Tests
- Agent communication
- Database interactions
- Blockchain interactions (mocked)

### E2E Tests
- Full trading cycle
- Dashboard interactions
- WebSocket connections

### Load Tests
- API throughput
- WebSocket concurrency
- Agent processing capacity

## Deployment

### CI/CD Pipeline

```
Code Push → GitHub Actions → Run Tests → Build Images → Push to Registry
                                                      ↓
                                              Deploy to Staging
                                                      ↓
                                              Integration Tests
                                                      ↓
                                              Deploy to Production
```

### Environment Strategy

| Environment | Purpose | Data |
|-------------|---------|------|
| Development | Local dev | Testnet |
| Staging | Integration | Testnet |
| Production | Live trading | Mainnet (cautious) |

## Future Enhancements

1. **Cross-Chain Arbitrage**: Bridge integration for multi-chain arb
2. **Machine Learning**: Deep RL for strategy optimization
3. **Social Signals**: Twitter/sentiment analysis
4. **Advanced Visualization**: 3D market visualization
5. **Mobile App**: React Native companion app
6. **Governance**: DAO for strategy voting
