"""
Flights MCP server
------------------
Exposes one tool, `find_best_flight`, that queries SerpAPI's Google Flights
engine and returns JSON with the best flight: non-stop, cheapest, and (on a
price tie) shortest.

Setup:
    pip install "mcp[cli]" httpx
    export SERPAPI_API_KEY="your_key"
    python flights_mcp_server.py          # runs over stdio
"""

import os
from typing import Any, Optional

import httpx
from mcp.server.fastmcp import FastMCP
from shared.http_client import request_json

SERPAPI_URL = "https://serpapi.com/search.json"

mcp = FastMCP("flights")


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def _is_nonstop(itinerary: dict) -> bool:
    """A non-stop itinerary has exactly one segment and no layovers."""
    return len(itinerary.get("flights", [])) == 1 and not itinerary.get("layovers")


def _sort_key(itinerary: dict) -> tuple:
    """Cheapest first; on equal price, the shorter flight wins."""
    return (
        itinerary.get("price", float("inf")),
        itinerary.get("total_duration", float("inf")),
    )


def _simplify(itinerary: dict) -> dict:
    """Trim a SerpAPI itinerary down to the fields a caller actually needs."""
    segments = []
    for seg in itinerary.get("flights", []):
        segments.append(
            {
                "airline": seg.get("airline"),
                "flight_number": seg.get("flight_number"),
                "airplane": seg.get("airplane"),
                "travel_class": seg.get("travel_class"),
                "departure_airport": seg.get("departure_airport", {}).get("id"),
                "departure_time": seg.get("departure_airport", {}).get("time"),
                "arrival_airport": seg.get("arrival_airport", {}).get("id"),
                "arrival_time": seg.get("arrival_airport", {}).get("time"),
                "duration_minutes": seg.get("duration"),
            }
        )
    return {
        "price": itinerary.get("price"),
        "type": itinerary.get("type"),
        "nonstop": _is_nonstop(itinerary),
        "total_duration_minutes": itinerary.get("total_duration"),
        "carbon_emissions_kg": (
            round(itinerary["carbon_emissions"]["this_flight"] / 1000)
            if itinerary.get("carbon_emissions", {}).get("this_flight")
            else None
        ),
        "segments": segments,
    }


def _pick_best(data: dict, nonstop_only: bool, top_n: int) -> dict:
    """Select the best flight and a few alternatives from a SerpAPI response."""
    candidates = (data.get("best_flights") or []) + (data.get("other_flights") or [])
    if nonstop_only:
        candidates = [c for c in candidates if _is_nonstop(c)]
    candidates = [c for c in candidates if c.get("price") is not None]

    if not candidates:
        return {"best_flight": None, "alternatives": [], "candidates_considered": 0}

    ranked = sorted(candidates, key=_sort_key)
    fastest = min(candidates, key=lambda c: c.get("total_duration", float("inf")))

    return {
        "best_flight": _simplify(ranked[0]),
        "fastest_flight": _simplify(fastest),
        "alternatives": [_simplify(c) for c in ranked[1 : 1 + top_n]],
        "candidates_considered": len(candidates),
        "_raw_best": ranked[0],  # used internally, removed before returning
    }


async def _serpapi_get(client: httpx.AsyncClient, params: dict) -> dict:
    resp = await client.get(SERPAPI_URL, params=params, timeout=60)
    resp.raise_for_status()
    return resp.json()


