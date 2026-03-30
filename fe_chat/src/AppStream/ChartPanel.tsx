import { useState, useEffect, useCallback, useMemo } from "react";
import type { Candle } from "./types";
import { calcSMC } from "./indicators";
import MarketBar from "./MarketBar";
import CandleChart from "./CandleChart";
import IndicatorChart from "./IndicatorChart";
import SMCPanel from "./SMCPanel";
import TimeframeSelector, { type Timeframe } from "./TimeframeSelector";

const TF_MAP: Record<Timeframe, string> = {
  "1m": "1m", "5m": "5m", "15m": "15m", "1h": "1h", "4h": "4h", "1d": "1d",
};

interface Props {
  symbol: string;
  onAnalyze: (symbol: string, timeframe: Timeframe) => void;
}

export default function ChartPanel({ symbol, onAnalyze }: Props) {
  const [timeframe, setTimeframe] = useState<Timeframe>("1h");
  const [candles, setCandles] = useState<Candle[]>([]);
  const [loading, setLoading] = useState(false);
  const [smcMode, setSmcMode] = useState(false);

  const fetchCandles = useCallback(async (sym: string, tf: Timeframe) => {
    setLoading(true);
    try {
      const res = await fetch(
        `https://api.binance.com/api/v3/klines?symbol=${sym}&interval=${TF_MAP[tf]}&limit=300`
      );
      const raw: [number, string, string, string, string, string][] = await res.json();
      setCandles(
        raw.map((k) => ({
          time: Math.floor(k[0] / 1000),
          open: parseFloat(k[1]),
          high: parseFloat(k[2]),
          low: parseFloat(k[3]),
          close: parseFloat(k[4]),
          volume: parseFloat(k[5]),
        }))
      );
    } catch (e) {
      console.error("Failed to fetch candles", e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCandles(symbol, timeframe);
    const interval = setInterval(() => fetchCandles(symbol, timeframe), 30000);
    return () => clearInterval(interval);
  }, [symbol, timeframe, fetchCandles]);

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
          <CandleChart
            candles={candles}
            height={360}
            smcMode={smcMode}
            smcData={smcData}
          />

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
