import asyncio

from langchain_core.prompts import ChatPromptTemplate

from ..shared.config import get_env, get_gemini_client
from ..shared.memory import TravelState
from ..shared.models import FlightResponse
from ..mcp_data.client_mcp import call_tool

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
     "Airport Information: {airports}\n"
     "Airline Information: {airlines}\n"
    )
])

flight_llm = get_gemini_client().with_structured_output(FlightResponse)

def flight_agent(state: TravelState):
    user_query = state.get("user_query")
    if not user_query:
        raise ValueError("user query is required")
    
    try:
        prompt_input = flight_agent_prompt.format_messages(
            query=user_query,
            airports=asyncio.run(call_tool("aviationstack", query=user_query)),
            airlines=asyncio.run(call_tool("aviationstack", query=user_query))
        )

        result: FlightResponse = flight_llm.invoke(prompt_input)
        
    except Exception as exc:
        raise RuntimeError(f"Flight agent failed: {exc}") from exc

    return {"flight_results": result.flight_details}
