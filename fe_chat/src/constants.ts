export const TIMEFRAMES = ["15m", "1h", "2h", "4h", "12h", "1d"] as const;
export type Timeframe = (typeof TIMEFRAMES)[number];
