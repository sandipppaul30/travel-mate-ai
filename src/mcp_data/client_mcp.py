import os
import sys
import certifi
from typing import Any
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from shared.config import get_env

load_dotenv()

os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

TAVILY_API_KEY = get_env("TAVILY_API_KEY")
AVIATION_STACK_API_KEY = get_env("AVIATION_STACK_API_KEY")
OPENWEATHER_API_KEY = get_env("OPENWEATHER_API_KEY")
GEMINI_API_KEY = get_env("GEMINI_API_KEY")
GEMINI_DEPLOYED_MODEL = get_env("GEMINI_DEPLOYED_MODEL")
tool_map = {}
mcp_client = MultiServerMCPClient(
    {
        "tavily": {
            "transport": "streamable_http",
            "url": f"https://mcp.tavily.com/mcp/?tavilyApiKey={TAVILY_API_KEY}"
        },
        "aviationstack": {
            "transport": "stdio",
            "command": "uvx",
            "args": [
                "aviationstack-mcp"
            ],
            "env": {
                "AVIATION_STACK_API_KEY": AVIATION_STACK_API_KEY
            }
        },
        "weather": {
            "transport": "stdio",
            "command": sys.executable,
            "args": ["weather_mcp_server.py"],
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
    if tool_name not in tool_map:
        raise ValueError(f"{tool_name} not found")

    return await tool_map[tool_name].ainvoke(kwargs)



