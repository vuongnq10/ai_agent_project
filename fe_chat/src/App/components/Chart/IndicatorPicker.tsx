import { useRef, useState, useEffect } from "react";

export type IndicatorId = "ema9" | "ema20" | "ema50" | "bb" | "rsi";

interface IndicatorDef {
  id: IndicatorId;
  label: string;
  color: string;
  group: "overlay" | "panel";
}

export const INDICATORS: IndicatorDef[] = [
  { id: "ema9",  label: "EMA 9",     color: "#f59e0b", group: "overlay" },
  { id: "ema20", label: "EMA 20",    color: "#3b82f6", group: "overlay" },
  { id: "ema50", label: "EMA 50",    color: "#a855f7", group: "overlay" },
  { id: "bb",    label: "BB (20,2)", color: "#64748b", group: "overlay" },
  { id: "rsi",   label: "RSI (14)",  color: "#f59e0b", group: "panel"   },
];

interface Props {
  active: Set<IndicatorId>;
  onChange: (id: IndicatorId, checked: boolean) => void;
}

export default function IndicatorPicker({ active, onChange }: Props) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  const overlays = INDICATORS.filter((i) => i.group === "overlay");
  const panels   = INDICATORS.filter((i) => i.group === "panel");

  return (
    <div className="ind-picker" ref={ref}>
      <button className="btn btn-ghost btn-icon" onClick={() => setOpen((o) => !o)}>
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
        </svg>
        Indicators
        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ opacity: 0.6 }}>
          <polyline points={open ? "18 15 12 9 6 15" : "6 9 12 15 18 9"} />
        </svg>
      </button>

      {open && (
        <div className="ind-picker-dropdown">
          <div className="ind-group-label">Overlay</div>
          {overlays.map((ind) => (
            <label key={ind.id} className="ind-row">
              <input
                type="checkbox"
                checked={active.has(ind.id)}
                onChange={(e) => onChange(ind.id, e.target.checked)}
              />
              <span className="ind-dot" style={{ background: ind.color }} />
              <span className="ind-name">{ind.label}</span>
            </label>
          ))}
          <div style={{ height: 1, background: "var(--border-subtle)", margin: "6px 0" }} />
          <div className="ind-group-label">Panel</div>
          {panels.map((ind) => (
            <label key={ind.id} className="ind-row">
              <input
                type="checkbox"
                checked={active.has(ind.id)}
                onChange={(e) => onChange(ind.id, e.target.checked)}
              />
              <span className="ind-dot" style={{ background: ind.color }} />
              <span className="ind-name">{ind.label}</span>
            </label>
          ))}
        </div>
      )}
    </div>
  );
}
