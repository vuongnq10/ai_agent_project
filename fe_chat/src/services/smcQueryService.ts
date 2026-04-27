import { smcAnalysis } from './tradingService';
import type { SmcAnalysisResult } from './tradingService';

const TIMEFRAMES = [
  { label: '4h', interval: '4h' },
  { label: '2h', interval: '2h' },
  { label: '1h', interval: '1h' },
] as const;

function fixNumber(n: number, digits = 4): string {
  return n.toFixed(digits);
}

function formatSMC(
  symbol: string,
  tf: string,
  data: SmcAnalysisResult,
): string {
  const activeOBs = data.order_blocks.filter((ob) => !ob.mitigated);
  const activeFVGs = data.fair_value_gaps.filter((f) => !f.filled);

  const lines: string[] = [
    `### ${symbol} — ${tf} Timeframe`,
    `Current Price: ${fixNumber(data.current_price)}`,
    `Trend: ${data.trend.toUpperCase()}`,
    `ATR(14): ${fixNumber(data.atr)}`,
    ``,
    `**Structure**`,
    `BOS: ${data.last_bos ? `${data.last_bos.direction} at ${fixNumber(data.last_bos.price)}` : 'none'}`,
    `CHoCH: ${data.last_choch ? `${data.last_choch.direction} at ${fixNumber(data.last_choch.price)}` : 'none'}`,
    ``,
    `**Premium / Discount**`,
    `Range: ${fixNumber(data.range_low)} – ${fixNumber(data.range_high)}`,
    `Equilibrium: ${fixNumber(data.equilibrium)}`,
    `Zone: ${data.premium_discount_zone} (${fixNumber(data.premium_discount_pct, 1)}%)`,
    ``,
    `**Order Blocks (unmitigated, strength 0–100%)**`,
    activeOBs.length === 0
      ? 'none'
      : activeOBs
          .slice(-4)
          .map(
            (ob) =>
              `  ${ob.type} OB: ${fixNumber(ob.low)} – ${fixNumber(ob.high)}  strength=${ob.strength}%`,
          )
          .join('\n'),
    ``,
    `**Fair Value Gaps (unfilled, strength 0–100%)**`,
    activeFVGs.length === 0
      ? 'none'
      : activeFVGs
          .slice(-4)
          .map(
            (f) =>
              `  ${f.type} FVG: ${fixNumber(f.low)} – ${fixNumber(f.high)}  strength=${f.strength}%`,
          )
          .join('\n'),
    ``,
    `**Potential Entry Zones (OB + FVG confluence)**`,
    data.potential_entries.length === 0
      ? 'none'
      : data.potential_entries
          .slice(0, 3)
          .map(
            (e) =>
              `  ${e.type.toUpperCase()} zone: ${fixNumber(e.zone_low)} – ${fixNumber(e.zone_high)}  confluence=${e.confluence_score}%  OB=${e.ob_strength}%  FVG=${e.fvg_strength}%  dist=${fixNumber(e.distance_pct, 2)}%`,
          )
          .join('\n'),
    ``,
    `**Liquidity**`,
    `Buy-side (above): ${
      data.buy_side_liquidity
        .slice(0, 3)
        .map((v) => fixNumber(v))
        .join(', ') || 'none'
    }`,
    `Sell-side (below): ${
      data.sell_side_liquidity
        .slice(0, 3)
        .map((v) => fixNumber(v))
        .join(', ') || 'none'
    }`,
    ``,
    `**Indicators**`,
    `EMA9: ${data.ema9 != null ? fixNumber(data.ema9) : 'n/a'}  EMA20: ${data.ema20 != null ? fixNumber(data.ema20) : 'n/a'}  EMA50: ${data.ema50 != null ? fixNumber(data.ema50) : 'n/a'}`,
    `RSI(14): ${data.rsi14 != null ? fixNumber(data.rsi14, 1) : 'n/a'}`,
    ``,
    `**Last 50 Candles**`,
    `\`\`\`json`,
    JSON.stringify(data.candles ?? [], null, 2),
    `\`\`\``,
  ];

  return lines.join('\n');
}

export async function buildSmcQuery(
  symbol: string,
  userNote: string,
): Promise<string> {
  const results = await Promise.all(
    TIMEFRAMES.map(async ({ label, interval }) => {
      const response = await smcAnalysis(symbol, interval);
      if (!response.result) {
        return `### ${symbol} — ${label} Timeframe\nError: ${response.message ?? 'Unknown error'}`;
      }
      return formatSMC(symbol, label, response.result);
    }),
  );

  const header = [
    `The following SMC analysis was fetched from the backend for ${symbol}.`,
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
