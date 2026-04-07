import json
from typing import List
from typing_extensions import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, END
from google.genai.types import Content, Part

from agents.gemini.agent import Agent
from tools.cx_connector import CXConnector

# ---------------------------------------------------------------------------
# Module-level singletons
# ---------------------------------------------------------------------------
memory = InMemorySaver()
agent = Agent()
cx_connector = CXConnector()

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
# System instructions
# ---------------------------------------------------------------------------
_MASTER_SYSTEM_INSTRUCTION = """
You are the Master Agent of an AI cryptocurrency trading system.

The user message contains pre-computed SMC (Smart Money Concepts) indicators
sent directly from the frontend — you do NOT need to fetch market data.

Your job is to classify what the conversation needs next:
- MARKET_ANALYSIS: Analyze the SMC indicators provided by the user.
- TRADE_DECISION: Make a buy/sell/wait decision based on completed analysis.
- TOOL_AGENT: Place a trade order on Binance (only after a trade is decided).
- GENERAL_QUERY: Answer a general question that does not require analysis.
- FINAL_RESPONSE: Deliver the final answer to the user.

Standard flow for a trade request:
1. Route to MARKET_ANALYSIS to interpret the provided indicators.
2. Route to TRADE_DECISION once analysis is complete.
3. If a trade is decided (including a limit order waiting for a pullback),
   route to TOOL_AGENT to place the order.
4. Route to FINAL_RESPONSE to deliver the outcome.

Respond in JSON format:
{
    "type": "CATEGORY",
    "symbol": "BTCUSDT",
    "timeframe": "1h",
    "confidence": 0.9,
    ... additional relevant details ...
}
"""

_ANALYSIS_SYSTEM_INSTRUCTION = """
You are the Analysis Agent of an AI cryptocurrency trading system.

The conversation contains pre-computed SMC indicators (order blocks, FVGs,
BOS/CHoCH, liquidity levels, swing highs/lows, EMA, RSI, Bollinger Bands, etc.)
sent from the frontend. Do NOT request more data — analyze what is provided.

Your responsibilities:
- Identify market structure (bullish/bearish/ranging) from BOS and CHoCH signals.
- Locate key order blocks and fair value gaps that price may react to.
- Assess liquidity sweeps and where smart money may be targeting.
- Evaluate EMA alignment, RSI momentum, and Bollinger Band position.
- Determine the dominant bias and the highest-probability trade direction.
- Suggest a specific entry zone, stop loss, and take profit based on the levels.

Route your response to:
- MARKET_ANALYSIS: If more in-depth analysis of a specific aspect is needed.
- TRADE_DECISION: Once you have a clear directional bias and trade setup.
- FINAL_RESPONSE: If the market is unclear and no trade setup is valid.

Respond in JSON format:
{
    "type": "CATEGORY",
    "symbol": "BTCUSDT",
    "timeframe": "1h",
    "bias": "bullish" | "bearish" | "neutral",
    "confidence": 0.9,
    "current_price": "30.00",
    "entry_price": "30.10",
    "stop_loss": "29.00",
    "take_profit": "32.00",
    "reasoning": "brief summary of key confluences",
    ... additional relevant details ...
}
"""

