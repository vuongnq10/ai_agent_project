import { useState } from "react";
import "../App.css";
import type { ChatMessage } from "./types";
import Header from "./Header";
import Sidebar from "./Sidebar";
import ChatMessages from "./ChatMessages";
import ChatInput from "./ChatInput";

const PROMPT =
  "Give me 2 random numbers between 1 and 10, if both of them are even, give me the sum of them.";

export default function App() {
  const [message, setMessage] = useState(PROMPT);
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const handleCoinClick = (coin: string) => {
    const query = `identify the trend of ${coin} in 2hr and lower timeframes, verify in lower timeframes for key support, resistance levels, entry points and others indicators, find the strongest demand and supply zones, determine the trade setup regarding the key levels`;
    setMessage(query);
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
          next[next.length - 1].content = fullMessage;
          return next;
        });
      };

      eventSource.addEventListener("end", () => {
        console.log("Stream finished ✅");
        eventSource.close();
        setLoading(false);
      });

      eventSource.onerror = (error) => {
        console.error("EventSource error:", error);
        eventSource.close();
        setLoading(false);
      };
    } catch (error) {
      console.error("Error setting up EventSource:", error);
      setChatHistory((prev) => [
        ...prev,
        { role: "assistant", content: "Sorry, something went wrong." },
      ]);
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <Header
        onToggleSidebar={() => setSidebarCollapsed(!sidebarCollapsed)}
        onClearChat={() => setChatHistory([])}
      />
      <main className="main-content">
        <Sidebar collapsed={sidebarCollapsed} onCoinClick={handleCoinClick} />
        <section className="chat-container">
          <ChatMessages chatHistory={chatHistory} loading={loading} />
          <ChatInput
            message={message}
            loading={loading}
            onChange={setMessage}
            onSubmit={handleSubmit}
          />
        </section>
      </main>
    </div>
  );
}
