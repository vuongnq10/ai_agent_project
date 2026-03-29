import json
import re
from typing_extensions import TypedDict
from typing import List

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, END

import sys
import os

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from agents_openai.agent import OpenAIAgent
from tools.openai_tools import OpenAITools

memory = InMemorySaver()
agent = OpenAIAgent()
openai_tools = OpenAITools()

class MasterState(TypedDict):
    chat_history: List[dict]
    agent_response: str
    user_prompt: str
    step_count: int
    max_steps: int
    user_feedback: str

class MasterOpenAI:
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

    def _routing(self, state: MasterState):
        response_state = (
            state.get("agent_response")
            or """```json
            {
                "type": "GENERAL_QUERY"
            }
            ```"""
        )

        # Clean and parse JSON response
        clean_str = response_state.strip().strip("`").strip("json").strip("`")
        
        try:
            data_obj = json.loads(clean_str)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', clean_str, re.DOTALL)
            if json_match:
                try:
                    data_obj = json.loads(json_match.group())
                except:
                    data_obj = {"type": "GENERAL_QUERY"}
            else:
                data_obj = {"type": "GENERAL_QUERY"}

        type_value = data_obj.get("type", "GENERAL_QUERY")

        switcher = {
            "TOOL_AGENT": "tools_agent",
            "MARKET_ANALYSIS": "analysis_agent",
            "TRADE_DECISION": "decision_agent",
            "GENERAL_QUERY": "master_agent",
            "FINAL_RESPONSE": "generate_response",
        }

        if state["step_count"] >= state["max_steps"]:
            state["user_feedback"] = "# Max steps reached, generating final response."
            return "generate_response"
        return switcher.get(type_value, "master_agent")

    def _init_flow(self, state: MasterState):
        state["user_feedback"] = "# Start the flow"
        return state

    def _call_master(self, state: MasterState):
        state["user_feedback"] = "# Master Agent Processing: " + str(
            state["step_count"]
        )
        
        if state["step_count"] == 0:
            messages = [{"role": "user", "content": state["user_prompt"]}]
            state["chat_history"] = messages
        else:
            messages = state["chat_history"] + [
                {"role": "assistant", "content": state["agent_response"]}
            ]
            state["chat_history"] = messages

        system_instruction = """
            You are a Master Agent in Agentic AI assistant that analyzes user prompts for cryptocurrency trading intentions.
            
            Classify the user's request into one of these categories:
            - TOOL_AGENT: Tools Agent to get market data and indicators.
            - TOOL_AGENT: Tools Agent to create the trade setup based on analysis and decision.
            - MARKET_ANALYSIS: Analyse Agent market conditions based on data and indicators.
            - TRADE_DECISION: Decision Agent to buy/sell or wait based on analysis.
            - GENERAL_QUERY: Generate the result of the prompt.
            - FINAL_RESPONSE: Provide the final response to the user based on the analysis and decisions made by other agents.

            Steps to follow:
            1. Get the data and indicators using TOOL_AGENT if needed.
            2. Analyze the market using MARKET_ANALYSIS if needed.
            3. Analyze again if needed.
            4. TOOL_AGENT can be called again if needed.
            5. Make a trade decision using TRADE_DECISION once analysis is sufficient.
            6. If decide to trade, use TOOL_AGENT to create the trade setup.
            7. If no trade is to be made, respond with GENERAL_QUERY or FINAL_RESPONSE

            Respond in JSON format:
            {
                "type": "CATEGORY", // One of the above categories
                "symbols": "BTC/USDT",
                "timeframes": ["1h", "4h"],
                "confidence": 0.9,
                ... additional relevant details ...
            }
            """

        response = agent(messages, system_instruction=system_instruction)

        print("Master Agent response:", response)
        print("*" * 20)

        serialized = self._process_response(response)

        if serialized["thought"]:
            state["user_feedback"] = serialized["thought"]

        if serialized["agent_response"]:
            state["agent_response"] = serialized["agent_response"]
            state["chat_history"].append({
                "role": "assistant",
                "content": serialized["agent_response"]
            })

        state["step_count"] += 1
        return state

    def _tool_agent(self, state: MasterState):
        try:
            state["user_feedback"] = "# Tool Agent Processing: " + str(
                state["step_count"]
            )
            messages = state["chat_history"]

            response = agent(messages, tools=openai_tools.tools)

            print("Tool Agent response:", response)
            print("*" * 20)

            # Handle tool calls
            if response and response.choices[0].message.tool_calls:
                for tool_call in response.choices[0].message.tool_calls:
                    function_name = tool_call.function.name
                    arguments = json.loads(tool_call.function.arguments)
                    
                    # Execute the tool
                    tool_result = openai_tools.execute_function(function_name, arguments)
                    
                    # Add tool call and result to chat history
                    state["chat_history"].append({
                        "role": "assistant",
                        "content": "",
                        "tool_calls": [tool_call.model_dump()]
                    })
                    
                    state["chat_history"].append({
                        "role": "tool",
                        "content": json.dumps(tool_result),
                        "tool_call_id": tool_call.id
                    })

            serialized = self._process_response(response)
            if serialized["thought"]:
                state["user_feedback"] = serialized["thought"]
            if serialized["agent_response"]:
                state["agent_response"] = serialized["agent_response"]
                state["chat_history"].append({
                    "role": "assistant",
                    "content": serialized["agent_response"]
                })
            else:
                state["agent_response"] = ""

            state["step_count"] += 1
            return state
        except Exception as e:
            print(f"Error in tool agent: {e}")
            state["agent_response"] = f"Error in tool execution: {e}"
            state["step_count"] += 1
            return state

    def _analyse_agent(self, state: MasterState):
        try:
            state["user_feedback"] = "# Analyse Agent Processing: " + str(
                state["step_count"]
            )
            messages = state["chat_history"]

            system_instruction = """
                You are a Analyse Agent in Agentic AI assistant that analyzes the data for cryptocurrency trading intentions.
                
                Use the data and indicators provided to analyze the market conditions.
                Provide insights on trends, key levels, and potential trade setups.
                Predict the price movement based on the analysis.
                Suggest whether to buy, sell, or wait based on the analysis.
                
                Classify the response into one of these categories:
                - TOOL_AGENT: Tools Agent to get market data and indicators.
                - TOOL_AGENT: Tools Agent to create the trade setup based on analysis and decision.
                - MARKET_ANALYSIS: Analyse Agent market conditions based on data and indicators.
                - TRADE_DECISION: Decision Agent to buy/sell or wait based on analysis.
                - GENERAL_QUERY: Generate the result of the prompt.
                - FINAL_RESPONSE: Provide the final response to the user based on the analysis and decisions made by other agents.

                Respond in JSON format:
                {
                    "type": "CATEGORY", // One of the above categories
                    "symbols": "BTC/USDT",
                    "timeframes": "4 hours" or "2 hours" or "1 hour",
                    "confidence": 0.9,
                    "current_price": "30.00",
                    "entry_price": "30.1",
                    "stop_loss": "29.00",
                    "take_profit": "32.00",
                    ... additional relevant details ...
                }
                """

            response = agent(messages, system_instruction=system_instruction)

            print("Analyse Agent response:", response)
            print("*" * 20)

            serialized = self._process_response(response)

            if serialized["thought"]:
                state["user_feedback"] = serialized["thought"]

            if serialized["agent_response"]:
                state["agent_response"] = serialized["agent_response"]
                state["chat_history"].append({
                    "role": "assistant",
                    "content": serialized["agent_response"]
                })

            state["step_count"] += 1
            return state
        except Exception as e:
            print(f"Error in Analyse Agent: {e}")
            state["agent_response"] = f"Error in analysis: {e}"
            state["step_count"] += 1
            return state

    def _decision_agent(self, state: MasterState):
        try:
            state["user_feedback"] = "# Decision Agent Processing: " + str(
                state["step_count"]
            )
            messages = state["chat_history"]

            system_instruction = """
                You are a Decision Agent in Agentic AI assistant that analyzes the data for cryptocurrency trading intentions.
                
                Use the insight of the analysis provided to make a decision on trading actions.
                Decide whether to buy, sell, or wait based on the analysis.
                If more analysis or data is needed, request it using MARKET_ANALYSIS or TOOL_AGENT.
                If decide to trade, provide a detailed trade setup including entry, stop loss, and take profit levels then call the TOOL_AGENT to execute the trade setup.
                If no trade is to be made, respond with GENERAL_QUERY or FINAL_RESPONSE

                Classify the response into one of these categories:
                - TOOL_AGENT: Tools Agent to get market data and indicators.
                - TOOL_AGENT: Tools Agent to create the trade setup based on analysis and decision.
                - MARKET_ANALYSIS: Analyse Agent market conditions based on data and indicators.
                - TRADE_DECISION: Decision Agent to buy/sell or wait based on analysis.
                - GENERAL_QUERY: Generate the result of the prompt.
                - FINAL_RESPONSE: Provide the final response to the user based on the analysis and decisions made by other agents.

                Respond in JSON format:
                {
                    "type": "CATEGORY", // One of the above categories
                    "symbols": "BTC/USDT",
                    "timeframes": ["1h", "4h"],
                    "confidence": 0.9,
                    "entry_price": "30.00",
                    "stop_loss": "29.00",
                    "take_profit": "32.00",
                    ... additional relevant details ...
                }
                """

            response = agent(messages, system_instruction=system_instruction)

            print("Decision Agent response:", response)
            print("*" * 20)

            serialized = self._process_response(response)

            if serialized["thought"]:
                state["user_feedback"] = serialized["thought"]

            if serialized["agent_response"]:
                state["agent_response"] = serialized["agent_response"]
                state["chat_history"].append({
                    "role": "assistant",
                    "content": serialized["agent_response"]
                })

            state["step_count"] += 1
            return state
        except Exception as e:
            print(f"Error in Decision Agent: {e}")
            state["agent_response"] = f"Error in decision making: {e}"
            state["step_count"] += 1
            return state

    def _generate_response(self, state: MasterState):
        state["user_feedback"] = ""
        return state

    def _process_response(self, response):
        """Process OpenAI response and extract relevant information"""
        agent_response = ""
        thought = ""

        if response and response.choices:
            message = response.choices[0].message
            if message.content:
                agent_response = message.content
                thought = f"Processing: {message.content[:100]}..."

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
            "max_steps": 10,
            "user_feedback": "",
        }
        config = {"configurable": {"thread_id": session_id}}

        events = self.graph.stream(initial_state, config=config, stream_mode="values")

        for event in events:
            try:
                print("Event:", event)
                if event.get("user_feedback"):
                    print("#" * 20)
                    print(event["user_feedback"])
                    print("#" * 20)

                    response_text = (
                        event["user_feedback"] + "\n *********************** \n"
                    )
                    yield response_text
            except Exception as e:
                print(f"Error in streaming: {e}")
                yield f"Error in streaming: {e}"
