from typing_extensions import TypedDict
from typing import Dict, Any

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, END, START
from google.genai.types import Content, Part

from master_agent.agents.agent import Agent

memory = InMemorySaver()
agent = Agent()


class MasterState(TypedDict):
    intent: Dict[str, Any]
    agent_response: str
    user_prompt: str
    step_count: int
    max_steps: int


class MasterAgent:
    def __init__(self):
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(MasterState)

        workflow.add_node("chatbot", self._call_master)
        workflow.add_node("generate_response", self._generate_response_node)

        workflow.set_entry_point("chatbot")
        workflow.add_edge("generate_response", END)

        return workflow.compile(checkpointer=memory)

    def _call_master(self, state: MasterState):
        prompt = state["user_prompt"]
        system_prompt = """
        You are an AI assistant that analyzes user prompts for cryptocurrency trading intentions.
        
        Classify the user's request into one of these categories:
        - GET_DATA_AND_INDICATORS: User wants to fetch market data and perform analysis
        - MARKET_ANALYSIS: User seeks market analysis based on data
        - TRADE_RECOMMENDATION: User seeks trade recommendations based on market analysis

        Respond in JSON format:
        {
            "type": "CATEGORY",
            "symbols": "BTC/USDT",
            "timeframes": ["1h", "4h"],
            "confidence": 0.9,
            ... additional relevant details ...
        }
        """
        # move this part to Agent class later
        contents = [
            Content(
                role="user",
                parts=[
                    Part.from_text(text=f"{system_prompt}\n\nUser prompt: {prompt}")
                ],
            )
        ]
        intent = agent(contents=contents)
        state["intent"] = intent

        state["step_count"] = state.get("step_count", 0) + 1
        return state

    def _routing(self, state: MasterState):
        response_state = state.get("intent", {}).get("type", "GENERAL_QUERY")
        switcher = {
            "GET_DATA_AND_INDICATORS": "data_agent",
            "MARKET_ANALYSIS": "analysis_agent",
            "TRADE_RECOMMENDATION": "trade_agent",
        }

        return switcher.get(response_state, "general_agent")

    def _generate_response_node(self, state: MasterState):
        return state

    def __call__(self, prompt: str, session_id="default_session"):
        initial_state = {
            "agent_response": "",
            "intent": {},
            "user_prompt": prompt,
            "step_count": 0,
            "max_steps": 20,
        }
        config = {"configurable": {"thread_id": session_id}}

        events = self.graph.stream(initial_state, config=config, stream_mode="values")

        for event in events:
            if event["agent_response"]:
                response_text = event["agent_response"]
                yield response_text
