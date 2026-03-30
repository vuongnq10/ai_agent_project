import { useEffect, useRef } from "react";
import { createChart, ColorType, LineSeries, HistogramSeries } from "lightweight-charts";
import type { Candle } from "../types";
import { calcRSI, calcMACD } from "../indicators";

interface Props {
  candles: Candle[];
}

export default function IndicatorChart({ candles }: Props) {
  const rsiRef = useRef<HTMLDivElement>(null);
  const macdRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!rsiRef.current || !macdRef.current || candles.length === 0) return;
    const closes = candles.map((c) => c.close);

    // RSI chart
    const rsiChart = createChart(rsiRef.current, {
      layout: { background: { type: ColorType.Solid, color: "#0d1117" }, textColor: "#9ca3af" },
      grid: { vertLines: { color: "#1f2937" }, horzLines: { color: "#1f2937" } },
      rightPriceScale: { borderColor: "#374151", scaleMargins: { top: 0.1, bottom: 0.1 } },
      timeScale: { borderColor: "#374151", timeVisible: true, secondsVisible: false },
      width: rsiRef.current.clientWidth,
      height: 120,
    });
    const rsiData = calcRSI(closes, 14);
    const rsiSeries = rsiChart.addSeries(LineSeries, {
      color: "#f59e0b",
      lineWidth: 2,
      priceLineVisible: false,
    });
    rsiSeries.setData(
      candles.map((c, i) => ({ time: c.time as any, value: rsiData[i] })).filter((d) => d.value != null) as any
    );
    // overbought / oversold reference lines
    const ob = rsiChart.addSeries(LineSeries, {
      color: "rgba(239,68,68,0.4)",
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: false,
    });
    const os = rsiChart.addSeries(LineSeries, {
      color: "rgba(34,197,94,0.4)",
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: false,
    });
    const validCandles = candles.filter((_, i) => rsiData[i] != null);
    if (validCandles.length > 0) {
      ob.setData(validCandles.map((c) => ({ time: c.time as any, value: 70 })));
      os.setData(validCandles.map((c) => ({ time: c.time as any, value: 30 })));
    }

    // MACD chart
    const macdChart = createChart(macdRef.current, {
      layout: { background: { type: ColorType.Solid, color: "#0d1117" }, textColor: "#9ca3af" },
      grid: { vertLines: { color: "#1f2937" }, horzLines: { color: "#1f2937" } },
      rightPriceScale: { borderColor: "#374151" },
      timeScale: { borderColor: "#374151", timeVisible: true, secondsVisible: false },
      width: macdRef.current.clientWidth,
      height: 120,
    });
    const { macdLine, signalLine, histogram } = calcMACD(closes);
    const macdSeries = macdChart.addSeries(LineSeries, {
      color: "#3b82f6",
      lineWidth: 2,
      priceLineVisible: false,
    });
    macdSeries.setData(
      candles.map((c, i) => ({ time: c.time as any, value: macdLine[i] })).filter((d) => d.value != null) as any
    );
    const sigSeries = macdChart.addSeries(LineSeries, {
      color: "#f97316",
      lineWidth: 1,
      priceLineVisible: false,
    });
    sigSeries.setData(
      candles.map((c, i) => ({ time: c.time as any, value: signalLine[i] })).filter((d) => d.value != null) as any
    );
    const histSeries = macdChart.addSeries(HistogramSeries, { priceLineVisible: false });
    histSeries.setData(
      candles
        .map((c, i) => ({
          time: c.time as any,
          value: histogram[i],
          color: (histogram[i] ?? 0) >= 0 ? "rgba(34,197,94,0.5)" : "rgba(239,68,68,0.5)",
        }))
        .filter((d) => d.value != null) as any
    );

    const roRsi = new ResizeObserver(() => rsiChart.applyOptions({ width: rsiRef.current!.clientWidth }));
    const roMacd = new ResizeObserver(() => macdChart.applyOptions({ width: macdRef.current!.clientWidth }));
    roRsi.observe(rsiRef.current);
    roMacd.observe(macdRef.current);

    return () => {
      roRsi.disconnect();
      roMacd.disconnect();
      rsiChart.remove();
      macdChart.remove();
    };
  }, [candles]);

  return (
    <div className="indicator-charts">
      <div className="indicator-label">RSI (14)</div>
      <div ref={rsiRef} className="indicator-chart-container" />
      <div className="indicator-label">MACD (12/26/9)</div>
      <div ref={macdRef} className="indicator-chart-container" />
    </div>
  );
}
