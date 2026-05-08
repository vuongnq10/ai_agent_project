import { useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { ChatMessage } from "../../types";

interface ChatMessagesProps {
  chatHistory: ChatMessage[];
  loading: boolean;
}

function UserIcon() {
  return (
    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
      <circle cx="12" cy="7" r="4"/>
    </svg>
  );
}

function AIIcon() {
  return (
    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/>
      <polyline points="16 7 22 7 22 13"/>
    </svg>
  );
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
          <p className="chat-empty-title">SMC Trading Assistant</p>
          <p className="chat-empty-sub">Ask about market structure, get multi-timeframe analysis, or request trade setups with confluences.</p>
          <div className="chat-hint-row">
            <span className="chat-hint">Analyze BTC structure</span>
            <span className="chat-hint">Find entry confluences</span>
            <span className="chat-hint">Check order blocks</span>
          </div>
        </div>
      ) : (
        chatHistory.map((item, index) => (
          <div key={index} className={`msg ${item.role === "user" ? "user" : "ai"}`}>
            <div className={`msg-avatar ${item.role === "user" ? "user" : "ai"}`}>
              {item.role === "user" ? <UserIcon /> : <AIIcon />}
            </div>
            <div className="msg-body">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {item.content.replace(/\\n/g, '\n').replace(/\\"/g, '"')}
              </ReactMarkdown>
            </div>
          </div>
        ))
      )}
      {loading && (
        <div className="loading-indicator">
          <div className="msg-avatar ai">
            <AIIcon />
          </div>
          <div className="typing-dots">
            <div className="typing-dot" />
            <div className="typing-dot" />
            <div className="typing-dot" />
          </div>
          <span>Analyzing...</span>
        </div>
      )}
    </div>
  );
}
