import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import "./App.css";
import { coins } from "./coins";

const PROMPT =
  "Give me 2 random numbers between 1 and 10, if both of them are even, give me the sum of them.";

function App() {
  const [message, setMessage] = useState(PROMPT);
  const [chatHistory, setChatHistory] = useState<
    { role: string; content: string }[]
  >([]);
  const [loading, setLoading] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const chatWindowRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (chatWindowRef.current) {
      chatWindowRef.current.scrollTop = chatWindowRef.current.scrollHeight;
    }
  }, [chatHistory]);

  const handleCoinClick = (coin: string) => {
    const query = `get indicator of ${coin} in 15m, 30m, 1h, 2h and 4h, analyze all provided indicators from tool and get entry price, side of buy or sell then save the trade setup`;
    setMessage(query);
    handleSubmit({ preventDefault: () => {} } as React.FormEvent, query);
  };

  const handleSubmit = async (e: React.FormEvent, query?: string) => {
    e.preventDefault();
    const messageToSend = query || message;
    if (!messageToSend) return;

    setLoading(true);
    const userMessage = { role: "user", content: messageToSend };
    setChatHistory((prev) => [...prev, userMessage]);
    setMessage(""); // Clear input after sending

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/chatbot?query=${encodeURIComponent(
          messageToSend
        )}`
      );
      const data = await response.json();
      const aiMessage = { role: "assistant", content: data.message };
      setChatHistory((prev) => [...prev, aiMessage]);
    } catch (error) {
      console.error("Error fetching chat response:", error);
      const errorMessage = {
        role: "assistant",
        content: "Sorry, something went wrong.",
      };
      setChatHistory((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const clearChat = () => {
    setChatHistory([]);
  };

  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <div className="header-left">
          <button
            className="sidebar-toggle"
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            aria-label="Toggle sidebar"
          >
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <line x1="3" y1="6" x2="21" y2="6"></line>
              <line x1="3" y1="12" x2="21" y2="12"></line>
              <line x1="3" y1="18" x2="21" y2="18"></line>
            </svg>
          </button>
          <h1 className="app-title">AI Trading Assistant</h1>
        </div>
        <div className="header-right">
          <button className="clear-chat-btn" onClick={clearChat}>
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <polyline points="3,6 5,6 21,6"></polyline>
              <path d="m19,6v14a2,2 0 0,1 -2,2H7a2,2 0 0,1 -2,-2V6m3,0V4a2,2 0 0,1 2,-2h4a2,2 0 0,1 2,2v2"></path>
            </svg>
            Clear Chat
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="main-content">
        {/* Sidebar */}
        <aside className={`sidebar ${sidebarCollapsed ? "collapsed" : ""}`}>
          <div className="sidebar-content">
            <div className="coin-section">
              <h3 className="section-title">
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <circle cx="12" cy="12" r="3"></circle>
                  <path d="m12 1v6m0 6v6"></path>
                  <path d="m1 12h6m6 0h6"></path>
                </svg>
                Popular Coins
              </h3>
              <div className="coin-grid">
                {coins.map((coin) => (
                  <button
                    key={coin}
                    className="coin-chip"
                    onClick={() => handleCoinClick(coin)}
                    title={`Analyze ${coin}`}
                  >
                    <span className="coin-symbol">{coin}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </aside>

        {/* Chat Area */}
        <section className="chat-container">
          <div className="chat-messages" ref={chatWindowRef}>
            {chatHistory.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon">
                  <svg
                    width="48"
                    height="48"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.5"
                  >
                    <path d="m3 21 1.9-5.7a8.5 8.5 0 1 1 3.8 3.8z"></path>
                  </svg>
                </div>
                <h3>Start a conversation</h3>
                <p>
                  Select a coin from the sidebar or type your own message to
                  begin.
                </p>
              </div>
            ) : (
              chatHistory.map((item, index) => (
                <div key={index} className={`message-wrapper ${item.role}`}>
                  <div className="message-avatar">
                    {item.role === "user" ? (
                      <svg
                        width="16"
                        height="16"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                      >
                        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                        <circle cx="12" cy="7" r="4"></circle>
                      </svg>
                    ) : (
                      <svg
                        width="16"
                        height="16"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                      >
                        <circle cx="12" cy="12" r="3"></circle>
                        <path d="m12 1v6m0 6v6"></path>
                        <path d="m1 12h6m6 0h6"></path>
                      </svg>
                    )}
                  </div>
                  <div className="message-content">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {item.content}
                    </ReactMarkdown>
                  </div>
                </div>
              ))
            )}
            {loading && (
              <div className="message-wrapper assistant">
                <div className="message-avatar">
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <circle cx="12" cy="12" r="3"></circle>
                    <path d="m12 1v6m0 6v6"></path>
                    <path d="m1 12h6m6 0h6"></path>
                  </svg>
                </div>
                <div className="message-content">
                  <div className="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Input Area */}
          <div className="chat-input-container">
            <form onSubmit={handleSubmit} className="chat-input-form">
              <div className="input-wrapper">
                <input
                  type="text"
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder="Type your message..."
                  className="message-input"
                  disabled={loading}
                />
                <button
                  type="submit"
                  className="send-button"
                  disabled={loading || !message.trim()}
                >
                  <svg
                    width="18"
                    height="18"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <line x1="22" y1="2" x2="11" y2="13"></line>
                    <polygon points="22,2 15,22 11,13 2,9 22,2"></polygon>
                  </svg>
                </button>
              </div>
            </form>
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;
