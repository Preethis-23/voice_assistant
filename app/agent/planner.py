import json
import re
from typing import Dict, Any, List, Optional
import requests
from app.core.config import settings
from app.core.logging import logger
from app.agent.state import AgentState, PlannedStep
from app.agent.prompts import (
    SYSTEM_PROMPT,
    PLANNING_PROMPT,
    REPLANNING_PROMPT,
    FINAL_RESPONSE_PROMPT
)
from app.tools.base import TOOL_REGISTRY, execute_tool, ToolResult
from app.memory.repository import memory_repo

def call_ollama(prompt: str, system: Optional[str] = SYSTEM_PROMPT, json_mode: bool = False) -> str:
    """Calls local Ollama instance with fallback to standard completion endpoint."""
    url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/generate"
    payload = {
        "model": settings.OLLAMA_MODEL,
        "prompt": prompt,
        "system": system,
        "stream": False,
        "options": {
            "temperature": settings.OLLAMA_TEMPERATURE
        }
    }
    if json_mode:
        payload["format"] = "json"

    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except Exception as e:
        logger.error(f"Ollama call failed: {e}")
        raise RuntimeError(f"Local Ollama model '{settings.OLLAMA_MODEL}' not responding at {settings.OLLAMA_BASE_URL}: {e}")

def extract_json(text: str) -> Dict[str, Any]:
    """Robustly parses JSON from LLM outputs with markdown backtick stripping."""
    cleaned = text.strip()
    if "`" in cleaned:
        match = re.search(r"`(?:json)?\s*([\s\S]*?)\s*`", cleaned)
        if match:
            cleaned = match.group(1).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1:
            return json.loads(cleaned[start:end+1])
        raise

def get_tool_descriptions_text() -> str:
    """Formats all registered tools into clean descriptive text for planner prompt."""
    lines = []
    for name, tool in TOOL_REGISTRY.items():
        props = tool.parameters.get("properties", {})
        req = tool.parameters.get("required", [])
        params_desc = ", ".join([f"{k} ({props[k].get('type', 'any')}{'*' if k in req else ''})" for k in props])
        lines.append(f"- {name}({params_desc}): {tool.description}")
    return "\n".join(lines)

# ─── LangGraph Node Implementations ──────────────────────────────────────────

def plan_node(state: AgentState) -> Dict[str, Any]:
    """Decomposes the user's goal into an actionable multi-step plan."""
    logger.info(f"[PLANNER] Decomposing goal: '{state.user_goal}'")

    recent_history = memory_repo.get_recent_history(limit=3)
    history_text = "\n".join([f"Past Goal: {h['user_goal']} -> Result: {h['final_response']}" for h in recent_history]) or "None"

    prompt = PLANNING_PROMPT.format(
        tool_descriptions=get_tool_descriptions_text(),
        user_goal=state.user_goal,
        recent_context=history_text
    )

    try:
        raw_output = call_ollama(prompt, json_mode=True)
        data = extract_json(raw_output)

        # Handle direct conversational answers (no tools needed)
        direct_answer = data.get("direct_answer", "").strip()
        if direct_answer and not data.get("plan"):
            logger.info("[PLANNER] Conversational question — answering directly without tools.")
            return {
                "plan": [PlannedStep(
                    step_number=1,
                    description="Direct answer",
                    tool_name=None,
                    arguments={},
                    status="completed",
                    result=direct_answer
                )],
                "final_response": direct_answer,
                "current_step_index": 1,
                "is_complete": True,
                "status_message": "Direct conversational answer"
            }

        steps = []
        for i, s in enumerate(data.get("plan", [])):
            steps.append(PlannedStep(
                step_number=i + 1,
                description=s.get("description", f"Step {i+1}"),
                tool_name=s.get("tool_name"),
                arguments=s.get("arguments", {}),
                status="pending"
            ))

        if not steps:
            steps.append(PlannedStep(
                step_number=1,
                description="Synthesize direct response",
                tool_name=None,
                arguments={},
                status="pending"
            ))

        return {
            "plan": steps,
            "current_step_index": 0,
            "status_message": f"Planned {len(steps)} step(s)"
        }
    except Exception as e:
        logger.warning(f"Planner fallback: {e}")
        return {
            "plan": [PlannedStep(step_number=1, description="Answer user request directly", tool_name=None)],
            "current_step_index": 0,
            "status_message": "Using fallback direct plan"
        }

