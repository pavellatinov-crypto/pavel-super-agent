from typing import TypedDict

class AgentState(TypedDict):
    user_input: str
    analysis: str
    strategy: str
    content: str
    goal: str