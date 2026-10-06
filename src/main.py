from fastapi import FastAPI
from mcp_data.client_mcp import mcp_tools
from shared.services import run_travel_agent, resume_travel_agent

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

@app.post("/travel_plan")
async def travel_plan(user_input: str, thread_id: str | None = None, user_id: str | None = None):
    result = run_travel_agent(user_input, thread_id, user_id)
    return result
