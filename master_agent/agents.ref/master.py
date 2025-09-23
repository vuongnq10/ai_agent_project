import os
from typing_extensions import TypedDict
from typing import Dict, Any, List, Literal

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, END, START
from google.genai import Client
from google.genai.types import HttpOptions, GenerateContentConfig, Content, Part

from broker_bot.tools.cx_connector import CXConnector

cx_connector = CXConnector()
memory = InMemorySaver()

GEMINI_MODEL = "gemini-2.5-flash"
API_KEY = os.getenv("GOOGLE_API_KEY")
client = Client(api_key=API_KEY, http_options=HttpOptions(api_version="v1alpha"))


class ChatState(TypedDict):
    agent_response: str
    chat_history: List[Content]
    step_count: int
    user_prompt: str
    max_steps: int


class MasterAgent:
    def __init__(self):
        self.cx_connector = CXConnector()
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(ChatState)

        workflow.add_node("chatbot", self._call_gemini)
        workflow.add_node("execute_tools", self._execute_tools)
        workflow.add_node("finalize", self._finalize_response)

        workflow.set_entry_point("chatbot")
        workflow.add_conditional_edges(
            "chatbot",
            self._should_execute_tools,
            {"execute_tools": "execute_tools", "finalize": "finalize"},
        )
        workflow.add_edge("finalize", END)

        return workflow.compile(checkpointer=memory)

    def _call_gemini(self, state: ChatState):
        prompt = state["user_prompt"]

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
            state["chat_history"].append(
                Content(role="user", parts=[Part.from_text(text=system_message)])
            )
        else:
            state["chat_history"].append(
                Content(role="user", parts=[Part.from_text(text=prompt)])
            )
        contents = state["chat_history"]
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=GenerateContentConfig(tools=[self.cx_connector.tools]),
        )

        print("Response from Gemini:", response.candidates)

        if response.candidates and response.text:
            state["agent_response"] = response.text

        if response.candidates:
            state["chat_history"].append(
                Content(role="model", parts=response.candidates[0].content.parts)
            )

        state["step_count"] += 1
        return state

    def _execute_tools(self, state: ChatState):
        # if not state["agent_response"]:
        #     return state

        last_message = state["chat_history"][-1]
        tool_responses = []

        for part in last_message.parts:
            if hasattr(part, "function_call") and part.function_call:
                func_call = part.function_call
                tool_name = func_call.name
                args = dict(func_call.args)

                tool_func = getattr(self.cx_connector, tool_name)
                tool_result = tool_func(**args)
                function_response = Part.from_function_response(
                    name=tool_name,
                    response=tool_result,
                )

                tool_responses.append(function_response)

        if tool_responses:
            state["chat_history"].append(Content(role="tool", parts=tool_responses))

        return state

    def _should_execute_tools(
        self, state: ChatState
    ) -> Literal["execute_tools", "finalize"]:
        if not state["chat_history"]:
            return "finalize"

        if state["step_count"] >= state["max_steps"]:
            return "finalize"

        last_message = state["chat_history"][-1]

        if hasattr(last_message, "parts") and last_message.parts:
            for part in last_message.parts:
                if hasattr(part, "function_call") and part.function_call:
                    print("🔧 Function calls detected, executing tools...")
                    return "execute_tools"

        return "finalize"

    def _finalize_response(self, state: ChatState) -> ChatState:
        return state

    def __call__(self, prompt: str, session_id="default_session"):
        initial_state = {
            "chat_history": [],
            "agent_response": "",
            "step_count": 0,
            "user_prompt": prompt,
            "max_steps": 20,
        }
        config = {"configurable": {"thread_id": session_id}}

        checkpoint = memory.get({"configurable": {"thread_id": session_id}})
        if checkpoint:
            initial_state["chat_history"] = checkpoint["channel_values"].get(
                "chat_history", []
            )

        print("Initial state:", initial_state["chat_history"])

        events = self.graph.stream(initial_state, config=config, stream_mode="values")

        for event in events:
            if event["agent_response"]:
                response_text = event["agent_response"]
                yield response_text
