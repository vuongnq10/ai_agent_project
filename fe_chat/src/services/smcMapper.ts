import type { SmcAnalysisResult } from './tradingService';
import type { SMCResult } from '../App/indicators';

const EMPTY_SMC: SMCResult = {
  trend: 'ranging',
  swingHighs: [], swingLows: [],
  lastBOS: null, lastCHoCH: null,
  orderBlocks: [], fairValueGaps: [],
  premiumDiscountPct: 50, premiumDiscountZone: 'equilibrium',
  equilibrium: 0, rangeHigh: 0, rangeLow: 0,
  buySideLiquidity: [], sellSideLiquidity: [],
  potentialEntries: [],
};

export { EMPTY_SMC };

export function mapApiToSMC(api: SmcAnalysisResult): SMCResult {
  return {
    trend: api.trend,
    swingHighs: api.swing_highs,
    swingLows: api.swing_lows,
    lastBOS: api.last_bos,
    lastCHoCH: api.last_choch,
    orderBlocks: api.order_blocks.map((ob) => ({
      type: ob.type,
      index: ob.index,
      high: ob.high,
      low: ob.low,
      mitigated: ob.mitigated,
      strength: ob.strength,
    })),
    fairValueGaps: api.fair_value_gaps.map((f) => ({
      type: f.type,
      high: f.high,
      low: f.low,
      index: f.index,
      filled: f.filled,
      strength: f.strength,
    })),
    premiumDiscountPct: api.premium_discount_pct,
    premiumDiscountZone: api.premium_discount_zone,
    equilibrium: api.equilibrium,
    rangeHigh: api.range_high,
    rangeLow: api.range_low,
    buySideLiquidity: api.buy_side_liquidity,
    sellSideLiquidity: api.sell_side_liquidity,
    potentialEntries: api.potential_entries.map((e) => ({
      type: e.type,
      zoneHigh: e.zone_high,
      zoneLow: e.zone_low,
      confluenceScore: e.confluence_score,
      obStrength: e.ob_strength,
      fvgStrength: e.fvg_strength,
      distancePct: e.distance_pct,
    })),
  };
}
