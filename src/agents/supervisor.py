from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage

from ..shared.config import get_env, get_gemini_client
from ..shared.memory import TravelState, AGENT_ORDER, empty_constraints
from ..shared.models import SupervisorResponse

supervisor_prompt = ChatPromptTemplate.from_messages([
    ("system",
        "You are a travel planning supervisor. Choose only the agent needed for this task. The itineray agent is always needed."
        "Agents:"
        "- flight_agent: flights, airports, airlines, routes, airfare, booking advice"
        "- hotel_agent: hotels, accommodation, neighborhoods"
        "- weather_agent: weather, climate, season, forecast, packing"
        "- budget_agent: cost, affordability, budget feasibility"
        "- itinerary_agent: integrated travel plan"
    ),
    ("human",
     "previous memory: {memory}\n"
     "user query: {query}\n",
    )
])

supervisor_llm = get_gemini_client().with_structured_output(SupervisorResponse)

def supervisor_agent(state: TravelState):
    user_query = state.get("user_query")
    memory_context = state.get("memory_context", {})
    if not user_query:
        raise ValueError("user query is required")

    try:
        prompt_input = supervisor_prompt.format_messages(
            memory=memory_context,
            query=user_query
        )

        result: SupervisorResponse = supervisor_llm.invoke(prompt_input)
        requested = result.selected_agents
        selected = [name for name in AGENT_ORDER if name in requested]
        if "itinerary_agent" not in selected:
            selected.append("itinerary_agent")

        constraints = empty_constraints()
        if isinstance(result["trip_constraints"], dict):
            constraints.update(result["trip_constraints"])

        reasoning = str(result.get("reasoning", "")).strip()

    except Exception as exc:
        selected = AGENT_ORDER.copy()
        constraints = empty_constraints()
        reasoning = "Supervisor fallback selected the full workflow."
        raise RuntimeError(f"Supervisor agent failed: {exc}") from exc  

    return {
        "supervisor_agent": result
    }


