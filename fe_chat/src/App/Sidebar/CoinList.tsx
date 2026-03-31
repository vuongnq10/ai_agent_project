import { useState, useRef, useEffect } from "react";
import { coins } from "../../coins";

interface Props {
  onCoinClick: (coin: string) => void;
  selectedCoin?: string;
}

export default function CoinList({ onCoinClick, selectedCoin }: Props) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const ref = useRef<HTMLDivElement>(null);

  const filtered = coins.filter((c) =>
    c.toLowerCase().includes(search.toLowerCase())
  );

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
        setSearch("");
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const handleSelect = (coin: string) => {
    onCoinClick(coin);
    setOpen(false);
    setSearch("");
  };

  return (
    <div className="coin-dropdown" ref={ref}>
      <button className="coin-dropdown-trigger" onClick={() => setOpen((o) => !o)}>
        <span className="coin-dd-symbol">{selectedCoin?.replace("USDT", "") ?? "BTC"}</span>
        <span className="coin-dd-pair">/ USDT</span>
        <svg
          width="11"
          height="11"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.5"
          className={`coin-dd-caret${open ? " open" : ""}`}
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>

      {open && (
        <div className="coin-dropdown-menu">
          <div className="coin-dropdown-search">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
            <input
              autoFocus
              type="text"
              className="coin-search-input"
              placeholder="Search coin..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <div className="coin-dropdown-list">
            {filtered.length === 0 ? (
              <div className="coin-dropdown-empty">No results</div>
            ) : (
              filtered.map((coin) => (
                <button
                  key={coin}
                  className={`coin-dropdown-item${selectedCoin === coin ? " active" : ""}`}
                  onClick={() => handleSelect(coin)}
                >
                  <span className="coin-dd-symbol">{coin.replace("USDT", "")}</span>
                  <span className="coin-dd-pair">USDT</span>
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
