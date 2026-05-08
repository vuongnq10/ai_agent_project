import httpx


class CandleService:
    BINANCE_FUTURES_URL = "https://fapi.binance.com/fapi/v1"

    def fetch_candles(self, symbol: str, timeframe: str, limit: int = 300) -> list[dict]:
        url = f"{self.BINANCE_FUTURES_URL}/klines"
        params = {"symbol": symbol, "interval": timeframe, "limit": limit}
        with httpx.Client(timeout=10) as client:
            resp = client.get(url, params=params)
            resp.raise_for_status()
        return [
            {
                "timestamp": int(k[0]),
                "open": float(k[1]),
                "high": float(k[2]),
                "low": float(k[3]),
                "close": float(k[4]),
                "volume": float(k[5]),
            }
            for k in resp.json()
        ]
