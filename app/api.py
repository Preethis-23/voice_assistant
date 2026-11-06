import sys
from pathlib import Path

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from app.agent.graph import run_agent_goal
from app.memory.repository import memory_repo
from app.tools.base import TOOL_REGISTRY

app = FastAPI(title="KIRA Agentic Assistant API", version="1.0.0")

class GoalRequest(BaseModel):
    user_goal: str
    session_id: Optional[str] = "api_session"

class GoalResponse(BaseModel):
    user_goal: str
    final_response: str
    plan: List[Dict[str, Any]]
    is_complete: bool
    error_count: int

@app.get("/")
def root():
    return {"status": "online", "agent": "KIRA Agentic AI Desktop Assistant"}

@app.get("/tools")
def list_tools():
    return [{"name": t.name, "description": t.description} for t in TOOL_REGISTRY.values()]

@app.get("/history")
def get_history(limit: int = 10):
    return memory_repo.get_recent_history(limit=limit)

@app.post("/execute", response_model=GoalResponse)
def execute_goal(req: GoalRequest):
    try:
        state = run_agent_goal(user_goal=req.user_goal, session_id=req.session_id)
        return GoalResponse(
            user_goal=state.user_goal,
            final_response=state.final_response or "",
            plan=[s.model_dump() for s in state.plan],
            is_complete=state.is_complete,
            error_count=state.error_count
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
