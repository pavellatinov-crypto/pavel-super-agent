from langgraph.graph import StateGraph, END

from state import AgentState
from agents.analyst import analyst
from agents.strategist import strategist
from agents.content_creator import content_creator
from agents.controller import controller

builder = StateGraph(AgentState)

builder.add_node("analyst", analyst)
builder.add_node("strategist", strategist)
builder.add_node("content_creator", content_creator)
builder.add_node("controller", controller)

builder.set_entry_point("analyst")

builder.add_edge("analyst", "strategist")
builder.add_edge("strategist", "content_creator")
builder.add_edge("content_creator", "controller")
builder.add_edge("controller", END)

graph = builder.compile()
