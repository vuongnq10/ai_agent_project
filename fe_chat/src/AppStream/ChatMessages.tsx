import { useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { ChatMessage } from "./types";

interface ChatMessagesProps {
  chatHistory: ChatMessage[];
  loading: boolean;
}

export default function ChatMessages({ chatHistory, loading }: ChatMessagesProps) {
  const chatWindowRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (chatWindowRef.current) {
      chatWindowRef.current.scrollTop = chatWindowRef.current.scrollHeight;
    }
  }, [chatHistory]);

  return (
    <div className="chat-messages" ref={chatWindowRef}>
      {chatHistory.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="m3 21 1.9-5.7a8.5 8.5 0 1 1 3.8 3.8z"></path>
            </svg>
          </div>
          <h3>Start a conversation</h3>
          <p>Select a coin from the sidebar or type your own message to begin.</p>
        </div>
      ) : (
        chatHistory.map((item, index) => (
          <div key={index} className={`message-wrapper ${item.role}`}>
            <div className="message-avatar">
              {item.role === "user" ? (
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                  <circle cx="12" cy="7" r="4"></circle>
                </svg>
              ) : (
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
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
        <div className="loading-indicator">
          <div className="loading-spinner">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="animate-spin">
              <path d="M21 12a9 9 0 1 1-6.219-8.56" />
            </svg>
          </div>
          <span className="loading-text">AI is thinking...</span>
        </div>
      )}
    </div>
  );
}
