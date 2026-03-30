import { coins } from "../coins";

interface Props {
  onCoinClick: (coin: string) => void;
  selectedCoin?: string;
}

export default function CoinList({ onCoinClick, selectedCoin }: Props) {
  return (
    <div className="coin-section">
      <div className="section-title">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="10"/>
          <path d="M12 6v6l4 2"/>
        </svg>
        Markets
      </div>
      <div className="coin-grid">
        {coins.map((coin) => (
          <button
            key={coin}
            className={`coin-chip ${selectedCoin === coin ? "active" : ""}`}
            onClick={() => onCoinClick(coin)}
          >
            <span className="coin-symbol">{coin.replace("USDT", "")}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
