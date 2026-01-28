# Stock Agent AI

> Autonomous AI investment agent for Indian stock markets (NSE) — analyzes live data, decides which stocks to buy, allocates your budget intelligently, and invests automatically.

---

##  Watch Full Demo

<p align="center">
  <a href="https://www.youtube.com/watch?v=BwZFpIvA5sI">
    <img src="https://img.youtube.com/vi/BwZFpIvA5sI/0.jpg" width="700">
  </a>
</p>

## Problem Statement

Most people want to invest in stocks but don't know which stocks to buy, how much to put in, or when to exit — so they either lose money or never invest at all. This AI agent solves that completely. You give it a budget, it analyzes 20 NSE stocks using live prices, technical indicators, and news sentiment, then decides exactly which stocks to buy, how many shares, and where to set stop-losses. It executes automatically via Upstox broker, generates a plain-English explanation of every decision, and reinvests monthly via SIP — without any manual action from you.

---

## Live URLs

| Service | URL |
|---|---|
| React Dashboard | http://localhost:3000 |
| FastAPI Backend | http://localhost:8000 |
| Swagger API Docs | http://localhost:8000/docs |

---

## Folder Structure

```
stock-agent/
│
├── agent/                          # Core AI agent
│   ├── __init__.py
│   ├── allocator.py                # Budget allocation engine
│   ├── autonomous.py               # Autonomous decision system
│   ├── orchestrator.py             # Main agent brain
│   ├── memory/
│   │   ├── __init__.py
│   │   └── behavior.py             # Investor behavior profiling
│   ├── prompts/                    # GPT prompt templates
│   └── tools/
│       ├── __init__.py
│       ├── advisor.py              # BUY/HOLD/SELL signal generator
│       ├── broker.py               # Upstox API v2 integration
│       ├── market_data.py          # Live NSE price fetcher (20 stocks)
│       ├── market_mood.py          # Nifty50 + India VIX mood detector
│       ├── risk.py                 # Risk scoring engine
│       ├── sentiment.py            # NewsAPI + GPT-4o-mini sentiment
│       └── technical.py            # RSI, MACD, MA200, indicators
│
├── backend/
│   ├── __init__.py
│   ├── database.py                 # PostgreSQL models + queries
│   ├── main.py                     # FastAPI app — 16 endpoints
│   ├── routers/                    # Route modules
│   └── scheduler.py                # APScheduler monthly SIP cron
│
├── frontend/
│   ├── public/
│   └── src/
│       ├── App.js
│       ├── App.css
│       ├── Dashboard.jsx           # Complete React dashboard
│       ├── index.js
│       └── index.css
│
├── data/                           # Static reference data
├── stockAgent/                     # Python virtual environment
│
├── .env                            # API keys — never commit this
├── .gitignore
├── Screenshots                     # Results
├── README.md
├── refresh_token.py                # Daily Upstox token refresh
└── requirements.txt
```

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | React 18, Recharts, Axios | Dashboard with live charts |
| Backend | FastAPI 2.0, Uvicorn | REST API server |
| Database | PostgreSQL 15, SQLAlchemy | Trade logs, SIP schedules |
| AI Model | OpenAI GPT-4o-mini | Sentiment scoring + report generation |
| Market Data | yfinance | Live NSE OHLCV data (20 stocks) |
| News | NewsAPI, Google News RSS | Stock headline fetching |
| Broker | Upstox API v2 | Paper + live NSE order execution |
| Scheduler | APScheduler | Monthly SIP automation |
| Fonts | DM Mono, Space Grotesk | Bloomberg terminal aesthetic |

---

## API Endpoints

