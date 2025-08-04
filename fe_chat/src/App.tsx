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
  const chatWindowRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (chatWindowRef.current) {
      chatWindowRef.current.scrollTop = chatWindowRef.current.scrollHeight;
    }
  }, [chatHistory]);

  const handleCoinClick = (coin: string) => {
    const query = `get indicator of ${coin} in 15m, 30m, 1h, 2h and 4h, analyze all provided indicators from tool and get entry price, side of buy or sell then save the trade setup`;
    setMessage(query);
    handleSubmit({ preventDefault: () => {} } as React.FormEvent, query); // Pass a dummy event and the query
  };

  const handleSubmit = async (e: React.FormEvent, query?: string) => {
    e.preventDefault();
    const messageToSend = query || message;
    if (!messageToSend) return;

    setLoading(true);
    const userMessage = { role: "user", content: messageToSend };
    setChatHistory((prev) => [...prev, userMessage]);
    setMessage(PROMPT); // Clear input after sending

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

  return (
    <div className="App">
      <div className="main-container">
        <div className="coin-buttons-container">
          <h3 className="coin-buttons-header">Popular Coins</h3>
          {coins.map((coin) => (
            <button
              key={coin}
              className="coin-button"
              onClick={() => handleCoinClick(coin)}
            >
              {coin}
            </button>
          ))}
        </div>
        <div className="chat-section">
          <div className="chat-window" ref={chatWindowRef}>
            {chatHistory.map((item, index) => (
              <div key={index} className={`message ${item.role}`}>
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {item.content}
                </ReactMarkdown>
              </div>
            ))}
            {loading && <div className="message assistant">...</div>}
          </div>
          <form onSubmit={handleSubmit} className="chat-form">
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Type your message..."
              className="chat-input"
            />
            <button type="submit" className="send-button">
              Send
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default App;
