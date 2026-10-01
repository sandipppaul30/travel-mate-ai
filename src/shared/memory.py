from __future__ import annotations

import operator
from datetime import datetime, timezone
from typing import Annotated, Any, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.runtime import Runtime


class TravelState(TypedDict, total=False):
    messages: Annotated[list[AnyMessage], operator.add]
    user_query: str

    guardrail_allowed: bool
    guardrail_reason: str
    selected_agents: list[str]
    trip_constraints: dict[str, Any]
    supervisor_reasoning: str

    flight_results: str
    hotel_results: str
    weather_results: str
    budget_results: str
    itinerary: str

    approval_request: str
    approved: bool
    human_feedback: str

    final_response: str
    memory_context: dict[str, Any]
    llm_calls: int


# Fields that are runtime/derived rather than durable trip data, so they're
# excluded from what gets persisted to the memory store.
NON_PERSISTED_FIELDS = frozenset({"messages", "memory_context"})

# Single source of truth: whatever is in TravelState (minus the excluded
# fields) is what gets snapshotted to memory. No separate list to maintain.
MEMORY_FIELDS: tuple[str, ...] = tuple(
    key for key in TravelState.__annotations__ if key not in NON_PERSISTED_FIELDS
)


AGENT_ORDER = [
    "flight_agent",
    "hotel_agent",
    "weather_agent",
    "budget_agent",
    "itinerary_agent",
]
KNOWN_AGENTS = set(AGENT_ORDER)


def empty_constraints() -> dict[str, Any]:
    return {
        "destination": "",
        "origin": "",
        "duration": "",
        "budget": "",
        "travel_style": "",
        "special_preferences": [],
    }


def initial_state(user_query: str) -> TravelState:
    return {
        "messages": [],
        "user_query": user_query,
        "guardrail_allowed": True,
        "guardrail_reason": "",
        "selected_agents": [],
        "trip_constraints": empty_constraints(),
        "supervisor_reasoning": "",
        "flight_results": "",
        "hotel_results": "",
        "weather_results": "",
        "budget_results": "",
        "itinerary": "",
        "approval_request": "",
        "approved": False,
        "human_feedback": "",
        "final_response": "",
        "memory_context": {},
        "llm_calls": 0,
    }


# --- Memory persistence -----------------------------------------------------

NAMESPACE = "travel_state"


def _namespace(runtime: Runtime) -> tuple[str, str]:
    return (NAMESPACE, runtime.context.user_id)


def snapshot(state: TravelState) -> dict[str, Any]:
    return {
        "saved_at": datetime.now(timezone.utc).isoformat(),
        **{key: state.get(key) for key in MEMORY_FIELDS},
    }


def memory_load_agent(state: TravelState, runtime: Runtime) -> dict[str, Any]:
    item = runtime.store.get(_namespace(runtime), "latest")
    return {"memory_context": {"latest_trip": item.value if item else {}}}


def memory_persist_agent(state: TravelState, runtime: Runtime) -> dict[str, Any]:
    runtime.store.put(
        _namespace(runtime), "latest", {**snapshot(state), "thread_id": runtime.context.thread_id}
    )
    return {}