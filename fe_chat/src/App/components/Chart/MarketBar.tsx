import { useTicker } from "../../../hooks/useTicker";

interface Props {
  symbol: string;
}

export default function MarketBar({ symbol }: Props) {
  const ticker = useTicker(symbol);

  if (!ticker) return <div className="market-bar">Loading...</div>;

  const isPos = ticker.changePercent >= 0;
  return (
    <div className="market-bar">
      <span className="market-symbol">{symbol.replace("USDT", "/USDT")}</span>
      <span className={`market-price ${isPos ? "up" : "down"}`}>
        {ticker.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 6 })}
      </span>
      <span className={`market-change ${isPos ? "up" : "down"}`}>
        {isPos ? "+" : ""}{ticker.changePercent.toFixed(2)}%
      </span>
      <div className="market-stat">
        <span className="market-stat-label">24h High</span>
        <span className="market-stat-value text-green">{ticker.high.toFixed(4)}</span>
      </div>
      <div className="market-stat">
        <span className="market-stat-label">24h Low</span>
        <span className="market-stat-value text-red">{ticker.low.toFixed(4)}</span>
      </div>
      <div className="market-stat">
        <span className="market-stat-label">24h Vol</span>
        <span className="market-stat-value">${(ticker.volume / 1e6).toFixed(1)}M</span>
      </div>
    </div>
  );
}