All 16 endpoints visible at `http://127.0.0.1:8000/docs`

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Root — API status |
| `GET` | `/health` | Health check + paper mode status |
| `POST` | `/invest` | Run full agent + save trade to DB |
| `GET` | `/history/{user_id}` | Past trades from PostgreSQL |
| `GET` | `/watchlist` | Live prices for 20 NSE stocks |
| `POST` | `/sip/setup` | Create monthly SIP schedule |
| `GET` | `/sip/{user_id}` | Get active SIP details |
| `DELETE` | `/sip/{user_id}` | Cancel active SIP |
| `GET` | `/market-mood` | Nifty50 + VIX market regime |
| `GET` | `/behavior/{user_id}` | Investor behavior profile |
| `GET` | `/funds` | Upstox account balance |
| `GET` | `/portfolio` | Current broker holdings |
| `GET` | `/verify-broker` | Test Upstox token validity |
| `GET` | `/advice/{symbol}` | BUY/HOLD/SELL for one stock |
| `GET` | `/advice-all` | Signals for all 20 stocks |
| `GET` | `/scenarios/{user_id}` | Bull / Base / Bear projections |
| `GET` | `/performance/{user_id}` | Agent accuracy + metrics |
| `GET` | `/rebalance-check/{user_id}` | Portfolio rebalance recommendation |

---

## Database Schema

Two tables auto-created on first run via SQLAlchemy:

```sql
-- Every investment the agent makes
trade_logs (
    id          UUID PRIMARY KEY,
    user_id     TEXT,
    budget      FLOAT,
    risk_level  TEXT,        -- conservative / moderate / aggressive
    allocation  JSON,        -- full holdings with shares, price, stop_loss
    explanation TEXT,        -- GPT-4o-mini generated 4-section report
    top_stocks  JSON,        -- ranked stock analysis data
    mode        TEXT,        -- paper / live
    created_at  TIMESTAMP
)

-- Monthly SIP automation config
sip_schedules (
    id          UUID PRIMARY KEY,
    user_id     TEXT,
    monthly_amt FLOAT,
    risk_level  TEXT,
    active      TEXT,        -- true / false
    created_at  TIMESTAMP
)
```

---

## How the Agent Works

```
User inputs: budget (e.g. ₹5000) + risk level (moderate)
                        ↓
        Fetch 6 months OHLCV for 15 stocks via yfinance
                        ↓
        Compute 6 technical indicators per stock:
        RSI (14-day) → MACD (12/26/9 EMA)
        → 200-day MA → Volume ratio
        → Momentum (20-day) → 52-week range
                        ↓
        Fetch news headlines (NewsAPI + Google News RSS)
        Send to GPT-4o-mini → sentiment score 0-100
                        ↓
        Final score = TA score (60%) + Sentiment (40%)
                        ↓
        Resolve signals per stock:
        BUY / HOLD / SELL + confidence % + stop-loss level
                        ↓
        Dynamic allocation (autonomous.py):
          Skip all SELL signal stocks
          Confidence-weighted position sizing
          Max 35% per stock (moderate risk)
          Reserve 10–20% cash based on VIX level
          Park leftover in LIQUIDBEES ETF
                        ↓
        Generate 4-section AI report via GPT-4o-mini:
          Section 1: Market Regime
          Section 2: Stock Picks with Stop-Losses
          Section 3: Portfolio Summary + Expected Returns
          Section 4: Behavioral Alert
                        ↓
        Save full trade to PostgreSQL (trade_logs table)
                        ↓
        Execute via Upstox API (paper or live mode)
```

---

## Setup Instructions

### Prerequisites

- Python 3.10 or higher
- Node.js 18 or higher
- PostgreSQL 15 with pgAdmin 4
- Upstox demat account (free to open, needs PAN + Aadhaar)
- OpenAI API account with credits

### Step 1 — Clone the repo

```bash
git clone https://github.com/yourusername/stock-agent.git
cd stock-agent
```

### Step 2 — Create virtual environment

```bash
python -m venv stockAgent

# Windows
stockAgent\Scripts\activate

# Mac/Linux
source stockAgent/bin/activate
```

### Step 3 — Install Python packages

```bash
pip install -r requirements.txt
```

