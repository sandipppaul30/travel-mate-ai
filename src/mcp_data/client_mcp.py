import os
import sys
import certifi
from typing import Any
from pathlib import Path
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from shared.config import get_env

load_dotenv()

os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

BASE_DIR = Path(__file__).resolve().parent

TAVILY_API_KEY = get_env("TAVILY_API_KEY")
AVIATION_STACK_API_KEY = get_env("AVIATION_STACK_API_KEY")
OPENWEATHER_API_KEY = get_env("OPENWEATHER_API_KEY")
GEMINI_API_KEY = get_env("GEMINI_API_KEY")
GEMINI_DEPLOYED_MODEL = get_env("GEMINI_DEPLOYED_MODEL")
SERPAPI_API_KEY = get_env("SERPAPI_API_KEY")
tool_map = {}
mcp_client = MultiServerMCPClient(
    {
        "tavily": {
            "transport": "streamable_http",
            "url": f"https://mcp.tavily.com/mcp/?tavilyApiKey={TAVILY_API_KEY}"
        },
        "ourairports": {
            "transport": "stdio",
            "command": "npx",
            "args": [
                "-y", "@cyanheads/ourairports-mcp-server"
            ]
        },
        "flight": {
            "transport": "stdio",
            "command": sys.executable,
            "args": [
                str(BASE_DIR / "flight_mcp_server.py")
            ],
            "env": {
                "SERPAPI_API_KEY": SERPAPI_API_KEY
            }
        },
        "weather": {
            "transport": "stdio",
            "command": sys.executable,
            "args": [str(BASE_DIR / "weather_mcp_server.py")],
            "env": {
                "OPENWEATHER_API_KEY": OPENWEATHER_API_KEY
            }
        }
    }
)

async def mcp_tools():
    tools = await mcp_client.get_tools()
    tool_map = {tool.name: tool for tool in tools}
    return tool_map

async def call_tool(tool_name: str, **kwargs):
    tool_map = await mcp_tools()
    if tool_name not in tool_map:
        raise ValueError(f"{tool_name} not found")

    return await tool_map[tool_name].ainvoke(kwargs)



