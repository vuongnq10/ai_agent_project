import os
from typing_extensions import TypedDict
from typing import Dict, Any, List, Literal

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, END, START
from google.genai import Client
from google.genai.types import HttpOptions, GenerateContentConfig, Content, Part

memory = InMemorySaver()

GEMINI_MODEL = "gemini-2.5-flash"
API_KEY = os.getenv("GOOGLE_API_KEY")
client = Client(api_key=API_KEY, http_options=HttpOptions(api_version="v1alpha"))


class ChatState(TypedDict):
    agent_response: str
    chat_history: List[Content]


class MasterAgent:
    def __init__(self):
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(ChatState)

        workflow.add_node("chatbot", self._call_gemini)
        workflow.set_entry_point("chatbot")
        workflow.add_edge("chatbot", END)

        return workflow.compile(checkpointer=memory)

    def _call_gemini(self, state: ChatState):
        contents = state["chat_history"]

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
        )

        if response.candidates:
            state["agent_response"] = response.text
            state["chat_history"].append(
                Content(role="model", parts=[Part.from_text(text=response.text)])
            )

        return state

    def __call__(self, prompt: str, session_id="default_session"):
        config = {"configurable": {"thread_id": session_id}}
        checkpoint = memory.get({"configurable": {"thread_id": session_id}})

        initial_state = {
            "chat_history": [],
            "agent_response": "",
        }
        if checkpoint:
            initial_state["chat_history"] = checkpoint["channel_values"].get(
                "chat_history", []
            )

        initial_state["chat_history"].append(
            Content(role="user", parts=[Part.from_text(text=prompt)])
        )

        print("Initial state:", initial_state["chat_history"])

        events = self.graph.stream(initial_state, config=config, stream_mode="values")

        for event in events:
            if event["agent_response"]:
                response_text = event["agent_response"]
                yield response_text
