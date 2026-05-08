from services.candle_service import CandleService

_candle_service = CandleService()


class WyckoffService:
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

    @staticmethod
    def _vol_sma(vols: list[float], i: int, period: int = 20) -> float:
        start = max(0, i - period + 1)
        sl = vols[start : i + 1]
        return sum(sl) / len(sl) if sl else 1.0

    @staticmethod
    def _spread(c: dict) -> float:
        return c["high"] - c["low"]

    @staticmethod
    def _close_ratio(c: dict) -> float:
        s = c["high"] - c["low"]
        return (c["close"] - c["low"]) / s if s > 0 else 0.5

    @staticmethod
    def _is_bullish(c: dict) -> bool:
        return c["close"] > c["open"]

    @staticmethod
    def _is_bearish(c: dict) -> bool:
        return c["close"] < c["open"]

    def _detect_prior_trend(self, candles: list[dict], end_idx: int, lookback: int = 20) -> str:
        start = max(0, end_idx - lookback)
        segment = candles[start : end_idx + 1]
        if len(segment) < 5:
            return "none"
        total = len(segment) - 1
        if total == 0:
            return "none"
        lows = [c["low"] for c in segment]
        highs = [c["high"] for c in segment]
        down = sum(1 for i in range(1, len(lows)) if lows[i] < lows[i - 1])
        up = sum(1 for i in range(1, len(highs)) if highs[i] > highs[i - 1])
        if down / total >= 0.5:
            return "down"
        if up / total >= 0.5:
            return "up"
        return "none"

    def _empty_result(self) -> dict:
        return {
            "phase": "UNDEFINED", "phase_confidence": 0.0, "events": [],
            "range_high": None, "range_low": None, "range_midpoint": None,
            "spring_low": None, "utad_high": None, "lps_level": None, "lpsy_level": None,
            "target_minimum": None, "target_moderate": None, "target_maximum": None,
            "vol_sma20": 0, "phase_b_up_vol": 0, "phase_b_down_vol": 0,
            "volume_asymmetry": 1.0, "spring_quality": None,
            "wyckoff_smc_bias": "neutral", "smc_score_bonus": 0,
        }

    def _detect_climaxes(
        self, candles: list[dict], vols: list[float], atr: float
    ) -> tuple[list[dict], list[dict], list[dict]]:
        """Pass 1: detect Selling Climax (SC) and Buying Climax (BC) bars."""
        events: list[dict] = []
        sc_events: list[dict] = []
        bc_events: list[dict] = []
        n = len(candles)

        for i in range(1, n - 1):
            vsma = self._vol_sma(vols, i)
            c = candles[i]
            s = self._spread(c)
            cr = self._close_ratio(c)
            vol_ratio = c["volume"] / vsma if vsma > 0 else 0
            spread_ratio = s / atr if atr > 0 else 0

            if (
                self._is_bearish(c)
                and vol_ratio >= 1.8
                and spread_ratio >= 1.5
                and 0.05 < cr < 0.45
                and candles[i + 1]["close"] > c["close"]
                and self._detect_prior_trend(candles, i - 1) == "down"
            ):
                quality = min(100, round(
                    (min(vol_ratio, 4) / 4) * 40 + (1 - cr) * 30 + min(spread_ratio, 3) / 3 * 30
                ))
                ev = {
                    "event_type": "SC", "bar_index": i, "price": c["low"],
                    "volume": c["volume"], "volume_ratio": round(vol_ratio, 2),
                    "spread_ratio": round(spread_ratio, 2), "close_ratio": round(cr, 2),
                    "quality_score": quality,
                }
                events.append(ev)
                sc_events.append(ev)

            if (
                self._is_bullish(c)
                and vol_ratio >= 1.8
                and spread_ratio >= 1.5
                and 0.55 < cr < 0.95
                and candles[i + 1]["close"] < c["close"]
                and self._detect_prior_trend(candles, i - 1) == "up"
            ):
                quality = min(100, round(
                    (min(vol_ratio, 4) / 4) * 40 + cr * 30 + min(spread_ratio, 3) / 3 * 30
                ))
                ev = {
                    "event_type": "BC", "bar_index": i, "price": c["high"],
                    "volume": c["volume"], "volume_ratio": round(vol_ratio, 2),
                    "spread_ratio": round(spread_ratio, 2), "close_ratio": round(cr, 2),
                    "quality_score": quality,
                }
                events.append(ev)
                bc_events.append(ev)

        return events, sc_events, bc_events

    def calc_wyckoff(self, candles: list[dict], atr: float) -> dict:
        """Wyckoff market cycle analysis: phase detection, key events, price targets."""
        n = len(candles)
        if n < 50:
            return self._empty_result()

        vols = [c["volume"] for c in candles]
        events, sc_events, bc_events = self._detect_climaxes(candles, vols, atr)

        # Anchor on the most recent SC or BC
        recent_sc = sc_events[-1] if sc_events else None
        recent_bc = bc_events[-1] if bc_events else None

        analysis_type = None
        anchor_idx = -1
        if recent_sc and recent_bc:
            if recent_sc["bar_index"] > recent_bc["bar_index"]:
                analysis_type, anchor_idx = "accumulation", recent_sc["bar_index"]
            else:
                analysis_type, anchor_idx = "distribution", recent_bc["bar_index"]
        elif recent_sc:
            analysis_type, anchor_idx = "accumulation", recent_sc["bar_index"]
        elif recent_bc:
            analysis_type, anchor_idx = "distribution", recent_bc["bar_index"]

        range_high = range_low = spring_low = spring_quality = utad_high = None
        lps_level = lpsy_level = None
        phase = "UNDEFINED"
        phase_confidence = 0.0
        wyckoff_bias = "neutral"
        smc_bonus = 0
        phase_b_up_vol = phase_b_down_vol = 0.0
        volume_asymmetry = 1.0

        # ── Accumulation branch ───────────────────────────────────────────────
        if analysis_type == "accumulation" and anchor_idx >= 0:
            sc_idx = anchor_idx
            sc_price = candles[sc_idx]["low"]
            range_low = sc_price

            # AR (Automatic Rally)
            ar_idx = ar_high = None
            for i in range(sc_idx + 1, min(sc_idx + 8, n)):
                c = candles[i]
                vsma = self._vol_sma(vols, i)
                if self._is_bullish(c) and c["volume"] >= vsma * 0.9 and self._close_ratio(c) > 0.5:
                    if ar_high is None or c["high"] > ar_high:
                        ar_high, ar_idx = c["high"], i

            if ar_high is not None and ar_idx is not None:
                range_high = ar_high
                events.append({
                    "event_type": "AR", "bar_index": ar_idx, "price": ar_high,
                    "volume": candles[ar_idx]["volume"],
                    "volume_ratio": round(candles[ar_idx]["volume"] / self._vol_sma(vols, ar_idx), 2),
                    "spread_ratio": round(self._spread(candles[ar_idx]) / atr, 2) if atr > 0 else 0,
                    "close_ratio": round(self._close_ratio(candles[ar_idx]), 2),
                    "quality_score": 70,
                })
                phase, phase_confidence = "ACCUMULATION_A", 0.5

            # ST (Secondary Test)
            if ar_idx is not None:
                for i in range(ar_idx + 1, min(ar_idx + 20, n)):
                    c = candles[i]
                    vsma = self._vol_sma(vols, i)
                    if (
                        abs(c["low"] - sc_price) / sc_price < 0.025
                        and c["volume"] < vsma * 0.75
                        and c["close"] > sc_price
                        and self._spread(c) < atr
                    ):
                        events.append({
                            "event_type": "ST", "bar_index": i, "price": c["low"],
                            "volume": c["volume"], "volume_ratio": round(c["volume"] / vsma, 2),
                            "spread_ratio": round(self._spread(c) / atr, 2) if atr > 0 else 0,
                            "close_ratio": round(self._close_ratio(c), 2),
                            "quality_score": 65,
                        })
                        phase, phase_confidence = "ACCUMULATION_B", 0.55
                        break

            # Phase B: volume asymmetry
            if ar_idx is not None and range_high is not None:
                for i in range(ar_idx, min(n, ar_idx + 60)):
                    c = candles[i]
                    if self._is_bullish(c):
                        phase_b_up_vol += c["volume"]
                    else:
                        phase_b_down_vol += c["volume"]
                volume_asymmetry = phase_b_up_vol / phase_b_down_vol if phase_b_down_vol > 0 else 1.0

            # Spring (Phase C)
            if ar_idx is not None:
                for i in range(ar_idx + 3, n):
                    c = candles[i]
                    vsma = self._vol_sma(vols, i)
                    penetration = (sc_price - c["low"]) / sc_price if sc_price > 0 else 0
                    if c["low"] < sc_price and penetration < 0.05:
                        recovery = False
                        recovery_bar = i
                        for j in range(i, min(i + 3, n)):
                            if candles[j]["close"] > sc_price:
                                recovery, recovery_bar = True, j
                                break
                        if recovery:
                            vol_ratio = c["volume"] / vsma if vsma > 0 else 0
                            cr = self._close_ratio(c)
                            pen_score = max(0, 100 - (penetration / 0.05) * 50)
                            vol_score = max(0, 100 * (1 - vol_ratio)) if vol_ratio < 1 else 0
                            rec_score = self._close_ratio(candles[recovery_bar]) * 100
                            quality = round((pen_score + vol_score + rec_score) / 3)
                            spring_low, spring_quality = c["low"], quality
                            events.append({
                                "event_type": "SPRING", "bar_index": i, "price": c["low"],
                                "volume": c["volume"], "volume_ratio": round(vol_ratio, 2),
                                "spread_ratio": round(self._spread(c) / atr, 2) if atr > 0 else 0,
                                "close_ratio": round(cr, 2),
                                "quality_score": quality,
                            })
                            phase, phase_confidence = "ACCUMULATION_C", 0.65
                            break

            # SOS (Sign of Strength) → Phase D
            sos_idx = None
            if ar_idx is not None and range_high is not None and range_low is not None:
                range_mid = (range_high + range_low) / 2
                for i in range(ar_idx + 1, n):
                    c = candles[i]
                    vsma = self._vol_sma(vols, i)
                    vol_ratio = c["volume"] / vsma if vsma > 0 else 0
                    cr = self._close_ratio(c)
                    s = self._spread(c)
                    if (
                        self._is_bullish(c)
                        and vol_ratio >= 1.5
                        and s > atr * 1.2
                        and cr > 0.65
                        and c["close"] > range_mid
                    ):
                        sos_idx = i
                        events.append({
                            "event_type": "SOS", "bar_index": i, "price": c["close"],
                            "volume": c["volume"], "volume_ratio": round(vol_ratio, 2),
                            "spread_ratio": round(s / atr, 2) if atr > 0 else 0,
                            "close_ratio": round(cr, 2),
                            "quality_score": min(100, round(
                                vol_ratio * 30 + cr * 40 + min(s / atr, 2) / 2 * 30
                            )),
                        })
                        if phase in ("ACCUMULATION_C", "ACCUMULATION_B", "ACCUMULATION_A"):
                            phase, phase_confidence = "ACCUMULATION_D", 0.75
                        break

            # LPS (Last Point of Support)
            if sos_idx is not None and range_low is not None:
                for i in range(sos_idx + 1, n):
                    c = candles[i]
                    vsma = self._vol_sma(vols, i)
                    vol_ratio = c["volume"] / vsma if vsma > 0 else 0
                    cr = self._close_ratio(c)
                    if (
                        self._is_bearish(c)
                        and vol_ratio < 0.75
                        and self._spread(c) < atr
                        and c["close"] > range_low
                        and cr > 0.4
                    ):
                        lps_level = c["close"]
                        events.append({
                            "event_type": "LPS", "bar_index": i, "price": c["close"],
                            "volume": c["volume"], "volume_ratio": round(vol_ratio, 2),
                            "spread_ratio": round(self._spread(c) / atr, 2) if atr > 0 else 0,
                            "close_ratio": round(cr, 2),
                            "quality_score": min(100, round((1 - vol_ratio) * 50 + cr * 50)),
                        })
                        break

            if range_high is not None and candles[-1]["close"] > range_high:
                phase, phase_confidence = "ACCUMULATION_E", 0.85

            wyckoff_bias = "bullish"
            smc_bonus = {
                "ACCUMULATION_C": 3, "ACCUMULATION_D": 3,
                "ACCUMULATION_E": 2, "ACCUMULATION_B": 2, "ACCUMULATION_A": 1,
            }.get(phase, 0)

        # ── Distribution branch ───────────────────────────────────────────────
        elif analysis_type == "distribution" and anchor_idx >= 0:
            bc_idx = anchor_idx
            bc_price = candles[bc_idx]["high"]
            range_high = bc_price

            # AR (Automatic Reaction)
            ar_idx = ar_low = None
            for i in range(bc_idx + 1, min(bc_idx + 8, n)):
                c = candles[i]
                vsma = self._vol_sma(vols, i)
                if self._is_bearish(c) and c["volume"] >= vsma * 0.9 and self._close_ratio(c) < 0.5:
                    if ar_low is None or c["low"] < ar_low:
                        ar_low, ar_idx = c["low"], i

            if ar_low is not None and ar_idx is not None:
                range_low = ar_low
                events.append({
                    "event_type": "AR", "bar_index": ar_idx, "price": ar_low,
                    "volume": candles[ar_idx]["volume"],
                    "volume_ratio": round(candles[ar_idx]["volume"] / self._vol_sma(vols, ar_idx), 2),
                    "spread_ratio": round(self._spread(candles[ar_idx]) / atr, 2) if atr > 0 else 0,
                    "close_ratio": round(self._close_ratio(candles[ar_idx]), 2),
                    "quality_score": 70,
                })
                phase, phase_confidence = "DISTRIBUTION_A", 0.5

            # ST (Secondary Test)
            if ar_idx is not None:
                for i in range(ar_idx + 1, min(ar_idx + 20, n)):
                    c = candles[i]
                    vsma = self._vol_sma(vols, i)
                    if (
                        abs(c["high"] - bc_price) / bc_price < 0.025
                        and c["volume"] < vsma * 0.75
                        and c["close"] < bc_price
                        and self._spread(c) < atr
                    ):
                        events.append({
                            "event_type": "ST", "bar_index": i, "price": c["high"],
                            "volume": c["volume"], "volume_ratio": round(c["volume"] / vsma, 2),
                            "spread_ratio": round(self._spread(c) / atr, 2) if atr > 0 else 0,
                            "close_ratio": round(self._close_ratio(c), 2),
                            "quality_score": 65,
                        })
                        phase, phase_confidence = "DISTRIBUTION_B", 0.55
                        break

            # Phase B: volume asymmetry
            if ar_idx is not None and range_low is not None:
                for i in range(ar_idx, min(n, ar_idx + 60)):
                    c = candles[i]
                    if self._is_bullish(c):
                        phase_b_up_vol += c["volume"]
                    else:
                        phase_b_down_vol += c["volume"]
                volume_asymmetry = phase_b_down_vol / phase_b_up_vol if phase_b_up_vol > 0 else 1.0

            # UTAD (Phase C)
            if ar_idx is not None and range_high is not None:
                for i in range(ar_idx + 3, n):
                    c = candles[i]
                    vsma = self._vol_sma(vols, i)
                    if c["high"] > range_high:
                        penetration = (c["high"] - range_high) / range_high
                        if penetration < 0.05:
                            recovery = any(
                                candles[j]["close"] < range_high
                                for j in range(i, min(i + 3, n))
                            )
                            if recovery:
                                vol_ratio = c["volume"] / vsma if vsma > 0 else 0
                                cr = self._close_ratio(c)
                                utad_high = c["high"]
                                events.append({
                                    "event_type": "UTAD", "bar_index": i, "price": c["high"],
                                    "volume": c["volume"], "volume_ratio": round(vol_ratio, 2),
                                    "spread_ratio": round(self._spread(c) / atr, 2) if atr > 0 else 0,
                                    "close_ratio": round(cr, 2),
                                    "quality_score": min(100, round(
                                        (1 - cr) * 60 + min(self._spread(c) / atr, 2) / 2 * 40
                                    )),
                                })
                                phase, phase_confidence = "DISTRIBUTION_C", 0.65
                                break

            # SOW (Sign of Weakness) → Phase D
            sow_idx = None
            if ar_idx is not None and range_high is not None and range_low is not None:
                range_mid = (range_high + range_low) / 2
                for i in range(ar_idx + 1, n):
                    c = candles[i]
                    vsma = self._vol_sma(vols, i)
                    vol_ratio = c["volume"] / vsma if vsma > 0 else 0
                    cr = self._close_ratio(c)
                    s = self._spread(c)
                    if (
                        self._is_bearish(c)
                        and vol_ratio >= 1.5
                        and s > atr * 1.2
                        and cr < 0.35
                        and c["close"] < range_mid
                    ):
                        sow_idx = i
                        events.append({
                            "event_type": "SOW", "bar_index": i, "price": c["close"],
                            "volume": c["volume"], "volume_ratio": round(vol_ratio, 2),
                            "spread_ratio": round(s / atr, 2) if atr > 0 else 0,
                            "close_ratio": round(cr, 2),
                            "quality_score": min(100, round(
                                vol_ratio * 30 + (1 - cr) * 40 + min(s / atr, 2) / 2 * 30
                            )),
                        })
                        if phase in ("DISTRIBUTION_C", "DISTRIBUTION_B", "DISTRIBUTION_A"):
                            phase, phase_confidence = "DISTRIBUTION_D", 0.75
                        break

            # LPSY (Last Point of Supply)
            if sow_idx is not None and range_high is not None:
                for i in range(sow_idx + 1, n):
                    c = candles[i]
                    vsma = self._vol_sma(vols, i)
                    vol_ratio = c["volume"] / vsma if vsma > 0 else 0
                    cr = self._close_ratio(c)
                    if (
                        self._is_bullish(c)
                        and vol_ratio < 0.75
                        and self._spread(c) < atr
                        and c["close"] < range_high
                        and cr < 0.6
                    ):
                        lpsy_level = c["close"]
                        events.append({
                            "event_type": "LPSY", "bar_index": i, "price": c["close"],
                            "volume": c["volume"], "volume_ratio": round(vol_ratio, 2),
                            "spread_ratio": round(self._spread(c) / atr, 2) if atr > 0 else 0,
                            "close_ratio": round(cr, 2),
                            "quality_score": min(100, round((1 - vol_ratio) * 50 + (1 - cr) * 50)),
                        })
                        break

            if range_low is not None and candles[-1]["close"] < range_low:
                phase, phase_confidence = "DISTRIBUTION_E", 0.85

            wyckoff_bias = "bearish"
            smc_bonus = {
                "DISTRIBUTION_C": 3, "DISTRIBUTION_D": 3,
                "DISTRIBUTION_E": 2, "DISTRIBUTION_B": 2, "DISTRIBUTION_A": 1,
            }.get(phase, 0)

        # ── Cause & Effect price targets ──────────────────────────────────────
        target_min = target_mod = target_max = None
        if range_high is not None and range_low is not None:
            rw = range_high - range_low
            if analysis_type == "accumulation":
                anchor = spring_low if spring_low is not None else range_low
                target_min = round(anchor + rw, 6)
                target_mod = round(anchor + rw * 1.5, 6)
                target_max = round(anchor + rw * 2, 6)
            elif analysis_type == "distribution":
                anchor = utad_high if utad_high is not None else range_high
                target_min = round(anchor - rw, 6)
                target_mod = round(anchor - rw * 1.5, 6)
                target_max = round(anchor - rw * 2, 6)

        return {
            "phase": phase,
            "phase_confidence": round(phase_confidence, 2),
            "events": sorted(events, key=lambda e: e["bar_index"], reverse=True)[:10],
            "range_high": range_high,
            "range_low": range_low,
            "range_midpoint": (
                round((range_high + range_low) / 2, 6)
                if range_high is not None and range_low is not None
                else None
            ),
            "spring_low": spring_low,
            "utad_high": utad_high,
            "lps_level": lps_level,
            "lpsy_level": lpsy_level,
            "target_minimum": target_min,
            "target_moderate": target_mod,
            "target_maximum": target_max,
            "vol_sma20": round(self._vol_sma(vols, n - 1), 2),
            "phase_b_up_vol": round(phase_b_up_vol, 2),
            "phase_b_down_vol": round(phase_b_down_vol, 2),
            "volume_asymmetry": round(volume_asymmetry, 3),
            "spring_quality": spring_quality,
            "wyckoff_smc_bias": wyckoff_bias,
            "smc_score_bonus": smc_bonus,
        }

    def wyckoff_analysis(self, symbol: str, timeframe: str = "1h", limit: int = 200) -> dict:
        try:
            candles = _candle_service.fetch_candles(symbol, timeframe, limit=limit)
            atr = self._calc_atr(candles, 14)
            wyckoff = self.calc_wyckoff(candles, atr)
            return {"result": {"symbol": symbol, "timeframe": timeframe, **wyckoff}}
        except Exception as e:
            return {"status": "error", "message": str(e)}
