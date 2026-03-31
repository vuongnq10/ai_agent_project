import { useState } from "react";
import type { LeverageStatus } from "../App/types";
import { setLeverage as setLeverageService } from "../services/tradingService";

export function useLeverage() {
  const [status, setStatus] = useState<LeverageStatus>({ type: null, message: "" });

  const applyLeverage = async (symbol: string, value: number) => {
    setStatus({ type: null, message: "" });
    try {
      const data = await setLeverageService(symbol, value);
      if (data.success) {
        setStatus({ type: "success", message: `Leverage set to ${value}x for ${symbol}` });
      } else {
        setStatus({ type: "error", message: data.message || "Failed" });
      }
    } catch {
      setStatus({ type: "error", message: "Request failed" });
    }
  };

  return { status, applyLeverage };
}
