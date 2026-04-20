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

    def _find_swings(self, candles: list[dict], lookback: int = 5) -> tuple[list[dict], list[dict]]:
        highs, lows = [], []
        for i in range(lookback, len(candles) - lookback):
            c = candles[i]
            is_high = is_low = True
            for j in range(i - lookback, i + lookback + 1):
                if j == i:
                    continue
                if candles[j]["high"] >= c["high"]:
                    is_high = False
                if candles[j]["low"] <= c["low"]:
                    is_low = False
            if is_high:
                highs.append({"index": i, "price": c["high"], "type": "high"})
            if is_low:
                lows.append({"index": i, "price": c["low"], "type": "low"})
        return highs, lows

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

    def _calc_smc(self, candles: list[dict]) -> dict:
        if len(candles) < 30:
            last = candles[-1]["close"] if candles else 0
            return {
                "trend": "ranging", "swing_highs": [], "swing_lows": [],
                "last_bos": None, "last_choch": None,
                "order_blocks": [], "fair_value_gaps": [],
                "premium_discount_pct": 50, "premium_discount_zone": "equilibrium",
                "equilibrium": last, "range_high": last, "range_low": last,
                "buy_side_liquidity": [], "sell_side_liquidity": [],
                "potential_entries": [],
            }

        atr = self._calc_atr(candles, 14)
        swing_highs, swing_lows = self._find_swings(candles, 5)
        recent_highs = swing_highs[-6:]
        recent_lows = swing_lows[-6:]

        trend = "ranging"
        if len(recent_highs) >= 2 and len(recent_lows) >= 2:
            hh_up = recent_highs[-1]["price"] > recent_highs[-2]["price"]
            hl_up = recent_lows[-1]["price"] > recent_lows[-2]["price"]
            lh_down = recent_highs[-1]["price"] < recent_highs[-2]["price"]
            ll_down = recent_lows[-1]["price"] < recent_lows[-2]["price"]
            if hh_up and hl_up:
                trend = "bullish"
            elif lh_down and ll_down:
                trend = "bearish"

        close = candles[-1]["close"]
        last_bos = None
        last_choch = None
        last_bos_swing_index = -1

        for i in range(len(swing_highs) - 1, -1, -1):
            if close > swing_highs[i]["price"]:
                last_bos = {"price": swing_highs[i]["price"], "direction": "bullish"}
                last_bos_swing_index = swing_highs[i]["index"]
                if trend == "bearish":
                    last_choch = {"price": swing_highs[i]["price"], "direction": "bullish"}
                break

        for i in range(len(swing_lows) - 1, -1, -1):
            if close < swing_lows[i]["price"]:
                if swing_lows[i]["index"] > last_bos_swing_index:
                    last_bos = {"price": swing_lows[i]["price"], "direction": "bearish"}
                    if trend == "bullish":
                        last_choch = {"price": swing_lows[i]["price"], "direction": "bearish"}
                break

        order_blocks = []

        for i in range(len(swing_lows) - 1, max(-1, len(swing_lows) - 5), -1):
            sw_idx = swing_lows[i]["index"]
            for j in range(sw_idx, max(-1, sw_idx - 11), -1):
                if candles[j]["close"] < candles[j]["open"]:
                    ob_high, ob_low = candles[j]["high"], candles[j]["low"]
                    mitigated = any(ob_low <= c["close"] <= ob_high for c in candles[j + 1:])
                    strength = 0 if mitigated else self._score_ob(candles[j], atr)
                    order_blocks.append({
                        "type": "bullish", "index": j,
                        "high": ob_high, "low": ob_low,
                        "mitigated": mitigated, "strength": strength,
                    })
                    break

        for i in range(len(swing_highs) - 1, max(-1, len(swing_highs) - 5), -1):
            sw_idx = swing_highs[i]["index"]
            for j in range(sw_idx, max(-1, sw_idx - 11), -1):
                if candles[j]["close"] > candles[j]["open"]:
                    ob_high, ob_low = candles[j]["high"], candles[j]["low"]
                    mitigated = any(ob_low <= c["close"] <= ob_high for c in candles[j + 1:])
                    strength = 0 if mitigated else self._score_ob(candles[j], atr)
                    order_blocks.append({
                        "type": "bearish", "index": j,
                        "high": ob_high, "low": ob_low,
                        "mitigated": mitigated, "strength": strength,
                    })
                    break

        fair_value_gaps = []
        for i in range(1, len(candles) - 1):
            prev, nxt = candles[i - 1], candles[i + 1]
            if prev["high"] < nxt["low"]:
                gap_bot, gap_top = prev["high"], nxt["low"]
                filled = any(gap_bot <= c["close"] <= gap_top for c in candles[i + 2:])
                strength = 0 if filled else self._score_fvg(gap_top, gap_bot, atr)
                fair_value_gaps.append({
                    "type": "bullish", "high": gap_top, "low": gap_bot,
                    "index": i, "filled": filled, "strength": strength,
                })
            if prev["low"] > nxt["high"]:
                gap_bot, gap_top = nxt["high"], prev["low"]
                filled = any(gap_bot <= c["close"] <= gap_top for c in candles[i + 2:])
                strength = 0 if filled else self._score_fvg(gap_top, gap_bot, atr)
                fair_value_gaps.append({
                    "type": "bearish", "high": gap_top, "low": gap_bot,
                    "index": i, "filled": filled, "strength": strength,
                })

        active_fvgs = [f for f in fair_value_gaps if not f["filled"]][-6:]

        range_candles = candles[-100:]
        range_high = max(c["high"] for c in range_candles)
        range_low = min(c["low"] for c in range_candles)
        rng = range_high - range_low
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
                proximity = abs(ob_mid - fvg_mid)
                if overlaps or proximity <= atr:
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
            "last_bos": last_bos,
            "last_choch": last_choch,
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
                "potential_entries": smc["potential_entries"][:5],
                **indicators,
            }
            return {"result": result}
        except Exception as e:
            return {"status": "error", "message": str(e)}
