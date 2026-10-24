import asyncio
import json
import re
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


def _parse_markdown_airports(text):
    """Parse the ourairports markdown output into airport dicts.

    Each airport looks like:
        **YEG** (ident CA-1291, id 610367)
        **Type:** large_airport | **Scheduled service:** yes
        **Codes:** IATA YEG · ICAO CYEG · GPS ... · Local ...
        **Location:** ...
        **Place:** Edmonton, region Alberta (CA-AB), country Canada
    Entries marked "(Duplicate)" are skipped.
    """
    airports = []
    # Split into per-airport chunks at each "**...** (ident" header line
    chunks = re.split(r"\n(?=\*\*[^\n]*?\*\*\s*\(ident )", "\n" + text)
    for chunk in chunks:
        if "**Type:**" not in chunk:
            continue
        header = chunk.strip().splitlines()[0]
        if "(Duplicate)" in header:
            continue
        type_m = re.search(r"\*\*Type:\*\*\s*([A-Za-z_]+)", chunk)
        iata_m = re.search(r"IATA\s+([A-Z0-9]{3})\b", chunk)
        airports.append({
            "type": type_m.group(1) if type_m else None,
            "iataCode": iata_m.group(1) if iata_m else None,
            "header": header,
        })
    return airports


def _extract_airports(response):
    """Normalize an MCP response into a list of airport dicts.

    Handles: JSON (string / dict / list), MCP content blocks
    ([{"type": "text", "text": "..."}]), and the markdown text format
    returned by ourairports_search_airports.
    """
    def parse_text(text):
        text = (text or "").strip()
        if not text:
            return []
        try:
            p = json.loads(text)
        except json.JSONDecodeError:
            return _parse_markdown_airports(text)
        if isinstance(p, dict):
            return p.get("airports", [p])
        return p if isinstance(p, list) else []

    if isinstance(response, str):
        return parse_text(response)

    # MCP content blocks: [{"type": "text", "text": "..."}, ...]
    if isinstance(response, list) and response and all(
        isinstance(i, dict) and i.get("type") == "text" and "text" in i
        for i in response
    ):
        airports = []
        for block in response:
            airports.extend(parse_text(block.get("text")))
        return airports

    if isinstance(response, dict):
        return response.get("airports", [])
    if isinstance(response, list):
        return response
    return []


def get_iata_code(response):
    """Return the iataCode of the first large_airport in an MCP response."""
    if not response:
        raise ValueError("Airport response is empty or None")

    airports = [a for a in _extract_airports(response) if isinstance(a, dict)]

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

    constraints = state.get("trip_constraints", {})
    origin = constraints.get("origin", "")
    destination = constraints.get("destination", "")
    duration = constraints.get("duration", "")
    start_date = constraints.get("start_date", "")
    end_date = constraints.get("end_date", "")
    adult_count = constraints.get("adult_count", 0)
    child_count = constraints.get("child_count", 0)

    try:
        departure, arrival = await asyncio.gather(
            call_tool("ourairports_search_airports", query=f"{origin}"),
            call_tool("ourairports_search_airports", query=f"{destination}"),
        )

        departure_iata = get_iata_code(departure)
        arrival_iata = get_iata_code(arrival)

        if not departure_iata:
            raise ValueError(f"No IATA airport code found for origin '{origin}'")
        if not arrival_iata:
            raise ValueError(f"No IATA airport code found for destination '{destination}'")

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