def execute_step_node(state: AgentState) -> Dict[str, Any]:
    """Executes the tool designated for the current planned step."""
    if state.current_step_index >= len(state.plan):
        return {"is_complete": True, "status_message": "All steps executed"}

    current_step = state.plan[state.current_step_index]
    logger.info(f"[EXECUTING STEP {current_step.step_number}/{len(state.plan)}] {current_step.description}")

    if not current_step.tool_name or current_step.tool_name.lower() in ("null", "none"):
        current_step.status = "completed"
        current_step.result = "No tool required."
        return {
            "current_step_index": state.current_step_index + 1,
            "status_message": f"Completed step {current_step.step_number}"
        }

    current_step.status = "in_progress"
    tool_result = execute_tool(current_step.tool_name, current_step.arguments)

    memory_repo.log_tool_execution(
        session_id=state.session_id,
        tool_name=current_step.tool_name,
        arguments=current_step.arguments,
        output=tool_result.output,
        success=tool_result.success,
        error=tool_result.error
    )

    if tool_result.success:
        current_step.status = "completed"
        current_step.result = str(tool_result.output)[:1000]
        logger.info(f"[STEP SUCCEEDED] {current_step.tool_name}")
        return {
            "observations": state.observations + [tool_result],
            "current_step_index": state.current_step_index + 1,
            "status_message": f"Step {current_step.step_number} completed"
        }
    else:
        current_step.status = "failed"
        current_step.result = tool_result.error
        logger.warning(f"[STEP FAILED] {current_step.tool_name}: {tool_result.error}")
        return {
            "observations": state.observations + [tool_result],
            "error_count": state.error_count + 1,
            "status_message": f"Step {current_step.step_number} failed: {tool_result.error}"
        }

def evaluate_and_replan_node(state: AgentState) -> Dict[str, Any]:
    """Analyzes failures, performs dynamic replanning, or marks goal complete."""
    if state.current_step_index >= len(state.plan):
        return {"is_complete": True, "status_message": "All planned tasks finished"}

    last_observation = state.observations[-1] if state.observations else None
    if last_observation and not last_observation.success and state.error_count <= state.max_retries:
        logger.info("[REPLANNING] Attempting failure recovery...")

        failed_step = state.plan[state.current_step_index]
        completed_steps = [f"Step {s.step_number}: {s.description} ({s.status})" for s in state.plan if s.status == "completed"]

        prompt = REPLANNING_PROMPT.format(
            user_goal=state.user_goal,
            failed_step=f"{failed_step.description} with {failed_step.tool_name}",
            tool_name=failed_step.tool_name,
            error_observation=last_observation.error,
            completed_steps="\n".join(completed_steps) or "None"
        )

        try:
            raw = call_ollama(prompt, json_mode=True)
            data = extract_json(raw)

            if data.get("can_recover") and data.get("revised_steps"):
                new_steps = []
                for i, s in enumerate(data.get("revised_steps", [])):
                    new_steps.append(PlannedStep(
                        step_number=len(completed_steps) + i + 1,
                        description=s.get("description", "Revised step"),
                        tool_name=s.get("tool_name"),
                        arguments=s.get("arguments", {}),
                        status="pending"
                    ))
                retained_plan = [s for s in state.plan if s.status == "completed"] + new_steps
                logger.info(f"[REPLAN SUCCESS] Generated {len(new_steps)} new step(s).")
                return {
                    "plan": retained_plan,
                    "current_step_index": len(completed_steps),
                    "status_message": "Recovered with revised plan"
                }
        except Exception as e:
            logger.error(f"Replanning evaluation failed: {e}")

    return {"is_complete": True, "status_message": "Proceeding to final response"}

def respond_node(state: AgentState) -> Dict[str, Any]:
    """Generates the final voice-friendly spoken response."""
    logger.info("[SYNTHESIZING RESPONSE] Generating spoken answer...")

    summary_items = []
    for s in state.plan:
        summary_items.append(f"- Step {s.step_number} ({s.description}): {s.status.upper()} -> Result: {s.result or 'None'}")

    summary_text = "\n".join(summary_items)

    prompt = FINAL_RESPONSE_PROMPT.format(
        user_goal=state.user_goal,
        execution_summary=summary_text
    )

    try:
        response_text = call_ollama(prompt, json_mode=False)
        clean_response = response_text.strip().strip("'\"")
    except Exception as e:
        logger.error(f"Response synthesis failed: {e}")
        clean_response = f"I have processed your request for: {state.user_goal}."

    memory_repo.record_task_run(
        session_id=state.session_id,
        user_goal=state.user_goal,
        plan=[s.description for s in state.plan],
        final_response=clean_response,
        success=state.error_count == 0
    )

    return {
        "final_response": clean_response,
        "is_complete": True,
        "status_message": "Task complete"
    }
