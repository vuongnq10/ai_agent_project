import { useState } from "react";
import "../App.css";
import { TIMEFRAMES, type Timeframe } from "../constants";
import { coins } from "../coins";
import Header from "./Header";
import CoinList from "./Sidebar/CoinList";
import LeveragePanel from "./Sidebar/LeveragePanel";
import ChatMessages from "./ChatMessages";
import ChatInput from "./ChatInput";
import ChartPanel from "./ChartPanel";
import { useChat } from "../hooks/useChat";

function getUrlParams(): { coin: string; tf: Timeframe } {
  const sp = new URLSearchParams(window.location.search);
  const coinParam = sp.get("coin") ?? "BTCUSDT";
  const tfParam = sp.get("tf") ?? "1h";
  const coin = coins.includes(coinParam) ? coinParam : "BTCUSDT";
  const tf = (TIMEFRAMES as readonly string[]).includes(tfParam) ? (tfParam as Timeframe) : "1h";
  return { coin, tf };
}

function updateUrlParam(key: string, value: string) {
  const sp = new URLSearchParams(window.location.search);
  sp.set(key, value);
  window.history.pushState(null, "", `?${sp.toString()}`);
}

export default function App() {
  const { message, setMessage, chatHistory, loading, submit, clearHistory } = useChat();
  const [selectedCoin, setSelectedCoin] = useState(() => getUrlParams().coin);
  const [timeframe, setTimeframe] = useState<Timeframe>(() => getUrlParams().tf);
  const [showLeverage, setShowLeverage] = useState(false);

  const handleCoinChange = (coin: string) => {
    setSelectedCoin(coin);
    updateUrlParam("coin", coin);
  };

  const handleTimeframeChange = (tf: Timeframe) => {
    setTimeframe(tf);
    updateUrlParam("tf", tf);
  };

  const handleAnalyze = (symbol: string, tf: Timeframe) => {
    const query = `Analyze ${symbol} on the ${tf} timeframe using Smart Money Concepts. Identify: trend direction, key support/resistance levels, order blocks, fair value gaps, BOS/CHoCH, liquidity levels, and suggest a trade setup with entry, stop loss, and take profit.`;
    submit(query);
  };

  const handleSubmit = (e: React.FormEvent, query?: string) => {
    e.preventDefault();
    submit(query);
  };

  return (
    <div className="app-container">
      <Header
        onToggleSidebar={() => {}}
        onClearChat={clearHistory}
        center={<CoinList onCoinClick={handleCoinChange} selectedCoin={selectedCoin} />}
        showLeverage={showLeverage}
        onToggleLeverage={() => setShowLeverage((v) => !v)}
      />
      {showLeverage && (
        <div className="leverage-popover">
          <LeveragePanel />
        </div>
      )}
      <main className="main-content">
        <section className="dashboard-center">
          <ChartPanel
            symbol={selectedCoin}
            timeframe={timeframe}
            onTimeframeChange={handleTimeframeChange}
            onAnalyze={handleAnalyze}
          />
        </section>
        <aside className="chat-panel">
          <div className="chat-panel-header">AI Trading Assistant</div>
          <ChatMessages chatHistory={chatHistory} loading={loading} />
          <ChatInput
            message={message}
            loading={loading}
            onChange={setMessage}
            onSubmit={handleSubmit}
          />
        </aside>
      </main>
    </div>
  );
}
