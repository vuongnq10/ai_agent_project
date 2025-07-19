from fastmcp import FastMCP
import random


class CXConnector:
    def __init__(self):
        self.mcp = FastMCP(name="CX Connector", version="1.0.0")
        self.setup_tools()

    def setup_tools(self):
        self.mcp.tools = {
            "add": {
                "name": "add",
                "description": "Returns the sum of two numbers.",
                "function": self.add,
                "parameters": {
                    "a": {"type": "number", "description": "First number."},
                    "b": {"type": "number", "description": "Second number."},
                },
                "required": ["a", "b"],
            },
            "times": {
                "name": "times",
                "description": "Returns the product of two numbers.",
                "function": self.times,
                "parameters": {
                    "a": {"type": "number", "description": "First number."},
                    "b": {"type": "number", "description": "Second number."},
                },
                "required": ["a", "b"],
            },
            "get_random_number": {
                "name": "get_random_number",
                "description": "Returns a random number between 0 and 100.",
                "function": self.get_random_number,
                "parameters": {},
            },
        }

    def add(self, a: int, b: int):
        """
        Returns the sum of two numbers.

        :param a: First number.
        :param b: Second number.
        :return: The sum of a and b.
        """
        print(f"Adding {a} and {b}")
        return f"The sum of {a} and {b} is {a + b}"

    def times(self, a: int, b: int):
        """
        Returns the product of two numbers.

        :param a: First number.
        :param b: Second number.
        :return: The product of a and b.
        """
        print(f"Multiplying {a} and {b}")
        return f"The product of {a} and {b} is {a * b}"

    def get_random_number(self):
        """Returns a random number between 0 and 100."""

        return random.randint(0, 100)

    def start(self):
        self.mcp.run()


if __name__ == "__main__":
    CXConnector().start()


# import ccxt
# from fastmcp import FastMCP
# import random

# binance = ccxt.binance({})
# mcp = FastMCP(name="CX Connector", version="1.0.0")


# @mcp.tool
# def add(a: int, b: int):
#     """
#     Returns the sum of two numbers.

#     :param a: First number.
#     :param b: Second number.
#     :return: The sum of a and b.
#     """

#     print(f"Adding {a} and {b}")

#     return f"The sum of {a} and {b} is {a + b}"


# @mcp.tool
# def times(a: int, b: int):
#     """
#     Returns the product of two numbers.

#     :param a: First number.
#     :param b: Second number.
#     :return: The product of a and b.
#     """
#     print(f"Multiplying {a} and {b}")

#     return f"The product of {a} and {b} is {a * b}"


# @mcp.tool
# def get_random_number():
#     """
#     Returns a random number between 0 and 100.
#     """
#     return random.randint(0, 100)


# @mcp.tool
# def ticker_ohlcv(symbol: str, timeframe: str):
#     """
#     Fetches the ticker price for a given symbol and timeframe.

#     :param symbol: The trading pair symbol (e.g., 'SOL/USDT').
#     :param timeframe: The timeframe for the OHLCV data (e.g., '1h', '30m').
#     :return: A list of dictionaries containing the OHLCV data.
#     """
#     ohlcv = binance.fetch_ohlcv(symbol, timeframe)
#     return ohlcv


# def get_data():
#     data = ticker_ohlcv("SOL/USDT", "1h")
#     return {"data": data}


# if __name__ == "__main__":
#     mcp.run(transport="http", host="0.0.0.0", port=8080)
