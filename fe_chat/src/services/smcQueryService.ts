import { fetchCandles } from './binanceService';
import { calcSMC, calcEMA, calcRSI, calcATR } from '../App/indicators';
import type { SMCResult } from '../App/indicators';
import type { Candle } from '../App/types';

const TIMEFRAMES = [
  { label: '30m', interval: '30m' },
  { label: '2h', interval: '2h' },
  { label: '4h', interval: '4h' },
] as const;

function p(n: number, digits = 4): string {
  return n.toFixed(digits);
}

function formatSMC(
  symbol: string,
  tf: string,
  candles: Candle[],
  smc: SMCResult,
): string {
  const closes = candles.map((c) => c.close);
  const lastClose = closes[closes.length - 1];
  const atr = calcATR(candles, 14);
  const ema9 = calcEMA(closes, 9).at(-1) ?? null;
  const ema20 = calcEMA(closes, 20).at(-1) ?? null;
  const ema50 = calcEMA(closes, 50).at(-1) ?? null;
  const rsi14 = calcRSI(closes, 14).at(-1) ?? null;

  const activeOBs = smc.orderBlocks.filter((ob) => !ob.mitigated);
  const activeFVGs = smc.fairValueGaps.filter((f) => !f.filled);

  const lines: string[] = [
    `### ${symbol} — ${tf} Timeframe`,
    `Current Price: ${p(lastClose)}`,
    `Trend: ${smc.trend.toUpperCase()}`,
    `ATR(14): ${p(atr)}`,
    ``,
    `**Structure**`,
    `BOS: ${smc.lastBOS ? `${smc.lastBOS.direction} at ${p(smc.lastBOS.price)}` : 'none'}`,
    `CHoCH: ${smc.lastCHoCH ? `${smc.lastCHoCH.direction} at ${p(smc.lastCHoCH.price)}` : 'none'}`,
    ``,
    `**Premium / Discount**`,
    `Range: ${p(smc.rangeLow)} – ${p(smc.rangeHigh)}`,
    `Equilibrium: ${p(smc.equilibrium)}`,
    `Zone: ${smc.premiumDiscountZone} (${p(smc.premiumDiscountPct, 1)}%)`,
    ``,
    `**Order Blocks (unmitigated)**`,
    activeOBs.length === 0
      ? 'none'
      : activeOBs
          .slice(-4)
          .map((ob) => `  ${ob.type} OB: ${p(ob.low)} – ${p(ob.high)}`)
          .join('\n'),
    ``,
    `**Fair Value Gaps (unfilled)**`,
    activeFVGs.length === 0
      ? 'none'
      : activeFVGs
          .slice(-4)
          .map((f) => `  ${f.type} FVG: ${p(f.low)} – ${p(f.high)}`)
          .join('\n'),
    ``,
    `**Liquidity**`,
    `Buy-side (above): ${
      smc.buySideLiquidity
        .slice(0, 3)
        .map((v) => p(v))
        .join(', ') || 'none'
    }`,
    `Sell-side (below): ${
      smc.sellSideLiquidity
        .slice(0, 3)
        .map((v) => p(v))
        .join(', ') || 'none'
    }`,
    ``,
    `**Indicators**`,
    `EMA9: ${ema9 != null ? p(ema9) : 'n/a'}  EMA20: ${ema20 != null ? p(ema20) : 'n/a'}  EMA50: ${ema50 != null ? p(ema50) : 'n/a'}`,
    `RSI(14): ${rsi14 != null ? p(rsi14, 1) : 'n/a'}`,
  ];

  return lines.join('\n');
}

export async function buildSmcQuery(
  symbol: string,
  userNote: string,
): Promise<string> {
  const results = await Promise.all(
    TIMEFRAMES.map(async ({ label, interval }) => {
      const candles = await fetchCandles(symbol, interval);
      const smc = calcSMC(candles);
      return formatSMC(symbol, label, candles, smc);
    }),
  );

  const header = [
    `The following SMC analysis was computed on the frontend for ${symbol}.`,
    `Analyze the multi-timeframe confluence, determine the highest-probability trade setup, then create an order if conditions are met.`,
    ``,
    `---`,
    ``,
    ...results.map((r) => r + '\n\n---'),
  ].join('\n');

  const footer = userNote.trim()
    ? `\n\nAdditional context: ${userNote.trim()}`
    : '';

  return header + footer;
}
