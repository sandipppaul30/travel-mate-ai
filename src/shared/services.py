from __future__ import annotations
import uuid
import requests
from typing import Any

from langchain_core.messages import HumanMessage
from langgraph.types import Command
from .memory import initial_state

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

