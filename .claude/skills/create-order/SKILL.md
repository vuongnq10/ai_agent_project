---
name: create-order
description: Place a leveraged futures order on Binance via the AI trading bot. Use when the user wants to open a trade, place a buy/sell order, or execute a bracket order (entry + take profit + stop loss). Arguments: [symbol] [side] [entry] [stop_loss] [take_profit]
argument-hint: [symbol] [side BUY|SELL] [entry price] [stop_loss price] [take_profit price]
user-invocable: true
allowed-tools: Read, Grep, Bash
---

# Place a Binance Futures Order

Place a leveraged bracket order for **$ARGUMENTS**.

## Order Details

Parse `$ARGUMENTS` as: `<symbol> <side> <entry> <stop_loss> <take_profit>`

- **symbol** — Trading pair (e.g., `SOLUSDT`, `BTCUSDT`)
- **side** — `BUY` or `SELL`
- **entry** — Limit entry price
- **stop_loss** — Stop loss price
- **take_profit** — Take profit price

If any argument is missing, ask the user to provide it before proceeding.

## How It Works

The `create_order` tool in `CXConnector` places **3 orders** simultaneously on Binance USDS Futures:

| # | Type                  | Description                                    |
|---|-----------------------|------------------------------------------------|
| 1 | `LIMIT`               | Entry order at the specified price             |
| 2 | `TAKE_PROFIT_MARKET`  | Auto-closes position when TP price is reached  |
| 3 | `STOP_MARKET`         | Auto-closes position when SL price is reached  |

## Trade Parameters

| Parameter     | Value                    |
|---------------|--------------------------|
| Leverage      | **20x**                  |
| Order amount  | **$5 USDT**              |
| TP % (raw)    | 0.40% (leveraged = 8%)   |
| SL % (raw)    | 0.75% (leveraged = 15%)  |

> Note: The system uses internal TP/SL percentages from `BinanceConnector`. The `stop_loss` and `take_profit` values passed to `create_order` are used as hints to the AI agent but the actual prices are recalculated from `EXPECTED_PROFIT` and `EXPECTED_STOP_LOSS` constants.

## Validation Rules

- **BUY**: `entry` must be **≤ current price** (limit below market)
- **SELL**: `entry` must be **≥ current price** (limit above market)
- If validation fails, the order is rejected and a Telegram notification is sent

## Key Files

- [cx_connector.py](bot-trading/src/tools/cx_connector.py) — `CXConnector.create_order()`
- [binance.py](bot-trading/src/binance_connector/binance.py) — `BinanceConnector.create_orders()`

## Example Usage

```
/create-order SOLUSDT BUY 130.5 128.0 135.0
```

Places a BUY bracket order on SOLUSDT:
- Entry: $130.50 (LIMIT)
- Stop loss: $128.00 (STOP_MARKET)
- Take profit: $135.00 (TAKE_PROFIT_MARKET)
- Leverage: 20x, Amount: $5 USDT

## Steps

1. Confirm all 5 required arguments are present
2. Validate the side and price relationship (BUY entry ≤ current price; SELL entry ≥ current price)
3. Display a summary of the order to the user for confirmation
4. Instruct the user to trigger the order via the chat UI or API:
   - **Chat UI**: Send a message like `"Place order SOLUSDT BUY entry=130.5 sl=128 tp=135"` to the Gemini or OpenAI stream endpoint
   - **Direct API**: `GET http://127.0.0.1:8000/gemini/stream?query=create_order+SOLUSDT+BUY+130.5+128+135`
5. Monitor Telegram for order confirmation notifications
