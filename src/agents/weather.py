import asyncio

from langchain_core.prompts import ChatPromptTemplate
from ..shared.config import get_env, get_gemini_client
from ..shared.memory import TravelState
from ..shared.models import WeatherResponse, Destination
from ..mcp_data.client_mcp import call_tool

weather_agent_prompt = ChatPromptTemplate.from_messages([
    ("system", 
    "You are a travel weather expert. \n"
    "Search below parameters:\n"
    "1. Current weather conditions\n"
    "2. Temperature\n"
    "3. Humidity\n"
    "4. Wind speed\n"
    "5. Forecast for the next few days\n"
    "Return the response based on the provided present weather information and forecast. If the information is insufficient, respond with 'Weather information unavailable'.\n"
    ),
    ("human",
     "Present Weather Information: {weather}\n"
     "Weather Forecast: {forecast}\n"   
    )   
])

destination_agent_prompt = ChatPromptTemplate.from_messages([
    ("system", 
    "messages=You are a travel destination expert. \n"
    "Extract only the destination city or country from the user query. If no destination is found, respond with 'Destination not found'.\n"
    ),
    ("human",
     "User Query: {query}\n"
    )
])

destination_llm = get_gemini_client().with_structured_output(Destination)
weather_llm = get_gemini_client().with_structured_output(WeatherResponse)

def extract_destination(state: TravelState):
    user_query = state.get("user_query")
    if not user_query:
        raise ValueError("user query is required")

    try:
        prompt_input = destination_agent_prompt.format_messages(
            query = user_query
        )

        result: Destination = destination_llm.invoke(prompt_input)

    except Exception as exc:
        raise RuntimeError(f"Destination extraction failed: {exc}") from exc

    return {"destination": result.name}

def weather_agent(state:TravelState):
    destination = extract_destination(state).get("destination")
    try:
        prompt_input = weather_agent_prompt.format_messages(
            weather = asyncio.run(call_tool("weather", query=destination)),
            forecast = asyncio.run(call_tool("weather", query=destination, forecast=True))
        )

        result: WeatherResponse = weather_llm.invoke(prompt_input)

    except Exception as exc:
        raise RuntimeError(f"Weather agent failed: {exc}") from exc

    return {"weather_results": result.weather_details}