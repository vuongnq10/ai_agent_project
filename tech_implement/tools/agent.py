# https://github.com/googleapis/python-genai

import os
from typing import Dict, Any, List, Literal
from google.genai import Client
from google.genai.types import HttpOptions, GenerateContentConfig, Content, Part
from tech_implement.tools.calculator import Calculator

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

GEMINI_MODEL = "gemini-2.0-flash-001"
API_KEY = os.getenv("GOOGLE_API_KEY")

calculator = Calculator()
client = Client(api_key=API_KEY, http_options=HttpOptions(api_version="v1alpha"))


class AgentState(TypedDict):
    """State for the LangGraph agent"""

    messages: List[Dict[str, Any]]
    user_prompt: str
    final_response: str
    iteration_count: int
    max_iterations: int


class LangGraphAgent:
    def __init__(self):
        self.calculator = Calculator()
        self.graph = self._create_graph()

    def _create_graph(self) -> StateGraph:
        """Create the LangGraph workflow"""
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("generate_response", self._generate_response)
        workflow.add_node("execute_tools", self._execute_tools)
        workflow.add_node("finalize", self._finalize_response)

        # Add edges
        workflow.set_entry_point("generate_response")

        # Conditional edge from generate_response
        workflow.add_conditional_edges(
            "generate_response",
            self._should_execute_tools,
            {"execute_tools": "execute_tools", "finalize": "finalize"},
        )

        # Edge from execute_tools back to generate_response
        workflow.add_edge("execute_tools", "generate_response")

        # Edge from finalize to END
        workflow.add_edge("finalize", END)

        return workflow.compile()

    def _generate_response(self, state: AgentState) -> AgentState:
        """Generate response from Gemini model"""
        print("#" * 50)
        print("🤖 Generating response from Gemini...")

        # Build content for the request
        if state["iteration_count"] == 0:
            # First iteration - user prompt with clear instructions
            system_message = """You are a helpful assistant with access to calculation tools. You must complete ALL parts of the user's request step by step using the available tools.

IMPORTANT: When a user asks for multiple operations (like "get 2 random numbers then find their sum"):
1. You must perform ALL requested operations 
2. Use function calls for each step
3. Continue calling tools until the complete task is finished
4. Only provide a final text response when ALL operations are complete

For the current request, analyze what needs to be done and execute ALL steps."""

            contents = [
                Content(
                    role="user",
                    parts=[
                        Part.from_text(
                            text=f"{system_message}\n\nUser request: {state['user_prompt']}\n\nNow execute all necessary steps to complete this request."
                        )
                    ],
                )
            ]
        else:
            # Subsequent iterations - include all previous messages plus a reminder
            contents = []
            for msg in state["messages"]:
                contents.append(msg)

            # Add a specific reminder based on the original task
            reminder_text = f"""
                Continue with the original task: '{state['user_prompt']}'.
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
            config=GenerateContentConfig(tools=[self.calculator.tools]),
        )

        print(
            f"🤖 Agent response (iteration {state['iteration_count'] + 1}):", response
        )

        # Add the response to messages
        if response.candidates:
            state["messages"].append(response.candidates[0].content)

        state["iteration_count"] += 1

        return state

    def _should_execute_tools(
        self, state: AgentState
    ) -> Literal["execute_tools", "finalize"]:
        """Determine if we need to execute tools or finalize"""
        if not state["messages"]:
            return "finalize"

        # Check for maximum iterations to prevent infinite loops
        if state["iteration_count"] >= state["max_iterations"]:
            print(
                f"🛑 Maximum iterations ({state['max_iterations']}) reached, finalizing..."
            )
            return "finalize"

        last_message = state["messages"][-1]

        # Check if there are function calls in the last message
        if hasattr(last_message, "parts") and last_message.parts:
            for part in last_message.parts:
                if hasattr(part, "function_call") and part.function_call:
                    print("🔧 Function calls detected, executing tools...")
                    return "execute_tools"

        print("✅ No function calls detected, finalizing response...")
        return "finalize"

    def _execute_tools(self, state: AgentState) -> AgentState:
        """Execute tool calls and add responses to state"""
        print("🔧 Executing tools...")

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

                    print(f"🔧 Executing tool: {tool_name} with args: {args}")

                    try:
                        tool_func = getattr(self.calculator, tool_name)
                        tool_result = tool_func(**args)
                        function_response = Part.from_function_response(
                            name=tool_name,
                            response=tool_result,
                        )
                        print(f"✅ Tool {tool_name} result: {tool_result}")
                    except (AttributeError, TypeError) as e:
                        function_response = Part.from_text(
                            text=f"Error: Tool {tool_name} not found or not callable. {e}"
                        )
                        print(f"❌ Tool error: {e}")
                    except Exception as e:
                        function_response = Part.from_text(text=f"Error: {str(e)}")
                        print(f"❌ Execution error: {e}")

                    tool_responses.append(function_response)

        # Add tool responses to messages if any were executed
        if tool_responses:
            # Create a content object with tool responses
            tool_content = Content(role="user", parts=tool_responses)
            state["messages"].append(tool_content)
            print("🔧 Tool responses added to conversation")

        return state

    def _finalize_response(self, state: AgentState) -> AgentState:
        """Extract final response text"""
        print("✅ Finalizing response...")

        if state["messages"]:
            # Find the last assistant message with text
            for message in reversed(state["messages"]):
                if hasattr(message, "parts") and message.parts:
                    for part in message.parts:
                        if hasattr(part, "text") and part.text:
                            state["final_response"] = part.text
                            print(f"✅ Final result: {part.text}")
                            return state

        # Fallback if no text found
        state["final_response"] = "No response generated"
        return state

    def call_agent(self, prompt: str, max_iterations: int = 10) -> str:
        """Main entry point for the agent"""
        print(f"🚀 Starting LangGraph agent with prompt: {prompt}")

        # Initialize state
        initial_state: AgentState = {
            "messages": [],
            "user_prompt": prompt,
            "final_response": "",
            "iteration_count": 0,
            "max_iterations": max_iterations,
        }

        # Run the graph
        final_state = self.graph.invoke(initial_state)

        return final_state["final_response"]

    def __call__(self, prompt: str) -> str:
        return self.call_agent(prompt)
