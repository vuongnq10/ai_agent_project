import ccxt
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime
from google.genai.types import Tool, FunctionDeclaration

from broker_bot.telegram.telegram import telegram_bot

from broker_bot.binance_connector.binance import BinanceConnector

binance = ccxt.binanceusdm({})
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

    def smc_analysis(self, symbol: str, timeframe="1h", limit=100):
        candles = binance.fetch_ohlcv(symbol, timeframe, limit=limit)
        self.current_price = candles[-1][4]

        # {"open": [], "high": [], "low": [], "close": []}
        data = self._convert_to_dict(candles)
        atr = self._calculate_atr(data)
        swing_points = self._find_swing_points(data, atr, lookback=5)
        fvg = self._find_fair_value_gaps(data)
        extremes = self._find_extremes(swing_points)

        indicators = {
            # "candles": candles,
            "symbol": symbol,
            "timeframe": timeframe,
            "atr": atr,
            **swing_points,
            **extremes,
            "fair_value_gaps": fvg,
        }
        return indicators

    def _find_extremes(self, swing_points):
        result = {}

        # Highest swing high
        if swing_points["swing_highs"]:
            highest_high = max(swing_points["swing_highs"], key=lambda x: x["price"])
            result["highest_swing_high"] = {
                "price": highest_high["price"],
                "at": highest_high["timestamp"],
            }

        # Lowest swing low
        if swing_points["swing_lows"]:
            lowest_low = min(swing_points["swing_lows"], key=lambda x: x["price"])
            result["lowest_swing_low"] = {
                "price": lowest_low["price"],
                "at": lowest_low["timestamp"],
            }

        return result

    def _convert_to_dict(self, data):
        result = {"timestamp": [], "open": [], "high": [], "low": [], "close": []}

        for row in data:
            # row = [time, open, high, low, close, volume]
            result["timestamp"].append(row[0])
            result["open"].append(row[1])
            result["high"].append(row[2])
            result["low"].append(row[3])
            result["close"].append(row[4])

        return result

    def _calculate_atr(self, data, period=5):
        high = data["high"]
        low = data["low"]
        close = data["close"]

        tr = []
        for i in range(1, len(high)):
            hl = high[i] - low[i]
            hc = abs(high[i] - close[i - 1])
            lc = abs(low[i] - close[i - 1])
            tr.append(max(hl, hc, lc))

        # Initial ATR = simple average of first `period` TR values
        atr = sum(tr[:period]) / period

        # Wilder’s smoothing
        for i in range(period, len(tr)):
            atr = (atr * (period - 1) + tr[i]) / period

        return atr

    def _find_swing_points(self, data, atr, lookback=5):
        high = data["high"]
        low = data["low"]
        timestamp = data["timestamp"]

        swing_highs = []
        swing_lows = []
        order_blocks = []

        for i in range(1, len(high)):
            is_high = True
            is_low = True

            # Check if current point is a swing high
            for j in range(1, lookback + 1):
                # Ensure index does not go out of range
                if i - j < 0 or i + j >= len(high):
                    is_high = False
                    break
                if high[i] <= high[i - j] or high[i] <= high[i + j]:
                    is_high = False
                    break

            # Check if current point is a swing low
            for j in range(1, lookback + 1):
                if i - j < 0 or i + j >= len(low):
                    is_low = False
                    break
                if low[i] >= low[i - j] or low[i] >= low[i + j]:
                    is_low = False
                    break

            if is_high:
                swing_highs.append({"timestamp": timestamp[i], "price": high[i]})
                order_blocks.append(
                    {
                        "high": high[i],
                        "low": low[i],
                        "timestamp": timestamp[i],
                        "type": "bearish",
                    }
                )

            if is_low:
                swing_lows.append({"timestamp": timestamp[i], "price": low[i]})
                order_blocks.append(
                    {
                        "high": high[i],
                        "low": low[i],
                        "timestamp": timestamp[i],
                        "type": "bullish",
                    }
                )

        # Filter order blocks
        filtered_order_blocks = [
            ob for ob in order_blocks if ob["high"] - ob["low"] <= atr * 2
        ]

        return {
            "swing_highs": swing_highs,
            "swing_lows": swing_lows,
            "order_blocks": filtered_order_blocks,
        }

    def _find_fair_value_gaps(self, data):
        timestamps = data["timestamp"]
        highs = data["high"]
        lows = data["low"]

        bullish_fvg = []
        bearish_fvg = []

        for i in range(len(highs) - 2):
            high1 = highs[i]
            low3 = lows[i + 2]
            high3 = highs[i + 2]
            low1 = lows[i]

            # Bullish FVG: gap between candle 1 high and candle 3 low
            if low3 > high1:
                bullish_fvg.append(
                    {
                        "top": high1,
                        "bottom": low3,
                        "timestamps": timestamps[i],
                        "type": "bullish",
                    }
                )

            # Bearish FVG: gap between candle 1 low and candle 3 high
            if low1 > high3:
                bearish_fvg.append(
                    {
                        "top": low1,
                        "bottom": high3,
                        "timestamps": timestamps[i],
                        "type": "bearish",
                    }
                )

        return {"bullish": bullish_fvg, "bearish": bearish_fvg}

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

    def get_ticker(self, symbol: str, timeframe="1h"):
        print(f"📈 Fetching ticker data for {symbol} at {timeframe} timeframe")
        ohlcv = binance.fetch_ohlcv(symbol, timeframe, limit=100)

        print(f"📈 Fetched OHLCV data for {symbol} at {timeframe} timeframe: {ohlcv}")
        return {"result": ohlcv}
