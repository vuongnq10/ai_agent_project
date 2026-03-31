import { BOT_BASE_URL } from "./config";

export async function setLeverage(
  symbol: string,
  leverage: number
): Promise<{ success: boolean; message?: string }> {
  const res = await fetch(`${BOT_BASE_URL}/trading/leverage`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ symbol, leverage }),
  });
  return res.json();
}

export interface BulkLeverageResult {
  symbol: string;
  success: boolean;
  leverage?: number;
  message?: string;
}

export async function setBulkLeverage(
  symbols: string[],
  leverage: number
): Promise<{ results: BulkLeverageResult[] }> {
  const res = await fetch(`${BOT_BASE_URL}/trading/leverage/bulk`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ symbols, leverage }),
  });
  return res.json();
}
