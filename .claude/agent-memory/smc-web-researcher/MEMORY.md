# SMC Web Researcher Memory

## Key File Paths
- SMC analysis: `bot-trading/src/tools/cx_connector.py`
- Binance connector: `bot-trading/src/binance_connector/binance.py`
- Gemini agent: `bot-trading/gemini/agents_gemini/agentic_agent.py`
- OpenAI agent: `bot-trading/open-ai/agents_openai/agentic_agent.py`

## Architecture Decisions
- All SMC functions operate on a pandas DataFrame (not dict-of-lists)
- DataFrame columns: timestamp, open, high, low, close, volume
- ATR uses Wilder's smoothing (period=14), used throughout for thresholds
- Swing detection uses fractal method with configurable swing_length (default=5)
- BOS/CHoCH are unified in one function tracking structure direction
- Output is trimmed (last N items) to avoid flooding LLM context

## SMC Implementation Patterns
- **Swing Points**: Fractal detection with deduplication of consecutive same-type swings
- **Order Blocks**: Last opposing candle before impulsive move (>0.5 ATR), width filter (<2 ATR), mitigation tracking
- **FVG**: 3-candle pattern, mitigation = close enters gap zone, fill_percent tracked
- **BOS**: Close beyond swing level IN direction of trend (continuation)
- **CHoCH**: Close beyond swing level AGAINST trend (reversal) -- requires structure tracking
- **Liquidity**: Cluster swing points within range_percent (1%), sweep = wick beyond + close back
- **Premium/Discount**: Uses most recent swing range, includes Fibonacci levels

## Reliable SMC Sources
- joshyattridge/smart-money-concepts (PyPI: smartmoneyconcepts) -- best reference implementation
- FluxCharts articles -- clear OB definitions
- TradingFinder BOS vs CHoCH article -- best BOS/CHoCH classification rules
- LuxAlgo TradingView indicators -- good for cross-referencing logic

## Critical Rules (ICT)
- BOS/CHoCH require candle CLOSE beyond the level, not just wick
- OB = last opposing candle, NOT any candle before the move
- FVG timestamp should reference the MIDDLE candle (the impulsive one)
- Liquidity sweep = wick beyond level but close back inside (stop hunt)

## Edge Cases
- Less than 20 candles: return error early
- No swing points found: return empty lists, premium/discount returns None
- EMA returns last 5 values only (not full series) to keep output concise
