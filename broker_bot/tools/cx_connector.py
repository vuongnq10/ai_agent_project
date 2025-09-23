import ccxt
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime
from google.genai.types import Tool, FunctionDeclaration

from broker_bot.telegram.telegram import telegram_bot

from broker_bot.binance_connector.binance import BinanceConnector

binance = ccxt.binance({})
binance_connector = BinanceConnector()


class CXConnector:
    def __init__(self):
        self.tools = Tool(
            function_declarations=[
                FunctionDeclaration(
                    name="smc_analysis",
                    description="Perform Smart Money Concept analysis on live candle chart by given symbol and timeframe.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "The trading pair symbol (e.g., 'SOLUSDT').",
                            },
                            "timeframe": {
                                "type": "string",
                                "description": "The timeframe for the analysis (e.g., 1h, 2h, 4h ).",
                                "default": "1h",
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Number of candles to fetch for analysis.",
                                "default": 100,
                            },
                        },
                        "required": ["symbol", "timeframe"],
                    },
                ),
                FunctionDeclaration(
                    name="create_order",
                    description="Save a 20 leverage trade setup with entry, stop loss, and take profit.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "The trading pair symbol (e.g., 'SOLUSDT').",
                            },
                            "side": {
                                "type": "string",
                                "description": "Type of order (e.g., 'BUY', 'SELL').",
                            },
                            "entry": {
                                "type": "number",
                                "description": "Entry price for the trade. ",
                            },
                            "stop_loss": {
                                "type": "string",
                                "description": "Stop loss price for the trade. String representation of a float.",
                            },
                            "take_profit": {
                                "type": "string",
                                "description": "Take profit price for the trade. String representation of a float.",
                            },
                        },
                        "required": [
                            "symbol",
                            "side",
                            "entry",
                            "take_profit",
                            "stop_loss",
                        ],
                    },
                ),
            ],
        )

    def get_ticker(self, symbol: str, timeframe="1h"):
        print(f"📈 Fetching ticker data for {symbol} at {timeframe} timeframe")
        ohlcv = binance.fetch_ohlcv(symbol, timeframe, limit=100)

        print(f"📈 Fetched OHLCV data for {symbol} at {timeframe} timeframe: {ohlcv}")
        return {"result": ohlcv}

    def smc_analysis(self, symbol: str, timeframe="1h", limit=100):
        candles = binance.fetch_ohlcv(symbol, timeframe, limit=limit)
        self.current_price = candles[-1][4]

        bollinger_bands = self._bollinger_bands(candles)
        ema_7 = self._ema(candles, 7)
        ema_20 = self._ema(candles, 20)

        rsi_6 = self._rsi(candles, 6)
        rsi_12 = self._rsi(candles, 12)
        rsi_24 = self._rsi(candles, 24)

        market_structure = self._calculate_market_structure(candles)
        liquidity_pools = self._liquidity_pools(candles)
        order_blocks = self._order_blocks(candles)
        fair_value_gaps = self._fair_value_gaps(candles)

        data = {
            # "bollinger_bands": bollinger_bands,
            # "rsi_6": rsi_6,
            # "rsi_12": rsi_12,
            # "rsi_24": rsi_24,
            # "ema_7": ema_7,
            # "ema_20": ema_20,
            "current_price": self.current_price,
            "market_structure": market_structure,
            "liquidity_pools": liquidity_pools,
            "order_blocks": order_blocks,
            "fair_value_gaps": fair_value_gaps,
        }

        return {"result": data}

    def _format_array(self, name, arr, max_items=3, emoji="📌"):
        """Format array/dict list into a more visual Telegram-friendly message"""
        if not arr:
            return f"{emoji} {name}: None"

        formatted = []
        for item in arr[:max_items]:
            if isinstance(item, dict):
                lines = []
                for k, v in item.items():
                    # Convert numpy floats
                    if isinstance(v, (np.floating, float)):
                        v = round(float(v), 2)
                    # Convert timestamp if looks like ms epoch
                    if "time" in k and isinstance(v, (int, float)) and v > 1e12:
                        v = datetime.utcfromtimestamp(v / 1000).strftime(
                            "%Y-%m-%d %H:%M UTC"
                        )
                    lines.append(f"      • {k}: {v}")
                block = "\n".join(lines)
                formatted.append(f"   🔹 {block}")
            else:
                if isinstance(item, (np.floating, float)):
                    item = round(float(item), 2)
                formatted.append(f"   🔹 {item}")

        if len(arr) > max_items:
            formatted.append(f"   ... (+{len(arr) - max_items} more)")

        return f"{emoji} {name}:\n" + "\n".join(formatted)

    def _ema(self, candles, period=20):
        df = pd.DataFrame(
            candles,
            columns=["timestamp", "open", "high", "low", "close", "volume"],
        )

        ema_series = df["close"].ewm(span=period, adjust=False).mean()

        return ema_series.tolist()

    def create_order(
        self,
        symbol: str,
        side: str,
        entry: float,
        take_profit: float,
        stop_loss: float,
    ):
        try:
            response = binance_connector.create_orders(
                symbol=symbol,
                side=side,
                order_price=entry,
                current_price=self.current_price,
                take_profit=take_profit,
                stop_loss=stop_loss,
            )

            return {"result": response}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _fair_value_gaps(self, candles):
        df = pd.DataFrame(
            candles, columns=["timestamp", "open", "high", "low", "close", "volume"]
        )

        gaps = []

        # Loop through candle triples
        for i in range(2, len(df)):
            c1 = df.iloc[i - 2]
            c2 = df.iloc[i - 1]
            c3 = df.iloc[i]

            # Bullish FVG: low of c3 > high of c1
            if c3["low"] > c1["high"]:
                gaps.append(
                    {
                        "type": "bullish",
                        "start_index": i - 2,
                        "end_index": i,
                        "gap_high": c3["low"],  # top of the gap
                        "gap_low": c1["high"],  # bottom of the gap
                        "timestamp": int(c2["timestamp"]),
                    }
                )

            # Bearish FVG: high of c3 < low of c1
            elif c3["high"] < c1["low"]:
                gaps.append(
                    {
                        "type": "bearish",
                        "start_index": i - 2,
                        "end_index": i,
                        "gap_high": c1["low"],  # top of the gap
                        "gap_low": c3["high"],  # bottom of the gap
                        "timestamp": int(c2["timestamp"]),
                    }
                )

        return gaps

    def _calculate_atr(self, candles):
        df = pd.DataFrame(
            candles, columns=["timestamp", "open", "high", "low", "close", "volume"]
        )
        tr_values = []
        for i in range(len(df) - 1):
            high = df["high"].iloc[i]
            low = df["low"].iloc[i]
            prev_close = df["close"].iloc[i + 1]
            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
            tr_values.append(tr)
        return sum(tr_values) / len(tr_values) if tr_values else 0

    def _calculate_market_structure(self, candles):
        df = pd.DataFrame(
            candles,
            columns=["timestamp", "open", "high", "low", "close", "volume"],
        )
        swing_highs = []
        swing_lows = []

        for i in range(1, len(df) - 1):
            if (
                df["high"].iloc[i] > df["high"].iloc[i - 1]
                and df["high"].iloc[i] > df["high"].iloc[i + 1]
            ):
                swing_highs.append({"price": df["high"].iloc[i], "index": i})
            if (
                df["low"].iloc[i] < df["low"].iloc[i - 1]
                and df["low"].iloc[i] < df["low"].iloc[i + 1]
            ):
                swing_lows.append({"price": df["low"].iloc[i], "index": i})

        structure = "UNDEFINED"
        if len(swing_highs) >= 2 and len(swing_lows) >= 2:
            recent_highs = swing_highs[:2]
            recent_lows = swing_lows[:2]
            higher_highs = recent_highs[0]["price"] > recent_highs[1]["price"]
            higher_lows = recent_lows[0]["price"] > recent_lows[1]["price"]
            if higher_highs and higher_lows:
                structure = "BULLISH_TREND"
            elif not higher_highs and not higher_lows:
                structure = "BEARISH_TREND"
            elif higher_highs and not higher_lows:
                structure = "BULLISH_BREAKOUT"
            elif not higher_highs and higher_lows:
                structure = "BEARISH_BREAKOUT"
            else:
                structure = "CONSOLIDATION"

        return {
            "structure": structure,
            "swing_highs": swing_highs,
            "swing_lows": swing_lows,
        }

    def _bollinger_bands(self, candles, period=20, multiplier=2):
        data_frame = pd.DataFrame(
            candles[-period:],
            columns=["timestamp", "open", "high", "low", "close", "volume"],
        )

        data_frame["sma"] = data_frame["close"].rolling(window=period).mean()
        data_frame["std"] = data_frame["close"].rolling(window=period).std()

        data_frame["upper_band"] = data_frame["sma"] + (multiplier * data_frame["std"])
        data_frame["lower_band"] = data_frame["sma"] - (multiplier * data_frame["std"])

        return {
            "upper_band": data_frame["upper_band"].iloc[-1],
            "lower_band": data_frame["lower_band"].iloc[-1],
            "sma": data_frame["sma"].iloc[-1],
        }

    def _rsi(self, candles, period=14):
        data_frame = pd.DataFrame(
            candles[-period:],
            columns=["timestamp", "open", "high", "low", "close", "volume"],
        )

        delta = data_frame["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        return rsi.iloc[-1]

    def _liquidity_pools(self, candles):
        df = pd.DataFrame(
            candles,
            columns=["timestamp", "open", "high", "low", "close", "volume"],
        )
        avg_volume = df["volume"].mean()
        high_volume_threshold = avg_volume * 1.5
        pools = []

        for i in range(1, len(df) - 1):
            if df["volume"].iloc[i] > high_volume_threshold:
                if (
                    df["low"].iloc[i] < df["low"].iloc[i - 1]
                    and df["low"].iloc[i] < df["low"].iloc[i + 1]
                ):
                    pools.append(
                        {
                            "type": "DEMAND",
                            "price": df["low"].iloc[i],
                            "volume": df["volume"].iloc[i],
                            "strength": df["volume"].iloc[i] / avg_volume,
                        }
                    )
                elif (
                    df["high"].iloc[i] > df["high"].iloc[i - 1]
                    and df["high"].iloc[i] > df["high"].iloc[i + 1]
                ):
                    pools.append(
                        {
                            "type": "SUPPLY",
                            "price": df["high"].iloc[i],
                            "volume": df["volume"].iloc[i],
                            "strength": df["volume"].iloc[i] / avg_volume,
                        }
                    )

        return sorted(pools, key=lambda x: x["strength"], reverse=True)[:3]

    def _order_blocks(self, candles):
        df = pd.DataFrame(
            candles, columns=["timestamp", "open", "high", "low", "close", "volume"]
        )
        avg_volume = df["volume"].mean()
        order_blocks = []

        for i in range(1, len(df) - 1):
            current_candle = df.iloc[i]
            next_candle = df.iloc[i - 1]
            if current_candle["volume"] > avg_volume * 1.5:
                price_change = (
                    (next_candle["close"] - current_candle["close"])
                    / current_candle["close"]
                ) * 100
                if (
                    price_change > 1.0
                    and current_candle["close"] > current_candle["open"]
                ):
                    order_blocks.append(
                        {
                            "type": "BULLISH",
                            "price": current_candle["close"],
                            "volume": current_candle["volume"],
                            "strength": abs(price_change),
                        }
                    )
                elif (
                    price_change < -1.0
                    and current_candle["close"] < current_candle["open"]
                ):
                    order_blocks.append(
                        {
                            "type": "BEARISH",
                            "price": current_candle["close"],
                            "volume": current_candle["volume"],
                            "strength": abs(price_change),
                        }
                    )

        return sorted(order_blocks, key=lambda x: x["strength"], reverse=True)[:3]
