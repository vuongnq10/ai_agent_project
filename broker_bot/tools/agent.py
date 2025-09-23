# https://github.com/googleapis/python-genai

import os
from typing import Dict, Any, List, Literal
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, END

from google.genai import Client
from google.genai.types import (
    HttpOptions,
    GenerateContentConfig,
    Content,
    Part,
    ThinkingConfig,
)

from broker_bot.tools.cx_connector import CXConnector

GEMINI_MODEL = "gemini-2.5-flash"
API_KEY = os.getenv("GOOGLE_API_KEY")

client = Client(api_key=API_KEY, http_options=HttpOptions(api_version="v1alpha"))


class AgentState(TypedDict):
    messages: List[Dict[str, Any]]
    user_prompt: str
    final_response: str
    step_count: int
    max_steps: int


class Agent:
    def __init__(self):
        self.cx_connector = CXConnector()
        self.graph = self.define_graph()

    def define_graph(self) -> StateGraph:
        workflow = StateGraph(AgentState)

        workflow.add_node("generate_response", self.generate_response)
        workflow.add_node("execute_tools", self.execute_tools)
        workflow.add_node("finalize", self.finalize_response)

        workflow.set_entry_point("generate_response")
        workflow.add_conditional_edges(
            "generate_response",
            self.should_execute_tools,
            {"execute_tools": "execute_tools", "finalize": "finalize"},
        )

        workflow.add_edge("execute_tools", "generate_response")

        workflow.add_edge("finalize", END)

        return workflow.compile()

    def generate_response(self, state: AgentState) -> AgentState:
        # - Fair value gaps, Liquidity pools and Order blocks are important indicators to consider.
        if state["step_count"] == 0:
            system_message = f"""
            You are Kite a helpful cryptocurrency trading broker with access to calculation tools.
            You will help the user to analyze the market and make decisions based on their requests.
            Regarding the indicators, you give projection on price then recommendation for potential trade setups or wait for better scienario.
            The trade setup should follow:
            - Current market trend
            - All indicators are important, to consider
            - Consider for all timeframes.
            - Decide to wait or enter a trade based on the analysis.
            - It's not required to enter a trade immediately, you can suggest to wait for a better setup.
            \n\n User request: {state["user_prompt"]}
            """

            user_propmpt = Content(
                role="user", parts=[Part.from_text(text=system_message)]
            )
            contents = [user_propmpt]

            state["messages"].append(user_propmpt)
        else:
            contents = []
            for msg in state["messages"]:
                contents.append(msg)

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=GenerateContentConfig(
                tools=[self.cx_connector.tools],
                thinking_config=ThinkingConfig(include_thoughts=True),
                # max_output_tokens=500,
            ),
        )

        print(
            f"🤖 Agent response (iteration {state['step_count'] + 1}):",
            response.candidates[0],
        )

        if response.candidates:
            state["messages"].append(response.candidates[0].content)

        state["step_count"] += 1

        return state

    def should_execute_tools(
        self, state: AgentState
    ) -> Literal["execute_tools", "finalize"]:
        if not state["messages"]:
            return "finalize"

        if state["step_count"] >= state["max_steps"]:
            return "finalize"

        last_message = state["messages"][-1]

        if hasattr(last_message, "parts") and last_message.parts:
            for part in last_message.parts:
                if hasattr(part, "function_call") and part.function_call:
                    print("🔧 Function calls detected, executing tools...")
                    return "execute_tools"

        return "finalize"

    def execute_tools(self, state: AgentState) -> AgentState:
        if not state["messages"]:
            return state

        last_message = state["messages"][-1]
        tool_responses = []

        if hasattr(last_message, "parts") and last_message.parts:
            for part in last_message.parts:
                if hasattr(part, "function_call") and part.function_call:
                    func_call = part.function_call
                    tool_name = func_call.name
                    args = dict(func_call.args)

                    try:
                        tool_func = getattr(self.cx_connector, tool_name)
                        tool_result = tool_func(**args)
                        function_response = Part.from_function_response(
                            name=tool_name,
                            response={"result": tool_result},
                        )
                    except (AttributeError, TypeError) as e:
                        function_response = Part.from_function_response(
                            name=tool_name,
                            response={
                                "error": f"Tool {tool_name} not found or not callable. {e}"
                            },
                        )
                        print(f"❌ Tool error: {e}")
                    except Exception as e:
                        function_response = Part.from_function_response(
                            name=tool_name,
                            response={"error": str(e)},
                        )
                        print(f"❌ Execution error: {e}")

                    tool_responses.append(function_response)

        if tool_responses:
            function_response_parts = []
            for tool_response in tool_responses:
                function_response_parts.append(tool_response)

            tool_content = Content(role="user", parts=function_response_parts)
            state["messages"].append(tool_content)

        return state

    def finalize_response(self, state: AgentState) -> AgentState:
        step_text = []

        if state["messages"]:
            for message in state["messages"]:
                if hasattr(message, "parts") and message.parts:
                    for part in message.parts:
                        if hasattr(part, "text") and part.text:
                            step_text.append(part.text)

            step_text.pop(0)  # Remove the first message (system prompt)
            state["final_response"] = "\n".join(step_text)
            return state

        return state

    def call_agent(self, prompt: str) -> str:
        initial_state: AgentState = {
            "messages": [],
            "user_prompt": prompt,
            "final_response": [],
            "step_count": 0,
            "max_steps": 20,
        }

        return self.graph.invoke(initial_state)["final_response"]

    def __call__(self, prompt: str):
        return self.call_agent(prompt)
