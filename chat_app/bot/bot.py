import os

from google.genai import Client
from google.genai.types import HttpOptions, Content, Part
from langgraph.graph import StateGraph, END, START
from typing import TypedDict, Annotated, List
from langgraph.graph.message import add_messages

GEMINI_MODEL = "gemini-2.5-flash"
API_KEY = os.getenv("GOOGLE_API_KEY")

client = Client(api_key=API_KEY, http_options=HttpOptions(api_version="v1alpha"))


class ChatState(TypedDict):
    messages: Annotated[List[Content], add_messages]


class ChatBot:
    def __init__(self):
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(ChatState)

        workflow.add_node("chatbot", self._call_gemini)
        workflow.set_entry_point("chatbot")
        workflow.add_edge("chatbot", END)

        return workflow.compile()

    def _call_gemini(self, state: ChatState):
        messages = state["messages"]
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=messages,
        )
        return {
            "messages": [
                Content(role="model", parts=[Part.from_text(text=response.text)])
            ]
        }

    def bot_response(
        self, user_message: str, chat_history: List[Content] = None
    ) -> str:
        if chat_history is None:
            chat_history = []

        user_prompt = Content(role="user", parts=[Part.from_text(text=user_message)])

        # Append the new user message to the chat history
        chat_history.append(user_prompt)

        print("Chat history before invoking graph:", chat_history)

        # Execute the graph with the updated chat history
        result = self.graph.invoke({"messages": chat_history})

        # Extract the latest model response
        model_response_content = result["messages"][-1]
        model_response_text = ""
        for part in model_response_content.parts:
            if part.text:
                model_response_text += part.text

        return model_response_text
