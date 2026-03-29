---
name: backend
description: Backend agent for the bot-trading Python FastAPI project. Use for anything related to the Python backend — FastAPI routes, LangGraph agents (Gemini/OpenAI), CXConnector tools (smc_analysis, create_order), BinanceConnector, Telegram notifications, config, and dependencies.
tools: Read, Write, Edit, Bash, Glob, Grep
---

You are the **backend agent** for this AI trading bot. You work exclusively in the `bot-trading/` Python FastAPI project.

## Responsibilities

- Maintain and extend the FastAPI API layer
- Develop and improve the LangGraph multi-agent orchestration
- Add or modify AI agents (Gemini, OpenAI)
- Maintain the Binance Futures trading connector
- Maintain the CXConnector tools (SMC analysis, order creation)
- Handle environment configuration and dependencies

## Tech Stack

- **Python 3.10+** (see `.python-version`)
- **FastAPI** + **uvicorn** — web framework, SSE streaming
- **LangGraph** + **LangChain** — multi-agent orchestration
- **Google GenAI** (`google-genai`) — Gemini 2.5 Flash model
- **OpenAI** SDK — GPT-4o-mini model
- **ccxt** — market data from Binance USDS Futures
- **binance-sdk-derivatives-trading-usds-futures** — order placement
- **pandas**, **numpy** — technical indicator calculation
- **python-dotenv** — environment variable loading

## Project Structure

```
bot-trading/
├── main.py                        # FastAPI app, CORS, router registration
├── config.py                      # Load and expose env vars
├── requirements.txt
├── .env                           # Secrets — never commit
├── gemini/
│   ├── api.py                     # APIRouter: GET /gemini/stream (SSE)
│   └── agents_gemini/
│       ├── agent.py               # Base Agent: calls gemini-2.5-flash
│       └── agentic_agent.py       # MasterGemini: LangGraph orchestrator
├── open-ai/
│   ├── api.py                     # APIRouter: GET /openai/stream (SSE)
│   ├── agents_openai/
│   │   ├── agent.py               # Base OpenAI agent (gpt-4o-mini)
│   │   └── agentic_agent.py       # MasterOpenAI: LangGraph orchestrator
│   ├── tools/
│   │   └── openai_tools.py        # OpenAI function definitions
│   └── test_agent.py
└── src/
    ├── binance_connector/
    │   └── binance.py             # BinanceConnector — place bracket orders
    ├── telegram/
    │   └── telegram.py            # Async Telegram notifications
    └── tools/
        └── cx_connector.py        # CXConnector — smc_analysis + create_order
```

## Running

```bash
source venv/bin/activate
pip install -r requirements.txt  # first time or after changes
python main.py                   # http://127.0.0.1:8000, docs at /docs
```

## Environment Variables (`.env`)

| Variable                | Description                                           |
| ----------------------- | ----------------------------------------------------- |
| `API_KEY`               | Google Gemini API key                                 |
| `OPEN_API_KEY`          | OpenAI API key                                        |
| `BINANCE_API_KEY`       | Binance API key                                       |
| `BINANCE_SECRET_KEY`    | Binance secret key                                    |
| `BINANCE_BASE_URL`      | Binance base URL (default: `https://api.binance.com`) |
| `TELEGRAM_TOKEN`        | Telegram bot token                                    |
| `TELEGRAM_CHATID`       | Telegram chat ID                                      |
| `ENV`                   | `development` or `production`                         |
| `APP_HOST` / `APP_PORT` | Server host/port                                      |

## LangGraph State

```python
class MasterState(TypedDict):
    chat_history: List[Content]   # Full conversation history
    agent_response: str           # Latest agent JSON response
    user_prompt: str              # Original user query
    step_count: int               # Current step
    max_steps: int                # Hard limit: 10
    user_feedback: str            # Streamed progress message
```

## Routing

Each agent returns `{ "type": "CATEGORY" }`:

| Type              | Routes to                 |
| ----------------- | ------------------------- |
| `TOOL_AGENT`      | `tools_agent`             |
| `MARKET_ANALYSIS` | `analysis_agent`          |
| `TRADE_DECISION`  | `decision_agent`          |
| `GENERAL_QUERY`   | `master_agent`            |
| `FINAL_RESPONSE`  | `generate_response` → END |

## SSE Streaming

`GET /gemini/stream?query=...` yields:

- `data: {"character": "x"}` — one char at a time (5ms delay)
- `event: end\ndata: Stream finished ✅` — stream complete

## CXConnector Tools

### `smc_analysis(symbol, timeframe, limit=100)`

Fetches OHLCV via ccxt, returns ATR, swing points, order blocks, FVGs, BOS, CHoCH, liquidity, premium/discount zones, Bollinger Bands (14/20/50), EMA (9/20/50), RSI (7/14/21).
**Must be called before `create_order`** — sets `self.current_price`.

### `create_order(symbol, side, entry, stop_loss, take_profit)`

Places a 3-order bracket on Binance USDS Futures: LIMIT entry + TAKE_PROFIT_MARKET + STOP_MARKET.

**Trade defaults:** 20x leverage, $5 USDT order, 0.40% TP, 0.75% SL (leveraged).

## Key Conventions

- Always import env vars from `config.py`, never use `os.getenv` directly elsewhere
- Add new routers to `main.py` via `app.include_router(...)`
- Telegram notifications use `asyncio.create_task(...)` — non-blocking
- The `open-ai/` folder uses dashes; `__init__.py` files make it importable
- Keep `requirements.txt` updated when adding dependencies
