from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from ..shared.config import get_env, get_gemini_client
from ..shared.memory import TravelState

final_agent_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a travel planning assistant. \n"
     "Your task is to provide a comprehensive travel plan based on the user's query and the information provided by other agents. \n"),
    ("human",
     "User Query: {query}\n"
     "Trip Constraints: {constraints}\n"
     "Flight Results: {flight_results}\n"
     "Hotel Results: {hotel_results}\n"
     "Weather Results: {weather_results}\n"
     "Budget Results: {budget_results}\n"
     "Itinerary: {itinerary}\n"
     "Human Feedback: {human_feedback}\n"
    )
])

def final_agent(state: TravelState):
    user_query = state.get("user_query")
    trip_constraints = state.get("trip_constraints")
    flight_results = state.get("flight_results")
    hotel_results = state.get("hotel_results")
    weather_results = state.get("weather_results")
    budget_results = state.get("budget_results")
    itinerary = state.get("itinerary")
    human_feedback = state.get("human_feedback")

    try:
        prompt_input = final_agent_prompt.format_messages(
            query=user_query,
            constraints=trip_constraints,
            flight_results=flight_results,
            hotel_results=hotel_results,
            weather_results=weather_results,
            budget_results=budget_results,
            itinerary=itinerary,
            human_feedback=human_feedback
        )

        final_llm = get_gemini_client()
        final_response = final_llm.invoke(prompt_input) 

    except Exception as exc:    
        raise RuntimeError(f"Final agent failed: {exc}") from exc

    return {"final_response": final_response.content}



