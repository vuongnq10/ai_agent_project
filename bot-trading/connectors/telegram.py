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

AGENT_MODEL = "claude-opus-4-6"
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


_master_claude = None


def _get_master_claude():
    global _master_claude
    if _master_claude is None:
        from agents.claude.agentic_agent import MasterClaude

        _master_claude = MasterClaude()
    return _master_claude


_AGENT_FEEDBACK_SEPARATOR = "\n *********************** \n"

_STEP_LABELS = {
    "# Master Agent": "🤖 Routing...",
    "# Analysis Agent": "📊 Analysing confluence...",
    "# Decision Agent": "⚡ Evaluating setup...",
    "# Tool Agent": "📝 Submitting bracket order...",
}


def _fix_num(n, digits=4):
    try:
        return f"{float(n):.{digits}f}"
    except Exception:
        return str(n)


def _format_smc_section(symbol: str, tf: str, data: dict) -> str:
    r = data["result"]
    active_obs = [ob for ob in r.get("order_blocks", []) if not ob.get("mitigated")]
    active_fvgs = [f for f in r.get("fair_value_gaps", []) if not f.get("filled")]

    last_bos = r.get("last_bos")
    bos_text = (
        f"{last_bos['direction']} at {_fix_num(last_bos['price'])}"
        if last_bos
        else "none"
    )

    last_choch = r.get("last_choch")
    choch_text = (
        f"{last_choch['direction']} at {_fix_num(last_choch['price'])}"
        if last_choch
        else "none"
    )

    internal_bos = r.get("internal_last_bos")
    internal_bos_text = (
        f"{internal_bos['direction']} at {_fix_num(internal_bos['price'])}"
        if internal_bos
        else "none"
    )

    internal_choch = r.get("internal_last_choch")
    internal_choch_text = (
        f"{internal_choch['direction']} at {_fix_num(internal_choch['price'])}"
        if internal_choch
        else "none"
    )

    internal_highs = r.get("internal_highs") or []
    internal_highs_text = (
        ", ".join(_fix_num(p["price"]) for p in internal_highs[-3:]) or "none"
    )

    internal_lows = r.get("internal_lows") or []
    internal_lows_text = (
        ", ".join(_fix_num(p["price"]) for p in internal_lows[-3:]) or "none"
    )

    obs_text = (
        "\n".join(
            f"  {ob['type'].upper()} OB: {_fix_num(ob['low'])} – {_fix_num(ob['high'])}  strength={ob.get('strength')}"
            for ob in active_obs[-4:]
        )
        or "none"
    )

    fvgs_text = (
        "\n".join(
            f"  {f['type'].upper()} FVG: {_fix_num(f['low'])} – {_fix_num(f['high'])}  strength={f.get('strength')}"
            for f in active_fvgs[-4:]
        )
        or "none"
    )

    entries_text = (
        "\n".join(
            f"  {e['type'].upper()} zone: {_fix_num(e['zone_low'])} – {_fix_num(e['zone_high'])}"
            f"  confluence={e.get('confluence_score')}  OB={e.get('ob_strength')}  FVG={e.get('fvg_strength')}  dist={_fix_num(e.get('distance_pct', 0), 2)}%"
            for e in r.get("potential_entries", [])[:3]
        )
        or "none"
    )

    buy_liq = (
        ", ".join(_fix_num(v) for v in r.get("buy_side_liquidity", [])[:3]) or "none"
    )
    sell_liq = (
        ", ".join(_fix_num(v) for v in r.get("sell_side_liquidity", [])[:3]) or "none"
    )
    # candles = r.get("candles", [])

    lines = [
        f"### {symbol} — {tf} Timeframe",
        f"Current Price: {_fix_num(r.get('current_price', 0))}",
        f"Trend: {r.get('trend', 'unknown').upper()}",
        f"ATR(14): {_fix_num(r.get('atr', 0))}",
        "",
        "**Swing Structure**",
        f"BOS:   {bos_text}",
        f"CHoCH: {choch_text}",
        "",
        "**Internal Structure (size-5 pivots)**",
        f"BOS:   {internal_bos_text}",
        f"CHoCH: {internal_choch_text}",
        f"Internal Highs (recent): {internal_highs_text}",
        f"Internal Lows  (recent): {internal_lows_text}",
        "",
        "**Premium / Discount**",
        f"Range:       {_fix_num(r.get('range_low', 0))} – {_fix_num(r.get('range_high', 0))}",
        f"Equilibrium: {_fix_num(r.get('equilibrium', 0))}",
        f"Zone:        {r.get('premium_discount_zone', 'unknown')} ({_fix_num(r.get('premium_discount_pct', 0), 1)}%)",
        "",
        "**Order Blocks — unmitigated (strength 0–100)**",
        obs_text,
        "",
        "**Fair Value Gaps — unfilled (strength 0–100)**",
        fvgs_text,
        "",
        "**Potential Entry Zones (OB + FVG confluence)**",
        entries_text,
        "",
        "**Liquidity**",
        f"Buy-side  (above): {buy_liq}",
        f"Sell-side (below): {sell_liq}",
        "",
        "**Indicators**",
        f"EMA9: {_fix_num(r.get('ema9') or 0)}  EMA20: {_fix_num(r.get('ema20') or 0)}  EMA50: {_fix_num(r.get('ema50') or 0)}",
        f"RSI7: {_fix_num(r.get('rsi7') or 0, 1)}  RSI14: {_fix_num(r.get('rsi14') or 0, 1)}  RSI21: {_fix_num(r.get('rsi21') or 0, 1)}",
        f"BB Upper: {_fix_num(r.get('bb_upper') or 0)}  BB Mid: {_fix_num(r.get('bb_middle') or 0)}  BB Lower: {_fix_num(r.get('bb_lower') or 0)}",
        "",
        # "**Last 50 Candles**",
        # "```json",
        # json.dumps(candles, indent=2),
        # "```",
    ]
    return "\n".join(lines)


