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
      <div className="coin-sidebar-list">
        {filtered.length === 0 ? (
          <div className="coin-item" style={{ color: "var(--text-muted)", cursor: "default" }}>No results</div>
        ) : (
          filtered.map((coin) => (
            <div
              key={coin}
              className={`coin-item${selectedCoin === coin ? " selected" : ""}`}
              onClick={() => onCoinClick(coin)}
            >
              <span className="coin-item-base">{coin.replace("USDT", "")}</span>
              <span className="coin-item-quote">USDT</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
