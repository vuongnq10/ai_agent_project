import { useState } from "react";
import "../App.css";
import type { ChatMessage } from "./types";
import type { Timeframe } from "./TimeframeSelector";
import Header from "./Header";
import Sidebar from "./Sidebar";
import ChatMessages from "./ChatMessages";
import ChatInput from "./ChatInput";
import ChartPanel from "./ChartPanel";

export default function App() {
  const [message, setMessage] = useState("");
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedCoin, setSelectedCoin] = useState("BTCUSDT");

  const handleCoinClick = (coin: string) => {
    setSelectedCoin(coin);
  };

  const handleAnalyze = (symbol: string, timeframe: Timeframe) => {
    const query = `Analyze ${symbol} on the ${timeframe} timeframe using Smart Money Concepts. Identify: trend direction, key support/resistance levels, order blocks, fair value gaps, BOS/CHoCH, liquidity levels, and suggest a trade setup with entry, stop loss, and take profit.`;
    handleSubmit({ preventDefault: () => {} } as React.FormEvent, query);
  };

  const handleSubmit = async (e: React.FormEvent, query?: string) => {
    e.preventDefault();
    const messageToSend = query || message;
    if (!messageToSend) return;

    setLoading(true);
    setChatHistory((prev) => [...prev, { role: "user", content: messageToSend }]);
    setMessage("");

    try {
      const eventSource = new EventSource(
        `http://127.0.0.1:8000/gemini/stream?query=${encodeURIComponent(messageToSend)}`
      );

      let fullMessage = "";
      setChatHistory((prev) => [...prev, { role: "assistant", content: "" }]);

      eventSource.onmessage = (event) => {
        const { character } = JSON.parse(event.data);
        fullMessage += character;
        setChatHistory((prev) => {
          const next = [...prev];
          next[next.length - 1] = { ...next[next.length - 1], content: fullMessage };
          return next;
        });
      };

      eventSource.addEventListener("end", () => {
        eventSource.close();
        setLoading(false);
      });

      eventSource.onerror = () => {
        eventSource.close();
        setLoading(false);
      };
    } catch {
      setChatHistory((prev) => [...prev, { role: "assistant", content: "Sorry, something went wrong." }]);
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <Header
        onToggleSidebar={() => {}}
        onClearChat={() => setChatHistory([])}
        selectedCoin={selectedCoin}
      />
      <main className="main-content">
        <Sidebar collapsed={false} onCoinClick={handleCoinClick} selectedCoin={selectedCoin} />
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
