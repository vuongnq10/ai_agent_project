import ccxt
import pandas as pd
import numpy as np
from google.genai.types import Tool, FunctionDeclaration

from src.binance_connector.binance import BinanceConnector

binance = ccxt.binanceusdm({})
binance_connector = BinanceConnector()


class CXConnector:
    def __init__(self):
        self.current_price = None
        self.tools = Tool(
            function_declarations=[
                #                FunctionDeclaration(
                #                    name="smc_analysis",
                #                    description="Perform Smart Money Concept analysis on live candle chart by given symbol and timeframe.",
                #                    parameters={
                #                        "type": "object",
                #                        "properties": {
                #                            "symbol": {
                #                                "type": "string",
                #                                "description": "The trading pair symbol (e.g., 'SOLUSDT').",
                #                            },
                #                            "timeframe": {
                #                                "type": "string",
                #                                "description": "The timeframe for the analysis (e.g., 1h, 2h, 4h ).",
                #                                "default": "1h",
                #                            },
                #                            "limit": {
                #                                "type": "integer",
                #                                "description": "Number of candles to fetch for analysis.",
                #                                "default": 100,
                #                            },
                #                        },
                #                        "required": ["symbol", "timeframe"],
                #                    },
                #                ),
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
                            "current_price": {
                                "type": "number",
                                "description": "Current market price for the symbol.",
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

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    #    def smc_analysis(self, symbol: str, timeframe="1h", limit=100):
    #        """Run full Smart Money Concepts analysis on OHLCV data.
    #
    #        Pipeline:
    #        1. Fetch OHLCV -> pandas DataFrame
    #        2. ATR (Wilder smoothing, 14-period)
    #        3. Swing Highs/Lows (fractal detection with configurable lookback)
    #        4. Order Blocks (last opposing candle before impulsive move, with mitigation)
    #        5. Fair Value Gaps (3-candle imbalance, with mitigation tracking)
    #        6. BOS & CHoCH (unified: BOS = trend continuation, CHoCH = reversal)
    #        7. Liquidity (equal highs/lows clustering + sweep detection)
    #        8. Premium / Discount zones (from most recent swing range)
    #        9. Bollinger Bands, EMA, RSI (standard indicators)
    #        """
    #        candles = binance.fetch_ohlcv(symbol, timeframe, limit=limit)
    #
    #        # Build DataFrame -- the single source of truth for all calculations
    #        df = pd.DataFrame(
    #            candles,
    #            columns=["timestamp", "open", "high", "low", "close", "volume"],
    #        )
    #
    #        if len(df) < 20:
    #            return {"error": "Not enough candle data (need at least 20)"}
    #
    #        self.current_price = float(df["close"].iloc[-1])
    #
    #        # --- Core SMC pipeline (all operate on the DataFrame) ---
    #        atr_value = self._calculate_atr(df, period=14)
    #        swing_df = self._find_swing_points(df, swing_length=5)
    #        order_blocks = self._find_order_blocks(df, swing_df, atr_value)
    #        fvg = self._find_fair_value_gaps(df)
    #        bos_choch = self._find_bos_choch(df, swing_df)
    #        liquidity = self._find_liquidity_levels(df, swing_df, atr_value)
    #        extremes = self._find_extremes(swing_df)
    #        premium_discount = self._premium_discount_zones(df, swing_df)
    #
    #        # --- Standard indicators ---
    #        bb_14 = self._bollinger_bands(df, period=14, multiplier=2)
    #        bb_20 = self._bollinger_bands(df, period=20, multiplier=2)
    #        bb_50 = self._bollinger_bands(df, period=50, multiplier=2.5)
    #        ema_9 = self._ema(df, 9)
    #        ema_20 = self._ema(df, 20)
    #        ema_50 = self._ema(df, 50)
    #        rsi_7 = self._rsi(df, 7)
    #        rsi_14 = self._rsi(df, 14)
    #        rsi_21 = self._rsi(df, 21)
    #
    #        # --- Format swing points for output ---
    #        swing_highs = self._swing_points_to_list(df, swing_df, kind="high")
    #        swing_lows = self._swing_points_to_list(df, swing_df, kind="low")
    #
    #        # Trim FVGs to recent to avoid flooding LLM context
    #        recent_fvg = {
    #            "bullish": fvg["bullish"][-5:],
    #            "bearish": fvg["bearish"][-5:],
    #        }
    #
    #        indicators = {
    #            "current_price": self.current_price,
    #            "symbol": symbol,
    #            "timeframe": timeframe,
    #            "atr": round(atr_value, 8),
    #            "swing_highs": swing_highs[-10:],
    #            "swing_lows": swing_lows[-10:],
    #            **extremes,
    #            "order_blocks": order_blocks[-10:],
    #            "fair_value_gaps": recent_fvg,
    #            "break_of_structure": bos_choch["bos"][-8:],
    #            "changes_of_character": bos_choch["choch"][-5:],
    #            "market_structure": bos_choch["current_structure"],
    #            "liquidity": liquidity,
    #            "premium_discount": premium_discount,
    #            "bollinger_bands": {
    #                "14": bb_14,
    #                "20": bb_20,
    #                "50": bb_50,
    #            },
    #            "ema": {"9": ema_9, "20": ema_20, "50": ema_50},
    #            "rsi": {"7": rsi_7, "14": rsi_14, "21": rsi_21},
    #        }
    #        return indicators

    # -----------------------------------------------------------------------
    # ATR  (Wilder smoothing)
    # -----------------------------------------------------------------------

    #    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
    #        """Average True Range using Wilder's smoothing method.
    #
    #        ATR measures volatility and is used throughout SMC for:
    #        - Order block width filtering
    #        - Liquidity tolerance bands
    #        - Impulsive move thresholds
    #
    #        Wilder's smoothing: ATR_t = (ATR_{t-1} * (period-1) + TR_t) / period
    #        """
    #        high = df["high"].values
    #        low = df["low"].values
    #        close = df["close"].values
    #
    #        # True Range: max(H-L, |H-prevC|, |L-prevC|)
    #        tr = np.empty(len(df))
    #        tr[0] = high[0] - low[0]
    #        tr[1:] = np.maximum(
    #            high[1:] - low[1:],
    #            np.maximum(
    #                np.abs(high[1:] - close[:-1]),
    #                np.abs(low[1:] - close[:-1]),
    #            ),
    #        )
    #
    #        # Wilder's smoothing
    #        atr = np.mean(tr[:period])
    #        for i in range(period, len(tr)):
    #            atr = (atr * (period - 1) + tr[i]) / period
    #
    #        return float(atr)

    # -----------------------------------------------------------------------
    # Swing Highs / Lows  (fractal detection)
    # -----------------------------------------------------------------------

    #    def _find_swing_points(self, df: pd.DataFrame, swing_length: int = 5) -> pd.DataFrame:
    #        """Identify swing highs and lows using a fractal lookback/lookahead window.
    #
    #        A swing high at index i means:
    #            high[i] is the HIGHEST high in the window [i - swing_length, i + swing_length]
    #
    #        A swing low at index i means:
    #            low[i] is the LOWEST low in the window [i - swing_length, i + swing_length]
    #
    #        When consecutive swings of the same type occur, only the most extreme
    #        is kept (highest for highs, lowest for lows).  This follows the ICT
    #        convention of identifying only *significant* swing points.
    #
    #        Returns a DataFrame aligned to df's index with columns:
    #            'swing_type':  1.0 = swing high, -1.0 = swing low, NaN = neither
    #            'swing_price': the price level at the swing point
    #        """
    #        n = len(df)
    #        high = df["high"].values
    #        low = df["low"].values
    #
    #        swing_type = np.full(n, np.nan)
    #        swing_price = np.full(n, np.nan)
    #
    #        for i in range(swing_length, n - swing_length):
    #            window_start = i - swing_length
    #            window_end = i + swing_length + 1  # exclusive
    #
    #            # Swing high: current high is strictly the max in the window
    #            if high[i] == np.max(high[window_start:window_end]):
    #                swing_type[i] = 1.0
    #                swing_price[i] = high[i]
    #
    #            # Swing low: current low is strictly the min in the window
    #            if low[i] == np.min(low[window_start:window_end]):
    #                # If already marked as swing high, keep the one that matters more
    #                # (rare case where a doji is both). Prefer the swing high; mark low
    #                # only if not already a high.
    #                if swing_type[i] == 1.0:
    #                    pass  # keep as swing high
    #                else:
    #                    swing_type[i] = -1.0
    #                    swing_price[i] = low[i]
    #
    #        # --- Deduplicate consecutive same-type swings ---
    #        # If two consecutive swing highs, keep the higher one.
    #        # If two consecutive swing lows, keep the lower one.
    #        swing_indices = np.where(~np.isnan(swing_type))[0]
    #        if len(swing_indices) > 1:
    #            to_remove = []
    #            i = 0
    #            while i < len(swing_indices) - 1:
    #                idx_a = swing_indices[i]
    #                idx_b = swing_indices[i + 1]
    #                if swing_type[idx_a] == swing_type[idx_b]:
    #                    # Same type -- keep the more extreme
    #                    if swing_type[idx_a] == 1.0:
    #                        # Two highs: remove the lower one
    #                        remove = idx_a if swing_price[idx_a] <= swing_price[idx_b] else idx_b
    #                    else:
    #                        # Two lows: remove the higher one
    #                        remove = idx_a if swing_price[idx_a] >= swing_price[idx_b] else idx_b
    #                    to_remove.append(remove)
    #                    i += 1
    #                else:
    #                    i += 1
    #
    #            for idx in to_remove:
    #                swing_type[idx] = np.nan
    #                swing_price[idx] = np.nan
    #
    #        result = pd.DataFrame(
    #            {"swing_type": swing_type, "swing_price": swing_price},
    #            index=df.index,
    #        )
    #        return result

    #    def _swing_points_to_list(self, df: pd.DataFrame, swing_df: pd.DataFrame, kind: str) -> list:
    #        """Convert swing DataFrame to list-of-dicts for JSON output."""
    #        target = 1.0 if kind == "high" else -1.0
    #        mask = swing_df["swing_type"] == target
    #        indices = swing_df.index[mask]
    #        result = []
    #        for idx in indices:
    #            result.append({
    #                "timestamp": int(df.at[idx, "timestamp"]),
    #                "price": float(swing_df.at[idx, "swing_price"]),
    #            })
    #        return result

    # -----------------------------------------------------------------------
    # Order Blocks  (ICT methodology)
    # -----------------------------------------------------------------------

    #    def _find_order_blocks(
    #        self,
    #        df: pd.DataFrame,
    #        swing_df: pd.DataFrame,
    #        atr: float,
    #        max_lookback: int = 10,
    #    ) -> list:
    #        """Detect order blocks per ICT methodology.
    #
    #        Bullish Order Block:
    #            The last BEARISH candle (close < open) before a significant bullish
    #            move that takes out a swing low.  The OB zone spans [low, high] of
    #            that candle.  Institutional logic: smart money placed buy orders
    #            here, absorbed sell-side liquidity, then drove price up.
    #
    #        Bearish Order Block:
    #            The last BULLISH candle (close > open) before a significant bearish
    #            move that takes out a swing high.  Institutional logic: smart money
    #            placed sell orders here, absorbed buy-side liquidity, then drove
    #            price down.
    #
    #        Validation rules:
    #            1. The move after the OB candle must be impulsive (body > 0.5 * ATR)
    #            2. The OB candle body must not be abnormally wide (< 2 * ATR)
    #            3. Mitigation: an OB is mitigated when price later returns into the
    #               zone (close enters the OB range).  Mitigated OBs are marked but
    #               still returned for context.
    #
    #        Sources:
    #            - ICT Core Content: "The order block is the last opposing candle
    #              before the impulsive move."
    #            - FluxCharts: OB drawn from the last bearish/bullish candle before
    #              the impulsive move, zone from candle low to candle high.
    #            - joshyattridge/smart-money-concepts: OB detection tied to swing
    #              level crosses with volume metrics.
    #        """
    #        open_ = df["open"].values
    #        close = df["close"].values
    #        high = df["high"].values
    #        low = df["low"].values
    #        timestamps = df["timestamp"].values
    #        n = len(df)
    #
    #        swing_type = swing_df["swing_type"].values
    #        swing_price = swing_df["swing_price"].values
    #
    #        order_blocks = []
    #
    #        # Find indices of swing highs and swing lows
    #        sh_indices = np.where(swing_type == 1.0)[0]
    #        sl_indices = np.where(swing_type == -1.0)[0]
    #
    #        # --- Bullish OBs: last bearish candle before move up from swing low ---
    #        for sl_idx in sl_indices:
    #            # The swing low is at sl_idx. Look backward for the last bearish candle.
    #            ob_idx = None
    #            for k in range(sl_idx, max(sl_idx - max_lookback, -1), -1):
    #                if close[k] < open_[k]:  # bearish candle
    #                    ob_idx = k
    #                    break
    #
    #            if ob_idx is None:
    #                continue
    #
    #            # Validate impulsive move: check candles after the OB for a strong bullish move
    #            move_end = min(ob_idx + max_lookback, n)
    #            max_close_after = np.max(close[ob_idx + 1:move_end]) if ob_idx + 1 < move_end else close[ob_idx]
    #            move_size = max_close_after - low[ob_idx]
    #
    #            if move_size < atr * 0.5:
    #                continue  # not impulsive enough
    #
    #            ob_width = high[ob_idx] - low[ob_idx]
    #            if ob_width > atr * 2:
    #                continue  # abnormally wide candle
    #
    #            # Check mitigation: did price close back into the OB zone after it formed?
    #            mitigated = False
    #            mitigated_at = None
    #            for m in range(sl_idx + 1, n):
    #                if close[m] <= high[ob_idx] and close[m] >= low[ob_idx]:
    #                    mitigated = True
    #                    mitigated_at = int(timestamps[m])
    #                    break
    #
    #            order_blocks.append({
    #                "type": "bullish",
    #                "ob_high": float(high[ob_idx]),
    #                "ob_low": float(low[ob_idx]),
    #                "timestamp": int(timestamps[ob_idx]),
    #                "mitigated": mitigated,
    #                "mitigated_at": mitigated_at,
    #            })
    #
    #        # --- Bearish OBs: last bullish candle before move down from swing high ---
    #        for sh_idx in sh_indices:
    #            ob_idx = None
    #            for k in range(sh_idx, max(sh_idx - max_lookback, -1), -1):
    #                if close[k] > open_[k]:  # bullish candle
    #                    ob_idx = k
    #                    break
    #
    #            if ob_idx is None:
    #                continue
    #
    #            move_end = min(ob_idx + max_lookback, n)
    #            min_close_after = np.min(close[ob_idx + 1:move_end]) if ob_idx + 1 < move_end else close[ob_idx]
    #            move_size = high[ob_idx] - min_close_after
    #
    #            if move_size < atr * 0.5:
    #                continue
    #
    #            ob_width = high[ob_idx] - low[ob_idx]
    #            if ob_width > atr * 2:
    #                continue
    #
    #            mitigated = False
    #            mitigated_at = None
    #            for m in range(sh_idx + 1, n):
    #                if close[m] >= low[ob_idx] and close[m] <= high[ob_idx]:
    #                    mitigated = True
    #                    mitigated_at = int(timestamps[m])
    #                    break
    #
    #            order_blocks.append({
    #                "type": "bearish",
    #                "ob_high": float(high[ob_idx]),
    #                "ob_low": float(low[ob_idx]),
    #                "timestamp": int(timestamps[ob_idx]),
    #                "mitigated": mitigated,
    #                "mitigated_at": mitigated_at,
    #            })
    #
    #        # Sort by timestamp
    #        order_blocks.sort(key=lambda x: x["timestamp"])
    #        return order_blocks

    # -----------------------------------------------------------------------
    # Fair Value Gaps  (3-candle imbalance)
    # -----------------------------------------------------------------------

    #    def _find_fair_value_gaps(self, df: pd.DataFrame) -> dict:
    #        """Detect Fair Value Gaps (FVG) -- price imbalances per ICT methodology.
    #
    #        A FVG is a 3-candle pattern where the middle candle's move is so
    #        impulsive that a gap is left between candle 1 and candle 3.
    #
    #        Bullish FVG (gap up):
    #            candle_3.low > candle_1.high
    #            Gap zone: [candle_1.high, candle_3.low]
    #            Indicates institutional buying -- price moved up so fast it left
    #            an unfilled zone.  Price tends to return here for "rebalancing."
    #
    #        Bearish FVG (gap down):
    #            candle_1.low > candle_3.high
    #            Gap zone: [candle_3.high, candle_1.low]
    #            Indicates institutional selling.
    #
    #        Mitigation:
    #            A FVG is considered mitigated (filled) when a subsequent candle's
    #            close enters the gap zone.  Partially mitigated gaps are tracked
    #            by how much of the zone was filled.
    #
    #        Sources:
    #            - ICT: "Imbalance = the gap between candle 1 high and candle 3 low"
    #            - smartmoneyconcepts PyPI: FVG with join_consecutive and mitigation
    #        """
    #        high = df["high"].values
    #        low = df["low"].values
    #        close = df["close"].values
    #        timestamps = df["timestamp"].values
    #        n = len(df)
    #
    #        bullish_fvg = []
    #        bearish_fvg = []
    #
    #        for i in range(n - 2):
    #            high1 = high[i]
    #            low1 = low[i]
    #            low3 = low[i + 2]
    #            high3 = high[i + 2]
    #
    #            # --- Bullish FVG: candle 3 low > candle 1 high ---
    #            if low3 > high1:
    #                gap_top = float(low3)
    #                gap_bottom = float(high1)
    #                gap_size = gap_top - gap_bottom
    #
    #                # Check mitigation: did any subsequent candle close into the gap?
    #                mitigated = False
    #                mitigated_at = None
    #                fill_percent = 0.0
    #
    #                for m in range(i + 3, n):
    #                    if close[m] <= gap_top:
    #                        # Price entered the gap from above
    #                        filled_depth = gap_top - max(close[m], gap_bottom)
    #                        fill_percent = max(fill_percent, filled_depth / gap_size if gap_size > 0 else 0)
    #                        if close[m] <= gap_bottom:
    #                            mitigated = True
    #                            mitigated_at = int(timestamps[m])
    #                            fill_percent = 1.0
    #                            break
    #
    #                bullish_fvg.append({
    #                    "top": gap_top,
    #                    "bottom": gap_bottom,
    #                    "timestamp": int(timestamps[i + 1]),  # middle candle timestamp
    #                    "type": "bullish",
    #                    "mitigated": mitigated,
    #                    "mitigated_at": mitigated_at,
    #                    "fill_percent": round(fill_percent, 2),
    #                })
    #
    #            # --- Bearish FVG: candle 1 low > candle 3 high ---
    #            if low1 > high3:
    #                gap_top = float(low1)
    #                gap_bottom = float(high3)
    #                gap_size = gap_top - gap_bottom
    #
    #                mitigated = False
    #                mitigated_at = None
    #                fill_percent = 0.0
    #
    #                for m in range(i + 3, n):
    #                    if close[m] >= gap_bottom:
    #                        filled_depth = min(close[m], gap_top) - gap_bottom
    #                        fill_percent = max(fill_percent, filled_depth / gap_size if gap_size > 0 else 0)
    #                        if close[m] >= gap_top:
    #                            mitigated = True
    #                            mitigated_at = int(timestamps[m])
    #                            fill_percent = 1.0
    #                            break
    #
    #                bearish_fvg.append({
    #                    "top": gap_top,
    #                    "bottom": gap_bottom,
    #                    "timestamp": int(timestamps[i + 1]),
    #                    "type": "bearish",
    #                    "mitigated": mitigated,
    #                    "mitigated_at": mitigated_at,
    #                    "fill_percent": round(fill_percent, 2),
    #                })
    #
    #        return {"bullish": bullish_fvg, "bearish": bearish_fvg}

    # -----------------------------------------------------------------------
    # BOS & CHoCH  (unified market structure tracking)
    # -----------------------------------------------------------------------

    #    def _find_bos_choch(self, df: pd.DataFrame, swing_df: pd.DataFrame) -> dict:
    #        """Unified Break of Structure and Change of Character detection.
    #
    #        Per ICT methodology, the distinction between BOS and CHoCH depends
    #        on whether the break is WITH or AGAINST the prevailing trend:
    #
    #        Break of Structure (BOS) -- trend CONTINUATION:
    #            - Bullish BOS: in an uptrend, price closes above the last swing high
    #            - Bearish BOS: in a downtrend, price closes below the last swing low
    #
    #        Change of Character (CHoCH) -- trend REVERSAL:
    #            - Bullish CHoCH: in a downtrend, price closes above the last swing high
    #              (first sign the downtrend may be reversing to bullish)
    #            - Bearish CHoCH: in an uptrend, price closes below the last swing low
    #              (first sign the uptrend may be reversing to bearish)
    #
    #        IMPORTANT: A valid break requires a candle CLOSE beyond the level,
    #        not just a wick.  This is the standard ICT rule.
    #
    #        The algorithm:
    #        1. Walk through candles in order
    #        2. Track the most recent confirmed swing high and swing low
    #        3. When close breaks a swing level, classify as BOS or CHoCH based
    #           on the current structure direction
    #        4. Update structure direction after each break
    #
    #        Sources:
    #            - TradingFinder BOS vs CHoCH: "BOS = continuation, CHoCH = reversal"
    #            - ICT Core Content: "CHoCH is the FIRST break of structure against
    #              the prevailing trend"
    #            - smartmoneyconcepts PyPI: bos_choch with close_break parameter
    #        """
    #        close = df["close"].values
    #        timestamps = df["timestamp"].values
    #        swing_type = swing_df["swing_type"].values
    #        swing_price = swing_df["swing_price"].values
    #        n = len(df)
    #
    #        bos_list = []
    #        choch_list = []
    #
    #        # Determine initial structure from the first two alternating swing points
    #        structure = None  # "bullish" or "bearish"
    #
    #        # Collect swing points in order
    #        swing_indices = np.where(~np.isnan(swing_type))[0]
    #
    #        # Need at least 4 swing points to establish structure
    #        if len(swing_indices) < 4:
    #            return {"bos": [], "choch": [], "current_structure": "unknown"}
    #
    #        # Determine initial structure from the first few swing points.
    #        # Walk swing points in chronological order, tracking the last two of
    #        # each type AS THEY ALTERNATE.  This enforces the HH+HL / LL+LH
    #        # pattern on actually adjacent swings rather than mixing non-adjacent
    #        # highs and lows from opposite ends of the dataset.
    #        prev_sh = None  # (index, price) of the second-to-last swing high seen
    #        last_sh = None  # (index, price) of the most recent swing high seen
    #        prev_sl = None
    #        last_sl = None
    #        for si in swing_indices:
    #            if swing_type[si] == 1.0:
    #                prev_sh = last_sh
    #                last_sh = (si, swing_price[si])
    #            else:
    #                prev_sl = last_sl
    #                last_sl = (si, swing_price[si])
    #            # Stop as soon as we have two of each type
    #            if prev_sh is not None and prev_sl is not None:
    #                break
    #
    #        if prev_sh is not None and prev_sl is not None:
    #            hh = last_sh[1] > prev_sh[1]   # higher high
    #            hl = last_sl[1] > prev_sl[1]   # higher low
    #            lh = last_sh[1] < prev_sh[1]   # lower high
    #            ll = last_sl[1] < prev_sl[1]   # lower low
    #            if hh and hl:
    #                structure = "bullish"
    #            elif lh and ll:
    #                structure = "bearish"
    #
    #        # Track the last confirmed swing high and swing low
    #        last_sh_price = None
    #        last_sl_price = None
    #        last_sh_ts = None
    #        last_sl_ts = None
    #
    #        # Build a set for quick lookup of swing candles
    #        swing_at = {}
    #        for si in swing_indices:
    #            swing_at[si] = (swing_type[si], swing_price[si])
    #
    #        for i in range(n):
    #            # If this candle is a swing point, update our tracking
    #            if i in swing_at:
    #                st, sp = swing_at[i]
    #                if st == 1.0:
    #                    last_sh_price = sp
    #                    last_sh_ts = int(timestamps[i])
    #                elif st == -1.0:
    #                    last_sl_price = sp
    #                    last_sl_ts = int(timestamps[i])
    #                continue  # Don't check breaks on the swing candle itself
    #
    #            # Check for breaks using candle CLOSE (ICT rule)
    #            # --- Bullish break: close above last swing high ---
    #            if last_sh_price is not None and close[i] > last_sh_price:
    #                broken_level = float(last_sh_price)
    #                ts = int(timestamps[i])
    #
    #                if structure == "bullish" or structure is None:
    #                    # Continuation -> BOS
    #                    bos_list.append({
    #                        "type": "BOS_bullish",
    #                        "timestamp": ts,
    #                        "price": float(close[i]),
    #                        "broken_level": broken_level,
    #                    })
    #                else:
    #                    # Was bearish, now breaking high -> CHoCH (reversal to bullish)
    #                    choch_list.append({
    #                        "type": "CHoCH_bullish",
    #                        "timestamp": ts,
    #                        "price": float(close[i]),
    #                        "broken_level": broken_level,
    #                    })
    #
    #                structure = "bullish"
    #                last_sh_price = None  # consumed
    #
    #            # --- Bearish break: close below last swing low ---
    #            # elif prevents the same candle from triggering both a bullish and
    #            # bearish break simultaneously (e.g. a wide engulfing candle that
    #            # closes above last_sh and below last_sl in extreme volatility).
    #            elif last_sl_price is not None and close[i] < last_sl_price:
    #                broken_level = float(last_sl_price)
    #                ts = int(timestamps[i])
    #
    #                if structure == "bearish" or structure is None:
    #                    bos_list.append({
    #                        "type": "BOS_bearish",
    #                        "timestamp": ts,
    #                        "price": float(close[i]),
    #                        "broken_level": broken_level,
    #                    })
    #                else:
    #                    choch_list.append({
    #                        "type": "CHoCH_bearish",
    #                        "timestamp": ts,
    #                        "price": float(close[i]),
    #                        "broken_level": broken_level,
    #                    })
    #
    #                structure = "bearish"
    #                last_sl_price = None  # consumed
    #
    #        return {
    #            "bos": bos_list,
    #            "choch": choch_list,
    #            "current_structure": structure or "unknown",
    #        }

    # -----------------------------------------------------------------------
    # Liquidity Levels  (equal highs/lows + sweep detection)
    # -----------------------------------------------------------------------

    #    def _find_liquidity_levels(
    #        self,
    #        df: pd.DataFrame,
    #        swing_df: pd.DataFrame,
    #        atr: float,
    #        range_percent: float = 0.01,
    #    ) -> dict:
    #        """Identify liquidity pools and detect sweeps per ICT methodology.
    #
    #        Buy-Side Liquidity (BSL):
    #            Clusters of swing highs at similar price levels (equal highs).
    #            Stop-loss orders from short sellers and breakout buy orders sit
    #            above these levels.  Institutions target BSL for short entries.
    #
    #        Sell-Side Liquidity (SSL):
    #            Clusters of swing lows at similar price levels (equal lows).
    #            Stop-loss orders from long traders sit below these levels.
    #            Institutions target SSL for long entries.
    #
    #        Equal Highs/Lows:
    #            Two or more swing points within `range_percent` of each other.
    #            The tighter the cluster, the more liquidity sits there.
    #
    #        Liquidity Sweep:
    #            Price briefly pierces a liquidity level (wick beyond it) but
    #            closes back inside.  This is the institutional "stop hunt."
    #            A bullish sweep takes SSL and closes above; a bearish sweep
    #            takes BSL and closes below.
    #
    #        Sources:
    #            - ICT: "Liquidity rests above equal highs and below equal lows"
    #            - AronGroups: BSL above swing highs, SSL below swing lows
    #            - smartmoneyconcepts PyPI: liquidity(range_percent=0.01) with sweep detection
    #        """
    #        swing_type = swing_df["swing_type"].values
    #        swing_price = swing_df["swing_price"].values
    #        high = df["high"].values
    #        low = df["low"].values
    #        close = df["close"].values
    #        timestamps = df["timestamp"].values
    #        n = len(df)
    #
    #        # Collect swing high and low prices with their indices
    #        sh_data = [(i, swing_price[i]) for i in range(n) if swing_type[i] == 1.0]
    #        sl_data = [(i, swing_price[i]) for i in range(n) if swing_type[i] == -1.0]
    #
    #        def _find_clusters(points, tolerance_pct):
    #            """Group swing points within tolerance_pct of each other."""
    #            if not points:
    #                return []
    #            # Sort by price
    #            sorted_pts = sorted(points, key=lambda x: x[1])
    #            clusters = []
    #            used = set()
    #
    #            for i in range(len(sorted_pts)):
    #                if i in used:
    #                    continue
    #                cluster = [sorted_pts[i]]
    #                used.add(i)
    #                for j in range(i + 1, len(sorted_pts)):
    #                    if j in used:
    #                        continue
    #                    price_diff = abs(sorted_pts[j][1] - sorted_pts[i][1])
    #                    ref_price = sorted_pts[i][1]
    #                    if ref_price > 0 and (price_diff / ref_price) <= tolerance_pct:
    #                        cluster.append(sorted_pts[j])
    #                        used.add(j)
    #                if len(cluster) >= 2:
    #                    clusters.append(cluster)
    #            return clusters
    #
    #        # --- Buy-Side Liquidity (equal highs) ---
    #        bsl_clusters = _find_clusters(sh_data, range_percent)
    #        buy_side = []
    #        for cluster in bsl_clusters:
    #            level = float(np.mean([p for _, p in cluster]))
    #            last_idx = max(idx for idx, _ in cluster)
    #            count = len(cluster)
    #
    #            # Check for sweep: did price wick above the level then close below?
    #            swept = False
    #            swept_at = None
    #            for m in range(last_idx + 1, n):
    #                if high[m] > level and close[m] < level:
    #                    swept = True
    #                    swept_at = int(timestamps[m])
    #                    break
    #
    #            buy_side.append({
    #                "price": round(level, 8),
    #                "count": count,
    #                "timestamps": [int(timestamps[idx]) for idx, _ in cluster],
    #                "swept": swept,
    #                "swept_at": swept_at,
    #            })
    #
    #        # --- Sell-Side Liquidity (equal lows) ---
    #        ssl_clusters = _find_clusters(sl_data, range_percent)
    #        sell_side = []
    #        for cluster in ssl_clusters:
    #            level = float(np.mean([p for _, p in cluster]))
    #            last_idx = max(idx for idx, _ in cluster)
    #            count = len(cluster)
    #
    #            # Check for sweep: did price wick below the level then close above?
    #            swept = False
    #            swept_at = None
    #            for m in range(last_idx + 1, n):
    #                if low[m] < level and close[m] > level:
    #                    swept = True
    #                    swept_at = int(timestamps[m])
    #                    break
    #
    #            sell_side.append({
    #                "price": round(level, 8),
    #                "count": count,
    #                "timestamps": [int(timestamps[idx]) for idx, _ in cluster],
    #                "swept": swept,
    #                "swept_at": swept_at,
    #            })
    #
    #        return {
    #            "buy_side_liquidity": buy_side,
    #            "sell_side_liquidity": sell_side,
    #        }

    # -----------------------------------------------------------------------
    # Premium / Discount Zones
    # -----------------------------------------------------------------------

    #    def _premium_discount_zones(self, df: pd.DataFrame, swing_df: pd.DataFrame) -> dict:
    #        """Calculate premium/discount zones from the most recent significant swing range.
    #
    #        Per ICT methodology:
    #        - Premium zone: above the 50% (equilibrium) of the swing range.
    #          Institutional sellers look to sell here.  Short entries are favored.
    #        - Discount zone: below the 50%.  Institutional buyers accumulate here.
    #          Long entries are favored.
    #        - Equilibrium (EQ): the exact 50% level.
    #
    #        The range is taken from the most recent swing high to the most recent
    #        swing low (whichever pair gives the widest current range), rather than
    #        the absolute extremes of the entire dataset.  This gives a more
    #        relevant, time-sensitive zone.
    #
    #        Fibonacci levels (0.236, 0.382, 0.5, 0.618, 0.786) are also computed
    #        as they are commonly used as institutional entry/exit targets within
    #        the premium/discount framework.
    #
    #        Sources:
    #            - ICT: "Trade from discount, target premium" (for longs)
    #            - ICT: Premium = above 50%, Discount = below 50%
    #        """
    #        swing_type = swing_df["swing_type"].values
    #        swing_price = swing_df["swing_price"].values
    #
    #        # Find the most recent swing high and swing low
    #        sh_indices = np.where(swing_type == 1.0)[0]
    #        sl_indices = np.where(swing_type == -1.0)[0]
    #
    #        if len(sh_indices) == 0 or len(sl_indices) == 0:
    #            return None
    #
    #        recent_sh_price = float(swing_price[sh_indices[-1]])
    #        recent_sl_price = float(swing_price[sl_indices[-1]])
    #
    #        range_high = max(recent_sh_price, recent_sl_price)
    #        range_low = min(recent_sh_price, recent_sl_price)
    #        swing_range = range_high - range_low
    #
    #        if swing_range <= 0:
    #            return None
    #
    #        equilibrium = range_low + swing_range * 0.5
    #        current_zone = "premium" if self.current_price > equilibrium else "discount"
    #
    #        # Distance from equilibrium as percentage of range (0 = at EQ, 1 = at extreme)
    #        eq_distance = abs(self.current_price - equilibrium) / (swing_range * 0.5)
    #
    #        # Standard Fibonacci retracement levels within the range
    #        fib_levels = {}
    #        for fib in [0.236, 0.382, 0.5, 0.618, 0.786]:
    #            fib_levels[str(fib)] = round(range_low + swing_range * fib, 8)
    #
    #        return {
    #            "range_high": range_high,
    #            "range_low": range_low,
    #            "equilibrium": round(equilibrium, 8),
    #            "premium_zone": {"from": round(equilibrium, 8), "to": range_high},
    #            "discount_zone": {"from": range_low, "to": round(equilibrium, 8)},
    #            "current_zone": current_zone,
    #            "eq_distance_pct": round(eq_distance * 100, 1),
    #            "fibonacci_levels": fib_levels,
    #        }

    # -----------------------------------------------------------------------
    # Extremes
    # -----------------------------------------------------------------------

    #    def _find_extremes(self, swing_df: pd.DataFrame) -> dict:
    #        """Find the highest swing high and lowest swing low in the dataset."""
    #        result = {}
    #        sh_mask = swing_df["swing_type"] == 1.0
    #        sl_mask = swing_df["swing_type"] == -1.0
    #
    #        if sh_mask.any():
    #            idx = swing_df.loc[sh_mask, "swing_price"].idxmax()
    #            result["highest_swing_high"] = {
    #                "price": float(swing_df.at[idx, "swing_price"]),
    #                "index": int(idx),
    #            }
    #
    #        if sl_mask.any():
    #            idx = swing_df.loc[sl_mask, "swing_price"].idxmin()
    #            result["lowest_swing_low"] = {
    #                "price": float(swing_df.at[idx, "swing_price"]),
    #                "index": int(idx),
    #            }
    #
    #        return result

    # -----------------------------------------------------------------------
    # Standard Indicators  (Bollinger Bands, EMA, RSI)
    # -----------------------------------------------------------------------

    #    def _bollinger_bands(self, df: pd.DataFrame, period: int = 20, multiplier: float = 2) -> dict:
    #        """Bollinger Bands with configurable period and multiplier."""
    #        if len(df) < period:
    #            return {"upper_band": None, "lower_band": None, "sma": None}
    #
    #        sma = df["close"].rolling(window=period).mean()
    #        std = df["close"].rolling(window=period).std(ddof=0)
    #
    #        return {
    #            "upper_band": round(float(sma.iloc[-1] + multiplier * std.iloc[-1]), 8),
    #            "lower_band": round(float(sma.iloc[-1] - multiplier * std.iloc[-1]), 8),
    #            "sma": round(float(sma.iloc[-1]), 8),
    #        }

    #    def _rsi(self, df: pd.DataFrame, period: int = 14) -> float:
    #        """RSI using Wilder's smoothing (EWM with alpha=1/period)."""
    #        if len(df) < period + 1:
    #            return None
    #
    #        delta = df["close"].diff()
    #        gain = delta.clip(lower=0)
    #        loss = (-delta).clip(lower=0)
    #
    #        avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    #        avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
    #
    #        rs = avg_gain / avg_loss
    #        rsi = 100 - (100 / (1 + rs))
    #
    #        return round(float(rsi.iloc[-1]), 2)

    #    def _ema(self, df: pd.DataFrame, period: int = 20) -> list:
    #        """Exponential Moving Average. Returns last 5 values for trend context."""
    #        if len(df) < period:
    #            return []
    #
    #        ema_series = df["close"].ewm(span=period, adjust=False).mean()
    #        # Return only the last 5 values to keep output concise
    #        return [round(float(v), 8) for v in ema_series.iloc[-5:].tolist()]

    # -----------------------------------------------------------------------
    # Order management (unchanged)
    # -----------------------------------------------------------------------

    def create_order(
        self,
        symbol: str,
        current_price: float,
        side: str,
        entry: float,
        take_profit: float,
        stop_loss: float,
    ):
        if current_price is None:
            return {"status": "error", "message": "current_price not set"}
        try:
            response = binance_connector.create_orders(
                symbol=symbol,
                side=side,
                order_price=entry,
                current_price=current_price,
                take_profit=take_profit,
                stop_loss=stop_loss,
            )

            return {"result": response}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_ticker(self, symbol: str, timeframe="1h"):
        ohlcv = binance.fetch_ohlcv(symbol, timeframe, limit=100)
        return {"result": ohlcv}
