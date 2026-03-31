// ─── SMC Types ────────────────────────────────────────────────────────────────

import type { Candle } from "./types";

export interface SwingPoint {
  index: number;
  price: number;
  type: "high" | "low";
}

export interface OrderBlock {
  type: "bullish" | "bearish";
  high: number;
  low: number;
  index: number;
  mitigated: boolean;
}

export interface FVG {
  type: "bullish" | "bearish";
  high: number;
  low: number;
  index: number;
  filled: boolean;
}

export interface SMCResult {
  trend: "bullish" | "bearish" | "ranging";
  swingHighs: SwingPoint[];
  swingLows: SwingPoint[];
  lastBOS: { price: number; direction: "bullish" | "bearish" } | null;
  lastCHoCH: { price: number; direction: "bullish" | "bearish" } | null;
  orderBlocks: OrderBlock[];
  fairValueGaps: FVG[];
  premiumDiscountPct: number; // 0–100
  premiumDiscountZone: "premium" | "equilibrium" | "discount";
  equilibrium: number;
  rangeHigh: number;
  rangeLow: number;
  buySideLiquidity: number[];  // swing high prices (sell stops above)
  sellSideLiquidity: number[]; // swing low prices (buy stops below)
}

// ─── SMC Calculations ─────────────────────────────────────────────────────────

function findSwings(candles: Candle[], lookback = 5): { highs: SwingPoint[]; lows: SwingPoint[] } {
  const highs: SwingPoint[] = [];
  const lows: SwingPoint[] = [];
  for (let i = lookback; i < candles.length - lookback; i++) {
    const c = candles[i];
    let isHigh = true, isLow = true;
    for (let j = i - lookback; j <= i + lookback; j++) {
      if (j === i) continue;
      if (candles[j].high >= c.high) isHigh = false;
      if (candles[j].low <= c.low) isLow = false;
    }
    if (isHigh) highs.push({ index: i, price: c.high, type: "high" });
    if (isLow) lows.push({ index: i, price: c.low, type: "low" });
  }
  return { highs, lows };
}

