interface ChatInputProps {
  message: string;
  loading: boolean;
  onChange: (value: string) => void;
  onSubmit: (e: React.FormEvent) => void;
}

export default function ChatInput({ message, loading, onChange, onSubmit }: ChatInputProps) {
  return (
    <div className="chat-input-container">
      <form onSubmit={onSubmit} className="chat-input-form">
        <div className="input-wrapper">
          <input
            type="text"
            value={message}
            onChange={(e) => onChange(e.target.value)}
            placeholder="Type your message..."
            className="message-input"
            disabled={loading}
          />
          <button
            type="submit"
            className="send-button"
            disabled={loading || !message.trim()}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="22" y1="2" x2="11" y2="13"></line>
              <polygon points="22,2 15,22 11,13 2,9 22,2"></polygon>
            </svg>
          </button>
        </div>
      </form>
    </div>
  );
}
