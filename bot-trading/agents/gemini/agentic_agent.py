import json
from typing import List
from typing_extensions import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, END
from google.genai.types import Content, Part

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

        workflow.add_edge("tools_agent", "generate_response")

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
            label = f"# Tool Agent — step {state['step_count']}"
            state["user_feedback"] = label

            response = agent(state["chat_history"], tools=[cx_connector.tools], model=state["model"])
            print("Tool Agent response:", response)
            print("*" * 20)

            parsed = self._parse_response(response)
            self._apply_parsed_response(state, parsed)

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
                text="Based on the conversation so far, write the final answer for the user. Do not use JSON."
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
