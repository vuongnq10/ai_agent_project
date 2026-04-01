import { useMemo } from "react";
import type { Candle } from "../../types";
import { calcSMC, calcATR, calcRSI, calcEMA, calcBB } from "../../indicators";

interface Props {
  candles: Candle[];
}

function fmt(n: number): string {
  if (n >= 10000) return n.toLocaleString(undefined, { maximumFractionDigits: 1 });
  if (n >= 100) return n.toFixed(2);
  return n.toFixed(4);
}

function distPct(price: number, ref: number): string {
  if (ref === 0) return "—";
  return (Math.abs((price - ref) / ref) * 100).toFixed(2) + "%";
}

function gapSizePct(high: number, low: number, ref: number): string {
  if (ref === 0) return "—";
  return ((high - low) / ref * 100).toFixed(2) + "%";
}

function rsiColor(v: number): string {
  if (v >= 70) return "#f23645";
  if (v <= 30) return "#089981";
  return "#9ca3af";
}

function emaColor(ema: number, price: number): string {
  return price > ema ? "#089981" : "#f23645";
}

export default function SMCPanel({ candles }: Props) {
  const smc = useMemo(() => calcSMC(candles), [candles]);
  const closes = useMemo(() => candles.map((c) => c.close), [candles]);

  const atr = useMemo(() => calcATR(candles, 14), [candles]);

  const rsi7 = useMemo(() => { const v = calcRSI(closes, 7); return v[v.length - 1] ?? null; }, [closes]);
  const rsi14 = useMemo(() => { const v = calcRSI(closes, 14); return v[v.length - 1] ?? null; }, [closes]);
  const rsi21 = useMemo(() => { const v = calcRSI(closes, 21); return v[v.length - 1] ?? null; }, [closes]);

  const ema9 = useMemo(() => { const v = calcEMA(closes, 9); return v[v.length - 1] ?? null; }, [closes]);
  const ema20 = useMemo(() => { const v = calcEMA(closes, 20); return v[v.length - 1] ?? null; }, [closes]);
  const ema50 = useMemo(() => { const v = calcEMA(closes, 50); return v[v.length - 1] ?? null; }, [closes]);

  const bb = useMemo(() => {
    const { upper, middle, lower } = calcBB(closes, 20, 2);
    return {
      upper: upper[upper.length - 1] ?? null,
      middle: middle[middle.length - 1] ?? null,
      lower: lower[lower.length - 1] ?? null,
    };
  }, [closes]);

  if (candles.length === 0) return null;

  const currentPrice = candles[candles.length - 1]?.close ?? 0;

  const trendColor =
    smc.trend === "bullish" ? "#089981" : smc.trend === "bearish" ? "#f23645" : "#f59e0b";
  const trendArrow =
    smc.trend === "bullish" ? "↑" : smc.trend === "bearish" ? "↓" : "→";

  const pdColor =
    smc.premiumDiscountZone === "premium"
      ? "#f23645"
      : smc.premiumDiscountZone === "discount"
      ? "#089981"
      : "#f59e0b";

  const activeBullOBs = smc.orderBlocks.filter((o) => o.type === "bullish" && !o.mitigated).slice(-2);
  const activeBearOBs = smc.orderBlocks.filter((o) => o.type === "bearish" && !o.mitigated).slice(-2);

  const topEntries = smc.potentialEntries.slice(0, 3);

  const bullFVGs = smc.fairValueGaps.filter((f) => f.type === "bullish").slice(-2);
  const bearFVGs = smc.fairValueGaps.filter((f) => f.type === "bearish").slice(-2);

  const bslAbove = smc.buySideLiquidity.filter((p) => p > currentPrice).slice(0, 3);
  const sslBelow = smc.sellSideLiquidity.filter((p) => p < currentPrice).slice(0, 3);

  const bbPctB =
    bb.upper != null && bb.lower != null && bb.upper !== bb.lower
      ? ((currentPrice - bb.lower) / (bb.upper - bb.lower)) * 100
      : null;

  const rsiValues: [number, number | null][] = [[7, rsi7], [14, rsi14], [21, rsi21]];
  const emaValues: [number, number | null][] = [[9, ema9], [20, ema20], [50, ema50]];

  return (
    <div className="smc-strip">

      {/* ── Market Structure ───────────────── */}
      <div className="smc-section">
        <div className="smc-sec-title">Structure</div>
        <div className="smc-stat-row">
          <span className="smc-stat-label">Trend</span>
          <span className="smc-strip-badge" style={{ color: trendColor, background: `${trendColor}18` }}>
            {trendArrow} {smc.trend.toUpperCase()}
          </span>
        </div>
        <div className="smc-stat-row">
          <span className="smc-stat-label">BOS</span>
          {smc.lastBOS ? (
            <span className="smc-stat-val" style={{ color: smc.lastBOS.direction === "bullish" ? "#089981" : "#f23645" }}>
              {smc.lastBOS.direction === "bullish" ? "↑" : "↓"} {fmt(smc.lastBOS.price)}
            </span>
          ) : <span className="smc-stat-val smc-none">—</span>}
        </div>
        <div className="smc-stat-row">
          <span className="smc-stat-label">CHoCH</span>
          {smc.lastCHoCH ? (
            <span className="smc-stat-val" style={{ color: smc.lastCHoCH.direction === "bullish" ? "#089981" : "#f23645" }}>
              {smc.lastCHoCH.direction === "bullish" ? "↑" : "↓"} {fmt(smc.lastCHoCH.price)}
            </span>
          ) : <span className="smc-stat-val smc-none">—</span>}
        </div>
        <div className="smc-stat-row">
          <span className="smc-stat-label">ATR (14)</span>
          <span className="smc-stat-val" style={{ color: "#f59e0b" }}>{atr > 0 ? fmt(atr) : "—"}</span>
        </div>
        <div className="smc-stat-row">
          <span className="smc-stat-label">Swings H/L</span>
          <span className="smc-stat-val">{smc.swingHighs.length} / {smc.swingLows.length}</span>
        </div>
      </div>

      <div className="smc-vsep" />

      {/* ── Order Blocks ───────────────────── */}
      <div className="smc-section" style={{ minWidth: 200 }}>
        <div className="smc-sec-title">
          Order Blocks
          {activeBullOBs.length + activeBearOBs.length > 0 && (
            <span style={{ color: "#f59e0b", marginLeft: 5 }}>
              {activeBullOBs.length + activeBearOBs.length} active
            </span>
          )}
        </div>
        {activeBullOBs.length === 0 && activeBearOBs.length === 0 && (
          <span className="smc-stat-val smc-none">No active OBs</span>
        )}
        {activeBullOBs.map((ob, i) => (
          <div key={`b${i}`} className="smc-stat-row">
            <span className="smc-ob-tag bull">Bull</span>
            <span className="smc-stat-val" style={{ color: "#089981" }}>{fmt(ob.low)} – {fmt(ob.high)}</span>
            <span className="smc-dist">+{distPct(ob.high, currentPrice)}</span>
            <span className="smc-strength-badge" style={{ background: `hsl(${ob.strength}, 70%, 35%)` }}>{ob.strength}%</span>
          </div>
        ))}
        {activeBearOBs.map((ob, i) => (
          <div key={`s${i}`} className="smc-stat-row">
            <span className="smc-ob-tag bear">Bear</span>
            <span className="smc-stat-val" style={{ color: "#f23645" }}>{fmt(ob.low)} – {fmt(ob.high)}</span>
            <span className="smc-dist">-{distPct(ob.low, currentPrice)}</span>
            <span className="smc-strength-badge" style={{ background: `hsl(${ob.strength}, 70%, 35%)` }}>{ob.strength}%</span>
          </div>
        ))}
      </div>

      <div className="smc-vsep" />

      {/* ── Fair Value Gaps ────────────────── */}
      <div className="smc-section" style={{ minWidth: 200 }}>
        <div className="smc-sec-title">
          Fair Value Gaps
          {bullFVGs.length + bearFVGs.length > 0 && (
            <span style={{ color: "#f59e0b", marginLeft: 5 }}>
              {bullFVGs.length + bearFVGs.length} open
            </span>
          )}
        </div>
        {bullFVGs.length === 0 && bearFVGs.length === 0 && (
          <span className="smc-stat-val smc-none">No open FVGs</span>
        )}
        {bullFVGs.map((fvg, i) => (
          <div key={`bf${i}`} className="smc-stat-row">
            <span className="smc-fvg-tag bull">↑ FVG</span>
            <span className="smc-stat-val" style={{ color: "#089981" }}>{fmt(fvg.low)} – {fmt(fvg.high)}</span>
            <span className="smc-dist">{gapSizePct(fvg.high, fvg.low, currentPrice)}</span>
            <span className="smc-strength-badge" style={{ background: `hsl(${fvg.strength}, 70%, 35%)` }}>{fvg.strength}%</span>
          </div>
        ))}
        {bearFVGs.map((fvg, i) => (
          <div key={`sf${i}`} className="smc-stat-row">
            <span className="smc-fvg-tag bear">↓ FVG</span>
            <span className="smc-stat-val" style={{ color: "#f23645" }}>{fmt(fvg.low)} – {fmt(fvg.high)}</span>
            <span className="smc-dist">{gapSizePct(fvg.high, fvg.low, currentPrice)}</span>
            <span className="smc-strength-badge" style={{ background: `hsl(${fvg.strength}, 70%, 35%)` }}>{fvg.strength}%</span>
          </div>
        ))}
      </div>

      <div className="smc-vsep" />

      {/* ── Potential Entries ──────────────── */}
      <div className="smc-section" style={{ minWidth: 220 }}>
        <div className="smc-sec-title">
          Potential Entries
          {topEntries.length > 0 && (
            <span style={{ color: "#f59e0b", marginLeft: 5 }}>{topEntries.length} signal{topEntries.length > 1 ? "s" : ""}</span>
          )}
        </div>
        {topEntries.length === 0 && (
          <span className="smc-stat-val smc-none">No confluence found</span>
        )}
        {topEntries.map((e, i) => (
          <div key={i} className="smc-entry-row">
            <span
              className="smc-ob-tag"
              style={{
                color: e.type === "bullish" ? "#089981" : "#f23645",
                background: e.type === "bullish" ? "#08998118" : "#f2364518",
                border: `1px solid ${e.type === "bullish" ? "#089981" : "#f23645"}`,
              }}
            >
              {e.type === "bullish" ? "↑ LONG" : "↓ SHORT"}
            </span>
            <span className="smc-stat-val" style={{ color: e.type === "bullish" ? "#089981" : "#f23645" }}>
              {fmt(e.zoneLow)} – {fmt(e.zoneHigh)}
            </span>
            <span className="smc-dist">{e.distancePct.toFixed(2)}%</span>
            <span
              className="smc-confluence-badge"
              style={{
                background: e.confluenceScore >= 70 ? "#f59e0b22" : "#ffffff10",
                border: `1px solid ${e.confluenceScore >= 70 ? "#f59e0b" : "#4b5563"}`,
                color: e.confluenceScore >= 70 ? "#f59e0b" : "#9ca3af",
              }}
            >
              {e.confluenceScore}%
            </span>
          </div>
        ))}
      </div>

      <div className="smc-vsep" />

      {/* ── Premium / Discount ─────────────── */}
      <div className="smc-section" style={{ minWidth: 165 }}>
        <div className="smc-sec-title">Premium / Discount</div>
        <div className="smc-stat-row">
          <span className="smc-stat-label">Zone</span>
          <span className="smc-strip-badge" style={{ color: pdColor, background: `${pdColor}18` }}>
            {smc.premiumDiscountZone.toUpperCase()}
          </span>
        </div>
        <div className="smc-mini-gauge">
          <div className="smc-mini-gauge-fill" style={{ width: `${Math.min(100, Math.max(0, smc.premiumDiscountPct))}%`, background: pdColor }} />
        </div>
        <div className="smc-stat-row">
          <span className="smc-stat-label">Pos</span>
          <span className="smc-stat-val" style={{ color: pdColor }}>{smc.premiumDiscountPct.toFixed(1)}%</span>
        </div>
        <div className="smc-stat-row">
          <span className="smc-stat-label">EQ</span>
          <span className="smc-stat-val" style={{ color: "#f59e0b" }}>{fmt(smc.equilibrium)}</span>
        </div>
        <div className="smc-stat-row">
          <span className="smc-stat-label">High</span>
          <span className="smc-stat-val" style={{ color: "#f23645" }}>{fmt(smc.rangeHigh)}</span>
        </div>
        <div className="smc-stat-row">
          <span className="smc-stat-label">Low</span>
          <span className="smc-stat-val" style={{ color: "#089981" }}>{fmt(smc.rangeLow)}</span>
        </div>
      </div>

      <div className="smc-vsep" />

      {/* ── Liquidity ──────────────────────── */}
      <div className="smc-section smc-liq-section">
        <div className="smc-sec-title">Liquidity Pools</div>
        <div className="smc-liq-cols">
          <div className="smc-liq-col">
            <div className="smc-liq-col-label" style={{ color: "#f23645" }}>↑ BSL above</div>
            {bslAbove.length === 0 ? (
              <span className="smc-stat-val smc-none">—</span>
            ) : bslAbove.map((p, i) => (
              <div key={i} className="smc-stat-row">
                <span className="smc-liq-level bear-liq">{fmt(p)}</span>
                <span className="smc-dist">+{distPct(p, currentPrice)}</span>
              </div>
            ))}
          </div>
          <div className="smc-liq-col">
            <div className="smc-liq-col-label" style={{ color: "#089981" }}>↓ SSL below</div>
            {sslBelow.length === 0 ? (
              <span className="smc-stat-val smc-none">—</span>
            ) : sslBelow.map((p, i) => (
              <div key={i} className="smc-stat-row">
                <span className="smc-liq-level bull-liq">{fmt(p)}</span>
                <span className="smc-dist">-{distPct(p, currentPrice)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="smc-vsep" />

      {/* ── RSI ────────────────────────────── */}
      <div className="smc-section" style={{ minWidth: 130 }}>
        <div className="smc-sec-title">RSI</div>
        {rsiValues.map(([period, val]) => (
          <div key={period} className="smc-stat-row">
            <span className="smc-stat-label">RSI {period}</span>
            {val != null ? (
              <span className="smc-stat-val" style={{ color: rsiColor(val) }}>
                {val.toFixed(1)}
                {val >= 70 ? " ▲OB" : val <= 30 ? " ▼OS" : ""}
              </span>
            ) : <span className="smc-stat-val smc-none">—</span>}
          </div>
        ))}
        {rsi14 != null && (
          <>
            <div className="smc-mini-gauge" style={{ marginTop: 2 }}>
              <div
                className="smc-mini-gauge-fill"
                style={{
                  width: `${Math.min(100, Math.max(0, rsi14))}%`,
                  background: rsiColor(rsi14),
                }}
              />
            </div>
          </>
        )}
      </div>

      <div className="smc-vsep" />

      {/* ── EMA ────────────────────────────── */}
      <div className="smc-section" style={{ minWidth: 155 }}>
        <div className="smc-sec-title">EMA</div>
        {emaValues.map(([period, val]) => (
          <div key={period} className="smc-stat-row">
            <span className="smc-stat-label">EMA {period}</span>
            {val != null ? (
              <span className="smc-stat-val" style={{ color: emaColor(val, currentPrice) }}>
                {fmt(val)}
              </span>
            ) : <span className="smc-stat-val smc-none">—</span>}
          </div>
        ))}
        <div className="smc-stat-row" style={{ marginTop: 2 }}>
          <span className="smc-stat-label">Stack</span>
          {ema9 != null && ema20 != null && ema50 != null ? (
            <span className="smc-stat-val" style={{
              color: ema9 > ema20 && ema20 > ema50 ? "#089981"
                : ema9 < ema20 && ema20 < ema50 ? "#f23645"
                : "#f59e0b"
            }}>
              {ema9 > ema20 && ema20 > ema50 ? "↑ Bull"
                : ema9 < ema20 && ema20 < ema50 ? "↓ Bear"
                : "Mixed"}
            </span>
          ) : <span className="smc-stat-val smc-none">—</span>}
        </div>
      </div>

      <div className="smc-vsep" />

      {/* ── Bollinger Bands ────────────────── */}
      <div className="smc-section" style={{ minWidth: 155 }}>
        <div className="smc-sec-title">
          BB (20,2)
          {bbPctB != null && (
            <span style={{
              color: bbPctB > 80 ? "#f23645" : bbPctB < 20 ? "#089981" : "#f59e0b",
              marginLeft: 5,
            }}>
              {bbPctB.toFixed(0)}%B
            </span>
          )}
        </div>
        <div className="smc-stat-row">
          <span className="smc-stat-label">Upper</span>
          {bb.upper != null
            ? <span className="smc-stat-val" style={{ color: "#f23645" }}>{fmt(bb.upper)}</span>
            : <span className="smc-stat-val smc-none">—</span>}
        </div>
        <div className="smc-stat-row">
          <span className="smc-stat-label">Middle</span>
          {bb.middle != null
            ? <span className="smc-stat-val" style={{ color: "#f59e0b" }}>{fmt(bb.middle)}</span>
            : <span className="smc-stat-val smc-none">—</span>}
        </div>
        <div className="smc-stat-row">
          <span className="smc-stat-label">Lower</span>
          {bb.lower != null
            ? <span className="smc-stat-val" style={{ color: "#089981" }}>{fmt(bb.lower)}</span>
            : <span className="smc-stat-val smc-none">—</span>}
        </div>
        {bb.upper != null && bb.lower != null && (
          <div className="smc-stat-row">
            <span className="smc-stat-label">Width</span>
            <span className="smc-stat-val" style={{ color: "#9ca3af" }}>
              {gapSizePct(bb.upper, bb.lower, currentPrice)}
            </span>
          </div>
        )}
        {bbPctB != null && (
          <div className="smc-mini-gauge" style={{ marginTop: 2 }}>
            <div
              className="smc-mini-gauge-fill"
              style={{
                width: `${Math.min(100, Math.max(0, bbPctB))}%`,
                background: bbPctB > 80 ? "#f23645" : bbPctB < 20 ? "#089981" : "#f59e0b",
              }}
            />
          </div>
        )}
      </div>

    </div>
  );
}
