# https://github.com/googleapis/python-genai

import os
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
        if state["iteration_count"] == 0:
            contents = [
                Content(role="user", parts=[Part.from_text(text=state["user_prompt"])])
            ]
        else:
            contents = []
            for message in state["messages"]:
                contents.append(message)

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=GenerateContentConfig(tools=[self.cx_connector.tools]),
        )

        if response.candidates:
            state["messages"].append(response.candidates[0].content)

        state["iteration_count"] += 1

        return state

    def _should_execute_tools(
        self, state: AgentState
    ) -> Literal["execute_tools", "finalize"]:

        if not state["messages"]:
            return "finalize"

        last_message = state["messages"][-1]

        if hasattr(last_message, "parts") and last_message.parts:
            for part in last_message.parts:
                if hasattr(part, "function_call") and part.function_call:
                    return "execute_tools"

        return 'finalize'

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

    def call_agent(self, prompt):
        initial_state: AgentState = {
            "messages": [],
            "user_prompt": prompt,
            "final_response": "",
            "iteration_count": 0,
        }

        final_state = self.graph.invoke(initial_state)

        return final_state["final_response"]

    def __call__(self, prompt: str):
        return self.call_agent(prompt)


# class Agent:

#     def call_agent(self, prompt: str) -> str:

#         response = client.models.generate_content(
#             model=GEMINI_MODEL,
#             contents=[Content(role="user", parts=[Part.from_text(text=prompt)])],
#             config=GenerateContentConfig(tools=[cx_connector.tools]),
#         )

#         print("🤖 Agent response:", response)

#         while True:
#             print("🤖 Waiting for function calls...")
#             function_calls = []
#             function_content = []
#             for candidate in response.candidates:
#                 function_content.append(candidate.content)
#                 if candidate.content.parts:
#                     for part in candidate.content.parts:
#                         if hasattr(part, "function_call") and part.function_call:
#                             function_calls.append(part.function_call)

#             if not function_calls:
#                 print("✅ Final result:", response.text)
#                 return response.text

#             # Execute and respond to tool calls
#             tool_responses = []
#             for func_call in function_calls:
#                 tool_name = func_call.name
#                 args = dict(func_call.args)

#                 try:
#                     tool_func = getattr(cx_connector, tool_name)
#                     tool_result = tool_func(**args)
#                     function_response = Part.from_function_response(
#                         name=tool_name,
#                         response=tool_result,
#                     )
#                 except (AttributeError, TypeError) as e:
#                     function_response = Part.from_text(
#                         text=f"Error: Tool {tool_name} not found or not callable. {e}"
#                     )
#                 except Exception as e:
#                     function_response = Part.from_text(text=f"Error: {str(e)}")

#                 tool_responses.append(function_response)

#             print("🤖 Tool responses:", tool_responses)

#             response = client.models.generate_content(
#                 model=GEMINI_MODEL,
#                 contents=[
#                     Content(role="user", parts=[Part.from_text(text=prompt)]),
#                     response.candidates[0].content,
#                     tool_responses,
#                 ],
#                 config=GenerateContentConfig(tools=[cx_connector.tools]),
#             )

#     def __call__(self, prompt: str) -> str:
#         return self.call_agent(prompt)
