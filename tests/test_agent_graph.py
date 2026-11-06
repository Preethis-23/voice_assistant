import pytest
from app.agent.state import AgentState, PlannedStep
from app.agent.graph import route_after_execution, route_after_evaluation
from app.tools.base import ToolResult

def test_graph_routing_continues_when_steps_remain():
    state = AgentState(
        user_goal="Test goal",
        plan=[
            PlannedStep(step_number=1, description="Step 1", status="completed"),
            PlannedStep(step_number=2, description="Step 2", status="pending")
        ],
        current_step_index=1,
        observations=[ToolResult(tool_name="test_tool", success=True, output="ok")]
    )
    route = route_after_execution(state)
    assert route == "executor"

def test_graph_routing_evaluates_on_failure():
    state = AgentState(
        user_goal="Test goal",
        plan=[PlannedStep(step_number=1, description="Step 1", status="failed")],
        current_step_index=1,
        observations=[ToolResult(tool_name="test_tool", success=False, output=None, error="Failed")]
    )
    route = route_after_execution(state)
    assert route == "evaluator"

def test_graph_routing_finishes_when_done():
    state = AgentState(
        user_goal="Test goal",
        plan=[PlannedStep(step_number=1, description="Step 1", status="completed")],
        current_step_index=1,
        observations=[ToolResult(tool_name="test_tool", success=True, output="ok")]
    )
    route = route_after_execution(state)
    assert route == "responder"
