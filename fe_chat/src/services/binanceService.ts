import type { Candle, Ticker } from "../App/types";

import { BINANCE_BASE_URL } from "./config";

export async function fetchCandles(symbol: string, timeframe: string): Promise<Candle[]> {
  const res = await fetch(
    `${BINANCE_BASE_URL}/klines?symbol=${symbol}&interval=${timeframe}&limit=300`
  );
  const raw: [number, string, string, string, string, string][] = await res.json();
  return raw.map((k) => ({
    time: Math.floor(k[0] / 1000),
    open: parseFloat(k[1]),
    high: parseFloat(k[2]),
    low: parseFloat(k[3]),
    close: parseFloat(k[4]),
    volume: parseFloat(k[5]),
  }));
}

export async function fetchTicker(symbol: string): Promise<Ticker> {
  const res = await fetch(`${BINANCE_BASE_URL}/ticker/24hr?symbol=${symbol}`);
  const data = await res.json();
  return {
    price: parseFloat(data.lastPrice),
    change: parseFloat(data.priceChange),
    changePercent: parseFloat(data.priceChangePercent),
    high: parseFloat(data.highPrice),
    low: parseFloat(data.lowPrice),
    volume: parseFloat(data.quoteVolume),
  };
}
