import json
from typing import List
from typing_extensions import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, END
from google.genai.types import Content, Part, Tool, FunctionDeclaration

from agents.gemini.agent import Agent
from agents.prompts import (
    MASTER_SYSTEM_INSTRUCTION as _MASTER_SYSTEM_INSTRUCTION,
    ANALYSIS_SYSTEM_INSTRUCTION as _ANALYSIS_SYSTEM_INSTRUCTION,
    DECISION_SYSTEM_INSTRUCTION as _DECISION_SYSTEM_INSTRUCTION,
    FINAL_RESPONSE_SYSTEM as _FINAL_RESPONSE_SYSTEM,
)
from tools.cx_connector import CXConnector

# ---------------------------------------------------------------------------
# Module-level singletons
# ---------------------------------------------------------------------------
memory = InMemorySaver()
agent = Agent()
cx_connector = CXConnector()

_CX_TOOLS = Tool(
    function_declarations=[
        FunctionDeclaration(
            name="smc_analysis",
            description="Fetch live OHLCV candles from Binance and compute SMC indicators: ATR, swing highs/lows, order blocks, Fair Value Gaps, BOS, CHoCH, liquidity levels, Bollinger Bands, EMA, and RSI.",
            parameters={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Trading pair symbol (e.g., 'SOLUSDT', 'BTCUSDT').",
                    },
                    "timeframe": {
                        "type": "string",
                        "description": "Candle timeframe (e.g., '30m', '1h', '4h'). Defaults to '1h'.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of candles to fetch. Defaults to 200.",
                    },
                },
                "required": ["symbol"],
            },
        ),
        FunctionDeclaration(
            name="create_order",
            description="Place a 10x leverage bracket order (entry + TP + SL) on Binance Futures.",
            parameters={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "The trading pair symbol (e.g., 'SOLUSDT').",
                    },
                    "current_price": {
                        "type": "number",
                        "description": "Current market price for the symbol.",
                    },
                    "side": {
                        "type": "string",
                        "description": "Type of order (e.g., 'BUY', 'SELL').",
                    },
                    "entry": {
                        "type": "number",
                        "description": "Entry price for the trade.",
                    },
                    "stop_loss": {
                        "type": "string",
                        "description": "Stop loss price for the trade. String representation of a float.",
                    },
                    "take_profit": {
                        "type": "string",
                        "description": "Take profit price for the trade. String representation of a float.",
                    },
                },
                "required": [
                    "symbol",
                    "side",
                    "entry",
                    "take_profit",
                    "stop_loss",
                ],
            },
        ),
    ],
)

# Separator appended after every streamed user_feedback chunk
_FEEDBACK_SEPARATOR = "\n *********************** \n"

# Routing map: JSON "type" value -> graph node name
_ROUTE_MAP = {
    "TOOL_AGENT": "tools_agent",
    "MARKET_ANALYSIS": "analysis_agent",
    "TRADE_DECISION": "decision_agent",
    "GENERAL_QUERY": "master_agent",
    "FINAL_RESPONSE": "generate_response",
}

# Fallback agent_response used when none is present in state
_DEFAULT_RESPONSE = '{"type": "GENERAL_QUERY"}'


