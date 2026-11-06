from typing import Literal
from langgraph.graph import StateGraph, END
from app.agent.state import AgentState
from app.agent.planner import (
    plan_node,
    execute_step_node,
    evaluate_and_replan_node,
    respond_node
)

def route_after_execution(state: AgentState) -> Literal["executor", "evaluator", "responder"]:
    """Conditional edge determining whether to continue execution, replan, or finish."""
    # If the last execution failed, route to evaluator for recovery
    if state.observations and not state.observations[-1].success:
        return "evaluator"

    # If there are more steps remaining in the plan, continue executing
    if state.current_step_index < len(state.plan):
        return "executor"

    # Otherwise, complete and synthesize response
    return "responder"

def route_after_evaluation(state: AgentState) -> Literal["executor", "responder"]:
    """Conditional edge after replanning."""
    if state.current_step_index < len(state.plan) and not state.is_complete:
        return "executor"
    return "responder"

def build_agent_graph():
    """Constructs the compiled LangGraph StateGraph."""
    builder = StateGraph(AgentState)

    # Register nodes
    builder.add_node("planner", plan_node)
    builder.add_node("executor", execute_step_node)
    builder.add_node("evaluator", evaluate_and_replan_node)
    builder.add_node("responder", respond_node)

    # Define edges
    builder.set_entry_point("planner")
    builder.add_edge("planner", "executor")

    builder.add_conditional_edges(
        "executor",
        route_after_execution,
        {
            "executor": "executor",
            "evaluator": "evaluator",
            "responder": "responder"
        }
    )

    builder.add_conditional_edges(
        "evaluator",
        route_after_evaluation,
        {
            "executor": "executor",
            "responder": "responder"
        }
    )

    builder.add_edge("responder", END)

    return builder.compile()

# Global compiled agent workflow
agent_workflow = build_agent_graph()

def run_agent_goal(user_goal: str, session_id: str = "cli_session") -> AgentState:
    """Executes the agent graph for a given user goal and returns the final state."""
    initial_state = AgentState(
        session_id=session_id,
        user_goal=user_goal
    )
    result = agent_workflow.invoke(initial_state)
    if isinstance(result, dict):
        return AgentState(**result)
    return result
