import { useState, useMemo } from "react";
import { calcSMC } from "../indicators";
import MarketBar from "./MarketBar";
import CandleChart from "./CandleChart";
import IndicatorChart from "./IndicatorChart";
import SMCPanel from "./SMCPanel";
import TimeframeSelector, { type Timeframe } from "./TimeframeSelector";
import IndicatorPicker, { type IndicatorId, INDICATORS } from "./IndicatorPicker";
import { useCandles } from "../../hooks/useCandles";

interface Props {
  symbol: string;
  timeframe: Timeframe;
  onTimeframeChange: (tf: Timeframe) => void;
  onAnalyze: (symbol: string, timeframe: Timeframe) => void;
}

const DEFAULT_ACTIVE = new Set<IndicatorId>(["ema9", "ema20", "ema50", "bb", "rsi"]);

export default function ChartPanel({ symbol, timeframe, onTimeframeChange, onAnalyze }: Props) {
  const [smcMode, setSmcMode] = useState(false);
  const [activeIndicators, setActiveIndicators] = useState<Set<IndicatorId>>(DEFAULT_ACTIVE);
  const { candles, loading } = useCandles(symbol, timeframe);
  const smcData = useMemo(() => calcSMC(candles), [candles]);

  const toggleIndicator = (id: IndicatorId, checked: boolean) => {
    setActiveIndicators((prev) => {
      const next = new Set(prev);
      if (checked) next.add(id);
      else next.delete(id);
      return next;
    });
  };

  const activeLegend = INDICATORS.filter(
    (i) => i.group === "overlay" && activeIndicators.has(i.id)
  );

  return (
    <div className="chart-panel">
      <div className="chart-toolbar">
        <MarketBar symbol={symbol} />
        <div className="chart-toolbar-right">
          <TimeframeSelector value={timeframe} onChange={onTimeframeChange} />
          <IndicatorPicker active={activeIndicators} onChange={toggleIndicator} />
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
          <CandleChart
            candles={candles}
            smcMode={smcMode}
            smcData={smcData}
            activeIndicators={activeIndicators}
          />
          {activeLegend.length > 0 && (
            <div className="chart-legend">
              {activeLegend.map((ind) => (
                <span key={ind.id} className="legend-item" style={{ color: ind.color }}>
                  {ind.label}
                </span>
              ))}
            </div>
          )}
          <IndicatorChart candles={candles} activeIndicators={activeIndicators} />
          <SMCPanel candles={candles} />
        </>
      )}
    </div>
  );
}
