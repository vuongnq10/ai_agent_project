import { useState } from "react";
import { coins } from "../../coins";
import { useLeverage } from "../../hooks/useLeverage";

export default function LeveragePanel() {
  const [symbol, setSymbol] = useState("SOLUSDT");
  const [value, setValue] = useState(20);
  const { status, applyLeverage } = useLeverage();

  return (
    <div className="leverage-section">
      <h3 className="section-title">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M12 2v20M2 12h20"></path>
        </svg>
        Leverage
      </h3>
      <div className="leverage-form">
        <select
          className="leverage-select"
          value={symbol}
          onChange={(e) => setSymbol(e.target.value)}
        >
          {coins.map((coin) => (
            <option key={coin} value={coin}>{coin}</option>
          ))}
        </select>
        <div className="leverage-input-row">
          <input
            type="number"
            className="leverage-input"
            value={value}
            min={1}
            max={125}
            onChange={(e) => setValue(Number(e.target.value))}
          />
          <span className="leverage-unit">x</span>
        </div>
        <button className="set-leverage-btn" onClick={() => applyLeverage(symbol, value)}>
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
