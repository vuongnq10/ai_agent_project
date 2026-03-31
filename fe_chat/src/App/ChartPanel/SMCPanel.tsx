import { useMemo } from "react";
import type { Candle } from "../types";
import { calcSMC } from "../indicators";

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

export default function SMCPanel({ candles }: Props) {
  const smc = useMemo(() => calcSMC(candles), [candles]);

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

  // mitigation is now close-based → stricter → more OBs stay active, show 3
  const activeBullOBs = smc.orderBlocks.filter((o) => o.type === "bullish" && !o.mitigated).slice(-3);
  const activeBearOBs = smc.orderBlocks.filter((o) => o.type === "bearish" && !o.mitigated).slice(-3);
  const mitigatedOBs  = smc.orderBlocks.filter((o) => o.mitigated).slice(-3);

  // fill is now close-based → calcSMC already filtered out filled FVGs
  const bullFVGs = smc.fairValueGaps.filter((f) => f.type === "bullish").slice(-3);
  const bearFVGs = smc.fairValueGaps.filter((f) => f.type === "bearish").slice(-3);

  // liquidity: split into above / below current price for clear context
  const bslAbove = smc.buySideLiquidity.filter((p) => p > currentPrice);
  const sslBelow = smc.sellSideLiquidity.filter((p) => p < currentPrice);

  return (
    <div className="smc-panel">
      <div className="smc-panel-title">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
        </svg>
        Smart Money Concepts
      </div>

      <div className="smc-cards">
        {/* ── Market Structure ─────────────────────────────── */}
        <div className="smc-card">
          <div className="smc-card-header">Market Structure</div>
          <div className="smc-card-body">
            <div className="smc-row">
              <span className="smc-label">Trend</span>
              <span className="smc-badge" style={{ color: trendColor, borderColor: trendColor }}>
                {trendArrow} {smc.trend.toUpperCase()}
              </span>
            </div>
            <div className="smc-row">
              <span className="smc-label">Last BOS</span>
              {smc.lastBOS ? (
                <span
                  className="smc-value"
                  style={{ color: smc.lastBOS.direction === "bullish" ? "#089981" : "#f23645" }}
                  title={`Broke level: ${fmt(smc.lastBOS.price)}`}
                >
                  {smc.lastBOS.direction === "bullish" ? "↑" : "↓"} {fmt(smc.lastBOS.price)}
                </span>
              ) : (
                <span className="smc-value smc-none">—</span>
              )}
            </div>
            <div className="smc-row">
              <span className="smc-label">CHoCH</span>
              {smc.lastCHoCH ? (
                <span
                  className="smc-value smc-choch"
                  style={{ color: smc.lastCHoCH.direction === "bullish" ? "#089981" : "#f23645" }}
                  title={`Reversal level: ${fmt(smc.lastCHoCH.price)}`}
                >
                  {smc.lastCHoCH.direction === "bullish" ? "↑" : "↓"} {fmt(smc.lastCHoCH.price)}
                </span>
              ) : (
                <span className="smc-value smc-none">—</span>
              )}
            </div>
            <div className="smc-row">
              <span className="smc-label">Price</span>
              <span className="smc-value">{fmt(currentPrice)}</span>
            </div>
          </div>
        </div>

        {/* ── Order Blocks ──────────────────────────────────── */}
        <div className="smc-card">
          <div className="smc-card-header">
            Order Blocks
            {activeBullOBs.length + activeBearOBs.length > 0 && (
              <span style={{ marginLeft: "0.4rem", color: "#f59e0b" }}>
                {activeBullOBs.length + activeBearOBs.length} active
              </span>
            )}
          </div>
          <div className="smc-card-body">
            {activeBullOBs.length === 0 && activeBearOBs.length === 0 ? (
              <span className="smc-value smc-none">No active OBs</span>
            ) : null}
            {activeBullOBs.map((ob, i) => (
              <div key={`b${i}`} className="smc-row">
                <span className="smc-ob-tag bull">Bull OB</span>
                <span className="smc-value" style={{ color: "#089981" }}>
                  {fmt(ob.low)} – {fmt(ob.high)}
                </span>
                <span className="smc-label" style={{ fontSize: "0.55rem" }}>
                  {distPct(ob.high, currentPrice)} away
                </span>
              </div>
            ))}
            {activeBearOBs.map((ob, i) => (
              <div key={`s${i}`} className="smc-row">
                <span className="smc-ob-tag bear">Bear OB</span>
                <span className="smc-value" style={{ color: "#f23645" }}>
                  {fmt(ob.low)} – {fmt(ob.high)}
                </span>
                <span className="smc-label" style={{ fontSize: "0.55rem" }}>
                  {distPct(ob.low, currentPrice)} away
                </span>
              </div>
            ))}
            {mitigatedOBs.length > 0 && (
              <>
                <div style={{ borderTop: "1px solid #21262d", margin: "0.2rem 0" }} />
                {mitigatedOBs.map((ob, i) => (
                  <div key={`m${i}`} className="smc-row smc-mitigated">
                    <span className="smc-ob-tag mitigated">{ob.type === "bullish" ? "Bull" : "Bear"}</span>
                    <span className="smc-value">{fmt(ob.low)} – {fmt(ob.high)}</span>
                  </div>
                ))}
              </>
            )}
          </div>
        </div>

        {/* ── Fair Value Gaps ───────────────────────────────── */}
        <div className="smc-card">
          <div className="smc-card-header">
            Fair Value Gaps
            {bullFVGs.length + bearFVGs.length > 0 && (
              <span style={{ marginLeft: "0.4rem", color: "#f59e0b" }}>
                {bullFVGs.length + bearFVGs.length} open
              </span>
            )}
          </div>
          <div className="smc-card-body">
            {bullFVGs.length === 0 && bearFVGs.length === 0 ? (
              <span className="smc-value smc-none">No open FVGs</span>
            ) : null}
            {bullFVGs.map((fvg, i) => (
              <div key={`bf${i}`} className="smc-row">
                <span className="smc-fvg-tag bull">↑ FVG</span>
                <span className="smc-value" style={{ color: "#089981" }}>
                  {fmt(fvg.low)} – {fmt(fvg.high)}
                </span>
                <span className="smc-label" style={{ fontSize: "0.55rem" }}>
                  {gapSizePct(fvg.high, fvg.low, currentPrice)}
                </span>
              </div>
            ))}
            {bearFVGs.map((fvg, i) => (
              <div key={`sf${i}`} className="smc-row">
                <span className="smc-fvg-tag bear">↓ FVG</span>
                <span className="smc-value" style={{ color: "#f23645" }}>
                  {fmt(fvg.low)} – {fmt(fvg.high)}
                </span>
                <span className="smc-label" style={{ fontSize: "0.55rem" }}>
                  {gapSizePct(fvg.high, fvg.low, currentPrice)}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* ── Premium / Discount ────────────────────────────── */}
        <div className="smc-card">
          <div className="smc-card-header">Premium / Discount</div>
          <div className="smc-card-body">
            <div className="smc-row">
              <span className="smc-label">Zone</span>
              <span className="smc-badge" style={{ color: pdColor, borderColor: pdColor }}>
                {smc.premiumDiscountZone.toUpperCase()}
              </span>
            </div>
            <div className="smc-pd-gauge">
              <div className="smc-pd-track">
                <div
                  className="smc-pd-fill"
                  style={{ width: `${Math.min(100, Math.max(0, smc.premiumDiscountPct))}%`, background: pdColor }}
                />
                <div className="smc-pd-eq-mark" />
              </div>
              <div className="smc-pd-labels">
                <span>Discount</span>
                <span>EQ</span>
                <span>Premium</span>
              </div>
            </div>
            <div className="smc-row">
              <span className="smc-label">Range High</span>
              <span className="smc-value" style={{ color: "#f23645" }}>{fmt(smc.rangeHigh)}</span>
            </div>
            <div className="smc-row">
              <span className="smc-label">Equilibrium</span>
              <span className="smc-value" style={{ color: "#f59e0b" }}>{fmt(smc.equilibrium)}</span>
            </div>
            <div className="smc-row">
              <span className="smc-label">Range Low</span>
              <span className="smc-value" style={{ color: "#089981" }}>{fmt(smc.rangeLow)}</span>
            </div>
            <div className="smc-row">
              <span className="smc-label">Position</span>
              <span className="smc-value" style={{ color: pdColor }}>
                {smc.premiumDiscountPct.toFixed(1)}%
              </span>
            </div>
          </div>
        </div>

        {/* ── Liquidity ─────────────────────────────────────── */}
        <div className="smc-card smc-card-wide">
          <div className="smc-card-header">Liquidity Pools</div>
          <div className="smc-liq-grid">
            {/* Buy-side: resting above current price (short sellers' stops) */}
            <div className="smc-liq-section">
              <span className="smc-liq-label bear">
                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <polyline points="18 8 12 2 6 8" />
                </svg>
                BSL — above {fmt(currentPrice)}
              </span>
              <div className="smc-liq-levels">
                {bslAbove.length === 0 ? (
                  <span className="smc-none">—</span>
                ) : (
                  bslAbove.map((p, i) => (
                    <span key={i} className="smc-liq-level bear-liq">
                      {fmt(p)}
                      <span style={{ fontSize: "0.5rem", opacity: 0.6 }}>+{distPct(p, currentPrice)}</span>
                    </span>
                  ))
                )}
              </div>
            </div>
            {/* Sell-side: resting below current price (long traders' stops) */}
            <div className="smc-liq-section">
              <span className="smc-liq-label bull">
                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <polyline points="6 16 12 22 18 16" />
                </svg>
                SSL — below {fmt(currentPrice)}
              </span>
              <div className="smc-liq-levels">
                {sslBelow.length === 0 ? (
                  <span className="smc-none">—</span>
                ) : (
                  sslBelow.map((p, i) => (
                    <span key={i} className="smc-liq-level bull-liq">
                      {fmt(p)}
                      <span style={{ fontSize: "0.5rem", opacity: 0.6 }}>-{distPct(p, currentPrice)}</span>
                    </span>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