def _build_smc_snapshot_msg(symbol: str, tf_results: list) -> str:
    lines = [f"<b>📊 SMC Snapshot — {symbol}</b>"]
    for tf, data in tf_results:
        r = data["result"]
        price = _fix_num(r.get("current_price", 0))
        trend = r.get("trend", "?").upper()
        zone = r.get("premium_discount_zone", "?")
        zpct = _fix_num(r.get("premium_discount_pct", 0), 1)
        rsi14 = _fix_num(r.get("rsi14") or 0, 1)
        bos = r.get("last_bos")
        choch = r.get("last_choch")
        bos_txt = f"{bos['direction']} <code>{_fix_num(bos['price'])}</code>" if bos else "—"
        choch_txt = f"{choch['direction']} <code>{_fix_num(choch['price'])}</code>" if choch else "—"
        top_e = (r.get("potential_entries") or [{}])[0]
        entry_txt = (
            f"<code>{_fix_num(top_e['zone_low'])}–{_fix_num(top_e['zone_high'])}</code> sc={top_e.get('confluence_score')}"
            if top_e.get("zone_low") else "none"
        )
        lines += [
            f"\n<b>{tf}</b>  price=<code>{price}</code>  trend={trend}  rsi={rsi14}",
            f"  BOS {bos_txt}  CHoCH {choch_txt}",
            f"  zone={zone}({zpct}%)  entry={entry_txt}",
        ]
    return "\n".join(lines)


def _build_smc_order_prompt(symbol: str, tf_results: list) -> str:
    sections = [
        _format_smc_section(symbol, tf, data) + "\n\n---" for tf, data in tf_results
    ]
    parts = [
        f"The following SMC analysis was fetched from the backend for {symbol}.",
        "Analyze the multi-timeframe data (4h bias → 2h setup → 30m execution), determine the highest-probability SMC trade setup at 20x leverage (target +15–20% account / -10–12% max loss, min RR 1.5), then create an order if conditions are met.",
        "",
        "---",
        "",
        *sections,
    ]
    return "\n".join(parts)


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


