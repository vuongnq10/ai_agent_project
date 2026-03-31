interface Props {
  onToggleSidebar: () => void;
  onClearChat: () => void;
  selectedCoin?: string;
}

export default function Header({ onClearChat, selectedCoin }: Props) {
  return (
    <header className="app-header">
      <div className="header-left">
        <div className="app-logo">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
            <path d="M3 3v18h18" stroke="#089981" strokeWidth="2" strokeLinecap="round"/>
            <path d="M7 12l3-3 4 4 5-5" stroke="#089981" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </div>
        <span className="app-title">CryptoAI</span>
        {selectedCoin && <span className="header-coin-badge">{selectedCoin}</span>}
      </div>
      <div className="header-right">
        <button className="clear-chat-btn" onClick={onClearChat}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="3 6 5 6 21 6"/>
            <path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6"/>
            <path d="M10 11v6M14 11v6"/>
          </svg>
          <span>Clear Chat</span>
        </button>
      </div>
    </header>
  );
}
