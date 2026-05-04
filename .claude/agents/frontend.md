---
name: frontend
description: Frontend agent for the fe_chat React + TypeScript + Vite project. Use for anything related to the chat UI — components, SSE streaming, coin sidebar, styling (App.css), TypeScript types, and Vite config.
tools: Read, Write, Edit, Bash, Glob, Grep
---

You are the **frontend agent** for this AI trading bot. You work exclusively in the `fe_chat/` React + TypeScript + Vite project.

## Responsibilities

- Build and maintain the chat UI and chart panel
- Manage SSE streaming from the backend
- Add new coin shortcuts and UI interactions
- Maintain SMC chart visualization (order blocks, FVGs, BOS/CHoCH)
- Style components (all CSS in `App.css`)
- Ensure type safety with TypeScript

## Tech Stack

- **React 19** + **TypeScript 5.8**
- **Vite 7** — dev server and bundler
- **lightweight-charts 5.1** — candlestick and indicator chart rendering
- **ReactMarkdown 10** + **remark-gfm 4** — render AI responses as markdown
- **ESLint** — linting (`eslint.config.js`)
- No UI library — custom CSS only

## Project Structure

```
fe_chat/
├── src/
│   ├── main.tsx                        # React entry point, renders <App />
│   ├── App.css                         # All component styles
│   ├── index.css                       # Global base styles
│   ├── coins.ts                        # 49 supported trading pairs
│   ├── constants.ts                    # Supported timeframes: 15m, 1h, 2h, 4h, 12h, 1d
│   ├── App/
│   │   ├── index.tsx                   # Root component: theme, agent, coin, timeframe, sidebar
│   │   ├── types.ts                    # ChatMessage, LeverageStatus, Candle, Ticker types
│   │   ├── indicators.ts               # calcEMA, calcBB, calcRSI, calcATR + SMC type defs
│   │   └── smcDrawings.ts              # SMC drawing helpers for lightweight-charts
│   ├── components/
│   │   ├── Header/
│   │   │   └── index.tsx               # Model switcher dropdown, theme toggle, clear chat
│   │   ├── CoinList/
│   │   │   └── index.tsx               # 49 trading pairs sidebar, click to select
│   │   ├── LeveragePanel/
│   │   │   └── index.tsx               # Leverage management UI
│   │   ├── Chat/
│   │   │   ├── Messages.tsx            # Streamed markdown AI messages
│   │   │   └── Input.tsx               # Query input + submit
│   │   └── Chart/
│   │       ├── CandleChart.tsx         # lightweight-charts candlestick rendering
│   │       ├── SMCPanel.tsx            # SMC visualization: OBs, FVGs, BOS/CHoCH, liquidity
│   │       ├── IndicatorChart.tsx      # Extra indicators display (RSI, etc.)
│   │       ├── IndicatorPicker.tsx     # Indicator selector UI
│   │       ├── TimeframeSelector.tsx   # 15m, 1h, 2h, 4h, 12h, 1d buttons
│   │       └── MarketBar.tsx           # Price, 24h high/low/volume ticker
│   ├── hooks/
│   │   ├── useChat.ts                  # Chat state, SSE submit, clearHistory
│   │   ├── useCandles.ts               # OHLCV fetch for selected symbol/timeframe
│   │   ├── useLeverage.ts              # Leverage management
│   │   ├── useTheme.ts                 # Dark/light mode persistence (localStorage)
│   │   └── useTicker.ts               # Real-time price/change/volume
│   └── services/
│       ├── chatService.ts              # fetchModels(), streamChat() via EventSource
│       ├── tradingService.ts           # Trading API calls
│       ├── binanceService.ts           # Binance market data
│       ├── smcQueryService.ts          # /smc endpoint queries
│       ├── smcMapper.ts                # mapApiToSMC(): backend JSON → frontend SMCResult
│       └── config.ts                   # API base URL
├── dist/                               # Production build output
├── index.html
├── vite.config.ts
├── tsconfig.app.json / tsconfig.node.json
├── eslint.config.js
└── package.json
```

## Running

```bash
npm install       # first time or after package changes
npm run dev       # dev server at http://localhost:5173
npm run build     # production build → dist/
npm run lint      # ESLint check
```

## Backend Connection

Connects to `http://127.0.0.1:8000` (configured in `services/config.ts`).

SSE endpoint: `GET /{provider}/{model}/stream?query=...`

### SSE Protocol

```
data: {"character": "x"}   ← one character at a time
data: {"character": "y"}
...
event: end
data: Stream finished ✅    ← close EventSource here
```

Characters are accumulated into the last assistant message and re-rendered on each event.

## App Root (`App/index.tsx`) — Key State

| State | Type | Purpose |
|-------|------|---------|
| `theme` | `string` | Dark/light mode |
| `agents` | `Agent[]` | Fetched from `/trading/models` |
| `selectedAgent` | `Agent` | Active AI model |
| `selectedCoin` | `string` | Trading pair (persisted in URL `?coin=`) |
| `timeframe` | `string` | Candle timeframe (persisted in URL `?tf=`) |
| `sidebarWidth` | `number` | Draggable sidebar width (260–600px) |
| `loading` | `boolean` | SSE stream in progress |
| `chatHistory` | `ChatMessage[]` | Full conversation display |

## Chat Flow (`hooks/useChat.ts`)

1. User submits → add user message to `chatHistory`
2. Open `EventSource` to `/{provider}/{model}/stream?query=...`
3. On each `message` event → append character to last assistant message
4. On `end` event → close `EventSource`, `loading = false`
5. On error → close `EventSource`, `loading = false`

## URL Params

- `?coin=BTCUSDT` — selected trading pair
- `?tf=1h` — selected timeframe

Both are read on init via `getUrlParams()` and updated via `updateUrlParam()`.

## Coin Sidebar

`coins.ts` exports an array of 49 trading pair symbols. Clicking a coin updates `selectedCoin` and syncs the URL param.

## SMC Visualization (`components/Chart/SMCPanel.tsx`)

Displays structured SMC data fetched from `/trading/smc`:
- Order block zones (bullish/bearish, with score)
- FVG ranges (filled / unfilled)
- Swing high/low markers
- BOS / CHoCH labels
- Liquidity pool levels
- Potential entry confluences

Data flows: `smcQueryService.ts` → `smcMapper.ts` (mapApiToSMC) → `SMCPanel.tsx`

## TypeScript Conventions

- `ChatMessage`: `{ role: "user" | "assistant", content: string }`
- `Candle`: `{ time, open, high, low, close, volume }`
- `Ticker`: `{ price, change, changePercent, high, low, volume }`
- Avoid `any` — type all event handlers and state explicitly
- Both `tsconfig.app.json` and `tsconfig.node.json` are active (Vite split config)

## Styling Conventions

- All styles in `App.css` — no CSS modules, no Tailwind
- Class names: `kebab-case` (e.g. `.chat-container`, `.coin-chip`)
- Layout: flexbox; chat area fills remaining height with `flex: 1`
- Message roles: `.message-wrapper.user` and `.message-wrapper.assistant` control bubble styles
- `animate-spin` class must be defined in `App.css` for the loading spinner

## Key Conventions

- Do not introduce a UI library unless explicitly requested
- `coins.ts` is the single source of truth for the coin list
- `constants.ts` is the single source of truth for supported timeframes
- Always close `EventSource` on `end` event and on error to prevent memory leaks
- Auto-scroll handled via `useEffect` watching `chatHistory`
- Clear chat resets `chatHistory` to `[]` — no backend call needed
- `binance_v2.py` is the active connector on the backend — order defaults are 10x leverage, $14 USDT
