from broker_bot.tools.cx_connector import CXConnector
from master_agent.agents.agent import Agent

agent = Agent()
cx_connector = CXConnector()


class ToolAgent:
    def __call__(self, prompt: str):
        response = agent(prompt=prompt, tools=cx_connector.tools)
        return response
