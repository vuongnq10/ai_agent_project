import { useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { ChatMessage } from "../../types";

interface ChatMessagesProps {
  chatHistory: ChatMessage[];
  loading: boolean;
}

export default function Messages({ chatHistory, loading }: ChatMessagesProps) {
  const chatWindowRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (chatWindowRef.current) {
      chatWindowRef.current.scrollTop = chatWindowRef.current.scrollHeight;
    }
  }, [chatHistory]);

  return (
    <div className="chat-messages" ref={chatWindowRef}>
      {chatHistory.length === 0 ? (
        <div className="chat-empty">
          <svg className="chat-empty-icon" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
          <p className="chat-empty-title">AI Trading Assistant</p>
          <p className="chat-empty-sub">Ask about market conditions, get analysis, or request trade setups.</p>
        </div>
      ) : (
        chatHistory.map((item, index) => (
          <div key={index} className={`message-wrapper ${item.role}`}>
            <div className={`message-avatar ${item.role}`}>
              {item.role === "user" ? "U" : "AI"}
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
        <div className="loading-indicator">
          <div className="typing-dots">
            <div className="typing-dot" />
            <div className="typing-dot" />
            <div className="typing-dot" />
          </div>
          <span>AI is thinking...</span>
        </div>
      )}
    </div>
  );
}
