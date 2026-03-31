interface ChatInputProps {
  message: string;
  loading: boolean;
  onChange: (value: string) => void;
  onSubmit: (e: React.FormEvent) => void;
}

export default function Input({ message, loading, onChange, onSubmit }: ChatInputProps) {
  return (
    <div className="chat-input-container">
      <form onSubmit={onSubmit}>
        <div className="input-wrapper">
          <input
            type="text"
            value={message}
            onChange={(e) => onChange(e.target.value)}
            placeholder="Type your message..."
            className="chat-input"
            disabled={loading}
          />
          <button
            type="submit"
            className="send-button"
            disabled={loading || !message.trim()}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <line x1="22" y1="2" x2="11" y2="13" stroke="currentColor" strokeWidth="2"/>
              <polygon points="22,2 15,22 11,13 2,9 22,2"/>
            </svg>
          </button>
        </div>
      </form>
    </div>
  );
}
