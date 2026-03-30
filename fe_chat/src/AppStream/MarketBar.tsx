import { useEffect, useState } from "react";
import type { Ticker } from "./types";

interface Props {
  symbol: string;
}

export default function MarketBar({ symbol }: Props) {
  const [ticker, setTicker] = useState<Ticker | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function fetchTicker() {
      try {
        const res = await fetch(
          `https://api.binance.com/api/v3/ticker/24hr?symbol=${symbol}`
        );
        const data = await res.json();
        if (!cancelled) {
          setTicker({
            price: parseFloat(data.lastPrice),
            change: parseFloat(data.priceChange),
            changePercent: parseFloat(data.priceChangePercent),
            high: parseFloat(data.highPrice),
            low: parseFloat(data.lowPrice),
            volume: parseFloat(data.quoteVolume),
          });
        }
      } catch {}
    }
    fetchTicker();
    const interval = setInterval(fetchTicker, 5000);
    return () => { cancelled = true; clearInterval(interval); };
  }, [symbol]);

  if (!ticker) return <div className="market-bar market-bar-loading">Loading...</div>;

  const isPos = ticker.changePercent >= 0;
  return (
    <div className="market-bar">
      <span className="market-bar-symbol">{symbol.replace("USDT", "/USDT")}</span>
      <span className={`market-bar-price ${isPos ? "up" : "down"}`}>
        {ticker.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 6 })}
      </span>
      <span className={`market-bar-change ${isPos ? "up" : "down"}`}>
        {isPos ? "+" : ""}{ticker.changePercent.toFixed(2)}%
      </span>
      <div className="market-bar-stats">
        <div className="stat-item"><span className="stat-label">24h High</span><span className="stat-value up">{ticker.high.toFixed(4)}</span></div>
        <div className="stat-item"><span className="stat-label">24h Low</span><span className="stat-value down">{ticker.low.toFixed(4)}</span></div>
        <div className="stat-item"><span className="stat-label">24h Vol</span><span className="stat-value">${(ticker.volume / 1e6).toFixed(1)}M</span></div>
      </div>
    </div>
  );
}