export function calcSMC(candles: Candle[]): SMCResult {
  if (candles.length < 30) {
    const last = candles[candles.length - 1]?.close ?? 0;
    return {
      trend: "ranging", swingHighs: [], swingLows: [],
      lastBOS: null, lastCHoCH: null, orderBlocks: [], fairValueGaps: [],
      premiumDiscountPct: 50, premiumDiscountZone: "equilibrium",
      equilibrium: last, rangeHigh: last, rangeLow: last,
      buySideLiquidity: [], sellSideLiquidity: [],
    };
  }

  const { highs: swingHighs, lows: swingLows } = findSwings(candles, 5);
  const recentHighs = swingHighs.slice(-6);
  const recentLows = swingLows.slice(-6);

  // ── Trend: compare last two swing highs and lows ─────────────────────────
  let trend: "bullish" | "bearish" | "ranging" = "ranging";
  if (recentHighs.length >= 2 && recentLows.length >= 2) {
    const hhUp = recentHighs[recentHighs.length - 1].price > recentHighs[recentHighs.length - 2].price;
    const hlUp = recentLows[recentLows.length - 1].price > recentLows[recentLows.length - 2].price;
    const lhDown = recentHighs[recentHighs.length - 1].price < recentHighs[recentHighs.length - 2].price;
    const llDown = recentLows[recentLows.length - 1].price < recentLows[recentLows.length - 2].price;
    if (hhUp && hlUp) trend = "bullish";
    else if (lhDown && llDown) trend = "bearish";
  }

  // ── BOS / CHoCH ──────────────────────────────────────────────────────────
  const close = candles[candles.length - 1].close;
  let lastBOS: SMCResult["lastBOS"] = null;
  let lastCHoCH: SMCResult["lastCHoCH"] = null;
  // Track the candle index of the swing point that was broken so we can
  // compare recency without fragile float equality on prices.
  let lastBOSSwingIndex = -1;

  // BOS bullish: current close is above the most recent swing high it broke
  for (let i = swingHighs.length - 1; i >= 0; i--) {
    if (close > swingHighs[i].price) {
      lastBOS = { price: swingHighs[i].price, direction: "bullish" };
      lastBOSSwingIndex = swingHighs[i].index;
      if (trend === "bearish") lastCHoCH = { price: swingHighs[i].price, direction: "bullish" };
      break;
    }
  }
  // BOS bearish: current close is below the most recent swing low it broke.
  // Only overrides the bullish BOS if this swing low occurred more recently
  // (higher candle index) than the swing high that was broken above.
  for (let i = swingLows.length - 1; i >= 0; i--) {
    if (close < swingLows[i].price) {
      if (swingLows[i].index > lastBOSSwingIndex) {
        lastBOS = { price: swingLows[i].price, direction: "bearish" };
        if (trend === "bullish") lastCHoCH = { price: swingLows[i].price, direction: "bearish" };
      }
      break;
    }
  }

  // ── Order Blocks ─────────────────────────────────────────────────────────
  const orderBlocks: OrderBlock[] = [];
  // Bullish OB: last red candle before a bullish BOS (demand zone)
  for (let i = swingLows.length - 1; i >= Math.max(0, swingLows.length - 4); i--) {
    const swIdx = swingLows[i].index;
    // find last red candle at/before this swing low
    for (let j = swIdx; j >= Math.max(0, swIdx - 10); j--) {
      if (candles[j].close < candles[j].open) {
        const obHigh = candles[j].high;
        const obLow = candles[j].low;
        // Mitigated when a subsequent candle CLOSES inside the OB zone.
        // Wick-only touches are not counted — price must commit with a close.
        const mitigated = candles.slice(j + 1).some(
          (c) => c.close >= obLow && c.close <= obHigh
        );
        orderBlocks.push({ type: "bullish", index: j, high: obHigh, low: obLow, mitigated });
        break;
      }
    }
  }
  // Bearish OB: last green candle before a bearish BOS (supply zone)
  for (let i = swingHighs.length - 1; i >= Math.max(0, swingHighs.length - 4); i--) {
    const swIdx = swingHighs[i].index;
    for (let j = swIdx; j >= Math.max(0, swIdx - 10); j--) {
      if (candles[j].close > candles[j].open) {
        const obHigh = candles[j].high;
        const obLow = candles[j].low;
        const mitigated = candles.slice(j + 1).some(
          (c) => c.close >= obLow && c.close <= obHigh
        );
        orderBlocks.push({ type: "bearish", index: j, high: obHigh, low: obLow, mitigated });
        break;
      }
    }
  }

  // ── Fair Value Gaps ───────────────────────────────────────────────────────
  const fairValueGaps: FVG[] = [];
  for (let i = 1; i < candles.length - 1; i++) {
    const prev = candles[i - 1];
    const next = candles[i + 1];
    // Bullish FVG: gap between prev high and next low [prev.high, next.low]
    if (prev.high < next.low) {
      const gapBottom = prev.high;
      const gapTop = next.low;
      // Filled when a subsequent candle CLOSES into the gap zone (not just wicks).
      const filled = candles.slice(i + 2).some((c) => c.close <= gapTop && c.close >= gapBottom);
      fairValueGaps.push({ type: "bullish", high: gapTop, low: gapBottom, index: i, filled });
    }
    // Bearish FVG: gap between next high and prev low [next.high, prev.low]
    if (prev.low > next.high) {
      const gapBottom = next.high;
      const gapTop = prev.low;
      const filled = candles.slice(i + 2).some((c) => c.close >= gapBottom && c.close <= gapTop);
      fairValueGaps.push({ type: "bearish", high: gapTop, low: gapBottom, index: i, filled });
    }
  }
  // Keep only the 3 most recent per type
  const activeFVGs = fairValueGaps
    .filter((f) => !f.filled)
    .slice(-6);

  // ── Premium / Discount ────────────────────────────────────────────────────
  const rangeCandles = candles.slice(-100);
  const rangeHigh = Math.max(...rangeCandles.map((c) => c.high));
  const rangeLow = Math.min(...rangeCandles.map((c) => c.low));
  const range = rangeHigh - rangeLow;
  const equilibrium = rangeLow + range / 2;
  const premiumDiscountPct = range > 0 ? ((close - rangeLow) / range) * 100 : 50;
  const premiumDiscountZone: SMCResult["premiumDiscountZone"] =
    premiumDiscountPct >= 55 ? "premium" : premiumDiscountPct <= 45 ? "discount" : "equilibrium";

  // ── Liquidity ─────────────────────────────────────────────────────────────
  const buySideLiquidity = swingHighs.slice(-5).map((s) => s.price).sort((a, b) => b - a);
  const sellSideLiquidity = swingLows.slice(-5).map((s) => s.price).sort((a, b) => a - b);

  return {
    trend, swingHighs, swingLows,
    lastBOS, lastCHoCH,
    orderBlocks, fairValueGaps: activeFVGs,
    premiumDiscountPct, premiumDiscountZone, equilibrium, rangeHigh, rangeLow,
    buySideLiquidity, sellSideLiquidity,
  };
}

