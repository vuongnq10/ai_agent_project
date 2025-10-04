import json
import re
from typing_extensions import TypedDict
from typing import Dict, Any, List

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, END, START
from google.genai.types import Content, Part

from master_agent.agents.agent import Agent

# from master_agent.agents.tool_agent import ToolAgent
# from master_agent.agents.analyse_agent import AnalyseAgent
# from master_agent.agents.decision_agent import DecisionAgent

from broker_bot.tools.cx_connector import CXConnector

memory = InMemorySaver()
agent = Agent()
# tool_agent = ToolAgent()
# analyze_agent = AnalyseAgent()
# decision_agent = DecisionAgent()
cx_connector = CXConnector()


class MasterState(TypedDict):
    chat_history: List[Content]
    agent_response: str
    user_prompt: str
    step_count: int
    max_steps: int
    user_feedback: str


class MasterAgent:
    def __init__(self):
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(MasterState)

        workflow.add_node("init_flow", self._init_flow)
        workflow.add_node("master_agent", self._call_master)
        workflow.add_node("tools_agent", self._tool_agent)
        workflow.add_node("analysis_agent", self._analyse_agent)
        workflow.add_node("decision_agent", self._decision_agent)
        workflow.add_node("generate_response", self._generate_response)

        workflow.add_conditional_edges(
            "init_flow",
            self._routing,
            {
                "master_agent": "master_agent",
            },
        )

        workflow.add_conditional_edges(
            "master_agent",
            self._routing,
            {
                "tools_agent": "tools_agent",
                "analysis_agent": "analysis_agent",
                "decision_agent": "decision_agent",
                "generate_response": "generate_response",
            },
        )

        workflow.add_conditional_edges(
            "tools_agent",
            self._routing,
            {
                "analysis_agent": "analysis_agent",
                "decision_agent": "decision_agent",
                "master_agent": "master_agent",
            },
        )

        workflow.add_conditional_edges(
            "analysis_agent",
            self._routing,
            {
                "tools_agent": "tools_agent",
                "decision_agent": "decision_agent",
                "master_agent": "master_agent",
            },
        )

        workflow.add_conditional_edges(
            "decision_agent",
            self._routing,
            {
                "tools_agent": "tools_agent",
                "analysis_agent": "analysis_agent",
                "master_agent": "master_agent",
            },
        )

        workflow.set_entry_point("init_flow")
        workflow.add_edge("generate_response", END)

        return workflow.compile(checkpointer=memory)

    def _routing(self, state: MasterState):
        response_state = (
            state.get("agent_response")
            or """```json
            {
                "type": "GENERAL_QUERY"
            }
            ```"""
        )

        clean_str = response_state.strip("`json").strip("`")
        data_obj = json.loads(clean_str)
        type_value = data_obj.get("type", "GENERAL_QUERY")

        switcher = {
            "GET_DATA_AND_INDICATORS": "tools_agent",
            "MARKET_ANALYSIS": "analysis_agent",
            "TRADE_DECISION": "decision_agent",
            "GENERAL_QUERY": "master_agent",
            "FINAL_RESPONSE": "generate_response",
        }

        return switcher.get(type_value, "master_agent")

    def _init_flow(self, state: MasterState):
        state["user_feedback"] = "# Start the flow"
        return state

    def _call_master(self, state: MasterState):
        state["user_feedback"] = "# Master Agent Processing: " + str(
            state["step_count"]
        )
        if state["step_count"] == 0:
            system_prompt = """
                You are a Master Agent in Agentic AI assistant that analyzes user prompts for cryptocurrency trading intentions.
                
                Classify the user's request into one of these categories:
                - GET_DATA_AND_INDICATORS: Tools Agent to fetch market data and compute indicators and place orders
                - MARKET_ANALYSIS: Analyse Agent market conditions based on data and indicators
                - TRADE_DECISION: Decision Agent to buy/sell or wait based on analysis
                - GENERAL_QUERY: Generate the result of the prompt
                - FINAL_RESPONSE: Provide the final response to the user based on the analysis and decisions made by other agents.

                Respond in JSON format:
                {
                    "type": "CATEGORY", // One of the above categories
                    "symbols": "BTC/USDT",
                    "timeframes": ["1h", "4h"],
                    "confidence": 0.9,
                    ... additional relevant details ...
                }
                """
            contents = [
                # Content(role="system", parts=[Part.from_text(text=system_prompt)]),
                Content(
                    role="user",
                    parts=[
                        Part.from_text(
                            text=f"{system_prompt}\n\nUser prompt: {state['user_prompt']}"
                        )
                    ],
                ),
            ]
            state["chat_history"] = contents
        else:
            contents = state["chat_history"] + [
                Content(
                    role="user", parts=[Part.from_text(text=state["agent_response"])]
                )
            ]
            state["chat_history"] = contents

        response = agent(contents)
        serialized = self._proceed_reponse(response)

        if serialized["thought"]:
            state["user_feedback"] = serialized["thought"]

        if serialized["agent_response"]:
            state["agent_response"] = serialized["agent_response"]
            state["chat_history"].append(
                Content(
                    role="user",
                    parts=[Part.from_text(text=serialized["agent_response"])],
                )
            )

        state["step_count"] += 1
        return state

    def _tool_agent(self, state: MasterState):
        state["user_feedback"] = "# Tool Agent Processing: " + str(state["step_count"])
        contents = state["chat_history"]

        response = agent(contents, tools=[cx_connector.tools])

        serialized = self._proceed_reponse(response)
        if serialized["thought"]:
            state["user_feedback"] = serialized["thought"]
        if serialized["agent_response"]:
            state["agent_response"] = serialized["agent_response"]
            state["chat_history"].append(
                Content(
                    role="user",
                    parts=[Part.from_text(text=serialized["agent_response"])],
                )
            )
        else:
            state["agent_response"] = ""

        if response.candidates[0]:
            parts = response.candidates[0].content.parts
            for part in parts:
                if hasattr(part, "function_call") and part.function_call:
                    func_call = part.function_call
                    tool_name = func_call.name
                    args = dict(func_call.args)

                    tool_func = getattr(cx_connector, tool_name)
                    tool_result = tool_func(**args)
                    function_response = Part.from_function_response(
                        name=tool_name,
                        response=tool_result,
                    )

                    state["chat_history"].append(
                        Content(role="user", parts=[function_response])
                    )

        state["step_count"] += 1
        return state

    def _analyse_agent(self, state: MasterState):
        state["user_feedback"] = "# Analyse Agent Processing: " + str(
            state["step_count"]
        )
        contents = state["chat_history"]

        response = agent(contents)
        serialized = self._proceed_reponse(response)

        if serialized["thought"]:
            state["user_feedback"] = serialized["thought"]

        if serialized["agent_response"]:
            state["agent_response"] = serialized["agent_response"]
            state["chat_history"].append(
                Content(
                    role="user",
                    parts=[Part.from_text(text=serialized["agent_response"])],
                )
            )

        state["step_count"] += 1
        return state

    def _decision_agent(self, state: MasterState):
        state["user_feedback"] = "# Decistion Agent Processing: " + str(
            state["step_count"]
        )
        contents = state["chat_history"]

        response = agent(contents)
        serialized = self._proceed_reponse(response)

        if serialized["thought"]:
            state["user_feedback"] = serialized["thought"]

        if serialized["agent_response"]:
            state["agent_response"] = serialized["agent_response"]
            state["chat_history"].append(
                Content(
                    role="user",
                    parts=[Part.from_text(text=serialized["agent_response"])],
                )
            )

        state["step_count"] += 1
        return state

    def _generate_response(self, state: MasterState):
        return state

    def _proceed_reponse(self, response):
        parts = response.candidates[0].content.parts

        agent_response = response.text
        thought = ""
        for part in parts:
            if hasattr(part, "thought") and part.thought:
                thought = part.text

        return {
            "thought": thought,
            "agent_response": agent_response,
        }

    def __call__(self, prompt: str, session_id="default_session"):
        initial_state = {
            "agent_response": "",
            "chat_history": [],
            "user_prompt": prompt,
            "step_count": 0,
            "max_steps": 20,
            "user_feedback": "",
        }
        config = {"configurable": {"thread_id": session_id}}

        events = self.graph.stream(initial_state, config=config, stream_mode="values")

        for event in events:
            try:
                if event["user_feedback"]:
                    response_text = (
                        event["user_feedback"] + "\n *********************** \n"
                    )
                    yield response_text
            except Exception as e:
                print(f"Error in streaming: {e}")
