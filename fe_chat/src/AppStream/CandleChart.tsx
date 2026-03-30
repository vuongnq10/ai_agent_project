import { useEffect, useRef } from "react";
import {
  createChart,
  ColorType,
  CrosshairMode,
  CandlestickSeries,
  HistogramSeries,
  LineSeries,
  LineStyle,
  createSeriesMarkers,
} from "lightweight-charts";
import type { Candle } from "./types";
import type { SMCResult } from "./indicators";
import { calcEMA, calcBB } from "./indicators";
import { BoxPrimitive, HLinePrimitive } from "./smcDrawings";

interface Props {
  candles: Candle[];
  height?: number;
  smcMode?: boolean;
  smcData?: SMCResult | null;
}

export default function CandleChart({
  candles,
  height = 360,
  smcMode = false,
  smcData,
}: Props) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current || candles.length === 0) return;
    const container = containerRef.current;

    const chart = createChart(container, {
      layout: {
        background: { type: ColorType.Solid, color: "#0d1117" },
        textColor: "#9ca3af",
      },
      grid: { vertLines: { color: "#1f2937" }, horzLines: { color: "#1f2937" } },
      crosshair: { mode: CrosshairMode.Normal },
      rightPriceScale: { borderColor: "#374151" },
      timeScale: { borderColor: "#374151", timeVisible: true, secondsVisible: false },
      width: container.clientWidth,
      height,
    });

    // ── Candlestick ──────────────────────────────────────────────────────────
    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: "#22c55e",
      downColor: "#ef4444",
      borderUpColor: "#22c55e",
      borderDownColor: "#ef4444",
      wickUpColor: "#22c55e",
      wickDownColor: "#ef4444",
    });
    candleSeries.setData(
      candles.map((c) => ({
        time: c.time as any,
        open: c.open,
        high: c.high,
        low: c.low,
        close: c.close,
      }))
    );

    // ── Volume (always) ──────────────────────────────────────────────────────
    const volumeSeries = chart.addSeries(HistogramSeries, {
      priceFormat: { type: "volume" },
      priceScaleId: "volume",
    });
    chart.priceScale("volume").applyOptions({ scaleMargins: { top: 0.82, bottom: 0 } });
    volumeSeries.setData(
      candles.map((c) => ({
        time: c.time as any,
        value: c.volume,
        color: c.close >= c.open ? "rgba(34,197,94,0.35)" : "rgba(239,68,68,0.35)",
      }))
    );

    const closes = candles.map((c) => c.close);
    const lastTime = candles[candles.length - 1].time as any;

    // ── Classic mode: EMA + Bollinger Bands ───────────────────────────────────
    if (!smcMode) {
      for (const { period, color } of [
        { period: 9, color: "#f59e0b" },
        { period: 20, color: "#3b82f6" },
        { period: 50, color: "#a855f7" },
      ]) {
        const ema = calcEMA(closes, period);
        const s = chart.addSeries(LineSeries, {
          color, lineWidth: 1, priceLineVisible: false, lastValueVisible: false,
        });
        s.setData(
          candles
            .map((c, i) => ({ time: c.time as any, value: ema[i] }))
            .filter((d) => d.value != null) as any
        );
      }
      const bb = calcBB(closes, 20, 2);
      const bbStyle = { color: "rgba(100,116,139,0.55)", lineWidth: 1 as const, priceLineVisible: false, lastValueVisible: false };
      const bbU = chart.addSeries(LineSeries, bbStyle);
      const bbL = chart.addSeries(LineSeries, bbStyle);
      bbU.setData(candles.map((c, i) => ({ time: c.time as any, value: bb.upper[i] })).filter((d) => d.value != null) as any);
      bbL.setData(candles.map((c, i) => ({ time: c.time as any, value: bb.lower[i] })).filter((d) => d.value != null) as any);

    // ── SMC mode: blocks, areas, lines, markers ────────────────────────────
    } else if (smcData) {

      // ── Order Blocks: filled rectangles ────────────────────────────────────
      for (const ob of smcData.orderBlocks) {
        const isBull = ob.type === "bullish";
        const timeFrom = candles[ob.index]?.time as any ?? lastTime;

        if (!ob.mitigated) {
          // Active OB — solid fill + solid border
          (candleSeries as any).attachPrimitive(
            new BoxPrimitive({
              timeFrom,
              timeTo: lastTime,
              priceHigh: ob.high,
              priceLow: ob.low,
              fillColor: isBull ? "rgba(34,197,94,0.13)" : "rgba(239,68,68,0.13)",
              borderColor: isBull ? "#22c55e" : "#ef4444",
              lineWidth: 1,
              label: isBull ? "Bull OB" : "Bear OB",
            })
          );
        } else {
          // Mitigated OB — faded, dashed border
          (candleSeries as any).attachPrimitive(
            new BoxPrimitive({
              timeFrom,
              timeTo: lastTime,
              priceHigh: ob.high,
              priceLow: ob.low,
              fillColor: isBull ? "rgba(34,197,94,0.04)" : "rgba(239,68,68,0.04)",
              borderColor: isBull ? "rgba(34,197,94,0.35)" : "rgba(239,68,68,0.35)",
              lineWidth: 1,
              lineDash: [3, 3],
            })
          );
        }
      }

      // ── Fair Value Gaps: filled areas ────────────────────────────────────
      for (const fvg of smcData.fairValueGaps) {
        const isBull = fvg.type === "bullish";
        const timeFrom = candles[fvg.index]?.time as any ?? lastTime;
        (candleSeries as any).attachPrimitive(
          new BoxPrimitive({
            timeFrom,
            timeTo: lastTime,
            priceHigh: fvg.high,
            priceLow: fvg.low,
            fillColor: isBull ? "rgba(245,158,11,0.12)" : "rgba(168,85,247,0.12)",
            borderColor: isBull ? "rgba(245,158,11,0.7)" : "rgba(168,85,247,0.7)",
            lineWidth: 1,
            lineDash: [4, 3],
            label: isBull ? "FVG +" : "FVG -",
          })
        );
      }

      // ── BOS: horizontal line from the broken swing to right edge ────────
      if (smcData.lastBOS) {
        const swings =
          smcData.lastBOS.direction === "bullish"
            ? smcData.swingHighs
            : smcData.swingLows;
        const swing = swings.find(
          (s) => Math.abs(s.price - smcData.lastBOS!.price) < smcData.lastBOS!.price * 0.001
        );
        if (swing && swing.index < candles.length) {
          const isBull = smcData.lastBOS.direction === "bullish";
          (candleSeries as any).attachPrimitive(
            new HLinePrimitive({
              timeFrom: candles[swing.index].time as any,
              price: smcData.lastBOS.price,
              color: isBull ? "#22c55e" : "#ef4444",
              lineWidth: 1.5,
              lineDash: [6, 3],
              label: "BOS",
            })
          );
        }
      }

      // ── CHoCH: horizontal line, orange ───────────────────────────────────
      if (smcData.lastCHoCH) {
        const swings =
          smcData.lastCHoCH.direction === "bullish"
            ? smcData.swingHighs
            : smcData.swingLows;
        const swing = swings.find(
          (s) => Math.abs(s.price - smcData.lastCHoCH!.price) < smcData.lastCHoCH!.price * 0.001
        );
        if (swing && swing.index < candles.length) {
          (candleSeries as any).attachPrimitive(
            new HLinePrimitive({
              timeFrom: candles[swing.index].time as any,
              price: smcData.lastCHoCH.price,
              color: "#f97316",
              lineWidth: 1.5,
              lineDash: [6, 3],
              label: "CHoCH",
              labelColor: "#f97316",
            })
          );
        }
      }

      // ── Equilibrium: dashed center line ──────────────────────────────────
      candleSeries.createPriceLine({
        price: smcData.equilibrium,
        color: "rgba(245,158,11,0.5)",
        lineWidth: 1,
        lineStyle: LineStyle.LargeDashed,
        axisLabelVisible: true,
        title: "EQ 50%",
      });

      // ── BSL / SSL: dotted liquidity levels ───────────────────────────────
      for (const level of smcData.buySideLiquidity.slice(0, 3)) {
        candleSeries.createPriceLine({
          price: level,
          color: "rgba(239,68,68,0.5)",
          lineWidth: 1,
          lineStyle: LineStyle.Dotted,
          axisLabelVisible: true,
          title: "BSL",
        });
      }
      for (const level of smcData.sellSideLiquidity.slice(0, 3)) {
        candleSeries.createPriceLine({
          price: level,
          color: "rgba(34,197,94,0.5)",
          lineWidth: 1,
          lineStyle: LineStyle.Dotted,
          axisLabelVisible: true,
          title: "SSL",
        });
      }

      // ── Swing Highs / Lows: circle markers ───────────────────────────────
      const markers: {
        time: any;
        position: "aboveBar" | "belowBar";
        color: string;
        shape: "circle" | "arrowUp" | "arrowDown";
        size: number;
        text: string;
      }[] = [];

      for (const sh of smcData.swingHighs.slice(-12)) {
        if (sh.index < candles.length) {
          markers.push({
            time: candles[sh.index].time as any,
            position: "aboveBar",
            color: "rgba(239,68,68,0.75)",
            shape: "circle",
            size: 0.5,
            text: "",
          });
        }
      }
      for (const sl of smcData.swingLows.slice(-12)) {
        if (sl.index < candles.length) {
          markers.push({
            time: candles[sl.index].time as any,
            position: "belowBar",
            color: "rgba(34,197,94,0.75)",
            shape: "circle",
            size: 0.5,
            text: "",
          });
        }
      }

      // BOS arrow marker at the swing that was broken
      if (smcData.lastBOS) {
        const swings =
          smcData.lastBOS.direction === "bullish"
            ? smcData.swingHighs
            : smcData.swingLows;
        const swing = swings.find(
          (s) => Math.abs(s.price - smcData.lastBOS!.price) < smcData.lastBOS!.price * 0.001
        );
        if (swing && swing.index < candles.length) {
          markers.push({
            time: candles[swing.index].time as any,
            position: smcData.lastBOS.direction === "bullish" ? "aboveBar" : "belowBar",
            color: smcData.lastBOS.direction === "bullish" ? "#22c55e" : "#ef4444",
            shape: smcData.lastBOS.direction === "bullish" ? "arrowUp" : "arrowDown",
            size: 1.5,
            text: "BOS",
          });
        }
      }

      // CHoCH arrow marker
      if (smcData.lastCHoCH) {
        const swings =
          smcData.lastCHoCH.direction === "bullish"
            ? smcData.swingHighs
            : smcData.swingLows;
        const swing = swings.find(
          (s) => Math.abs(s.price - smcData.lastCHoCH!.price) < smcData.lastCHoCH!.price * 0.001
        );
        if (swing && swing.index < candles.length) {
          markers.push({
            time: candles[swing.index].time as any,
            position: smcData.lastCHoCH.direction === "bullish" ? "aboveBar" : "belowBar",
            color: "#f97316",
            shape: smcData.lastCHoCH.direction === "bullish" ? "arrowUp" : "arrowDown",
            size: 1.5,
            text: "CHoCH",
          });
        }
      }

      // Deduplicate and sort by time
      const seen = new Set<string>();
      const unique = markers.filter((m) => {
        const k = `${m.time}-${m.position}-${m.text}`;
        if (seen.has(k)) return false;
        seen.add(k);
        return true;
      });
      unique.sort((a, b) => a.time - b.time);
      createSeriesMarkers(candleSeries, unique);
    }

    const ro = new ResizeObserver(() =>
      chart.applyOptions({ width: container.clientWidth })
    );
    ro.observe(container);

    return () => {
      ro.disconnect();
      chart.remove();
    };
  }, [candles, height, smcMode, smcData]);

  return <div ref={containerRef} className="candle-chart-container" />;
}
