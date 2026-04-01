import MarketBar from "../Chart/MarketBar";

interface Props {
  onClearChat: () => void;
  coinList: React.ReactNode;
  symbol: string;
  showLeverage: boolean;
  onToggleLeverage: () => void;
  theme: "light" | "dark";
  onToggleTheme: () => void;
}

export default function Header({ onClearChat, coinList, symbol, showLeverage, onToggleLeverage, theme, onToggleTheme }: Props) {
  return (
    <header className="app-header">
      <div className="header-brand">
        <div className="header-logo">🥔</div>
        <span className="header-title">Great Potato</span>
      </div>

      <div className="header-vsep" />

      <div className="header-coin">{coinList}</div>

      <div className="header-ticker">
        <MarketBar symbol={symbol} />
      </div>

      <div className="header-actions">
        <button
          className={`btn btn-ghost${showLeverage ? " btn-active" : ""}`}
          onClick={onToggleLeverage}
          title="Leverage Settings"
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 20V10M18 20V4M6 20v-4"/>
          </svg>
          <span>Leverage</span>
        </button>
        <button className="btn btn-ghost" onClick={onClearChat} title="Clear Chat">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="3 6 5 6 21 6"/>
            <path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6"/>
          </svg>
          <span>Clear</span>
        </button>
        <button
          className="theme-toggle"
          onClick={onToggleTheme}
          title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
        >
          {theme === "dark" ? "☀" : "☾"}
        </button>
      </div>
    </header>
  );
}
