from __future__ import annotations
import uuid
import requests
from typing import Any

from langchain_core.messages import HumanMessage
from langgraph.types import Command
from .memory import initial_state
from .graph import travel_graph, TravelContext

def request_json(url:str, params: dict[str, Any], timeout: int) -> dict[str, Any]:

    try:

        response = requests.get(url, params=params, timeout=timeout)

        response.raise_for_status()
        print(f"response: {response}")
        return response.json()

    except requests.RequestException as exc:

        details = ""

        failed_response = getattr(
            exc,
            "response",
            None
        )

        if failed_response is not None:

            details = (f"Response: {failed_response.text[:500]}")

        raise RuntimeError(f"API request failed {exec}.{details}") from exc

def _interrupt(result: dict[str, Any]) -> dict[str, Any] | None:

    items = result.get("__interrupt__", [])
    if not items:
        return None

    value = getattr(items[0], "value", items[0])
    return value if isinstance(value,dict) else {"value": value}

def _serialize(result: dict[str, Any], thread_id: str) -> dict[str, Any]:
    interrupt = _interrupt(result)
    itinerary = (interrupt or {}).get("draft_itinerary") or result.get("itinerary", "")
    messages = result.get("messages", [])

    return {
        "thread_id": thread_id,
        "answer": itinerary if interrupt else result.get("final_response") or (messages[-1].content if messages else ""),
        "requires_approval": interrupt is not None,
        "approval_request": (interrupt or {}).get("approval_request", result.get("approval_request", "")),
        "flight_results": result.get("flight_results", ""),
        "hotel_results": result.get("hotel_results", ""),
        "weather_results": result.get("weather_results", ""),
        "budget_results": result.get("budget_results", ""),
        "itinerary": itinerary,
        "selected_agents": result.get("selected_agents", []),
        "trip_constraints": result.get("trip_constraints", {}),
        "supervisor_reasoning": result.get("supervisor_reasoning", ""),
        "guardrail_allowed": result.get("guardrail_allowed", True),
        "guardrail_reason": result.get("guardrail_reason", ""),
        "approved": result.get("approved"),
        "human_feedback": result.get("human_feedback", ""),
        "llm_calls": result.get("llm_calls", 0),
        "memory_context": result.get("memory_context", {}),
    }

def run_travel_agent(user_input: str, thread_id: str | None = None, user_id: str | None = None):
    thread_id = thread_id or f"user_{uuid.uuid4().hex}"
    user_id = user_id or thread_id
    state = initial_state(user_input)
    state["messages"] = [HumanMessage(content=user_input)]

    result = travel_graph.invoke(
        state,
        config={"configurable": {"thread_id": thread_id}},
        context=TravelContext(user_id=user_id, thread_id=thread_id),
    )
    return _serialize(result, thread_id)


def resume_travel_agent(thread_id: str, approved: bool, feedback: str = "", user_id: str | None = None):
    if not thread_id:
        raise ValueError("thread_id is required to resume a travel plan.")

    user_id = user_id or thread_id
    result = travel_graph.invoke(
        Command(resume={"approved": approved, "feedback": feedback.strip()}),
        config={"configurable": {"thread_id": thread_id}},
        context=TravelContext(user_id=user_id, thread_id=thread_id),
    )
    return _serialize(result, thread_id)
