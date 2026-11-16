import sqlite3
from pathlib import Path
from app.core.config import settings
from app.core.logging import logger

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    user_goal TEXT NOT NULL,
    plan TEXT,
    final_response TEXT,
    success BOOLEAN NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tool_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    tool_name TEXT NOT NULL,
    arguments TEXT,
    output TEXT,
    success BOOLEAN NOT NULL,
    error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_preferences (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS task_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    task_goal TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING',
    result TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);
"""

from contextlib import contextmanager

@contextmanager
def get_db_connection():
    """Context manager that opens and properly closes a SQLite connection."""
    db_path = settings.DATABASE_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """Initializes SQLite tables if they do not exist."""
    with get_db_connection() as conn:
        conn.executescript(SCHEMA_SQL)
        conn.commit()
    logger.info(f"Database initialized at {settings.DATABASE_PATH}")
