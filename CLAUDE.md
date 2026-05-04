# AI Trading Bot — Project Guide

## Overview

This is a **multi-agent AI trading bot** for cryptocurrency futures trading on Binance. It uses LangGraph to orchestrate specialized AI agents (Gemini, Claude, or ChatGPT) that analyze markets using Smart Money Concepts and execute leveraged trades automatically.

The project has two parts:

- `bot-trading/` — Python FastAPI backend with AI agents
- `fe_chat/` — React + TypeScript + Vite chat frontend

---

## Architecture

```
fe_chat (React 19 SSE client)
    │
    ▼
bot-trading/main.py  (FastAPI, port 8000)
    │
    ├── /{provider}/{model}/stream  ──►  MasterGemini | MasterClaude | MasterChatGPT (LangGraph)
    │                                        ├── master_agent      (routes requests)
    │                                        ├── tools_agent       (fetches market data, places orders)
    │                                        ├── analysis_agent    (SMC technical analysis)
    │                                        ├── decision_agent    (buy/sell/wait decisions)
    │                                        └── generate_response (final output)
    │
    └── /trading/...  ──►  models list, leverage management, SMC data
```

Supported providers: `gemini`, `claude`, `chatgpt`

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
│   ├── main.py                        # FastAPI app entry point + Telegram lifespan
│   ├── config.py                      # Env var loading (dotenv)
│   ├── requirements.txt               # Python dependencies
│   ├── .env                           # Secrets (never commit)
│   ├── .python-version                # Python version pin
│   ├── agents/
│   │   ├── prompts.py                 # Basic 4-agent system prompts
│   │   ├── prompts_enhance.py         # Advanced multi-timeframe prompts (4h→2h→1h)
│   │   ├── gemini/
│   │   │   ├── agent.py               # Google GenAI SDK wrapper (gemini-2.5-flash)
│   │   │   └── agentic_agent.py       # MasterGemini LangGraph orchestrator
│   │   ├── claude/
│   │   │   ├── agent.py               # Claude Agent SDK via CLI subprocess (claude-opus-4-6)
│   │   │   └── agentic_agent.py       # MasterClaude LangGraph orchestrator
│   │   └── chat_gpt/
│   │       ├── agent.py               # OpenAI SDK wrapper (gpt-4o)
│   │       └── agentic_agent.py       # MasterChatGPT LangGraph orchestrator
│   ├── connectors/
│   │   ├── binance.py                 # BinanceConnector v1 (legacy)
│   │   ├── binance_v2.py              # BinanceConnector v2 (UMFutures, 10x leverage, $14 USDT)
│   │   └── telegram.py               # Async Telegram bot + MasterClaude integration
│   ├── routers/
│   │   ├── stream.py                  # APIRouter: GET /{provider}/{model}/stream (SSE)
│   │   └── trading.py                 # APIRouter: /models, /leverage, /leverage/bulk, /smc
│   ├── services/
│   │   └── smc_service.py             # SmcService: OHLCV fetch + full indicator calculations
│   ├── tests/
│   │   └── test_create_orders.py
│   └── tools/
│       └── cx_connector.py            # CXConnector: smc_analysis + create_order + get_ticker
└── fe_chat/
    ├── src/
    │   ├── App/
    │   │   ├── index.tsx              # Root component: theme, agent, coin, timeframe, sidebar
    │   │   ├── types.ts               # ChatMessage, LeverageStatus, Candle, Ticker types
    │   │   └── indicators.ts          # calcEMA, calcBB, calcRSI, calcATR + SMC type defs
    │   ├── components/
    │   │   ├── Header/                # Model switcher dropdown, theme toggle, clear chat
    │   │   ├── CoinList/              # 49 trading pairs sidebar
    │   │   ├── LeveragePanel/         # Leverage management UI
    │   │   ├── Chat/
    │   │   │   ├── Messages.tsx       # Streamed markdown AI messages
    │   │   │   └── Input.tsx          # Query input + submit
    │   │   └── Chart/
    │   │       ├── CandleChart.tsx    # lightweight-charts candlestick rendering
    │   │       ├── SMCPanel.tsx       # SMC visualization: OBs, FVGs, BOS/CHoCH, liquidity
    │   │       ├── IndicatorChart.tsx # Extra indicators display
    │   │       ├── IndicatorPicker.tsx# Indicator selector
    │   │       ├── TimeframeSelector.tsx # 15m, 1h, 2h, 4h, 12h, 1d buttons
    │   │       └── MarketBar.tsx      # Price, 24h high/low/volume ticker
    │   ├── hooks/
    │   │   ├── useChat.ts             # Chat state, SSE submit, clearHistory
    │   │   ├── useCandles.ts          # OHLCV fetch for selected symbol/timeframe
    │   │   ├── useLeverage.ts         # Leverage management
    │   │   ├── useTheme.ts            # Dark/light mode persistence
    │   │   └── useTicker.ts           # Real-time price/change/volume
    │   ├── services/
    │   │   ├── chatService.ts         # fetchModels(), streamChat() via EventSource
    │   │   ├── tradingService.ts      # Trading API calls
    │   │   ├── binanceService.ts      # Binance market data
    │   │   ├── smcQueryService.ts     # /smc endpoint queries
    │   │   ├── smcMapper.ts           # mapApiToSMC(): backend JSON → frontend SMCResult
    │   │   └── config.ts              # API base URL
    │   ├── coins.ts                   # 49 supported trading pairs
    │   ├── constants.ts               # Supported timeframes: 15m, 1h, 2h, 4h, 12h, 1d
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