async def _cmd_analyze(_: str, args: list):
    try:
        if not args:
            await telegram_bot("Usage: /analyze SYMBOL [timeframe] [limit]")
            return
        raw = args[0].upper()
        symbol = raw if raw.endswith("USDT") else raw + "USDT"
        timeframe = args[1] if len(args) > 1 else "1h"
        limit = int(args[2]) if len(args) > 2 else 200

        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(
            None, _get_cx().smc_analysis, symbol, timeframe, limit
        )

        if data.get("status") == "error":
            await telegram_bot(f"Analysis error: {data.get('message')}")
            return

        r = data["result"]
        current_price = r.get("current_price", 0)
        trend = r.get("trend", "unknown")

        last_bos = r.get("last_bos")
        if last_bos:
            bos_text = (
                f"{last_bos.get('direction')} @ <code>{last_bos.get('price')}</code>"
            )
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


async def _cmd_price(_: str, args: list):
    try:
        if not args:
            await telegram_bot("Usage: /price SYMBOL")
            return
        raw = args[0].upper()
        symbol = raw if raw.endswith("USDT") else raw + "USDT"

        loop = asyncio.get_event_loop()
        candles = await loop.run_in_executor(
            None, _get_fetch_candles(), symbol, "1h", 25
        )

        current_price = candles[-1]["close"]
        change_pct = (
            (candles[-1]["close"] - candles[0]["open"]) / candles[0]["open"]
        ) * 100
        sign = "+" if change_pct >= 0 else ""
        await telegram_bot(
            f"<b>{symbol}</b>  <code>{current_price}</code>  |  24h: {sign}{change_pct:.1f}%"
        )
    except Exception as e:
        await telegram_bot(f"Error: {e}")


async def _cmd_balance(*_):
    try:
        binance = _get_binance()
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, binance.get_balance)
        await telegram_bot(f"<b>Balance</b>\nUSDT: <code>{binance.balance}</code>")
    except Exception as e:
        await telegram_bot(f"Error: {e}")


async def _cmd_positions(*_):
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


async def _cmd_orders(_: str, args: list):
    try:
        if not args:
            await telegram_bot("Usage: /orders SYMBOL")
            return
        raw = args[0].upper()
        symbol = raw if raw.endswith("USDT") else raw + "USDT"
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
            lines.append(
                f"#{oid}  {side} {otype} @ <code>{price}</code>  qty: <code>{qty}</code>"
            )

        await telegram_bot("\n".join(lines))
    except Exception as e:
        await telegram_bot(f"Error: {e}")


async def _cmd_cancel(_: str, args: list):
    try:
        if not args:
            await telegram_bot("Usage: /cancel SYMBOL")
            return
        raw = args[0].upper()
        symbol = raw if raw.endswith("USDT") else raw + "USDT"
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

        raw = args[0].upper()
        symbol = raw if raw.endswith("USDT") else raw + "USDT"
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
        candles = await loop.run_in_executor(
            None, _get_fetch_candles(), symbol, "1m", 1
        )
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


async def _cmd_status(*_):
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


async def _cmd_leverage(_: str, args: list):
    try:
        if len(args) < 2:
            await telegram_bot("Usage: /leverage SYMBOL N")
            return
        raw = args[0].upper()
        symbol = raw if raw.endswith("USDT") else raw + "USDT"
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


