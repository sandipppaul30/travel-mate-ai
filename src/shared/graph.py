from dataclasses import dataclass

from langgraph.graph import StateGraph, END, START
from .memory import TravelState, memory_load_agent, memory_persist_agent
from ..agents.guardrail import guardrail_agent, guardrail_blocked_agent
from ..agents.supervisor import supervisor_agent
from ..agents.flight import flight_agent
from ..agents.hotel import hotel_agent
from ..agents.weather import weather_agent
from ..agents.budget import budget_agent
from ..agents.itinerary import itinerary_agent
from ..agents.human_approval import human_approval_agent
from ..agents.final import final_agent
from .routing import ROUTES, route_after, route_after_guardrail, route_from_supervisor
from ..shared.database import checkpointer, memory_store

@dataclass()
class TravelContext:
    user_id: str
    thread_id: str

def build_graph():
    g = StateGraph(state_schema=TravelState, context_schema=TravelContext)

    nodes = {
        "memory_load": memory_load_agent,
        "memory_persist": memory_persist_agent,
        "guardrail": guardrail_agent,
        "guardrail_blocked": guardrail_blocked_agent,
        "supervisor": supervisor_agent,
        "flight": flight_agent,
        "hotel": hotel_agent,
        "weather": weather_agent,
        "budget": budget_agent,
        "itinerary": itinerary_agent,
        "human_approval": human_approval_agent,
        "final": final_agent
    }
    for name, agent in nodes.items():
        g.add_node(name, agent)

    g.add_node(START, "memory_load")
    g.add_edge("memory_load", "guardrail")
    g.add_conditional_edges("guardrail", route_after_guardrail, ROUTES)
    g.add_conditional_edges("supervisor", route_from_supervisor, ROUTES)

    for agent in ("flight_agent", "hotel_agent", "weather_agent", "budget_agent"):
        g.add_conditional_edges(agent, route_after(agent), ROUTES)

    g.add_edge("itinerary", "human_approval")
    g.add_edge("human_approval", "final_agent")
    g.add_edge("final_agent", "memory_persist")
    g.add_edge("memory_persist", END)
    g.add_edge("guardrail_blocked", END)

    return g.compile(checkpointer=checkpointer, store=memory_store)

travel_graph = build_graph()

    
