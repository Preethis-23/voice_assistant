import json
from typing import List, Dict, Any, Optional
from app.memory.database import get_db_connection, init_db

class MemoryRepository:
    """Provides structured persistence for agent conversation memory, tool telemetry, and user preferences."""

    def __init__(self):
        init_db()

    def record_task_run(
        self,
        session_id: str,
        user_goal: str,
        plan: Optional[List[str]],
        final_response: str,
        success: bool = True
    ):
        with get_db_connection() as conn:
            conn.execute(
                """
                INSERT INTO conversations (session_id, user_goal, plan, final_response, success)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    user_goal,
                    json.dumps(plan or []),
                    final_response,
                    1 if success else 0
                )
            )
            conn.commit()

    def log_tool_execution(
        self,
        session_id: str,
        tool_name: str,
        arguments: Dict[str, Any],
        output: Any,
        success: bool,
        error: Optional[str] = None
    ):
        with get_db_connection() as conn:
            conn.execute(
                """
                INSERT INTO tool_logs (session_id, tool_name, arguments, output, success, error)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    tool_name,
                    json.dumps(arguments),
                    str(output)[:2000],
                    1 if success else 0,
                    error
                )
            )
            conn.commit()

    def get_recent_history(self, limit: int = 5) -> List[Dict[str, Any]]:
        with get_db_connection() as conn:
            rows = conn.execute(
                """
                SELECT session_id, user_goal, plan, final_response, success, created_at
                FROM conversations
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,)
            ).fetchall()

            history = []
            for r in rows:
                history.append({
                    "session_id": r["session_id"],
                    "user_goal": r["user_goal"],
                    "plan": json.loads(r["plan"]) if r["plan"] else [],
                    "final_response": r["final_response"],
                    "success": bool(r["success"]),
                    "created_at": r["created_at"]
                })
            return history

    def set_preference(self, key: str, value: str):
        with get_db_connection() as conn:
            conn.execute(
                """
                INSERT INTO user_preferences (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=CURRENT_TIMESTAMP
                """,
                (key, value)
            )
            conn.commit()

    def get_preference(self, key: str, default: Optional[str] = None) -> Optional[str]:
        with get_db_connection() as conn:
            row = conn.execute(
                "SELECT value FROM user_preferences WHERE key = ?",
                (key,)
            ).fetchone()
            return row["value"] if row else default

memory_repo = MemoryRepository()
