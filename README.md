# AI Trading Bot

A **multi-agent AI cryptocurrency futures trading system** that combines Smart Money Concepts (SMC) technical analysis with large language models to analyze markets and execute leveraged trades on Binance automatically.

## What It Does

- Accepts natural-language queries like *"Analyze SOLUSDT 1h and place a trade if setup is valid"*
- Fetches multi-timeframe SMC data (1h / 2h / 4h) and formats it as context for the AI
- Routes through a LangGraph pipeline: market analysis → trade decision → order execution
- Streams the agent's reasoning back to the browser in real time (Server-Sent Events)
- Places bracket orders on Binance Futures (LIMIT entry + Take-Profit + Stop-Loss)
- Sends Telegram notifications on order placement

---

## Project Structure

```
ai_agent_project/
├── bot-trading/          # Python FastAPI backend
└── fe_chat/              # React + TypeScript + Vite frontend
```

---

## Backend (`bot-trading/`)

**Runtime:** Python 3.10+ · FastAPI · uvicorn · LangGraph

### Directory Layout

```
bot-trading/
├── main.py                        # App entry point, router registration, lifespan
├── config.py                      # Env var loading via python-dotenv
├── requirements.txt
├── agents/
│   ├── gemini/
│   │   ├── agent.py               # Google GenAI wrapper (gemini-2.5-flash, thinking enabled)
│   │   └── agentic_agent.py       # MasterGemini — LangGraph state machine
│   ├── claude/
│   │   ├── agent.py               # Claude Agent SDK wrapper (CLI-backed, claude-opus-4-6)
│   │   └── agentic_agent.py       # MasterClaude — LangGraph state machine
│   └── chat_gpt/
│       ├── agent.py               # OpenAI wrapper (gpt-4o)
│       └── agentic_agent.py       # MasterChatGPT — LangGraph state machine
│   ├── prompts.py                 # System instructions for each agent role
│   └── prompts_enhance.py         # Advanced multi-timeframe hierarchy instructions
├── connectors/
│   ├── binance_v2.py              # BinanceConnector — bracket order placement, leverage mgmt
│   └── telegram.py                # Async Telegram notifications
├── routers/
│   ├── stream.py                  # GET /{provider}/{model}/stream  (SSE endpoint)
│   └── trading.py                 # /trading/models · /trading/leverage · /trading/smc
├── services/
│   └── smc_service.py             # SmcService — full SMC + classic indicator engine
├── tools/
│   └── cx_connector.py            # Agent-callable tools: smc_analysis, create_order
└── tests/
    └── test_create_orders.py
```

### Key Components

#### SmcService (`services/smc_service.py`)
The analytical core. Fetches OHLCV from Binance Futures REST and computes:

| Category | Metrics |
|---|---|
| Trend | Bullish (HH+HL) / Bearish (LH+LL) / Ranging |
| Structure | Break of Structure (BOS), Change of Character (CHoCH) |
| Order Blocks | Bullish & bearish OBs, strength score (0–100%), mitigation status |
| Fair Value Gaps | Bullish & bearish FVGs, fill status |
| Liquidity | Buy-side (swing highs), sell-side (swing lows) |
| Premium/Discount | 100-candle range zones |
| Potential Entries | OB + FVG confluence zones with scoring |
| Classic Indicators | ATR · EMA 9/20/50 · Bollinger Bands (20, 2σ) · RSI 7/14/21 |

#### CXConnector (`tools/cx_connector.py`)
The tool layer exposed to all AI agents:
- **`smc_analysis(symbol, timeframe, limit)`** — Delegates to SmcService, returns full indicator dict
- **`create_order(symbol, current_price, side, entry, stop_loss, take_profit)`** — Places a 3-order bracket on Binance Futures via BinanceConnector

#### BinanceConnector (`connectors/binance_v2.py`)
Wraps `binance-futures-connector` (`UMFutures`). Defaults:
- Leverage: **10x** (configurable per symbol)
- Order size: **8 USDT**
- Take-profit: **0.40%**, Stop-loss: **0.30%** (leveraged)

Places three orders atomically: `LIMIT` entry + `TAKE_PROFIT_MARKET` + `STOP_MARKET`.

#### LangGraph Agent Flow

All three providers (Gemini, Claude, ChatGPT) share the same state machine topology:

```
init_flow
    ↓
master_agent  ──(classify intent)──►  TOOL_AGENT       → tools_agent
                                  ►  MARKET_ANALYSIS   → analysis_agent
                                  ►  TRADE_DECISION    → decision_agent
                                  ►  GENERAL_QUERY     → master_agent (loop)
                                  ►  FINAL_RESPONSE    → generate_response → END
```

- **State:** `MasterState` TypedDict — `chat_history`, `agent_response`, `user_prompt`, `step_count`, `max_steps`, `user_feedback`
- **Max steps:** 10 (overflow → `generate_response`)
- **Session persistence:** `InMemorySaver` keyed by `thread_id`
- **Streaming:** each node appends to `user_feedback`; content is streamed character-by-character with `_FEEDBACK_SEPARATOR` marking step transitions

#### API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/{provider}/{model}/stream?query=...` | SSE stream — multi-agent reasoning + result |
| `GET` | `/trading/models` | List available AI models (9 total) |
| `POST` | `/trading/leverage` | Set leverage for one symbol |
| `POST` | `/trading/leverage/bulk` | Set leverage for multiple symbols |
| `GET` | `/trading/smc?symbol=&timeframe=&limit=` | Raw SMC analysis (JSON) |

