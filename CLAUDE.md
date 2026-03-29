# AI Trading Bot — Project Guide

## Overview

This is a **multi-agent AI trading bot** for cryptocurrency futures trading on Binance. It uses LangGraph to orchestrate specialized AI agents (Gemini or OpenAI) that analyze markets using Smart Money Concepts and execute leveraged trades automatically.

The project has two parts:

- `bot-trading/` — Python FastAPI backend with AI agents
- `fe_chat/` — React + TypeScript + Vite chat frontend

---

## Architecture

```
fe_chat (React SSE client)
    │
    ▼
bot-trading/main.py  (FastAPI, port 8000)
    │
    ├── /gemini/stream  ──►  MasterGemini (LangGraph)
    │                            ├── master_agent      (routes requests)
    │                            ├── tools_agent       (fetches market data, places orders)
    │                            ├── analysis_agent    (SMC technical analysis)
    │                            ├── decision_agent    (buy/sell/wait decisions)
    │                            └── generate_response (final output)
    │
    └── /openai/stream  ──►  MasterOpenAI (same structure, OpenAI GPT-4o-mini)
```

### LangGraph Agent Flow

Each agent responds with a JSON `{ "type": "CATEGORY" }` that drives routing:

- `TOOL_AGENT` → `tools_agent` (fetch data or place an order)
- `MARKET_ANALYSIS` → `analysis_agent`
- `TRADE_DECISION` → `decision_agent`
- `GENERAL_QUERY` → back to `master_agent`
- `FINAL_RESPONSE` → `generate_response` (stream ends)

Max steps per request: **10** (prevents infinite loops).

---

## Project Structure

```
ai_agent_project/
├── CLAUDE.md
├── bot-trading/
│   ├── main.py                        # FastAPI app entry point
│   ├── config.py                      # Env var loading (dotenv)
│   ├── requirements.txt               # Python dependencies
│   ├── .env                           # Secrets (never commit)
│   ├── .python-version                # Python version pin
│   ├── gemini/
│   │   ├── api.py                     # FastAPI router: GET /gemini/stream
│   │   └── agents_gemini/
│   │       ├── agent.py               # Base Gemini agent (gemini-2.5-flash)
│   │       └── agentic_agent.py       # MasterGemini LangGraph orchestrator
│   ├── open-ai/
│   │   ├── api.py                     # FastAPI router: GET /openai/stream
│   │   ├── agents_openai/
│   │   │   ├── agent.py               # Base OpenAI agent (gpt-4o-mini)
│   │   │   └── agentic_agent.py       # MasterOpenAI LangGraph orchestrator
│   │   ├── tools/
│   │   │   └── openai_tools.py        # OpenAI tool definitions
│   │   └── test_agent.py              # Test script
│   └── src/
│       ├── binance_connector/
│       │   └── binance.py             # BinanceConnector (USDS Futures, 20x leverage)
│       ├── telegram/
│       │   └── telegram.py            # Telegram notification bot
│       └── tools/
│           └── cx_connector.py        # CXConnector: smc_analysis + create_order tools
└── fe_chat/
    ├── src/
    │   ├── AppStream.tsx              # Main chat UI (SSE streaming)
    │   ├── coins.ts                   # List of supported trading pairs
    │   └── main.tsx                   # React entry point
    ├── package.json
    └── vite.config.ts
```

---

## Running the Project

### Backend

```bash
cd bot-trading
python -m venv venv          # first time only
source venv/bin/activate
pip install -r requirements.txt

python main.py               # runs on http://127.0.0.1:8000
```

### Frontend

```bash
cd fe_chat
npm install                  # first time only
npm run dev                  # runs on http://localhost:5173
```

---

## Environment Variables

Create `bot-trading/.env`:

```env
# AI Models
API_KEY=your-google-gemini-api-key
GOOGLE_API_KEY=your-google-gemini-api-key
OPEN_API_KEY=your-openai-api-key

# Binance Futures
BINANCE_API_KEY=your-binance-api-key
BINANCE_SECRET_KEY=your-binance-secret-key
BINANCE_BASE_URL=https://api.binance.com   # leave empty for production default

# Telegram Notifications
TELEGRAM_TOKEN=your-telegram-bot-token
TELEGRAM_CHATID=your-telegram-chat-id

# App
ENV=development              # development | production
APP_HOST=127.0.0.1
APP_PORT=8000
```

---

## API Endpoints

| Method | Path                       | Description                              |
| ------ | -------------------------- | ---------------------------------------- |
| GET    | `/gemini/stream?query=...` | SSE stream — Gemini multi-agent response |
| GET    | `/openai/stream?query=...` | SSE stream — OpenAI multi-agent response |

Responses are **Server-Sent Events** streaming character by character. The stream ends with `event: end`.

---

## Key Components

### CXConnector (`src/tools/cx_connector.py`)

The tool layer exposed to AI agents:

- **`smc_analysis(symbol, timeframe, limit)`** — Fetches OHLCV via ccxt, computes:
  - ATR, swing highs/lows, order blocks
  - Fair Value Gaps (bullish/bearish)
  - Break of Structure (BOS) and Change of Character (CHoCH)
  - Liquidity levels (buy-side / sell-side)
  - Premium/discount zones
  - Bollinger Bands (14, 20, 50 periods)
  - EMA (9, 20, 50 periods)
  - RSI (7, 14, 21 periods)

- **`create_order(symbol, side, entry, stop_loss, take_profit)`** — Places a 3-order bracket on Binance Futures (LIMIT entry + TAKE_PROFIT_MARKET + STOP_MARKET). Uses 20x leverage.

### BinanceConnector (`src/binance_connector/binance.py`)

Wraps `binance_sdk_derivatives_trading_usds_futures`. Trade defaults:

- Leverage: **20x**
- Order amount: **$5 USDT**
- Take profit: **0.40%** (leveraged)
- Stop loss: **0.75%** (leveraged)

### Telegram (`src/telegram/telegram.py`)

Sends async notifications on order placement and errors using `aiohttp`.

---

## Tech Stack

| Layer            | Technology                     |
| ---------------- | ------------------------------ |
| Backend runtime  | Python 3.10+                   |
| Web framework    | FastAPI + uvicorn              |
| AI orchestration | LangGraph + LangChain          |
| AI models        | Gemini 2.5 Flash / GPT-4o-mini |
| Market data      | ccxt (Binance USDS Futures)    |
| Data processing  | pandas, numpy                  |
| Frontend         | React 18 + TypeScript + Vite   |
| UI rendering     | ReactMarkdown + remark-gfm     |

---

## Development Notes

- The Gemini agent uses `gemini-2.5-flash` with `ThinkingConfig(include_thoughts=True)` — thinking steps are surfaced as `user_feedback` in the stream.
- Agents communicate via a `MasterState` TypedDict (LangGraph state): `chat_history`, `agent_response`, `user_prompt`, `step_count`, `max_steps`, `user_feedback`.
- `InMemorySaver` provides session-level conversation persistence keyed by `thread_id`.
- The frontend connects to `http://127.0.0.1:8000/gemini/stream` by default (hardcoded in `AppStream.tsx`).
- The `open-ai/` directory uses dashes in the folder name — use `import` carefully (it has `__init__.py` files).