| Method | Path                                    | Description                                      |
| ------ | --------------------------------------- | ------------------------------------------------ |
| GET    | `/{provider}/{model}/stream?query=...`  | SSE stream — multi-agent response                |
| GET    | `/trading/models`                       | List available AI models (9 across 3 providers)  |
| POST   | `/trading/leverage`                     | Set leverage for a symbol                        |
| POST   | `/trading/leverage/bulk`                | Set leverage for multiple symbols                |
| GET    | `/trading/smc`                          | Raw SMC analysis (symbol, timeframe, limit)      |

`provider` is one of: `gemini`, `claude`, `chatgpt`. `model` is the provider-specific model name.

Responses are **Server-Sent Events** streaming character by character. The stream ends with `event: end`.

### Supported Models

| Provider | Models |
| -------- | ------ |
| gemini   | gemini-2.5-flash, gemini-2.5-pro, gemini-2.0-flash, gemini-1.5-pro, gemini-1.5-flash |
| claude   | claude-haiku-4-5-20251001, claude-sonnet-4-6, claude-opus-4-6 |
| chatgpt  | gpt-4o |

---

## Key Components

### SmcService (`services/smc_service.py`)

The analytical core. Fetches OHLCV from Binance Futures REST and computes:

- **ATR** — 14-period Average True Range
- **EMA** — 9, 20, 50 periods
- **Bollinger Bands** — 20-period, 2σ
- **RSI** — 7, 14, 21 periods
- **Swing highs/lows** — Pine Script-based detection (size=50 for structure, size=5 for internal)
- **Order Blocks (OB)** — Bullish/bearish, scored 0–100 (body ratio + size vs ATR)
- **Fair Value Gaps (FVG)** — Bullish/bearish, scored 0–100 (gap size vs ATR), fill status tracked
- **BOS** — Break of Structure (trend continuation)
- **CHoCH** — Change of Character (trend reversal signal)
- **Liquidity levels** — Buy-side / sell-side pools
- **Premium/discount zones** — 0.618 Fibonacci of swing range

### CXConnector (`tools/cx_connector.py`)

Tool layer exposed to AI agents — delegates to SmcService and BinanceConnector:

- **`smc_analysis(symbol, timeframe, limit)`** — Full SMC analysis JSON
- **`create_order(symbol, side, entry, stop_loss, take_profit)`** — Places bracket order
- **`get_ticker(symbol)`** — Returns last 100 candles for a symbol

