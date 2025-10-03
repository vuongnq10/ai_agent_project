import json
import re
from typing_extensions import TypedDict
from typing import Dict, Any

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, END, START
from google.genai.types import Content, Part

from master_agent.agents.agent import Agent
from master_agent.agents.tool_agent import ToolAgent
from master_agent.agents.analyse_agent import AnalyseAgent
from master_agent.agents.decision_agent import DecisionAgent

from broker_bot.tools.cx_connector import CXConnector

memory = InMemorySaver()
agent = Agent()
tool_agent = ToolAgent()
analyze_agent = AnalyseAgent()
decision_agent = DecisionAgent()
cx_connector = CXConnector()


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

        workflow.add_node("master_agent", self._call_master)
        workflow.add_node("tools_agent", self._tool_agent)
        workflow.add_node("analysis_agent", self._analyse_agent)
        workflow.add_node("decision_agent", self._decision_agent)
        workflow.add_node("generate_response", self._generate_response_node)

        workflow.add_conditional_edges(
            "master_agent",
            self._routing,
            {
                "tools_agent": "tools_agent",
                "analysis_agent": "analysis_agent",
                "decision_agent": "decision_agent",
                "master_agent": "master_agent",
            },
        )

        workflow.set_entry_point("master_agent")
        workflow.add_edge("generate_response", END)

        return workflow.compile(checkpointer=memory)

    def _call_master(self, state: MasterState):
        prompt = state["user_prompt"]
        intent = state.get("intent", {})
        system_prompt = """
        You are an AI assistant that analyzes user prompts for cryptocurrency trading intentions.
        
        Classify the user's request into one of these categories:
        - GET_DATA_AND_INDICATORS: Tools to fetch market data and compute indicators and place orders
        - MARKET_ANALYSIS: Analyse market conditions based on data and indicators
        - TRADE_RECOMMENDATION: Make decision to buy/sell or wait based on analysis

        Respond in JSON format:
        {
            "type": "CATEGORY" // One of the above categories,
            "symbols": "BTC/USDT",
            "timeframes": ["1h", "4h"],
            "confidence": 0.9,
            ... additional relevant details ...
        }
        """

        response = agent(prompt=f"{system_prompt}\n\nUser prompt: {prompt} \n\n Previous intent: {json.dumps(intent)}")
        cleaned = re.sub(
            r"^```json\s*|\s*```$", "", response.text.strip(), flags=re.MULTILINE
        )
        print("Master Agent Response:", response.text + " \n")

        state["intent"] = json.loads(cleaned)

        state["agent_response"] = response.text

        state["step_count"] = state.get("step_count", 0) + 1
        return state

    def _routing(self, state: MasterState):
        response_state = state.get("intent", {}).get("type", "GENERAL_QUERY")
        switcher = {
            "GET_DATA_AND_INDICATORS": "tools_agent",
            "MARKET_ANALYSIS": "analysis_agent",
            "TRADE_RECOMMENDATION": "decision_agent",
        }

        return switcher.get(response_state, "master_agent")

    def _tool_agent(self, state: MasterState):

        intent = state.get("intent", {})
        response = agent(prompt=json.dumps(intent), tools=cx_connector.tools)

        result = []
        if response.text:
            result += response.text + "\n"

        if response.candidates:
            parts = response.candidates[0].content.parts
            for part in parts:
                if hasattr(part, "function_call") and part.function_call:
                    func_call = part.function_call
                    tool_name = func_call.name
                    args = dict(func_call.args)

                    tool_func = getattr(cx_connector, tool_name)
                    tool_result = tool_func(**args)
                    result.append({tool_name: tool_name, result: tool_result})

        print("Tool Agent Result:", result + " \n")

        cleaned = re.sub(r"^```json\s*|\s*```$", "", result.strip(), flags=re.MULTILINE)
        print("Master Agent Response:", response.text + " \n")

        state["intent"] = {**json.loads(cleaned), "data": result}

        state["agent_response"] = response.text

        state["step_count"] = state.get("step_count", 0) + 1
        return state

    def _analyse_agent(self, state: MasterState):
        intent = state.get("intent", {})

        system_prompt = """
        You are an AI Analyse Agent that analyse the market and given insights for the market condition.

        Classify the user's request into one of these categories:
        - GET_DATA_AND_INDICATORS: Tools to fetch market data and compute indicators and place orders
        - MARKET_ANALYSIS: Analyse market conditions based on data and indicators
        - TRADE_RECOMMENDATION: Make decision to buy/sell or wait based on analysis

        Respond in JSON format:
        {
            "type": "CATEGORY" // One of the above categories,
            "symbols": "BTC/USDT",
            "timeframes": ["1h", "4h"],
            "confidence": 0.9,
            ... additional relevant details ...
        }
        """

        response = agent(prompt=f"{system_prompt}\n\n Request: {json.dumps(intent)}")

        print("Analyse Agent Response:", response.text + " \n")

        cleaned = re.sub(
            r"^```json\s*|\s*```$", "", response.text.strip(), flags=re.MULTILINE
        )
        print("Master Agent Response:", response.text + " \n")

        state["intent"] = json.loads(cleaned)

        state["agent_response"] = response.text

        state["step_count"] = state.get("step_count", 0) + 1
        return state

    def _decision_agent(self, state: MasterState):
        intent = state.get("intent", {})

        system_prompt = """
        You are an AI Decision Agent that make decision for cryptocurrency trading based on market analysis.

        Classify the user's request into one of these categories:
        - GET_DATA_AND_INDICATORS: Tools to fetch market data and compute indicators and place orders
        - MARKET_ANALYSIS: Analyse market conditions based on data and indicators
        - TRADE_RECOMMENDATION: Make decision to buy/sell or wait based on analysis

        Respond in JSON format:
        {
            "type": "CATEGORY" // One of the above categories,
            "symbols": "BTC/USDT",
            "timeframes": ["1h", "4h"],
            "confidence": 0.9,
            ... additional relevant details ...
        }
        """

        response = agent(prompt=f"{system_prompt}\n\n Request: {json.dumps(intent)}")

        cleaned = re.sub(
            r"^```json\s*|\s*```$", "", response.text.strip(), flags=re.MULTILINE
        )
        print("Decision Agent Response:", response.text + " \n")

        state["intent"] = json.loads(cleaned)

        state["agent_response"] = response.text

        state["step_count"] = state.get("step_count", 0) + 1
        return state

    def _generate_response_node(self, state: MasterState):
        # intent = state.get("intent", {})

        # state["agent_response"] = intent

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
