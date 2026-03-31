import { TIMEFRAMES, type Timeframe } from "../../../constants";
export type { Timeframe };

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
