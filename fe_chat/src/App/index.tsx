import { useState } from "react";
import "../App.css";
import type { Timeframe } from "./ChartPanel/TimeframeSelector";
import Header from "./Header";
import Sidebar from "./Sidebar";
import ChatMessages from "./ChatMessages";
import ChatInput from "./ChatInput";
import ChartPanel from "./ChartPanel";
import { useChat } from "../hooks/useChat";

export default function App() {
  const { message, setMessage, chatHistory, loading, submit, clearHistory } = useChat();
  const [selectedCoin, setSelectedCoin] = useState("BTCUSDT");

  const handleAnalyze = (symbol: string, timeframe: Timeframe) => {
    const query = `Analyze ${symbol} on the ${timeframe} timeframe using Smart Money Concepts. Identify: trend direction, key support/resistance levels, order blocks, fair value gaps, BOS/CHoCH, liquidity levels, and suggest a trade setup with entry, stop loss, and take profit.`;
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
        selectedCoin={selectedCoin}
      />
      <main className="main-content">
        <Sidebar collapsed={false} onCoinClick={setSelectedCoin} selectedCoin={selectedCoin} />
        <section className="dashboard-center">
          <ChartPanel symbol={selectedCoin} onAnalyze={handleAnalyze} />
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