async def _cmd_order(_: str, args: list):
    try:
        if not args:
            await telegram_bot("Usage: /order SYMBOL  (e.g. /order BTCUSDT)")
            return

        raw = args[0].upper()
        symbol = raw if raw.endswith("USDT") else raw + "USDT"
        await telegram_bot(
            f"⚡ <b>Quick SMC — {symbol}</b>\nFetching 30m / 2h / 4h data..."
        )

        loop = asyncio.get_event_loop()
        cx = _get_cx()

        results_4h, results_2h, results_30m = await asyncio.gather(
            loop.run_in_executor(None, cx.smc_analysis, symbol, "4h", 200),
            loop.run_in_executor(None, cx.smc_analysis, symbol, "2h", 200),
            loop.run_in_executor(None, cx.smc_analysis, symbol, "30m", 200),
        )

        tf_results = [("4h", results_4h), ("2h", results_2h), ("30m", results_30m)]

        for tf, data in tf_results:
            if data.get("status") == "error":
                await telegram_bot(
                    f"<b>Fetch error [{tf}] {symbol}</b>\n<code>{data.get('message')}</code>"
                )
                return

        await telegram_bot(_build_smc_snapshot_msg(symbol, tf_results))

        prompt = _build_smc_order_prompt(symbol, tf_results)
        await telegram_bot(f"🤖 <b>AI analysis started — {symbol}</b>\nRunning multi-agent SMC pipeline...")

        master = _get_master_claude()
        session_id = f"tg_order_{symbol}_{int(time.time())}"
        agent_final_response = []

        def run_agent():
            for chunk in master(prompt, session_id=session_id, model=AGENT_MODEL):
                clean = chunk.replace(_AGENT_FEEDBACK_SEPARATOR, "").strip()
                if not clean:
                    continue
                label = None
                for key, msg in _STEP_LABELS.items():
                    if clean.startswith(key):
                        label = msg
                        break
                if label:
                    body = "\n".join(clean.split("\n")[1:]).strip()
                    msg_text = f"{label}\n\n{body[:3000]}" if body else label
                else:
                    msg_text = clean[:3500]
                    agent_final_response[:] = [clean]
                fut = asyncio.run_coroutine_threadsafe(telegram_bot(msg_text), loop)
                fut.result(timeout=15)

        await loop.run_in_executor(None, run_agent)

        if agent_final_response:
            await telegram_bot(
                f"<b>📋 Agent Response — {symbol}</b>\n\n{agent_final_response[0][:3500]}"
            )
        await telegram_bot(f"✅ <b>Analysis complete — {symbol}</b>")

    except Exception as e:
        await telegram_bot(f"<b>❌ Error</b> /order {symbol if 'symbol' in dir() else ''}\n<code>{e}</code>")


async def _cmd_cancel_all(*_):
    try:
        binance = _get_binance()
        loop = asyncio.get_event_loop()

        orders = await loop.run_in_executor(None, binance.client.get_open_orders)

        if not orders:
            await telegram_bot("No open orders to cancel.")
            return

        symbols = list({o["symbol"] for o in orders})
        cancelled = 0
        errors = []

        for sym in symbols:
            try:
                cancel_fn = getattr(binance.client, "cancel_open_orders", None)
                if cancel_fn:
                    await loop.run_in_executor(
                        None, functools.partial(cancel_fn, symbol=sym)
                    )
                else:
                    sym_orders = [o for o in orders if o["symbol"] == sym]
                    for o in sym_orders:
                        await loop.run_in_executor(
                            None,
                            functools.partial(
                                binance.client.cancel_order,
                                symbol=sym,
                                orderId=o["orderId"],
                            ),
                        )
                cancelled += len([o for o in orders if o["symbol"] == sym])
            except Exception as e:
                errors.append(f"{sym}: {e}")

        lines = [f"✅ Cancelled {cancelled} order(s) across {len(symbols)} symbol(s)."]
        if errors:
            lines.append("⚠️ Errors:")
            lines.extend(errors)
        await telegram_bot("\n".join(lines))

    except Exception as e:
        await telegram_bot(f"❌ /cancel_all error: {e}")


async def _cmd_help(*_):
    try:
        await telegram_bot(
            "<b>Available Commands</b>\n"
            "\n"
            "<b>Analysis</b>\n"
            "/analyze SOLUSDT 1h — SMC analysis (timeframe: 1m 5m 15m 1h 4h 1d)\n"
            "/price SOLUSDT — current price + 24h change\n"
            "\n"
            "<b>AI Trading</b>\n"
            "/order BTCUSDT — ⚡ Quick SMC 30m/2h/4h: AI analyses and places order if conditions met\n"
            "\n"
            "<b>Account</b>\n"
            "/balance — USDT wallet balance\n"
            "/positions — open positions with uPnL\n"
            "/orders SOLUSDT — list open orders for symbol\n"
            "/cancel SOLUSDT — cancel all orders for symbol\n"
            "/cancel_all — cancel ALL open orders across all symbols\n"
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
    "/cancel_all": _cmd_cancel_all,
    "/buy": _cmd_trade,
    "/sell": _cmd_trade,
    "/order": _cmd_order,
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
                async with session.get(
                    url, params=params, timeout=aiohttp.ClientTimeout(total=35)
                ) as response:
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
