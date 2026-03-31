import { useState, useMemo } from "react";
import { calcSMC } from "../indicators";
import MarketBar from "./MarketBar";
import CandleChart from "./CandleChart";
import IndicatorChart from "./IndicatorChart";
import SMCPanel from "./SMCPanel";
import TimeframeSelector, { type Timeframe } from "./TimeframeSelector";
import { useCandles } from "../../hooks/useCandles";

interface Props {
  symbol: string;
  onAnalyze: (symbol: string, timeframe: Timeframe) => void;
}

export default function ChartPanel({ symbol, onAnalyze }: Props) {
  const [smcMode, setSmcMode] = useState(false);
  const { candles, loading, timeframe, setTimeframe } = useCandles(symbol);
  const smcData = useMemo(() => calcSMC(candles), [candles]);

  return (
    <div className="chart-panel">
      <div className="chart-toolbar">
        <MarketBar symbol={symbol} />
        <div className="chart-toolbar-right">
          <TimeframeSelector value={timeframe} onChange={setTimeframe} />
          <label className="smc-toggle" title={smcMode ? "Switch to Classic" : "Switch to SMC"}>
            <input
              type="checkbox"
              checked={smcMode}
              onChange={(e) => setSmcMode(e.target.checked)}
            />
            <span className="smc-toggle-track">
              <span className="smc-toggle-thumb" />
            </span>
            <span className="smc-toggle-label">SMC</span>
          </label>
          <button className="analyze-btn" onClick={() => onAnalyze(symbol, timeframe)}>
            AI Analyze
          </button>
        </div>
      </div>
      {loading && candles.length === 0 ? (
        <div className="chart-loading">Loading chart data...</div>
      ) : (
        <>
          <CandleChart candles={candles} height={360} smcMode={smcMode} smcData={smcData} />
          <div className="chart-legend">
            <span className="legend-item ema9">EMA 9</span>
            <span className="legend-item ema20">EMA 20</span>
            <span className="legend-item ema50">EMA 50</span>
            <span className="legend-item bb">BB (20,2)</span>
          </div>
          <IndicatorChart candles={candles} />
          <SMCPanel candles={candles} />
        </>
      )}
    </div>
  );
}
