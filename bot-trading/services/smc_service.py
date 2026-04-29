import httpx


class SmcService:
    BINANCE_FUTURES_URL = "https://fapi.binance.com/fapi/v1"

    def fetch_candles(self, symbol: str, timeframe: str, limit: int = 300) -> list[dict]:
        url = f"{self.BINANCE_FUTURES_URL}/klines"
        params = {"symbol": symbol, "interval": timeframe, "limit": limit}
        with httpx.Client(timeout=10) as client:
            resp = client.get(url, params=params)
            resp.raise_for_status()
        return [
            {
                "timestamp": int(k[0]),
                "open": float(k[1]),
                "high": float(k[2]),
                "low": float(k[3]),
                "close": float(k[4]),
                "volume": float(k[5]),
            }
            for k in resp.json()
        ]

    def _calc_atr(self, candles: list[dict], period: int = 14) -> float:
        if len(candles) < period + 1:
            return 0.0
        trs = []
        for i in range(1, len(candles)):
            hl = candles[i]["high"] - candles[i]["low"]
            hpc = abs(candles[i]["high"] - candles[i - 1]["close"])
            lpc = abs(candles[i]["low"] - candles[i - 1]["close"])
            trs.append(max(hl, hpc, lpc))
        atr = sum(trs[:period]) / period
        for i in range(period, len(trs)):
            atr = (atr * (period - 1) + trs[i]) / period
        return atr

    def _calc_ema(self, closes: list[float], period: int) -> list[float | None]:
        if len(closes) < period:
            return [None] * len(closes)
        k = 2 / (period + 1)
        result: list[float | None] = [None] * (period - 1)
        ema = sum(closes[:period]) / period
        result.append(ema)
        for i in range(period, len(closes)):
            ema = closes[i] * k + ema * (1 - k)
            result.append(ema)
        return result

    def _calc_bb(self, closes: list[float], period: int = 20, mult: float = 2.0) -> dict:
        upper, middle, lower = [], [], []
        for i in range(len(closes)):
            if i < period - 1:
                upper.append(None); middle.append(None); lower.append(None)
            else:
                sl = closes[i - period + 1: i + 1]
                avg = sum(sl) / period
                std = (sum((x - avg) ** 2 for x in sl) / period) ** 0.5
                upper.append(avg + mult * std)
                middle.append(avg)
                lower.append(avg - mult * std)
        return {"upper": upper, "middle": middle, "lower": lower}

    def _calc_rsi(self, closes: list[float], period: int = 14) -> list[float | None]:
        if len(closes) < period + 1:
            return [None] * len(closes)
        result: list[float | None] = [None] * period
        gains = [max(closes[i] - closes[i - 1], 0) for i in range(1, period + 1)]
        losses = [max(closes[i - 1] - closes[i], 0) for i in range(1, period + 1)]
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        result.append(100.0 if avg_loss == 0 else 100 - 100 / (1 + avg_gain / avg_loss))
        for i in range(period + 1, len(closes)):
            diff = closes[i] - closes[i - 1]
            avg_gain = (avg_gain * (period - 1) + max(diff, 0)) / period
            avg_loss = (avg_loss * (period - 1) + max(-diff, 0)) / period
            result.append(100.0 if avg_loss == 0 else 100 - 100 / (1 + avg_gain / avg_loss))
        return result

    def _score_ob(self, candle: dict, atr: float) -> int:
        rng = candle["high"] - candle["low"]
        if rng == 0 or atr == 0:
            return 0
        body_ratio = abs(candle["close"] - candle["open"]) / rng
        size_vs_atr = min(rng / atr, 2) / 2
        return min(100, round(body_ratio * 65 + (1 - size_vs_atr) * 35))

    def _score_fvg(self, high: float, low: float, atr: float) -> int:
        if atr == 0:
            return 0
        return min(100, round(((high - low) / atr) * 80))

    def _find_swings(self, candles: list[dict], size: int) -> tuple[list[dict], list[dict]]:
        """Pine Script leg()-based swing detection.

        Checks if bar at (i - size) is a pivot vs the next `size` bars.
        size=50 → swing structure, size=5 → internal structure.
        """
        pivots_high: list[dict] = []
        pivots_low: list[dict] = []
        leg: str | None = None  # 'bearish' | 'bullish' | None

        for i in range(size, len(candles)):
            pivot_idx = i - size
            # Pine: high[size] > ta.highest(size) — pivot bar vs next `size` bars
            sub_high = max(candles[j]["high"] for j in range(pivot_idx + 1, i + 1))
            sub_low = min(candles[j]["low"] for j in range(pivot_idx + 1, i + 1))

            new_leg_high = candles[pivot_idx]["high"] > sub_high
            new_leg_low = candles[pivot_idx]["low"] < sub_low

            prev_leg = leg
            if new_leg_high:
                leg = "bearish"
            elif new_leg_low:
                leg = "bullish"

            if leg != prev_leg and prev_leg is not None:
                if leg == "bullish":  # startOfBullishLeg → pivot LOW confirmed
                    pivots_low.append({
                        "index": pivot_idx,
                        "price": candles[pivot_idx]["low"],
                        "type": "low",
                    })
                elif leg == "bearish":  # startOfBearishLeg → pivot HIGH confirmed
                    pivots_high.append({
                        "index": pivot_idx,
                        "price": candles[pivot_idx]["high"],
                        "type": "high",
                    })

        return pivots_high, pivots_low

    def _detect_structure_and_obs(
        self,
        candles: list[dict],
        swing_highs: list[dict],
        swing_lows: list[dict],
        parsed_highs: list[float],
        parsed_lows: list[float],
        atr: float,
    ) -> tuple[str, dict | None, dict | None, list[dict]]:
        """BOS/CHoCH detection with trend-bias tracking + order block finding.

        Matches Pine Script displayStructure():
        - Bullish break: close > active swing high → BOS if trend==bullish, CHoCH if trend==bearish
        - Bearish break: close < active swing low → BOS if trend==bearish, CHoCH if trend==bullish
        OBs are found at the bar with min parsedLow (bullish) or max parsedHigh (bearish)
        between the pivot and break bar — matching Pine's storeOrdeBlock().
        """
        trend = "ranging"
        last_bos: dict | None = None
        last_choch: dict | None = None
        order_blocks: list[dict] = []

        sh_ptr = 0
        sl_ptr = 0
        current_sh: dict | None = None
        current_sl: dict | None = None
        sh_crossed = False
        sl_crossed = False

        for i in range(len(candles)):
            close = candles[i]["close"]

            # Advance to latest confirmed swing high/low up to bar i
            while sh_ptr < len(swing_highs) and swing_highs[sh_ptr]["index"] <= i:
                current_sh = swing_highs[sh_ptr]
                sh_crossed = False
                sh_ptr += 1

            while sl_ptr < len(swing_lows) and swing_lows[sl_ptr]["index"] <= i:
                current_sl = swing_lows[sl_ptr]
                sl_crossed = False
                sl_ptr += 1

            # Bullish break: close crosses above swing high
            if current_sh and not sh_crossed and close > current_sh["price"]:
                tag = "CHoCH" if trend == "bearish" else "BOS"
                event = {"price": current_sh["price"], "direction": "bullish", "type": tag, "bar_index": i}
                last_bos = event
                if tag == "CHoCH":
                    last_choch = event
                trend = "bullish"
                sh_crossed = True

                # Bullish OB: bar with min parsedLow in [pivot_idx, break_bar)
                pivot_idx = current_sh["index"]
                if pivot_idx < i:
                    min_pl = float("inf")
                    ob_idx = pivot_idx
                    for j in range(pivot_idx, i):
                        if parsed_lows[j] < min_pl:
                            min_pl = parsed_lows[j]
                            ob_idx = j
                    ob_high = parsed_highs[ob_idx]
                    ob_low = parsed_lows[ob_idx]
                    mitigated = any(candles[k]["low"] < ob_low for k in range(ob_idx + 1, len(candles)))
                    strength = 0 if mitigated else self._score_ob(candles[ob_idx], atr)
                    order_blocks.append({
                        "type": "bullish", "index": ob_idx,
                        "high": ob_high, "low": ob_low,
                        "mitigated": mitigated, "strength": strength,
                    })

            # Bearish break: close crosses below swing low
            if current_sl and not sl_crossed and close < current_sl["price"]:
                tag = "CHoCH" if trend == "bullish" else "BOS"
                event = {"price": current_sl["price"], "direction": "bearish", "type": tag, "bar_index": i}
                last_bos = event
                if tag == "CHoCH":
                    last_choch = event
                trend = "bearish"
                sl_crossed = True

                # Bearish OB: bar with max parsedHigh in [pivot_idx, break_bar)
                pivot_idx = current_sl["index"]
                if pivot_idx < i:
                    max_ph = float("-inf")
                    ob_idx = pivot_idx
                    for j in range(pivot_idx, i):
                        if parsed_highs[j] > max_ph:
                            max_ph = parsed_highs[j]
                            ob_idx = j
                    ob_high = parsed_highs[ob_idx]
                    ob_low = parsed_lows[ob_idx]
                    mitigated = any(candles[k]["high"] > ob_high for k in range(ob_idx + 1, len(candles)))
                    strength = 0 if mitigated else self._score_ob(candles[ob_idx], atr)
                    order_blocks.append({
                        "type": "bearish", "index": ob_idx,
                        "high": ob_high, "low": ob_low,
                        "mitigated": mitigated, "strength": strength,
                    })

        return trend, last_bos, last_choch, order_blocks

    def _find_fvgs(self, candles: list[dict], atr: float) -> list[dict]:
        """Pine Script FVG detection with close confirmation.

        Bullish: candle[i+1].low > candle[i-1].high AND candle[i].close > candle[i-1].high
        Bearish: candle[i+1].high < candle[i-1].low AND candle[i].close < candle[i-1].low
        """
        fvgs = []
        for i in range(1, len(candles) - 1):
            prev, mid, nxt = candles[i - 1], candles[i], candles[i + 1]

            if nxt["low"] > prev["high"] and mid["close"] > prev["high"]:
                gap_low, gap_high = prev["high"], nxt["low"]
                filled = any(c["low"] < gap_low for c in candles[i + 2:])
                strength = 0 if filled else self._score_fvg(gap_high, gap_low, atr)
                fvgs.append({
                    "type": "bullish", "high": gap_high, "low": gap_low,
                    "index": i, "filled": filled, "strength": strength,
                })

            if nxt["high"] < prev["low"] and mid["close"] < prev["low"]:
                gap_low, gap_high = nxt["high"], prev["low"]
                filled = any(c["high"] > gap_high for c in candles[i + 2:])
                strength = 0 if filled else self._score_fvg(gap_high, gap_low, atr)
                fvgs.append({
                    "type": "bearish", "high": gap_high, "low": gap_low,
                    "index": i, "filled": filled, "strength": strength,
                })

        return fvgs

    def _calc_smc(self, candles: list[dict]) -> dict:
        if len(candles) < 60:
            last = candles[-1]["close"] if candles else 0
            return {
                "trend": "ranging",
                "swing_highs": [], "swing_lows": [],
                "internal_highs": [], "internal_lows": [],
                "last_bos": None, "last_choch": None,
                "internal_last_bos": None, "internal_last_choch": None,
                "order_blocks": [], "fair_value_gaps": [],
                "premium_discount_pct": 50, "premium_discount_zone": "equilibrium",
                "equilibrium": last, "range_high": last, "range_low": last,
                "buy_side_liquidity": [], "sell_side_liquidity": [],
                "potential_entries": [],
            }

        atr = self._calc_atr(candles, 14)

        # Volatility filter: high-volatility bars get inverted high/low (Pine: parsedHigh/parsedLow)
        atr200 = self._calc_atr(candles, min(200, len(candles) - 1))
        if atr200 == 0:
            atr200 = atr
        parsed_highs: list[float] = []
        parsed_lows: list[float] = []
        for c in candles:
            high_vol = (c["high"] - c["low"]) >= 2 * atr200
            parsed_highs.append(c["low"] if high_vol else c["high"])
            parsed_lows.append(c["high"] if high_vol else c["low"])

        # Swing structure (size=50) + internal structure (size=5)
        swing_highs, swing_lows = self._find_swings(candles, 50)
        internal_highs, internal_lows = self._find_swings(candles, 5)

        # Swing BOS/CHoCH + swing OBs
        trend, last_bos, last_choch, swing_obs = self._detect_structure_and_obs(
            candles, swing_highs, swing_lows, parsed_highs, parsed_lows, atr
        )

        # Internal BOS/CHoCH + internal OBs
        _, int_last_bos, int_last_choch, internal_obs = self._detect_structure_and_obs(
            candles, internal_highs, internal_lows, parsed_highs, parsed_lows, atr
        )

        order_blocks = swing_obs + internal_obs

        fvgs = self._find_fvgs(candles, atr)
        active_fvgs = [f for f in fvgs if not f["filled"]][-6:]

        # Premium/Discount: full dataset range (Pine Script trailing extremes)
        range_high = max(c["high"] for c in candles)
        range_low = min(c["low"] for c in candles)
        rng = range_high - range_low
        close = candles[-1]["close"]
        equilibrium = range_low + rng / 2
        premium_discount_pct = ((close - range_low) / rng * 100) if rng > 0 else 50
        if premium_discount_pct >= 55:
            premium_discount_zone = "premium"
        elif premium_discount_pct <= 45:
            premium_discount_zone = "discount"
        else:
            premium_discount_zone = "equilibrium"

        buy_side_liquidity = sorted([s["price"] for s in swing_highs[-5:]], reverse=True)
        sell_side_liquidity = sorted([s["price"] for s in swing_lows[-5:]])

        potential_entries = []
        strong_obs = [ob for ob in order_blocks if not ob["mitigated"] and ob["strength"] >= 50]
        strong_fvgs = [f for f in active_fvgs if not f["filled"] and f["strength"] >= 30]

        for ob in strong_obs:
            for fvg in strong_fvgs:
                if ob["type"] != fvg["type"]:
                    continue
                overlaps = ob["low"] <= fvg["high"] and ob["high"] >= fvg["low"]
                ob_mid = (ob["high"] + ob["low"]) / 2
                fvg_mid = (fvg["high"] + fvg["low"]) / 2
                if overlaps or abs(ob_mid - fvg_mid) <= atr:
                    zone_high = max(ob["high"], fvg["high"])
                    zone_low = min(ob["low"], fvg["low"])
                    zone_mid = (zone_high + zone_low) / 2
                    confluence_score = round((ob["strength"] + fvg["strength"]) / 2)
                    distance_pct = abs(close - zone_mid) / close * 100 if close > 0 else 0
                    potential_entries.append({
                        "type": ob["type"],
                        "zone_high": zone_high, "zone_low": zone_low,
                        "confluence_score": confluence_score,
                        "ob_strength": ob["strength"], "fvg_strength": fvg["strength"],
                        "distance_pct": round(distance_pct, 4),
                    })

        potential_entries.sort(key=lambda x: x["confluence_score"], reverse=True)

        return {
            "trend": trend,
            "swing_highs": swing_highs,
            "swing_lows": swing_lows,
            "internal_highs": internal_highs,
            "internal_lows": internal_lows,
            "last_bos": last_bos,
            "last_choch": last_choch,
            "internal_last_bos": int_last_bos,
            "internal_last_choch": int_last_choch,
            "order_blocks": order_blocks,
            "fair_value_gaps": active_fvgs,
            "premium_discount_pct": round(premium_discount_pct, 2),
            "premium_discount_zone": premium_discount_zone,
            "equilibrium": equilibrium,
            "range_high": range_high,
            "range_low": range_low,
            "buy_side_liquidity": buy_side_liquidity,
            "sell_side_liquidity": sell_side_liquidity,
            "potential_entries": potential_entries,
        }

    def _calc_classic_indicators(self, candles: list[dict]) -> dict:
        closes = [c["close"] for c in candles]
        atr = self._calc_atr(candles, 14)

        ema9 = self._calc_ema(closes, 9)
        ema20 = self._calc_ema(closes, 20)
        ema50 = self._calc_ema(closes, 50)
        bb = self._calc_bb(closes, 20, 2.0)
        rsi7 = self._calc_rsi(closes, 7)
        rsi14 = self._calc_rsi(closes, 14)
        rsi21 = self._calc_rsi(closes, 21)

        last = -1
        return {
            "atr": round(atr, 6),
            "ema9": ema9[last],
            "ema20": ema20[last],
            "ema50": ema50[last],
            "bb_upper": bb["upper"][last],
            "bb_middle": bb["middle"][last],
            "bb_lower": bb["lower"][last],
            "rsi7": round(rsi7[last], 2) if rsi7[last] is not None else None,
            "rsi14": round(rsi14[last], 2) if rsi14[last] is not None else None,
            "rsi21": round(rsi21[last], 2) if rsi21[last] is not None else None,
        }

    def smc_analysis(self, symbol: str, timeframe: str = "1h", limit: int = 200) -> dict:
        try:
            candles = self.fetch_candles(symbol, timeframe, limit=limit)
            smc = self._calc_smc(candles)
            indicators = self._calc_classic_indicators(candles)
            current_price = candles[-1]["close"]

            result = {
                "symbol": symbol,
                "timeframe": timeframe,
                "current_price": current_price,
                "trend": smc["trend"],
                "last_bos": smc["last_bos"],
                "last_choch": smc["last_choch"],
                "internal_last_bos": smc["internal_last_bos"],
                "internal_last_choch": smc["internal_last_choch"],
                "order_blocks": [ob for ob in smc["order_blocks"] if not ob["mitigated"]],
                "fair_value_gaps": smc["fair_value_gaps"],
                "premium_discount_pct": smc["premium_discount_pct"],
                "premium_discount_zone": smc["premium_discount_zone"],
                "equilibrium": smc["equilibrium"],
                "range_high": smc["range_high"],
                "range_low": smc["range_low"],
                "buy_side_liquidity": smc["buy_side_liquidity"],
                "sell_side_liquidity": smc["sell_side_liquidity"],
                "swing_highs": smc["swing_highs"][-10:],
                "swing_lows": smc["swing_lows"][-10:],
                "internal_highs": smc["internal_highs"][-10:],
                "internal_lows": smc["internal_lows"][-10:],
                "potential_entries": smc["potential_entries"][:5],
                "candles": candles[-50:],
                **indicators,
            }
            return {"result": result}
        except Exception as e:
            return {"status": "error", "message": str(e)}
