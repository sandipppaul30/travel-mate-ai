from langgraph.types import interrupt
from ..shared.memory import TravelState

def human_approval_agent(state: TravelState):

    review = interrupt({
        "question": "Do you approve this itinerary?",
        "draft_itinerary": state.get("itinerary"),
        "approval_request": state.get("approval_request"),
        "selected_agents": state.get("selected_agents"),
        "supervisor_reasoning": state.get("supervisor_reasoning"),
        "expected_response": {"approved": True, "feedback": "Optional revision feedback from the user."}
    })

    return {
        "approved": bool(review.get("approved", False)),
        "human_feedback": str(review.get("feedback", "")).strip()
    }