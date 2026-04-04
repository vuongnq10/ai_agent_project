import { useState, useEffect, useRef, useCallback } from "react";
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
import { useTheme } from "../hooks/useTheme";
import { fetchModels, type AgentId, type AIModel } from "../services/chatService";

// const FALLBACK_AGENTS: AIModel[] = [
//   { id: "gemini", label: "Gemini 2.5 Flash", model: "gemini-2.5-flash" },
//   { id: "gemini", label: "Gemini 2.5 Pro", model: "gemini-2.5-pro" },
//   { id: "gemini", label: "Gemini 2.0 Flash", model: "gemini-2.0-flash" },
//   { id: "gemini", label: "Gemini 1.5 Pro", model: "gemini-1.5-pro" },
//   { id: "gemini", label: "Gemini 1.5 Flash", model: "gemini-1.5-flash" },
//   { id: "claude", label: "Claude", model: "claude-opus-4-6" },
//   { id: "chatgpt", label: "ChatGPT", model: "gpt-4o" },
// ];

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
  const [theme, toggleTheme] = useTheme();
  const [agents, setAgents] = useState<AIModel[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<AIModel | null>(null);
  const [agentMenuOpen, setAgentMenuOpen] = useState(false);
  const activeAgent = selectedAgent ?? { id: "gemini" as AgentId, model: "", label: "" };
  const { message, setMessage, chatHistory, loading, submit, clearHistory } = useChat(activeAgent.id, activeAgent.model);
  const [selectedCoin, setSelectedCoin] = useState(() => getUrlParams().coin);
  const [timeframe, setTimeframe] = useState<Timeframe>(() => getUrlParams().tf);
  const [showLeverage, setShowLeverage] = useState(false);
  const [sidebarWidth, setSidebarWidth] = useState(380);
  const isDragging = useRef(false);
  const startX = useRef(0);
  const startWidth = useRef(0);

  const onDragStart = useCallback((e: React.MouseEvent) => {
    isDragging.current = true;
    startX.current = e.clientX;
    startWidth.current = sidebarWidth;
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
  }, [sidebarWidth]);

  useEffect(() => {
    const onMouseMove = (e: MouseEvent) => {
      if (!isDragging.current) return;
      const delta = startX.current - e.clientX;
      const newWidth = Math.min(600, Math.max(260, startWidth.current + delta));
      setSidebarWidth(newWidth);
    };
    const onMouseUp = () => {
      if (!isDragging.current) return;
      isDragging.current = false;
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
    };
    document.addEventListener("mousemove", onMouseMove);
    document.addEventListener("mouseup", onMouseUp);
    return () => {
      document.removeEventListener("mousemove", onMouseMove);
      document.removeEventListener("mouseup", onMouseUp);
    };
  }, []);

  useEffect(() => {
    fetchModels()
      .then((data) => {
        setAgents(data);
        setSelectedAgent(data[0] ?? null);
      })
      .catch(() => {/* keep fallback */ });
  }, []);

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
        theme={theme}
        onToggleTheme={toggleTheme}
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
            theme={theme}
          />
        </div>
        <div className="workspace-divider" onMouseDown={onDragStart} />
        <aside className="chat-sidebar" style={{ width: sidebarWidth, flexShrink: 0 }}>
          <div className="chat-header">
            <div className="chat-header-title">
              <div className="chat-online-dot" />
              AI Trading Assistant
            </div>
            <div className="agent-switcher">
              <button
                className="agent-trigger"
                onClick={() => setAgentMenuOpen((v) => !v)}
              >
                <span className="agent-trigger-label">{activeAgent.label}</span>
                <span className="agent-trigger-model">{activeAgent.model}</span>
                <svg
                  className={`agent-trigger-chevron${agentMenuOpen ? " open" : ""}`}
                  width="10" height="10" viewBox="0 0 24 24" fill="none"
                  stroke="currentColor" strokeWidth="2.5"
                >
                  <polyline points="6 9 12 15 18 9" />
                </svg>
              </button>
              {agentMenuOpen && (
                <div className="agent-menu">
                  {agents.map((a) => (
                    <button
                      key={`${a.id}-${a.model}`}
                      className={`agent-menu-item${a.model === selectedAgent?.model ? " active" : ""}`}
                      onClick={() => { setSelectedAgent(a); setAgentMenuOpen(false); }}
                    >
                      <span className="agent-menu-label">{a.label}</span>
                      <span className="agent-menu-model">{a.model}</span>
                    </button>
                  ))}
                </div>
              )}
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