### BinanceConnector v2 (`connectors/binance_v2.py`)

Wraps `binance.um_futures.UMFutures`. Trade defaults:

- Leverage: **10x**
- Order amount: **$14 USDT**
- Expected profit: **0.40%** (leveraged)
- Expected stop loss: **0.30%** (leveraged)

Places a 3-leg bracket order: LIMIT entry + TAKE_PROFIT_MARKET + STOP_MARKET.

### Claude Agent (`agents/claude/agent.py`)

- Backed by local `claude` CLI binary via **subprocess** (Claude Agent SDK)
- Uses `anyio` thread pool for async execution
- Model: `claude-opus-4-6`
- Flattens conversation history into a single prompt string
- System prompt passed via `ClaudeAgentOptions` to override default CLAUDE.md context

### Telegram (`connectors/telegram.py`)

- Async notifications via `aiohttp`
- Lazy singleton pattern for `CXConnector`, `BinanceConnector`, `MasterClaude`
- Formats SMC analysis with emoji labels and separators
- Integrates with MasterClaude agent for AI-assisted reasoning

---

## SMC Analysis Hierarchy (Multi-Timeframe)

Used by `agents/prompts_enhance.py`:

1. **4h Bias** — Determines dominant trend (bullish/bearish/ranging) via BOS direction, swing structure, EMA alignment
2. **2h Setup** — Identifies Point of Interest (POI): highest-scored unmitigated OB or FVG aligned with 4h bias
3. **1h Execution** — Entry trigger: CHoCH or BOS confirmed at 2h POI level with EMA stack + RSI validation

### 5-Gate Decision Model

All gates must PASS to execute a trade:

| Gate | Check |
| ---- | ----- |
| 1 (4h Bias) | Bias matches intended trade direction |
| 2 (Zone) | Price in correct premium (sell) or discount (buy) zone |
| 3 (2h POI) | Valid unmitigated OB/FVG with score ≥50 |
| 4 (1h Trigger) | CHoCH or BOS confirmed with candle body close |
| 5 (R:R) | Risk-reward ≥1.5x minimum, ideally ≥1:3 |

Additional thresholds: `confluence_score ≥6/10`, `confidence ≥0.65`.

---

## Tech Stack

| Layer            | Technology                                        |
| ---------------- | ------------------------------------------------- |
| Backend runtime  | Python 3.10+                                      |
| Web framework    | FastAPI + uvicorn                                 |
| AI orchestration | LangGraph + LangChain                             |
| AI models        | Gemini 2.5 Flash / Claude Opus 4.6 / GPT-4o      |
| Market data      | Binance Futures REST (via httpx)                  |
| Data processing  | pandas, numpy                                     |
| Frontend         | React 19 + TypeScript + Vite 7                    |
| Chart rendering  | lightweight-charts 5.1.0                          |
| UI rendering     | ReactMarkdown + remark-gfm                        |

---

## Development Notes

- The Gemini agent uses `gemini-2.5-flash` with `ThinkingConfig(include_thoughts=True)` — thinking steps are surfaced as `user_feedback` in the stream.
- Agents communicate via a `MasterState` TypedDict (LangGraph state): `chat_history`, `agent_response`, `user_prompt`, `step_count`, `max_steps`, `user_feedback`, `model`.
- `InMemorySaver` provides session-level conversation persistence keyed by `thread_id`.
- The frontend connects via the unified `/{provider}/{model}/stream` endpoint.
- All agents are registered in `routers/stream.py` via a lazy-loaded registry.
- Two prompt systems exist: `prompts.py` (basic 4-agent routing) and `prompts_enhance.py` (advanced multi-timeframe hierarchy).
- The frontend persists selected coin and timeframe in URL params (`?coin=BTCUSDT&tf=1h`).
- The sidebar width is user-resizable (260–600px) via a drag divider.
