import { useState } from "react";
import type { ChatMessage } from "../App/types";
import { streamChat, type AgentId } from "../services/chatService";

export function useChat(agent: AgentId) {
  const [message, setMessage] = useState("");
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);

  const submit = (query?: string) => {
    const messageToSend = query || message;
    if (!messageToSend) return;

    setLoading(true);
    setChatHistory((prev) => [...prev, { role: "user", content: messageToSend }]);
    setMessage("");

    let fullMessage = "";
    setChatHistory((prev) => [...prev, { role: "assistant", content: "" }]);

    streamChat(
      messageToSend,
      agent,
      (char) => {
        fullMessage += char;
        setChatHistory((prev) => {
          const next = [...prev];
          next[next.length - 1] = { ...next[next.length - 1], content: fullMessage };
          return next;
        });
      },
      () => setLoading(false),
      () => setLoading(false)
    );
  };

  const clearHistory = () => setChatHistory([]);

  return { message, setMessage, chatHistory, loading, submit, clearHistory };
}
