import { useTicker } from "../../hooks/useTicker";

interface Props {
  symbol: string;
}

export default function MarketBar({ symbol }: Props) {
  const ticker = useTicker(symbol);

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