_DECISION_SYSTEM_INSTRUCTION = """
You are the Decision Agent of an AI cryptocurrency trading system.

You receive the analysis from the Analysis Agent and must make a final
trading decision: BUY, SELL, or WAIT.

Decision rules:
- Only decide BUY or SELL when there are at least 2 strong confluences
  (e.g. bullish order block + FVG fill + RSI oversold, or BOS confirmation
  + EMA stack alignment + liquidity sweep).
- If confluences are weak, conflicting, or market structure is unclear → WAIT.
- Never chase price; entry must be at a defined level (order block, FVG, or
  a retest of a broken structure level).
- Stop loss must be placed beyond the invalidation level (below OB for longs,
  above OB for shorts).
- Take profit must target the next liquidity pool or significant swing level.

Pullback / limit-order entries (IMPORTANT):
- It is completely acceptable — and often preferable — to place a LIMIT order
  at a key level below (for longs) or above (for shorts) the current price,
  anticipating a retracement before the move continues.
- If the market structure is clearly bullish or bearish but price has not yet
  pulled back to a confluence zone (order block, FVG, discount/premium area),
  do NOT wait or skip the trade. Instead, place the BUY or SELL limit order
  at that key level and let price come to you.
- Do not hesitate to route to TOOL_AGENT with a limit entry price that is
  better than the current market price when a pullback setup is evident.
  The order will sit on the book and fill if price retraces to the level.

Route your response to:
- MARKET_ANALYSIS: If the analysis is insufficient to make a confident decision.
- TOOL_AGENT: If placing a BUY or SELL trade (include full order details).
- FINAL_RESPONSE: If the decision is WAIT or no valid setup exists.

Respond in JSON format:
{
    "type": "CATEGORY",
    "symbol": "BTCUSDT",
    "side": "BUY" | "SELL" | "WAIT",
    "confidence": 0.9,
    "entry": 30.00,
    "stop_loss": "29.00",
    "take_profit": "32.00",
    "reasoning": "key confluences that drove the decision",
    ... additional relevant details ...
}
"""


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

        # init_flow always proceeds to master_agent
        workflow.add_edge("init_flow", "master_agent")

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

        workflow.add_conditional_edges(
            "tools_agent",
            self._routing,
            {
                "analysis_agent": "analysis_agent",
                "decision_agent": "decision_agent",
                "master_agent": "master_agent",
                "generate_response": "generate_response",
            },
        )

        workflow.add_conditional_edges(
            "analysis_agent",
            self._routing,
            {
                "tools_agent": "tools_agent",
                "analysis_agent": "analysis_agent",
                "decision_agent": "decision_agent",
                "master_agent": "master_agent",
                "generate_response": "generate_response",
            },
        )

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
    # Router
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

    # ------------------------------------------------------------------
    # Helper: parse thought + response text out of a Gemini response
    # ------------------------------------------------------------------
    def _parse_response(self, response) -> dict:
        """Return ``{"thought": str, "agent_response": str}`` from a Gemini response."""
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
    def _apply_parsed_response(self, state: MasterState, parsed: dict) -> None:
        """Mutate *state* in-place with thought and agent_response from *parsed*."""
        if parsed["thought"]:
            state["user_feedback"] = parsed["thought"]
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
        state["user_feedback"] = f"# Master Agent — step {state['step_count']}"

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

        self._apply_parsed_response(state, self._parse_response(response))
        state["step_count"] += 1
        return state

    def _tool_agent(self, state: MasterState) -> MasterState:
        try:
            state["user_feedback"] = f"# Tool Agent — step {state['step_count']}"

            response = agent(state["chat_history"], tools=[cx_connector.tools], model=state["model"])
            print("Tool Agent response:", response)
            print("*" * 20)

            parsed = self._parse_response(response)
            self._apply_parsed_response(state, parsed)

            if not parsed["agent_response"]:
                state["agent_response"] = ""

            # Execute any function calls returned by the model
            candidate = response.candidates[0]
            for part in candidate.content.parts:
                if hasattr(part, "function_call") and part.function_call:
                    func_call = part.function_call
                    tool_func = getattr(cx_connector, func_call.name)
                    tool_result = tool_func(**dict(func_call.args))
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

            state["step_count"] += 1
            return state
        except Exception as e:
            print(f"Error in Tool Agent: {e}")
            return state

    def _analyse_agent(self, state: MasterState) -> MasterState:
        try:
            state["user_feedback"] = f"# Analysis Agent — step {state['step_count']}"

            response = agent(
                state["chat_history"],
                system_instruction=_ANALYSIS_SYSTEM_INSTRUCTION,
                model=state["model"],
            )
            print("Analysis Agent response:", response)
            print("*" * 20)

            self._apply_parsed_response(state, self._parse_response(response))
            state["step_count"] += 1
            return state
        except Exception as e:
            print(f"Error in Analysis Agent: {e}")
            return state

    def _decision_agent(self, state: MasterState) -> MasterState:
        try:
            state["user_feedback"] = f"# Decision Agent — step {state['step_count']}"

            response = agent(
                state["chat_history"],
                system_instruction=_DECISION_SYSTEM_INSTRUCTION,
                model=state["model"],
            )
            print("Decision Agent response:", response)
            print("*" * 20)

            self._apply_parsed_response(state, self._parse_response(response))
            state["step_count"] += 1
            return state
        except Exception as e:
            print(f"Error in Decision Agent: {e}")
            return state

    def _generate_response(self, state: MasterState) -> MasterState:
        state["user_feedback"] = ""
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