`provider`: `gemini` · `claude` · `chatgpt`

#### Supported Models

| Provider | Models |
|---|---|
| Gemini | `gemini-2.5-flash`, `gemini-2.5-pro`, `gemini-2.0-flash`, `gemini-1.5-pro`, `gemini-1.5-flash` |
| Claude | `claude-haiku-4-5`, `claude-sonnet-4-6`, `claude-opus-4-6` |
| ChatGPT | `gpt-4o` |

---

## Frontend (`fe_chat/`)

**Runtime:** React 19 · TypeScript · Vite · lightweight-charts

### Directory Layout

```
fe_chat/src/
├── App/
│   ├── index.tsx                  # Main layout (chart + chat sidebar)
│   ├── types.ts                   # ChatMessage, Candle, Ticker types
│   └── components/
│       ├── Header/                # Model switcher, theme toggle
│       ├── CoinList/              # 49 trading pairs list
│       ├── Chat/
│       │   ├── Messages.tsx       # Streamed markdown messages
│       │   └── Input.tsx          # Query input box
│       ├── Chart/
│       │   ├── CandleChart.tsx    # lightweight-charts candle renderer
│       │   ├── IndicatorChart.tsx # EMA / RSI / BB overlays
│       │   ├── SMCPanel.tsx       # OB / FVG / liquidity drawings
│       │   └── TimeframeSelector.tsx
│       └── LeveragePanel/         # Set leverage per symbol
├── hooks/
│   ├── useChat.ts                 # Chat state + SSE streaming
│   ├── useCandles.ts              # Fetch/cache OHLCV candles
│   ├── useLeverage.ts             # Leverage management
│   └── useTheme.ts                # Dark/light theme
├── services/
│   ├── chatService.ts             # streamChat() + fetchModels()
│   ├── tradingService.ts          # smcAnalysis(), setLeverage()
│   ├── smcQueryService.ts         # buildSmcQuery() — multi-TF markdown builder
│   ├── binanceService.ts          # Binance price/candle data
│   └── config.ts                  # BOT_BASE_URL = "http://localhost:8000"
├── coins.ts                       # 49 supported USDT perpetual pairs
└── constants.ts                   # TIMEFRAMES: 15m 1h 2h 4h 12h 1d
```

### Key Services

#### `smcQueryService.ts` — Multi-Timeframe Context Builder
Before every chat message, `buildSmcQuery()`:
1. Calls `GET /trading/smc` in parallel for **1h, 2h, 4h**
2. Formats each response as a structured markdown block (trend, BOS/CHoCH, OBs, FVGs, liquidity, confluence zones, indicators)
3. Prepends the full multi-timeframe context to the user's query

This means the AI receives pre-computed SMC data — it doesn't need to re-fetch market data unless it wants live price confirmation.

#### `chatService.ts` — SSE Streaming
```ts
streamChat(query, agent, model, onCharacter, onEnd, onError)
```
Opens an `EventSource` to `/{agent}/{model}/stream?query=...`. Each SSE event contains `{"character": "c"}` — a single character that is appended to the current message in React state, producing a typewriter effect. The stream closes on `event: end`.

---

## Communication Flow

```
User types query in browser
        │
        ▼
smcQueryService.buildSmcQuery(symbol)
  → GET /trading/smc  (1h, 2h, 4h in parallel)
  → Formats as multi-TF markdown
        │
        ▼
chatService.streamChat(fullQuery, agent, model)
  → EventSource: GET /{agent}/{model}/stream?query=<full_query>
        │
        ▼ (Backend)
stream.py router → MasterAgent (LangGraph)
  init_flow
    → master_agent     classifies intent
    → analysis_agent   interprets SMC indicators
    → decision_agent   BUY / SELL / WAIT + price levels
    → tools_agent      calls cx_connector.create_order()
      → BinanceConnector.create_orders()  →  Binance Futures API
      → telegram.py  (async notification)
    → generate_response  final markdown summary
        │
        ▼ (SSE back to browser)
Each character streamed → React appends to chat message
        │
        ▼
event: end → EventSource closed, loading = false
```

---

## Running the Project

### Backend

```bash
cd bot-trading
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py          # http://127.0.0.1:8000
```

### Frontend

```bash
cd fe_chat
npm install
npm run dev             # http://localhost:5173
```

### Environment Variables

Create `bot-trading/.env`:

```env
# AI Models
API_KEY=your-google-gemini-api-key
GOOGLE_API_KEY=your-google-gemini-api-key
OPEN_API_KEY=your-openai-api-key

# Binance Futures
BINANCE_API_KEY=your-binance-api-key
BINANCE_SECRET_KEY=your-binance-secret-key

# Telegram
TELEGRAM_TOKEN=your-telegram-bot-token
TELEGRAM_CHATID=your-telegram-chat-id

# App
ENV=development
APP_HOST=127.0.0.1
APP_PORT=8000
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend runtime | Python 3.10+ |
| Web framework | FastAPI + uvicorn |
| AI orchestration | LangGraph + LangChain |
| AI models | Gemini 2.5 Flash / Claude Opus 4.6 / GPT-4o |
| Market data | Binance Futures REST (httpx) |
| Data processing | pandas, numpy |
| Order execution | binance-futures-connector (`UMFutures`) |
| Notifications | Telegram Bot API (aiohttp) |
| Frontend | React 19 + TypeScript + Vite |
| Charts | lightweight-charts v5 |
| UI rendering | ReactMarkdown + remark-gfm |
