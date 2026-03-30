export interface ChatMessage {
  role: string;
  content: string;
}

export interface LeverageStatus {
  type: "success" | "error" | null;
  message: string;
}

export interface Candle {
  time: number; // unix seconds
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface Ticker {
  price: number;
  change: number;
  changePercent: number;
  high: number;
  low: number;
  volume: number;
}
