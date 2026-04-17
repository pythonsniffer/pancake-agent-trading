# PancakeSwap AI Powered Autonomous Multi-Agent Trading System

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.12+-blue)
![Node](https://img.shields.io/badge/node-20.x-green)
![Next.js](https://img.shields.io/badge/Next.js-15-black)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green)

A production-grade autonomous trading platform built for PancakeSwap that leverages AI-powered multi-agent architecture to execute profitable trades across multiple chains with advanced risk management and MEV protection.

## 🏆 Key Features

### Multi-Agent Architecture (LangGraph)
- **Market Intelligence Agent** — Real-time price monitoring, whale detection, market regime analysis
- **Strategy Agent** — Multi-strategy signal generation (Arbitrage, Trend Following, Mean Reversion, LP Yield)
- **Risk Management Agent** — Dynamic risk scoring, circuit breakers, VaR calculations
- **Execution Agent** — MEV-protected transaction execution with Flashbots support
- **Portfolio Agent** — P&L tracking, position management, performance analytics
- **Liquidity Analysis Agent** — Pool discovery, depth analysis, IL simulation
- **Backtest Agent** — Historical simulation, what-if scenarios, strategy validation

### Advanced Capabilities
- 🔒 **MEV Protection** — Flashbots-style bundle submission, private transactions
- 🧠 **Vector Memory** — ChromaDB-based RAG for learning from historical trades
- 📊 **Real-time Dashboard** — 8 full pages: Dashboard, Agents, Trades, Portfolio, Pools, Analytics, Backtest, Settings
- 🔗 **Multi-Chain Support** — BNB Chain, Ethereum, Arbitrum
- 🎯 **V2 + V3 Support** — PancakeSwap V2 and V3 concentrated liquidity
- 🎨 **Agent Decision Graph** — Animated flow visualization of the LangGraph state machine

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.12+** with pip
- **Node.js 20+** with npm

### 1. Clone & Install

```bash
# Clone repository
git clone https://github.com/your-org/pancake-agent-trading.git
cd pancake-agent-trading

# Install frontend dependencies
npm install --legacy-peer-deps

# Install backend dependencies
cd apps/api
pip install -r requirements.txt
cd ../..
```

### 2. Start the Backend (Terminal 1)

```bash
cd apps/api
python -m uvicorn src.main:app --reload --port 8000
```

The API starts at **http://localhost:8000** with:
- Auto-created SQLite database
- Demo seed data (7 agents, 20 trades, portfolio, pools)
- Interactive docs at **http://localhost:8000/docs**

### 3. Start the Frontend (Terminal 2)

```bash
cd apps/web
npm run dev
```

Open **http://localhost:3000** — the full dashboard is ready!

### Optional: Docker Compose (Full Stack)

```bash
cp .env.example .env
# Edit .env with your API keys
docker-compose up -d
```

---

## 📸 Dashboard Pages

| Page | Description |
|------|------------|
| **Dashboard** | Portfolio overview, performance charts, strategy distribution |
| **Agents** | 7 AI agents with live status, workflow visualization, agent decision graph |
| **Trades** | Trade history with filtering, real-time stats, gas tracking |
| **Portfolio** | Asset allocation, equity curve, performance metrics |
| **Pools** | Liquidity pool explorer, top APY pools, TVL rankings |
| **Analytics** | Cumulative P&L, strategy comparison, chain distribution |
| **Backtest** | Historical simulation runner with equity curve results |
| **Settings** | Trading parameters, risk management, network config |

---

## 📁 Project Structure

```
pancake-agent-trading/
├── apps/
│   ├── web/                  # Next.js 15 Frontend
│   │   └── src/
│   │       ├── app/          # 8 pages (dashboard, agents, trades, etc.)
│   │       ├── components/   # Sidebar, Header, Charts, Agent Graph
│   │       └── lib/          # API client, utils
│   └── api/                  # FastAPI Backend
│       └── src/
│           ├── routes/       # REST API + WebSocket endpoints
│           ├── models/       # SQLAlchemy models (Trade, Pool, Agent, Portfolio)
│           ├── config/       # Settings with environment variables
│           └── seed.py       # Demo data seeder
├── services/
│   ├── agents/               # LangGraph multi-agent orchestrator
│   ├── market-data/          # Market data ingestion service
│   ├── risk-engine/          # Risk calculations microservice
│   ├── backtester/           # Historical simulation service
│   ├── execution/            # Trade execution service
│   └── vector-memory/        # ChromaDB memory store
├── packages/
│   ├── shared-types/         # TypeScript type definitions
│   └── config/               # Chain configs, contract ABIs
├── docker-compose.yml        # Full stack Docker setup
└── README.md
```

---

## 🧠 Agent Architecture

### LangGraph State Machine

```
┌──────────────────┐     ┌──────────────────┐
│     Market       │     │    Liquidity      │
│  Intelligence    │     │    Analysis       │
└────────┬─────────┘     └────────┬──────────┘
         │                        │
         └───────────┬────────────┘
                     ▼
           ┌─────────────────┐
           │  Strategy Engine │
           └────────┬────────┘
                    ▼
           ┌─────────────────┐
           │ Risk Management  │
           └───┬─────────┬───┘
               │         │
         Approved    Rejected
               │         │
               ▼         ▼
        ┌───────────┐ ┌──────────┐
        │ Execution  │ │Portfolio │
        └─────┬─────┘ └──────────┘
              │              ▲
              └──────────────┘
```

Agents communicate through a shared `TradingState` managed by LangGraph, enabling autonomous decision-making with full observability.

---

## 🌐 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/agents` | List all agents with status |
| `GET` | `/api/agents/stats/overview` | Agent statistics summary |
| `POST` | `/api/agents/{id}/start` | Start an agent |
| `POST` | `/api/agents/{id}/stop` | Stop an agent |
| `GET` | `/api/trades` | Trade history with filtering |
| `GET` | `/api/trades/stats/summary` | Trade statistics |
| `GET` | `/api/portfolio/current` | Current portfolio snapshot |
| `GET` | `/api/portfolio/history` | Portfolio history over time |
| `GET` | `/api/pools` | Liquidity pools with TVL, APR |
| `GET` | `/api/pools/top/apy` | Top APY pools |
| `GET` | `/health` | Health check |
| `GET` | `/docs` | Interactive API documentation |

---

## 🔒 Security Features

- **MEV Protection** — Flashbots relay integration for private mempool submission
- **Circuit Breakers** — Auto-stop on excessive losses
- **Dynamic Position Sizing** — Risk-adjusted trade amounts
- **VaR Calculations** — Value at Risk monitoring
- **Testnet by Default** — No private key = simulation mode only
- **Slippage Protection** — Configurable max slippage per trade

---

## 🧪 Testing

```bash
# Backend tests
cd apps/api
pytest tests/ -v

# Frontend build check
cd apps/web
npm run build
```

---

## ⚙️ Configuration

All settings are configurable via environment variables or the Settings page:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `MIN_PROFIT_USD` | 1.0 | Minimum profit threshold |
| `MAX_SLIPPAGE_PERCENT` | 0.5 | Max slippage tolerance |
| `MAX_POSITION_SIZE_USD` | 500 | Max position size |
| `MAX_DAILY_LOSS_USD` | 100 | Daily loss circuit breaker |
| `BSC_RPC_URL` | Public node | BNB Chain RPC endpoint |
| `OPENAI_API_KEY` | — | For LLM-powered features |

---

## 📄 License

MIT License — see [LICENSE](LICENSE) file

---

**⚠️ Disclaimer**: This software is for educational and hackathon purposes. Trading cryptocurrencies carries significant risk. Always use testnet for development and never trade more than you can afford to lose.
