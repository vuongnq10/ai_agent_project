import { useState, useRef, useEffect } from "react";
import { coins } from "../../../coins";

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

  const base = selectedCoin?.replace("USDT", "") ?? "BTC";

  return (
    <div className="coin-dropdown" ref={ref}>
      <button className="coin-trigger" onClick={() => setOpen((o) => !o)}>
        <span className="coin-trigger-base">{base}</span>
        <span className="coin-trigger-quote">/ USDT</span>
        <svg
          width="11"
          height="11"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.5"
          className={`coin-trigger-chevron${open ? " open" : ""}`}
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>

      {open && (
        <div className="coin-dropdown-menu">
          <div className="coin-search-wrap">
            <input
              autoFocus
              type="text"
              className="coin-search"
              placeholder="Search coin..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <div className="coin-list-scroll">
            {filtered.length === 0 ? (
              <div className="coin-item" style={{ color: "var(--text-muted)", cursor: "default" }}>No results</div>
            ) : (
              filtered.map((coin) => (
                <div
                  key={coin}
                  className={`coin-item${selectedCoin === coin ? " selected" : ""}`}
                  onClick={() => handleSelect(coin)}
                >
                  {coin.replace("USDT", "")} <span style={{ color: "var(--text-muted)", fontWeight: 400 }}>USDT</span>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
