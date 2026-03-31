interface Props {
  onToggleSidebar: () => void;
  onClearChat: () => void;
  center?: React.ReactNode;
  showLeverage: boolean;
  onToggleLeverage: () => void;
}

export default function Header({ onClearChat, center, showLeverage, onToggleLeverage }: Props) {
  return (
    <header className="app-header">
      <div className="header-left">
        <div className="app-logo">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
            <path d="M3 3v18h18" stroke="#38bdf8" strokeWidth="2" strokeLinecap="round"/>
            <path d="M7 12l3-3 4 4 5-5" stroke="#38bdf8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </div>
        <span className="app-title">CryptoAI</span>
      </div>
      {center && <div className="header-center">{center}</div>}
      <div className="header-right">
        <button
          className={`leverage-toggle-btn${showLeverage ? " active" : ""}`}
          onClick={onToggleLeverage}
          title="Leverage Settings"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="3"/>
            <path d="M19.07 4.93a10 10 0 0 1 0 14.14M4.93 4.93a10 10 0 0 0 0 14.14"/>
          </svg>
          <span>Leverage</span>
        </button>
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