### Step 4 — Install frontend packages

```bash
cd frontend
npm install
cd ..
```

### Step 5 — Create .env in project root

```env
# OpenAI
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxx

# NewsAPI — free at newsapi.org
NEWS_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Upstox broker
UPSTOX_API_KEY=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
UPSTOX_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
UPSTOX_ACCESS_TOKEN=eyJ0eXAiOiJKV1Qi...

# PostgreSQL — local
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/stockagent

# App config
PAPER_MODE=true
ENVIRONMENT=development
```

### Step 6 — Create PostgreSQL database

Open pgAdmin 4 → Servers → PostgreSQL → right-click **Databases** → Create → Database → name: `stockagent` → Save.

Run this once to create tables:

```bash
python backend/database.py
```

Expected: `Database tables created successfully`

### Step 7 — Start backend

```bash
uvicorn backend.main:app --reload --port 8000
```

Expected terminal output:
```
Database tables created successfully
Database ready
[Scheduler] Started — SIP runs on 1st of every month at 9:15 AM
INFO: Application startup complete.
INFO: Uvicorn running on http://127.0.0.1:8000
```

### Step 8 — Start frontend

Open a second terminal:

```bash
cd frontend
npm start
```

Expected:
```
webpack compiled successfully
Local: http://localhost:3000
```

Browser opens automatically at `http://localhost:3000`.

---

## API Keys — Where to Get Them

| Key | URL | Cost | Notes |
|---|---|---|---|
| `OPENAI_API_KEY` | platform.openai.com/api-keys | ~₹0.33/run | Needs credit card |
| `NEWS_API_KEY` | newsapi.org/register | Free | 100 req/day on free tier |
| `UPSTOX_API_KEY` | developer.upstox.com | Free | Needs demat account |
| `UPSTOX_ACCESS_TOKEN` | Run `refresh_token.py` | Free | Expires every 24 hours |
| `DATABASE_URL` | Local PostgreSQL | Free | pgAdmin install |

**Getting Upstox API credentials:**
1. Open demat account at upstox.com
2. Go to developer.upstox.com → sign in → Create New App
3. App name: `stock-agent` | Redirect URL: `http://127.0.0.1:8000/callback`
4. Copy `API Key` and `Secret Key` to `.env`
5. Run `python refresh_token.py` each morning to get `UPSTOX_ACCESS_TOKEN`

---

## Daily Token Refresh

Upstox access token expires every 24 hours (SEBI mandate). Run each morning:

```bash
python refresh_token.py
```

Flow: opens browser → you login to Upstox → redirects to localhost → copy the `code=` value → paste in terminal → token auto-written to `.env`.

---

## Switching to Live Trading

```bash
# 1. Refresh token
python refresh_token.py

# 2. Set live mode in .env
PAPER_MODE=false

# 3. Restart backend
uvicorn backend.main:app --reload --port 8000
```

On dashboard: flip **Paper Mode** toggle → button turns red → click **Analyze** → confirm popup → real NSE market orders placed via Upstox.

---

## Dashboard Walkthrough

**Control Bar** — Budget, risk level, analyze button, quick-access buttons, paper/live toggle.

**Market Pulse** (click Pulse) — Market regime (BULLISH/NEUTRAL/CAUTIOUS/BEARISH), live Nifty50, India VIX fear index with visual fear meter, investor behavior profile.

**Live Prices** (click Prices) — Real-time prices for 20 NSE stocks with green/red % change. Covers IT, Banking, FMCG, Auto, Energy, Pharma sectors.

**AI Signals** (click Signals) — BUY/HOLD/SELL for all stocks in a sortable table. Columns: Stock, Price, Action, Confidence bar, RSI, Distance from 52W high, Signal reason. Click any row to expand full technical analysis.

**Analyze Results** (click Analyze ₹X,XXX) — 4 tabs:
- Overview: stat cards + donut chart + score/RSI bar chart
- Allocation: position table with shares, prices, stop-losses, confidence scores
- Report: GPT-4o-mini structured 4-section investment report
- Orders: paper or live execution status per position

