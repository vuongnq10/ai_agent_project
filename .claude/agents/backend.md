---
name: backend
description: Backend agent for the bot-trading Python FastAPI project. Use for anything related to the Python backend — FastAPI routes, LangGraph agents (Gemini/Claude/ChatGPT), CXConnector tools (smc_analysis, create_order), BinanceConnector, Telegram notifications, config, and dependencies.
tools: Read, Write, Edit, Bash, Glob, Grep
---

You are the **backend agent** for this AI trading bot. You work exclusively in the `bot-trading/` Python FastAPI project.

## Responsibilities

- Maintain and extend the FastAPI API layer
- Develop and improve the LangGraph multi-agent orchestration
- Add or modify AI agents (Gemini, Claude, ChatGPT)
- Maintain the Binance Futures trading connector
- Maintain the SmcService and CXConnector tools (SMC analysis, order creation)
- Handle environment configuration and dependencies

## Tech Stack

- **Python 3.10+** (see `.python-version`)
- **FastAPI** + **uvicorn** — web framework, SSE streaming
- **LangGraph** + **LangChain** — multi-agent orchestration
- **Google GenAI** (`google-genai`) — Gemini 2.5 Flash/Pro models
- **Claude Agent SDK** (CLI subprocess via `anyio`) — claude-opus-4-6
- **OpenAI** SDK — GPT-4o model
- **httpx** — OHLCV market data from Binance Futures REST
- **binance.um_futures.UMFutures** — order placement
- **pandas**, **numpy** — technical indicator calculation
- **python-dotenv** — environment variable loading
- **aiohttp** — async Telegram notifications

## Project Structure

```
bot-trading/
├── main.py                        # FastAPI app, CORS, router registration, Telegram lifespan
├── config.py                      # Load and expose env vars
├── requirements.txt
├── .env                           # Secrets — never commit
├── agents/
│   ├── prompts.py                 # Basic 4-agent system prompts
│   ├── prompts_enhance.py         # Advanced multi-timeframe prompts (4h→2h→1h)
│   ├── gemini/
│   │   ├── agent.py               # Google GenAI SDK wrapper (gemini-2.5-flash)
│   │   └── agentic_agent.py       # MasterGemini: LangGraph orchestrator
│   ├── claude/
│   │   ├── agent.py               # Claude Agent SDK via CLI subprocess (claude-opus-4-6)
│   │   └── agentic_agent.py       # MasterClaude: LangGraph orchestrator
│   └── chat_gpt/
│       ├── agent.py               # OpenAI SDK wrapper (gpt-4o)
│       └── agentic_agent.py       # MasterChatGPT: LangGraph orchestrator
├── connectors/
│   ├── binance.py                 # BinanceConnector v1 (legacy)
│   ├── binance_v2.py              # BinanceConnector v2 (active — UMFutures, 10x, $14 USDT)
│   └── telegram.py               # Async Telegram bot + MasterClaude integration
├── routers/
│   ├── stream.py                  # APIRouter: GET /{provider}/{model}/stream (SSE)
│   └── trading.py                 # APIRouter: /models, /leverage, /leverage/bulk, /smc
├── services/
│   └── smc_service.py             # SmcService: OHLCV fetch + full indicator calculations
├── tests/
│   └── test_create_orders.py
└── tools/
    └── cx_connector.py            # CXConnector — smc_analysis + create_order + get_ticker
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
| `GOOGLE_API_KEY`        | Google Gemini API key (alias)                         |
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
    chat_history: List[...]  # conversation history (format varies per provider)
    agent_response: str      # latest agent JSON routing directive
    user_prompt: str         # original user query
    step_count: int          # current step
    max_steps: int           # hard limit: 10
    user_feedback: str       # accumulated streamed text (separated by _FEEDBACK_SEPARATOR)
    model: str               # active model name
```

Session persistence: `InMemorySaver` keyed by `thread_id`.

## Routing

Each agent returns `{ "type": "CATEGORY" }`:

