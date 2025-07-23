tools = [
    {
        "type": "function",
        "function": {
            "name": "ticker_ohlcv",
            "description": "Fetches the ticker price for a given symbol and timeframe.",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "The trading pair symbol (e.g., 'SOL/USDT')."
                    },
                    "timeframe": {
                        "type": "string",
                        "description": "The timeframe for the OHLCV data (e.g., '1h', '30m')."
                    }
                },
                "required": ["symbol", "timeframe"]
            }
        }
    }
]
