import { useState } from "react";
import type { LeverageStatus } from "../App/types";
import { setLeverage as setLeverageService, setBulkLeverage, type BulkLeverageResult } from "../services/tradingService";

export function useLeverage() {
  const [status, setStatus] = useState<LeverageStatus>({ type: null, message: "" });
  const [bulkResults, setBulkResults] = useState<BulkLeverageResult[]>([]);
  const [loading, setLoading] = useState(false);

  const applyLeverage = async (symbol: string, value: number) => {
    setStatus({ type: null, message: "" });
    setLoading(true);
    try {
      const data = await setLeverageService(symbol, value);
      if (data.success) {
        setStatus({ type: "success", message: `Leverage set to ${value}x for ${symbol}` });
      } else {
        setStatus({ type: "error", message: data.message || "Failed" });
      }
    } catch {
      setStatus({ type: "error", message: "Request failed" });
    } finally {
      setLoading(false);
    }
  };

  const applyBulkLeverage = async (symbols: string[], value: number) => {
    setStatus({ type: null, message: "" });
    setBulkResults([]);
    setLoading(true);
    try {
      const data = await setBulkLeverage(symbols, value);
      setBulkResults(data.results);
      const failed = data.results.filter((r) => !r.success);
      if (failed.length === 0) {
        setStatus({ type: "success", message: `Leverage set to ${value}x for ${symbols.length} coin(s)` });
      } else {
        setStatus({ type: "error", message: `${failed.length} coin(s) failed` });
      }
    } catch {
      setStatus({ type: "error", message: "Request failed" });
    } finally {
      setLoading(false);
    }
  };

  return { status, bulkResults, loading, applyLeverage, applyBulkLeverage };
}
