# https://github.com/googleapis/python-genai

import os
from typing import Dict, Any, List, Literal
from google.genai import Client
from google.genai.types import HttpOptions, GenerateContentConfig, Content, Part
from chatbot.tools.cx_connector import CXConnector

from langgraph.graph import StateGraph, END
from typing_extensions import TypedDict

GEMINI_MODEL = "gemini-2.5-pro"
API_KEY = os.getenv("GOOGLE_API_KEY")

client = Client(api_key=API_KEY, http_options=HttpOptions(api_version="v1alpha"))


class AgentState(TypedDict):
    """State for the LangGraph agent"""

    messages: List[Dict[str, Any]]
    user_prompt: str
    final_response: str
    iteration_count: int


class Agent:
    def __init__(self):
        self.cx_tools = CXConnector()
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
        print("🤖 Generating response from Gemini...")

        # Build content for the request
        if state["iteration_count"] == 0:
            # First iteration - just the user prompt
            contents = [
                Content(role="user", parts=[Part.from_text(text=state["user_prompt"])])
            ]
        else:
            # Subsequent iterations - include previous messages
            contents = []
            for msg in state["messages"]:
                contents.append(msg)

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=GenerateContentConfig(tools=[self.cx_tools.tools]),
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
                        tool_func = getattr(self.cx_tools, tool_name)
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

    def call_agent(self, prompt: str) -> str:
        """Main entry point for the agent"""
        print(f"🚀 Starting LangGraph agent with prompt: {prompt}")

        # Initialize state
        initial_state: AgentState = {
            "messages": [],
            "user_prompt": prompt,
            "final_response": "",
            "iteration_count": 0,
        }

        # Run the graph
        final_state = self.graph.invoke(initial_state)

        return final_state["final_response"]

    def __call__(self, prompt: str) -> str:
        return self.call_agent(prompt)



# https://github.com/googleapis/python-genai

import os
import threading
import queue
import time
from typing import Dict, Any, List, Literal, Generator
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
        self.streaming_callback = None

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

        # Use streaming if callback is set
        if self.streaming_callback:
            response = self._generate_streaming_response(contents, state)
        else:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=contents,
                config=GenerateContentConfig(tools=[self.cx_connector.tools]),
            )

        print(
            f"🤖 Agent response (iteration {state['iteration_count'] + 1}):", response
        )

        if response and response.candidates:
            state["messages"].append(response.candidates[0].content)

        state["iteration_count"] += 1

        return state

    def _generate_streaming_response(self, contents: List[Content], state: AgentState):
        """Generate streaming response and call the streaming callback for each chunk"""
        print(
            f"🔄 Starting streaming response (iteration {state['iteration_count'] + 1})..."
        )

        response_stream = client.models.generate_content_stream(
            model=GEMINI_MODEL,
            contents=contents,
            config=GenerateContentConfig(tools=[self.cx_connector.tools]),
        )

        complete_response = None
        accumulated_text = ""

        for chunk in response_stream:
            if chunk.candidates:
                candidate = chunk.candidates[0]
                if candidate.content and candidate.content.parts:
                    for part in candidate.content.parts:
                        if hasattr(part, "text") and part.text:
                            accumulated_text += part.text
                            # Stream the text chunk via callback
                            if self.streaming_callback:
                                self.streaming_callback(part.text)
                            print(f"📝 Streaming chunk: {part.text}")

                # Keep the last complete response for processing
                complete_response = chunk

        print(f"✅ Streaming complete. Total text: {accumulated_text}")
        return complete_response

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

    def set_streaming_callback(self, callback):
        """Set a callback function to receive streaming text chunks"""
        self.streaming_callback = callback

    # def call_agent_simple_stream(self, prompt: str) -> Generator[str, None, None]:
    #     """
    #     Simple streaming interface that directly streams a single response without tools.
    #     Use this for basic chatbot functionality with streaming.
    #     """
    #     contents = [Content(role="user", parts=[Part.from_text(text=prompt)])]

    #     response_stream = client.models.generate_content_stream(
    #         model=GEMINI_MODEL,
    #         contents=contents,
    #         config=GenerateContentConfig(),
    #     )

    #     for chunk in response_stream:
    #         if chunk.candidates:
    #             candidate = chunk.candidates[0]
    #             if candidate.content and candidate.content.parts:
    #                 for part in candidate.content.parts:
    #                     if hasattr(part, "text") and part.text:
    #                         print(f"📝 Streaming chunk: {part.text}")
    #                         yield part.text

    def call_agent_stream(
        self, prompt: str, max_iterations: int = 20
    ) -> Generator[str, None, None]:
        """
        Stream the agent response as it's generated using LangGraph with tools.
        Yields text chunks as they arrive in real-time.
        """
        # Create a queue to pass chunks from the callback to the generator
        chunk_queue = queue.Queue()
        execution_done = threading.Event()
        exception_holder = [None]

        def stream_callback(chunk: str):
            """Callback that puts chunks into the queue"""
            chunk_queue.put(chunk)

        def run_graph():
            """Run the LangGraph execution in a separate thread"""
            try:
                # Set the streaming callback
                original_callback = self.streaming_callback
                self.streaming_callback = stream_callback

                initial_state: AgentState = {
                    "messages": [],
                    "user_prompt": prompt,
                    "final_response": "",
                    "iteration_count": 0,
                    "max_iterations": max_iterations,
                }

                # Execute the graph with streaming
                self.graph.invoke(initial_state)

                # Restore original callback
                self.streaming_callback = original_callback

            except Exception as e:
                exception_holder[0] = e
            finally:
                # Signal that execution is done
                execution_done.set()

        # Start the graph execution in a separate thread
        graph_thread = threading.Thread(target=run_graph)
        graph_thread.start()

        # Yield chunks as they arrive
        while True:
            try:
                # Check if execution is done and queue is empty
                if execution_done.is_set() and chunk_queue.empty():
                    break

                # Get chunk with timeout to allow checking execution status
                chunk = chunk_queue.get(timeout=0.1)
                yield chunk

            except queue.Empty:
                # Continue if queue is empty but execution is not done
                if not execution_done.is_set():
                    continue
                else:
                    break
            except Exception as e:
                print(f"Error in streaming: {e}")
                break

        # Wait for the thread to complete and check for exceptions
        graph_thread.join()
        if exception_holder[0]:
            raise exception_holder[0]

    # def call_agent(self, prompt, max_iterations=20):
    #     initial_state: AgentState = {
    #         "messages": [],
    #         "user_prompt": prompt,
    #         "final_response": "",
    #         "iteration_count": 0,
    #         "max_iterations": max_iterations,
    #     }

    #     final_state = self.graph.invoke(initial_state)

    #     return final_state["final_response"]

    def __call__(self, prompt: str):
        # Use LangGraph streaming with tools for direct calls
        return self.call_agent_stream(prompt)
