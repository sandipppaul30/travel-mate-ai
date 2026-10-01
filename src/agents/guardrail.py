from langchain_core.messages import AIMessage
from llm_guard import scan_prompt
from llm_guard.input_scanners import BanTopics, PromptInjection, Toxicity
from ..shared.memory import TravelState, empty_constraints

DEFAULT_BLOCK_REASON = (
    "TripMate AI can only help with travel-planning requests. "
    "Please ask about a destination, flight, hotel, weather, budget, or itinerary."
)

FAIL_OPEN = False

SCANNERS = [
    PromptInjection(threshold=0.9),
    Toxicity(threshold=0.7),
    BanTopics(
        topics=[
            "politics", "programming", "medical advice", "investment advice",
            "illegal activities", "violence", "weapons", "adult content",
        ],
        threshold=0.7
    )
]

BLOCK_MESSAGES = {
    "PromptInjection": "Your request looks like an attempt to override my instructions.",
    "Toxicity": "Please keep the conversation respectful.",
    "BanTopics": DEFAULT_BLOCK_REASON,
}

def _blocked(reason:str, log: str):

    return {
        "guardrail_allowed": False,
        "guardrail_reason": reason,
        "selected_agents": [],
        "trip_constraints": empty_constraints(),
        "supervisor_reasoning": reason,
        "final_response": reason,
        "messages": [AIMessage(content=f"Guardrail blocked request: {log}")],
    }

def guardrail_agent(state: TravelState):
    try:
        _, valid, scores = scan_prompt(SCANNERS, state["user_query"], fail_fast=True)
    except Exception as exc:

        print(f"Guardrail Error")
        if FAIL_OPEN:
            valid = {}
        else:
            return _blocked("Sorry, I couldn't validate your request. Please try again.", str(exc))

    failed = [name for name, ok in valid.items() if not ok]
    if failed:
        name = failed[0]
        return _blocked(BLOCK_MESSAGES.get(name, DEFAULT_BLOCK_REASON), f"{name} ({scores[name]:.2f})")

    return {
        "guardrail_allowed": True,
        "guardrail_reason": "",
        "messages": [AIMessage(content="Travel request passed guardrail.")],
    }

def guardrail_blocked_agent(state: TravelState):
    reason = state.get("final_response") or state.get("guardrail_reason") or "Request blocked."
    return {"final_response": reason, "messages": [AIMessage(content=reason)]}

