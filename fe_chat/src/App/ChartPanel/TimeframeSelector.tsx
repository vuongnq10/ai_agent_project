const TIMEFRAMES = ["1m", "5m", "15m", "1h", "4h", "1d"] as const;
export type Timeframe = typeof TIMEFRAMES[number];

interface Props {
  value: Timeframe;
  onChange: (tf: Timeframe) => void;
}

export default function TimeframeSelector({ value, onChange }: Props) {
  return (
    <div className="timeframe-selector">
      {TIMEFRAMES.map((tf) => (
        <button
          key={tf}
          className={`tf-btn ${value === tf ? "active" : ""}`}
          onClick={() => onChange(tf)}
        >
          {tf}
        </button>
      ))}
    </div>
  );
}
