export interface ChatMessage {
  role: string;
  content: string;
}

export interface LeverageStatus {
  type: "success" | "error" | null;
  message: string;
}
