import pytest
from app.memory.repository import memory_repo
from app.memory.database import get_db_connection

def test_record_task_and_retrieve():
    session_id = "test_sess_001"
    user_goal = "Search ML news and save to desktop"
    plan = ["Search web", "Write file"]
    response = "Completed successfully."

    memory_repo.record_task_run(
        session_id=session_id,
        user_goal=user_goal,
        plan=plan,
        final_response=response,
        success=True
    )

    history = memory_repo.get_recent_history(limit=5)
    assert len(history) >= 1
    latest = history[0]
    assert latest["user_goal"] == user_goal
    assert latest["plan"] == plan

def test_user_preferences():
    memory_repo.set_preference("default_browser", "chrome")
    val = memory_repo.get_preference("default_browser")
    assert val == "chrome"
