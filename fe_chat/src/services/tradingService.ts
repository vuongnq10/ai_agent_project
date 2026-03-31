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
