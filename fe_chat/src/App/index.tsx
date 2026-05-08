import { useState, useEffect } from "react";
import "../App.css";
import { TIMEFRAMES, type Timeframe } from "../constants";
import { coins as defaultCoins } from "../coins";
import Header from "./components/Header";
import CoinList from "./components/CoinList";
import LeveragePanel from "./components/LeveragePanel";
import Messages from "./components/Chat/Messages";
import Input from "./components/Chat/Input";
import ChartPanel from "./components/Chart";
import { useChat } from "../hooks/useChat";
import { useTheme } from "../hooks/useTheme";
import { fetchModels, type AgentId, type AIModel } from "../services/chatService";
import { fetchPairs } from "../services/tradingService";

function getUrlParams(): { coin: string; tf: Timeframe } {
  const sp = new URLSearchParams(window.location.search);
  const coin = sp.get("coin") ?? "BTCUSDT";
  const tfParam = sp.get("tf") ?? "1h";
  const tf = (TIMEFRAMES as readonly string[]).includes(tfParam) ? (tfParam as Timeframe) : "1h";
  return { coin, tf };
}

function updateUrlParam(key: string, value: string) {
  const sp = new URLSearchParams(window.location.search);
  sp.set(key, value);
  window.history.pushState(null, "", `?${sp.toString()}`);
}

export default function App() {
  const [theme, toggleTheme] = useTheme();
  const [coins, setCoins] = useState<string[]>(defaultCoins);
  const [agents, setAgents] = useState<AIModel[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<AIModel | null>(null);
  const activeAgent = selectedAgent ?? { id: "gemini" as AgentId, model: "", label: "" };
  const { message, setMessage, chatHistory, loading, submit, clearHistory } = useChat(activeAgent.id, activeAgent.model);
  const [selectedCoin, setSelectedCoin] = useState(() => getUrlParams().coin);
  const [timeframe, setTimeframe] = useState<Timeframe>(() => getUrlParams().tf);
  const [showLeverage, setShowLeverage] = useState(false);

  useEffect(() => {
    fetchModels()
      .then((data) => {
        setAgents(data);
        setSelectedAgent(data[0] ?? null);
      })
      .catch(() => {/* keep fallback */});
  }, []);

  useEffect(() => {
    fetchPairs().then(setCoins).catch(() => {/* keep default */});
  }, []);

  const handleCoinChange = (coin: string) => {
    setSelectedCoin(coin);
    updateUrlParam("coin", coin);
  };

  const handleTimeframeChange = (tf: Timeframe) => {
    setTimeframe(tf);
    updateUrlParam("tf", tf);
  };

  const handleSubmit = (e: React.FormEvent, query?: string) => {
    e.preventDefault();
    submit(query);
  };

  const handleAgentChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const [id, model] = e.target.value.split(":");
    const found = agents.find((a) => a.id === id && a.model === model);
    if (found) setSelectedAgent(found);
  };

  return (
    <div className="app-container">
      <Header
        onClearChat={clearHistory}
        symbol={selectedCoin}
        showLeverage={showLeverage}
        onToggleLeverage={() => setShowLeverage((v) => !v)}
        theme={theme}
        onToggleTheme={toggleTheme}
      />
      {showLeverage && (
        <div className="leverage-popover">
          <LeveragePanel coins={coins} />
        </div>
      )}
      <div className="workspace">
        <CoinList coins={coins} onCoinClick={handleCoinChange} selectedCoin={selectedCoin} />
        <div className="chart-area">
          <ChartPanel
            symbol={selectedCoin}
            timeframe={timeframe}
            onTimeframeChange={handleTimeframeChange}
            theme={theme}
          />
        </div>
        <aside className="chat-panel">
          <div className="chat-toolbar">
            <div className="chat-toolbar-title">
              <span className="live-dot" />
              AI ASSISTANT
            </div>
            <select
              className="agent-select"
              value={activeAgent.model ? `${activeAgent.id}:${activeAgent.model}` : ""}
              onChange={handleAgentChange}
            >
              {agents.length === 0 && (
                <option value="">Loading models...</option>
              )}
              {agents.map((a) => (
                <option key={`${a.id}-${a.model}`} value={`${a.id}:${a.model}`}>
                  {a.label}
                </option>
              ))}
            </select>
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
