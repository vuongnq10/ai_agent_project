# https://github.com/googleapis/python-genai

import os
import json
from typing import Dict, Any, List, Literal
from typing_extensions import TypedDict

from google.genai import Client
from google.genai.types import HttpOptions, GenerateContentConfig, Content, Part
from langgraph.graph import StateGraph, END

from chatbot.tools.cx_connector import CXConnector

GEMINI_MODEL = "gemini-2.0-flash-001"
API_KEY = os.getenv("GOOGLE_API_KEY")

# cx_connector = CXConnector()

client = Client(api_key=API_KEY, http_options=HttpOptions(api_version="v1alpha"))


class AgentState(TypedDict):
    """State for the LangGraph agent"""

    messages: List[Dict[str, Any]]
    user_prompt: str
    final_response: str
    iteration_count: int
    max_iterations: int


class Agent:
    def __init__(self):
        self.cx_connector = CXConnector()
        self.graph = self._create_graph()

    def _create_graph(self):
        workflow = StateGraph(AgentState)

        workflow.add_node("generate_response", self._generate_response)
        workflow.add_node("execute_tools", self._execute_tools)
        workflow.add_node("finalize", self._finalize_response)

        workflow.set_entry_point("generate_response")

        workflow.add_conditional_edges(
            "generate_response",
            self._should_execute_tools,
            {"execute_tools": "execute_tools", "finalize": "finalize"},
        )

        workflow.add_edge("execute_tools", "generate_response")

        workflow.add_edge("finalize", END)

        return workflow.compile()

    def _generate_response(self, state: AgentState):
        print("#" * 50)

        if state["iteration_count"] == 0:
            system_message = f"""
            You are a helpful cryptocurrency trading assistant with access to calculation tools.
            You must complete ALL parts of the user's request step by step using the available tools.
            \n\n User request: {state["user_prompt"]}
            """
            contents = [
                Content(role="user", parts=[Part.from_text(text=system_message)])
            ]
        else:
            contents = []
            for message in state["messages"]:
                contents.append(message)

            reminder_text = f"""Continue with the original task: '{state['user_prompt']}'. 
                You have executed some steps but the task is not complete yet. 
                Think about what operations are still needed and continue using tools to finish ALL required operations. 
                Do not repeat operations you have already completed.
            """
            contents.append(
                Content(role="user", parts=[Part.from_text(text=reminder_text)])
            )

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=GenerateContentConfig(tools=[self.cx_connector.tools]),
        )

        # if response.candidates and response.candidates[0].content.parts:
        #     part = response.candidates[0].content.parts[0]
        #     if hasattr(part, "text") and part.text:
        #         # send text back to whoever called the graph
        #         yield part.text

        # partial_text = ""
        # for event in response.candidates:
        #     if event.candidates and event.candidates[0].content.parts:
        #         for part in event.candidates[0].content.parts:
        #             if hasattr(part, "text") and part.text:
        #                 partial_text += part.text
        #                 # Yield partial tokens directly to caller
        #                 yield {"partial_response": partial_text}

        if response.candidates:
            state["messages"].append(response.candidates[0].content)

        state["iteration_count"] += 1

        return state

    def _should_execute_tools(
        self, state: AgentState
    ) -> Literal["execute_tools", "finalize"]:

        if not state["messages"]:
            return "finalize"

        if state["iteration_count"] >= state["max_iterations"]:
            print(
                f"🛑 Maximum iterations ({state['max_iterations']}) reached, finalizing..."
            )
            return "finalize"

        last_message = state["messages"][-1]

        if hasattr(last_message, "parts") and last_message.parts:
            for part in last_message.parts:
                if hasattr(part, "function_call") and part.function_call:
                    return "execute_tools"

        return "finalize"

    def _execute_tools(self, state: AgentState):
        if not state["messages"]:
            return state

        last_message = state["messages"][-1]
        tool_responses = []

        if hasattr(last_message, "parts") and last_message.parts:
            for part in last_message.parts:
                if hasattr(part, "function_call") and part.function_call:
                    function_call = part.function_call
                    tool_name = function_call.name
                    args = dict(function_call.args)

                    try:
                        tool_func = getattr(self.cx_connector, tool_name)
                        tool_result = tool_func(**args)
                        function_response = Part.from_function_response(
                            name=tool_name,
                            response=tool_result,
                        )
                    except (AttributeError, TypeError) as e:
                        function_response = Part.from_text(
                            text=f"Error: Tool {tool_name} not found or not callable. {e}"
                        )
                    except Exception as e:
                        function_response = Part.from_text(text=f"Error: {str(e)}")

                    tool_responses.append(function_response)
        if tool_responses:
            tool_content = Content(role="user", parts=tool_responses)
            state["messages"].append(tool_content)

        return state

    def _finalize_response(self, state: AgentState):

        if state["messages"]:
            for message in reversed(state["messages"]):
                for part in message.parts:
                    if hasattr(part, "text") and part.text:
                        state["final_response"] = part.text
                        return state

        state["final_response"] = "No response generated."
        return state

    def call_agent(self, prompt, max_iterations=20):
        initial_state: AgentState = {
            "messages": [],
            "user_prompt": prompt,
            "final_response": "",
            "iteration_count": 0,
            "max_iterations": max_iterations,
        }

        final_state = self.graph.invoke(initial_state)

        return final_state["final_response"]

    def __call__(self, prompt: str, max_iterations=20):
        # return self.call_agent(prompt)
        initial_state: AgentState = {
            "messages": [],
            "user_prompt": prompt,
            "final_response": "",
            "iteration_count": 0,
            "max_iterations": max_iterations,
        }

        for update in self.graph.stream(initial_state, stream_mode="updates"):
            messages = update.get("messages", [])
            for msg in messages:
                if hasattr(msg, "parts"):
                    for part in msg.parts:
                        if hasattr(part, "text") and part.text:
                            yield part.text
                elif isinstance(msg, dict) and "parts" in msg:
                    # If messages are dicts, not objects
                    for part in msg["parts"]:
                        if isinstance(part, dict) and "text" in part and part["text"]:
                            yield part["text"]
