import asyncio
import aiohttp
from datetime import datetime
import json
import time
import functools
import config

token = config.TELEGRAM_TOKEN
chat_id = config.TELEGRAM_CHATID
env = config.ENV

_start_time = time.time()

_cx = None


def _get_cx():
    global _cx
    if _cx is None:
        from tools.cx_connector import CXConnector
        _cx = CXConnector()
    return _cx


def _get_fetch_candles():
    from tools.cx_connector import _fetch_candles
    return _fetch_candles

_binance = None


def _get_binance():
    global _binance
    if _binance is None:
        from connectors.binance_v2 import BinanceConnector
        _binance = BinanceConnector()
    return _binance


async def telegram_bot(message: str, more=None):
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": f"""
                {env}: {message}
                {json.dumps(more, indent=4) if more else ''}
                at: {datetime.now().strftime('%m/%d/%Y, %I:%M:%S %p')}
                """,
            "parse_mode": "HTML",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    raise Exception(f"HTTP error! status: {response.status}")
                data = await response.json()
                return data

    except Exception as e:
        return {"ok": False, "description": str(e)}


# ─── Command Handlers ─────────────────────────────────────────────────────────

async def _cmd_analyze(cmd: str, args: list):
    try:
        if not args:
            await telegram_bot("Usage: /analyze SYMBOL [timeframe] [limit]")
            return
        symbol = args[0].upper()
        timeframe = args[1] if len(args) > 1 else "1h"
        limit = int(args[2]) if len(args) > 2 else 200

        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, _get_cx().smc_analysis, symbol, timeframe, limit)

        if data.get("status") == "error":
            await telegram_bot(f"Analysis error: {data.get('message')}")
            return

        r = data["result"]
        current_price = r.get("current_price", 0)
        trend = r.get("trend", "unknown")

        last_bos = r.get("last_bos")
        if last_bos:
            bos_text = f"{last_bos.get('direction')} @ <code>{last_bos.get('price')}</code>"
        else:
            bos_text = "none"

        last_choch = r.get("last_choch")
        if last_choch:
            choch_text = f"{last_choch.get('direction')} @ <code>{last_choch.get('price')}</code>"
        else:
            choch_text = "none"

        zone = r.get("premium_discount_zone", "unknown")
        zone_pct = r.get("premium_discount_pct", 0)
        rsi14 = r.get("rsi14", 0)

        entries = r.get("potential_entries", [])[:3]

        lines = [
            f"<b>{symbol} {timeframe} Analysis</b>",
            f"Price: <code>{current_price}</code>",
            f"Trend: {trend}",
            f"BOS: {bos_text}",
            f"CHoCH: {choch_text}",
            f"Zone: {zone} ({zone_pct}%)",
            "",
            "<b>Top Entries</b>",
        ]

        if entries:
            for i, e in enumerate(entries, 1):
                entry_type = "LONG" if e.get("type") == "bullish" else "SHORT"
                zone_low = e.get("zone_low", 0)
                zone_high = e.get("zone_high", 0)
                score = e.get("confluence_score", 0)
                dist = e.get("distance_pct", 0)
                lines.append(
                    f"{i}. {entry_type} zone <code>{zone_low} \u2013 {zone_high}</code>"
                    f" | score: {score} | dist: {dist}%"
                )
        else:
            lines.append("No confluence entries found")

        lines.append("")
        lines.append(f"RSI14: {rsi14}")

        await telegram_bot("\n".join(lines))
    except Exception as e:
        await telegram_bot(f"Error: {e}")


async def _cmd_price(cmd: str, args: list):
    try:
        if not args:
            await telegram_bot("Usage: /price SYMBOL")
            return
        symbol = args[0].upper()

        loop = asyncio.get_event_loop()
        candles = await loop.run_in_executor(None, _get_fetch_candles(), symbol, "1h", 25)

        current_price = candles[-1]["close"]
        change_pct = ((candles[-1]["close"] - candles[0]["open"]) / candles[0]["open"]) * 100
        sign = "+" if change_pct >= 0 else ""
        await telegram_bot(
            f"<b>{symbol}</b>  <code>{current_price}</code>  |  24h: {sign}{change_pct:.1f}%"
        )
    except Exception as e:
        await telegram_bot(f"Error: {e}")


async def _cmd_balance(cmd: str, args: list):
    try:
        binance = _get_binance()
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, binance.get_balance)
        await telegram_bot(f"<b>Balance</b>\nUSDT: <code>{binance.balance}</code>")
    except Exception as e:
        await telegram_bot(f"Error: {e}")


async def _cmd_positions(cmd: str, args: list):
    try:
        binance = _get_binance()
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, binance.get_balance)

        open_pos = [p for p in binance.positions if float(p.get("positionAmt", 0)) != 0]

        if not open_pos:
            await telegram_bot("No open positions")
            return

        blocks = []
        for p in open_pos:
            sym = p.get("symbol", "")
            amt = float(p.get("positionAmt", 0))
            side = "LONG" if amt > 0 else "SHORT"
            entry = p.get("entryPrice", "0")
            upnl = float(p.get("unrealizedProfit", 0))
            sign = "+" if upnl >= 0 else ""
            blocks.append(
                f"<b>{sym}</b>  {side}\n"
                f"Size: <code>{abs(amt)}</code>  Entry: <code>{entry}</code>\n"
                f"uPnL: <code>{sign}{upnl}</code> USDT"
            )

        await telegram_bot("\n\n".join(blocks))
    except Exception as e:
        await telegram_bot(f"Error: {e}")


async def _cmd_orders(cmd: str, args: list):
    try:
        if not args:
            await telegram_bot("Usage: /orders SYMBOL")
            return
        symbol = args[0].upper()
        binance = _get_binance()
        loop = asyncio.get_event_loop()

        orders = await loop.run_in_executor(
            None, functools.partial(binance.client.get_open_orders, symbol=symbol)
        )

        if not orders:
            await telegram_bot(f"No open orders for {symbol}")
            return

        lines = [f"<b>Open Orders: {symbol}</b>"]
        for o in orders:
            oid = o.get("orderId", "")
            side = o.get("side", "")
            otype = o.get("type", "")
            price = o.get("price", "0")
            qty = o.get("origQty", "0")
            lines.append(f"#{oid}  {side} {otype} @ <code>{price}</code>  qty: <code>{qty}</code>")

        await telegram_bot("\n".join(lines))
    except Exception as e:
        await telegram_bot(f"Error: {e}")


async def _cmd_cancel(cmd: str, args: list):
    try:
        if not args:
            await telegram_bot("Usage: /cancel SYMBOL")
            return
        symbol = args[0].upper()
        binance = _get_binance()
        loop = asyncio.get_event_loop()

        cancel_fn = getattr(binance.client, "cancel_open_orders", None) or getattr(
            binance.client, "cancel_all_open_orders", None
        )

        if cancel_fn is not None:
            await loop.run_in_executor(
                None, functools.partial(cancel_fn, symbol=symbol)
            )
        else:
            orders = await loop.run_in_executor(
                None, functools.partial(binance.client.get_open_orders, symbol=symbol)
            )
            for o in orders:
                await loop.run_in_executor(
                    None,
                    functools.partial(
                        binance.client.cancel_order, symbol=symbol, orderId=o["orderId"]
                    ),
                )

        await telegram_bot(f"Cancelled all orders for {symbol}")
    except Exception as e:
        await telegram_bot(f"Error: {e}")


async def _cmd_trade(cmd: str, args: list):
    try:
        side = "BUY" if cmd == "/buy" else "SELL"

        if not args:
            await telegram_bot(f"Usage: {cmd} SYMBOL entry=N sl=N tp=N")
            return

        symbol = args[0].upper()
        kv_args = args[1:]

        params = {}
        for token_str in kv_args:
            if "=" not in token_str:
                await telegram_bot(f"Usage: {cmd} SYMBOL entry=N sl=N tp=N")
                return
            k, v = token_str.split("=", 1)
            try:
                params[k.strip()] = float(v.strip())
            except ValueError:
                await telegram_bot(f"Invalid value for '{k}': must be a number")
                return

        missing = [k for k in ("entry", "sl", "tp") if k not in params]
        if missing:
            await telegram_bot(f"Missing required parameters: {', '.join(missing)}")
            return

        loop = asyncio.get_event_loop()
        candles = await loop.run_in_executor(None, _get_fetch_candles(), symbol, "1m", 1)
        current_price = candles[-1]["close"]

        binance = _get_binance()
        await loop.run_in_executor(
            None,
            functools.partial(
                binance.create_orders,
                symbol=symbol,
                side=side,
                order_price=params["entry"],
                current_price=current_price,
                take_profit=params["tp"],
                stop_loss=params["sl"],
            ),
        )
    except Exception as e:
        await telegram_bot(f"Error: {e}")


async def _cmd_status(cmd: str, args: list):
    try:
        uptime = int(time.time() - _start_time)
        h = uptime // 3600
        m = (uptime % 3600) // 60
        s = uptime % 60
        now = datetime.now().strftime("%m/%d/%Y, %I:%M:%S %p")
        await telegram_bot(
            f"<b>Bot Status</b>\n"
            f"Env: {env}\n"
            f"Uptime: {h}h {m}m {s:02d}s\n"
            f"Time: {now}"
        )
    except Exception as e:
        await telegram_bot(f"Error: {e}")


async def _cmd_leverage(cmd: str, args: list):
    try:
        if len(args) < 2:
            await telegram_bot("Usage: /leverage SYMBOL N")
            return
        symbol = args[0].upper()
        leverage_str = args[1]
        try:
            leverage_int = int(leverage_str)
        except ValueError:
            await telegram_bot(f"Invalid leverage value: {leverage_str}")
            return

        binance = _get_binance()
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, functools.partial(binance.set_leverage, symbol, leverage_int)
        )

        if result is not None:
            await telegram_bot(f"Leverage set: {symbol} x{leverage_int}")
        else:
            await telegram_bot(f"Failed to set leverage for {symbol}")
    except Exception as e:
        await telegram_bot(f"Error: {e}")


async def _cmd_help(cmd: str, args: list):
    try:
        await telegram_bot(
            "<b>Available Commands</b>\n"
            "\n"
            "<b>Analysis</b>\n"
            "/analyze SOLUSDT 1h — SMC analysis (timeframe: 1m 5m 15m 1h 4h 1d)\n"
            "/price SOLUSDT — current price + 24h change\n"
            "\n"
            "<b>Account</b>\n"
            "/balance — USDT wallet balance\n"
            "/positions — open positions with uPnL\n"
            "/orders SOLUSDT — list open orders for symbol\n"
            "/cancel SOLUSDT — cancel all orders for symbol\n"
            "\n"
            "<b>Trading</b>\n"
            "/buy SOLUSDT entry=150 sl=148 tp=155\n"
            "/sell SOLUSDT entry=150 sl=152 tp=145\n"
            "\n"
            "<b>Bot</b>\n"
            "/status — uptime and environment\n"
            "/leverage SOLUSDT 10 — set leverage for symbol\n"
            "/help — this message"
        )
    except Exception as e:
        await telegram_bot(f"Error: {e}")


# ─── Command Router ───────────────────────────────────────────────────────────

_COMMAND_MAP = {
    "/analyze": _cmd_analyze,
    "/price": _cmd_price,
    "/balance": _cmd_balance,
    "/positions": _cmd_positions,
    "/orders": _cmd_orders,
    "/cancel": _cmd_cancel,
    "/buy": _cmd_trade,
    "/sell": _cmd_trade,
    "/status": _cmd_status,
    "/leverage": _cmd_leverage,
    "/help": _cmd_help,
}


async def _route_command(text: str):
    if not text.startswith("/"):
        return

    parts = text.split()
    cmd = parts[0].lower()
    args = parts[1:]

    handler = _COMMAND_MAP.get(cmd)
    if handler is None:
        await telegram_bot(f"Unknown command: {cmd}. Send /help for the list.")
        return

    await handler(cmd, args)


# ─── Listener ─────────────────────────────────────────────────────────────────

async def listen_messages():
    """Long-poll Telegram for new messages and print their text.

    Handles both private/group 'message' updates and channel 'channel_post' updates.
    """
    offset = None
    url = f"https://api.telegram.org/bot{token}/getUpdates"

    print("[Telegram] Listener started, waiting for messages...")

    async with aiohttp.ClientSession() as session:
        while True:
            params = {"timeout": 30}
            if offset is not None:
                params["offset"] = offset

            try:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=35)) as response:
                    data = await response.json()

                if not data.get("ok"):
                    print(f"[Telegram] getUpdates error: {data}")
                    await asyncio.sleep(3)
                    continue

                for update in data.get("result", []):
                    offset = update["update_id"] + 1

                    # Private chat or group message
                    msg = update.get("message") or update.get("channel_post")
                    if msg:
                        text = msg.get("text")
                        if text:
                            print(f"[Telegram] {text}")
                            await _route_command(text)

            except Exception as e:
                print(f"[Telegram] polling error: {e}")
                await asyncio.sleep(3)
