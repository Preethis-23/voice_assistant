import re
from typing import List, Dict, Any, Optional
from app.core.logging import logger
from app.memory.repository import memory_repo
from app.agent.graph import run_agent_goal

# Regex pattern to identify multi-command intent
MULTI_COMMAND_SPLIT_PATTERN = re.compile(
    r'\s*(?:,\s*and\s+then\s+|;\s*and\s+then\s+|\s+and\s+then\s+|\s+after\s+that\s+|,\s*then\s+|\s+then\s+|;\s*also\s+|,\s*also\s+|\s+also\s+|;\s+)\s*',
    re.IGNORECASE
)

def split_user_goals(raw_command: str) -> List[str]:
    """Splits a compound user command into atomic sub-goals if multiple works are requested."""
    cleaned = raw_command.strip()
    # Check if there are multi-command delimiters
    parts = MULTI_COMMAND_SPLIT_PATTERN.split(cleaned)
    valid_parts = [p.strip() for p in parts if len(p.strip()) > 3]
    return valid_parts if len(valid_parts) > 1 else [cleaned]

class TaskQueueManager:
    """Manages local SQLite sequential task queue for compound multi-work instructions."""

    @staticmethod
    def process_command(user_command: str, session_id: str, on_task_start=None, on_task_finish=None) -> Dict[str, Any]:
        """Detects if single or multi-task; enqueues and runs sequentially if multiple."""
        sub_goals = split_user_goals(user_command)

        if len(sub_goals) <= 1:
            # Single task — run directly through LangGraph
            state = run_agent_goal(user_command, session_id=session_id)
            return {
                "is_multi_task": False,
                "total_tasks": 1,
                "completed_tasks": 1 if state.is_complete else 0,
                "final_response": state.final_response,
                "state": state
            }

        # Multi-task compound command
        logger.info(f"[TASK QUEUE] Multi-command detected with {len(sub_goals)} distinct tasks: {sub_goals}")
        task_ids = []
        for g in sub_goals:
            tid = memory_repo.enqueue_task(session_id=session_id, task_goal=g)
            task_ids.append((tid, g))

        results = []
        responses = []
        for index, (tid, goal) in enumerate(task_ids, start=1):
            logger.info(f"[TASK QUEUE] Executing task {index}/{len(task_ids)}: '{goal}'")
            memory_repo.update_task_status(tid, "IN_PROGRESS")
            if on_task_start:
                on_task_start(index, len(task_ids), goal)

            state = run_agent_goal(goal, session_id=session_id)
            status = "COMPLETED" if (state.is_complete and state.error_count == 0) else "COMPLETED_WITH_WARNINGS"
            memory_repo.update_task_status(tid, status, result=state.final_response)

            results.append({
                "task_id": tid,
                "goal": goal,
                "status": status,
                "response": state.final_response
            })
            responses.append(f"Task {index}: {state.final_response}")
            if on_task_finish:
                on_task_finish(index, len(task_ids), goal, state.final_response)

        aggregated_response = f"Completed all {len(sub_goals)} queued tasks. " + " ".join(responses)
        return {
            "is_multi_task": True,
            "total_tasks": len(sub_goals),
            "completed_tasks": len(results),
            "final_response": aggregated_response,
            "tasks": results
        }

task_queue_manager = TaskQueueManager()
