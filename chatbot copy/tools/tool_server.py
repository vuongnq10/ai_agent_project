# tool_server.py
from typing import Any, Callable

from chatbot.tools.cx_connector import CXConnector
from chatbot.tools.cx_tools import tools as cx_tools

cx_connector = CXConnector()

# A mapping from tool name to the actual function
AVAILABLE_TOOLS = {
    "ticker_ohlcv": cx_connector.ticker_ohlcv,
}


class ToolServer:
    def __init__(self):
        self.tools: dict[str, Callable] = {}
        self.tool_configs = []
        self.register_tools()

    def register_tools(self):
        self.tool_configs.extend(cx_tools)
        for tool_config in self.tool_configs:
            tool_name = tool_config["function"]["name"]
            if tool_name in AVAILABLE_TOOLS:
                self.tools[tool_name] = AVAILABLE_TOOLS[tool_name]

    def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """Execute a tool directly by name with given arguments"""
        if tool_name not in self.tools:
            raise ValueError(f"Tool {tool_name} not found")

        tool_func = self.tools[tool_name]
        return tool_func(**kwargs)

    def get_tools_config(self):
        """Get tool configurations in format compatible with Gemini"""
        return self.tool_configs
