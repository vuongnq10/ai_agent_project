import ccxt

binance = ccxt.binance({})


class CXConnector:
    def __init__(self):
        self.binance = ccxt.binance({})

    def ticker_ohlcv(self, symbol, timeframe):
        """
        Fetches the ticker price for a given symbol and timeframe.

        :param symbol: The trading pair symbol (e.g., 'SOL/USDT').
        :param timeframe: The timeframe for the OHLCV data (e.g., '1h', '30m').
        :return: A list of dictionaries containing the OHLCV data.
        """
        ohlcv = self.binance.fetch_ohlcv(symbol, timeframe)
        return ohlcv
