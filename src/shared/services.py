import requests
from typing import Any


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



