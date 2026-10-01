from .memory import AGENT_ORDER, TravelState

ROUTES = {name: name for name in AGENT_ORDER}
ROUTES |= {
    "guardrail_blocked": "guardrail_blocked",
    "supervisor": "supervisor",
}

def selected_agents(state: TravelState) -> list[str]:

    selected = set(state.get("selected_agents", []))
    return [agent for agent in AGENT_ORDER if agent in selected]

def route_after_guardrail(state: TravelState) -> str:

    return "supervisor" if state.get("guardrail_allowed", True) else "guardrail_blocked"

def route_from_supervisor(state: TravelState) -> str:

    agents = selected_agents(state)
    return agents[0] if agents else "itinerary_agent"

def route_after(agent: str):

    later = tuple(AGENT_ORDER[AGENT_ORDER.index(agent) + 1:])

    def router(state: TravelState) -> str:

        agents = selected_agents(state)
        if agent not in agents:
            return "itinerary_agent"
        return next((name for name in later if name in agents), "itinerary_agent")

    return router
        