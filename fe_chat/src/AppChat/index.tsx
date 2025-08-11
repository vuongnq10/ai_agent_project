import React, { useState } from "react";
import "./styles.css"; // Assuming styles.css exists for basic styling

interface Message {
  text: string;
  sender: "user" | "bot";
}

const AppChat: React.FC = () => {
  const [message, setMessage] = useState<string>("");
  const [chatHistory, setChatHistory] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const handleSendMessage = async () => {
    if (message.trim() === "") return;

    const userMessage: Message = { text: message, sender: "user" };
    setChatHistory((prev) => [...prev, userMessage]);
    setMessage("");
    setIsLoading(true);

    try {
      // Simulate a network request to a mock URL
      const response = await fetch(
        `http://127.0.0.1:8000/chat_app?query=${message}`
      );
      const data = await response.json();

      if (!data.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Assuming the mock API returns a JSON object with a 'response' field

      const botResponse: Message = {
        text: data.data || "No response from mock server.",
        sender: "bot",
      };
      setChatHistory((prev) => [...prev, botResponse]);
    } catch (error) {
      console.error("Error sending message:", error);
      const errorMessage: Message = {
        text: `Error: ${
          error instanceof Error ? error.message : "Unknown error"
        }`,
        sender: "bot",
      };
      setChatHistory((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !isLoading) {
      handleSendMessage();
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-history">
        {chatHistory.map((msg, index) => (
          <div key={index} className={`chat-message ${msg.sender}`}>
            {msg.text}
          </div>
        ))}
        {isLoading && <div className="chat-message bot">Typing...</div>}
      </div>
      <div className="chat-input-area">
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Type your message..."
          disabled={isLoading}
        />
        <button onClick={handleSendMessage} disabled={isLoading}>
          Send
        </button>
      </div>
    </div>
  );
};

export default AppChat;
