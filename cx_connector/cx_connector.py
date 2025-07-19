import ccxt
from fastmcp import FastMCP
import random

binance = ccxt.binance({})
mcp = FastMCP(name="CX Connector", version="1.0.0")


@mcp.tool()
def add(a: int, b: int):
    """
    Returns the sum of two numbers.

    :param a: First number.
    :param b: Second number.
    :return: The sum of a and b.
    """

    print(f"Adding {a} and {b}")

    return f"The sum of {a} and {b} is {a + b}"


@mcp.tool()
def times(a: int, b: int):
    """
    Returns the product of two numbers.

    :param a: First number.
    :param b: Second number.
    :return: The product of a and b.
    """
    print(f"Multiplying {a} and {b}")

    return f"The product of {a} and {b} is {a * b}"


@mcp.tool()
def get_random_number():
    """
    Returns a random number between 0 and 100.
    """
    return random.randint(0, 100)


@mcp.tool()
def ticker_ohlcv(symbol: str, timeframe: str):
    """
    Fetches the ticker price for a given symbol and timeframe.

    :param symbol: The trading pair symbol (e.g., 'SOL/USDT').
    :param timeframe: The timeframe for the OHLCV data (e.g., '1h', '30m').
    :return: A list of dictionaries containing the OHLCV data.
    """
    ohlcv = binance.fetch_ohlcv(symbol, timeframe)
    return ohlcv


def get_data():
    data = ticker_ohlcv("SOL/USDT", "1h")
    return {"data": data}


if __name__ == "__main__":
    mcp.run(transport="stdio")
