import { useEffect, useRef } from "react";
import { createChart, ColorType, LineSeries } from "lightweight-charts";
import type { Candle } from "../../types";
import type { IndicatorId } from "./IndicatorPicker";
import { calcRSI } from "../../indicators";

interface Props {
  candles: Candle[];
  activeIndicators: Set<IndicatorId>;
}

export default function IndicatorChart({ candles, activeIndicators }: Props) {
  const rsiRef = useRef<HTMLDivElement>(null);

  const showRSI = activeIndicators.has("rsi");

  useEffect(() => {
    if (!showRSI || !rsiRef.current || candles.length === 0) return;

    const closes = candles.map((c) => c.close);

    const chart = createChart(rsiRef.current, {
      layout: { background: { type: ColorType.Solid, color: "#0d1117" }, textColor: "#9ca3af" },
      grid: { vertLines: { color: "#1f2937" }, horzLines: { color: "#1f2937" } },
      rightPriceScale: { borderColor: "#374151", scaleMargins: { top: 0.1, bottom: 0.1 } },
      timeScale: { borderColor: "#374151", timeVisible: true, secondsVisible: false },
      width: rsiRef.current.clientWidth,
      height: 120,
    });

    const rsiData = calcRSI(closes, 14);
    const rsiSeries = chart.addSeries(LineSeries, {
      color: "#f59e0b",
      lineWidth: 2,
      priceLineVisible: false,
    });
    rsiSeries.setData(
      candles.map((c, i) => ({ time: c.time as any, value: rsiData[i] })).filter((d) => d.value != null) as any
    );

    const ob = chart.addSeries(LineSeries, { color: "rgba(242,54,69,0.4)", lineWidth: 1, priceLineVisible: false, lastValueVisible: false });
    const os = chart.addSeries(LineSeries, { color: "rgba(8,153,129,0.4)", lineWidth: 1, priceLineVisible: false, lastValueVisible: false });
    const validCandles = candles.filter((_, i) => rsiData[i] != null);
    if (validCandles.length > 0) {
      ob.setData(validCandles.map((c) => ({ time: c.time as any, value: 70 })));
      os.setData(validCandles.map((c) => ({ time: c.time as any, value: 30 })));
    }

    const ro = new ResizeObserver(() => chart.applyOptions({ width: rsiRef.current!.clientWidth }));
    ro.observe(rsiRef.current);

    return () => {
      ro.disconnect();
      chart.remove();
    };
  }, [candles, showRSI]);

  if (!showRSI) return null;

  return (
    <div className="indicator-charts">
      <div className="indicator-label">RSI (14)</div>
      <div ref={rsiRef} className="indicator-chart-container" />
    </div>
  );
}
