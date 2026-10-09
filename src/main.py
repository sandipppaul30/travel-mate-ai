import uuid
from fastapi import FastAPI
from mcp_data.client_mcp import mcp_tools
from shared.services import run_travel_agent, resume_travel_agent
from shared.models import TravelplanRequest

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
async def travel_plan(request: TravelplanRequest):
    thread_id = f"t_{uuid.uuid4().hex}"
    user_id = f"u_{uuid.uuid4().hex}"
    result = run_travel_agent(
        request.user_input,
        thread_id,
        user_id
    )
    return result
