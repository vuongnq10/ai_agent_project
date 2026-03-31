import { useState, useEffect, useCallback } from "react";
import type { Candle } from "../App/types";
import type { Timeframe } from "../constants";
import { fetchCandles as fetchCandlesService } from "../services/binanceService";

export function useCandles(symbol: string) {
  const [timeframe, setTimeframe] = useState<Timeframe>("1h");
  const [candles, setCandles] = useState<Candle[]>([]);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async (sym: string, tf: Timeframe) => {
    setLoading(true);
    try {
      const data = await fetchCandlesService(sym, tf);
      setCandles(data);
    } catch (e) {
      console.error("Failed to fetch candles", e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load(symbol, timeframe);
    const interval = setInterval(() => load(symbol, timeframe), 30000);
    return () => clearInterval(interval);
  }, [symbol, timeframe, load]);

  return { candles, loading, timeframe, setTimeframe };
}
