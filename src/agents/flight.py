import asyncio
import json
from langchain_core.prompts import ChatPromptTemplate

from shared.config import get_env, get_gemini_client
from shared.memory import TravelState
from shared.models import FlightResponse
from mcp_data.client_mcp import call_tool

MAX_CONTEXT_CHARS = int(get_env("MAX_CONTEXT_CHARS"))

flight_agent_prompt = ChatPromptTemplate.from_messages([
    ("system", 
    "You are a travel flight expert. \n"
    "Search below parameters:\n"
    "1. Likely departure airport\n"
    "2. Likely arrival airport\n"
    "3. Airlines serving the route\n"
    "4. Typical flight duration\n"
    "5. Estimated airfare range\n"
    "6. Peak season pricing warning\n"
    "7. Booking advice\n"
    "Return the response based on the user query and the provided airport and airline information. If the information is insufficient, respond with 'Flight information unavailable'.\n"
    ),
    ("human",
     "User Query: {query}\n"
     "Airline Information: {airlines}\n"
    )
])

flight_llm = get_gemini_client().with_structured_output(FlightResponse)

def get_iata_code(response):
    if not response:
        raise ValueError("Airport response is empty or None")

    """Return the iataCode of the first large_airport in an MCP response."""
    data = json.loads(response) if isinstance(response, str) else response
    airports = data.get("airports", [])

    # First large_airport
    for a in airports:
        if a.get("type") == "large_airport" and a.get("iataCode"):
            return a["iataCode"]

    # Fallback: first airport that has an IATA code
    for a in airports:
        if a.get("iataCode"):
            return a["iataCode"]

    return None

async def flight_agent(state: TravelState):
    user_query = state.get("user_query")
    if not user_query:
        raise ValueError("user query is required")

    origin = state.get("trip_constraints", {}).get("origin", "")
    destination = state.get("trip_constraints", {}).get("destination", "")
    duration = state.get("trip_constraints", {}).get("duration", "")
    start_date = state.get("trip_constraints", {}).get("start_date", "")
    end_date = state.get("trip_constraints", {}).get("end_date", "")
    adult_count = state.get("trip_constraints", {}).get("adult_count", 0)
    child_count = state.get("trip_constraints", {}).get("child_count", 0)

    try:
        departure, arrival = await asyncio.gather(
            call_tool("ourairports-mcp-server", query=f"{origin}"),
            call_tool("ourairports-mcp-server", query=f"{destination}"),
        )  

        departure_iata = get_iata_code(departure)
        arrival_iata = get_iata_code(arrival)

        airlines = await call_tool(
            "find_best_flight", 
            departure_id=departure_iata, 
            arrival_id=arrival_iata,
            outbound_date=start_date,
            return_date=end_date,
            adults=adult_count,
            children=child_count,
            nonstop_only=True,
            include_return_flight=True,
            api_key=get_env("SERPAPI_API_KEY")  
        )

        prompt_input = flight_agent_prompt.format_messages(
            query=user_query,
            airlines=f"{airlines}"
        )

        result: FlightResponse = await flight_llm.ainvoke(prompt_input)
        
    except Exception as exc:
        raise RuntimeError(f"Flight agent failed: {exc}") from exc

    return {"flight_results": result.flight_details}
