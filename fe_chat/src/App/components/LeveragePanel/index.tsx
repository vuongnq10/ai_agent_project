import { useState } from "react";
import { coins } from "../../../coins";
import { useLeverage } from "../../../hooks/useLeverage";

export default function LeveragePanel() {
  const [symbol, setSymbol] = useState("SOLUSDT");
  const [value, setValue] = useState(20);
  const { status, applyLeverage } = useLeverage();

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
          <label className="leverage-label">Symbol</label>
          <select
            className="leverage-select"
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
          >
            {coins.map((coin) => (
              <option key={coin} value={coin}>{coin}</option>
            ))}
          </select>
        </div>
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
        <button
          className="btn btn-accent"
          style={{ width: "100%" }}
          onClick={() => applyLeverage(symbol, value)}
        >
          Set Leverage
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
