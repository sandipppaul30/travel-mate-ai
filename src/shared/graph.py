from dataclasses import dataclass

from langgraph.graph import StateGraph, END, START
from .memory import TravelState, memory_load_agent, memory_persist_agent
from agents.guardrail import guardrail_agent, guardrail_blocked_agent
from agents.supervisor import supervisor_agent
from agents.flight import flight_agent
from agents.hotel import hotel_agent
from agents.weather import weather_agent
from agents.budget import budget_agent
from agents.itinerary import itinerary_agent
from agents.human_approval import human_approval_agent
from agents.final import final_agent
from .routing import ROUTES, route_after, route_after_guardrail, route_from_supervisor
from shared.database import init_database

@dataclass()
class TravelContext:
    user_id: str
    thread_id: str

async def build_graph():
    g = StateGraph(state_schema=TravelState, context_schema=TravelContext)

    nodes = {
        "memory_load_agent": memory_load_agent,
        "memory_persist_agent": memory_persist_agent,
        "guardrail_agent": guardrail_agent,
        "guardrail_blocked_agent": guardrail_blocked_agent,
        "supervisor_agent": supervisor_agent,
        "flight_agent": flight_agent,
        "hotel_agent": hotel_agent,
        "weather_agent": weather_agent,
        "budget_agent": budget_agent,
        "itinerary_agent": itinerary_agent,
        "human_approval_agent": human_approval_agent,
        "final_agent": final_agent
    }
    for name, agent in nodes.items():
        g.add_node(name, agent)

    g.add_edge(START, "memory_load_agent")
    g.add_edge("memory_load_agent", "guardrail_agent")
    g.add_conditional_edges("guardrail_agent", route_after_guardrail, ROUTES)
    g.add_conditional_edges("supervisor_agent", route_from_supervisor, ROUTES)

    for agent in ("flight_agent", "hotel_agent", "weather_agent", "budget_agent"):
        g.add_conditional_edges(agent, route_after(agent), ROUTES)

    g.add_edge("itinerary_agent", "human_approval_agent")
    g.add_edge("human_approval_agent", "final_agent")
    g.add_edge("final_agent", "memory_persist_agent")
    g.add_edge("memory_persist_agent", END)
    g.add_edge("guardrail_blocked_agent", END)

    checkpointer, memory_store, checkpoint_conn, memory_conn =  await init_database()

    return g.compile(checkpointer=checkpointer, store=memory_store)


    