# --------------------------------------------------------------------------
# Tool
# --------------------------------------------------------------------------
@mcp.tool()
async def find_best_flight(
    departure_id: str,
    arrival_id: str,
    outbound_date: str,
    return_date: Optional[str] = None,
    adults: int = 1,
    children: int = 0,
    infants_in_seat: int = 0,
    infants_on_lap: int = 0,
    currency: str = "INR",
    gl: str = "in",
    hl: str = "en",
    travel_class: int = 1,
    nonstop_only: bool = True,
    include_return_flight: bool = True,
    top_n: int = 3,
    api_key: Optional[str] = None,
) -> dict[str, Any]:
    """Find the best flight: non-stop, cheapest, and shortest on a price tie.

    Args:
        departure_id: IATA code of the origin airport, e.g. "CCU".
        arrival_id: IATA code of the destination airport, e.g. "DEL".
        outbound_date: Departure date, YYYY-MM-DD.
        return_date: Return date, YYYY-MM-DD. Omit for a one-way trip.
        adults: Number of adult passengers.
        children: Number of child passengers.
        infants_in_seat: Number of infants with their own seat.
        infants_on_lap: Number of infants on a lap.
        currency: Currency code for prices, e.g. "INR", "USD".
        gl: Google country code, e.g. "in".
        hl: Google language code, e.g. "en".
        travel_class: 1=Economy, 2=Premium economy, 3=Business, 4=First.
        nonstop_only: Only consider non-stop flights.
        include_return_flight: For round trips, also pick the best return flight.
        top_n: Number of alternative flights to include.
        api_key: SerpAPI key. Falls back to the SERPAPI_API_KEY env variable.
    """
    key = api_key or os.environ.get("SERPAPI_API_KEY")
    if not key:
        return {"error": "Missing SerpAPI key. Set SERPAPI_API_KEY or pass api_key."}

    round_trip = return_date is not None
    params: dict[str, Any] = {
        "engine": "google_flights",
        "departure_id": departure_id,
        "arrival_id": arrival_id,
        "outbound_date": outbound_date,
        "type": 1 if round_trip else 2,  # 1 = round trip, 2 = one way
        "adults": adults,
        "children": children,
        "infants_in_seat": infants_in_seat,
        "infants_on_lap": infants_on_lap,
        "currency": currency,
        "gl": gl,
        "hl": hl,
        "travel_class": travel_class,
        "sort_by": 2,  # sort by price
        "api_key": key,
    }
    if round_trip:
        params["return_date"] = return_date
    if nonstop_only:
        params["stops"] = 1  # SerpAPI: 1 = non-stop only

    try:
        data = request_json(SERPAPI_URL, params, timeout=60)
        if data.get("error"):
            return {"error": data["error"]}

        outbound = _pick_best(data, nonstop_only, top_n)
        raw_best = outbound.pop("_raw_best", None)

        result: dict[str, Any] = {
            "search": {
                "departure_id": departure_id,
                "arrival_id": arrival_id,
                "outbound_date": outbound_date,
                "return_date": return_date,
                "trip_type": "round_trip" if round_trip else "one_way",
                "passengers": {
                    "adults": adults,
                    "children": children,
                    "infants_in_seat": infants_in_seat,
                    "infants_on_lap": infants_on_lap,
                },
                "currency": currency,
                "nonstop_only": nonstop_only,
                "google_flights_url": data.get("search_metadata", {}).get(
                    "google_flights_url"
                ),
            },
            "outbound": outbound,
        }

        # Round trip: the first call returns outbound options (priced as a
        # round trip). A second call with departure_token returns the
        # matching return flights.
        if (
            round_trip
            and include_return_flight
            and raw_best
            and raw_best.get("departure_token")
        ):
            ret_params = {**params, "departure_token": raw_best["departure_token"]}
            ret_data = request_json(SERPAPI_URL, ret_params, timeout=60)
            if ret_data.get("error"):
                result["return"] = {"error": ret_data["error"]}
            else:
                ret = _pick_best(ret_data, nonstop_only, top_n)
                ret.pop("_raw_best", None)
                result["return"] = ret
                ret_best = ret.get("best_flight")
                if ret_best:
                    result["total_round_trip_price"] = ret_best["price"]

        return result

    except httpx.HTTPStatusError as e:
        return {"error": f"SerpAPI HTTP {e.response.status_code}: {e.response.text[:300]}"}
    except httpx.HTTPError as e:
        return {"error": f"Request to SerpAPI failed: {e}"}


if __name__ == "__main__":
    mcp.run()