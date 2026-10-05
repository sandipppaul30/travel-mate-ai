

from langchain_core.prompts import ChatPromptTemplate
from ..shared.config import get_env, get_gemini_client
from ..shared.memory import TravelState
from ..shared.models import BudgetResponse
from ..mcp_data.client_mcp import call_tool

budget_agent_prompt = ChatPromptTemplate.from_messages([
    ("system", 
    "You are a travel budget expert. \n"
    "Prepare budget based on the following parameters:\n"
    "1. Estimated costs for flights\n"
    "2. Estimated costs for hotels\n"
    "3. Estimated costs for meals\n"
    "4. Estimated costs for activities\n"
    "5. Any additional expenses\n"
    "Return the response based on the provided budget information. If the information is insufficient, respond with 'Budget information unavailable'.\n"
    ),
    ("human",
    "User Query: {query}\n"
    "Trip Constraints: {constraints}\n"
    "Flight Results: {flight_results}\n"
    "Hotel Results: {hotel_results}\n"
    "Weather Results: {weather_results}\n"
    )
])

budget_llm = get_gemini_client().with_structured_output(BudgetResponse)

def budget_agent(state: TravelState):

    user_query = state.get("user_query")
    trip_constraints = state.get("trip_constraints")
    flight_results = state.get("flight_results")
    hotel_results = state.get("hotel_results")
    weather_results = state.get("weather_results")

    try:
        prompt_input = budget_agent_prompt.format_messages(
            query=user_query,
            constraints=trip_constraints,
            flight_results=flight_results,
            hotel_results=hotel_results,
            weather_results=weather_results
        )

        result: BudgetResponse = budget_llm.invoke(prompt_input)

    except Exception as exc:
        raise RuntimeError(f"Budget agent failed: {exc}") from exc

    return {"budget_details": result.budget_details}