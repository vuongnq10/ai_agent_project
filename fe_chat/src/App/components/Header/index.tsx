import MarketBar from "../Chart/MarketBar";

interface Props {
  onClearChat: () => void;
  symbol: string;
  showLeverage: boolean;
  onToggleLeverage: () => void;
  theme: "light" | "dark";
  onToggleTheme: () => void;
}

export default function Header({ onClearChat, symbol, showLeverage, onToggleLeverage, theme, onToggleTheme }: Props) {
  return (
    <header className="topbar">
      <div className="topbar-brand">
        <span className="topbar-brand-icon">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="22 7 13.5 15.5 8.5 10.5 2 17" />
            <polyline points="16 7 22 7 22 13" />
          </svg>
        </span>
        <span className="topbar-brand-name">SMC</span>
      </div>

      <div className="topbar-ticker">
        <MarketBar symbol={symbol} />
      </div>

      <div className="topbar-actions">
        <button
          className={`btn btn-ghost btn-icon${showLeverage ? " btn-active" : ""}`}
          onClick={onToggleLeverage}
          title="Leverage Settings"
        >
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 20V10M18 20V4M6 20v-4"/>
          </svg>
          <span>Lev</span>
        </button>
        <button className="btn btn-ghost btn-icon" onClick={onClearChat} title="Clear Chat History">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="3 6 5 6 21 6"/>
            <path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6"/>
          </svg>
        </button>
        <button
          className="theme-toggle"
          onClick={onToggleTheme}
          title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
        >
          {theme === "dark" ? (
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <circle cx="12" cy="12" r="5"/>
              <line x1="12" y1="1" x2="12" y2="3"/>
              <line x1="12" y1="21" x2="12" y2="23"/>
              <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
              <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
              <line x1="1" y1="12" x2="3" y2="12"/>
              <line x1="21" y1="12" x2="23" y2="12"/>
              <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
              <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
            </svg>
          ) : (
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
            </svg>
          )}
        </button>
      </div>
    </header>
  );
}
