# tool_server.py
from dataclasses import dataclass
from typing import Any, Callable

from chatbot.tools.calculator import Calculator

calculator = Calculator()


@dataclass
class Tool:
    name: str
    func: Callable
    description: str
    input_params: dict


class ToolServer:
    def __init__(self):
        self.tools = {}
        self.register_tools()

    def register_tools(self):
        calculator_tools = calculator.tools
        self.tools.update(calculator_tools)

    def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """Execute a tool directly by name with given arguments"""
        if tool_name not in self.tools:
            raise ValueError(f"Tool {tool_name} not found")

        tool = self.tools[tool_name]
        return tool.func(**kwargs)

    def get_tools_config(self):
        """Get tool configurations in format compatible with Gemini"""
        function_declarations = []
        for tool in self.tools.values():
            properties = {}
            for param_name, param_type in tool.input_params.items():
                properties[param_name] = {
                    "type": param_type,
                    "description": f"The {param_name} parameter for {tool.name}",
                }

            function_declarations.append(
                {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {
                        "type": "OBJECT",
                        "properties": properties,
                        "required": list(tool.input_params.keys()),
                    },
                }
            )
        print([{"function_declarations": function_declarations}])
        return [{"function_declarations": function_declarations}]
