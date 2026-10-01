from fastapi import FastAPI
from mcp_data.client_mcp import mcp_tools

app = FastAPI(
    title = "TravelMateAI"
)

@app.get("/")
def home():
    return "Welcome to TravelMate AI portal"

@app.get("/list_tools")
async def get_mcp_tools():
    tool_map = await mcp_tools()
    return list(tool_map.keys())

