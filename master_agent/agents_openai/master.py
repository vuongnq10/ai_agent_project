from typing_extensions import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, END
from master_agent.agents_openai.openai import OpenAIAgent

# from openai import OpenAI

memory = InMemorySaver()
open_ai = OpenAIAgent()


class MasterState(TypedDict):
    next_step: str
    current_step: int
    max_steps: int
    user_prompt: str
    user_feedback: str


class MasterOpenAI:
    def __init__(self):
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(MasterState)
        workflow.add_node("init_flow", self._init_flow)
        workflow.add_node("master", self._master)
        workflow.add_node("finalize_flow", self._finalize_flow)

        workflow.add_conditional_edges(
            "init_flow",
            self._routing,
            {
                "master": "master",
            },
        )

        workflow.add_conditional_edges(
            "master",
            self._routing,
            {
                "finalize_flow": "finalize_flow",
            },
        )

        workflow.set_entry_point("init_flow")
        workflow.add_edge("finalize_flow", END)
        return workflow.compile(checkpointer=memory)

    def _init_flow(self, state: MasterState):
        state["user_feedback"] = "# Start the flow - Open AI\n"
        return state

    def _routing(self, state: MasterState):
        next_step = state["next_step"]
        switcher = {
            "MASTER_AGENT": "master",
            "FINAL_RESPONSE": "finalize_flow",
        }

        return switcher.get(next_step, "master")

    def _master(self, state: MasterState):
        user_prompt = state["user_prompt"]

        response = open_ai(user_prompt)

        state["user_feedback"] = response.output_text
        state["next_step"] = "FINAL_RESPONSE"
        return state

    def _finalize_flow(self, state: MasterState):
        state["user_feedback"] = ""
        return state

    def __call__(self, prompt: str, session_id="default_session"):

        initial_state: MasterState = {
            "next_step": "MASTER_AGENT",
            "current_step": 0,
            "max_steps": 5,
            "user_prompt": prompt,
            "user_feedback": "",
        }
        config = {"configurable": {"thread_id": session_id}}

        events = self.graph.stream(initial_state, config=config, stream_mode="values")
        for event in events:
            if event.get("user_feedback"):
                response_text = event["user_feedback"] + "\n *********************** \n"
                yield response_text