# ---------------------------------------------------------------------------
# LangGraph state
# ---------------------------------------------------------------------------
class MasterState(TypedDict):
    chat_history: List[Content]
    agent_response: str
    user_prompt: str
    step_count: int
    max_steps: int
    user_feedback: str
    model: str


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------
class MasterGemini:
    def __init__(self):
        self.graph = self._build_graph()

    # ------------------------------------------------------------------
    # Graph construction
    # ------------------------------------------------------------------
    def _build_graph(self):
        workflow = StateGraph(MasterState)

        workflow.add_node("init_flow", self._init_flow)
        workflow.add_node("master_agent", self._call_master)
        workflow.add_node("tools_agent", self._tool_agent)
        workflow.add_node("analysis_agent", self._analyse_agent)
        workflow.add_node("decision_agent", self._decision_agent)
        workflow.add_node("generate_response", self._generate_response)

        workflow.add_edge("init_flow", "master_agent")

        # master_agent → any node
        workflow.add_conditional_edges(
            "master_agent",
            self._routing,
            {
                "master_agent": "master_agent",
                "tools_agent": "tools_agent",
                "analysis_agent": "analysis_agent",
                "decision_agent": "decision_agent",
                "generate_response": "generate_response",
            },
        )

        # tools_agent → master_agent only (generate_response on max_steps)
        workflow.add_conditional_edges(
            "tools_agent",
            self._route_tools,
            {
                "master_agent": "master_agent",
                "analysis_agent": "analysis_agent",
                "generate_response": "generate_response",
            },
        )

        # analysis_agent → decision_agent, tools_agent (fetch data), master_agent, or wrap up
        workflow.add_conditional_edges(
            "analysis_agent",
            self._route_analysis,
            {
                "decision_agent": "decision_agent",
                "tools_agent": "tools_agent",
                "master_agent": "master_agent",
                "generate_response": "generate_response",
            },
        )

        # decision_agent → any node
        workflow.add_conditional_edges(
            "decision_agent",
            self._routing,
            {
                "tools_agent": "tools_agent",
                "analysis_agent": "analysis_agent",
                "decision_agent": "decision_agent",
                "master_agent": "master_agent",
                "generate_response": "generate_response",
            },
        )

        workflow.set_entry_point("init_flow")
        workflow.add_edge("generate_response", END)

        return workflow.compile(checkpointer=memory)

    # ------------------------------------------------------------------
    # Routers
    # ------------------------------------------------------------------
    def _routing(self, state: MasterState) -> str:
        if state["step_count"] >= state["max_steps"]:
            return "generate_response"

        raw = state.get("agent_response") or _DEFAULT_RESPONSE
        clean = raw.strip("`").removeprefix("json").strip()

        try:
            data = json.loads(clean)
        except json.JSONDecodeError:
            return "master_agent"

        type_value = data.get("type", "GENERAL_QUERY")
        return _ROUTE_MAP.get(type_value, "master_agent")

    def _route_tools(self, state: MasterState) -> str:
        if state["step_count"] >= state["max_steps"]:
            return "generate_response"

        raw = state.get("agent_response") or _DEFAULT_RESPONSE
        clean = raw.strip("`").removeprefix("json").strip()
        try:
            data = json.loads(clean)
        except json.JSONDecodeError:
            return "master_agent"

        type_value = data.get("type", "GENERAL_QUERY")
        route = _ROUTE_MAP.get(type_value, "master_agent")
        # tools_agent can only reach these three nodes
        if route not in {"analysis_agent", "master_agent", "generate_response"}:
            return "master_agent"
        return route

    def _route_analysis(self, state: MasterState) -> str:
        if state["step_count"] >= state["max_steps"]:
            return "generate_response"

        raw = state.get("agent_response") or _DEFAULT_RESPONSE
        clean = raw.strip("`").removeprefix("json").strip()
        try:
            data = json.loads(clean)
        except json.JSONDecodeError:
            return "master_agent"

        type_value = data.get("type", "GENERAL_QUERY")
        if type_value == "TRADE_DECISION":
            return "decision_agent"
        if type_value == "TOOL_AGENT":
            return "tools_agent"
        if type_value == "FINAL_RESPONSE":
            return "generate_response"
        return "master_agent"

    # ------------------------------------------------------------------
    # Helper: parse thought + response text out of a Gemini response
    # ------------------------------------------------------------------
    def _parse_response(self, response) -> dict:
        """Return {"thought": str, "agent_response": str} from a Gemini response."""
        parts = response.candidates[0].content.parts

        thought = ""
        agent_response = ""

        for part in parts:
            if hasattr(part, "thought") and part.thought:
                thought = part.text.rstrip()
            else:
                agent_response += part.text if hasattr(part, "text") and part.text else ""

        return {"thought": thought, "agent_response": agent_response.strip()}

    # ------------------------------------------------------------------
    # Helper: apply parsed response fields back onto state
    # ------------------------------------------------------------------
    def _apply_parsed_response(
        self, state: MasterState, parsed: dict, label: str = ""
    ) -> None:
        """Mutate state in-place with thought and agent_response from parsed.

        Always updates user_feedback so the streamed output shows the actual
        agent response after every step, not just the step header.
        """
        response_text = parsed["thought"] or parsed["agent_response"]
        if response_text:
            header = f"{label}\n\n" if label else ""
            state["user_feedback"] = header + response_text

        if parsed["agent_response"]:
            state["agent_response"] = parsed["agent_response"]
            state["chat_history"].append(
                Content(
                    role="user",
                    parts=[Part.from_text(text=parsed["agent_response"])],
                )
            )

    # ------------------------------------------------------------------
    # Nodes
    # ------------------------------------------------------------------
    def _init_flow(self, state: MasterState) -> MasterState:
        state["user_feedback"] = "# Starting flow"
        return state

    def _call_master(self, state: MasterState) -> MasterState:
        label = f"# Master Agent — step {state['step_count']}"
        state["user_feedback"] = label

        if state["step_count"] == 0:
            state["chat_history"] = [
                Content(role="user", parts=[Part.from_text(text=state["user_prompt"])])
            ]
        else:
            state["chat_history"].append(
                Content(role="user", parts=[Part.from_text(text=state["agent_response"])])
            )

        response = agent(state["chat_history"], system_instruction=_MASTER_SYSTEM_INSTRUCTION, model=state["model"])
        print("Master Agent response:", response)
        print("*" * 20)

        self._apply_parsed_response(state, self._parse_response(response), label=label)
        state["step_count"] += 1
        return state

    def _tool_agent(self, state: MasterState) -> MasterState:
        try:
            label = f"# Tool Agent — step {state['step_count']}"
            state["user_feedback"] = label

            response = agent(state["chat_history"], tools=[_CX_TOOLS], model=state["model"])
            print("Tool Agent response:", response)
            print("*" * 20)

            parsed = self._parse_response(response)
            self._apply_parsed_response(state, parsed, label=label)

            # Execute any function calls returned by the model
            candidate = response.candidates[0]
            for part in candidate.content.parts:
                if hasattr(part, "function_call") and part.function_call:
                    func_call = part.function_call
                    tool_func = getattr(cx_connector, func_call.name)
                    tool_result = tool_func(**dict(func_call.args))
                    tool_result_str = json.dumps(tool_result)
                    state["chat_history"].append(
                        Content(
                            role="user",
                            parts=[
                                Part.from_function_response(
                                    name=func_call.name,
                                    response=tool_result,
                                )
                            ],
                        )
                    )
                    state["user_feedback"] = f"{label}\n\n**Tool executed:** `{func_call.name}`\n\n{tool_result_str}"
                    # smc_analysis → continue to analysis_agent; any other tool → wrap up
                    next_type = "MARKET_ANALYSIS" if func_call.name == "smc_analysis" else "FINAL_RESPONSE"
                    state["agent_response"] = json.dumps({"type": next_type})

            state["step_count"] += 1
            return state
        except Exception as e:
            print(f"Error in Tool Agent: {e}")
            return state

    def _analyse_agent(self, state: MasterState) -> MasterState:
        try:
            label = f"# Analysis Agent — step {state['step_count']}"
            state["user_feedback"] = label

            response = agent(
                state["chat_history"],
                system_instruction=_ANALYSIS_SYSTEM_INSTRUCTION,
                model=state["model"],
            )
            print("Analysis Agent response:", response)
            print("*" * 20)

            self._apply_parsed_response(state, self._parse_response(response), label=label)
            state["step_count"] += 1
            return state
        except Exception as e:
            print(f"Error in Analysis Agent: {e}")
            return state

    def _decision_agent(self, state: MasterState) -> MasterState:
        try:
            label = f"# Decision Agent — step {state['step_count']}"
            state["user_feedback"] = label

            response = agent(
                state["chat_history"],
                system_instruction=_DECISION_SYSTEM_INSTRUCTION,
                model=state["model"],
            )
            print("Decision Agent response:", response)
            print("*" * 20)

            self._apply_parsed_response(state, self._parse_response(response), label=label)
            state["step_count"] += 1
            return state
        except Exception as e:
            print(f"Error in Decision Agent: {e}")
            return state

    def _generate_response(self, state: MasterState) -> MasterState:
        raw = state.get("agent_response", "").strip()
        cleaned = raw.strip("`").removeprefix("json").strip()
        is_routing_json = False
        try:
            data = json.loads(cleaned)
            if isinstance(data, dict) and "type" in data:
                is_routing_json = True
        except (json.JSONDecodeError, ValueError):
            pass

        if is_routing_json or not raw:
            history = list(state.get("chat_history", []))
            history.append(Content(role="user", parts=[Part.from_text(
                text="Based on the conversation so far, write a clear, concise final answer for the user. Do not use JSON — write in plain prose."
            )]))
            response = agent(history, system_instruction=_FINAL_RESPONSE_SYSTEM, model=state["model"])
            parsed = self._parse_response(response)
            state["user_feedback"] = parsed["agent_response"] or raw
        else:
            state["user_feedback"] = raw
        return state

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------
    def __call__(self, prompt: str, session_id: str = "default_session", model: str = "gemini-2.5-flash"):
        initial_state: MasterState = {
            "agent_response": "",
            "chat_history": [],
            "user_prompt": prompt,
            "step_count": 0,
            "max_steps": 10,
            "user_feedback": "",
            "model": model,
        }
        graph_config = {"configurable": {"thread_id": session_id}}

        for event in self.graph.stream(initial_state, config=graph_config, stream_mode="values"):
            try:
                print("Event:", event)
                feedback = event.get("user_feedback")
                if feedback:
                    print("#" * 20)
                    print(feedback)
                    print("#" * 20)
                    yield feedback + _FEEDBACK_SEPARATOR
            except Exception as e:
                print(f"Error in streaming: {e}")
                yield f"Error in streaming: {e}"
