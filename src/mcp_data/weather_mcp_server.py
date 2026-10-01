from mcp.server.fastmcp import FastMCP
from typing import Any
from shared.config import get_env
from shared.services import request_json

mcp = FastMCP("Weather MCP server")

OPENWEATHER_API_KEY = get_env("OPENWEATHER_API_KEY")
REQUEST_TIMEOUT_SECONDS = get_env("REQUEST_TIMEOUT_SECONDS")
WEATHER_API = get_env("WEATHER_API")
FORECAST_API = get_env("FORECAST_API")

@mcp.tool()
def get_current_weather(city: str) -> dict[str, Any]:

    """Return current weather for a city"""

    city = city.strip()

    if not city:
        raise ValueError("City can't be empty")

    params = {
        "q": city,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric"
    }

    city_weather = request_json(WEATHER_API, params, REQUEST_TIMEOUT_SECONDS)
    
    return {
        "city": city_weather["name"],
        "tempareture_c": city_weather["main"]["temp"],
        "feels_like_c": city_weather["main"]["feels_like"],
        "humidity": city_weather["main"]["humidity"],
        "condition": city_weather["weather"][0]["description"],
        "wind_speed": city_weather["wind"]["speed"]
    }

@mcp.tool()
def get_forecast(city: str) -> dict[str, Any]:

    """Return the first five three-hour forecast entries for a city."""

    city = city.strip()

    if not city:

        raise ValueError("City can't be empty")

    params = {
        "q": city,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric"
    }

    forecast_data = request_json(FORECAST_API, params, REQUEST_TIMEOUT_SECONDS)

    forecast = [
        {
            "datetime": item["dt_txt"],
            "tempareture_c": item["main"]["temp"],
            "condition": item["weather"][0]["description"]
        }
        for item in forecast_data.get("list", [])[:5]
    ]

    return {
        "city": forecast_data.get("city", {}).get("name", city), "forecast": forecast
    }

if __name__ == "__main__":

    mcp.run(
        transport="stdio"
    )