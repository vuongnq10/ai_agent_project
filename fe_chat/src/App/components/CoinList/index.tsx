import { useState } from "react";

interface Props {
  coins: string[];
  onCoinClick: (coin: string) => void;
  selectedCoin?: string;
}

export default function CoinList({ coins, onCoinClick, selectedCoin }: Props) {
  const [search, setSearch] = useState("");

  const filtered = coins.filter((c) =>
    c.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="coin-sidebar">
      <div className="coin-sidebar-header">
        <span className="coin-sidebar-title">Markets</span>
        <span className="coin-sidebar-count">{filtered.length}</span>
      </div>
      <div className="coin-search-wrap">
        <input
          type="text"
          className="coin-search"
          placeholder="Search..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>
      <div className="coin-list">
        {filtered.length === 0 ? (
          <div className="coin-empty">
            <span>No results</span>
          </div>
        ) : (
          filtered.map((coin) => {
            const isActive = selectedCoin === coin;
            const base = coin.replace("USDT", "");
            return (
              <div
                key={coin}
                className={`coin-row${isActive ? " active" : ""}`}
                onClick={() => onCoinClick(coin)}
                title={coin}
              >
                <span className="coin-row-symbol">{base}</span>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
