// ─── SMC Types ────────────────────────────────────────────────────────────────

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
  strength: number; // 0–100
}

export interface FVG {
  type: "bullish" | "bearish";
  high: number;
  low: number;
  index: number;
  filled: boolean;
  strength: number; // 0–100
}

export interface PotentialEntry {
  type: "bullish" | "bearish";
  zoneHigh: number;
  zoneLow: number;
  confluenceScore: number; // 0–100
  obStrength: number;
  fvgStrength: number;
  distancePct: number; // % distance from current price to zone midpoint
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
  potentialEntries: PotentialEntry[];
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

export function calcATR(candles: { high: number; low: number; close: number }[], period = 14): number {
  if (candles.length < period + 1) return 0;
  const trs: number[] = [];
  for (let i = 1; i < candles.length; i++) {
    const hl = candles[i].high - candles[i].low;
    const hpc = Math.abs(candles[i].high - candles[i - 1].close);
    const lpc = Math.abs(candles[i].low - candles[i - 1].close);
    trs.push(Math.max(hl, hpc, lpc));
  }
  let atr = trs.slice(0, period).reduce((a, b) => a + b, 0) / period;
  for (let i = period; i < trs.length; i++) {
    atr = (atr * (period - 1) + trs[i]) / period;
  }
  return atr;
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
