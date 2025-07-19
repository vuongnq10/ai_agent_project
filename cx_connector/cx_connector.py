import ccxt

binance = ccxt.binance({})


def ticker_ohlcv(symbol, timeframe):
    """
    Fetches the ticker price for a given symbol and timeframe.

    :param symbol: The trading pair symbol (e.g., 'SOL/USDT').
    :param timeframe: The timeframe for the OHLCV data (e.g., '1h', '30m').
    :return: A list of dictionaries containing the OHLCV data.
    """
    ohlcv = binance.fetch_ohlcv(symbol, timeframe)
    return ohlcv


def hello_world():
    print("Hello, world!")
    data = ticker_ohlcv("SOL/USDT", "1h")
    return {"data": data}
