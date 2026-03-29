import { useState } from "react";
import { coins } from "../coins";
import type { LeverageStatus } from "./types";

export default function LeveragePanel() {
  const [symbol, setSymbol] = useState("SOLUSDT");
  const [value, setValue] = useState(20);
  const [status, setStatus] = useState<LeverageStatus>({ type: null, message: "" });

  const handleSetLeverage = async () => {
    setStatus({ type: null, message: "" });
    try {
      const res = await fetch("http://127.0.0.1:8000/trading/leverage", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ symbol, leverage: value }),
      });
      const data = await res.json();
      if (data.success) {
        setStatus({ type: "success", message: `Leverage set to ${value}x for ${symbol}` });
      } else {
        setStatus({ type: "error", message: data.message || "Failed" });
      }
    } catch {
      setStatus({ type: "error", message: "Request failed" });
    }
  };

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
        <button className="set-leverage-btn" onClick={handleSetLeverage}>
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