**Insights** (click Insights) — Scenario analysis (Bull/Base/Bear), agent performance metrics, rebalance recommendation.

---

## Test Each Module

```bash
# 1. Live prices — should show 20 stocks, no NaN values
python -m agent.tools.market_data

# 2. Technical indicators
python -m agent.tools.technical

# 3. Sentiment scoring (needs OPENAI_API_KEY)
python -m agent.tools.sentiment

# 4. Market mood — Nifty + VIX
python -m agent.tools.market_mood

# 5. Budget allocation
python -m agent.allocator

# 6. Autonomous system with scenario simulation
python -m agent.autonomous

# 7. Full agent end-to-end (takes ~45 seconds)
python -m agent.orchestrator

# 8. Broker connection
python -m agent.tools.broker
```

---

## Verify All Keys Loaded

```bash
python -c "
from dotenv import load_dotenv
import os
load_dotenv()
keys = ['OPENAI_API_KEY','NEWS_API_KEY',
        'UPSTOX_API_KEY','UPSTOX_SECRET',
        'UPSTOX_ACCESS_TOKEN','DATABASE_URL','PAPER_MODE']
for k in keys:
    v = os.getenv(k)
    print(f'  {\"OK\" if v else \"MISSING\"}  {k}')
"
```

---

## What Makes This Different

| Feature | Groww | Smallcase | Zerodha | This Project |
|---|---|---|---|---|
| AI stock selection | No | No | No | Yes |
| Explains every decision | No | No | No | Yes |
| Auto-executes trades | No | No | No | Yes |
| Market mood detection | No | No | No | Yes |
| Stop-loss per position | No | No | Manual | Automatic |
| Behavioral coaching | No | No | No | Yes |
| Bull/Bear scenario sim | No | No | No | Yes |
| Intelligent SIP | Basic | Basic | Basic | AI-driven |
| Rebalance alerts | No | No | No | Yes |

---

## Risk Management

- Max 35% in any single stock (moderate), 25% (conservative), 50% (aggressive)
- Cash reserve: 10% neutral, 15% cautious, 20% bearish market
- Skips all SELL-signal stocks during allocation
- Stop-loss: 5% below entry (low volatility), 7% (high volatility)
- Scenario projections: 3 cases over 6-month horizon
- VIX-aware: increases reserve automatically when VIX > 20

---

## Known Limitations

- yfinance data is ~15 minutes delayed (free tier)
- Upstox token requires manual daily refresh (SEBI rule)
- NewsAPI free plan works on localhost only, not on deployed servers
- Agent learning improves with more trade history (10+ trades recommended)
- Live trading requires active SEBI-registered Upstox demat account

---

## Future Roadmap

- [ ] Auto Upstox token refresh (no manual step)
- [ ] WhatsApp / Telegram alerts on trade execution
- [ ] Real P&L tracking with live price updates
- [ ] JWT multi-user authentication
- [ ] Docker + cloud deployment (AWS / Railway)
- [ ] F&O options signal generation
- [ ] Backtesting dashboard with equity curves
- [ ] Mobile app (React Native)

---

## License

MIT — free to use, modify, and distribute with attribution.

---

## Author

**Aditya Singh Bhadauria** — AI/ML Engineer & Full Stack Developer

Built end-to-end using Python, FastAPI, React, PostgreSQL, and OpenAI API.

- GitHub: [github.com/Adi77189](https://github.com/Adi77189)
- LinkedIn: [linkedin.com/in/aditya-bhadauria-9b8082302/](https://www.linkedin.com/in/aditya-bhadauria-9b8082302/)
- Email: youremail@gmail.com

> *"Groww shows you stocks. Zerodha gives you tools. This agent makes the decision, explains the reasoning, executes the trade, and learns from outcomes — automatically."*

