
from langchain_core.prompts import ChatPromptTemplate
from ..shared.config import get_env, get_gemini_client
from ..shared.memory import TravelState
from ..shared.models import ItineraryResponse
from ..mcp_data.client_mcp import call_tool

itinerary_agent_prompt = ChatPromptTemplate.from_messages([
    ("system", 
    "You are a travel itinerary expert. \n"
    "Prepare a detailed itinerary based on the following parameters:\n"
    "1. Day-by-day plan\n"
    "2. Activities\n"
    "3. Recommendations\n"
    "Return the response based on the provided itinerary information. If the information is insufficient, respond with 'Itinerary information unavailable'.\n"
    ),
    ("human",
    "User Query: {query}\n"
    "Trip Constraints: {constraints}\n"
    "Flight Results: {flight_results}\n"
    "Hotel Results: {hotel_results}\n"
    "Weather Results: {weather_results}\n"
    "Budget Results: {budget_results}\n"    
    )
])

itinerary_llm = get_gemini_client().with_structured_output(ItineraryResponse)

def itinerary_agent(state: TravelState):
    user_query = state.get("user_query")
    trip_constraints = state.get("trip_constraints")
    flight_results = state.get("flight_results")
    hotel_results = state.get("hotel_results")
    weather_results = state.get("weather_results")
    budget_results = state.get("budget_results")

    try:
        prompt_input = itinerary_agent_prompt.format_messages(
            query=user_query,
            constraints=trip_constraints,
            flight_results=flight_results,
            hotel_results=hotel_results,
            weather_results=weather_results,
            budget_results=budget_results
        )

        result: ItineraryResponse = itinerary_llm.invoke(prompt_input)

    except Exception as exc:
        raise RuntimeError(f"Itinerary agent failed: {exc}") from exc

    return {"itinerary_details": result.itinerary_details}