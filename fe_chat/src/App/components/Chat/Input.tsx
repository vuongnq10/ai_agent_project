import { useState, useRef, useEffect } from "react";
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
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-expand textarea height based on content
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 100)}px`;
  }, [message]);

  const handleQuickSmc = async (e: React.MouseEvent) => {
    e.preventDefault();
    setFetching(true);
    try {
      const query = await buildSmcQuery(selectedCoin, message);
      const fakeEvent = { preventDefault: () => {} } as React.FormEvent;
      onSubmit(fakeEvent, query);
      onChange("");
    } finally {
      setFetching(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!busy && message.trim()) {
        const fakeEvent = { preventDefault: () => {} } as React.FormEvent;
        onSubmit(fakeEvent);
      }
    }
  };

  const busy = loading || fetching;

  return (
    <div className="chat-input-area">
      <button
        className="quick-btn"
        onClick={handleQuickSmc}
        disabled={busy}
        title={`Fetch SMC data for ${selectedCoin} on 30m / 2h / 4h and send to AI`}
      >
        {fetching ? (
          <>
            <svg className="animate-spin" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M21 12a9 9 0 11-6.219-8.56"/>
            </svg>
            Fetching SMC data...
          </>
        ) : (
          <>
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
              <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
            </svg>
            Quick SMC Analysis — 30m / 2h / 4h
          </>
        )}
      </button>
      <form onSubmit={onSubmit}>
        <div className="input-box">
          <textarea
            ref={textareaRef}
            rows={1}
            value={message}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask anything... (Enter to send)"
            className="chat-textarea"
            disabled={busy}
          />
          <button
            type="submit"
            className="send-btn"
            disabled={busy || !message.trim()}
            title="Send message"
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="12" y1="19" x2="12" y2="5"/>
              <polyline points="5 12 12 5 19 12"/>
            </svg>
          </button>
        </div>
      </form>
    </div>
  );
}
