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
import type { Candle } from "../types";
import type { SMCResult } from "../indicators";
import { calcEMA, calcBB } from "../indicators";
import { BoxPrimitive, HLinePrimitive } from "../smcDrawings";

interface Props {
  candles: Candle[];
  height?: number;
  smcMode?: boolean;
  smcData?: SMCResult | null;
  activeIndicators?: Set<string>;
}

export default function CandleChart({
  candles,
  height = 360,
  smcMode = false,
  smcData,
  activeIndicators = new Set(["ema9", "ema20", "ema50", "bb"]),
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
      upColor: "#089981",
      downColor: "#f23645",
      borderUpColor: "#089981",
      borderDownColor: "#f23645",
      wickUpColor: "#089981",
      wickDownColor: "#f23645",
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
        color: c.close >= c.open ? "rgba(8,153,129,0.35)" : "rgba(242,54,69,0.35)",
      }))
    );

    const closes = candles.map((c) => c.close);
    const lastTime = candles[candles.length - 1].time as any;

    // ── Overlay indicators: shown independently of SMC mode ──────────────────
    if (activeIndicators.has("ema9") || activeIndicators.has("ema20") || activeIndicators.has("ema50")) {
      for (const { id, period, color } of [
        { id: "ema9",  period: 9,  color: "#f59e0b" },
        { id: "ema20", period: 20, color: "#3b82f6" },
        { id: "ema50", period: 50, color: "#a855f7" },
      ]) {
        if (!activeIndicators.has(id)) continue;
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
    }

    if (activeIndicators.has("bb")) {
      const bb = calcBB(closes, 20, 2);
      const bbStyle = { color: "rgba(100,116,139,0.55)", lineWidth: 1 as const, priceLineVisible: false, lastValueVisible: false };
      const bbU = chart.addSeries(LineSeries, bbStyle);
      const bbL = chart.addSeries(LineSeries, bbStyle);
      bbU.setData(candles.map((c, i) => ({ time: c.time as any, value: bb.upper[i] })).filter((d) => d.value != null) as any);
      bbL.setData(candles.map((c, i) => ({ time: c.time as any, value: bb.lower[i] })).filter((d) => d.value != null) as any);
    }

    // ── SMC mode overlays ─────────────────────────────────────────────────────
    if (smcMode && smcData) {

      // ── Order Blocks: filled rectangles ────────────────────────────────────
      for (const ob of smcData.orderBlocks) {
        const isBull = ob.type === "bullish";
        const timeFrom = candles[ob.index]?.time as any ?? lastTime;

        if (!ob.mitigated) {
          (candleSeries as any).attachPrimitive(
            new BoxPrimitive({
              timeFrom,
              timeTo: lastTime,
              priceHigh: ob.high,
              priceLow: ob.low,
              fillColor: isBull ? "rgba(8,153,129,0.13)" : "rgba(242,54,69,0.13)",
              borderColor: isBull ? "#089981" : "#f23645",
              lineWidth: 1,
              label: isBull ? "Bull OB" : "Bear OB",
            })
          );
        } else {
          (candleSeries as any).attachPrimitive(
            new BoxPrimitive({
              timeFrom,
              timeTo: lastTime,
              priceHigh: ob.high,
              priceLow: ob.low,
              fillColor: isBull ? "rgba(8,153,129,0.04)" : "rgba(242,54,69,0.04)",
              borderColor: isBull ? "rgba(8,153,129,0.35)" : "rgba(242,54,69,0.35)",
              lineWidth: 1,
              lineDash: [3, 3],
            })
          );
        }
      }

      // ── Fair Value Gaps ──────────────────────────────────────────────────
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

      // ── BOS ──────────────────────────────────────────────────────────────
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
              color: isBull ? "#089981" : "#f23645",
              lineWidth: 1.5,
              lineDash: [6, 3],
              label: "BOS",
            })
          );
        }
      }

      // ── CHoCH ────────────────────────────────────────────────────────────
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

      // ── Equilibrium ──────────────────────────────────────────────────────
      candleSeries.createPriceLine({
        price: smcData.equilibrium,
        color: "rgba(245,158,11,0.5)",
        lineWidth: 1,
        lineStyle: LineStyle.LargeDashed,
        axisLabelVisible: true,
        title: "EQ 50%",
      });

      // ── BSL / SSL ────────────────────────────────────────────────────────
      for (const level of smcData.buySideLiquidity.slice(0, 3)) {
        candleSeries.createPriceLine({
          price: level,
          color: "rgba(242,54,69,0.5)",
          lineWidth: 1,
          lineStyle: LineStyle.Dotted,
          axisLabelVisible: true,
          title: "BSL",
        });
      }
      for (const level of smcData.sellSideLiquidity.slice(0, 3)) {
        candleSeries.createPriceLine({
          price: level,
          color: "rgba(8,153,129,0.5)",
          lineWidth: 1,
          lineStyle: LineStyle.Dotted,
          axisLabelVisible: true,
          title: "SSL",
        });
      }

      // ── Swing Markers ────────────────────────────────────────────────────
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
          markers.push({ time: candles[sh.index].time as any, position: "aboveBar", color: "rgba(242,54,69,0.75)", shape: "circle", size: 0.5, text: "" });
        }
      }
      for (const sl of smcData.swingLows.slice(-12)) {
        if (sl.index < candles.length) {
          markers.push({ time: candles[sl.index].time as any, position: "belowBar", color: "rgba(8,153,129,0.75)", shape: "circle", size: 0.5, text: "" });
        }
      }

      if (smcData.lastBOS) {
        const swings = smcData.lastBOS.direction === "bullish" ? smcData.swingHighs : smcData.swingLows;
        const swing = swings.find((s) => Math.abs(s.price - smcData.lastBOS!.price) < smcData.lastBOS!.price * 0.001);
        if (swing && swing.index < candles.length) {
          markers.push({
            time: candles[swing.index].time as any,
            position: smcData.lastBOS.direction === "bullish" ? "aboveBar" : "belowBar",
            color: smcData.lastBOS.direction === "bullish" ? "#089981" : "#f23645",
            shape: smcData.lastBOS.direction === "bullish" ? "arrowUp" : "arrowDown",
            size: 1.5, text: "BOS",
          });
        }
      }

      if (smcData.lastCHoCH) {
        const swings = smcData.lastCHoCH.direction === "bullish" ? smcData.swingHighs : smcData.swingLows;
        const swing = swings.find((s) => Math.abs(s.price - smcData.lastCHoCH!.price) < smcData.lastCHoCH!.price * 0.001);
        if (swing && swing.index < candles.length) {
          markers.push({
            time: candles[swing.index].time as any,
            position: smcData.lastCHoCH.direction === "bullish" ? "aboveBar" : "belowBar",
            color: "#f97316",
            shape: smcData.lastCHoCH.direction === "bullish" ? "arrowUp" : "arrowDown",
            size: 1.5, text: "CHoCH",
          });
        }
      }

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

    // ── Viewport High / Low labels pinned to candle ──────────────────────────
    container.style.position = "relative";

    const fmt = (p: number) =>
      p < 0.0001 ? p.toPrecision(4)
      : p < 0.01  ? p.toFixed(6)
      : p < 1     ? p.toFixed(4)
      : p < 100   ? p.toFixed(3)
      : p < 10000 ? p.toFixed(2)
      : p.toFixed(1);

    const mkLabel = (isHigh: boolean) => {
      const el = document.createElement("div");
      el.style.cssText = [
        "position:absolute",
        `background:${isHigh ? "rgba(8,153,129,0.15)" : "rgba(242,54,69,0.15)"}`,
        `border:1px solid ${isHigh ? "rgba(8,153,129,0.7)" : "rgba(242,54,69,0.7)"}`,
        `color:${isHigh ? "#0ecaa8" : "#f56e7a"}`,
        "font-size:10px",
        "font-family:monospace",
        "padding:1px 5px",
        "border-radius:3px",
        "white-space:nowrap",
        "pointer-events:none",
        "display:none",
        "z-index:10",
        "line-height:16px",
        "transform:translateX(-50%)",
      ].join(";");
      container.appendChild(el);
      return el;
    };

    const highLabel = mkLabel(true);
    const lowLabel  = mkLabel(false);

    // Clamp label so it doesn't overflow left/right edges of the chart area
    const clampX = (x: number, labelW: number, chartW: number) =>
      Math.min(Math.max(x, labelW / 2 + 4), chartW - labelW / 2 - 70);

    const updateHL = () => {
      const range = chart.timeScale().getVisibleLogicalRange();
      if (!range) return;
      const from = Math.max(0, Math.floor(range.from));
      const to   = Math.min(candles.length - 1, Math.ceil(range.to));
      if (from > to) return;

      let maxH = -Infinity, minL = Infinity;
      let maxIdx = from, minIdx = from;
      for (let i = from; i <= to; i++) {
        if (candles[i].high > maxH) { maxH = candles[i].high; maxIdx = i; }
        if (candles[i].low  < minL) { minL = candles[i].low;  minIdx = i; }
      }

      const highY = candleSeries.priceToCoordinate(maxH);
      const lowY  = candleSeries.priceToCoordinate(minL);
      const highX = chart.timeScale().timeToCoordinate(candles[maxIdx].time as any);
      const lowX  = chart.timeScale().timeToCoordinate(candles[minIdx].time as any);
      const chartW = container.clientWidth;
      const LABEL_H = 18;

      if (highY != null && highX != null) {
        const top = Math.max(0, highY - LABEL_H - 4);
        highLabel.textContent = `▲ ${fmt(maxH)}`;
        highLabel.style.top     = `${top}px`;
        highLabel.style.left    = `${clampX(highX, highLabel.offsetWidth || 80, chartW)}px`;
        highLabel.style.display = "block";
      } else {
        highLabel.style.display = "none";
      }

      if (lowY != null && lowX != null) {
        const top = lowY + 4;
        lowLabel.textContent = `▼ ${fmt(minL)}`;
        lowLabel.style.top     = `${top}px`;
        lowLabel.style.left    = `${clampX(lowX, lowLabel.offsetWidth || 80, chartW)}px`;
        lowLabel.style.display = "block";
      } else {
        lowLabel.style.display = "none";
      }
    };

    chart.timeScale().subscribeVisibleLogicalRangeChange(updateHL);
    updateHL();

    const ro = new ResizeObserver(() => {
      chart.applyOptions({ width: container.clientWidth });
      updateHL();
    });
    ro.observe(container);

    return () => {
      ro.disconnect();
      chart.remove();
      highLabel.remove();
      lowLabel.remove();
    };
  }, [candles, height, smcMode, smcData, activeIndicators]);

  return <div ref={containerRef} className="candle-chart-container" />;
}
