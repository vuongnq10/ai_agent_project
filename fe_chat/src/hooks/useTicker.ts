import { useState, useEffect } from "react";
import type { Ticker } from "../App/types";
import { fetchTicker as fetchTickerService } from "../services/binanceService";

export function useTicker(symbol: string) {
  const [ticker, setTicker] = useState<Ticker | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const data = await fetchTickerService(symbol);
        if (!cancelled) setTicker(data);
      } catch {}
    }
    load();
    const interval = setInterval(load, 5000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [symbol]);

  return ticker;
}
