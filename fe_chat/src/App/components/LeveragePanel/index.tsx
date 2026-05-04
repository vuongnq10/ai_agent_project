import { useState } from "react";
import { useLeverage } from "../../../hooks/useLeverage";

interface Props {
  coins: string[];
}

export default function LeveragePanel({ coins }: Props) {
  const [selected, setSelected] = useState<Set<string>>(new Set(["SOLUSDT"]));
  const [value, setValue] = useState(20);
  const { status, bulkResults, loading, applyBulkLeverage } = useLeverage();

  const allSelected = selected.size === coins.length;

  const toggleAll = () => {
    if (allSelected) {
      setSelected(new Set());
    } else {
      setSelected(new Set(coins));
    }
  };

  const toggleCoin = (coin: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(coin)) {
        next.delete(coin);
      } else {
        next.add(coin);
      }
      return next;
    });
  };

  const resultMap = new Map(bulkResults.map((r) => [r.symbol, r]));

  return (
    <div>
      <div className="leverage-title">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M12 2v20M2 12h20"></path>
        </svg>
        Leverage Settings
      </div>
      <div className="leverage-section">
        <div className="leverage-row">
          <label className="leverage-label">Leverage (x)</label>
          <input
            type="number"
            className="leverage-input"
            value={value}
            min={1}
            max={125}
            onChange={(e) => setValue(Number(e.target.value))}
          />
        </div>

        <div className="leverage-row">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
            <label className="leverage-label">Coins ({selected.size}/{coins.length})</label>
            <button
              className="btn btn-ghost"
              style={{ fontSize: 11, padding: "2px 6px" }}
              onClick={toggleAll}
            >
              {allSelected ? "Deselect All" : "Select All"}
            </button>
          </div>
          <div className="leverage-coin-list">
            {coins.map((coin) => {
              const result = resultMap.get(coin);
              return (
                <label key={coin} className="leverage-coin-item">
                  <input
                    type="checkbox"
                    checked={selected.has(coin)}
                    onChange={() => toggleCoin(coin)}
                    style={{ accentColor: "var(--accent)" }}
                  />
                  <span className="leverage-coin-name">{coin}</span>
                  {result && (
                    <span className={`leverage-coin-badge ${result.success ? "success" : "error"}`}>
                      {result.success ? `${result.leverage}x` : "!"}
                    </span>
                  )}
                </label>
              );
            })}
          </div>
        </div>

        <button
          className="btn btn-accent"
          style={{ width: "100%" }}
          disabled={selected.size === 0 || loading}
          onClick={() => applyBulkLeverage(Array.from(selected), value)}
        >
          {loading ? "Applying..." : `Set ${value}x for ${selected.size} Coin(s)`}
        </button>

        {status.type && (
          <p className={`leverage-status ${status.type}`}>
            {status.message}
          </p>
        )}
      </div>
    </div>
  );
}
