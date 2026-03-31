import { useState } from "react";
import "../App.css";
import { TIMEFRAMES, type Timeframe } from "../constants";
import { coins } from "../coins";
import Header from "./components/Header";
import CoinList from "./components/CoinList";
import LeveragePanel from "./components/LeveragePanel";
import Messages from "./components/Chat/Messages";
import Input from "./components/Chat/Input";
import ChartPanel from "./components/Chart";
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
        onClearChat={clearHistory}
        coinList={<CoinList onCoinClick={handleCoinChange} selectedCoin={selectedCoin} />}
        symbol={selectedCoin}
        showLeverage={showLeverage}
        onToggleLeverage={() => setShowLeverage((v) => !v)}
      />
      {showLeverage && (
        <div className="leverage-popover">
          <LeveragePanel />
        </div>
      )}
      <div className="workspace">
        <div className="chart-workspace">
          <ChartPanel
            symbol={selectedCoin}
            timeframe={timeframe}
            onTimeframeChange={handleTimeframeChange}
            onAnalyze={handleAnalyze}
          />
        </div>
        <aside className="chat-sidebar">
          <div className="chat-header">
            <div className="chat-header-title">
              <div className="chat-online-dot" />
              AI Trading Assistant
            </div>
          </div>
          <Messages chatHistory={chatHistory} loading={loading} />
          <Input
            message={message}
            loading={loading}
            selectedCoin={selectedCoin}
            onChange={setMessage}
            onSubmit={handleSubmit}
          />
        </aside>
      </div>
    </div>
  );
}