// ─── Classic Indicators ───────────────────────────────────────────────────────

export function calcEMA(closes: number[], period: number): (number | null)[] {
  const k = 2 / (period + 1);
  const result: (number | null)[] = new Array(period - 1).fill(null);
  let ema = closes.slice(0, period).reduce((a, b) => a + b, 0) / period;
  result.push(ema);
  for (let i = period; i < closes.length; i++) {
    ema = closes[i] * k + ema * (1 - k);
    result.push(ema);
  }
  return result;
}

export function calcBB(closes: number[], period = 20, mult = 2) {
  const upper: (number | null)[] = [];
  const middle: (number | null)[] = [];
  const lower: (number | null)[] = [];
  for (let i = 0; i < closes.length; i++) {
    if (i < period - 1) {
      upper.push(null); middle.push(null); lower.push(null);
    } else {
      const slice = closes.slice(i - period + 1, i + 1);
      const avg = slice.reduce((a, b) => a + b, 0) / period;
      const std = Math.sqrt(slice.reduce((a, b) => a + (b - avg) ** 2, 0) / period);
      upper.push(avg + mult * std);
      middle.push(avg);
      lower.push(avg - mult * std);
    }
  }
  return { upper, middle, lower };
}

export function calcRSI(closes: number[], period = 14): (number | null)[] {
  if (closes.length < period + 1) return closes.map(() => null);
  const result: (number | null)[] = new Array(period).fill(null);
  const gains: number[] = [];
  const losses: number[] = [];
  for (let i = 1; i <= period; i++) {
    const diff = closes[i] - closes[i - 1];
    gains.push(Math.max(diff, 0));
    losses.push(Math.max(-diff, 0));
  }
  let avgGain = gains.reduce((a, b) => a + b, 0) / period;
  let avgLoss = losses.reduce((a, b) => a + b, 0) / period;
  result.push(avgLoss === 0 ? 100 : 100 - 100 / (1 + avgGain / avgLoss));
  for (let i = period + 1; i < closes.length; i++) {
    const diff = closes[i] - closes[i - 1];
    avgGain = (avgGain * (period - 1) + Math.max(diff, 0)) / period;
    avgLoss = (avgLoss * (period - 1) + Math.max(-diff, 0)) / period;
    result.push(avgLoss === 0 ? 100 : 100 - 100 / (1 + avgGain / avgLoss));
  }
  return result;
}

export function calcMACD(closes: number[], fast = 12, slow = 26, signal = 9) {
  const fastEMA = calcEMA(closes, fast);
  const slowEMA = calcEMA(closes, slow);
  const macdLine: (number | null)[] = [];
  for (let i = 0; i < closes.length; i++) {
    const f = fastEMA[i]; const s = slowEMA[i];
    macdLine.push(f != null && s != null ? f - s : null);
  }
  const validMacd = macdLine.filter((v): v is number => v !== null);
  const signalRaw = calcEMA(validMacd, signal);
  let sigIdx = 0;
  const signalLine: (number | null)[] = macdLine.map((v) =>
    v == null ? null : (signalRaw[sigIdx++] ?? null)
  );
  const histogram: (number | null)[] = macdLine.map((v, i) => {
    const s = signalLine[i];
    return v != null && s != null ? v - s : null;
  });
  return { macdLine, signalLine, histogram };
}
