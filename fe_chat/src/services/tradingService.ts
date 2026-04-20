import { BOT_BASE_URL } from './config';

export async function setLeverage(
  symbol: string,
  leverage: number,
): Promise<{ success: boolean; message?: string }> {
  const res = await fetch(`${BOT_BASE_URL}/trading/leverage`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ symbol, leverage }),
  });
  return res.json();
}

export interface BulkLeverageResult {
  symbol: string;
  success: boolean;
  leverage?: number;
  message?: string;
}

export async function setBulkLeverage(
  symbols: string[],
  leverage: number,
): Promise<{ results: BulkLeverageResult[] }> {
  const res = await fetch(`${BOT_BASE_URL}/trading/leverage/bulk`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ symbols, leverage }),
  });
  return res.json();
}

// ─── SMC Analysis Types ────────────────────────────────────────────────────────

export type Trend = 'bullish' | 'bearish' | 'ranging';
export type Direction = 'bullish' | 'bearish';
export type Zone = 'premium' | 'discount' | 'equilibrium';

export interface BosChoch {
  price: number;
  direction: Direction;
}

export interface OrderBlock {
  type: Direction;
  index: number;
  high: number;
  low: number;
  mitigated: boolean;
  strength: number;
}

export interface FairValueGap {
  type: Direction;
  high: number;
  low: number;
  index: number;
  filled: boolean;
  strength: number;
}

export interface SwingPoint {
  index: number;
  price: number;
  type: 'high' | 'low';
}

export interface PotentialEntry {
  type: Direction;
  zone_high: number;
  zone_low: number;
  confluence_score: number;
  ob_strength: number;
  fvg_strength: number;
  distance_pct: number;
}

export interface SmcAnalysisResult {
  symbol: string;
  timeframe: string;
  current_price: number;
  trend: Trend;
  last_bos: BosChoch | null;
  last_choch: BosChoch | null;
  order_blocks: OrderBlock[];
  fair_value_gaps: FairValueGap[];
  premium_discount_pct: number;
  premium_discount_zone: Zone;
  equilibrium: number;
  range_high: number;
  range_low: number;
  buy_side_liquidity: number[];
  sell_side_liquidity: number[];
  swing_highs: SwingPoint[];
  swing_lows: SwingPoint[];
  potential_entries: PotentialEntry[];
  atr: number;
  ema9: number | null;
  ema20: number | null;
  ema50: number | null;
  bb_upper: number | null;
  bb_middle: number | null;
  bb_lower: number | null;
  rsi7: number | null;
  rsi14: number | null;
  rsi21: number | null;
}

export interface SmcAnalysisResponse {
  result?: SmcAnalysisResult;
  status?: 'error';
  message?: string;
}

export async function smcAnalysis(
  symbol: string,
  timeframe = '1h',
  limit = 200,
): Promise<SmcAnalysisResponse> {
  const params = new URLSearchParams({
    symbol,
    timeframe,
    limit: String(limit),
  });
  const res = await fetch(`${BOT_BASE_URL}/trading/smc?${params}`);
  return res.json();
}