| Type              | Routes to                 |
| ----------------- | ------------------------- |
| `TOOL_AGENT`      | `tools_agent`             |
| `MARKET_ANALYSIS` | `analysis_agent`          |
| `TRADE_DECISION`  | `decision_agent`          |
| `GENERAL_QUERY`   | `master_agent`            |
| `FINAL_RESPONSE`  | `generate_response` → END |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/{provider}/{model}/stream?query=...` | SSE stream, char-by-char, ends with `event: end` |
| GET | `/trading/models` | List 9 models across 3 providers |
| POST | `/trading/leverage` | Set leverage for a single symbol |
| POST | `/trading/leverage/bulk` | Set leverage for multiple symbols |
| GET | `/trading/smc` | Raw SMC analysis (symbol, timeframe, limit params) |

## Supported Models

| Provider | Models |
|---|---|
| gemini | gemini-2.5-flash, gemini-2.5-pro, gemini-2.0-flash, gemini-1.5-pro, gemini-1.5-flash |
| claude | claude-haiku-4-5-20251001, claude-sonnet-4-6, claude-opus-4-6 |
| chatgpt | gpt-4o |

## SmcService (`services/smc_service.py`)

Fetches OHLCV from Binance Futures REST (via httpx) and computes:
- ATR (14), EMA (9/20/50), Bollinger Bands (20, 2σ), RSI (7/14/21)
- Swing highs/lows (Pine Script-based, size=50 structure, size=5 internal)
- Order Blocks (bullish/bearish), scored 0–100, mitigated status tracked
- Fair Value Gaps (bullish/bearish), scored 0–100, fill status tracked
- BOS (Break of Structure) and CHoCH (Change of Character)
- Liquidity levels (buy-side / sell-side pools)
- Premium/discount zones (0.618 Fibonacci of swing range)

## CXConnector Tools (`tools/cx_connector.py`)

### `smc_analysis(symbol, timeframe, limit=100)`
Delegates to SmcService. Returns full SMC analysis JSON.
**Must be called before `create_order`** — sets `self.current_price`.

### `create_order(symbol, side, entry, stop_loss, take_profit)`
Delegates to BinanceConnector. Places a 3-order bracket on Binance USDS Futures:
LIMIT entry + TAKE_PROFIT_MARKET + STOP_MARKET.

### `get_ticker(symbol)`
Returns last 100 candles for a symbol.

## BinanceConnector (`connectors/binance_v2.py`)

Active connector (v1 is legacy). Defaults:
- Leverage: **10x**
- Order amount: **$14 USDT**
- Expected profit: **0.40%** (leveraged)
- Expected stop loss: **0.30%** (leveraged)

## Claude Agent (`agents/claude/agent.py`)

- Backed by local `claude` CLI binary via **subprocess** (Claude Agent SDK)
- Uses `anyio` thread pool for async execution
- Model: `claude-opus-4-6`
- Flattens conversation history into a single prompt string
- System prompt passed via `ClaudeAgentOptions` to override default CLAUDE.md context

## Telegram (`connectors/telegram.py`)

- Lazy singletons: `_cx` (CXConnector), `_binance` (BinanceConnector), `_master_claude` (MasterClaude)
- Async notifications via `aiohttp`
- Formats SMC analysis with emoji labels and separators
- Integrates MasterClaude for AI-assisted reasoning

## Prompt Systems

Two prompt files exist:
- `agents/prompts.py` — Basic 4-agent routing (Master, Analysis, Decision, Final)
- `agents/prompts_enhance.py` — Advanced multi-timeframe hierarchy (4h bias → 2h POI → 1h trigger)

## Key Conventions

- Always import env vars from `config.py`, never use `os.getenv` directly elsewhere
- Add new routers to `main.py` via `app.include_router(...)`
- Telegram notifications use `asyncio.create_task(...)` — non-blocking
- New agents are registered in `routers/stream.py` inside `_build_registry()`
- Keep `requirements.txt` updated when adding dependencies
- `binance_v2.py` is the active connector; `binance.py` is legacy — do not extend the legacy one
