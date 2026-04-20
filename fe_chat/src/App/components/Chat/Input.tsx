import { useState } from "react";
import { buildSmcQuery } from "../../../services/smcQueryService";

interface ChatInputProps {
  message: string;
  loading: boolean;
  selectedCoin: string;
  onChange: (value: string) => void;
  onSubmit: (e: React.FormEvent, query?: string) => void;
}

export default function Input({ message, loading, selectedCoin, onChange, onSubmit }: ChatInputProps) {
  const [fetching, setFetching] = useState(false);

  const handleQuickSmc = async (e: React.MouseEvent) => {
    e.preventDefault();
    setFetching(true);
    try {
      const query = await buildSmcQuery(selectedCoin, message);
      const fakeEvent = { preventDefault: () => { } } as React.FormEvent;
      onSubmit(fakeEvent, query);
      onChange("");
    } finally {
      setFetching(false);
    }
  };

  const busy = loading || fetching;

  return (
    <div className="chat-input-container">
      <button
        className="quick-smc-button"
        onClick={handleQuickSmc}
        disabled={busy}
        title={`Fetch SMC data for ${selectedCoin} on 1h / 2h / 4h and send to AI`}
      >
        {fetching ? "Fetching SMC data…" : `⚡ Quick SMC — 1h / 2h / 4h`}
      </button>
      <form onSubmit={onSubmit}>
        <div className="input-wrapper">
          <input
            type="text"
            value={message}
            onChange={(e) => onChange(e.target.value)}
            placeholder="Optional context for SMC or ask anything..."
            className="chat-input"
            disabled={busy}
          />
          <button
            type="submit"
            className="send-button"
            disabled={busy || !message.trim()}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <line x1="22" y1="2" x2="11" y2="13" stroke="currentColor" strokeWidth="2" />
              <polygon points="22,2 15,22 11,13 2,9 22,2" />
            </svg>
          </button>
        </div>
      </form>
    </div>
  );
}
