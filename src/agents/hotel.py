import asyncio

from langchain_core.prompts import ChatPromptTemplate
from ..shared.config import get_env, get_gemini_client
from ..shared.memory import TravelState
from ..shared.models import HotelResponse
from ..mcp_data.client_mcp import call_tool

hotel_agent_prompt = ChatPromptTemplate.from_messages([
    ("system", 
    "You are a travel hotel expert. \n"
    "Search below parameters:\n"
    "1. Hotel location\n"
    "2. Amenities offered\n"
    "3. Pricing range\n"
    "4. Booking advice\n"
    "Return the response based on the user query and the provided hotel information. If the information is insufficient, respond with 'Hotel information unavailable'.\n"
    ),
    ("human",
     "User Query: {query}\n"
     "Hotel Information: {hotels}\n"
    )
])

hotel_llm = get_gemini_client().with_structured_output(HotelResponse)

def hotel_agent(state: TravelState):
    user_query = state.get("user_query")
    if not user_query:
        raise ValueError("user query is required")

    try:
        prompt_input = hotel_agent_prompt.format_messages(
            query = user_query,
            hotels = asyncio.run(call_tool("tavily", query=user_query))
        )

        result: HotelResponse = hotel_llm.invoke(prompt_input)

    except Exception as exc:
        raise RuntimeError(f"Hotel agent failed: {exc}") from exc

    return {"hotel_results": result.hotel_details}