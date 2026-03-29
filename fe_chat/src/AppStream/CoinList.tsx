import { coins } from "../coins";

interface CoinListProps {
  onCoinClick: (coin: string) => void;
}

export default function CoinList({ onCoinClick }: CoinListProps) {
  return (
    <div className="coin-section">
      <h3 className="section-title">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="3"></circle>
          <path d="m12 1v6m0 6v6"></path>
          <path d="m1 12h6m6 0h6"></path>
        </svg>
        Popular Coins
      </h3>
      <div className="coin-grid">
        {coins.map((coin) => (
          <button
            key={coin}
            className="coin-chip"
            onClick={() => onCoinClick(coin)}
            title={`Analyze ${coin}`}
          >
            <span className="coin-symbol">{coin}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
