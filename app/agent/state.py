from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.tools.base import ToolResult

class PlannedStep(BaseModel):
    step_number: int
    description: str
    tool_name: Optional[str] = None
    arguments: Dict[str, Any] = Field(default_factory=dict)
    status: str = "pending"  # pending, in_progress, completed, failed
    result: Optional[str] = None

class AgentState(BaseModel):
    """LangGraph typed agent state representing current execution context."""
    session_id: str = "default"
    user_goal: str
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)
    plan: List[PlannedStep] = Field(default_factory=list)
    current_step_index: int = 0
    current_tool_call: Optional[Dict[str, Any]] = None
    observations: List[ToolResult] = Field(default_factory=list)
    error_count: int = 0
    max_retries: int = 3
    is_complete: bool = False
    status_message: str = "Initializing"
    final_response: Optional[str] = None
